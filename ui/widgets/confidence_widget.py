from functools import partial
from typing import Dict

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from core.localization import get_text
from ui.components.hint_button import HintButton
from ui.components.validators import FallbackDoubleValidator

# Константы
DEFAULT_CONFIDENCE = 0.9
ANALYSIS_CLASSES = ("claps", "heavy_breathing", "kisses", "moans")

class ConfidenceWidget(QWidget):
    confidenceChanged = pyqtSignal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._inputs: Dict[str, QLineEdit] = {}
        self._text_updaters = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        validator = FallbackDoubleValidator(0.0, 1.0, 2, DEFAULT_CONFIDENCE, self)

        for class_name in ANALYSIS_CLASSES:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel(get_text(f"classes.{class_name}"))
            label.setMinimumWidth(120)
            self._text_updaters.append((label, f"classes.{class_name}"))

            input_field = QLineEdit()
            input_field.setMaximumWidth(80)
            input_field.setFixedHeight(32)
            input_field.setPlaceholderText(f"{DEFAULT_CONFIDENCE:.2f}")
            input_field.setValidator(validator)
            
            input_field.editingFinished.connect(
                partial(self._on_editing_finished, class_name, input_field)
            )
            
            self._inputs[class_name] = input_field

            row_layout.addWidget(label)
            row_layout.addWidget(input_field)
            row_layout.addStretch()
            layout.addWidget(row)
            
        hint_layout = QHBoxLayout()
        hint_layout.setContentsMargins(0, 8, 0, 0)
        self.hint_button = HintButton("ui.labels.confidence_hint")
        hint_layout.addWidget(self.hint_button)
        hint_layout.addStretch()
        
        layout.addLayout(hint_layout)

    def _on_editing_finished(self, class_name: str, input_field: QLineEdit):
        text = input_field.text().strip()
        
        # 1. Обработка пустого ввода или одиночной точки
        if not text or text == ".":
            val = DEFAULT_CONFIDENCE
        else:
            try:
                val = float(text)
                # 2. АВТОКОРРЕКЦИЯ: Если ввели > 1.0, станет 1.0. Если < 0.0, станет 0.0.
                val = max(0.0, min(1.0, val))
            except ValueError:
                # Если ввели нечисловой мусор
                val = DEFAULT_CONFIDENCE
        
        # 3. Форматируем значение до 2 знаков и обновляем поле ввода.
        formatted_val = f"{val:.2f}"
        if input_field.text() != formatted_val:
            input_field.setText(formatted_val)

        # Отправляем в программу гарантированно корректное число
        self.confidenceChanged.emit(class_name, val)

    def set_values(self, thresholds: dict):
        for class_name, input_field in self._inputs.items():
            if class_name in thresholds:
                try:
                    # Применяем ту же логику автокоррекции для значений извне
                    safe_val = max(0.0, min(1.0, float(thresholds[class_name])))
                    input_field.setText(f"{safe_val:.2f}")
                except (ValueError, TypeError):
                    input_field.setText(f"{DEFAULT_CONFIDENCE:.2f}")

    def update_texts(self):
        for label, key in self._text_updaters:
            label.setText(get_text(key))
        self.hint_button.update_texts()

    def update_styles(self):
        self.hint_button.update_styles()