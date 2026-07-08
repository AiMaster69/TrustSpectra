from PyQt6.QtCore import QLocale
from PyQt6.QtGui import QDoubleValidator, QValidator


class FallbackDoubleValidator(QDoubleValidator):
    """
    Валидатор для PyQt6.
    """

    def __init__(
        self,
        bottom: float,
        top: float,
        decimals: int,
        default_value: float,
        parent=None,
    ):
        super().__init__(bottom, top, decimals, parent)
        self.default_value = default_value
        self.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.setLocale(QLocale(QLocale.Language.C))  # Точка как разделитель

    def validate(self, input_str: str, pos: int) -> tuple:
        # Разрешаем пустую строку или одиночные символы как начало ввода
        if not input_str or input_str in (".", "-"):
            return (QValidator.State.Intermediate, input_str, pos)

        try:
            # Пробуем преобразовать в число
            float(input_str)

            # Если строка заканчивается на точку (пользователь еще печатает),
            # считаем это допустимым промежуточным состоянием
            if input_str.endswith("."):
                return (QValidator.State.Intermediate, input_str, pos)

            # Число корректно
            return (QValidator.State.Acceptable, input_str, pos)

        except ValueError:
            # Блокируем только явно нечисловые символы (буквы, множественные точки и т.д.)
            return (QValidator.State.Invalid, input_str, pos)

    def fixup(self, input_text: str) -> None:
        """
        В PyQt6 обязан возвращать None.
        """
        return None
