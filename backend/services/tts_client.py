"""
TTSClient — 语音合成客户端

功能说明：
封装基于 OpenAI 协议的语音合成（Text-to-Speech）接口。
主要方法：
1. synthesize：将单段文字合成为 WAV 音频并写入本地磁盘。
2. synthesize_segments：遍历脚本列表，批量调用 synthesize 并返回生成文件的路径列表。
"""

import base64
import logging
import os
import uuid
from openai import OpenAI

from config.settings import settings
from config.exceptions import TTSError

logger = logging.getLogger(__name__)


class TTSClient:
    """TTS 语音合成客户端"""

    # 内置支持的中英文音色表
    VOICES = {
        "冰糖": "冰糖", "茉莉": "茉莉", "苏打": "苏打", "白桦": "白桦",
        "Mia": "Mia", "Chloe": "Chloe", "Milo": "Milo", "Dean": "Dean",
    }

    def __init__(self, api_key: str = "", base_url: str = "", model: str = "", voice: str = ""):
        self.api_key = api_key or settings.tts_api_key or settings.llm_api_key
        self.base_url = base_url or settings.tts_base_url
        self.model = model or settings.tts_model
        self.voice = voice or settings.tts_voice
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def synthesize(self, text: str, output_path: str, voice: str = "", style: str = "") -> str:
        """
        单句语音合成并保存为本地文件
        :param text: 待合成的文本
        :param output_path: 输出音频文件绝对或相对路径
        :param voice: 音色名称（如 冰糖）
        :param style: 风格提示语（可选）
        :return: 生成的音频文件绝对路径
        """
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            voice = voice or self.voice

            messages = []
            if style:
                messages.append({"role": "user", "content": style})
            messages.append({"role": "assistant", "content": text})

            # 调用接口请求音频数据
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                audio={"format": "wav", "voice": voice},
            )

            # 接口返回 base64 编码的音频字节串，需进行解码
            audio_bytes = base64.b64decode(completion.choices[0].message.audio.data)

            # 以二进制只写模式 ("wb") 写入文件
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"TTS 合成完成: {output_path} ({len(audio_bytes)} 字节)")
            return os.path.abspath(output_path)

        except Exception as e:
            logger.error(f"TTS 合成失败: {e}")
            raise TTSError(f"TTS 失败: {e}") from e

    def synthesize_segments(self, segments: list[dict], output_dir: str, voice: str = "") -> list[str]:
        """
        批量合成所有脚本分段
        :param segments: 包含 content 和 type 的分段字典列表
        :param output_dir: 输出目录路径
        :param voice: 音色
        :return: 合成的音频文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        for seg in segments:
            seg_type = seg.get("type", "seg")
            filename = f"{seg_type}_{uuid.uuid4().hex[:8]}.wav"
            path = os.path.join(output_dir, filename)
            self.synthesize(seg["content"], path, voice=voice)
            paths.append(path)
        return paths
