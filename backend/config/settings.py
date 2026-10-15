"""
Application settings — loaded from environment variables.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration"""

    # --- App ---
    app_name: str = "PodCraft"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database ---
    database_url: str = "postgresql+asyncpg://podcraft:podcraft@localhost:5432/podcraft_db"

    # --- JWT ---
    jwt_secret: str = "podcraft-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30

    # --- LLM ---
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"

    # --- TTS (MiMo) ---
    tts_api_key: str = ""
    tts_base_url: str = "https://api.xiaomimimo.com/v1"
    tts_model: str = "mimo-v2.5-tts"
    tts_voice: str = "冰糖"

    # --- RAG ---
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- MiniMax Music ---
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimaxi.com"
    minimax_model: str = "music-2.6-free"

    # --- Audio ---
    output_dir: str = "./output"
    bgm_path: str = "./assets/bgm.mp3"
    silence_ms: int = 1000
    fade_in_ms: int = 2000
    fade_out_ms: int = 3000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
