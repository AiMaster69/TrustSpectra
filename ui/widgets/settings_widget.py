from typing import Dict, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from core.localization import get_text
from ui.styles.style_factory import sf

from .language_selector import LanguageSelector
from .theme_toggle import ThemeToggle
from .confidence_widget import ConfidenceWidget
from .performance_widget import PerformanceWidget


class SettingsWidget(QWidget):
    settingsChanged = pyqtSignal(dict)
    settingsClosed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._settings: Dict[str, dict] = {}
        self._blocks: list[QWidget] = []
        self._text_updaters = []

        # Ссылка на сервис (для загрузки, сохранение теперь в MainWindow)
        self._settings_service = None
        if parent and hasattr(parent, "settings_service"):
            self._settings_service = parent.settings_service

        self._setup_ui()
        self._load_saved_settings()

    def _setup_ui(self) -> None:
        self.setMinimumWidth(260)
        self.setMaximumWidth(400)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(16, 8, 16, 16)
        self._content_layout.setSpacing(12)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # 1. Блок темы
        self._theme_toggle = ThemeToggle()
        self._theme_toggle.themeChanged.connect(self._on_theme_changed)
        self._add_block("ui.labels.theme", self._theme_toggle)

        # 2. Блок языка
        self._language_selector = LanguageSelector()
        self._language_selector.languageChanged.connect(self._on_language_changed)
        self._add_block("ui.labels.language", self._language_selector)

        # 3. Блок порогов
        self._confidence_widget = ConfidenceWidget()
        self._confidence_widget.confidenceChanged.connect(self._on_confidence_changed)
        self._add_block("ui.labels.confidence_thresholds", self._confidence_widget)

        # 4. Блок производительности
        self._performance_widget = PerformanceWidget()
        self._performance_widget.threadsChanged.connect(self._on_threads_changed)
        self._add_block("ui.labels.performance", self._performance_widget)

        self._content_layout.addStretch()

    def _add_block(self, title_key: str, widget: QWidget) -> None:
        """Оборачивает переданный виджет в блок с заголовком."""
        block = QWidget()
        block.setObjectName("settings_block")

        layout = QVBoxLayout(block)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_label = QLabel(get_text(title_key))
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)

        layout.addWidget(title_label)
        layout.addWidget(widget)

        self._blocks.append(block)
        self._text_updaters.append((title_label, title_key))
        self._content_layout.addWidget(block)

    # ---------- обработчики сигналов от блоков ----------
    def _on_theme_changed(self, theme: str) -> None:
        self._settings.setdefault("ui", {})["theme"] = theme
        self.settingsChanged.emit(self._settings)

    def _on_language_changed(self, language: str) -> None:
        self._settings.setdefault("ui", {})["language"] = language
        self.settingsChanged.emit(self._settings)

    def _on_confidence_changed(self, class_name: str, value: float) -> None:
        self._settings.setdefault("analysis", {}).setdefault("confidence_thresholds", {})[class_name] = value
        self.settingsChanged.emit(self._settings)

    def _on_threads_changed(self, value: int) -> None:
        self._settings.setdefault("performance", {})["num_threads"] = value
        self.settingsChanged.emit(self._settings)

    # ---------- загрузка ----------
    def _load_saved_settings(self) -> None:
        """Загружает настройки из сервиса и заполняет self._settings + виджеты."""
        if self._settings_service is None:
            return

        ui = self._settings_service.get_category("ui")
        analysis = self._settings_service.get_category("analysis")
        performance = self._settings_service.get_category("performance")

        self._settings = {
            "ui": ui.copy(),
            "analysis": analysis.copy(),
            "performance": performance.copy(),
        }

        self._language_selector.set_language(ui.get("language", "auto"))
        self._confidence_widget.set_values(analysis.get("confidence_thresholds", {}))
        self._performance_widget.set_threads(performance.get("num_threads", 4))

    # ---------- обновление внешнего вида ----------
    def update_styles(self) -> None:
        self.setStyleSheet(sf().build("settings_widget"))
        for block in self._blocks:
            block.setStyleSheet(sf().build("settings_block"))

        self._theme_toggle.update_styles()
        self._language_selector.update_styles()
        self._confidence_widget.update_styles()
        self._performance_widget.update_styles()

    def update_texts(self) -> None:
        for label, key in self._text_updaters:
            label.setText(get_text(key))

        self._language_selector.update_texts()
        self._confidence_widget.update_texts()
        self._performance_widget.update_texts()

    # ---------- управление видимостью ----------
    def show_settings(self, window_width: int = None) -> None:
        self.show()
        self.raise_()

    def hide_settings(self) -> None:
        # Сохранение уже выполнено через сигнал settingsChanged → MainWindow
        self.hide()

    def instant_hide_settings(self) -> None:
        # Используется при принудительном закрытии (например, клик вне панели или потеря фокуса)
        # Сигнал settingsChanged уже отработал, поэтому просто скрываем и оповещаем
        self.hide()
        self.settingsClosed.emit()

    def toggle_menu(self) -> None:
        if self.isVisible() and self.width() > 0:
            self.hide_settings()
        else:
            self.show_settings()

    def wheelEvent(self, event):
        event.ignore()