import json
import os
from pathlib import Path
from typing import Dict, Any

from utils.paths import get_user_data_dir
from utils.logger import logger
from .style_factory import sf, register_style


THEME_COLORS: Dict[str, Dict[str, str]] = {
    "light": {
        "primary": "#1976D2",         
        "background": "#FFFFFF",
        "text": "#212121",           
        "text_on_primary": "#FFFFFF",
        "secondary": "#757575",        
        "button_bg": "#F5F5F5",
        "button_hover": "#E0E0E0",
        "title_bg": "#F5F5F5",
        "border": "#E0E0E0",
        "success": "#43A047",         
        "warning": "#FB8C00",         
        "error": "#E53935",           
        "info": "#1E88E5",             
        "surface": "#FFFFFF",
        "surface_alt": "#F5F5F5",
        "segment_bg": "#FAFAFA",
    },
    "dark": {
        "primary": "#42A5F5",          
        "background": "#121212",       
        "text": "#E0E0E0",             
        "text_on_primary": "#000000",  
        "secondary": "#B0BEC5",       
        "button_bg": "#2C2C2C",        
        "button_hover": "#3D3D3D",
        "title_bg": "#1E1E1E",         
        "border": "#333333",           
        "success": "#66BB6A",          
        "warning": "#FFA726",          
        "error": "#EF5350",            
        "info": "#42A5F5",
        "surface": "#1E1E1E",         
        "surface_alt": "#252525",     
        "segment_bg": "#2C2C2C",      
    },
}
COLORS: Dict[str, str] = THEME_COLORS["dark"].copy()

SIZES: Dict[str, int] = {
    "button_height": 40,
    "slider_height": 4,
    "slider_handle": 16,
    "timeline_height": 150,
    "font_size": 14,
    "radius": 8,
    "spacing": 20,
    "title_height": 35,
    "content_margin": 30,
    "content_width": 1200,
    "content_min_width": 800,
}


def update_theme_colors(theme: str) -> None:
    if theme in THEME_COLORS:
        COLORS.update(THEME_COLORS[theme])
        sf().update_colors(COLORS)
        logger.info(f"Тема изменена на: {theme}")
    else:
        logger.warning(f"Неизвестная тема: {theme}")


def save_theme(theme: str) -> None:
    try:
        config_dir = get_user_data_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        settings_file = config_dir / "theme.json"
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump({"theme": theme}, f, indent=2, ensure_ascii=False)
        logger.info(f"Тема сохранена: {theme}")
    except Exception as e:
        logger.error(f"Ошибка сохранения темы: {e}")


def load_saved_theme() -> str:
    try:
        settings_file = get_user_data_dir() / "theme.json"
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("theme", "dark")
        return "dark"
    except Exception as e:
        logger.error(f"Ошибка загрузки темы: {e}")
        return "dark"


def get_current_theme() -> str:
    for theme_name, theme_colors in THEME_COLORS.items():
        if theme_colors == COLORS:
            return theme_name
    return "dark"


def get_available_themes() -> list:
    return list(THEME_COLORS.keys())


def create_custom_theme(name: str, colors: Dict[str, str]) -> bool:
    try:
        THEME_COLORS[name] = colors
        logger.info(f"Создана пользовательская тема: {name}")
        return True
    except Exception as e:
        logger.error(f"Ошибка создания темы: {e}")
        return False


def export_theme(theme_name: str, file_path: str) -> bool:
    try:
        if theme_name in THEME_COLORS:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(THEME_COLORS[theme_name], f, indent=2, ensure_ascii=False)
            logger.info(f"Тема экспортирована в {file_path}")
            return True
        logger.error(f"Тема не найдена: {theme_name}")
        return False
    except Exception as e:
        logger.error(f"Ошибка экспорта темы: {e}")
        return False


def import_theme(file_path: str, theme_name: str = None) -> bool:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            colors = json.load(f)
        if theme_name is None:
            theme_name = Path(file_path).stem
        THEME_COLORS[theme_name] = colors
        logger.info(f"Тема импортирована: {theme_name}")
        return True
    except Exception as e:
        logger.error(f"Ошибка импорта темы: {e}")
        return False


sf().register_palette(COLORS)
sf().register_sizes(SIZES)