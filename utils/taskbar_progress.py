import sys
import ctypes
from threading import Lock
from enum import IntEnum
from typing import Optional

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt

from utils.logger import logger

# --- Windows COM/ctypes для ITaskbarList3 ---
if sys.platform == "win32":
    # БЕЗОПАСНЫЙ ИМПОРТ: импортируем wintypes только если мы на Windows
    from ctypes import wintypes

    # GUID структура
    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", wintypes.BYTE * 8),
        ]

        def __init__(self, uuid_string: str):
            s = uuid_string.strip("{}").replace("-", "")
            self.Data1 = int(s[0:8], 16)
            self.Data2 = int(s[8:12], 16)
            self.Data3 = int(s[12:16], 16)
            for i in range(8):
                self.Data4[i] = int(s[16 + i * 2:18 + i * 2], 16)

    CLSID_TaskbarList = GUID("{56FDF344-FD6D-11d0-958A-006097C9A090}")
    IID_ITaskbarList3 = GUID("{ea1afb91-9e28-4b86-90e9-9e9f8a5eefaf}")

    # HRESULT
    S_OK = 0
    RPC_E_CHANGED_MODE = -2147417850  # 0x80010106

    # Инициализация ole32
    ole32 = ctypes.windll.ole32
    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole32.CoInitializeEx.restype = ctypes.HRESULT
    ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(GUID), ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)
    ]
    ole32.CoCreateInstance.restype = ctypes.HRESULT

    # Инициализация user32 для очистки GDI объектов (важно для иконок)
    user32 = ctypes.windll.user32
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    user32.DestroyIcon.restype = wintypes.BOOL

    COINIT_APARTMENTTHREADED = 0x2
    CLSCTX_INPROC_SERVER = 0x1

    # IUnknown vtable
    class IUnknownVtbl(ctypes.Structure):
        pass

    class IUnknown(ctypes.Structure):
        _fields_ = [("lpVtbl", ctypes.POINTER(IUnknownVtbl))]

    # ITaskbarList3 vtable
    class ITaskbarList3Vtbl(ctypes.Structure):
        pass

    class ITaskbarList3(ctypes.Structure):
        _fields_ = [("lpVtbl", ctypes.POINTER(ITaskbarList3Vtbl))]

    # Определяем функции vtable
    IUnknownVtbl._fields_ = [
        ("QueryInterface", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(IUnknown), ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))),
        ("AddRef", ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.POINTER(IUnknown))),
        ("Release", ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.POINTER(IUnknown))),
    ]

    ITaskbarList3Vtbl._fields_ = [
        # IUnknown
        ("QueryInterface", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))),
        ("AddRef", ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.POINTER(ITaskbarList3))),
        ("Release", ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.POINTER(ITaskbarList3))),
        # ITaskbarList
        ("HrInit", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3))),
        ("AddTab", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND)),
        ("DeleteTab", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND)),
        ("ActivateTab", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND)),
        ("SetActiveAlt", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND)),
        # ITaskbarList2
        ("MarkFullscreenWindow", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, wintypes.BOOL)),
        # ITaskbarList3
        ("SetProgressValue", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, ctypes.c_ulonglong, ctypes.c_ulonglong)),
        ("SetProgressState", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, ctypes.c_int)),
        ("RegisterTab", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, wintypes.HWND)),
        ("UnregisterTab", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND)),
        ("SetTabOrder", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, wintypes.HWND)),
        ("SetTabActive", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, wintypes.HWND, wintypes.DWORD)),
        ("ThumbBarAddButtons", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, ctypes.c_uint, ctypes.c_void_p)),
        ("ThumbBarUpdateButtons", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, ctypes.c_uint, ctypes.c_void_p)),
        ("ThumbBarSetImageList", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, ctypes.c_void_p)),
        ("SetOverlayIcon", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, wintypes.HICON, wintypes.LPCWSTR)),
        ("SetThumbnailTooltip", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, wintypes.LPCWSTR)),
        ("SetThumbnailClip", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.POINTER(ITaskbarList3), wintypes.HWND, ctypes.c_void_p)),
    ]


class TaskbarState(IntEnum):
    NOPROGRESS = 0x00000000
    INDETERMINATE = 0x00000001
    NORMAL = 0x00000002
    ERROR = 0x00000004
    PAUSED = 0x00000008


class TaskbarProgressManager(QObject):
    """
    Менеджер прогресса в панели задач Windows через ITaskbarList3.
    Оптимизирован для многопоточности и минимального потребления ресурсов.
    """
    
    # Сигналы для безопасного вызова из фоновых потоков
    sig_set_overlay = pyqtSignal(QIcon, str)
    sig_clear_overlay = pyqtSignal()

    def __init__(self, parent_window: QWidget) -> None:
        super().__init__()
        self._parent = parent_window
        self._hwnd: Optional[int] = None
        self._taskbar = None
        
        # Кэшированные методы vtable для ускорения вызовов
        self._com_SetProgressValue = None
        self._com_SetProgressState = None
        self._com_SetOverlayIcon = None
        self._com_Release = None
        
        self._initialized = False
        self._total_files = 0
        self._files_progress: dict[str, int] = {}
        self._total_progress_sum = 0
        
        # Оптимизация COM-вызовов (предотвращает спам одинаковыми значениями)
        self._last_overall_percent = -1
        
        # Блокировка для обеспечения потокобезопасности
        self._lock = Lock()

        # Привязываем сигналы к слотам с QueuedConnection (гарантирует выполнение в GUI потоке)
        self.sig_set_overlay.connect(self._slot_set_overlay, Qt.ConnectionType.QueuedConnection)
        self.sig_clear_overlay.connect(self._slot_clear_overlay, Qt.ConnectionType.QueuedConnection)

    def __del__(self):
        """Гарантированное освобождение COM-объекта."""
        try:
            self._release_com()
        except Exception:
            pass

    def _release_com(self):
        """Освобождает интерфейс ITaskbarList3."""
        if self._taskbar is not None and self._com_Release is not None:
            self._com_Release(self._taskbar)
            self._taskbar = None
            logger.debug("ITaskbarList3 освобожден.")

    # Инициализация

    def init_if_needed(self) -> bool:
        """Инициализирует COM и получает ITaskbarList3."""
        if self._initialized:
            return self._taskbar is not None

        self._initialized = True

        if sys.platform != "win32":
            return False

        try:
            # Получаем native HWND
            self._hwnd = int(self._parent.winId())
            if self._hwnd == 0:
                logger.warning("winId() вернул 0 — taskbar progress недоступен")
                return False

            # Инициализируем COM
            hr = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
            if hr < 0 and hr != RPC_E_CHANGED_MODE:
                logger.warning(f"CoInitializeEx failed: {hr:#x}")
                return False

            # Создаём ITaskbarList3
            ptr = ctypes.c_void_p()
            hr = ole32.CoCreateInstance(
                ctypes.byref(CLSID_TaskbarList),
                None,
                CLSCTX_INPROC_SERVER,
                ctypes.byref(IID_ITaskbarList3),
                ctypes.byref(ptr)
            )
            if hr < 0:
                logger.warning(f"CoCreateInstance ITaskbarList3 failed: {hr:#x}")
                return False

            self._taskbar = ctypes.cast(ptr, ctypes.POINTER(ITaskbarList3))
            vtbl = self._taskbar.contents.lpVtbl.contents

            # HrInit
            hr = vtbl.HrInit(self._taskbar)
            if hr < 0:
                logger.warning(f"ITaskbarList3::HrInit failed: {hr:#x}")
                self._release_com()
                return False

            # КЭШИРОВАНИЕ: Сохраняем ссылки на функции vtable
            self._com_SetProgressValue = vtbl.SetProgressValue
            self._com_SetProgressState = vtbl.SetProgressState
            self._com_SetOverlayIcon = vtbl.SetOverlayIcon
            self._com_Release = vtbl.Release

            logger.debug(f"TaskbarProgressManager инициализирован (HWND={self._hwnd})")
            return True

        except Exception as e:
            logger.warning(f"Не удалось инициализировать TaskbarProgress: {e}")
            self._release_com()
            return False

    # Публичный API

    def start(self, total_files: int) -> None:
        """Начинает отслеживание прогресса для N файлов."""
        if not self.init_if_needed():
            return

        with self._lock:
            self._total_files = max(total_files, 1)
            self._files_progress.clear()
            self._total_progress_sum = 0
            self._last_overall_percent = -1
            
        self._set_state(TaskbarState.NORMAL)
        self._set_value(0)
        logger.debug(f"Taskbar progress started: {total_files} files")

    def update_file(self, file_path: str, percent: int) -> None:
        """Потокобезопасное обновление прогресса конкретного файла."""
        if self._taskbar is None or self._hwnd is None:
            return

        # ЗАЩИТА: если start() не был вызван или finish() уже вызван
        if self._total_files == 0:
            logger.debug(f"update_file вызван без start(), игнорируем: {file_path}")
            return

        percent = max(0, min(100, percent))
        
        with self._lock:
            old_percent = self._files_progress.get(file_path, 0)
            
            # Пропускаем, если процент конкретного файла не изменился
            if old_percent == percent:
                return

            self._total_progress_sum += (percent - old_percent)
            
            # ОПТИМИЗАЦИЯ ПАМЯТИ: Удаляем файл, если он завершен на 100%
            if percent == 100:
                self._files_progress.pop(file_path, None)
            else:
                self._files_progress[file_path] = percent
            
            # ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА: проверяем _total_files ещё раз под блокировкой
            if self._total_files == 0:
                return
                
            overall = int(self._total_progress_sum / self._total_files)
            
            # ОПТИМИЗАЦИЯ COM: Вызываем Windows API, только если ИЗМЕНИЛСЯ ОБЩИЙ процент
            if overall == self._last_overall_percent:
                return
                
            self._last_overall_percent = overall

        # Вызов COM вне блока блокировки, чтобы не тормозить другие потоки
        self._set_value(overall)

    def pause(self) -> None:
        """Ставит прогресс на паузу (жёлтый цвет)."""
        if self._taskbar is not None:
            self._set_state(TaskbarState.PAUSED)

    def resume(self) -> None:
        """Возобновляет прогресс (зелёный цвет)."""
        if self._taskbar is not None:
            self._set_state(TaskbarState.NORMAL)

    def stop(self) -> None:
        """Останавливает прогресс (красный цвет)."""
        if self._taskbar is not None:
            self._set_state(TaskbarState.ERROR)

    def finish(self) -> None:
        """Завершает и скрывает индикатор."""
        if self._taskbar is not None:
            self._set_state(TaskbarState.NOPROGRESS)
            
        with self._lock:
            self._files_progress.clear()
            self._total_progress_sum = 0
            self._total_files = 0
            self._last_overall_percent = -1
            
        logger.debug("Taskbar progress finished")

    def set_overlay_icon(self, icon: QIcon, description: str = "") -> None:
        """Устанавливает overlay-иконку на кнопку панели задач."""
        if self._taskbar is None:
            return
        self.sig_set_overlay.emit(icon, description)

    def clear_overlay_icon(self) -> None:
        """Убирает overlay-иконку."""
        if self._taskbar is None:
            return
        self.sig_clear_overlay.emit()

    # Приватные методы и Слоты

    def _set_value(self, value: int) -> None:
        if self._com_SetProgressValue:
            self._com_SetProgressValue(self._taskbar, self._hwnd, value, 100)

    def _set_state(self, state: TaskbarState) -> None:
        if self._com_SetProgressState:
            self._com_SetProgressState(self._taskbar, self._hwnd, int(state))

    @pyqtSlot(QIcon, str)
    def _slot_set_overlay(self, icon: QIcon, description: str) -> None:
        if not self._com_SetOverlayIcon:
            return
            
        try:
            pixmap = icon.pixmap(16, 16)
            if pixmap.isNull():
                self._slot_clear_overlay()
                return

            # toHICON() возвращает указатель, приводим к int
            hicon = int(pixmap.toImage().toHICON())
            if hicon == 0:
                return

            desc = description if description else None
            self._com_SetOverlayIcon(self._taskbar, self._hwnd, hicon, desc)
            
            # Устранение утечки памяти GDI: оригинал нужно уничтожить
            if sys.platform == "win32":
                user32.DestroyIcon(hicon)
                
        except Exception as e:
            logger.warning(f"Не удалось установить overlay icon: {e}")

    @pyqtSlot()
    def _slot_clear_overlay(self) -> None:
        if self._com_SetOverlayIcon:
            self._com_SetOverlayIcon(self._taskbar, self._hwnd, 0, None)