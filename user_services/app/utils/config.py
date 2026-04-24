from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # adjust as needed

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        # env_prefix='APP_',
        extra='ignore'
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: PostgresDsn

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

settings = Settings()
