
class TrustSpectraError(Exception):
    """Базовое исключение для приложения."""
    pass


class AudioFileError(TrustSpectraError):
    """Исключение для ошибок работы с аудио файлами."""
    pass


class ModelError(TrustSpectraError):
    """Исключение для ошибок работы с моделью."""
    pass


class ConfigurationError(TrustSpectraError):
    """Исключение для ошибок конфигурации."""
    pass


class UIError(TrustSpectraError):
    """Исключение для ошибок пользовательского интерфейса."""
    pass


class AnalysisError(TrustSpectraError):
    """Исключение для ошибок анализа."""
    pass


class FileServiceError(TrustSpectraError):
    """Исключение для ошибок сервиса файлов."""
    pass


class SettingsError(TrustSpectraError):
    """Исключение для ошибок настроек."""
    pass 