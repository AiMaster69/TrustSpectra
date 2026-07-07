from .analyzer_adapter import create_analyzer_adapter

# Создаем анализатор через адаптер для безопасного импорта
TrustSpectra = create_analyzer_adapter

__all__ = ['TrustSpectra'] 