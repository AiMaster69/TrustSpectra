import os
import sys

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

import ui.styles.themes as themes
from ui.styles.style_factory import register_style, sf

_FALLBACK_ICONS = {"light": "☀", "dark": "🌙", "system": "⚙"}
_MATERIAL_ICONS = {"light": "\ue518", "dark": "\ue51c", "system": "\ue8b8"}

_FONT_LOADED = False
_USE_MATERIAL_ICONS = False
_ACTIVE_ICONS: dict[str, str] = {}


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def _load_fonts_once() -> None:
    global _FONT_LOADED, _USE_MATERIAL_ICONS, _ACTIVE_ICONS
    if _FONT_LOADED:
        return
    try:
        font_path = resource_path("resources/fonts/MaterialIcons-Regular.ttf")
        if (
            os.path.exists(font_path)
            and QFontDatabase.addApplicationFont(font_path) != -1
        ):
            _USE_MATERIAL_ICONS = True
            _ACTIVE_ICONS = dict(_MATERIAL_ICONS)
        else:
            _USE_MATERIAL_ICONS = False
            _ACTIVE_ICONS = dict(_FALLBACK_ICONS)
    except Exception:
        _USE_MATERIAL_ICONS = False
        _ACTIVE_ICONS = dict(_FALLBACK_ICONS)
    _FONT_LOADED = True


def _register_theme_toggle_template() -> None:
    def _builder() -> str:
        colors = getattr(themes, "COLORS", {})
        return f"""
            QPushButton {{ background: {colors.get('button_bg', '#e0e0e0')}; color: {colors.get('text', '#000')}; border: none; border-radius: 6px; font-size: 15px; }}
            QPushButton:hover {{ background: {colors.get('button_hover', '#d0d0d0')}; }}
            QPushButton:checked {{ background: {colors.get('primary', '#1976d2')}; color: white; }}
        """

    try:
        sf().build("theme_toggle")
    except KeyError:
        register_style("theme_toggle", _builder)


class ThemeToggle(QWidget):
    themeChanged = pyqtSignal(str)

    def __init__(self, initial_theme: str = "system"):
        super().__init__()
        _load_fonts_once()
        _register_theme_toggle_template()

        self.current_theme = initial_theme
        self._buttons: dict[str, QPushButton] = {}
        self._is_initialized = False  # Флаг для блокировки сигналов при старте
        self._setup_ui()
        self.update_styles()
        self._is_initialized = True

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._buttons = {
            "light": QPushButton(_ACTIVE_ICONS["light"]),
            "dark": QPushButton(_ACTIVE_ICONS["dark"]),
            "system": QPushButton(_ACTIVE_ICONS["system"]),
        }

        for theme_key, button in self._buttons.items():
            button.setFixedSize(32, 32)
            button.setCheckable(True)
            if _USE_MATERIAL_ICONS:
                font = QFont("Material Icons", 25)
                font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
                button.setFont(font)
            else:
                button.setFont(QFont("Segoe UI Emoji", 12))

            # Используем clicked - он не срабатывает при setChecked()
            button.clicked.connect(lambda _, t=theme_key: self._on_button_clicked(t))
            layout.addWidget(button)

        self._update_active_button()

    def _on_button_clicked(self, theme: str):
        if not self._is_initialized:
            return
        button = self._buttons.get(theme)
        if button and button.isChecked():
            self.set_theme(theme)
        elif button and not button.isChecked():
            button.blockSignals(True)
            button.setChecked(True)
            button.blockSignals(False)

    def set_theme(self, theme: str, emit_signal: bool = True):
        if theme not in self._buttons:
            return
        if theme == self.current_theme and self._buttons[theme].isChecked():
            return

        self.current_theme = theme
        self._update_active_button()
        self.update_styles()

        if emit_signal and self._is_initialized:
            self.themeChanged.emit(theme)

    def _update_active_button(self):
        for theme_key, button in self._buttons.items():
            should_be_checked = theme_key == self.current_theme
            if button.isChecked() != should_be_checked:
                button.blockSignals(True)
                button.setChecked(should_be_checked)
                button.blockSignals(False)

    def update_styles(self):
        sf().invalidate("theme_toggle")
        self.setStyleSheet(sf().build("theme_toggle"))
