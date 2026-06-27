import logging
from logging.handlers import RotatingFileHandler

from app.config import settings

LOG_DIR = settings.log_dir
APP_LOG_PATH = LOG_DIR / "app.log"
ERROR_LOG_PATH = LOG_DIR / "error.log"


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s / %(levelname)s / %(name)s / %(message)s"
    )

    app_handler = RotatingFileHandler(
        APP_LOG_PATH,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler(
        ERROR_LOG_PATH,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [
        handler
        for handler in root_logger.handlers
        if not isinstance(handler, RotatingFileHandler)
    ]
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
