from .style_factory import sf, register_style
from .themes import COLORS, SIZES


def _c(key: str, fallback: str = "#FFFFFF") -> str:
    """Короткий алиас для получения цвета."""
    return sf().color(key, fallback)


def _s(key: str, fallback: int = 0) -> int:
    """Короткий алиас для получения размера."""
    return sf().size(key, fallback)


# РЕГИСТРАЦИЯ ШАБЛОНОВ

def _register_all_styles() -> None:
    """Регистрирует все именованные шаблоны стилей."""

    # Базовые кнопки
    register_style("button", lambda: f"""
        QPushButton {{
            min-height: {_s('button_height')}px;
            border-radius: {_s('radius')}px;
            background: {_c('button_bg')};
            color: {_c('text')};
            border: none;
            padding: 8px 16px;
            font-size: {_s('font_size')}px;
        }}
        QPushButton:hover {{
            background: {_c('button_hover')};
        }}
        QPushButton:pressed {{
            background: {_c('primary')};
            color: white;
        }}
        QPushButton:disabled {{
            background: {_c('border')};
            color: {_c('secondary')};
        }}
    """)

    # Кнопка настроек
    register_style("settings_button", lambda: f"""
        QPushButton {{
            background: {_c('button_bg')};
            color: {_c('text')};
            border: none;
            border-radius: 8px;
            font-size: 20px;
            font-weight: bold;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-width: 40px;
            min-height: {_s('button_height')}px;
            max-width: 40px;
            max-height: {_s('button_height')}px;
        }}
        QPushButton:hover {{
            background: {_c('button_hover')};
        }}
        QPushButton:pressed {{
            background: {_c('primary')};
            color: white;
        }}
        QPushButton:checked {{
            background: {_c('primary')};
            color: white;
        }}
    """)

    # Кнопка анализа
    register_style("analyze_button", lambda: f"""
        QPushButton {{
            min-height: {_s('button_height')}px;
            border-radius: {_s('radius')}px;
            background: {_c('primary')};
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: {_s('font_size')}px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {_c('button_hover')};
        }}
        QPushButton:pressed {{
            background: {_c('secondary')};
        }}
        QPushButton:disabled {{
            background: {_c('border')};
            color: {_c('secondary')};
        }}
    """)

    # Заголовок / Title
    register_style("title", lambda: f"""
        background: {_c('title_bg')};
        border-radius: {_s('radius')}px;
        border: none;
    """)

    # Слайдер
    register_style("slider", lambda: f"""
        QSlider::groove:horizontal {{
            border: none;
            height: {_s('slider_height')}px;
            background: {_c('button_bg')};
            border-radius: {_s('slider_height') // 2}px;
            margin: 2px 0;
        }}
        QSlider::handle:horizontal {{
            background: {_c('primary')};
            border: none;
            width: {_s('slider_handle')}px;
            height: {_s('slider_handle')}px;
            margin: -{_s('slider_handle') // 2 - _s('slider_height') // 2}px 0;
            border-radius: {_s('slider_handle') // 2}px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {_c('button_hover')};
        }}
        QSlider::handle:horizontal:pressed {{
            background: {_c('secondary')};
        }}
        QSlider::sub-page:horizontal {{
            background: {_c('primary')};
            border-radius: {_s('slider_height') // 2}px;
        }}
    """)

    # ComboBox
    register_style("combobox", lambda: f"""
        QComboBox {{
            min-height: {_s('button_height')}px;
            border-radius: {_s('radius')}px;
            background: {_c('button_bg')};
            color: {_c('text')};
            border: 1px solid {_c('border')};
            padding: 0 8px;
            font-size: {_s('font_size')}px;
        }}
        QComboBox:hover {{
            background: {_c('button_hover')};
            border-color: {_c('primary')};
        }}
        QComboBox:focus {{
            border-color: {_c('primary')};
            background: {_c('button_hover')};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {_c('text')};
            width: 0px;
            height: 0px;
            margin-right: 6px;
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: {_c('primary')};
        }}
        QComboBox QAbstractItemView {{
            background: {_c('button_bg')};
            color: {_c('text')};
            border: 1px solid {_c('border')};
            border-radius: {_s('radius')}px;
            selection-background-color: {_c('primary')};
            selection-color: white;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 6px 12px;
            border-radius: {_s('radius') - 2}px;
            margin: 2px;
            background: transparent;
            color: {_c('text')};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background: {_c('button_hover')};
            color: {_c('primary')};
        }}
    """)

    # SpinBox
    register_style("spinbox", lambda: f"""
        QSpinBox, QDoubleSpinBox {{
            min-height: {_s('button_height')}px;
            border-radius: {_s('radius')}px;
            background: {_c('button_bg')};
            color: {_c('text')};
            border: none;
            padding: 0 8px;
            font-size: {_s('font_size')}px;
        }}
        QSpinBox:hover, QDoubleSpinBox:hover {{
            background: {_c('button_hover')};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            background: {_c('button_hover')};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            border: none;
            background: transparent;
            width: 16px;
            margin: 0;
            padding: 0;
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            border: none;
            background: transparent;
            width: 16px;
            margin: 0;
            padding: 0;
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background: transparent;
        }}
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: transparent;
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-bottom: 5px solid {_c('text')};
            width: 0;
            height: 0;
        }}
        QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {{
            border-bottom-color: {_c('primary')};
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {_c('text')};
            width: 0;
            height: 0;
        }}
        QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {{
            border-top-color: {_c('primary')};
        }}
    """)

    # CheckBox
    register_style("checkbox", lambda: f"""
        QCheckBox {{
            spacing: 8px;
            font-size: {_s('font_size')}px;
            color: {_c('text')};
            background: transparent;
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid {_c('border')};
            background: {_c('button_bg')};
        }}
        QCheckBox::indicator:checked {{
            background: {_c('primary')};
            border-color: {_c('primary')};
        }}
        QCheckBox::indicator:hover {{
            border-color: {_c('primary')};
            background: {_c('button_hover')};
        }}
        QCheckBox::indicator:pressed {{
            background: {_c('secondary')};
            border-color: {_c('secondary')};
        }}
    """)

    # GroupBox
    register_style("groupbox", lambda: f"""
        QGroupBox {{
            font-weight: bold;
            font-size: {_s('font_size')}px;
            border: 2px solid {_c('border')};
            border-radius: {_s('radius')}px;
            margin-top: 10px;
            padding-top: 10px;
            color: {_c('text')};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: {_c('text')};
        }}
    """)

    # ScrollBar (толстый, общий)
    register_style("scrollbar", lambda: f"""
        QScrollBar:vertical {{
            background: {_c('button_bg')};
            width: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background: {_c('border')};
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {_c('primary')};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {_c('button_bg')};
            height: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background: {_c('border')};
            border-radius: 6px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {_c('primary')};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """)

    # ToolTip
    register_style("tooltip", lambda: f"""
        QToolTip {{
            color: {_c('text')};
            background-color: {_c('background')};
            border: 1px solid {_c('border')};
            border-radius: {_s('radius') - 2}px;
            padding: 4px 8px;
            font-size: {_s('font_size') - 2}px;
        }}
    """)

    # TimeLabel
    register_style("time_label", lambda: f"""
        QLabel {{
            color: {_c('text')};
            font-size: {_s('font_size') - 2}px;
            background: transparent;
            border: none;
        }}
    """)

    # MainWidget
    register_style("main_widget", lambda: f"""
        QWidget {{
            background: {_c('background')};
            color: {_c('text')};
            border-radius: 0px;
        }}
    """)

    

    register_style("file_block", lambda: f"""
       QFrame#file_block {{
           background-color: {_c('surface_alt', _c('button_bg'))};
           border: none;
           border-radius: {_s('radius', 8)}px;
       }}
""")

    register_style("segment_block", lambda: f"""
        QFrame#segment_block {{
            background-color: {_c('segment_bg', _c('button_bg'))};
            border: none;
            border-radius: {_s('radius', 4)}px;
        }}
    """)

    register_style("file_header", lambda: f"""
        QLabel#file_header {{
            color: {_c('primary')};
            padding: {_s('padding', 12)}px;
            border: none;
            background-color: transparent;
            max-height: {_s('file_header_max_height', 60)}px;
        }}
    """)

    register_style("file_info", lambda: f"""
        QLabel#file_info {{
            color: {_c('text')};
            padding: {_s('padding', 12)}px;
            max-height: {_s('file_info_max_height', 60)}px;
            background-color: transparent;
            border: none;
        }}
    """)

    register_style("progress_label", lambda: f"""
        QLabel#progress_label {{
            color: {_c('secondary')};
            padding: {_s('padding', 12)}px;
            background-color: transparent;
            border: none;
        }}
    """)

    register_style("time_button", lambda: f"""
        QPushButton {{
            background: transparent;
            border: none;
            color: {_c('primary')};
            text-align: left;
            padding: {_s('small_padding', 4)}px;
            min-width: {_s('time_button_min_width', 70)}px;
            max-width: {_s('time_button_max_width', 100)}px;
        }}
    """)

    register_style("scrollbar_thin_horizontal", lambda: f"""
        QScrollBar:horizontal {{
            height: {_s('scrollbar_thin_width', 6)}px;
            background: transparent;
            border: none;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {_c('border')};
            border-radius: {_s('scrollbar_thin_handle_radius', 3)}px;
            min-width: {_s('scrollbar_thin_min_size', 20)}px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {_c('primary')};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
        QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
            width: 0;
            height: 0;
            background: none;
            border: none;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
    """)

    register_style("scrollbar_thin_vertical", lambda: f"""
        QScrollBar:vertical {{
            width: {_s('scrollbar_thin_width', 6)}px;
            background: transparent;
            border: none;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {_c('border')};
            border-radius: {_s('scrollbar_thin_handle_radius', 3)}px;
            min-height: {_s('scrollbar_thin_min_size', 20)}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {_c('primary')};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
            height: 0;
            width: 0;
            background: none;
            border: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
    """)

        # TimelineWidget
    register_style("timeline_widget", lambda: f"""
        TimelineWidget {{
            background-color: {_c('background')};
        }}
        QWidget#results_container {{
            background-color: transparent;
            border: 2px solid {_c('border')};
            border-radius: {_s('radius', 8)}px;
            margin: 5px;
        }}
        QFrame#file_block {{
            border: none;
            border-radius: {_s('radius', 8)}px;
            background-color: {_c('surface_alt', _c('button_bg'))};
        }}
        QLabel[objectName="file_info"] {{
            background-color: transparent;
            border: none;
        }}
        QLabel[objectName="progress_label"] {{
            background-color: transparent;
            border: none;
        }}
        QFrame[objectName="segment_block"] {{
            background-color: {_c('segment_bg', _c('button_bg'))};
            border: none;
            border-radius: {_s('radius', 4)}px;
        }}
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        QScrollArea QWidget {{
            background-color: transparent;
        }}
        QLabel {{
            color: {_c('text')};
        }}
        {sf().build('tooltip')}
    """)

    # SettingsWidget
    register_style("settings_widget", lambda: f"""
        QWidget {{
            background: {_c('background')};
            color: {_c('text')};
            border: none;
        }}
        QScrollBar:vertical {{
            width: 6px;
            background: transparent;
            border: none;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {_c('border')};
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {_c('primary')};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
            height: 0;
            width: 0;
            background: none;
            border: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        QScrollArea {{
            border: none;
            background: {_c('background')};
        }}
        QScrollArea > QWidget > QWidget {{
            background: {_c('background')};
        }}
        QLabel {{
            background: transparent;
            color: {_c('text')};
            font-size: {_s('font_size')}px;
            padding: 0px;
            margin: 0px;
        }}
        QPushButton {{
            border-radius: {_s('radius')}px;
            background: {_c('button_bg')};
            color: {_c('text')};
            border: none;
            padding: 4px 8px;
            font-size: {_s('font_size')}px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {_c('button_hover')};
        }}
        QPushButton:pressed {{
            background: {_c('primary')};
            color: white;
        }}
        QPushButton:disabled {{
            background: {_c('border')};
            color: {_c('secondary')};
        }}
        QWidget#settings_block {{
            background: {_c('button_bg')};
            border: none;
            border-radius: {_s('radius')}px;
        }}
        QLabel[class="title"] {{
            font-weight: bold;
            font-size: {_s('font_size') + 2}px;
            padding: 0px;
            margin: 0px;
        }}
        QLineEdit {{
            border-radius: {_s('radius')}px;
            background: {_c('button_bg')};
            color: {_c('text')};
            border: 1px solid {_c('border')};
            padding: 0 8px;
            font-size: {_s('font_size')}px;
        }}
        QLineEdit:hover {{
            border-color: {_c('primary')};
            background: {_c('button_hover')};
        }}
        QLineEdit:focus {{
            border-color: {_c('primary')};
            background: {_c('button_hover')};
        }}
    """)

    # SettingsBlock
    register_style("settings_block", lambda: f"""
        QWidget {{
            border: none;
            border-radius: {_s('radius')}px;
            background: {_c('button_bg')};
        }}
        QLabel {{
            color: {_c('text')};
            background: transparent;
            font-size: {_s('font_size')}px;
            padding: 0px;
            margin: 0px;
        }}
        QLabel[class="title"] {{
            font-weight: bold;
            font-size: {_s('font_size') + 2}px;
            padding: 0px;
            margin: 0px;
        }}
    """)

    # CloseButton
    register_style("close_button", lambda: f"""
        QPushButton {{
            background: transparent;
            color: {_c('text')};
            border: none;
            border-radius: 16px;
            font-size: 18px;
            min-width: 32px;
            min-height: 32px;
            max-width: 32px;
            max-height: 32px;
        }}
        QPushButton:hover {{
            background: {_c('error')};
            color: white;
        }}
        QPushButton:pressed {{
            background: {_c('primary')};
            color: white;
        }}
    """)

    # PlayerWidget
    register_style("player_widget", lambda: f"""
        QPushButton {{
            background: {_c('button_bg')};
            border: none;
            border-radius: {_s('radius')}px;
            color: {_c('text')};
            font-family: 'Material Icons';
            font-size: 18px;
        }}
        QPushButton:hover {{
            background: {_c('button_hover')};
        }}
        QPushButton:pressed {{
            background: {_c('button_bg')};
        }}
        QLabel#time_label {{
            color: {_c('text')};
            background: transparent;
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            min-width: 36px;
        }}
        QSlider {{
            margin: 0;
        }}
        QSlider::groove:horizontal {{
            border: none;
            height: 4px;
            background: {_c('border')};
            border-radius: 2px;
            margin: 4px 0;
        }}
        QSlider::handle:horizontal {{
            background: {_c('primary')};
            border-radius: 8px;
            width: 16px;
            height: 16px;
            margin: -6px 0;
        }}
        QSlider::add-page:horizontal {{
            background: {_c('border')};
            border-top-right-radius: 2px;
            border-bottom-right-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{
            background: {_c('primary')};
            border-top-left-radius: 2px;
            border-bottom-left-radius: 2px;
        }}
        {sf().build('tooltip')}
    """)

    # TitleBar
    register_style("title_bar", lambda: f"""
        TitleBar {{
            background: {_c('title_bg')};
            border-top-left-radius: {_s('radius')}px;
            border-top-right-radius: {_s('radius')}px;
        }}
        QLabel {{
            color: {_c('text')};
            background: transparent;
        }}
        QWidget {{
            background: transparent;
        }}
        {sf().build('tooltip')}
    """)

    # FileListWidget
    register_style("file_list", lambda: f"""
        QListWidget {{
            background: {_c('button_bg')};
            border: 1px solid {_c('border')};
            border-radius: {_s('radius')}px;
            color: {_c('text')};
            font-size: {_s('font_size')}px;
            padding: 4px;
        }}
        QListWidget::item {{
            border-radius: {_s('radius') - 2}px;
            padding: 6px 8px;
            margin: 2px;
        }}
        QListWidget::item:hover {{
            background: {_c('button_hover')};
        }}
        QListWidget::item:selected {{
            background: {_c('primary')};
            color: white;
        }}
        QScrollBar:vertical {{
            width: 6px;
            background: transparent;
            border: none;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {_c('border')};
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {_c('primary')};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """)

    # ThemedMessageBox
    register_style("message_box", lambda: f"""
        QMessageBox {{
            background: {_c('background')};
        }}
        QLabel {{
            color: {_c('text')};
            font-size: {_s('font_size')}px;
        }}
        QPushButton {{
            min-height: {_s('button_height')}px;
            border-radius: {_s('radius')}px;
            background: {_c('button_bg')};
            color: {_c('text')};
            border: none;
            padding: 8px 16px;
            font-size: {_s('font_size')}px;
        }}
        QPushButton:hover {{
            background: {_c('button_hover')};
        }}
        QPushButton:pressed {{
            background: {_c('primary')};
            color: white;
        }}
    """)
    
    # ThemedDialog
    register_style("themed_dialog", lambda: f"""
        QWidget#dialogContent {{
            background-color: {_c('surface_alt', _c('button_bg'))};
            border-radius: {_s('dialog_radius', 12)}px;
            border: none;
        }}
        QLabel#dialogIcon {{
            background-color: transparent;
        }}
        QLabel#dialogTitle {{
            color: {_c('text')};
            background-color: transparent;
            font-size: {_s('dialog_title_size', 14)}px;
            font-weight: bold;
        }}
        QLabel#dialogMessage {{
            color: {_c('text')};
            background-color: transparent;
            line-height: 1.5;
            font-size: {_s('font_size')}px;
        }}
        
        /* Главная кнопка (синяя, без рамок) */
        QPushButton#dialogConfirmButton {{
            background-color: {_c('primary')};
            color: white;
            border: none;
            border-radius: {_s('radius', 6)}px;
            font-size: {_s('font_size', 13)}px;
            font-weight: bold;
            padding: 0 20px; /* Чтобы любой текст влезал и дышал */
        }}
        QPushButton#dialogConfirmButton:hover {{
            background-color: {_c('button_hover')};
        }}
        QPushButton#dialogConfirmButton:pressed {{
            background-color: {_c('secondary')};
        }}

        /* Кнопка отмены (серая, без рамок) */
        QPushButton#dialogCancelButton {{
            background-color: {_c('button_bg')};
            color: {_c('text')};
            border: none;
            border-radius: {_s('radius', 6)}px;
            font-size: {_s('font_size', 13)}px;
            font-weight: bold;
            padding: 0 20px; /* Чтобы любой текст влезал и дышал */
        }}
        QPushButton#dialogCancelButton:hover {{
            background-color: {_c('button_hover')};
        }}
        QPushButton#dialogCancelButton:pressed {{
            background-color: {_c('secondary')};
            color: white;
        }}
    """)




# Выполняем регистрацию при импорте модуля
_register_all_styles()