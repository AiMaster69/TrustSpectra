from typing import Optional
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QPainter, QBrush, QColor
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QToolButton

from core.localization import get_text
from ui.styles.style_factory import sf


class SolidTooltip(QWidget):
    """Кастомное всплывающее окно-подсказка."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._bg_color = QColor("#1E1E1E")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(280)
        self.label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.label)

    def set_colors(self, bg_hex: str, text_hex: str):
        self._bg_color = QColor(bg_hex)
        self.label.setStyleSheet(f"color: {text_hex}; background: transparent; border: none;")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 4, 4)


class HintButton(QToolButton):
    """Кнопка с иконкой 'info', показывающая SolidTooltip при наведении."""
    def __init__(self, text_key: str, parent=None):
        super().__init__(parent)
        self._text_key = text_key
        self._popup: Optional[SolidTooltip] = None
        
        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.setInterval(200)
        self._show_timer.timeout.connect(self._show_popup)
        
        self.setAutoRaise(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText("\ue88e") # Иконка 'info'
        
        icon_font = QFont("Material Icons")
        icon_font.setPixelSize(18)
        self.setFont(icon_font)
        self.setFixedSize(24, 24)

    def _create_popup(self):
        if self._popup is None:
            self._popup = SolidTooltip()

    def _apply_popup_style(self):
        if not self._popup:
            return
            
        try:
            bg_color = sf().color("surface_alt")
        except Exception:
            try:
                bg_color = sf().color("surface")
            except Exception:
                bg_color = "#2D2D2D"
                
        try:
            text_color = sf().color("text")
        except Exception:
            text_color = "#FFFFFF"

        self._popup.set_colors(bg_color, text_color)

    def enterEvent(self, event):
        self._show_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._show_timer.stop()
        if self._popup:
            self._popup.hide()
        super().leaveEvent(event)

    def _show_popup(self):
        self._create_popup()
        self._popup.label.setText(get_text(self._text_key))
        self._apply_popup_style()
        self._popup.adjustSize()
        
        global_pos = self.mapToGlobal(QPoint(0, 0))
        popup_size = self._popup.sizeHint()
        
        x = global_pos.x() + (self.width() - popup_size.width()) // 2
        y = global_pos.y() - popup_size.height() - 8
        
        screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = max(geom.left() + 10, min(x, geom.right() - popup_size.width() - 10))
            if y < geom.top():
                y = global_pos.y() + self.height() + 8
                
        self._popup.move(x, y)
        self._popup.show()

    def update_texts(self):
        if self._popup:
            self._popup.label.setText(get_text(self._text_key))

    def update_styles(self):
        if self._popup and self._popup.isVisible():
            self._apply_popup_style()