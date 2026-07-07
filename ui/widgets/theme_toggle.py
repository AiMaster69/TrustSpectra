from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QApplication
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase, QPalette
import ui.styles.themes as themes
from ui.styles.themes import load_saved_theme
from ui.styles.style_factory import sf, register_style
import os
import sys

# Резервные эмодзи
_FALLBACK_ICONS = {
    'light': '☀',
    'dark': '🌙',
    'system': '⚙',
}

# Material Icons Unicode
_MATERIAL_ICONS = {
    'light': '\ue518',
    'dark': '\ue51c',
    'system': '\ue8b8',
}

# Загрузка шрифта один раз на уровне модуля
_FONT_LOADED = False
_USE_MATERIAL_ICONS = False
_ACTIVE_ICONS: dict[str, str] = {}


def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу. Работает и в .py, и в собранном .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def _load_fonts_once() -> None:
    """Загружает Material Icons один раз при первом импорте модуля."""
    global _FONT_LOADED, _USE_MATERIAL_ICONS, _ACTIVE_ICONS
    if _FONT_LOADED:
        return

    try:
        font_path = resource_path("resources/fonts/MaterialIcons-Regular.ttf")
        font_loaded = False

        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_loaded = True
                print(f"✓ Material Icons шрифт загружен из: {font_path}")

        if font_loaded:
            _USE_MATERIAL_ICONS = True
            _ACTIVE_ICONS = dict(_MATERIAL_ICONS)
            print("  Используем Material Icons")
        else:
            print("⚠ Material Icons шрифт не найден, используем резервные эмодзи")
            _USE_MATERIAL_ICONS = False
            _ACTIVE_ICONS = dict(_FALLBACK_ICONS)

    except Exception as e:
        print(f"✗ Ошибка при загрузке шрифта Material Icons: {e}")
        _USE_MATERIAL_ICONS = False
        _ACTIVE_ICONS = dict(_FALLBACK_ICONS)

    _FONT_LOADED = True


# Регистрация шаблона в StyleFactory один раз
def _register_theme_toggle_template() -> None:
    """Регистрирует QSS-шаблон для ThemeToggle."""
    def _builder() -> str:
        colors = getattr(themes, 'COLORS', {})
        button_bg = colors.get('button_bg', '#e0e0e0')
        text_color = colors.get('text', '#000000')
        button_hover = colors.get('button_hover', '#d0d0d0')
        primary = colors.get('primary', '#1976d2')
        secondary = colors.get('secondary', '#1565c0')

        return f"""
            QPushButton {{
                background: {button_bg};
                color: {text_color};
                border: none;
                border-radius: 6px;
                font-size: 15px;
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
        sf().build('theme_toggle')
    except KeyError:
        register_style('theme_toggle', _builder)


class ThemeToggle(QWidget):
    """Виджет для переключения между темами."""

    themeChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        _load_fonts_once()
        _register_theme_toggle_template()
        self.current_theme = load_saved_theme()
        self._buttons: dict[str, QPushButton] = {}

        self._setup_ui()
        self.update_styles()

    def _setup_ui(self):
        """Настройка интерфейса."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._buttons = {
            'light': QPushButton(_ACTIVE_ICONS['light']),
            'dark': QPushButton(_ACTIVE_ICONS['dark']),
            'system': QPushButton(_ACTIVE_ICONS['system']),
        }

        for theme_key, button in self._buttons.items():
            button.setFixedSize(32, 32)
            button.setCheckable(True)

            if _USE_MATERIAL_ICONS:
                font = QFont("Material Icons", 25)
                font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
                font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
                button.setFont(font)
            else:
                button.setFont(QFont("Segoe UI Emoji", 12))

            button.toggled.connect(lambda checked, t=theme_key: self._change_theme(t, checked))
            layout.addWidget(button)

        self._update_active_button()

    def _change_theme(self, theme: str, checked: bool):
        """Слот для кнопок — обрабатывает переключение checked."""
        if not checked and theme == self.current_theme:
            button = self._buttons[theme]
            button.blockSignals(True)
            button.setChecked(True)
            button.blockSignals(False)
            return

        if checked and theme != self.current_theme:
            self.set_theme(theme)

    def set_theme(self, theme: str):
        """Единая точка входа для изменения темы."""
        if theme == self.current_theme:
            return
        self.current_theme = theme
        self._update_active_button()
        self.update_styles()
        self.themeChanged.emit(theme)

    def _update_active_button(self):
        """Обновляет активную кнопку — только нужная кнопка получает checked."""
        for theme_key, button in self._buttons.items():
            should_be_checked = theme_key == self.current_theme
            if button.isChecked() != should_be_checked:
                button.blockSignals(True)
                button.setChecked(should_be_checked)
                button.blockSignals(False)

    def update_styles(self):
        """Обновляет стили виджета через StyleFactory."""
        sf().invalidate('theme_toggle')
        self.setStyleSheet(sf().build('theme_toggle'))

    @property
    def using_material_icons(self) -> bool:
        """Возвращает True, если используются Material Icons."""
        return _USE_MATERIAL_ICONS