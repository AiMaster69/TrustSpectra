from PyQt6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.localization import get_text
from ui.styles.style_factory import sf
from ui.styles.themes import COLORS


class BaseThemedDialog(QDialog):
    """
    Универсальный базовый класс для всех всплывающих окон.
    Берет на себя настройку окна, анимации, стили, иконки, заголовок и текст.
    """

    def __init__(
        self, parent=None, title: str = "", message: str = "", icon_type: str = "info"
    ):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.icon_type = icon_type
        self.title_text = title
        self.message_text = message

        self._setup_colors()
        self._setup_base_ui()
        self._apply_styles()

        self._animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._animation.setDuration(150)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def _setup_colors(self):
        icon_map = {
            "error": ("#F44336", "✕"),
            "warning": ("#FF9800", "⚠"),
            "success": ("#4CAF50", "✓"),
            "info": ("#2196F3", "ℹ"),
        }
        color_key = self.icon_type if self.icon_type in icon_map else "info"
        self.icon_color = COLORS.get(color_key, icon_map[color_key][0])
        self.icon_text = icon_map[color_key][1]

    def _setup_base_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("dialogContent")

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 30, 30, 20)

        header_layout = QHBoxLayout()

        self.icon_label = QLabel(self.icon_text)
        self.icon_label.setObjectName("dialogIcon")
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_font = QFont()
        icon_font.setPointSize(20)
        self.icon_label.setFont(icon_font)
        header_layout.addWidget(self.icon_label)

        title_label = QLabel(self.title_text)
        title_label.setObjectName("dialogTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        content_layout.addLayout(header_layout)

        message_label = QLabel(self.message_text)
        message_label.setObjectName("dialogMessage")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        content_layout.addWidget(message_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(12)
        self.button_layout.addStretch()

        content_layout.addLayout(self.button_layout)
        main_layout.addWidget(self.content_widget)

        self.setMinimumWidth(440)
        self.setMaximumWidth(640)

    def _apply_styles(self):
        # Получаем общие стили окна и кнопок из StyleFactory
        base_stylesheet = sf().build("themed_dialog")
        # Локально меняем ТОЛЬКО цвет самой иконки (чтобы ⚠ был оранжевым, а ✕ красным)
        icon_stylesheet = f"QLabel#dialogIcon {{ color: {self.icon_color}; }}"

        self.content_widget.setStyleSheet(base_stylesheet + "\n" + icon_stylesheet)

    def changeEvent(self, event):
        if event.type() in (
            QEvent.Type.StyleChange,
            QEvent.Type.ApplicationPaletteChange,
        ):
            self._setup_colors()
            self._apply_styles()
        super().changeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.center().x() - self.width() // 2,
                parent_rect.center().y() - self.height() // 2,
            )
        if self._animation.state() != QPropertyAnimation.State.Running:
            self.setWindowOpacity(0.0)
            self._animation.start()

    def closeEvent(self, event):
        self._animation.stop()
        super().closeEvent(event)


class ThemedDialog(BaseThemedDialog):
    def __init__(
        self, parent=None, title: str = "", message: str = "", icon_type: str = "info"
    ):
        super().__init__(parent, title, message, icon_type)

        self.ok_button = QPushButton("OK")
        self.ok_button.setObjectName("dialogConfirmButton")
        self.ok_button.setFixedHeight(
            36
        )  # Фиксируем только высоту! Ширина подстроится под текст
        self.ok_button.setMinimumWidth(
            100
        )  # Но делаем не меньше 100px, чтобы не была крошечной
        self.ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ok_button.clicked.connect(self.accept)

        self.button_layout.addWidget(self.ok_button)


class ThemedConfirmDialog(BaseThemedDialog):
    def __init__(
        self,
        parent=None,
        title: str = "",
        message: str = "",
        icon_type: str = "warning",
        cancel_text: str = "Cancel",
        confirm_text: str = "Continue",
    ):
        super().__init__(parent, title, message, icon_type)

        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.setObjectName("dialogCancelButton")
        self.cancel_button.setFixedHeight(36)
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)

        self.confirm_button = QPushButton(confirm_text)
        self.confirm_button.setObjectName("dialogConfirmButton")
        self.confirm_button.setFixedHeight(36)
        self.confirm_button.setMinimumWidth(100)
        self.confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_button.setDefault(True)
        self.confirm_button.clicked.connect(self.accept)

        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.confirm_button)


class AIWarningDialog(BaseThemedDialog):
    def __init__(self, parent=None, settings_service=None):
        super().__init__(
            parent,
            title=get_text("ui.messages.ai_warning_title"),
            message=get_text("ui.messages.ai_warning_message"),
            icon_type="warning",
        )
        self.settings_service = settings_service

        self.dont_show_button = QPushButton(get_text("ui.buttons.dont_show_again"))
        self.dont_show_button.setObjectName("dialogCancelButton")
        self.dont_show_button.setFixedHeight(36)
        # Тут не ставим MinWidth, кнопка сама растянется под длинный текст "Больше не показывать"
        self.dont_show_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dont_show_button.clicked.connect(self._on_dont_show_again)

        self.ok_button = QPushButton(get_text("ui.buttons.ok"))
        self.ok_button.setObjectName("dialogConfirmButton")
        self.ok_button.setFixedHeight(36)
        self.ok_button.setMinimumWidth(100)
        self.ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)

        self.button_layout.addWidget(self.dont_show_button)
        self.button_layout.addWidget(self.ok_button)

    def _on_dont_show_again(self):
        if self.settings_service:
            settings = self.settings_service.get_all_settings()
            if "ui" not in settings:
                settings["ui"] = {}
            settings["ui"]["show_ai_warning"] = False
            self.settings_service.set_all_settings(settings)
        self.accept()


class ThemedMessageBox:
    @staticmethod
    def _show(parent, title: str, message: str, icon_type: str) -> int:
        dialog = ThemedDialog(parent, title, message, icon_type)
        return dialog.exec()

    @staticmethod
    def information(parent, title: str, message: str) -> int:
        return ThemedMessageBox._show(parent, title, message, "info")

    @staticmethod
    def warning(parent, title: str, message: str) -> int:
        return ThemedMessageBox._show(parent, title, message, "warning")

    @staticmethod
    def critical(parent, title: str, message: str) -> int:
        return ThemedMessageBox._show(parent, title, message, "error")

    @staticmethod
    def success(parent, title: str, message: str) -> int:
        return ThemedMessageBox._show(parent, title, message, "success")

    @staticmethod
    def confirm(
        parent,
        title: str,
        message: str,
        icon_type: str = "warning",
        cancel_text: str = "Cancel",
        confirm_text: str = "Continue",
    ) -> int:
        dialog = ThemedConfirmDialog(
            parent, title, message, icon_type, cancel_text, confirm_text
        )
        return dialog.exec()
