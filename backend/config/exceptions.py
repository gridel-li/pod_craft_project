"""自定义异常"""


class PodCraftError(Exception):
    """项目基础异常"""
    pass


class LLMError(PodCraftError):
    """LLM 调用失败"""
    pass


class TTSError(PodCraftError):
    """TTS 调用失败"""
    pass


class RAGError(PodCraftError):
    """RAG 操作失败"""
    pass


class WorkflowError(PodCraftError):
    """Workflow 执行失败"""
    pass


class AudioError(PodCraftError):
    """音频处理失败"""
    pass


class DatabaseError(PodCraftError):
    """数据库操作失败"""
    pass
