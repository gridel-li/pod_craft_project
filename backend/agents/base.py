"""
Agent 基类 — 所有 Agent 的基础
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Agent 执行上下文"""
    topic: str = ""
    mood: str = "neutral"
    style: str = "narrative"
    duration_min: int = 5
    voice: str = "冰糖"
    custom_prompt: str = ""
    rag_context: str = ""
    plan: dict = field(default_factory=dict)
    script: dict = field(default_factory=dict)
    review_notes: str = ""
    segments: list = field(default_factory=list)
    audio_paths: list = field(default_factory=list)
    final_audio: str = ""
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, name: str, llm_client=None):
        self.name = name
        self.llm = llm_client
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentContext:
        """执行 Agent 任务"""
        pass

    async def _llm_chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """调用 LLM"""
        return await self.llm.chat(messages, temperature=temperature)

    async def _llm_json(self, messages: list[dict], temperature: float = 0.7) -> dict:
        """调用 LLM 并解析 JSON"""
        return await self.llm.chat_json(messages, temperature=temperature)
