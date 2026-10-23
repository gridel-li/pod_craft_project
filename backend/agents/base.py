"""
Agent 基础定义与数据上下文模型

包含两个核心类：
1. AgentContext：存储单个播客生成任务在整个生命周期中的所有数据状态。
2. BaseAgent：所有具体 Agent（情绪分析、内容策划、脚本撰写、质量审查）必须继承的抽象基类。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """
    播客生成任务的数据上下文对象。
    在工作流的整个执行链路中，各个 Agent 和外部服务按顺序读写这同一个上下文对象。

    Python 语法说明：
    - @dataclass: Python 的数据类装饰器，自动生成 __init__ 构造函数，无需手动写赋值语句。
    - field(default_factory=dict/list): 针对字典、列表等可变类型设置默认值。
      必须使用 default_factory，不能直接写 plan: dict = {}，否则所有 AgentContext 实例会共享同一个字典内存地址。
    """

    # 1. 前端传入的初始配置
    topic: str = ""              # 播客主题，例如 "如何缓解职场焦虑"
    mood: str = "neutral"        # 情绪基调：neutral(平和), excited(兴奋), calm(舒缓), humorous(幽默), serious(严肃)
    style: str = "narrative"     # 叙事风格：narrative(叙事), conversational(对话), educational(科普)
    duration_min: int = 5        # 目标时长（分钟）
    voice: str = "冰糖"          # TTS 选用的声音名称
    custom_prompt: str = ""      # 用户填写的自定义补充要求

    # 2. 工作流执行过程中由各个模块填充的数据
    rag_context: str = ""        # RAG 模块从 ChromaDB 检索出的参考资料文本
    plan: dict = field(default_factory=dict)         # ContentPlanner 生成的大纲结构字典
    script: dict = field(default_factory=dict)       # ScriptWriter 生成的完整脚本 JSON 字典
    review_notes: str = ""                           # Reviewer 审查后给出的修改建议文本
    segments: list = field(default_factory=list)     # 分段脚本列表，每个元素包含 type, content, duration_sec
    audio_paths: list = field(default_factory=list)  # TTS 为每个 segment 生成的 wav 音频本地文件路径
    final_audio: str = ""                            # AudioService 混音合并后的最终完整音频文件绝对路径
    metadata: dict = field(default_factory=dict)     # 存放过程数据，例如 mood_strategy, review 原始字典等


class BaseAgent(ABC):
    """
    Agent 抽象基类。
    规范所有子类 Agent 的通用属性和接口。

    Python 语法说明：
    - ABC (Abstract Base Class): 抽象基类。用于定义接口规范，不能直接实例化。
    - @abstractmethod: 抽象方法装饰器。凡是继承 BaseAgent 的子类，必须重写并实现 execute 方法，否则在实例化时会直接抛出 TypeError 异常。
    """

    def __init__(self, name: str, llm_client=None):
        """
        初始化 Agent
        :param name: 当前 Agent 的名称标识，用于日志记录（例如 mood_analyzer, script_writer）
        :param llm_client: LLMClient 实例，用于向大语言模型发送请求
        """
        self.name = name
        self.llm = llm_client
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentContext:
        """
        Agent 的核心执行方法。每个具体的子类必须实现此方法。
        :param context: 输入的数据上下文
        :return: 写入了当前 Agent 执行结果后的上下文
        """
        pass

    async def _llm_chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """调用大模型，获取纯文本字符串响应"""
        return await self.llm.chat(messages, temperature=temperature)

    async def _llm_json(self, messages: list[dict], temperature: float = 0.7) -> dict:
        """调用大模型，并解析大模型返回的内容为 Python 字典（JSON）"""
        return await self.llm.chat_json(messages, temperature=temperature)
