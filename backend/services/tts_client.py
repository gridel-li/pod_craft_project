"""
TTS 客户端 — MiMo TTS API
"""

import base64
import logging
import os

from openai import OpenAI

from config.settings import settings
from config.exceptions import TTSError

logger = logging.getLogger(__name__)


class TTSClient:
    """MiMo TTS 客户端"""

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
        """文字 → 音频文件"""
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            voice = voice or self.voice

            messages = []
            if style:
                messages.append({"role": "user", "content": style})
            messages.append({"role": "assistant", "content": text})

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                audio={"format": "wav", "voice": voice},
            )

            audio_bytes = base64.b64decode(completion.choices[0].message.audio.data)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"TTS 完成: {output_path} ({len(audio_bytes)} bytes)")
            return os.path.abspath(output_path)
        except Exception as e:
            logger.error(f"TTS 失败: {e}")
            raise TTSError(f"TTS 失败: {e}") from e

    def synthesize_segments(self, segments: list[dict], output_dir: str, voice: str = "") -> list[str]:
        """批量合成"""
        import uuid
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        for seg in segments:
            filename = f"{seg.get('type', 'seg')}_{uuid.uuid4().hex[:8]}.wav"
            path = os.path.join(output_dir, filename)
            self.synthesize(seg["content"], path, voice=voice)
            paths.append(path)
        return paths
