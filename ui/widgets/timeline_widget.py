from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QFrame,
                             QLabel, QHBoxLayout, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor
from typing import List, Dict, Any, Tuple
from core.localization import get_text
from ui.styles.style_factory import sf


class TimelineWidget(QWidget):
    """Виджет временной шкалы."""
    marker_clicked = pyqtSignal(float)
    time_clicked = pyqtSignal(str, float)

    def __init__(self):
        super().__init__()
        self.markers = []
        self.duration = 0
        self.file_blocks = {}
        self._widget_pool = []
        self._active_widgets = []
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._perform_update)
        self._pending_results = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.results_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_scroll.setStyleSheet(self._get_horizontal_scrollbar_style())

        self.results_container = QWidget()
        self.results_container.setObjectName("results_container")
        self.results_layout = QHBoxLayout(self.results_container)
        m = sf().size('results_contents_margin', 10)
        self.results_layout.setContentsMargins(m, m, m, m)
        self.results_layout.setSpacing(sf().size('results_spacing', 10))
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.results_scroll.setWidget(self.results_container)
        layout.addWidget(self.results_scroll)

        self.timeline_scroll = QScrollArea()
        self.timeline_scroll.setWidgetResizable(True)
        self.timeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.timeline_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.timeline_scroll.setStyleSheet(self._get_horizontal_scrollbar_style())

        self.draw_widget = TimelineDrawWidget(self)
        self.timeline_scroll.setWidget(self.draw_widget)
        self.timeline_scroll.hide()
        layout.addWidget(self.timeline_scroll)

        self.setMinimumHeight(sf().size("timeline_height", 150))
        self.update_styles()

    def _get_horizontal_scrollbar_style(self) -> str:
        return f"""
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        {sf().build('scrollbar_thin_horizontal')}
        """

    def _get_vertical_scrollbar_style(self) -> str:
        return f"""
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        {sf().build('scrollbar_thin_vertical')}
        """

    def start_analysis(self, file_paths):
        try:
            for file_path in file_paths:
                if file_path in self.file_blocks:
                    continue
                file_block = self._create_progress_file_block(file_path)
                self.file_blocks[file_path] = file_block

                count = self.results_layout.count()
                if count > 0 and self.results_layout.itemAt(count - 1).spacerItem():
                    self.results_layout.insertWidget(count - 1, file_block)
                else:
                    self.results_layout.addWidget(file_block)
                self._active_widgets.append(file_block)

            count = self.results_layout.count()
            if count == 0 or not self.results_layout.itemAt(count - 1).spacerItem():
                self.results_layout.addStretch()

            self.results_container.update()
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Ошибка начала анализа: {e}")
            import traceback
            traceback.print_exc()

    def update_file_progress(self, file_path, progress_percent, estimated_time_remaining=None):
        if file_path in self.file_blocks:
            file_block = self.file_blocks[file_path]
            progress_label = file_block.findChild(QLabel, "progress_label")
            if progress_label:
                text = f"{int(progress_percent)}%"
                if estimated_time_remaining is not None and estimated_time_remaining > 0:
                    if estimated_time_remaining < 60:
                        time_str = f"{int(estimated_time_remaining)}s"
                    else:
                        minutes = int(estimated_time_remaining // 60)
                        seconds = int(estimated_time_remaining % 60)
                        time_str = f"{minutes}m {seconds}s"
                    text += f"\n~{time_str}"
                progress_label.setText(text)
                progress_label.update()
                file_block.update()

    def update_file_result(self, file_path, analysis_result):
        try:
            if file_path not in self.file_blocks:
                new_block = self._create_file_block_optimized(file_path, analysis_result)
                self.file_blocks[file_path] = new_block

                count = self.results_layout.count()
                if count > 0 and self.results_layout.itemAt(count - 1).spacerItem():
                    self.results_layout.insertWidget(count - 1, new_block)
                else:
                    self.results_layout.addWidget(new_block)
                self._active_widgets.append(new_block)
                new_block.show()
                return

            old_block = self.file_blocks[file_path]
            insert_index = -1
            for i in range(self.results_layout.count()):
                item = self.results_layout.itemAt(i)
                if item and item.widget() == old_block:
                    insert_index = i
                    break

            self.results_layout.removeWidget(old_block)
            if old_block in self._active_widgets:
                self._active_widgets.remove(old_block)
            old_block.deleteLater()

            new_block = self._create_file_block_optimized(file_path, analysis_result)
            if insert_index >= 0:
                self.results_layout.insertWidget(insert_index, new_block)
            else:
                count = self.results_layout.count()
                if count > 0 and self.results_layout.itemAt(count - 1).spacerItem():
                    self.results_layout.insertWidget(count - 1, new_block)
                else:
                    self.results_layout.addWidget(new_block)

            self.file_blocks[file_path] = new_block
            self._active_widgets.append(new_block)
            new_block.show()
            new_block.update()
            self.results_container.update()
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Ошибка обновления результата файла: {e}")
            import traceback
            traceback.print_exc()

    def show_multiple_analysis_results(self, results_list: List[Tuple[str, Any]]):
        self._pending_results = results_list
        self._update_timer.start(sf().size('update_timer_delay', 50))

    def _perform_update(self):
        try:
            self.clear_analysis_results()
            for file_path, analysis_result in self._pending_results:
                file_block = self._create_file_block_optimized(file_path, analysis_result)
                self.file_blocks[file_path] = file_block
                self.results_layout.addWidget(file_block)
                self._active_widgets.append(file_block)

            self.results_layout.addStretch()
            self.results_container.update()
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Ошибка отображения результатов: {e}")
            import traceback
            traceback.print_exc()

    def _create_progress_file_block(self, file_path: str) -> QFrame:
        main_frame = QFrame()
        main_frame.setObjectName("file_block")
        main_frame.setFixedWidth(sf().size('file_block_width', 300))
        main_frame.setMinimumHeight(sf().size('progress_block_min_height', 150))
        main_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        main_frame.setStyleSheet(sf().build('file_block'))

        main_layout = QVBoxLayout(main_frame)
        m = sf().size('file_block_margin', 5)
        main_layout.setContentsMargins(m, m, m, m)
        main_layout.setSpacing(sf().size('file_block_spacing', 8))

        progress_label = QLabel("0%")
        progress_label.setObjectName("progress_label")
        progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_label_font = QFont()
        progress_label_font.setPixelSize(sf().size('progress_font_size', 18))
        progress_label_font.setBold(True)
        progress_label.setFont(progress_label_font)
        progress_label.setStyleSheet(sf().build('progress_label'))

        main_layout.addStretch()
        main_layout.addWidget(progress_label)
        main_layout.addStretch()

        return main_frame

    def _create_file_block_optimized(self, file_path: str, analysis_result) -> QFrame:
        import os
        filename = os.path.basename(file_path)

        main_frame = QFrame()
        main_frame.setObjectName("file_block")
        main_frame.setFixedWidth(sf().size('file_block_width', 300))
        main_frame.setMinimumHeight(sf().size('file_block_min_height', 200))
        main_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        main_frame.setStyleSheet(sf().build('file_block'))

        main_layout = QVBoxLayout(main_frame)
        m = sf().size('file_block_margin', 5)
        main_layout.setContentsMargins(m, m, m, m)
        main_layout.setSpacing(sf().size('file_block_spacing', 8))

        file_header = self._create_file_header(filename)
        main_layout.addWidget(file_header)

        if hasattr(analysis_result, "total_duration"):
            total_duration = analysis_result.total_duration
            segments = analysis_result.segments
        elif isinstance(analysis_result, dict):
            total_duration = analysis_result.get("file_duration", 0)
            segments = analysis_result.get("segments", [])
        else:
            total_duration = 0
            segments = []

        info_text = (
            f"{get_text('ui.labels.duration')}: {total_duration:.1f}s\n"
            f"{get_text('ui.labels.segments')}: {len(segments)}"
        )

        info_label = QLabel(info_text)
        info_label.setObjectName("file_info")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label_font = QFont()
        info_label_font.setPixelSize(sf().size('info_font_size', 13))
        info_label.setFont(info_label_font)
        info_label.setStyleSheet(sf().build('file_info'))
        main_layout.addWidget(info_label)

        segments_scroll = self._create_segments_scroll(segments, file_path)
        main_layout.addWidget(segments_scroll, stretch=1)

        return main_frame

    def _create_file_header(self, filename: str) -> QLabel:
        file_header = QLabel(filename)
        file_header.setObjectName("file_header")
        file_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_header.setWordWrap(True)
        file_header_font = QFont()
        file_header_font.setPixelSize(sf().size('header_font_size', 16))
        file_header_font.setBold(True)
        file_header.setFont(file_header_font)
        file_header.setStyleSheet(sf().build('file_header'))
        return file_header

    def _create_segments_scroll(self, segments: List, file_path: str) -> QScrollArea:
        segments_scroll = QScrollArea()
        segments_scroll.setWidgetResizable(True)
        segments_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        segments_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        segments_scroll.setStyleSheet(self._get_vertical_scrollbar_style())

        segments_container = QWidget()
        segments_layout = QVBoxLayout(segments_container)
        sm = sf().size('segment_container_margin', 2)
        segments_layout.setContentsMargins(sm, sm, sm, sm)
        segments_layout.setSpacing(sf().size('segment_container_spacing', 4))

        if segments:
            segment_blocks = [
                self._create_segment_block_optimized(i + 1, segment, file_path)
                for i, segment in enumerate(segments)
            ]
            for block in segment_blocks:
                segments_layout.addWidget(block)
        else:
            no_results_label = QLabel(get_text("ui.labels.no_segments"))
            no_results_label.setObjectName("no_results_label")
            no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results_label.setStyleSheet(
                f"color: {sf().color('secondary')}; "
                f"font-style: italic; "
                f"padding: {sf().size('padding', 12)}px;"
            )
            segments_layout.addWidget(no_results_label)

        segments_layout.addStretch()
        segments_scroll.setWidget(segments_container)
        return segments_scroll

    def _create_segment_block_optimized(self, index: int, segment, file_path: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("segment_block")
        frame.setMinimumHeight(sf().size('segment_min_height', 50))
        frame.setMaximumHeight(sf().size('segment_max_height', 60))
        frame.setStyleSheet(sf().build('segment_block'))

        layout = QHBoxLayout(frame)
        h = sf().size('segment_padding_h', 8)
        v = sf().size('segment_padding_v', 6)
        layout.setContentsMargins(h, v, h, v)
        layout.setSpacing(sf().size('segment_spacing', 8))

        if isinstance(segment, dict):
            start_time = segment.get("segment_start", segment.get("start_time", 0))
            label = segment.get("label", "unknown")
            confidence = segment.get("confidence", 0.5)
        elif hasattr(segment, "start_time"):
            start_time = segment.start_time
            label = segment.label
            confidence = segment.confidence
        elif hasattr(segment, "segment_start"):
            start_time = segment.segment_start
            label = segment.label
            confidence = segment.confidence
        else:
            start_time = 0
            label = "unknown"
            confidence = 0.5

        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            if hours > 0:
                return f"{hours}h {minutes}m {secs}s"
            elif minutes > 0:
                return f"{minutes}m {secs}s"
            else:
                return f"{secs}s"

        time_button = self._create_time_button_formatted(
            start_time, file_path, format_time(start_time)
        )
        time_button.setMinimumWidth(sf().size('time_button_min_width', 70))
        time_button_font = QFont()
        time_button_font.setPixelSize(sf().size('segment_font_size', 13))
        time_button_font.setBold(True)
        time_button.setFont(time_button_font)
        layout.addWidget(time_button)

        class_name = get_text(f"classes.{label}")
        class_label = QLabel(class_name)
        class_label.setObjectName("class_label")
        class_label.setProperty("label_key", label)
        class_label.setWordWrap(True)
        class_font = QFont()
        class_font.setBold(True)
        class_font.setPixelSize(sf().size('segment_font_size', 13))
        class_label.setFont(class_font)
        class_label.setMinimumWidth(sf().size('class_label_min_width', 100))
        class_label.setMaximumWidth(sf().size('class_label_max_width', 140))
        layout.addWidget(class_label)

        confidence_label = QLabel(f"{confidence:.1%}")
        confidence_font = QFont()
        confidence_font.setPixelSize(sf().size('segment_font_size', 13))
        confidence_label.setFont(confidence_font)
        confidence_label.setStyleSheet(f"color: {sf().color('secondary')};")
        confidence_label.setMinimumWidth(sf().size('confidence_min_width', 45))
        layout.addWidget(confidence_label)

        layout.addStretch()
        return frame

    def _create_time_button(self, start_time: float, file_path: str) -> QPushButton:
        return self._create_time_button_formatted(file_path, file_path, f"{start_time:.2f}s")

    def _create_time_button_formatted(self, start_time: float, file_path: str, formatted_time: str) -> QPushButton:
        time_button = QPushButton(formatted_time)
        time_button.setStyleSheet(sf().build('time_button'))
        time_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        time_button.clicked.connect(lambda: self.time_clicked.emit(file_path, start_time))
        return time_button

    def update_texts(self):
        for file_path, file_block in self.file_blocks.items():
            progress_label = file_block.findChild(QLabel, "progress_label")
            if progress_label and get_text("ui.labels.analysis") in progress_label.text():
                try:
                    percent = progress_label.text().split(":")[-1].strip()
                    progress_label.setText(f"{get_text('ui.labels.analysis')}: {percent}")
                except Exception:
                    pass

            info_label = file_block.findChild(QLabel, "file_info")
            if info_label:
                try:
                    lines = info_label.text().split("\n")
                    if len(lines) >= 2:
                        duration_val = lines[0].split(":")[-1].strip()
                        segments_val = lines[1].split(":")[-1].strip()
                        info_label.setText(
                            f"{get_text('ui.labels.duration')}: {duration_val}\n"
                            f"{get_text('ui.labels.segments')}: {segments_val}"
                        )
                except Exception:
                    pass

            no_results = file_block.findChild(QLabel, "no_results_label")
            if no_results:
                no_results.setText(get_text("ui.labels.no_segments"))

            for segment_block in file_block.findChildren(QFrame, "segment_block"):
                class_label = segment_block.findChild(QLabel, "class_label")
                if class_label:
                    label_key = class_label.property("label_key")
                    if label_key:
                        class_label.setText(get_text(f"classes.{label_key}"))

    def _get_widget_from_pool(self) -> QFrame:
        if self._widget_pool:
            return self._widget_pool.pop()
        return None

    def _return_widget_to_pool(self, widget: QFrame):
        if len(self._widget_pool) < 10:
            self._widget_pool.append(widget)
        else:
            widget.deleteLater()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def clear_analysis_results(self):
        try:
            while self.results_layout.count() > 0:
                item = self.results_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
            self._active_widgets.clear()
            self.file_blocks.clear()
            self.results_container.update()
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Ошибка очистки результатов: {e}")
            import traceback
            traceback.print_exc()

    def update_styles(self):
        self.setStyleSheet(sf().build('timeline_widget'))
        self.results_scroll.setStyleSheet(self._get_horizontal_scrollbar_style())
        self.timeline_scroll.setStyleSheet(self._get_horizontal_scrollbar_style())

        try:
            for i in range(self.results_layout.count()):
                item = self.results_layout.itemAt(i)
                w = item.widget() if item else None
                if not w:
                    continue
                w.setStyleSheet(sf().build('file_block'))

                header = w.findChild(QLabel, "file_header")
                if header:
                    header.setStyleSheet(sf().build('file_header'))

                info = w.findChild(QLabel, "file_info")
                if info:
                    info.setStyleSheet(sf().build('file_info'))

                progress = w.findChild(QLabel, "progress_label")
                if progress:
                    progress.setStyleSheet(sf().build('progress_label'))

                for segment in w.findChildren(QFrame, "segment_block"):
                    segment.setStyleSheet(sf().build('segment_block'))
        except Exception:
            pass

    def show_analysis_results(self, file_path: str, analysis_result):
        self.show_multiple_analysis_results([(file_path, analysis_result)])

    def set_duration(self, duration):
        self.duration = duration
        if hasattr(self, "draw_widget"):
            self.draw_widget.update()

    def add_marker(self, time, label):
        self.markers.append((time, label))
        self.markers.sort(key=lambda x: x[0])
        if hasattr(self, "draw_widget"):
            self.draw_widget.update()

    def clear_markers(self):
        self.markers.clear()
        if hasattr(self, "draw_widget"):
            self.draw_widget.update()

    def on_player_dragging_started(self):
        if hasattr(self, "draw_widget"):
            self.draw_widget._is_scrolling = True

    def on_player_dragging_stopped(self):
        if hasattr(self, "draw_widget"):
            self.draw_widget._is_scrolling = False
            self.draw_widget.update()


class TimelineDrawWidget(QFrame):
    """Виджет для рисования временной шкалы."""

    def __init__(self, parent):
        super().__init__(parent)
        self._timeline_widget = parent
        self.setMinimumWidth(sf().size('timeline_min_width', 1000))
        self._hover_time = None
        self._is_scrolling = False
        self.setMouseTracking(True)
        self._cached_painter_settings = None

    def paintEvent(self, event):
        if not self._timeline_widget.duration:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._cached_painter_settings:
            self._cached_painter_settings = {
                "text_color": QColor(sf().color("text")),
                "marker_color": QColor(sf().color("primary")),
                "hover_color": QColor(sf().color("button_hover")),
            }
        colors = self._cached_painter_settings

        hover_line_width = sf().size('timeline_hover_line_width', 1)
        hover_offset_x = sf().size('timeline_hover_text_offset_x', 5)
        hover_offset_y = sf().size('timeline_hover_text_offset_y', 5)
        marker_line_width = sf().size('timeline_marker_line_width', 2)
        marker_offset_x = sf().size('timeline_marker_text_offset_x', 5)
        marker_offset_y = sf().size('timeline_marker_text_offset_y', 20)

        if self._hover_time is not None:
            x = int(self._hover_time * self.width() / self._timeline_widget.duration)
            painter.setPen(QPen(colors["hover_color"], hover_line_width, Qt.PenStyle.DashLine))
            painter.drawLine(x, 0, x, self.height())

            time_text = f"{int(self._hover_time // 60)}:{int(self._hover_time % 60):02d}"
            painter.setPen(colors["text_color"])
            painter.drawText(x + hover_offset_x, self.height() - hover_offset_y, time_text)

        if self._timeline_widget.markers:
            width_ratio = self.width() / self._timeline_widget.duration
            for time, label in self._timeline_widget.markers:
                x = int(time * width_ratio)
                painter.setPen(QPen(colors["marker_color"], marker_line_width))
                painter.drawLine(x, 0, x, self.height())
                painter.setPen(colors["text_color"])
                painter.drawText(x + marker_offset_x, marker_offset_y, label)

    def mouseMoveEvent(self, event):
        if self._timeline_widget.duration:
            pos = event.position().x()
            new_hover_time = (pos * self._timeline_widget.duration) / self.width()

            if not self._is_scrolling:
                if new_hover_time != self._hover_time:
                    self._hover_time = new_hover_time
                    self.update()

            if event.buttons() & Qt.MouseButton.LeftButton:
                self._handle_click(event)

    def leaveEvent(self, event):
        if not self._is_scrolling:
            self._hover_time = None
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._timeline_widget.duration:
            self._is_scrolling = True
            self._handle_click(event)

    def _handle_click(self, event):
        pos = event.position().x()
        time_ms = int((pos / self.width()) * self._timeline_widget.duration * 1000)
        time_ms = max(0, min(time_ms, self._timeline_widget.duration * 1000))
        self._timeline_widget.marker_clicked.emit(time_ms)