import logging

from PyQt6.QtNetwork import QLocalServer, QLocalSocket

logger = logging.getLogger("TrustSpectra")

_SINGLE_INSTANCE_SERVER = None  # удерживаем ссылку, иначе GC уничтожит сервер


def ensure_single_instance(app_id: str = "TrustSpectra_SingleInstance") -> bool:
    """
    Возвращает True, если это единственный запущенный экземпляр.
    Требует созданного QApplication (QLocalSocket использует Qt event loop).
    """
    global _SINGLE_INSTANCE_SERVER

    socket = QLocalSocket()
    socket.connectToServer(app_id)
    if socket.waitForConnected(500):
        logger.warning("Обнаружен уже запущенный экземпляр приложения")
        return False

    _SINGLE_INSTANCE_SERVER = QLocalServer()
    if not _SINGLE_INSTANCE_SERVER.listen(app_id):
        logger.error(
            "Не удалось создать single-instance сервер: %s",
            _SINGLE_INSTANCE_SERVER.errorString(),
        )
        return False
    return True
