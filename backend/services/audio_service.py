"""
AudioService — 音频处理与混音服务

功能说明：
使用 pydub 库完成播客语音片段的连接、停顿插入、淡入淡出与背景音乐混音。
主要方法：
1. merge：接收多个语音 wav 文件路径，在各片段之间插入静音，并叠加背景音乐，导出为目标 wav 文件。
2. _mix_bgm：将背景音乐音量衰减后，循环对齐到人声总长度并进行波形叠加（overlay）。
3. get_duration：读取音频文件的时长（秒）。
"""

import logging
import os
from pydub import AudioSegment
from config.exceptions import AudioError

logger = logging.getLogger(__name__)


class AudioService:
    """音频处理与混音服务"""

    def __init__(self, silence_ms: int = 1000, fade_in_ms: int = 2000, fade_out_ms: int = 3000):
        """
        初始化音频参数（单位均为毫秒 ms）
        :param silence_ms: 片段之间的静音停顿长度（默认 1000ms = 1秒）
        :param fade_in_ms: 开头淡入时长
        :param fade_out_ms: 结尾淡出时长
        """
        self.silence_ms = silence_ms
        self.fade_in_ms = fade_in_ms
        self.fade_out_ms = fade_out_ms

    def merge(self, audio_paths: list[str], output_path: str, bgm_path: str = "") -> str:
        """
        合并多个音频文件并叠加背景音乐
        :param audio_paths: 待合并的语音文件路径列表
        :param output_path: 输出音频文件的目标路径
        :param bgm_path: 背景音乐文件路径（可选）
        :return: 合成文件的绝对路径
        """
        try:
            if not audio_paths:
                raise AudioError("没有音频文件")

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            # 构造指定时长的静音片段
            silence = AudioSegment.silent(duration=self.silence_ms)

            # 将 wav 文件加载为内存中的 AudioSegment 音频波形对象
            segments = [AudioSegment.from_wav(p) for p in audio_paths]

            # 串行拼接：第 1 段 + 静音 + 第 2 段 + 静音 ...
            combined = segments[0]
            for seg in segments[1:]:
                combined = combined + silence + seg

            # 音频首尾渐变效果
            if self.fade_in_ms > 0:
                combined = combined.fade_in(self.fade_in_ms)
            if self.fade_out_ms > 0:
                combined = combined.fade_out(self.fade_out_ms)

            # 混入背景音乐
            if bgm_path and os.path.exists(bgm_path):
                combined = self._mix_bgm(combined, bgm_path)

            # 导出为 WAV 格式
            combined.export(output_path, format="wav")
            logger.info(f"音频合并完成: {output_path} ({len(combined)}ms)")
            return os.path.abspath(output_path)

        except AudioError:
            raise
        except Exception as e:
            raise AudioError(f"音频合并失败: {e}") from e

    def _mix_bgm(self, voice: AudioSegment, bgm_path: str, bgm_volume: int = -20) -> AudioSegment:
        """
        将背景音乐与人声混音
        :param voice: 拼接好的人声音频对象
        :param bgm_path: 背景音乐文件路径
        :param bgm_volume: 音乐音量调整值（dB，负数表示降低音量）
        :return: 混音后的音频对象
        """
        try:
            bgm = AudioSegment.from_file(bgm_path)
            bgm = bgm + bgm_volume  # 降低背景音乐音量，避免掩盖人声

            # 若背景音乐时长不足人声总长，循环拼接
            while len(bgm) < len(voice):
                bgm = bgm + bgm

            # 裁剪背景音乐，使其长度与人声严格一致
            bgm = bgm[:len(voice)]

            # overlay：在人声音轨上叠加背景音乐音轨
            return voice.overlay(bgm)
        except Exception as e:
            logger.warning(f"BGM 混音失败，跳过: {e}")
            return voice

    def get_duration(self, audio_path: str) -> float:
        """获取指定音频文件的时长（秒）"""
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0
