import os

from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.styles.style_factory import sf
from ui.styles.themes import COLORS, SIZES

# Опциональный импорт mutagen
try:
    from mutagen import File as MutagenFile

    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    MutagenFile = None


class WorkerSignals(QObject):
    """Сигналы для возврата результата из фонового потока."""

    finished = pyqtSignal(str, int)  # file_path, duration


class MetadataWorker(QRunnable):
    """Читает метаданные аудио в фоновом потоке."""

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.signals = WorkerSignals()

    def run(self):
        if not MUTAGEN_AVAILABLE:
            self.signals.finished.emit(self.file_path, 0)
            return

        try:
            audio = MutagenFile(self.file_path)
            if audio and hasattr(audio, "info") and hasattr(audio.info, "length"):
                duration = int(audio.info.length)
            else:
                duration = 0
        except Exception:
            duration = 0

        self.signals.finished.emit(self.file_path, duration)


class FileItemWidget(QFrame):
    """Виджет элемента файла в списке."""

    deleted = pyqtSignal(str)
    selected = pyqtSignal(str)

    def __init__(
        self, file_path: str, file_size: int, duration: int = None, parent=None
    ):
        super().__init__(parent)
        self.file_path = file_path
        self.file_size = file_size
        self.duration = duration

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        self.setFixedHeight(70)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 12, 12, 12)

        # Заголовок: имя файла + кнопка удаления в одном layout
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        self.name_label = QLabel(os.path.basename(self.file_path))
        self.name_label.setMaximumHeight(20)

        self.delete_button = QPushButton("\ue5cd")
        self.delete_button.setFont(QFont("Material Icons", 18))
        self.delete_button.setFixedSize(32, 32)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_button.clicked.connect(self._on_delete)

        header_layout.addWidget(self.name_label, 1)  # stretch
        header_layout.addWidget(self.delete_button)

        # Длительность и размер
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)

        if self.duration is not None and self.duration > 0:
            self.duration_label = QLabel(
                f"{self.duration // 60}:{self.duration % 60:02d}"
            )
        else:
            self.duration_label = QLabel("--:--")

        self.size_label = QLabel(self._format_size(self.file_size))

        info_layout.addWidget(self.duration_label)
        info_layout.addStretch()
        info_layout.addWidget(self.size_label)

        layout.addLayout(header_layout)
        layout.addLayout(info_layout)
        layout.addStretch()

    def _on_delete(self):
        self.deleted.emit(self.file_path)

    def set_duration(self, duration: int):
        """Обновляет длительность, когда фоновый поток вернул результат."""
        self.duration = duration
        if duration > 0:
            self.duration_label.setText(f"{duration // 60}:{duration % 60:02d}")
        else:
            self.duration_label.setText("--:--")

    def set_item_width(self, width: int):
        """Обновляет ширину при resize родителя."""
        self.setFixedWidth(width)

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.file_path)

    def _apply_styles(self):
        """Применяет стили. Вызывается один раз при создании."""
        self.setStyleSheet(
            f"""
            FileItemWidget {{
                background: {COLORS['button_bg']};
                border-radius: {SIZES['radius']}px;
            }}
            FileItemWidget:hover {{
                background: {COLORS['button_hover']};
            }}
            QLabel {{
                color: {COLORS['text']};
                background: transparent;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text']};
                padding: 0;
            }}
            QPushButton:hover {{
                color: {COLORS['error']};
            }}
        """
        )
        self.duration_label.setStyleSheet(f"color: {COLORS['secondary']}")
        self.size_label.setStyleSheet(f"color: {COLORS['secondary']}")


class FileListWidget(QWidget):
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = {}  # file_path -> FileItemWidget
        self.thread_pool = QThreadPool()
        self._pending_workers = {}  # file_path -> MetadataWorker

        # Скрыт до появления файлов
        self.setFixedHeight(0)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setStyleSheet(sf().build("scrollbar"))
        # Убираем рамку, которая даёт лишние пиксели
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(SIZES["spacing"])
        # Симметричные отступы сверху и снизу
        self.grid.setContentsMargins(0, SIZES["spacing"], 0, SIZES["spacing"])
        self.grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)

    def _get_scrollbar_style(self):
        return f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 8px;
                background: transparent;
                border: none;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['primary']};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::up-arrow:vertical,
            QScrollBar::down-arrow:vertical {{
                border: none;
                background: none;
                height: 0;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """

    def _update_height(self):
        """Обновляет высоту виджета в зависимости от количества строк."""
        if not self.files:
            self.setFixedHeight(0)
        else:
            rows = (len(self.files) + 2) // 3
            # rows * высота_элемента + spacing между ними + отступы сверху и снизу
            total_height = (
                (rows * 70) + max(0, rows - 1) * SIZES["spacing"] + 2 * SIZES["spacing"]
            )
            self.setFixedHeight(total_height)

    def update_styles(self):
        """Обновляет стили при смене темы (вызывать вручную)."""
        self.scroll_area.setStyleSheet(sf().build("scrollbar"))
        for widget in self.files.values():
            widget._apply_styles()

    def _get_item_width(self) -> int:
        available = self.scroll_area.viewport().width() - SIZES["spacing"] * 4
        return max(available // 3, 200)

    def _update_item_widths(self):
        """Обновляет ширину всех элементов при resize."""
        width = self._get_item_width()
        for widget in self.files.values():
            widget.set_item_width(width)

    def _get_grid_position(self, index: int):
        return (index // 3, index % 3)

    def add_file(self, file_path: str):
        """
        Добавляет файл в список. Создаёт виджет сразу,
        метаданные читает в фоне.
        """
        if file_path in self.files:
            return

        try:
            size = os.path.getsize(file_path)
        except OSError:
            size = 0

        item = FileItemWidget(file_path, size, duration=None)
        item.deleted.connect(self.remove_file)
        item.selected.connect(self.file_selected.emit)

        width = self._get_item_width()
        item.set_item_width(width)

        index = len(self.files)
        row, col = self._get_grid_position(index)
        self.grid.addWidget(item, row, col)

        self.files[file_path] = item

        # Обновляем высоту — отодвигаем нижний контент
        self._update_height()

        # Читаем длительность в фоновом потоке
        self._load_metadata(file_path)

    def _load_metadata(self, file_path: str):
        worker = MetadataWorker(file_path)
        worker.signals.finished.connect(self._on_metadata_loaded)
        self._pending_workers[file_path] = worker
        self.thread_pool.start(worker)

    def _on_metadata_loaded(self, file_path: str, duration: int):
        self._pending_workers.pop(file_path, None)
        if file_path in self.files:
            self.files[file_path].set_duration(duration)

    def remove_file(self, file_path: str):
        """
        Удаляет файл из списка. Убирает виджет из layout,
        переупорядочивает оставшиеся.
        """
        if file_path not in self.files:
            return

        # Отменяем pending worker если есть
        self._pending_workers.pop(file_path, None)

        item = self.files.pop(file_path)
        self.grid.removeWidget(item)
        item.deleteLater()

        # Переупорядочиваем оставшиеся и обновляем высоту
        self._reorder_grid()
        self._update_height()

    def _reorder_grid(self):
        """Переставляет существующие виджеты в сетке без их пересоздания."""
        # Убираем из layout (виджеты не удаляем!)
        while self.grid.count():
            self.grid.takeAt(0)

        for i, widget in enumerate(self.files.values()):
            row, col = self._get_grid_position(i)
            self.grid.addWidget(widget, row, col)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Только меняем ширину, не трогаем стили и не пересоздаём виджеты
        self._update_item_widths()

    def clear(self):
        """Удаляет все файлы."""
        for path in list(self.files.keys()):
            self.remove_file(path)
