from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Optional imports at module level with feature flags
try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

try:
    import mutagen
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False


@dataclass
class AudioFile:
    """Модель аудио файла с метаданными.

    Извлекает информацию без загрузки аудиоданных в память,
    используя soundfile.info() и mutagen.
    """

    path: Path
    name: str
    size: int
    duration: float
    format: str
    sample_rate: int
    channels: int
    bit_depth: Optional[int] = None
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None

    def __post_init__(self):
        """Валидация полей после создания."""
        if self.duration < 0:
            raise ValueError(f"duration must be >= 0, got {self.duration}")
        if self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be > 0, got {self.sample_rate}")
        if self.channels <= 0:
            raise ValueError(f"channels must be > 0, got {self.channels}")
        if self.size < 0:
            raise ValueError(f"size must be >= 0, got {self.size}")

    @classmethod
    def from_path(cls, file_path: Path) -> 'AudioFile':
        """Создает объект AudioFile из пути к файлу.

        Читает метаданные без декодирования аудио (быстро и не требует RAM).
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = file_path.stat()
        suffix = file_path.suffix.lower()

        duration = 0.0
        sample_rate = 44100
        channels = 2
        bit_depth = None

        # 1. Пытаемся soundfile.info() — самый быстрый и точный способ
        if HAS_SOUNDFILE:
            try:
                info = sf.info(str(file_path))
                duration = info.duration
                sample_rate = info.samplerate
                channels = info.channels
                # bit_depth извлекаем только для PCM-форматов (WAV, FLAC, AIFF)
                if info.subtype and 'PCM' in info.subtype:
                    try:
                        bit_depth = int(info.subtype.replace('PCM_', ''))
                    except ValueError:
                        pass
            except Exception as e:
                logger.warning(
                    "soundfile failed to read info for %s: %s", 
                    file_path.name, e
                )

        # 2. Fallback на mutagen (MP3, AAC, OGG и т.д.)
        if duration == 0.0 and HAS_MUTAGEN:
            try:
                audio_info = mutagen.File(str(file_path))
                if audio_info and hasattr(audio_info, 'info'):
                    info = audio_info.info
                    if hasattr(info, 'length') and info.length:
                        duration = float(info.length)
                    if hasattr(info, 'sample_rate') and info.sample_rate:
                        sample_rate = int(info.sample_rate)
                    if hasattr(info, 'channels') and info.channels:
                        channels = int(info.channels)
                    # bit_depth имеет смысл только для несжатых форматов
                    if suffix in ('.wav', '.flac', '.aiff', '.pcm', '.raw'):
                        if hasattr(info, 'bits_per_sample') and info.bits_per_sample:
                            bit_depth = int(info.bits_per_sample)
            except Exception as e:
                logger.warning(
                    "mutagen failed to read info for %s: %s", 
                    file_path.name, e
                )

        # 3. Последний fallback — грубая оценка по размеру файла
        if duration == 0.0:
            duration = stat.st_size / (sample_rate * channels * 2)  # assume 16-bit
            logger.warning(
                "Could not determine exact audio parameters for %s. "
                "Using rough estimate: %.2f s", 
                file_path.name, duration
            )

        return cls(
            path=file_path,
            name=file_path.name,
            size=stat.st_size,
            duration=duration,
            format=suffix,
            sample_rate=sample_rate,
            channels=channels,
            bit_depth=bit_depth,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            last_accessed=datetime.fromtimestamp(stat.st_atime)
        )

    def to_dict(self) -> dict:
        """Преобразует объект в словарь для сериализации."""
        return {
            'path': str(self.path),
            'name': self.name,
            'size': self.size,
            'duration': self.duration,
            'format': self.format,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'bit_depth': self.bit_depth,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AudioFile':
        """Создает объект AudioFile из словаря.

        Безопасно обрабатывает отсутствующие ключи с разумными значениями по умолчанию.
        """
        return cls(
            path=Path(data.get('path', '')),
            name=data.get('name', 'unknown'),
            size=data.get('size', 0),
            duration=data.get('duration', 0.0),
            format=data.get('format', ''),
            sample_rate=data.get('sample_rate', 44100),
            channels=data.get('channels', 2),
            bit_depth=data.get('bit_depth'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None
        )

    def __str__(self) -> str:
        return f"AudioFile({self.name}, {self.duration:.2f}s, {self.format})"

    def __repr__(self) -> str:
        return self.__str__()