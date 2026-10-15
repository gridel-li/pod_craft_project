"""
LLM 客户端 — 统一封装 DeepSeek/MiMo 等 OpenAI 兼容 API
"""

import json
import logging
from typing import AsyncIterator

import httpx

from config.settings import settings
from config.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM API 客户端"""

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
        """普通调用"""
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
        """调用并解析 JSON 响应"""
        raw = await self.chat(messages, temperature=temperature, response_format={"type": "json_object"})
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # 尝试清理
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
        """流式调用"""
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
        await self.client.aclose()
