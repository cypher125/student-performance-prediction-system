"""Configuration, overridable with environment variables prefixed SAPPS_ (or a backend/.env file).

Example: SAPPS_DATABASE_URL=postgresql+psycopg://user:pass@localhost/sapps switches to PostgreSQL.
"""
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from ml import config as ml_config

DATA_DIR = ml_config.DATA_DIR
ARTIFACTS_DIR = ml_config.BACKEND_DIR / "artifacts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SAPPS_", env_file=ml_config.BACKEND_DIR / ".env",
                                      extra="ignore")

    app_name: str = "Student Performance Prediction System"
    database_url: str = f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"
    secret_key: str | None = None
    token_hours: int = 8
    cookie_name: str = "sapps_session"
    cookie_secure: bool = False  # set true when served over HTTPS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    frontend_dir: Path = ml_config.PROJECT_DIR / "frontend" / "out"
    model_path: Path = ARTIFACTS_DIR / "model.joblib"
    model_meta_path: Path = ARTIFACTS_DIR / "model_meta.json"
    current_session: str = "2025/2026"
    current_semester: str = "First"
    # Local screenshot capture only: treats unauthenticated requests as this username.
    demo_auto_login: str | None = None

    def signing_key(self) -> str:
        if self.secret_key:
            return self.secret_key
        key_file = DATA_DIR / "secret.key"
        if not key_file.exists():
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_text(secrets.token_urlsafe(48))
        return key_file.read_text().strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
