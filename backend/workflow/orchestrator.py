"""
WorkflowOrchestrator — 播客生成工作流主编排器

功能说明：
串联播客生成的完整生命周期，按固定业务步骤依次调用：
1. RAGService：检索向量数据库中的参考资料
2. MoodAnalyzerAgent：分析主题与情绪，输出内容调优策略
3. ContentPlannerAgent：生成分段大纲与各段时长规划
4. ScriptWriterAgent：生成具体口语分段台词脚本
5. ReviewerAgent：对脚本进行质量审查
6. TTSClient：将各段台词文本逐段合成为独立的 WAV 音频文件
7. MusicClient：调用音乐模型生成匹配情绪的背景音乐（支持失败优雅降级）
8. AudioService：将各人声音频拼接并混入背景音乐，输出最终播客音频
"""

import logging
import uuid

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

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """工作流编排器：按序协调各个 Agent 与外部音视频服务"""

    def __init__(self):
        # 1. 外部服务客户端初始化
        self.llm = LLMClient()
        self.tts = TTSClient()
        self.music = MusicClient()
        self.audio = AudioService(
            silence_ms=settings.silence_ms,
            fade_in_ms=settings.fade_in_ms,
            fade_out_ms=settings.fade_out_ms,
        )
        self.rag = RAGService()

        # 2. 四个 Agent 初始化并注入统一的 LLM 客户端
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
        """
        执行播客生成流水线
        :param topic: 播客主题
        :param mood: 情绪基调 (neutral, excited, calm, humorous, serious)
        :param style: 风格 (narrative, conversational, educational, storytelling)
        :param duration_min: 目标时长（分钟）
        :param voice: 配音音色
        :param use_rag: 是否启用知识库检索
        :param custom_prompt: 用户自定义要求
        :param progress_callback: 异步回调函数 (step: str, status: str, progress: int)，向调用方上报进度
        :return: 包含 task_id, success, segments, audio_path, duration_sec, steps 的字典
        """
        task_id = uuid.uuid4().hex[:8]
        steps = []

        try:
            # 步骤 0: 初始化数据上下文
            ctx = AgentContext(
                topic=topic,
                mood=mood,
                style=style,
                duration_min=duration_min,
                voice=voice or settings.tts_voice,
                custom_prompt=custom_prompt,
            )

            # 步骤 1: RAG 知识检索
            if use_rag:
                await self._report(progress_callback, "rag", "running", 10)
                ctx.rag_context = self.rag.get_context(topic, top_k=5)
                steps.append({
                    "name": "rag",
                    "status": "completed",
                    "output": f"检索到 {len(ctx.rag_context)} 字"
                })
                await self._report(progress_callback, "rag", "completed", 15)

            # 步骤 2: 情绪与调优策略分析
            await self._report(progress_callback, "mood_analysis", "running", 20)
            ctx = await self.mood_agent.execute(ctx)
            steps.append({
                "name": "mood_analysis",
                "status": "completed",
                "output": ctx.metadata.get("mood_strategy", {}).get("tone", "")
            })
            await self._report(progress_callback, "mood_analysis", "completed", 30)

            # 步骤 3: 内容与结构规划
            await self._report(progress_callback, "planning", "running", 35)
            ctx = await self.planner_agent.execute(ctx)
            steps.append({
                "name": "planning",
                "status": "completed",
                "output": ctx.plan.get("title", "")
            })
            await self._report(progress_callback, "planning", "completed", 45)

            # 步骤 4: 分段脚本撰写
            await self._report(progress_callback, "writing", "running", 50)
            ctx = await self.writer_agent.execute(ctx)
            steps.append({
                "name": "writing",
                "status": "completed",
                "output": f"{len(ctx.segments)} 个片段"
            })
            await self._report(progress_callback, "writing", "completed", 65)

            # 步骤 5: 脚本质量审查
            await self._report(progress_callback, "reviewing", "running", 70)
            ctx = await self.reviewer_agent.execute(ctx)
            steps.append({
                "name": "reviewing",
                "status": "completed",
                "output": ctx.review_notes
            })
            await self._report(progress_callback, "reviewing", "completed", 75)

            # 步骤 6: TTS 分段语音合成
            await self._report(progress_callback, "synthesizing", "running", 78)
            output_dir = f"{settings.output_dir}/{task_id}"
            ctx.audio_paths = self.tts.synthesize_segments(
                ctx.segments, output_dir, voice=ctx.voice
            )
            steps.append({
                "name": "synthesizing",
                "status": "completed",
                "output": f"{len(ctx.audio_paths)} 个音频"
            })
            await self._report(progress_callback, "synthesizing", "completed", 85)

            # 步骤 7: 背景音乐生成（具备异常隔离与优雅降级机制）
            await self._report(progress_callback, "bgm", "running", 87)
            bgm_path = f"{output_dir}/bgm.mp3"
            try:
                bgm_path = self.music.generate_bgm(
                    mood=mood,
                    style=style,
                    duration_sec=duration_min * 60,
                    output_path=bgm_path,
                )
                steps.append({"name": "bgm", "status": "completed", "output": "背景音乐生成成功"})
                logger.info(f"[{task_id}] 背景音乐生成成功: {bgm_path}")
            except Exception as e:
                # BGM 为增强功能，生成失败时降级为空路径，不阻断主流程
                logger.warning(f"[{task_id}] 背景音乐生成失败，降级跳过: {e}")
                bgm_path = ""
                steps.append({"name": "bgm", "status": "skipped", "output": f"跳过: {e}"})
            await self._report(progress_callback, "bgm", "completed", 92)

            # 步骤 8: 音频混音与格式导出
            await self._report(progress_callback, "merging", "running", 94)
            final_path = f"{settings.output_dir}/{task_id}.wav"
            ctx.final_audio = self.audio.merge(ctx.audio_paths, final_path, bgm_path=bgm_path)
            duration_sec = self.audio.get_duration(final_path)
            steps.append({
                "name": "merging",
                "status": "completed",
                "output": f"{duration_sec:.1f}s"
            })
            await self._report(progress_callback, "merging", "completed", 100)

            # 返回任务成功执行结果
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
            # 捕获异常并返回带有错误信息的字典
            logger.error(f"Workflow 执行失败: {e}", exc_info=True)
            steps.append({"name": "error", "status": "failed", "output": str(e)})
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "steps": steps,
            }

    async def _report(self, callback, step: str, status: str, progress: int):
        """执行进度上报回调函数"""
        if callback:
            await callback(step, status, progress)
