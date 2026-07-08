import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ui.styles.style_factory import sf


def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу. Работает и в .py, и в собранном .exe"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def _ensure_material_icons_loaded() -> bool:
    """Проверяет наличие шрифта Material Icons, при необходимости загружает сам."""
    if "Material Icons" in QFontDatabase.families():
        return True

    font_path = resource_path("resources/fonts/MaterialIcons-Regular.ttf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            return True
    return False


class TitleBarButton(QPushButton):
    def __init__(
        self, icon_text: str, fallback_text: str, is_close: bool = False, parent=None
    ):
        super().__init__(parent)
        self._icon_text = icon_text
        self._fallback_text = fallback_text
        self._is_close = is_close

        self.setFixedSize(sf().size("title_height", 35), sf().size("title_height", 35))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._setup_font()
        self.update_styles()

    def _setup_font(self):
        if _ensure_material_icons_loaded():
            self.setText(self._icon_text)
            font = QFont("Material Icons")
            font.setPixelSize(22)
            self.setFont(font)
        else:
            self.setText(self._fallback_text)
            font = QFont()
            font.setPixelSize(18)
            font.setBold(True)
            self.setFont(font)

    def update_styles(self):
        """Обновляет стили в соответствии с текущей темой. Вызывать при смене темы."""
        base_color = sf().color("error") if self._is_close else sf().color("primary")
        text_color = sf().color("text")

        self.setStyleSheet(
            f"""
            QPushButton {{
                border: none;
                background: transparent;
                padding: 0;
                color: {text_color};
            }}
            QPushButton:hover {{
                color: {base_color};
            }}
        """
        )


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(sf().size("title_height", 35))
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(20, 20)

        # Исправленный путь к иконке — работает и в .py, и в .exe
        icon_path = resource_path("resources/icons/icon.svg")
        if os.path.exists(icon_path):
            self.logo_label.setPixmap(QIcon(icon_path).pixmap(20, 20))

        layout.addWidget(self.logo_label)
        layout.addSpacing(8)

        self.title = QLabel("TrustSpectra")
        layout.addWidget(self.title)
        layout.addStretch()

        self.buttons = {
            "minimize": TitleBarButton("\ue15b", "―", parent=self),
            "maximize": TitleBarButton("\ue3c6", "□", parent=self),
            "close": TitleBarButton("\ue5cd", "✕", is_close=True, parent=self),
        }

        main_window = self.parent()
        if main_window:
            self.buttons["minimize"].clicked.connect(main_window.showMinimized)
            self.buttons["maximize"].clicked.connect(main_window.toggleMaximized)
            self.buttons["close"].clicked.connect(main_window.close)

        for i, btn in enumerate(self.buttons.values()):
            if i > 0:
                layout.addSpacing(4)
            layout.addWidget(btn)

        self.update_styles()

    def update_state(self):
        """Вызывается из MainWindow при любых системных изменениях состояния окна."""
        main_window = self.parent()
        if not main_window:
            return

        is_maximized = (
            bool(main_window.windowState() & Qt.WindowState.WindowMaximized)
            or main_window.isFullScreen()
        )
        btn = self.buttons["maximize"]

        if _ensure_material_icons_loaded():
            btn.setText("\ue85f" if is_maximized else "\ue3c6")
        else:
            btn.setText("❐" if is_maximized else "□")

    def update_styles(self):
        """Обновляет стили TitleBar и всех кнопок при смене темы."""
        self.setStyleSheet(sf().build("title_bar"))

        # Обновляем стили всех кнопок
        for btn in self.buttons.values():
            btn.update_styles()
