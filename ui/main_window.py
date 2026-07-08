import os
import platform
import sys
import time
from typing import Optional

from PyQt6.QtCore import QEvent, QPoint, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QIcon, QMouseEvent, QScreen
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.localization import LocalizationService, get_text
from core.services.settings_service import SettingsService
from ui.controllers.main_controller import MainController
from ui.styles.style_factory import refresh_all_styles, sf
from ui.styles.themes import COLORS, SIZES, save_theme, update_theme_colors
from ui.widgets.file_list_widget import FileListWidget
from ui.widgets.player_widget import PlayerWidget
from ui.widgets.settings_widget import SettingsWidget
from ui.widgets.themed_dialog import AIWarningDialog, ThemedMessageBox
from ui.widgets.timeline_widget import TimelineWidget
from ui.widgets.title_bar import TitleBar
from utils.exceptions import TrustSpectraError
from utils.logger import logger
from utils.taskbar_progress import TaskbarProgressManager


class AnalysisWorker(QThread):
    progress = pyqtSignal(str, int, float)
    file_finished = pyqtSignal(str, object)
    error = pyqtSignal(str, str)
    all_finished = pyqtSignal()

    def __init__(self, controller: MainController, files_to_analyze: list[str]) -> None:
        super().__init__()
        self.controller = controller
        self.files = files_to_analyze
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True
        self.wait(3000)

    def run(self) -> None:
        for file_path in self.files:
            if self._stop_requested:
                break
            try:
                start_time = time.time()

                def progress_cb(percent: int) -> None:
                    if percent > 0:
                        elapsed = time.time() - start_time
                        remaining = (elapsed / (percent / 100)) - elapsed
                    else:
                        remaining = 0.0
                    self.progress.emit(file_path, percent, remaining)

                result = self.controller.analyze_file(
                    file_path, progress_callback=progress_cb
                )
                self.file_finished.emit(file_path, result)
            except Exception as e:
                self.error.emit(file_path, str(e))

        self.all_finished.emit()


class MainWindow(QMainWindow):
    BASE_EDGE_GRIP = 6
    TITLE_BAR_RESIZE_THRESHOLD = 160

    def __init__(self) -> None:
        super().__init__()

        self.settings_service = SettingsService()
        self.controller = MainController(self.settings_service)
        self.localization = LocalizationService()

        # Определяем тему ОС при старте
        self._real_os_theme = self._detect_real_os_theme()

        ui_settings = self.settings_service.get_category("ui")
        self.localization.set_language(ui_settings.get("language", "auto"))

        self._taskbar = TaskbarProgressManager(self)
        self._setup_app_icon()

        self.setMinimumSize(
            SIZES["content_min_width"] + SIZES["content_margin"] * 2, 600
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMaximizeButtonHint
        )

        self.main_widget = QWidget()
        self.title_bar = TitleBar(self)
        self.player = PlayerWidget()
        self.timeline = TimelineWidget()
        self.file_list = FileListWidget()
        self.settings_widget = SettingsWidget(self)
        self.settings_widget.hide()

        self.load_button = QPushButton(get_text("ui.buttons.load"))
        self.analyze_button = QPushButton(get_text("ui.buttons.analyze"))
        self.settings_button = QPushButton(get_text("ui.buttons.settings"))
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setCheckable(True)

        self._worker: Optional[AnalysisWorker] = None
        self._analysis_queue: list[str] = []
        self._ai_warning_shown_this_session = False

        self.setup_ui()
        self._connect_signals()
        self.update_styles()

        self.main_widget.setMouseTracking(True)
        QApplication.instance().installEventFilter(self)

        logger.info("Главное окно инициализировано")

    def _is_window_maximized(self) -> bool:
        return (
            bool(self.windowState() & Qt.WindowState.WindowMaximized)
            or self.isFullScreen()
        )

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            self.title_bar.update_state()
        super().changeEvent(event)

    def toggleMaximized(self) -> None:
        self.activateWindow()
        self.showNormal() if self._is_window_maximized() else self.showMaximized()

    def _connect_signals(self) -> None:
        self.timeline.time_clicked.connect(self.on_time_clicked)
        self.player.draggingStarted.connect(self.timeline.on_player_dragging_started)
        self.player.draggingStopped.connect(self.timeline.on_player_dragging_stopped)
        self.load_button.clicked.connect(self.load_audio)
        self.analyze_button.clicked.connect(self.analyze_audio)
        self.settings_button.clicked.connect(self.toggle_settings)
        self.settings_widget.settingsClosed.connect(self.on_settings_closed)
        self.settings_widget.settingsChanged.connect(self.on_settings_changed)
        self.file_list.file_selected.connect(self.load_selected_file)

    def _get_edge_grip(self) -> int:
        dpr = self.screen().devicePixelRatio() if self.screen() else 1.0
        return max(5, int(self.BASE_EDGE_GRIP * dpr))

    def _setup_app_icon(self) -> None:
        icon_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "resources", "icons", "icon.svg"
            )
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._taskbar.init_if_needed()
        if handle := self.windowHandle():
            handle.screenChanged.connect(lambda s: self.update_styles() if s else None)
        self.title_bar.update_state()

    def eventFilter(self, obj: object, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseMove and not self._is_window_maximized():
            if isinstance(event, QMouseEvent):
                pos = self.mapFromGlobal(event.globalPosition().toPoint())
                self._update_cursor(pos) if self.rect().contains(
                    pos
                ) else self.unsetCursor()

        elif self.settings_widget.isVisible():
            if event.type() == QEvent.Type.WindowDeactivate:
                self.settings_widget.instant_hide_settings()
            elif event.type() == QEvent.Type.MouseButtonPress and isinstance(
                obj, QWidget
            ):
                if obj not in (
                    self.settings_widget,
                    self.settings_button,
                ) and not self.settings_widget.isAncestorOf(obj):
                    self.settings_widget.instant_hide_settings()

        return super().eventFilter(obj, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapFromGlobal(event.globalPosition().toPoint())

            if not self._is_window_maximized() and (edge := self._get_edge_at(pos)):
                edge_map = {
                    "left": Qt.Edge.LeftEdge,
                    "right": Qt.Edge.RightEdge,
                    "bottom": Qt.Edge.BottomEdge,
                    "bottom-left": Qt.Edge.BottomEdge | Qt.Edge.LeftEdge,
                    "bottom-right": Qt.Edge.BottomEdge | Qt.Edge.RightEdge,
                }
                if self.windowHandle() and self.windowHandle().startSystemResize(
                    edge_map[edge]
                ):
                    return event.accept()

            if self.title_bar.geometry().contains(pos):
                is_on_btn = any(
                    btn.geometry().contains(self.title_bar.mapFrom(self, pos))
                    for btn in self.title_bar.buttons.values()
                )
                if (
                    pos.x()
                    <= self.title_bar.geometry().right()
                    - self.TITLE_BAR_RESIZE_THRESHOLD
                    and not is_on_btn
                ):
                    if self.windowHandle() and self.windowHandle().startSystemMove():
                        return event.accept()

        super().mousePressEvent(event)

    def _update_cursor(self, pos: QPoint) -> None:
        cursors = {
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "bottom-left": Qt.CursorShape.SizeBDiagCursor,
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,
        }
        self.setCursor(cursors.get(self._get_edge_at(pos), Qt.CursorShape.ArrowCursor))

    def _get_edge_at(self, pos: QPoint) -> Optional[str]:
        grip = self._get_edge_grip()
        r = self.rect()
        b = (r.bottom() - grip) <= pos.y() <= r.bottom()
        l = r.left() <= pos.x() <= (r.left() + grip)
        ri = (r.right() - grip) <= pos.x() <= r.right()
        if b and l:
            return "bottom-left"
        if b and ri:
            return "bottom-right"
        if b:
            return "bottom"
        if l:
            return "left"
        if ri:
            return "right"
        return None

    def _on_worker_progress(
        self, file_path: str, percent: int, remaining: float
    ) -> None:
        self.timeline.update_file_progress(file_path, percent, remaining)
        self._taskbar.update_file(file_path, percent)

    def _on_worker_file_finished(self, file_path: str, result: object) -> None:
        self.timeline.update_file_result(file_path, result)
        self._taskbar.update_file(file_path, 100)
        self._show_ai_warning_if_needed()

    def _show_ai_warning_if_needed(self) -> None:
        if (
            not self._ai_warning_shown_this_session
            and self.settings_service.get_setting("ui.show_ai_warning", True)
        ):
            AIWarningDialog(self, self.settings_service).exec()
            self._ai_warning_shown_this_session = True

    def _on_worker_error(self, file_path: str, error_msg: str) -> None:
        self._taskbar.stop()
        full_msg = f"{get_text('ui.messages.file')}: {file_path}\n{error_msg}"
        ThemedMessageBox.warning(self, get_text("ui.messages.analysis_error"), full_msg)

    def _on_worker_all_finished(self) -> None:
        if self._analysis_queue:
            next_batch = self._analysis_queue
            self._analysis_queue = []
            self._taskbar.start(len(next_batch))
            self._start_worker(next_batch)
        else:
            self._taskbar.finish()
            self._worker = None

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.title_bar)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setMinimumWidth(SIZES["content_min_width"])
        content.setMaximumWidth(SIZES["content_width"])

        content_layout = QVBoxLayout(content)
        m = SIZES["content_margin"]
        content_layout.setContentsMargins(m, m, m, m)

        settings_row = QHBoxLayout()
        settings_row.addWidget(self.settings_button)
        settings_row.addStretch()

        main_buttons = QHBoxLayout()
        main_buttons.addWidget(self.load_button)
        main_buttons.addWidget(self.analyze_button)
        main_buttons.addStretch()

        content_layout.addLayout(settings_row)
        content_layout.addLayout(main_buttons)
        content_layout.addWidget(self.player)
        content_layout.addWidget(self.file_list)
        content_layout.addWidget(self.timeline)

        layout.addStretch()
        layout.addWidget(content)
        layout.addStretch()

        main_layout.addWidget(container)
        self.setCentralWidget(self.main_widget)

    def is_analyzing(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def load_audio(self) -> None:
        try:
            supported = self.controller.get_supported_formats()
            filters = f"Audio Files ({' '.join(f'*{ext}' for ext in supported)})"
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, get_text("ui.dialogs.select_audio"), "", filters
            )

            if not file_paths:
                return

            for path in file_paths:
                self.controller.load_audio_file(path)
                self.file_list.add_file(path)

            if not self.player.current_file:
                self.player.load_audio(file_paths[0])

            if self.settings_service.get_setting("analysis.auto_analyze", False):
                self.analyze_audio()

        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
            ThemedMessageBox.critical(self, get_text("ui.messages.error"), str(e))

    def analyze_audio(self) -> None:
        if not self.file_list.files:
            return ThemedMessageBox.information(
                self,
                get_text("ui.messages.info"),
                get_text("ui.messages.load_files_first"),
            )

        analyzed = set(self.timeline.file_blocks.keys())
        queued = set(self._analysis_queue)
        processing = set(self._worker.files) if self._worker else set()

        to_analyze = [
            f
            for f in self.file_list.files
            if f not in analyzed and f not in queued and f not in processing
        ]

        if not to_analyze:
            return ThemedMessageBox.information(
                self,
                get_text("ui.messages.info"),
                get_text("ui.messages.all_files_analyzed"),
            )

        self.timeline.start_analysis(to_analyze)

        if self.is_analyzing():
            self._analysis_queue.extend(to_analyze)
        else:
            self._taskbar.start(len(to_analyze))
            self._start_worker(to_analyze)

    def _start_worker(self, files: list[str]) -> None:
        self._worker = AnalysisWorker(self.controller, files)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.file_finished.connect(self._on_worker_file_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.all_finished.connect(self._on_worker_all_finished)
        self._worker.start()

    def load_selected_file(self, file_path: str) -> None:
        try:
            self.controller.load_audio_file(file_path)
            self.player.load_audio(file_path)
            self.timeline.clear_markers()
            self.player.play_pause()
        except TrustSpectraError as e:
            ThemedMessageBox.warning(self, get_text("ui.messages.error"), str(e))

    def on_time_clicked(self, file_path: str, time_seconds: float) -> None:
        try:
            self.player.load_audio(file_path)
            self.player.seek(int(time_seconds * 1000))
            self.player.play()
        except Exception as e:
            logger.error(f"Ошибка перехода: {e}")

    def toggle_settings(self) -> None:
        if getattr(self.settings_widget, "_is_animating", False):
            return

        if self.settings_widget.isVisible() and self.settings_widget.width() > 0:
            self.settings_widget.hide_settings()
        else:
            global_pos = self.settings_button.mapToGlobal(
                self.settings_button.rect().bottomLeft()
            )
            local_pos = (self.settings_widget.parent() or self).mapFromGlobal(
                global_pos
            )
            w = min(400, self.width() // 3)
            self.settings_widget.adjustSize()
            h = self.settings_widget.sizeHint().height()
            self.settings_widget.setGeometry(
                local_pos.x(), max(0, min(local_pos.y(), self.height() - h)), w, h
            )
            self.settings_widget.show_settings(self.width())
            self.settings_widget.raise_()
            self.settings_button.raise_()

        self.settings_button.setChecked(
            self.settings_widget.isVisible() and self.settings_widget.width() > 0
        )

    def on_settings_closed(self) -> None:
        self.settings_button.setChecked(False)

    def _detect_real_os_theme(self) -> str:
        # Читает тему ОС напрямую из реестра Windows
        system = platform.system()
        if system == "Windows":
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                )
                try:
                    system_value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
                except Exception:
                    system_value = None
                try:
                    apps_value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                except Exception:
                    apps_value = None
                winreg.CloseKey(key)
                if system_value is not None:
                    return "dark" if system_value == 0 else "light"
                elif apps_value is not None:
                    return "dark" if apps_value == 0 else "light"
            except Exception:
                pass
        app = QGuiApplication.instance()
        if app:
            if hasattr(app.styleHints(), "colorScheme"):
                return (
                    "dark"
                    if app.styleHints().colorScheme() == Qt.ColorScheme.Dark
                    else "light"
                )
            c = app.palette().window().color()
            is_dark = (c.red() * 0.299 + c.green() * 0.587 + c.blue() * 0.114) < 128
            return "dark" if is_dark else "light"
        return "dark"

    def _resolve_actual_theme(self, theme_name: str) -> str:
        if theme_name != "system":
            return theme_name
        return self._real_os_theme

    def is_system_theme_dark(self) -> bool:
        return self._real_os_theme == "dark"

    def on_settings_changed(self, settings: dict) -> None:
        self.settings_service.set_all_settings(settings)

        ui_settings = settings.get("ui", {})
        theme = ui_settings.get("theme")

        if theme:
            actual_theme = self._resolve_actual_theme(theme)
            update_theme_colors(actual_theme)
            save_theme(theme)
            refresh_all_styles()
            self.update_styles()

        if lang := ui_settings.get("language"):
            self.localization.set_language(lang)
            self.load_button.setText(get_text("ui.buttons.load"))
            self.analyze_button.setText(get_text("ui.buttons.analyze"))
            for w in (self.timeline, self.settings_widget):
                if hasattr(w, "update_texts"):
                    w.update_texts()

        if hasattr(self.controller, "apply_settings"):
            self.controller.apply_settings(settings)

    def update_styles(self) -> None:
        self.main_widget.setStyleSheet(sf().build("main_widget"))
        self.load_button.setStyleSheet(sf().build("button"))
        self.analyze_button.setStyleSheet(sf().build("analyze_button"))
        self.settings_button.setStyleSheet(sf().build("settings_button"))
        for w in (
            self.title_bar,
            self.player,
            self.timeline,
            self.file_list,
            self.settings_widget,
        ):
            if hasattr(w, "update_styles"):
                w.update_styles()

    def closeEvent(self, event) -> None:
        if self.is_analyzing() or self._analysis_queue:
            res = ThemedMessageBox.confirm(
                self,
                title=get_text("ui.messages.analysis_in_progress_title"),
                message=get_text("ui.messages.analysis_in_progress_message"),
                icon_type="warning",
                cancel_text=get_text("ui.buttons.cancel"),
                confirm_text=get_text("ui.buttons.close_anyway"),
            )
            if res == QDialog.DialogCode.Rejected:
                return event.ignore()
            if self._worker:
                self._worker.stop()
            self._analysis_queue.clear()

        self._taskbar.finish()
        super().closeEvent(event)
