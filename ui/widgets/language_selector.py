import locale
import os
from typing import Dict

from PyQt6.QtCore import QLocale, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QPushButton, QWidget

from core.localization import get_text
from ui.styles.style_factory import register_style, sf
from ui.styles.themes import COLORS


# Регистрация шаблона в StyleFactory один раз
def _register_language_selector_template() -> None:
    """Регистрирует QSS-шаблон для LanguageSelector."""

    def _builder() -> str:
        colors = getattr(
            __import__("ui.styles.themes", fromlist=["COLORS"]), "COLORS", {}
        )
        button_bg = colors.get("button_bg", "#e0e0e0")
        text_color = colors.get("text", "#000000")
        button_hover = colors.get("button_hover", "#d0d0d0")
        primary = colors.get("primary", "#1976d2")
        secondary = colors.get("secondary", "#1565c0")

        return f"""
            QPushButton {{
                background: {button_bg};
                color: {text_color};
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {button_hover};
            }}
            QPushButton:checked {{
                background: {primary};
                color: white;
            }}
            QPushButton:pressed {{
                background: {secondary};
            }}
        """

    try:
        sf().build("language_selector")
    except KeyError:
        register_style("language_selector", _builder)


class LanguageSelector(QWidget):
    """Виджет для выбора языка интерфейса."""

    languageChanged = pyqtSignal(str)

    LANGUAGES: Dict[str, str] = {
        "auto": "ui.labels.language_auto",
        "en": "English",
        "zh": "中文",
        "es": "Español",
        "fr": "Français",
        "de": "Deutsch",
        "pt": "Português",
        "ru": "Русский",
    }

    _WINDOWS_LANG_MAP = {
        "russian": "ru",
        "english": "en",
        "chinese": "zh",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "portuguese": "pt",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        _register_language_selector_template()
        self.current_language = "auto"
        self.buttons: Dict[str, QPushButton] = {}

        self._setup_ui()
        self.update_styles()

    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        row = 0
        col = 0
        for lang_code, lang_name in self.LANGUAGES.items():
            button_text = get_text(lang_name) if lang_code == "auto" else lang_name

            button = QPushButton(button_text)
            button.setCheckable(True)
            button.setFixedHeight(32)
            button.toggled.connect(
                lambda checked, lang=lang_code: self._on_language_toggled(lang, checked)
            )

            self.buttons[lang_code] = button
            layout.addWidget(button, row, col)

            col += 1
            if col >= 3:
                col = 0
                row += 1

        self._update_active_button()

    def _on_language_toggled(self, language: str, checked: bool):
        """Слот для кнопок — обрабатывает переключение checked."""
        if not checked and language == self.current_language:
            # Запрещаем снятие выделения с активной кнопки
            button = self.buttons[language]
            button.blockSignals(True)
            button.setChecked(True)
            button.blockSignals(False)
            return

        if checked and language != self.current_language:
            self.set_language(language)

    def set_language(self, language: str):
        """Единая точка входа для изменения языка."""
        if language not in self.LANGUAGES or language == self.current_language:
            return

        self.current_language = language
        self._update_active_button()
        self.languageChanged.emit(language)

    def _update_active_button(self):
        """Обновляет активную кнопку — только нужная кнопка получает checked."""
        for lang_code, button in self.buttons.items():
            should_be_checked = lang_code == self.current_language
            if button.isChecked() != should_be_checked:
                button.blockSignals(True)
                button.setChecked(should_be_checked)
                button.blockSignals(False)

    def _detect_system_language(self) -> str:
        # Способ 1: QLocale (без side-эффектов)
        qt_locale = QLocale.system().name().lower()
        lang_code = qt_locale.split("_")[0]
        if lang_code in self.LANGUAGES and lang_code != "auto":
            return lang_code

        # Способ 2: переменная окружения
        lang_env = os.environ.get("LANG", "")
        if lang_env:
            lang_code = lang_env.split("_")[0].lower().split(".")[0]
            if lang_code in self.LANGUAGES and lang_code != "auto":
                return lang_code

        # Способ 3: getdefaultlocale (безопасный)
        try:
            default_locale = locale.getdefaultlocale()[0]
            if default_locale:
                lang_code = self._parse_locale(default_locale)
                if lang_code in self.LANGUAGES and lang_code != "auto":
                    return lang_code
        except Exception:
            pass

        return "en"

    def _parse_locale(self, locale_str: str) -> str | None:
        locale_str = locale_str.lower()
        if "_" in locale_str:
            return locale_str.split("_")[0]
        lang_name = locale_str.split("_")[0]
        return self._WINDOWS_LANG_MAP.get(lang_name)

    def update_styles(self):
        """Обновляет стили виджета через StyleFactory."""
        sf().invalidate("language_selector")
        self.setStyleSheet(sf().build("language_selector"))

    def update_texts(self):
        auto_button = self.buttons.get("auto")
        if auto_button is not None:
            auto_button.setText(get_text(self.LANGUAGES["auto"]))
