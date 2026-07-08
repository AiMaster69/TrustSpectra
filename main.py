import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        from run import main

        main()
    except ImportError:
        # Настраиваем общее количество потоков для CPU-вычислений
        try:
            from core.services.settings_service import SettingsService

            service = SettingsService()
            perf_settings = service.get_category("performance")
            num_threads = perf_settings.get("num_threads")

            if num_threads:
                os.environ["OMP_NUM_THREADS"] = str(num_threads)
                os.environ["MKL_NUM_THREADS"] = str(num_threads)
        except Exception:
            pass

        # Запуск приложения
        from PyQt6.QtWidgets import QApplication

        from ui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("TrustSpectra")
        app.setApplicationVersion("0.9.0")

        # --- Защита от второго экземпляра ---
        from utils.single_instance import ensure_single_instance

        if not ensure_single_instance():
            sys.exit(0)

        window = MainWindow()
        window.show()

        sys.exit(app.exec())
