"""
Tests for Agent logic with mocked LLM client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.base import AgentContext
from agents.mood_analyzer import MoodAnalyzerAgent
from agents.content_planner import ContentPlannerAgent
from agents.script_writer import ScriptWriterAgent
from agents.reviewer import ReviewerAgent


@pytest.fixture
def mock_llm():
    """Create a mock LLM client"""
    llm = MagicMock()
    llm.chat = AsyncMock(return_value="mock response")
    llm.chat_json = AsyncMock(return_value={})
    return llm


@pytest.fixture
def base_context():
    """Create a base agent context for testing"""
    return AgentContext(
        topic="Python 异步编程入门",
        mood="neutral",
        style="educational",
        duration_min=5,
        voice="冰糖",
    )


# ============================================================
# MoodAnalyzerAgent Tests
# ============================================================

@pytest.mark.asyncio
async def test_mood_analyzer_returns_strategy(mock_llm, base_context):
    mock_llm.chat_json.return_value = {
        "tone": "温暖轻松",
        "pace": "中等偏慢",
        "vocabulary": "口语化",
        "structure": "总分总",
        "key_elements": ["类比", "代码示例"],
    }
    agent = MoodAnalyzerAgent(mock_llm)
    result = await agent.execute(base_context)

    assert "mood_strategy" in result.metadata
    assert result.metadata["mood_strategy"]["tone"] == "温暖轻松"
    mock_llm.chat_json.assert_called_once()


@pytest.mark.asyncio
async def test_mood_analyzer_with_different_moods(mock_llm, base_context):
    mock_llm.chat_json.return_value = {"tone": "energetic", "pace": "fast"}

    for mood in ["excited", "calm", "humorous", "serious", "neutral"]:
        base_context.mood = mood
        agent = MoodAnalyzerAgent(mock_llm)
        result = await agent.execute(base_context)
        assert "mood_strategy" in result.metadata


# ============================================================
# ContentPlannerAgent Tests
# ============================================================

@pytest.mark.asyncio
async def test_content_planner_creates_plan(mock_llm, base_context):
    mock_llm.chat_json.return_value = {
        "title": "异步编程揭秘",
        "subtitle": "从入门到精通",
        "segments": [
            {"type": "intro", "theme": "什么是异步", "duration_sec": 30},
            {"type": "body", "theme": "asyncio 基础", "duration_sec": 120},
            {"type": "outro", "theme": "总结", "duration_sec": 20},
        ],
        "key_points": ["事件循环", "协程"],
    }
    agent = ContentPlannerAgent(mock_llm)
    result = await agent.execute(base_context)

    assert result.plan["title"] == "异步编程揭秘"
    assert len(result.plan["segments"]) == 3


@pytest.mark.asyncio
async def test_content_planner_with_rag_context(mock_llm, base_context):
    base_context.rag_context = "Python asyncio 是一个标准库模块..."
    mock_llm.chat_json.return_value = {
        "title": "Test",
        "segments": [{"type": "intro", "theme": "开场", "duration_sec": 30}],
        "key_points": [],
    }
    agent = ContentPlannerAgent(mock_llm)
    await agent.execute(base_context)

    # Verify the RAG context was included in the prompt
    call_args = mock_llm.chat_json.call_args
    messages = call_args[0][0]
    prompt_text = messages[-1]["content"]
    assert "参考资料" in prompt_text


# ============================================================
# ScriptWriterAgent Tests
# ============================================================

@pytest.mark.asyncio
async def test_script_writer_generates_segments(mock_llm, base_context):
    base_context.plan = {
        "title": "异步编程揭秘",
        "segments": [
            {"type": "intro", "theme": "开场", "duration_sec": 30},
            {"type": "body", "theme": "正文", "duration_sec": 120},
        ],
    }
    mock_llm.chat_json.return_value = {
        "title": "异步编程揭秘",
        "segments": [
            {"type": "intro", "content": "大家好，欢迎收听...", "duration_sec": 30},
            {"type": "body", "content": "异步编程其实...", "duration_sec": 120},
        ],
    }
    agent = ScriptWriterAgent(mock_llm)
    result = await agent.execute(base_context)

    assert len(result.segments) == 2
    assert result.segments[0]["type"] == "intro"
    assert result.script["title"] == "异步编程揭秘"


# ============================================================
# ReviewerAgent Tests
# ============================================================

@pytest.mark.asyncio
async def test_reviewer_approves_good_script(mock_llm, base_context):
    base_context.segments = [
        {"type": "intro", "content": "大家好", "duration_sec": 30},
        {"type": "body", "content": "今天聊聊异步编程", "duration_sec": 120},
        {"type": "outro", "content": "感谢收听", "duration_sec": 20},
    ]
    mock_llm.chat_json.return_value = {
        "approved": True,
        "notes": "质量合格，内容连贯",
    }
    agent = ReviewerAgent(mock_llm)
    result = await agent.execute(base_context)

    assert result.metadata["review"]["approved"] is True
    assert result.review_notes == "质量合格，内容连贯"


@pytest.mark.asyncio
async def test_reviewer_rejects_with_suggestions(mock_llm, base_context):
    base_context.segments = [
        {"type": "intro", "content": "一段话", "duration_sec": 10},
    ]
    mock_llm.chat_json.return_value = {
        "approved": False,
        "notes": "内容过短，缺少正文和结尾",
        "suggestions": ["增加正文段落", "补充结尾"],
    }
    agent = ReviewerAgent(mock_llm)
    result = await agent.execute(base_context)

    assert result.metadata["review"]["approved"] is False
    assert "suggestions" in result.metadata["review"]
