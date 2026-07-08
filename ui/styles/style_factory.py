from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class StyleFactory:
    """
    Фабрика стилей. Хранит текущую палитру и размеры,
    генерирует QSS через шаблоны-функции с автоматическим кэшированием.
    """

    def __init__(self) -> None:
        self._colors: Dict[str, str] = {}
        self._sizes: Dict[str, int] = {}
        self._cache: Dict[str, str] = {}
        self._builders: Dict[str, Callable[[], str]] = {}

    # Регистрация данных темы

    def register_palette(self, colors: Dict[str, str]) -> None:
        """Регистрирует палитру цветов."""
        self._colors = colors.copy()
        self._cache.clear()

    def register_sizes(self, sizes: Dict[str, int]) -> None:
        """Регистрирует размеры."""
        self._sizes = sizes.copy()
        self._cache.clear()

    def update_colors(self, colors: Dict[str, str]) -> None:
        """Обновляет цвета и сбрасывает кэш."""
        self._colors.update(colors.copy())
        self._cache.clear()

    # Доступ к значениям

    def color(self, key: str, fallback: str = "#FFFFFF") -> str:
        return self._colors.get(key, fallback)

    def size(self, key: str, fallback: int = 0) -> int:
        return self._sizes.get(key, fallback)

    # Регистрация шаблонов

    def register(self, name: str, builder: Callable[[], str]) -> None:
        """Регистрирует именованный шаблон стиля."""
        self._builders[name] = builder
        self._cache.pop(name, None)

    def build(self, name: str) -> str:
        """Возвращает готовый QSS по имени шаблона."""
        if name in self._cache:
            return self._cache[name]
        builder = self._builders.get(name)
        if builder is None:
            raise KeyError(f"Шаблон стиля '{name}' не зарегистрирован")
        result = builder()
        self._cache[name] = result
        return result

    def refresh(self) -> None:
        """Сбрасывает кэш — вызывать после смены темы."""
        self._cache.clear()

    def invalidate(self, name: str) -> None:
        """Сбрасывает кэш конкретного шаблона."""
        self._cache.pop(name, None)

    # Утилиты для inline-стилей

    def inline(self, **rules: Any) -> str:
        """Генерирует однострочный CSS из kwargs."""
        if not rules:
            return ""
        return "; ".join(f"{k.replace('_', '-')}:{v}" for k, v in rules.items()) + ";"

    def widget_style(self, selector: str, **rules: Any) -> str:
        """Генерирует блок QSS для одного селектора."""
        body = self.inline(**rules)
        return f"{selector} {{ {body} }}"

    # Глобальный синглтон

    _instance: Optional["StyleFactory"] = None

    @classmethod
    def instance(cls) -> "StyleFactory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Удобные алиасы для использования в модулях


def sf() -> StyleFactory:
    """Возвращает глобальный экземпляр StyleFactory."""
    return StyleFactory.instance()


def register_style(name: str, builder: Callable[[], str]) -> None:
    """Регистрирует шаблон в глобальной фабрике."""
    sf().register(name, builder)


def get_style(name: str) -> str:
    """Возвращает готовый QSS по имени."""
    return sf().build(name)


def refresh_all_styles() -> None:
    """Сбрасывает кэш всех стилей — вызывать при смене темы."""
    sf().refresh()
