from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


BASE_DIR = get_base_dir()
load_dotenv(BASE_DIR / ".env")
load_dotenv()


def resource_path(relative_path: str) -> Path:
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir) / relative_path
    return BASE_DIR / relative_path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    deepseek_temperature: float
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    app_host: str
    app_port: int
    auto_open_browser: bool
    speech_language: str
    max_interview_questions: int

    @property
    def mysql_server_url(self) -> str:
        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return f"mysql+pymysql://{user}:{password}@{self.mysql_host}:{self.mysql_port}"

    @property
    def database_url(self) -> str:
        return f"{self.mysql_server_url}/{self.mysql_database}?charset=utf8mb4"

    @property
    def app_url(self) -> str:
        return f"http://{self.app_host}:{self.app_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip(),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip(),
        deepseek_temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.4")),
        mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1").strip(),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", "root").strip(),
        mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
        mysql_database=os.getenv("MYSQL_DATABASE", "interview_agent").strip(),
        app_host=os.getenv("APP_HOST", "127.0.0.1").strip(),
        app_port=int(os.getenv("APP_PORT", "8000")),
        auto_open_browser=_bool_env("AUTO_OPEN_BROWSER", True),
        speech_language=os.getenv("SPEECH_LANGUAGE", "zh-CN").strip(),
        max_interview_questions=int(os.getenv("MAX_INTERVIEW_QUESTIONS", "8")),
    )
