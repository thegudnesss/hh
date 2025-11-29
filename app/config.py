from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClickSettings(BaseSettings):
    BOT_TOKEN: SecretStr
    MONGO_URL: SecretStr
    DB_CHANNEL: Optional[str] = None
    
    # Click Payment Settings
    CLICK_SERVICE_ID: Optional[str] = None
    CLICK_MERCHANT_ID: Optional[str] = None
    CLICK_MERCHANT_USER_ID: Optional[str] = None
    CLICK_SECRET_KEY: Optional[SecretStr] = None
    CLICK_TEST_MODE: bool = False

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


config = ClickSettings()