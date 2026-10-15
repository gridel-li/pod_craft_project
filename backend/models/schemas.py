"""
Pydantic 模型 — API 请求/响应
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 请求模型
# ============================================================

class GenerateRequest(BaseModel):
    """播客生成请求"""
    topic: str = Field(..., min_length=1, max_length=500, description="播客主题")
    mood: str = Field(default="neutral", description="心情/情感基调: neutral/excited/calm/humorous/serious")
    style: str = Field(default="narrative", description="风格: narrative/conversational/educational/storytelling")
    duration_min: int = Field(default=5, ge=1, le=30, description="时长（分钟）")
    voice: str = Field(default="冰糖", description="TTS 语音")
    use_rag: bool = Field(default=True, description="是否使用 RAG 增强")
    custom_prompt: str = Field(default="", description="自定义 Prompt 补充")


class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: str = Field(default="")


class PreferenceUpdateRequest(BaseModel):
    """偏好更新请求"""
    preferred_voice: Optional[str] = None
    preferred_style: Optional[str] = None
    preferred_mood: Optional[str] = None
    tts_speed: Optional[float] = None


# ============================================================
# 响应模型
# ============================================================

class SegmentResponse(BaseModel):
    """片段响应"""
    type: str
    content: str
    duration_sec: float
    audio_path: str = ""


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    topic: str
    mood: str
    style: str
    status: str
    progress: float
    current_step: str
    title: str
    segments: list[SegmentResponse] = []
    audio_path: str = ""
    duration_sec: float = 0.0
    error_message: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: list[TaskResponse]
    total: int


class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    title: str
    source: str
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    """检索响应"""
    query: str
    results: list[dict]
    count: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    database: str
    llm: str
    tts: str


class WorkflowStepResponse(BaseModel):
    """Workflow 步骤响应"""
    name: str
    status: str
    input_summary: str = ""
    output_summary: str = ""
    error: str = ""


class WorkflowResponse(BaseModel):
    """Workflow 执行响应"""
    task_id: str
    success: bool
    steps: list[WorkflowStepResponse]
    final_output: dict = {}
