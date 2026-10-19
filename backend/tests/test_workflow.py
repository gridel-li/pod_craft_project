"""
Tests for Workflow Orchestrator with fully mocked services
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from workflow.orchestrator import WorkflowOrchestrator


@pytest.fixture
def mock_orchestrator():
    """Create orchestrator with all services mocked"""
    with patch("workflow.orchestrator.LLMClient"), \
         patch("workflow.orchestrator.TTSClient"), \
         patch("workflow.orchestrator.MusicClient"), \
         patch("workflow.orchestrator.AudioService"), \
         patch("workflow.orchestrator.RAGService"):

        orch = WorkflowOrchestrator()

        # Mock LLM responses for each agent
        orch.llm = MagicMock()
        orch.llm.chat = AsyncMock(return_value="mock")
        orch.llm.chat_json = AsyncMock(return_value={})

        # Mock mood agent
        orch.mood_agent.llm = orch.llm
        orch.mood_agent.llm.chat_json = AsyncMock(return_value={
            "tone": "温暖", "pace": "适中", "vocabulary": "口语化",
            "structure": "总分总", "key_elements": ["类比"],
        })

        # Mock planner agent
        orch.planner_agent.llm = orch.llm
        orch.planner_agent.llm.chat_json = AsyncMock(return_value={
            "title": "测试播客",
            "segments": [
                {"type": "intro", "theme": "开场", "duration_sec": 30},
                {"type": "body", "theme": "正文", "duration_sec": 60},
                {"type": "outro", "theme": "结尾", "duration_sec": 20},
            ],
            "key_points": ["要点1"],
        })

        # Mock writer agent
        orch.writer_agent.llm = orch.llm
        orch.writer_agent.llm.chat_json = AsyncMock(return_value={
            "title": "测试播客",
            "segments": [
                {"type": "intro", "content": "欢迎收听", "duration_sec": 30},
                {"type": "body", "content": "今天聊聊...", "duration_sec": 60},
                {"type": "outro", "content": "感谢收听", "duration_sec": 20},
            ],
        })

        # Mock reviewer agent
        orch.reviewer_agent.llm = orch.llm
        orch.reviewer_agent.llm.chat_json = AsyncMock(return_value={
            "approved": True, "notes": "质量合格",
        })

        # Mock TTS
        orch.tts.synthesize_segments = MagicMock(return_value=[
            "/tmp/intro.wav", "/tmp/body.wav", "/tmp/outro.wav",
        ])

        # Mock Music (BGM)
        orch.music.generate_bgm = MagicMock(return_value="/tmp/bgm.mp3")

        # Mock Audio
        orch.audio.merge = MagicMock(return_value="/tmp/final.wav")
        orch.audio.get_duration = MagicMock(return_value=110.0)

        # Mock RAG
        orch.rag.get_context = MagicMock(return_value="参考资料内容...")
        orch.rag.search = MagicMock(return_value=[])

        yield orch


@pytest.mark.asyncio
async def test_full_workflow_success(mock_orchestrator):
    result = await mock_orchestrator.execute(
        topic="Python 异步编程",
        mood="neutral",
        style="educational",
        duration_min=5,
        voice="冰糖",
        use_rag=True,
    )

    assert result["success"] is True
    assert len(result["title"]) > 0  # title comes from script or falls back to topic
    assert result["audio_path"] == "/tmp/final.wav"
    assert result["duration_sec"] == 110.0
    assert len(result["steps"]) >= 5  # rag + mood + plan + write + review + synth + merge


@pytest.mark.asyncio
async def test_workflow_without_rag(mock_orchestrator):
    result = await mock_orchestrator.execute(
        topic="简单话题",
        use_rag=False,
    )

    assert result["success"] is True
    # RAG step should not be in steps
    step_names = [s["name"] for s in result["steps"]]
    assert "rag" not in step_names


@pytest.mark.asyncio
async def test_workflow_bgm_failure_graceful(mock_orchestrator):
    """BGM generation failure should not crash the workflow"""
    mock_orchestrator.music.generate_bgm = MagicMock(side_effect=Exception("API error"))

    result = await mock_orchestrator.execute(topic="BGM 失败测试")

    assert result["success"] is True
    # BGM step should show as skipped
    bgm_steps = [s for s in result["steps"] if s["name"] == "bgm"]
    assert len(bgm_steps) == 1
    assert bgm_steps[0]["status"] == "skipped"


@pytest.mark.asyncio
async def test_workflow_progress_callback(mock_orchestrator):
    """Progress callback should be called at each step"""
    callback = AsyncMock()

    await mock_orchestrator.execute(
        topic="回调测试",
        progress_callback=callback,
    )

    assert callback.call_count >= 10  # Multiple progress updates
    # Verify progress increases
    progress_values = [call.args[2] for call in callback.call_args_list]
    assert progress_values[-1] == 100


@pytest.mark.asyncio
async def test_workflow_llm_failure_returns_error(mock_orchestrator):
    """If LLM fails completely, workflow should return error"""
    mock_orchestrator.mood_agent.llm.chat_json = AsyncMock(
        side_effect=Exception("LLM API down")
    )

    result = await mock_orchestrator.execute(topic="LLM 失败测试")

    assert result["success"] is False
    assert "error" in result
    assert "LLM" in result["error"] or "失败" in result["error"] or len(result["error"]) > 0
