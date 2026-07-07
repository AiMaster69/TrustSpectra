import os
import platform
from pathlib import Path


def get_user_data_dir() -> Path:
    """Возвращает директорию для пользовательских данных."""
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'TrustSpectra'
    elif system == "Darwin":
        return Path.home() / 'Library' / 'Application Support' / 'TrustSpectra'
    else:
        return Path.home() / '.config' / 'TrustSpectra'


def get_log_dir() -> Path:
    """Возвращает директорию для логов."""
    return get_user_data_dir() / 'logs'


def get_temp_dir() -> Path:
    """Возвращает временную директорию."""
    return get_user_data_dir() / 'temp'