from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    app_name: str = "AlgoRecall"
    app_env: str = "development"
    app_timezone: str = "Asia/Shanghai"
    database_url: str = f"sqlite:///{(ROOT_DIR / 'data' / 'algorecall.db').as_posix()}"
    host: str = "127.0.0.1"
    port: int = 8000
    notifications_enabled: bool = True
    notification_time: str = "08:00"


@lru_cache
def get_settings() -> Settings:
    return Settings()

