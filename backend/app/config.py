from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    riot_api_key: str = ""
    frontend_origin: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")


settings = Settings()
