import multiprocessing
import os
import tempfile

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.localization import get_text
from ui.styles.style_factory import sf


class CoreLineEdit(QLineEdit):
    def __init__(self, spinbox):
        super().__init__(spinbox)
        self.spinbox = spinbox

    def _max_pos(self):
        return max(0, len(self.text()) - len(self.spinbox.suffix()))

    def _clamp(self):
        max_pos = self._max_pos()
        if self.hasSelectedText():
            sel_start = self.selectionStart()
            sel_end = sel_start + len(self.selectedText())
            if sel_end > max_pos:
                if sel_start >= max_pos:
                    self.setCursorPosition(max_pos)
                else:
                    self.setSelection(sel_start, max_pos - sel_start)
        elif self.cursorPosition() > max_pos:
            self.setCursorPosition(max_pos)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._clamp()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self._clamp()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        max_pos = self._max_pos()
        if self.hasSelectedText():
            sel_start = self.selectionStart()
            sel_end = sel_start + len(self.selectedText())
            if sel_end > max_pos or sel_start >= max_pos:
                self.setSelection(0, max_pos)
        elif self.cursorPosition() > max_pos:
            self.setCursorPosition(max_pos)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        self._clamp()

    def contextMenuEvent(self, event):
        super().contextMenuEvent(event)
        self._clamp()

    def inputMethodEvent(self, event):
        super().inputMethodEvent(event)
        self._clamp()


class CoreSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_edit = CoreLineEdit(self)
        self.setLineEdit(self._line_edit)

    def wheelEvent(self, event):
        event.ignore()

    def stepEnabled(self):
        return (
            QAbstractSpinBox.StepEnabledFlag.StepUpEnabled
            | QAbstractSpinBox.StepEnabledFlag.StepDownEnabled
        )


class PerformanceWidget(QWidget):
    threadsChanged = pyqtSignal(int)

    def __init__(self, parent=None, initial_threads: int | None = None):
        super().__init__(parent)
        self._num_cores = multiprocessing.cpu_count()
        self._text_updaters = []
        self._styled_labels = []

        self._setup_ui()

        # Устанавливаем начальное значение: либо переданное, либо максимум
        start_value = (
            initial_threads if initial_threads is not None else self._num_cores
        )
        self.set_threads(start_value)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        row = QWidget()
        row.setMinimumHeight(52)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 8, 0, 8)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.threads_label = QLabel(get_text("ui.labels.cpu_threads"))
        self._text_updaters.append((self.threads_label, "ui.labels.cpu_threads"))
        self.threads_label.setMinimumWidth(120)

        self.threads_spinbox = CoreSpinBox()
        self.threads_spinbox.setMaximumWidth(80)
        self.threads_spinbox.setFixedHeight(32)
        self.threads_spinbox.setMinimum(1)
        self.threads_spinbox.setMaximum(self._num_cores)
        self.threads_spinbox.setSuffix(f" / {self._num_cores}")
        self.threads_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.threads_spinbox.valueChanged.connect(self.threadsChanged.emit)

        row_layout.addWidget(
            self.threads_label, alignment=Qt.AlignmentFlag.AlignVCenter
        )
        row_layout.addWidget(
            self.threads_spinbox, alignment=Qt.AlignmentFlag.AlignVCenter
        )
        row_layout.addStretch()

        layout.addWidget(row)

        self.info_label = self._create_info_label(
            "ui.labels.performance_info", bold=False
        )
        self.restart_label = self._create_info_label(
            "ui.labels.performance_restart", bold=True
        )

        layout.addWidget(self.info_label)
        layout.addWidget(self.restart_label)
        layout.addStretch()

    def _create_info_label(self, text_key: str, bold: bool) -> QLabel:
        label = QLabel(get_text(text_key))
        label.setWordWrap(True)
        self._text_updaters.append((label, text_key))
        self._styled_labels.append((label, bold))
        return label

    def set_threads(self, value: int):
        if not (1 <= value <= self._num_cores):
            raise ValueError(
                f"Допустимый диапазон: 1–{self._num_cores}, получено {value}"
            )

        self.threads_spinbox.blockSignals(True)
        self.threads_spinbox.setValue(value)
        self.threads_spinbox.blockSignals(False)

    def update_texts(self):
        for label, key in self._text_updaters:
            label.setText(get_text(key))

    def _generate_icon_path(self, char_code, color_hex):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )

        font = QFont("Material Icons", 24)
        painter.setFont(font)
        painter.setPen(QColor(color_hex))

        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, chr(char_code))
        painter.end()

        temp_dir = tempfile.gettempdir()
        filename = f"mat_icon_{char_code}_{color_hex.replace('#', '')}.png"
        file_path = os.path.join(temp_dir, filename).replace("\\", "/")
        pixmap.save(file_path, "PNG")

        return f'"{file_path}"'

    def update_styles(self):
        base_style = sf().build("spinbox")

        up_gray = self._generate_icon_path(0xE316, "#888888")
        up_light = self._generate_icon_path(0xE316, "#aaaaaa")
        down_gray = self._generate_icon_path(0xE313, "#888888")
        down_light = self._generate_icon_path(0xE313, "#aaaaaa")

        try:
            border_radius = sf().get("border_radius", "4px")
        except AttributeError:
            border_radius = "4px"

        custom_arrows_qss = f"""
            QSpinBox::up-button, QSpinBox::down-button {{
                subcontrol-origin: border;
                width: 20px;
                border: none;
                background: transparent;
            }}
            QSpinBox::up-button {{
                subcontrol-position: top right;
                border-top-right-radius: {border_radius};
            }}
            QSpinBox::down-button {{
                subcontrol-position: bottom right;
                border-bottom-right-radius: {border_radius};
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: rgba(128, 128, 128, 0.15);
            }}

            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                border: none;
                background: transparent;
                width: 20px;
                height: 16px;
            }}

            QSpinBox::up-arrow {{
                image: url({up_gray});
            }}
            QSpinBox::up-arrow:hover {{
                image: url({up_light});
            }}

            QSpinBox::down-arrow {{
                image: url({down_gray});
            }}
            QSpinBox::down-arrow:hover {{
                image: url({down_light});
            }}
        """

        self.threads_spinbox.setStyleSheet(base_style + custom_arrows_qss)

        for label, bold in self._styled_labels:
            color = sf().color("text") if bold else sf().color("secondary")
            weight = "bold" if bold else "normal"
            label.setStyleSheet(
                f"color: {color}; font-size: 10px; margin-top: 8px; font-weight: {weight}; border: none;"
            )
