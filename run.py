import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Мы должны загрузить ONNX Runtime до того, как numpy/librosa
try:
    import onnxruntime
except Exception as e:
    print(f"Критическая ошибка инициализации ONNX Runtime: {e}")
    import sys
    sys.exit(1)

import sys
import json
import logging

from utils.paths import get_user_data_dir

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger("TrustSpectra")


def setup_performance_settings() -> None:
    """
    Настраивает количество потоков для OMP / MKL на основе
    пользовательских настроек из settings.json.

    Эти переменные окружения также используются ONNX Runtime
    для ограничения количества потоков при инференсе.
    """
    settings_file = get_user_data_dir() / 'settings.json'

    if not settings_file.exists():
        logger.info("Файл настроек не найден — используются значения по умолчанию")
        return

    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Не удалось прочитать файл настроек %s: %s", settings_file, e)
        return

    num_threads = data.get('performance', {}).get('num_threads')
    if not num_threads:
        logger.info("performance.num_threads не задан — значения по умолчанию")
        return

    try:
        num_threads = int(num_threads)
    except (TypeError, ValueError):
        logger.warning("Некорректное значение num_threads: %r", num_threads)
        return

    if num_threads <= 0:
        logger.warning("num_threads должен быть положительным, получено: %d", num_threads)
        return

    # Установка переменных окружения.
    # Важно: они должны быть установлены до импорта onnxruntime в других модулях.
    os.environ['OMP_NUM_THREADS'] = str(num_threads)
    os.environ['MKL_NUM_THREADS'] = str(num_threads)

    logger.info("Настроено потоков для ONNX/OMP/MKL: %d", num_threads)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
    )


def main() -> int:
    """
    Точка входа в приложение.

    Упрощённого (fallback) режима нет: при любой критической ошибке
    пользователь получает понятное сообщение и трассировку стека.
    """
    _configure_logging()

    # Настройка производительности не критична для запуска — логируем и идём дальше
    try:
        setup_performance_settings()
    except Exception:
        logger.exception("Ошибка настройки производительности — продолжаем с параметрами по умолчанию")

    # PyQt6 импортируем здесь, чтобы при её отсутствии выдать понятное сообщение,
    # а не ImportError на верхнем уровне модуля
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
    except ImportError:
        logger.error("PyQt6 не установлена. Установите зависимости: pip install PyQt6")
        return 1

    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication(sys.argv)
        app.setApplicationName("TrustSpectra")
        app.setApplicationVersion("0.9.0")
        app.setStyle('Fusion')

        # --- Защита от второго экземпляра ---
        from utils.single_instance import ensure_single_instance
        if not ensure_single_instance():
            logger.warning("Экземпляр уже запущен, выход")
            return 0

        for i, screen in enumerate(app.screens()):
            size = screen.size()
            dpr = screen.devicePixelRatio()
            name = screen.name() or f"Screen {i+1}"
            logger.debug("Экран %s: %dx%d, DPR=%s", name, size.width(), size.height(), dpr)

        # 1. Применяем сохранённую тему
        from ui.styles.themes import load_saved_theme, update_theme_colors
        update_theme_colors(load_saved_theme())

        # 2. Регистрируем стили компонентов (побочный эффект импорта)
        from ui.styles import components  # noqa: F401 — _register_all_styles()
        from ui.styles.style_factory import sf

        registered = list(sf()._builders.keys())
        logger.info("Зарегистрировано стилей: %d — %s", len(registered), registered)

        # 3. Главное окно — без try/except вокруг создания, любая ошибка
        #    пробрасывается в общий handler ниже и выдаёт честный traceback
        from ui.main_window import MainWindow
        window = MainWindow()
        window.show()

        return app.exec()

    except Exception:
        logger.exception("Критическая ошибка при запуске приложения")
        return 1


if __name__ == "__main__":
    sys.exit(main())