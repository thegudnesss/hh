from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    MONGO_URL: SecretStr
    DB_CHANNEL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file = "bot/data/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


config = Settings()