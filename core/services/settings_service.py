import copy
import json
import multiprocessing
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logger import logger
from utils.paths import get_user_data_dir


class SettingsServiceOptimized:
    """Сервис для управления настройками."""

    def __init__(self):
        self.config_dir = get_user_data_dir()
        self.settings_file = self.config_dir / "settings.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._defaults = self._get_default_settings()
        self._settings = self._load_settings()

        self._save_timer: Optional[threading.Timer] = None
        self._save_delay = 0.3

    def _get_default_settings(self) -> Dict[str, Any]:
        # При холодном старте — максимально доступное количество ядер
        default_threads = multiprocessing.cpu_count()
        return {
            "audio": {"default_volume": 50, "auto_play": True, "loop_playback": False},
            "analysis": {
                "min_duration": 2.0,
                "confidence_threshold": 0.9,
                "confidence_thresholds": {
                    "claps": 0.9,
                    "heavy_breathing": 0.9,
                    "kisses": 0.9,
                    "moans": 0.9,
                },
                "auto_analyze": False,
                "chunk_duration": 60.0,
                "use_chunked_loading": True,
                "max_memory_mb": 512,
            },
            "ui": {
                "theme": "system",
                "language": "auto",
                "font_size": "medium",
                "show_tooltips": True,
                "enable_animations": True,
                "window_width": 1200,
                "window_height": 800,
                "show_ai_warning": True,
            },
            "files": {"max_history": 20, "auto_save_settings": True},
            "performance": {"num_threads": default_threads},
        }

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Универсальное получение настройки по точечному пути (напр. 'ui.theme')."""
        with self._lock:
            return self._get_nested(self._settings, key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Универсальная установка настройки по точечному пути."""
        with self._lock:
            self._set_nested(self._settings, key, value)
            self._schedule_save()
            logger.info(f"Настройка обновлена: {key} = {value}")

    def get_category(self, category: str) -> Dict[str, Any]:
        """Возвращает все настройки определенной категории (audio, ui, analysis)."""
        with self._lock:
            return copy.deepcopy(self._settings.get(category, {}))

    def set_category(self, category: str, settings: Dict[str, Any]) -> None:
        """Заменяет/дополняет настройки указанной категории за одну операцию."""
        with self._lock:
            cat_dict = self._settings.setdefault(category, {})
            self._deep_merge(cat_dict, settings)
            self._schedule_save()

    def get_all_settings(self) -> Dict[str, Any]:
        """Возвращает полную копию текущих настроек со всеми дефолтами."""
        with self._lock:
            return copy.deepcopy(self._settings)

    def set_all_settings(self, settings: Dict[str, Any]) -> None:
        """Обновляет множество настроек из вложенного словаря."""
        with self._lock:
            self._deep_merge(self._settings, settings)
            self._schedule_save()

    def _get_nested(self, data: Dict, key: str, default: Any) -> Any:
        keys = key.split(".")
        curr = data
        try:
            for k in keys:
                curr = curr[k]
            return curr
        except (KeyError, TypeError):
            return default

    def _set_nested(self, data: Dict, key: str, value: Any) -> None:
        keys = key.split(".")
        curr = data
        for k in keys[:-1]:
            curr = curr.setdefault(k, {})
        curr[keys[-1]] = value

    def _deep_merge(self, target: Dict, source: Dict) -> None:
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _load_settings(self) -> Dict[str, Any]:
        result = copy.deepcopy(self._defaults)
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self._deep_merge(result, json.load(f))
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
        return result

    def _schedule_save(self) -> None:
        if not self._get_nested(self._settings, "files.auto_save_settings", True):
            return
        if self._save_timer:
            self._save_timer.cancel()
        self._save_timer = threading.Timer(self._save_delay, self.save)
        self._save_timer.daemon = True  # не блокирует выход из приложения
        self._save_timer.start()

    def save(self) -> None:
        # Всё управление таймером теперь под защитой лока
        with self._lock:
            if self._save_timer:
                self._save_timer.cancel()
                self._save_timer = None
            try:
                with open(self.settings_file, "w", encoding="utf-8") as f:
                    json.dump(self._settings, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Ошибка сохранения настроек: {e}")


SettingsService = SettingsServiceOptimized
