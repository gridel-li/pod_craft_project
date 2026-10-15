"""
Workflow 编排器 — 协调所有 Agent 完成播客生成
"""

import logging
import uuid
from datetime import datetime

from agents.base import AgentContext
from agents.mood_analyzer import MoodAnalyzerAgent
from agents.content_planner import ContentPlannerAgent
from agents.script_writer import ScriptWriterAgent
from agents.reviewer import ReviewerAgent
from services.llm_client import LLMClient
from services.tts_client import TTSClient
from services.audio_service import AudioService
from services.music_client import MusicClient
from rag.service import RAGService
from config.settings import settings
from config.exceptions import WorkflowError

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Workflow 编播器"""

    def __init__(self):
        self.llm = LLMClient()
        self.tts = TTSClient()
        self.music = MusicClient()
        self.audio = AudioService(
            silence_ms=settings.silence_ms,
            fade_in_ms=settings.fade_in_ms,
            fade_out_ms=settings.fade_out_ms,
        )
        self.rag = RAGService()

        # 初始化 Agents
        self.mood_agent = MoodAnalyzerAgent(self.llm)
        self.planner_agent = ContentPlannerAgent(self.llm)
        self.writer_agent = ScriptWriterAgent(self.llm)
        self.reviewer_agent = ReviewerAgent(self.llm)

    async def execute(
        self,
        topic: str,
        mood: str = "neutral",
        style: str = "narrative",
        duration_min: int = 5,
        voice: str = "",
        use_rag: bool = True,
        custom_prompt: str = "",
        progress_callback=None,
    ) -> dict:
        """执行完整的播客生成 Workflow"""
        task_id = uuid.uuid4().hex[:8]
        steps = []

        try:
            # 初始化上下文
            ctx = AgentContext(
                topic=topic, mood=mood, style=style,
                duration_min=duration_min, voice=voice or settings.tts_voice,
                custom_prompt=custom_prompt,
            )

            # Step 1: RAG 检索
            if use_rag:
                await self._report(progress_callback, "rag", "running", 10)
                ctx.rag_context = self.rag.get_context(topic, top_k=5)
                steps.append({"name": "rag", "status": "completed", "output": f"检索到 {len(ctx.rag_context)} 字"})
                await self._report(progress_callback, "rag", "completed", 15)

            # Step 2: 心情分析
            await self._report(progress_callback, "mood_analysis", "running", 20)
            ctx = await self.mood_agent.execute(ctx)
            steps.append({"name": "mood_analysis", "status": "completed", "output": ctx.metadata.get("mood_strategy", {}).get("tone", "")})
            await self._report(progress_callback, "mood_analysis", "completed", 30)

            # Step 3: 内容规划
            await self._report(progress_callback, "planning", "running", 35)
            ctx = await self.planner_agent.execute(ctx)
            steps.append({"name": "planning", "status": "completed", "output": ctx.plan.get("title", "")})
            await self._report(progress_callback, "planning", "completed", 45)

            # Step 4: 脚本生成
            await self._report(progress_callback, "writing", "running", 50)
            ctx = await self.writer_agent.execute(ctx)
            steps.append({"name": "writing", "status": "completed", "output": f"{len(ctx.segments)} 个片段"})
            await self._report(progress_callback, "writing", "completed", 65)

            # Step 5: 质量审查
            await self._report(progress_callback, "reviewing", "running", 70)
            ctx = await self.reviewer_agent.execute(ctx)
            steps.append({"name": "reviewing", "status": "completed", "output": ctx.review_notes})
            await self._report(progress_callback, "reviewing", "completed", 75)

            # Step 6: TTS 合成
            await self._report(progress_callback, "synthesizing", "running", 78)
            output_dir = f"{settings.output_dir}/{task_id}"
            ctx.audio_paths = self.tts.synthesize_segments(ctx.segments, output_dir, voice=ctx.voice)
            steps.append({"name": "synthesizing", "status": "completed", "output": f"{len(ctx.audio_paths)} 个音频"})
            await self._report(progress_callback, "synthesizing", "completed", 85)

            # Step 7: 生成背景音乐
            await self._report(progress_callback, "bgm", "running", 87)
            bgm_path = f"{output_dir}/bgm.mp3"
            try:
                bgm_path = self.music.generate_bgm(
                    mood=mood, style=style,
                    duration_sec=duration_min * 60,
                    output_path=bgm_path,
                )
                steps.append({"name": "bgm", "status": "completed", "output": "背景音乐生成成功"})
                logger.info(f"[{task_id}] 背景音乐生成成功: {bgm_path}")
            except Exception as e:
                logger.warning(f"[{task_id}] 背景音乐生成失败，跳过: {e}")
                bgm_path = ""
                steps.append({"name": "bgm", "status": "skipped", "output": f"跳过: {e}"})
            await self._report(progress_callback, "bgm", "completed", 92)

            # Step 8: 音频合并（语音 + BGM）
            await self._report(progress_callback, "merging", "running", 94)
            final_path = f"{settings.output_dir}/{task_id}.wav"
            ctx.final_audio = self.audio.merge(ctx.audio_paths, final_path, bgm_path=bgm_path)
            duration_sec = self.audio.get_duration(final_path)
            steps.append({"name": "merging", "status": "completed", "output": f"{duration_sec:.1f}s"})
            await self._report(progress_callback, "merging", "completed", 100)

            return {
                "task_id": task_id,
                "success": True,
                "title": ctx.script.get("title", topic),
                "segments": ctx.segments,
                "audio_path": ctx.final_audio,
                "duration_sec": duration_sec,
                "steps": steps,
            }

        except Exception as e:
            logger.error(f"Workflow 失败: {e}", exc_info=True)
            steps.append({"name": "error", "status": "failed", "output": str(e)})
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "steps": steps,
            }

    async def _report(self, callback, step: str, status: str, progress: int):
        if callback:
            await callback(step, status, progress)
