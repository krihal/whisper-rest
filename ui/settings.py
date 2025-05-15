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
    API_URL: str = "http://localhost:8000/api/v1"
    STATIC_FILES: str = "static"


@lru_cache
def get_settings() -> Settings:
    """
    Get the settings for the application.
    """

    # Create static files directory if it doesn't exist
    if not os.path.exists(Settings().STATIC_FILES):
        os.makedirs(Settings().STATIC_FILES)

    return Settings()
