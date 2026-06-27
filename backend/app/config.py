from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(PROJECT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    parts = path.parts
    if parts and parts[0] == "backend":
        return PROJECT_DIR / path
    return BACKEND_DIR / path


@dataclass(frozen=True)
class Settings:
    database_url: str = _env("DATABASE_URL", "sqlite:///./lotos_ai_approval.db")
    app_env: str = _env("APP_ENV", "development")
    secret_key: str = _env("SECRET_KEY", "change-this-secret")
    upload_dir: Path = _resolve_path(_env("UPLOAD_DIR", "uploads"))
    report_dir: Path = _resolve_path(_env("REPORT_DIR", "generated_reports"))
    log_dir: Path = _resolve_path(_env("LOG_DIR", "logs"))
    backup_dir: Path = _resolve_path(_env("BACKUP_DIR", "backups"))
    export_dir: Path = _resolve_path(_env("EXPORT_DIR", "exports"))
    access_token_expire_minutes: int = int(_env("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    allowed_origins: str = _env("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def database_type(self) -> str:
        if self.database_url.startswith("postgresql"):
            return "postgresql"
        return "sqlite"

    @property
    def is_sqlite(self) -> bool:
        return self.database_type == "sqlite"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def sqlite_path(self) -> Path | None:
        if not self.is_sqlite:
            return None
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return None
        raw_path = self.database_url.removeprefix(prefix)
        path = Path(raw_path)
        if path.is_absolute():
            return path
        return BACKEND_DIR / path

    @property
    def database_url_masked(self) -> str:
        if not self.database_url.startswith("postgresql"):
            return self.database_url
        parsed = urlsplit(self.database_url)
        if "@" not in parsed.netloc or ":" not in parsed.netloc.split("@", 1)[0]:
            return self.database_url
        user_info, host_info = parsed.netloc.rsplit("@", 1)
        username = user_info.split(":", 1)[0]
        return urlunsplit(
            (
                parsed.scheme,
                f"{username}:****@{host_info}",
                parsed.path,
                parsed.query,
                parsed.fragment,
            )
        )


settings = Settings()
