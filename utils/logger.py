import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from utils.paths import get_log_dir


class Logger:
    def __init__(self, name: str = "TrustSpectra"):
        self._name = name
        self._logger: Optional[logging.Logger] = None
        self._initialized = False

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = logging.getLogger(self._name)
        if not self._initialized:
            self._setup_logger()
            self._initialized = True
        return self._logger

    def _setup_logger(self):
        self._logger.setLevel(logging.INFO)

        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        log_dir = get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_dir / "TrustSpectra.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    def __getattr__(self, name: str):
        return getattr(self.logger, name)


logger = Logger()


def setup_logging(level: Optional[str] = None):
    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.logger.setLevel(log_level)
    return logger
