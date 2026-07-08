from pathlib import Path
from typing import Any, Dict, List, Optional

from core.audio.analyzer_adapter import create_analyzer_adapter
from core.models.analysis_result import AnalysisResult
from core.models.audio_file import AudioFile
from core.services.file_service import FileService
from core.services.settings_service import SettingsService
from utils.exceptions import TrustSpectraError
from utils.logger import logger


class MainController:
    def __init__(self, settings_service: SettingsService):
        self.settings_service = settings_service
        self.file_service = FileService(self.settings_service)

        performance_settings = self.settings_service.get_category("performance")
        num_threads = performance_settings.get("num_threads")

        analysis_settings = self.settings_service.get_category("analysis")
        threshold = analysis_settings.get("confidence_threshold", 0.9)
        chunk_duration = analysis_settings.get("chunk_duration", 60.0)
        use_chunked_loading = analysis_settings.get("use_chunked_loading", True)

        self.analyzer = create_analyzer_adapter(
            threshold=threshold,
            num_threads=num_threads,
            chunk_duration=chunk_duration,
            use_chunked_loading=use_chunked_loading,
        )

        self.analyzer.update_parameters(**analysis_settings)

        self.current_audio_file: Optional[AudioFile] = None
        self.current_analysis_result: Optional[AnalysisResult] = None

        logger.info(
            f"Главный контроллер инициализирован с порогом {threshold}, чанки: {chunk_duration}s"
        )

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """
        Единая точка входа для применения настроек из UI в реальном времени.
        Вызывается из MainWindow.on_settings_changed после сохранения в JSON.
        """
        if analysis := settings.get("analysis"):
            # Анализатор обновляем напрямую, без повторного сохранения в JSON
            # (MainWindow уже вызвал set_all_settings)
            self.analyzer.update_parameters(**analysis)
            logger.info(f"Настройки анализа применены к анализатору: {analysis}")

        if performance := settings.get("performance"):
            # Потоки ONNX применятся только после перезапуска
            logger.info(
                f"Настройки производительности сохранены, применятся при перезапуске: {performance}"
            )

    def load_audio_file(self, file_path: str) -> AudioFile:
        """Загружает аудио файл."""
        try:
            audio_file = self.file_service.load_audio_file(file_path)
            self.current_audio_file = audio_file

            logger.info(f"Аудио файл загружен: {audio_file.name}")
            return audio_file

        except Exception as e:
            logger.error(f"Ошибка загрузки аудио файла: {e}")
            raise TrustSpectraError(f"Ошибка загрузки аудио файла: {e}")

    def analyze_file(self, file_path: str, progress_callback=None) -> AnalysisResult:
        """Анализирует любой файл и преобразует результат в объект, понятный UI."""
        try:
            # Получаем сырой результат от ONNX модели в виде словаря
            result = self.analyzer.analyze_audio(
                file_path, progress_callback=progress_callback
            )

            # Если словарь содержит ошибку - прерываем работу
            if isinstance(result, dict) and "error" in result:
                raise Exception(result["error"])

            # Конвертируем словарь в нужные объекты
            from datetime import datetime

            from core.models.analysis_result import AnalysisResult, AnalysisSegment

            segments = []
            if "segments" in result:
                for seg in result["segments"]:
                    segments.append(
                        AnalysisSegment(
                            start_time=seg["segment_start"],
                            end_time=seg["segment_end"],
                            label=seg["label"],
                            confidence=seg["confidence"],
                        )
                    )

            analysis_result = AnalysisResult(
                file_path=file_path,
                segments=segments,
                total_duration=result.get("file_duration", 0),
                analysis_duration=result.get("processing_time", 0),
                model_used=result.get("model_used", "onnx_model"),
                parameters={
                    "threshold": self.get_analysis_settings().get(
                        "confidence_threshold", 0.9
                    ),
                    "detected_classes": result.get("detected_classes", []),
                    "analyzer_type": "onnx",
                },
                created_at=datetime.now(),
            )

            # Сохраняем в кэш контроллера, если это тот же файл, что открыт в плеере
            if (
                self.current_audio_file
                and str(self.current_audio_file.path) == file_path
            ):
                self.current_analysis_result = analysis_result

            return analysis_result

        except Exception as e:
            logger.error(f"Ошибка анализа файла {file_path}: {e}")
            raise TrustSpectraError(f"Сбой при анализе: {e}")

    def analyze_current_file(self, progress_callback=None) -> AnalysisResult:
        """Анализирует текущий загруженный файл."""
        if not self.current_audio_file:
            raise TrustSpectraError("Нет загруженного аудио файла")

        file_path = str(
            getattr(self.current_audio_file, "path", self.current_audio_file)
        )
        return self.analyze_file(file_path, progress_callback)

    def get_recent_files(self) -> List[Dict[str, Any]]:
        return self.file_service.get_recent_files()

    def get_audio_settings(self) -> Dict[str, Any]:
        return self.settings_service.get_category("audio")

    def set_audio_settings(self, settings: Dict[str, Any]):
        self.settings_service.set_audio_settings(settings)

    def get_analysis_settings(self) -> Dict[str, Any]:
        return self.settings_service.get_category("analysis")

    def set_analysis_settings(self, settings: Dict[str, Any]):
        self.settings_service.set_analysis_settings(settings)
        self.analyzer.update_parameters(**settings)
        logger.info(f"Настройки анализа обновлены: {settings}")

    def get_ui_settings(self) -> Dict[str, Any]:
        return self.settings_service.get_category("ui")

    def set_ui_settings(self, settings: Dict[str, Any]):
        self.settings_service.set_ui_settings(settings)

    def get_performance_settings(self) -> Dict[str, Any]:
        return self.settings_service.get_category("performance")

    def set_performance_settings(self, settings: Dict[str, Any]):
        self.settings_service.set_performance_settings(settings)
        logger.info(
            f"Настройки производительности обновлены и применятся при следующем запуске: {settings}"
        )

    def get_file_settings(self) -> Dict[str, Any]:
        return self.settings_service.get_file_settings()

    def set_file_settings(self, settings: Dict[str, Any]):
        self.settings_service.set_file_settings(settings)

    def clear_recent_files(self):
        self.file_service.clear_recent_files()

    def get_supported_formats(self) -> List[str]:
        return self.file_service.get_supported_formats()

    def validate_file(self, file_path: str) -> bool:
        return self.file_service.validate_file(file_path)

    def get_current_file_info(self) -> Optional[Dict[str, Any]]:
        if self.current_audio_file:
            return self.current_audio_file.to_dict()
        return None

    def get_current_analysis_info(self) -> Optional[Dict[str, Any]]:
        if self.current_analysis_result:
            return self.current_analysis_result.to_dict()
        return None

    def export_settings(self, file_path: str):
        self.settings_service.export_settings(file_path)

    def import_settings(self, file_path: str):
        self.settings_service.import_settings(file_path)

    def reset_settings(self):
        self.settings_service.reset_settings()

    def validate_settings(self) -> bool:
        return True
