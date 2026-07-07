import os
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from utils.paths import get_user_data_dir, get_log_dir, get_temp_dir
from utils.logger import logger


# Система и форматирование

def get_system_info() -> Dict[str, str]:
    """Возвращает информацию о системе."""
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.architecture()[0],
        'python_version': platform.python_version(),
        'processor': platform.processor()
    }


def format_duration(seconds: float) -> str:
    """Форматирует длительность в читаемый вид."""
    if seconds < 0:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}ч {minutes:02d}м {secs:02d}с"
    elif minutes > 0:
        return f"{minutes}м {secs:02d}с"
    else:
        return f"{secs}с"


def format_file_size(size_bytes: int) -> str:
    """Форматирует размер файла в читаемый вид."""
    if size_bytes <= 0:
        return "0 Б"
    
    size_names = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


# Работа с файлами

_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac',}


def get_file_extension(file_path: str) -> str:
    """Получает расширение файла без создания Path-объекта."""
    if '.' not in file_path:
        return ''
    return file_path[file_path.rfind('.'):].lower()


def is_audio_file(file_path: str) -> bool:
    """Проверяет, является ли файл аудио файлом."""
    return get_file_extension(file_path) in _AUDIO_EXTENSIONS


def find_audio_files(directory: str, recursive: bool = True) -> List[str]:
    """Находит все аудио файлы в директории."""
    directory_path = Path(directory)
    if not directory_path.exists():
        return []
    
    pattern = "**/*" if recursive else "*"
    return [
        str(f) for f in directory_path.glob(pattern)
        if f.is_file() and f.suffix.lower() in _AUDIO_EXTENSIONS
    ]


def create_directory_if_not_exists(directory: str) -> bool:
    """Создает директорию, если она не существует."""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def cleanup_temp_files(max_age_hours: int = 24, recursive: bool = False):
    """Очищает временные файлы старше указанного возраста."""
    temp_dir = get_temp_dir()
    if not temp_dir.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    pattern = "**/*" if recursive else "*"
    
    for file_path in temp_dir.glob(pattern):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time.timestamp():
            try:
                file_path.unlink()
            except OSError:
                pass


def validate_file_path(file_path: str) -> bool:
    """Проверяет валидность пути к файлу."""
    try:
        return Path(file_path).is_file()
    except (OSError, ValueError):
        return False


def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о файле."""
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        stat = path.stat()
        ext = path.suffix.lower()
        return {
            'name': path.name,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'extension': ext,
            'is_audio': ext in _AUDIO_EXTENSIONS
        }
    except (OSError, ValueError):
        return None


_INVALID_CHARS_TRANS = str.maketrans('<>:"/\\|?*', '_________')

def sanitize_filename(filename: str) -> str:
    """Очищает имя файла от недопустимых символов."""
    filename = filename.translate(_INVALID_CHARS_TRANS)
    return filename.strip(' .')


# --- Время и математика ---

def format_time(seconds: float) -> str:
    """Форматирует время в формат MM:SS или HH:MM:SS."""
    if seconds < 0:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def parse_timestamp(timestamp: str) -> Optional[float]:
    """Парсит временную метку из строки."""
    try:
        parts = timestamp.split(':')
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return None
    except ValueError:
        return None


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Ограничивает значение в заданном диапазоне."""
    return max(min_val, min(value, max_val))


def lerp(start: float, end: float, t: float) -> float:
    """Линейная интерполяция между двумя значениями."""
    return start + (end - start) * clamp(t, 0.0, 1.0)


def normalize(value: float, min_val: float, max_val: float) -> float:
    """Нормализует значение в диапазон [0, 1]."""
    if max_val == min_val:
        return 0.0
    return clamp((value - min_val) / (max_val - min_val), 0.0, 1.0)