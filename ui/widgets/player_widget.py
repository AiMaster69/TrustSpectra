import logging
import os
import sys
import threading
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStyle,
    QStyleOptionSlider,
    QVBoxLayout,
    QWidget,
)

from ui.styles.style_factory import sf

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    import soundfile as sf_audio

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sd = None  # type: ignore
    sf_audio = None  # type: ignore
    logger.warning("sounddevice / soundfile не найдены. Работа в демо-режиме.")


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def _load_material_icons() -> dict[str, str]:
    icons_unicode = {
        "play": "\ue037",
        "pause": "\ue034",
        "volume_high": "\ue050",
        "volume_low": "\ue04d",
        "volume_mute": "\ue04e",
        "volume_off": "\ue04f",
    }
    icons_fallback = {
        "play": "▶",
        "pause": "⏸",
        "volume_high": "🔊",
        "volume_low": "🔉",
        "volume_mute": "🔇",
        "volume_off": "🔈",
    }

    try:
        font_path = resource_path("resources/fonts/MaterialIcons-Regular.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                return icons_unicode
    except Exception as exc:
        logger.warning("Не удалось загрузить шрифт Material Icons: %s", exc)

    return icons_fallback


class TimeSlider(QSlider):
    clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setFixedHeight(16)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setTracking(True)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        style = self.style()

        handle = style.subControlRect(
            QStyle.ComplexControl.CC_Slider,
            opt,
            QStyle.SubControl.SC_SliderHandle,
            self,
        )
        if handle.contains(event.pos()):
            super().mousePressEvent(event)
            return

        groove = style.subControlRect(
            QStyle.ComplexControl.CC_Slider,
            opt,
            QStyle.SubControl.SC_SliderGroove,
            self,
        )
        if not groove.contains(event.pos()):
            return

        available = groove.width() - handle.width()
        if available <= 0:
            return

        x = event.pos().x() - groove.x() - handle.width() // 2
        x = max(0, min(x, available))
        ratio = x / available
        value = int(self.minimum() + (self.maximum() - self.minimum()) * ratio)

        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
        self.clicked.emit(value)

    def wheelEvent(self, event):
        event.ignore()


class AudioEngine(QThread):
    position_changed = pyqtSignal(int, int)
    duration_changed = pyqtSignal(int)
    state_changed = pyqtSignal(bool)
    finished_ = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._file_path: Optional[str] = None
        self._audio_file: Optional[sf_audio.SoundFile] = None
        self._samplerate = 44100
        self._channels = 2
        self._total_frames = 0
        self._duration_ms = 0

        self._lock = threading.Lock()
        self._current_frame = 0
        self._seek_frame = -1
        self._volume = 0.5
        self._generation = 0

        self._stop_event = threading.Event()
        self._play_event = threading.Event()

        self._blocksize = 2048
        self._last_emitted_ms = -1

    def is_loaded(self) -> bool:
        return self._audio_file is not None

    def load(self, file_path: str) -> bool:
        if self.isRunning():
            self.stop()
            if not self.wait(500):
                logger.error("Аудио-поток не остановился вовремя при загрузке")
                self.error_occurred.emit("Таймаут остановки аудиопотока")
                return False

        if self._audio_file:
            self._audio_file.close()
            self._audio_file = None

        try:
            self._audio_file = sf_audio.SoundFile(file_path, "r")
            self._file_path = file_path
            self._samplerate = self._audio_file.samplerate
            self._channels = self._audio_file.channels

            self._total_frames = len(self._audio_file)
            if self._total_frames <= 0:
                self._audio_file.seek(0, sf_audio.SEEK_END)
                self._total_frames = self._audio_file.tell()
                self._audio_file.seek(0, sf_audio.SEEK_SET)

            self._duration_ms = int(self._total_frames / self._samplerate * 1000)

            with self._lock:
                self._current_frame = 0
                self._seek_frame = -1
                self._last_emitted_ms = -1
                # ВАЖНО: НЕ сбрасываем _generation здесь,
                # он синхронизируется извне через set_generation()
                self._stop_event.clear()
                self._play_event.clear()

            self.duration_changed.emit(self._duration_ms)
            logger.info(
                "Аудио загружено: %s, duration=%d мс", file_path, self._duration_ms
            )

            self.start()
            return True

        except Exception as exc:
            self.error_occurred.emit(f"Ошибка загрузки: {exc}")
            return False

    def play(self) -> None:
        if not self._audio_file:
            return
        self._play_event.set()
        self.state_changed.emit(True)

    def pause(self) -> None:
        self._play_event.clear()
        self.state_changed.emit(False)

    def stop(self) -> None:
        self._stop_event.set()
        self._play_event.set()
        self.state_changed.emit(False)

    def reset(self, generation: int = 0) -> None:
        if not self._audio_file:
            return
        with self._lock:
            self._generation = generation
            self._audio_file.seek(0)
            self._current_frame = 0
            self._seek_frame = -1
            self._last_emitted_ms = -1
        self._play_event.clear()
        self.state_changed.emit(False)
        self._maybe_emit_position(0, generation)

    def seek(self, ms: int, generation: int = 0) -> None:
        if not self._audio_file or self._samplerate <= 0:
            return
        frame = int(ms / 1000 * self._samplerate)
        with self._lock:
            self._generation = generation
            self._seek_frame = min(max(0, frame), max(0, self._total_frames - 1))
            self._last_emitted_ms = -1

            if not self._play_event.is_set():
                self._audio_file.seek(self._seek_frame)
                self._current_frame = self._seek_frame
                self._seek_frame = -1

    def set_generation(self, generation: int) -> None:
        """Явная синхронизация generation с PlayerWidget."""
        with self._lock:
            self._generation = generation

    def set_volume(self, volume: float) -> None:
        with self._lock:
            self._volume = max(0.0, min(1.0, volume))

    def _maybe_emit_position(self, current_frame: int, generation: int) -> None:
        if self._samplerate <= 0:
            return
        ms = int(current_frame / self._samplerate * 1000)
        if ms != self._last_emitted_ms:
            self._last_emitted_ms = ms
            self.position_changed.emit(ms, generation)

    def run(self) -> None:
        if not self._audio_file:
            return

        try:
            with sd.OutputStream(
                samplerate=self._samplerate,
                channels=self._channels,
                dtype="float32",
                blocksize=self._blocksize,
            ) as stream:
                while not self._stop_event.is_set():
                    self._play_event.wait()
                    if self._stop_event.is_set():
                        break

                    with self._lock:
                        seek_to = self._seek_frame
                        self._seek_frame = -1
                        gen = self._generation

                    if seek_to >= 0:
                        with self._lock:
                            self._audio_file.seek(seek_to)
                            self._current_frame = seek_to

                    with self._lock:
                        data = self._audio_file.read(self._blocksize, dtype="float32")
                        frames = data.shape[0]

                        if frames == 0:
                            self._audio_file.seek(0)
                            self._current_frame = 0
                            self._last_emitted_ms = -1

                    if frames == 0:
                        self._play_event.clear()
                        self.finished_.emit()
                        continue

                    with self._lock:
                        vol = self._volume

                    if vol < 1.0:
                        data *= vol

                    with self._lock:
                        self._current_frame += frames
                        snapshot = self._current_frame

                    stream.write(data)
                    self._maybe_emit_position(snapshot, gen)

        except Exception as exc:
            self.error_occurred.emit(f"Ошибка воспроизведения: {exc}")

    def close(self) -> None:
        self.stop()
        self.wait(1000)
        if self._audio_file:
            self._audio_file.close()
            self._audio_file = None


class PlayerWidget(QWidget):
    draggingStarted = pyqtSignal()
    draggingStopped = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._icons = _load_material_icons()

        self.current_file: Optional[str] = None
        self.is_playing = False
        self.current_position = 0
        self.duration = 0
        self.volume = 0.5
        self._is_dragging = False
        self._was_playing = False
        self._seek_generation = 0

        self._audio_engine: Optional[AudioEngine] = None
        if AUDIO_AVAILABLE:
            self._audio_engine = AudioEngine(self)
            self._audio_engine.position_changed.connect(self._update_position)
            self._audio_engine.duration_changed.connect(self._on_duration_changed)
            self._audio_engine.state_changed.connect(self._on_audio_state_changed)
            self._audio_engine.finished_.connect(self._on_audio_finished)
            self._audio_engine.error_occurred.connect(self._on_audio_error)

        self._demo_timer = QTimer(self)
        self._demo_timer.setInterval(100)
        self._demo_timer.timeout.connect(self._on_demo_tick)

        self._setup_ui()
        self._connect_signals()
        self.update_styles()
        self._reset_ui()

    def _setup_ui(self) -> None:
        self.time_slider = TimeSlider()
        self.time_slider.setObjectName("time_slider")

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMinimumWidth(100)
        self.volume_slider.setFixedHeight(16)
        self.volume_slider.setObjectName("volume_slider")

        self.current_time = QLabel("0:00")
        self.current_time.setObjectName("time_label")

        self.total_time = QLabel("0:00")
        self.total_time.setObjectName("time_label")

        self.play_button = QPushButton(self._icons["play"])
        self.play_button.setFixedSize(
            sf().size("button_height", 36), sf().size("button_height", 36)
        )
        self.play_button.setObjectName("play_button")

        controls = QHBoxLayout()
        controls.setSpacing(sf().size("spacing", 8))
        controls.addWidget(self.play_button)
        controls.addWidget(self.current_time)
        controls.addWidget(self.time_slider, 4)
        controls.addWidget(self.total_time)
        controls.addWidget(self.volume_slider, 1)

        layout = QVBoxLayout(self)
        layout.setSpacing(sf().size("spacing", 8))
        layout.addLayout(controls)
        layout.setContentsMargins(8, 8, 8, 8)

    def _connect_signals(self) -> None:
        self.play_button.clicked.connect(self.play_pause)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

        self.time_slider.clicked.connect(self._on_slider_clicked)
        self.time_slider.sliderPressed.connect(self._on_slider_pressed)
        self.time_slider.sliderReleased.connect(self._on_slider_released)
        self.time_slider.sliderMoved.connect(self._on_slider_moved)

    def _on_slider_clicked(self, value: int) -> None:
        self._update_time(value)
        self.seek(value)

    def _on_slider_pressed(self) -> None:
        self._is_dragging = True
        self._was_playing = self.is_playing
        if self._was_playing:
            self.pause()
        self.draggingStarted.emit()

    def _on_slider_released(self) -> None:
        if not self._is_dragging:
            return
        self._is_dragging = False
        self.draggingStopped.emit()
        self.seek(self.time_slider.value())
        if self._was_playing:
            self.play()

    def _on_slider_moved(self, position: int) -> None:
        if self._is_dragging:
            self._update_time(position)

    def play_pause(self) -> None:
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self) -> None:
        if self.is_playing or not self.current_file:
            return

        if self._audio_engine:
            self._audio_engine.play()
        else:
            self._demo_timer.start()

    def pause(self) -> None:
        if not self.is_playing:
            return

        if self._audio_engine:
            self._audio_engine.pause()
        else:
            self._demo_timer.stop()

    def stop(self) -> None:
        self.current_position = 0
        self._seek_generation += 1
        self._update_position(0, self._seek_generation)

        if self._audio_engine:
            self._audio_engine.reset(self._seek_generation)
        else:
            self._demo_timer.stop()

        self._on_audio_state_changed(False)

    def seek(self, position: int) -> None:
        ms = max(0, min(int(position), self.duration))
        if ms == self.current_position:
            return

        self._seek_generation += 1
        self.current_position = ms
        self._update_time(ms)

        if self.time_slider.value() != ms:
            self.time_slider.blockSignals(True)
            self.time_slider.setValue(ms)
            self.time_slider.blockSignals(False)

        if self._audio_engine and self._audio_engine.is_loaded():
            self._audio_engine.seek(ms, self._seek_generation)

    def load_audio(self, file_path: str, autoplay: bool = False) -> None:
        self.stop()
        self.current_file = file_path

        if self._audio_engine:
            success = self._audio_engine.load(file_path)
            if success:
                # СИНХРОНИЗИРУЕМ generation после загрузки
                self._audio_engine.set_generation(self._seek_generation)
                self.play_button.setEnabled(True)
                if autoplay:
                    self.play()
            else:
                self._reset_ui()
        else:
            self.duration = 60000
            self._on_duration_changed(self.duration)
            self.current_position = 0
            self._update_position(0, self._seek_generation)
            self.play_button.setEnabled(True)
            logger.info("Демо-режим: загружен %s", os.path.basename(file_path))
            if autoplay:
                self.play()

    def load_and_seek(
        self, file_path: str, position_ms: int = 0, autoplay: bool = False
    ) -> None:
        self.current_file = file_path

        if self._audio_engine:
            success = self._audio_engine.load(file_path)
            if success:
                self.play_button.setEnabled(True)
                # seek() уже обновит generation внутри AudioEngine
                self.seek(position_ms)
                if autoplay:
                    self.play()
            else:
                self._reset_ui()
        else:
            self.duration = 60000
            self._on_duration_changed(self.duration)
            self.play_button.setEnabled(True)
            self.seek(position_ms)
            if autoplay:
                self.play()

    def _reset_ui(self) -> None:
        self.current_file = None
        self.duration = 0
        self.current_position = 0
        self._seek_generation += 1
        self.time_slider.setRange(0, 0)
        self.total_time.setText("0:00")
        self._update_time(0)

        self.is_playing = False
        self.play_button.setText(self._icons["play"])
        self.play_button.setEnabled(False)

    def _on_volume_changed(self, value: int) -> None:
        self.volume = value / 100.0
        if self._audio_engine:
            self._audio_engine.set_volume(self.volume)

    def _update_position(self, position: int, generation: int = 0) -> None:
        if self._is_dragging:
            return

        if generation != self._seek_generation:
            return

        if abs(self.time_slider.value() - position) <= 2:
            return

        self.time_slider.blockSignals(True)
        self.time_slider.setValue(position)
        self.time_slider.blockSignals(False)
        self._update_time(position)

    def _update_time(self, position: int) -> None:
        self.current_time.setText(self._format_time(position))

    def _on_duration_changed(self, duration: int) -> None:
        self.duration = duration
        self.time_slider.setRange(0, duration)
        self.total_time.setText(self._format_time(duration))

    def _on_audio_state_changed(self, is_playing: bool) -> None:
        self.is_playing = is_playing
        self.play_button.setText(
            self._icons["pause"] if is_playing else self._icons["play"]
        )

    def _on_audio_finished(self) -> None:
        self.stop()

    def _on_audio_error(self, message: str) -> None:
        logger.error("AudioEngine: %s", message)
        self._reset_ui()

    def _on_demo_tick(self) -> None:
        if not self.is_playing:
            return
        self.current_position += 100
        if self.current_position >= self.duration:
            self.stop()
        else:
            self._update_position(self.current_position, self._seek_generation)

    def update_styles(self) -> None:
        self.setStyleSheet(sf().build("player_widget"))

    def closeEvent(self, event):
        if self._audio_engine:
            self._audio_engine.close()
        super().closeEvent(event)

    @staticmethod
    def _format_time(ms: int) -> str:
        s = max(0, ms) // 1000
        return f"{s // 60}:{s % 60:02d}"
