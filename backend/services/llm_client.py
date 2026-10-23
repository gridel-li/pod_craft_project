"""
LLMClient — 统一大语言模型 HTTP 客户端

功能说明：
基于 httpx.AsyncClient 异步网络库，统一封装 OpenAI 兼容协议的对话调用。
主要方法：
1. chat：向 /chat/completions 发送对话请求，返回模型生成的字符串。
2. chat_json：请求 JSON 格式输出，并对模型返回的文本做 Markdown 代码块剥离与容错解析，返回 Python 字典。
3. chat_stream：流式请求接口（Server-Sent Events 协议），以异步生成器方式逐字 yield 文本片段。
4. close：异步关闭底层的 HTTP 连接池。
"""

import json
import logging
from typing import AsyncIterator
import httpx

from config.settings import settings
from config.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI 兼容协议的 LLM 客户端"""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        timeout: float = 120.0,
    ):
        self.api_key = api_key or settings.llm_api_key
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model
        
        # 使用 httpx.AsyncClient 异步非阻塞发起网络请求，避免阻塞 Python 事件循环
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=timeout, write=10.0, pool=5.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:
        """
        同步获取模型完整文本输出
        :param messages: 对话历史消息列表 [{"role": "system/user", "content": "..."}]
        :param temperature: 采样温度 (0.0~2.0)，值越高越发散
        :param max_tokens: 最大生成 token 数
        :param response_format: 约束输出格式，例如 {"type": "json_object"}
        :return: 模型回复的文本内容
        """
        try:
            body = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                body["response_format"] = response_format

            resp = await self.client.post(f"{self.base_url}/chat/completions", json=body)
            resp.raise_for_status()

            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise LLMError(f"LLM 调用失败: {e}") from e

    async def chat_json(self, messages: list[dict], temperature: float = 0.7) -> dict:
        """
        请求并解析 JSON 格式响应，具备 Markdown 代码块清洗容错
        :param messages: 对话消息列表
        :param temperature: 采样温度
        :return: 解析后的字典对象
        """
        raw = await self.chat(
            messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # 容错：若大语言模型包裹了 ```json ... ``` 标记，进行截取提取
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            start = clean.find("{")
            end = clean.rfind("}")
            if start != -1 and end != -1:
                clean = clean[start:end + 1]
            return json.loads(clean)

    async def chat_stream(
        self, messages: list[dict], temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        流式获取模型文本输出（SSE 协议解析）
        :param messages: 对话消息列表
        :param temperature: 采样温度
        :return: 异步字符串生成器
        """
        body = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }
        async with self.client.stream("POST", f"{self.base_url}/chat/completions", json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip() or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    content = chunk["choices"][0].get("delta", {}).get("content", "")
                    if content:
                        yield content
                except (KeyError, IndexError, json.JSONDecodeError):
                    continue

    async def close(self):
        """关闭客户端连接池"""
        await self.client.aclose()
