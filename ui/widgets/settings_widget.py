from typing import Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from core.localization import get_text
from ui.styles.style_factory import sf

from .confidence_widget import ConfidenceWidget
from .language_selector import LanguageSelector
from .performance_widget import PerformanceWidget
from .theme_toggle import ThemeToggle


class SettingsWidget(QWidget):
    settingsChanged = pyqtSignal(dict)
    settingsClosed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._settings: Dict[str, dict] = {"ui": {}, "analysis": {}, "performance": {}}
        self._blocks: list[QWidget] = []
        self._text_updaters = []

        self._settings_service = getattr(parent, "settings_service", None)

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

        # Создаем ThemeToggle с дефолтной темой (пока не загрузили настройки)
        self._theme_toggle = ThemeToggle(initial_theme="system")
        self._theme_toggle.themeChanged.connect(self._on_theme_changed)
        self._add_block("ui.labels.theme", self._theme_toggle)

        self._language_selector = LanguageSelector()
        self._language_selector.languageChanged.connect(self._on_language_changed)
        self._add_block("ui.labels.language", self._language_selector)

        self._confidence_widget = ConfidenceWidget()
        self._confidence_widget.confidenceChanged.connect(self._on_confidence_changed)
        self._add_block("ui.labels.confidence_thresholds", self._confidence_widget)

        self._performance_widget = PerformanceWidget()
        self._performance_widget.threadsChanged.connect(self._on_threads_changed)
        self._add_block("ui.labels.performance", self._performance_widget)

        self._content_layout.addStretch()

    def _add_block(self, title_key: str, widget: QWidget) -> None:
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

    def _on_theme_changed(self, theme: str) -> None:
        self._settings.setdefault("ui", {})["theme"] = theme
        self.settingsChanged.emit(self._settings)

    def _on_language_changed(self, language: str) -> None:
        self._settings.setdefault("ui", {})["language"] = language
        self.settingsChanged.emit(self._settings)

    def _on_confidence_changed(self, class_name: str, value: float) -> None:
        self._settings.setdefault("analysis", {}).setdefault(
            "confidence_thresholds", {}
        )[class_name] = value
        self.settingsChanged.emit(self._settings)

    def _on_threads_changed(self, value: int) -> None:
        self._settings.setdefault("performance", {})["num_threads"] = value
        self.settingsChanged.emit(self._settings)

    def _load_saved_settings(self) -> None:
        if self._settings_service is None:
            return

        ui = self._settings_service.get_category("ui")
        analysis = self._settings_service.get_category("analysis")
        performance = self._settings_service.get_category("performance")

        # Аккуратно обновляем self._settings, не теряя текущие значения
        self._settings["ui"].update(ui)
        self._settings["analysis"].update(analysis)
        self._settings["performance"].update(performance)

        # Синхронизируем виджеты БЕЗ эмитирования сигналов
        self._language_selector.set_language(ui.get("language", "auto"))
        self._confidence_widget.set_values(analysis.get("confidence_thresholds", {}))
        self._performance_widget.set_threads(performance.get("num_threads", 4))

        # САМОЕ ВАЖНОЕ: Читаем реальную тему из themes.py и отдаем её в Toggle
        import ui.styles.themes as themes

        actual_theme = getattr(themes, "CURRENT_THEME", "system")
        # Обновляем словарь, чтобы при смене языка улетала ПРАВИЛЬНАЯ тема
        self._settings["ui"]["theme"] = actual_theme
        self._theme_toggle.set_theme(actual_theme, emit_signal=False)

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

    def show_settings(self, window_width: int = None) -> None:
        self.show()
        self.raise_()

    def hide_settings(self) -> None:
        self.hide()

    def instant_hide_settings(self) -> None:
        self.hide()
        self.settingsClosed.emit()

    def toggle_menu(self) -> None:
        if self.isVisible() and self.width() > 0:
            self.hide_settings()
        else:
            self.show_settings()

    def wheelEvent(self, event):
        event.ignore()
