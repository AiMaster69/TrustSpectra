import json
from pathlib import Path
from typing import Dict, Optional
from utils.logger import logger


class LocalizationService:
    """Сервис для управления локализацией."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.translations_dir = Path(__file__).parent / 'translations'
        self.current_language = 'auto'  # По умолчанию автоопределение
        self.translations: Dict[str, Dict[str, str]] = {}
        # Порядок языков: авто + по популярности использования в мире
        self.available_languages = ['auto', 'en', 'zh', 'es', 'fr', 'de', 'pt', 'ru']
        
        # Загружаем все переводы
        self._load_all_translations()
    
    def _load_all_translations(self):
        """Загружает все доступные переводы."""
        for lang in self.available_languages:
            if lang != 'auto':  # Пропускаем 'auto', это не реальный язык
                self._load_translation(lang)
    
    def _load_translation(self, language: str):
        """Загружает перевод для указанного языка."""
        try:
            translation_file = self.translations_dir / f'{language}.json'
            if translation_file.exists():
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations[language] = json.load(f)
                logger.info(f"Загружен перевод для языка: {language}")
            else:
                logger.warning(f"Файл перевода не найден: {translation_file}")
                self.translations[language] = {}
        except Exception as e:
            logger.error(f"Ошибка загрузки перевода для {language}: {e}")
            self.translations[language] = {}
    
    def set_language(self, language: str):
        """Устанавливает текущий язык."""
        if language in self.available_languages:
            self.current_language = language
            logger.info(f"Язык изменен на: {language}")
        else:
            logger.warning(f"Неподдерживаемый язык: {language}")
    
    def get_language(self) -> str:
        """Возвращает текущий язык."""
        return self.current_language
    
    def get_actual_language(self) -> str:
        """
        Возвращает фактический язык для использования.
        Если установлен 'auto', определяет язык системы.
        
        Returns:
            Код языка для использования
        """
        if self.current_language == 'auto':
            return self._detect_system_language()
        return self.current_language
    
    def _detect_system_language(self) -> str:
        """
        Определяет язык системы.
        
        Returns:
            Код языка из доступных или 'en' по умолчанию
        """
        try:
            import locale
            import os
            
            lang_code = None
            
            # Способ 1: Переменная окружения LANG (работает на Linux/Mac)
            lang_env = os.environ.get('LANG', '')
            if lang_env:
                lang_code = lang_env.split('_')[0].lower()
                if lang_code in self.available_languages and lang_code != 'auto':
                    logger.info(f"Определен системный язык из LANG: {lang_code}")
                    return lang_code
            
            # Способ 2: getlocale (работает на Windows и Unix)
            try:
                locale.setlocale(locale.LC_ALL, '')
                current_locale = locale.getlocale()[0]
                
                if current_locale:
                    # Обрабатываем разные форматы:
                    # Windows: 'Russian_Russia', 'English_United States'
                    # Unix: 'ru_RU', 'en_US'
                    
                    # Маппинг Windows-названий на коды языков
                    windows_lang_map = {
                        'russian': 'ru',
                        'english': 'en',
                        'chinese': 'zh',
                        'spanish': 'es',
                        'french': 'fr',
                        'german': 'de',
                        'portuguese': 'pt'
                    }
                    
                    # Пробуем Unix-формат (ru_RU)
                    if '_' in current_locale:
                        lang_code = current_locale.split('_')[0].lower()
                    else:
                        # Пробуем Windows-формат (Russian_Russia)
                        lang_name = current_locale.split('_')[0].lower()
                        lang_code = windows_lang_map.get(lang_name)
                    
                    if lang_code and lang_code in self.available_languages and lang_code != 'auto':
                        logger.info(f"Определен системный язык из locale: {lang_code}")
                        return lang_code
            except Exception as e:
                logger.debug(f"Ошибка при определении локали через getlocale: {e}")
            
        except Exception as e:
            logger.warning(f"Не удалось определить системный язык: {e}")
        
        # По умолчанию английский
        logger.info("Используется язык по умолчанию: en")
        return 'en'
    
    def get_text(self, key: str, language: Optional[str] = None) -> str:
        """
        Получает переведенный текст по ключу.
        
        Args:
            key: Ключ перевода (может быть вложенным через точку)
            language: Язык (если None, используется текущий)
            
        Returns:
            Переведенный текст или ключ, если перевод не найден
        """
        # Определяем фактический язык
        if language is None:
            lang = self.get_actual_language()
        elif language == 'auto':
            lang = self._detect_system_language()
        else:
            lang = language
        
        if lang not in self.translations:
            logger.warning(f"Переводы для языка {lang} не загружены")
            return key
        
        # Поддержка вложенных ключей (например, "ui.buttons.load")
        keys = key.split('.')
        current = self.translations[lang]
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            logger.debug(f"Перевод не найден для ключа: {key} (язык: {lang})")
            return key
    
    def get_available_languages(self) -> list:
        """Возвращает список доступных языков."""
        return self.available_languages.copy()
    
    def get_language_name(self, language: str) -> str:
        """Возвращает название языка."""
        names = {
            'auto': self.get_text('ui.labels.language_auto'),  # Переводимое название
            'en': 'English',
            'zh': '中文',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'pt': 'Português',
            'ru': 'Русский'
        }
        return names.get(language, language)


# Глобальный экземпляр сервиса
_localization_service = LocalizationService()


def get_text(key: str, language: Optional[str] = None) -> str:
    """
    Удобная функция для получения переведенного текста.
    
    Args:
        key: Ключ перевода
        language: Язык (если None, используется текущий)
        
    Returns:
        Переведенный текст
    """
    return _localization_service.get_text(key, language)
