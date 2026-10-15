"""
音频服务 — 合并、混音、效果处理
"""

import logging
import os

from pydub import AudioSegment

from config.exceptions import AudioError

logger = logging.getLogger(__name__)


class AudioService:
    """音频处理服务"""

    def __init__(self, silence_ms: int = 1000, fade_in_ms: int = 2000, fade_out_ms: int = 3000):
        self.silence_ms = silence_ms
        self.fade_in_ms = fade_in_ms
        self.fade_out_ms = fade_out_ms

    def merge(self, audio_paths: list[str], output_path: str, bgm_path: str = "") -> str:
        """合并多个音频"""
        try:
            if not audio_paths:
                raise AudioError("没有音频文件")

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            silence = AudioSegment.silent(duration=self.silence_ms)

            segments = [AudioSegment.from_wav(p) for p in audio_paths]
            combined = segments[0]
            for seg in segments[1:]:
                combined = combined + silence + seg

            if self.fade_in_ms > 0:
                combined = combined.fade_in(self.fade_in_ms)
            if self.fade_out_ms > 0:
                combined = combined.fade_out(self.fade_out_ms)

            # BGM 混音
            if bgm_path and os.path.exists(bgm_path):
                combined = self._mix_bgm(combined, bgm_path)

            combined.export(output_path, format="wav")
            logger.info(f"音频合并完成: {output_path} ({len(combined)}ms)")
            return os.path.abspath(output_path)
        except AudioError:
            raise
        except Exception as e:
            raise AudioError(f"音频合并失败: {e}") from e

    def _mix_bgm(self, voice: AudioSegment, bgm_path: str, bgm_volume: int = -20) -> AudioSegment:
        """混入背景音乐"""
        try:
            bgm = AudioSegment.from_file(bgm_path)
            bgm = bgm + bgm_volume  # 降低音量
            # 循环 BGM 到语音长度
            while len(bgm) < len(voice):
                bgm = bgm + bgm
            bgm = bgm[:len(voice)]
            return voice.overlay(bgm)
        except Exception as e:
            logger.warning(f"BGM 混音失败，跳过: {e}")
            return voice

    def get_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000
