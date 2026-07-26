"""Configuration module for LLM Service."""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.app_host: str = os.getenv("APP_HOST", "0.0.0.0")
        self.app_port: int = int(os.getenv("APP_PORT", "8000"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_format: str = os.getenv("LOG_FORMAT", "default")

        # LLM API Keys
        self.yandex_cloud_api_key: Optional[str] = os.getenv("YANDEX_CLOUD_API_KEY")
        self.yandex_cloud_folder: Optional[str] = os.getenv("YANDEX_CLOUD_FOLDER")
        self.yandex_cloud_model: Optional[str] = os.getenv("YANDEX_CLOUD_MODEL")

        # Redis Settings
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_host: str = os.getenv("REDIS_HOST", "localhost")
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db: int = int(os.getenv("REDIS_DB", "0"))


settings = Settings()