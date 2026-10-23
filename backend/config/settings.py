"""
全局配置定义

所有配置项都从环境变量或 backend/.env 文件读取（由 pydantic-settings 完成）。
字段名与环境变量名一致、大小写不敏感，例如 llm_api_key 对应 .env 中的 LLM_API_KEY。

每一项配置的实际读取位置都写在注释里，便于确认「改了到底会不会生效」。
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置集合"""

    # --- 应用基础信息 ---
    app_name: str = "PodCraft"          # 服务名称，出现在启动日志与 FastAPI 文档标题（main.py）
    app_version: str = "1.0.0"          # 版本号，/api/health 与根路径返回（api/routes.py、main.py）
    debug: bool = False                 # 为 True 时日志降为 DEBUG，并让 SQLAlchemy 打印每条 SQL（main.py、models/database.py）
    host: str = "0.0.0.0"               # 监听地址，仅在直接运行 main.py 时使用
    port: int = 8000                    # 监听端口，仅在直接运行 main.py 时使用

    # --- 数据库 ---
    # 必须是异步驱动（postgresql+asyncpg），因为项目全程使用 AsyncSession。
    # 本地不想装 PostgreSQL 时可改为 sqlite+aiosqlite:///./data/podcraft.db
    database_url: str = "postgresql+asyncpg://podcraft:podcraft@localhost:5432/podcraft_db"

    # --- JWT 登录令牌 ---
    jwt_secret: str = "podcraft-secret-key-change-in-production"  # 签名密钥，生产环境必须更换（models/user.py）
    jwt_algorithm: str = "HS256"        # 签名算法（models/user.py）
    jwt_expire_days: int = 30           # 令牌有效期，单位天（models/user.py）

    # --- 大语言模型（OpenAI 兼容接口）---
    llm_api_key: str = ""               # 为空时所有 Agent 调用都会失败（services/llm_client.py）
    llm_base_url: str = "https://api.deepseek.com/v1"  # 接口地址，末尾不带 /chat/completions
    llm_model: str = "deepseek-chat"    # 模型名称

    # --- TTS 语音合成 ---
    tts_api_key: str = ""               # 为空时回退使用 llm_api_key（services/tts_client.py）
    tts_base_url: str = "https://api.xiaomimimo.com/v1"
    tts_model: str = "mimo-v2.5-tts"
    tts_voice: str = "冰糖"             # 默认音色，前端未传 voice 时使用（workflow/orchestrator.py）

    # --- RAG 向量库 ---
    chroma_persist_dir: str = "./data/chroma"  # ChromaDB 本地持久化目录（rag/service.py）
    # 说明：embedding_model 目前在代码中未被读取。
    # 向量由 ChromaDB 内置的默认 embedding 函数计算；如需更换必须在 rag/service.py 里显式传入 embedding_function。
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- MiniMax 背景音乐生成 ---
    minimax_api_key: str = ""           # 为空时 BGM 生成会失败，但工作流会降级跳过（services/music_client.py）
    minimax_base_url: str = "https://api.minimaxi.com"
    minimax_model: str = "music-2.6-free"

    # --- 音频处理 ---
    output_dir: str = "./output"        # 音频产物目录，同时被挂载为 /files 静态资源（main.py、workflow/orchestrator.py）
    # 说明：bgm_path 目前在代码中未被读取。
    # 背景音乐由 MusicClient 实时生成到 output/{task_id}/bgm.mp3，不会使用这个预置文件。
    bgm_path: str = "./assets/bgm.mp3"
    silence_ms: int = 1000              # 段落之间的静音时长，毫秒（services/audio_service.py）
    fade_in_ms: int = 2000              # 开头淡入时长，毫秒（services/audio_service.py）
    fade_out_ms: int = 3000             # 结尾淡出时长，毫秒（services/audio_service.py）

    model_config = {
        "env_file": ".env",             # 从 backend/.env 读取
        "env_file_encoding": "utf-8",
    }


# 模块级单例：其他文件统一 from config.settings import settings，共享同一个对象
settings = Settings()
