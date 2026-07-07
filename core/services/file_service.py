import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.paths import get_user_data_dir
from utils.exceptions import AudioFileError
from utils.logger import logger
from core.models.audio_file import AudioFile


class FileService:
    def __init__(self, settings_service):
        self.settings_service = settings_service
        self.config_dir = get_user_data_dir()
        self.recent_files_path = self.config_dir / 'recent_files.json'
        self.config_dir.mkdir(parents=True, exist_ok=True)

    @property
    def max_history(self) -> int:
        # Берем значение из настроек, если там нет — дефолт 20
        return self.settings_service.get_setting('files.max_history', 20)

    def get_supported_formats(self) -> List[str]:
        return ['.mp3', '.wav', '.ogg', '.flac']

    def is_supported_format(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.get_supported_formats()

    def validate_file(self, file_path: str) -> bool:
        """Валидирует файл. Возвращает True или выбрасывает AudioFileError с причиной."""
        path = Path(file_path)

        if not path.exists():
            raise AudioFileError(f"Файл не найден: {file_path}")

        if not self.is_supported_format(file_path):
            raise AudioFileError(f"Неподдерживаемый формат: {path.suffix}")

        file_size_mb = path.stat().st_size / (1024 * 1024)
        logger.info(f"Размер файла: {file_size_mb:.1f}MB")

        return True

    def load_audio_file(self, file_path: str) -> AudioFile:
        try:
            self.validate_file(file_path)
            audio_file = AudioFile.from_path(Path(file_path))
            self.add_to_recent_files(audio_file)
            logger.info(f"Аудио файл загружен: {audio_file.name}")
            return audio_file
        except AudioFileError:
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки аудио файла {file_path}: {e}")
            raise AudioFileError(f"Ошибка загрузки аудио файла: {e}")

    def add_to_recent_files(self, audio_file: AudioFile) -> None:
        try:
            recent_files = self.get_recent_files()
            # Нормализуем путь один раз
            file_path_resolved = str(audio_file.path.resolve())

            # Сравниваем как строки, так как пути в истории уже должны быть разрешены (resolved)
            recent_files = [
                f for f in recent_files
                if f.get('path') != file_path_resolved
            ]

            file_data = audio_file.to_dict()
            file_data['path'] = file_path_resolved
            file_data['added_at'] = datetime.now().isoformat()
            recent_files.insert(0, file_data)

            max_hist = self.max_history
            if len(recent_files) > max_hist:
                recent_files = recent_files[:max_hist]

            self._save_recent_files(recent_files)

        except Exception as e:
            logger.error(f"Ошибка добавления файла в историю: {e}")

    def get_recent_files(self) -> List[Dict[str, Any]]:
        try:
            if self.recent_files_path.exists():
                with open(self.recent_files_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки списка недавних файлов: {e}")
        return []

    def _save_recent_files(self, files: List[Dict[str, Any]]) -> None:
        try:
            with open(self.recent_files_path, 'w', encoding='utf-8') as f:
                json.dump(files, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения списка недавних файлов: {e}")

    def clear_recent_files(self) -> None:
        try:
            self._save_recent_files([])
            logger.info("Список недавних файлов очищен")
        except Exception as e:
            logger.error(f"Ошибка очистки списка недавних файлов: {e}")

    def remove_from_recent_files(self, file_path: str) -> None:
        try:
            recent_files = self.get_recent_files()
            target_resolved = str(Path(file_path).resolve())
            recent_files = [
                f for f in recent_files
                if f.get('path') != target_resolved
            ]
            self._save_recent_files(recent_files)
        except Exception as e:
            logger.error(f"Ошибка удаления файла из истории: {e}")

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        audio_file = AudioFile.from_path(Path(file_path))
        return audio_file.to_dict()

    def scan_directory(self, directory_path: str) -> List[AudioFile]:
        try:
            directory = Path(directory_path)
            if not directory.exists() or not directory.is_dir():
                raise AudioFileError(f"Директория не найдена: {directory_path}")

            audio_files: List[AudioFile] = []
            supported = self.get_supported_formats()

            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in supported:
                    try:
                        audio_files.append(AudioFile.from_path(file_path))
                    except Exception as e:
                        logger.warning(f"Ошибка загрузки файла {file_path}: {e}")

            logger.info(f"Найдено {len(audio_files)} аудио файлов в {directory_path}")
            return audio_files

        except Exception as e:
            logger.error(f"Ошибка сканирования директории {directory_path}: {e}")
            raise AudioFileError(f"Ошибка сканирования директории: {e}")