import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Settings for the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_assignment=True,
    )

    DEBUG: bool = True
    API_BROKER_URL: str = "http://localhost:8000"
    API_FILE_STORAGE_DIR: str = "/tmp/downloads"
    TRANSCODER_FILE_STORAGE_DIR: str = "/tmp/transcoder"
    API_VERSION: str = "v1"
    WORKERS: int = 2


@lru_cache
def get_settings() -> Settings:
    """
    Get the settings for the application.
    """
    if not os.path.exists(Settings().API_FILE_STORAGE_DIR):
        os.makedirs(Settings().API_FILE_STORAGE_DIR)
    if not os.path.exists(Settings().TRANSCODER_FILE_STORAGE_DIR):
        os.makedirs(Settings().TRANSCODER_FILE_STORAGE_DIR)

    return Settings()
