"""
MiniMax 音乐生成客户端 — 根据风格生成背景音乐。

API 文档：https://platform.minimaxi.com/docs/guides/music-generation

用法：
  client = MusicClient(api_key="sk-xxx")
  bgm_path = client.generate_bgm(mood="calm", duration_sec=120)
"""

import logging
import os
import time

import httpx

from config.settings import settings
from config.exceptions import PodCraftError

logger = logging.getLogger(__name__)


class MusicError(PodCraftError):
    """音乐生成失败"""
    pass


# 心情 → 音乐风格映射
MOOD_MUSIC_MAP = {
    "neutral": "Gentle acoustic guitar, soft piano, warm and relaxed, ambient",
    "excited": "Upbeat electronic, energetic drums, positive vibes, pop",
    "calm": "Soft piano, ambient pads, peaceful and serene, lo-fi",
    "humorous": "Playful ukulele, light percussion, fun and quirky, comedic",
    "serious": "Cinematic orchestral, deep strings, dramatic and thoughtful",
}

# 风格 → 音乐风格补充
STYLE_MUSIC_MAP = {
    "narrative": "storytelling, cinematic",
    "conversational": "casual, relaxed, easy listening",
    "educational": "focused, clean, minimal",
    "storytelling": "dramatic, atmospheric, emotional",
}


class MusicClient:
    """MiniMax 音乐生成客户端"""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key or settings.minimax_api_key
        self.base_url = (base_url or settings.minimax_base_url).rstrip("/")
        self.model = model or settings.minimax_model
        self.client = httpx.Client(
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    def generate_bgm(
        self,
        mood: str = "neutral",
        style: str = "narrative",
        duration_sec: int = 120,
        output_path: str = "",
    ) -> str:
        """
        生成背景音乐。

        参数：
            mood: 心情（neutral/excited/calm/humorous/serious）
            style: 风格（narrative/conversational/educational/storytelling）
            duration_sec: 期望时长（秒），实际时长由 API 决定
            output_path: 输出文件路径

        返回：音频文件路径
        """
        try:
            # 将产品侧 mood/style 转为供应商更容易理解的英文音乐提示词。
            prompt = self._build_prompt(mood, style)

            logger.info(f"生成背景音乐: mood={mood}, style={style}, prompt={prompt}")

            # 调用 MiniMax API
            payload = {
                "model": self.model,
                "prompt": prompt,
                "is_instrumental": True,  # 纯音乐，无人声
                "audio_setting": {
                    "sample_rate": 44100,
                    "bitrate": 128000,
                    "format": "mp3",
                },
                "output_format": "hex",  # hex 格式直接返回音频数据，不需要下载
            }

            response = self.client.post(
                f"{self.base_url}/v1/music_generation",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            # 检查响应
            base_resp = result.get("base_resp", {})
            if base_resp.get("status_code", -1) != 0:
                raise MusicError(f"MiniMax API 错误: {base_resp.get('status_msg', '未知错误')}")

            # 获取音频数据（hex 格式）：hex 是字节的文本表示，bytes.fromhex 才能还原真实音频。
            audio_hex = result.get("data", {}).get("audio", "")
            if not audio_hex:
                raise MusicError("MiniMax API 未返回音频数据")

            # 确保输出目录存在
            if not output_path:
                output_path = os.path.join(settings.output_dir, f"bgm_{mood}_{int(time.time())}.mp3")
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            # 解码 hex 并写入文件
            audio_bytes = bytes.fromhex(audio_hex)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            duration = result.get("extra_info", {}).get("music_duration", 0) / 1000
            logger.info(f"背景音乐生成完成: {output_path} ({duration:.1f}s)")
            return os.path.abspath(output_path)

        except MusicError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"MiniMax API HTTP 错误: {e}")
            raise MusicError(f"MiniMax API HTTP 错误: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"音乐生成失败: {e}")
            raise MusicError(f"音乐生成失败: {e}") from e

    def _build_prompt(self, mood: str, style: str) -> str:
        """根据心情和风格构建音乐描述"""
        mood_desc = MOOD_MUSIC_MAP.get(mood, MOOD_MUSIC_MAP["neutral"])
        style_desc = STYLE_MUSIC_MAP.get(style, "")
        prompt = f"{mood_desc}, {style_desc}, background music for podcast, instrumental"
        return prompt.strip(", ")

    def close(self):
        """关闭 HTTP 客户端"""
        self.client.close()
