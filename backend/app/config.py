from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://mis_sim:mis_sim@db:5432/mis_sim"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    # AI providers are deliberately disabled by default.  These are non-secret
    # routing settings only; approved adapters receive credentials out of band.
    AI_PRIMARY_ENABLED: bool = False
    AI_PRIMARY_PROVIDER: str = "dashscope"
    AI_PRIMARY_MODEL: str = "qwen_max"
    AI_PRIMARY_URL: str | None = None
    AI_PRIMARY_TIMEOUT_MS: int = 2000
    AI_FALLBACK_ENABLED: bool = False
    AI_FALLBACK_PROVIDER: str = "together"
    AI_FALLBACK_MODEL: str = "qwen_72b"
    AI_FALLBACK_URL: str | None = None
    AI_FALLBACK_TIMEOUT_MS: int = 3000
    AI_LOCAL_ENABLED: bool = False
    AI_LOCAL_PROVIDER: str = "vllm"
    AI_LOCAL_MODEL: str = "qwen_14b_awq"
    AI_LOCAL_URL: str | None = None
    AI_LOCAL_TIMEOUT_MS: int = 5000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
