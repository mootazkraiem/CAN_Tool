from .theme import (
    BUTTON_HEIGHT,
    FONT_FAMILY_FALLBACK,
    FONT_FAMILY_MONO,
    FONT_FAMILY_UI,
    FONT_SIZE_CAPTION,
    FONT_SIZE_HERO,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_MICRO,
    FONT_SIZE_SMALL,
    FONT_SIZE_XL,
    INPUT_HEIGHT,
    RADIUS_LARGE,
    RADIUS_MEDIUM,
    RADIUS_SMALL,
    SIDEBAR_BUTTON_HEIGHT,
    TAB_HEIGHT,
    get_theme_palette,
)


def get_stylesheet(theme_name="Carbon Cyan"):
    p = get_theme_palette(theme_name)
    return f"""
    QMainWindow, QWidget {{
        background-color: {p["window_bg"]};
        color: {p["window_fg"]};
        font-family: '{FONT_FAMILY_UI}', '{FONT_FAMILY_FALLBACK}', sans-serif;
        font-size: {FONT_SIZE_LARGE}px;
    }}

    QLabel {{
        color: {p["window_fg"]};
        background: transparent;
        font-size: {FONT_SIZE_LARGE}px;
    }}

    QPushButton {{
        font-family: '{FONT_FAMILY_UI}', '{FONT_FAMILY_FALLBACK}', sans-serif;
        font-size: {FONT_SIZE_LARGE}px;
        min-height: {BUTTON_HEIGHT}px;
    }}

    QLineEdit, QComboBox, QPlainTextEdit, QTextEdit {{
        font-family: '{FONT_FAMILY_UI}', '{FONT_FAMILY_FALLBACK}', sans-serif;
        font-size: {FONT_SIZE_LARGE}px;
    }}

    QTableWidget, QListWidget, QTreeWidget {{
        font-size: {FONT_SIZE_MEDIUM}px;
    }}

    QStatusBar {{
        background: {p["status_bg"]};
        color: {p["status_fg"]};
        border-top: 1px solid {p["topbar_border"]};
        font-size: {FONT_SIZE_SMALL}px;
    }}

    QToolTip {{
        background: {p["tooltip_bg"]};
        color: {p["window_fg"]};
        border: 1px solid {p["tooltip_border"]};
        padding: 6px 8px;
        font-size: {FONT_SIZE_SMALL}px;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {p["scroll_handle"]};
        border-radius: 4px;
        min-height: 34px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p["scroll_handle_hover"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        height: 0;
        background: transparent;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p["scroll_handle"]};
        border-radius: 4px;
        min-width: 34px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {p["scroll_handle_hover"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        width: 0;
        background: transparent;
    }}

    QFrame#Sidebar {{
        background-color: {p["sidebar_bg"]};
        border-right: 1px solid {p["sidebar_border"]};
    }}

    QLabel#SidebarBrand {{
        color: {p["topbar_title"]};
        font-family: '{FONT_FAMILY_MONO}', monospace;
        font-size: {FONT_SIZE_XL}px;
        font-weight: 800;
        letter-spacing: 1px;
    }}

    QLabel#SidebarVersionTag {{
        color: {p["sidebar_version"]};
        font-family: '{FONT_FAMILY_MONO}', monospace;
        font-size: {FONT_SIZE_MICRO}px;
        font-weight: 800;
        letter-spacing: 2px;
    }}

    QLabel#SidebarFooter {{
        color: {p["sidebar_footer"]};
        font-family: '{FONT_FAMILY_MONO}', monospace;
        font-size: {FONT_SIZE_MICRO}px;
        font-weight: 700;
        border-top: 1px solid {p["sidebar_border"]};
        padding: 14px 0;
    }}

    QPushButton#SidebarBtn {{
        background-color: {p.get("sidebar_btn_bg", p["sidebar_bg"])};
        text-align: left;
        border-radius: 10px;
        border: none;
        min-height: {SIDEBAR_BUTTON_HEIGHT}px;
    }}
    QPushButton#SidebarBtn QLabel {{
        color: {p["sidebar_btn_fg"]};
        font-size: {FONT_SIZE_LARGE}px;
        font-weight: 600;
    }}
    QPushButton#SidebarBtn:hover {{
        background-color: {p["sidebar_btn_hover_bg"]};
        border: none;
    }}
    QPushButton#SidebarBtn:hover QLabel {{
        color: {p["sidebar_btn_hover_fg"]};
    }}
    QPushButton#SidebarBtn:checked {{
        background-color: {p["sidebar_btn_checked_bg"]};
        border: 1px solid {p["sidebar_btn_checked_border"]};
        border-left: 3px solid {p["accent_primary"]};
    }}
    QPushButton#SidebarBtn:checked QLabel {{
        color: {p["sidebar_btn_checked_fg"]};
        font-weight: 700;
    }}

    QFrame#TopBar {{
        background-color: {p["topbar_bg"]};
        border-bottom: 1px solid {p["topbar_border"]};
    }}

    QLabel#TopbarTitle {{
        color: {p["topbar_title"]};
        font-family: '{FONT_FAMILY_MONO}', monospace;
        font-size: {FONT_SIZE_XL}px;
        font-weight: 800;
        letter-spacing: 1px;
    }}

    QPushButton#BtnTopBarTab {{
        background: transparent;
        color: {p["tab_fg"]};
        border: none;
        font-size: {FONT_SIZE_LARGE}px;
        font-weight: 600;
        min-height: {max(28, TAB_HEIGHT - 6)}px;
        padding: 5px 12px;
        border-radius: 8px;
    }}
    QPushButton#BtnTopBarTab:hover {{
        background: #232323;
        color: {p["tab_hover_fg"]};
    }}
    QPushButton#BtnTopBarTabActive {{
        background: {p["card_bg"]};
        color: {p["tab_active_fg"]};
        border: 1px solid {p.get("strong_border", p["card_border"])};
        border-radius: 8px;
        font-size: {FONT_SIZE_LARGE}px;
        font-weight: 700;
        min-height: {max(28, TAB_HEIGHT - 6)}px;
        padding: 5px 12px;
    }}

    QFrame#TopStatusLive, QFrame#TopStatusOffline {{
        border-radius: {RADIUS_MEDIUM}px;
        min-height: {BUTTON_HEIGHT}px;
    }}
    QFrame#TopStatusLive {{
        background-color: {p["status_live_bg"]};
        border: 1px solid {p["status_live_border"]};
    }}
    QFrame#TopStatusLive QLabel {{
        color: {p["status_live_fg"]};
    }}
    QFrame#TopStatusOffline {{
        background-color: {p["status_offline_bg"]};
        border: 1px solid {p["status_offline_border"]};
    }}
    QFrame#TopStatusOffline QLabel {{
        color: {p["status_offline_fg"]};
    }}

    QPushButton#BtnLiveCapture {{
        background-color: {p["status_live_bg"]};
        color: {p["status_live_fg"]};
        border: 1px solid {p["status_live_border"]};
        border-radius: {RADIUS_SMALL}px;
        padding: 6px 16px;
        min-height: {BUTTON_HEIGHT}px;
        font-family: '{FONT_FAMILY_MONO}', monospace;
        font-size: {FONT_SIZE_SMALL}px;
        font-weight: 800;
        letter-spacing: 1px;
    }}
    QPushButton#BtnLiveCapture:hover {{
        background-color: {p["btn_primary_hover_bg"]};
    }}
    QPushButton#BtnOffline {{
        background-color: {p["status_offline_bg"]};
        color: {p["status_offline_fg"]};
        border: 1px solid {p["status_offline_border"]};
        border-radius: {RADIUS_SMALL}px;
        padding: 6px 16px;
        min-height: {BUTTON_HEIGHT}px;
        font-family: '{FONT_FAMILY_MONO}', monospace;
        font-size: {FONT_SIZE_SMALL}px;
        font-weight: 800;
        letter-spacing: 1px;
    }}

    QLineEdit, QComboBox, QPlainTextEdit, QTextEdit {{
        background-color: {p["input_bg"]};
        border: 1px solid {p["input_border"]};
        border-radius: {RADIUS_MEDIUM}px;
        padding: 8px 12px;
        color: {p["input_fg"]};
        min-height: {INPUT_HEIGHT}px;
        font-size: {FONT_SIZE_LARGE}px;
        selection-background-color: {p["accent_primary"]};
        selection-color: {p["window_fg"]};
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{
        border: 1px solid {p["input_focus_border"]};
        background-color: {p["input_focus_bg"]};
    }}
    QLineEdit::placeholder {{
        color: {p["input_placeholder"]};
        font-size: {FONT_SIZE_MEDIUM}px;
    }}
    QComboBox {{
        min-height: {INPUT_HEIGHT}px;
        padding-right: 24px;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p["dropdown_bg"]};
        border: 1px solid {p["dropdown_border"]};
        border-radius: {RADIUS_MEDIUM}px;
        color: {p["input_fg"]};
        font-size: {FONT_SIZE_MEDIUM}px;
        selection-background-color: {p["dropdown_selection_bg"]};
        outline: none;
    }}

    QTableWidget, QListWidget, QTreeWidget, QPlainTextEdit, QTextEdit {{
        background-color: {p["table_bg"]};
        color: {p["table_fg"]};
        alternate-background-color: {p["table_alt_bg"]};
        gridline-color: transparent;
        border: 1px solid {p["table_border"]};
        border-radius: 12px;
        selection-background-color: {p["table_selection_bg"]};
        selection-color: {p["table_selection_fg"]};
        outline: none;
    }}
    QTableWidget::item, QListWidget::item, QTreeWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {p["table_item_border"]};
    }}
    QTableWidget::item:hover, QListWidget::item:hover, QTreeWidget::item:hover {{
        background-color: {p["dropdown_selection_bg"]};
    }}
    QListWidget::item:selected, QTreeWidget::item:selected {{
        background: {p["dropdown_selection_bg"]};
        border: 1px solid {p["accent_primary"]};
    }}

    QHeaderView::section {{
        background-color: {p["header_bg"]};
        color: {p["header_fg"]};
        padding: 10px;
        border: none;
        border-bottom: 1px solid {p["header_border"]};
        font-size: {FONT_SIZE_CAPTION}px;
        font-weight: 800;
        font-family: '{FONT_FAMILY_MONO}', monospace;
        letter-spacing: 1px;
    }}

    QFrame#RightPanel {{
        background-color: {p["right_panel_bg"]};
        border-left: 1px solid {p["right_panel_border"]};
    }}

    QFrame#metricCard {{
        background-color: {p["card_bg"]};
        border: 1px solid {p["card_border"]};
        border-radius: 12px;
    }}
    QFrame#metricCard:hover {{
        background-color: {p["card_hover"] if "card_hover" in p else p["dropdown_selection_bg"]};
        border: 1px solid {p["accent_primary"]};
    }}

    QFrame#AlertCard,
    QFrame#AlertCard_Info,
    QFrame#AlertCard_Warning,
    QFrame#AlertCard_Critical,
    QFrame#SurfaceCard,
    QFrame#SurfaceCardAlt {{
        background-color: {p["card_bg"]};
        border: 1px solid {p["card_border"]};
        border-radius: 12px;
    }}
    QFrame#SurfaceCardAlt {{
        background-color: {p["card_alt_bg"]};
    }}
    QFrame#SurfaceCard:hover,
    QFrame#SurfaceCardAlt:hover,
    QFrame#AlertCard:hover,
    QFrame#AlertCard_Info:hover,
    QFrame#AlertCard_Warning:hover,
    QFrame#AlertCard_Critical:hover {{
        background-color: {p["card_hover"] if "card_hover" in p else p["dropdown_selection_bg"]};
    }}
    QFrame#AlertCard_Info {{
        border-top: 1px solid {p["alert_info_border"]};
    }}
    QFrame#AlertCard_Warning {{
        border-top: 1px solid {p["alert_warning_border"]};
    }}
    QFrame#AlertCard_Critical {{
        border-top: 1px solid {p["alert_critical_border"]};
    }}

    QFrame#HealthCard {{
        background-color: {p["card_bg"]};
        border: 1px solid {p.get("strong_border", p["card_border"])};
        border-radius: 14px;
    }}

    QFrame#ChatBubbleUser, QFrame#ChatBubbleAI {{
        border-radius: 14px;
        border: 1px solid {p.get("strong_border", p["card_border"])};
    }}
    QFrame#ChatBubbleUser {{
        background-color: {p["card_hover"]};
        border-color: {p["accent_primary"]};
    }}
    QFrame#ChatBubbleAI {{
        background-color: {p["card_bg"]};
    }}
    QFrame#ChatBubbleUser QLabel, QFrame#ChatBubbleAI QLabel {{
        background: transparent;
        font-size: {FONT_SIZE_SMALL}px;
        color: {p["window_fg"]};
    }}

    QLabel#AlertTitle {{
        font-size: {FONT_SIZE_SMALL}px;
        font-weight: 700;
        color: {p["alert_title"]};
    }}
    QLabel#AlertDesc {{
        font-size: {FONT_SIZE_MICRO}px;
        color: {p["alert_desc"]};
        line-height: 1.45;
    }}
    QLabel#AlertTime {{
        font-size: {FONT_SIZE_CAPTION}px;
        color: {p["alert_time"]};
        font-family: '{FONT_FAMILY_MONO}', monospace;
    }}

    QLabel#BadgeCritical, QLabel#BadgeWarning, QLabel#BadgeInfo, QLabel#CountBadge {{
        border-radius: 9px;
        padding: 4px 10px;
        font-size: {FONT_SIZE_MICRO}px;
        font-weight: 800;
        font-family: '{FONT_FAMILY_MONO}', monospace;
        letter-spacing: 0.5px;
    }}
    QLabel#BadgeCritical {{
        background-color: {p["badge_critical_bg"]};
        color: {p["badge_critical_fg"]};
        border: 1px solid {p["badge_critical_border"]};
    }}
    QLabel#BadgeWarning {{
        background-color: {p["badge_warning_bg"]};
        color: {p["badge_warning_fg"]};
        border: 1px solid {p["badge_warning_border"]};
    }}
    QLabel#BadgeInfo {{
        background-color: {p["badge_info_bg"]};
        color: {p["badge_info_fg"]};
        border: 1px solid {p["badge_info_border"]};
    }}
    QLabel#CountBadge {{
        background-color: {p["count_badge_bg"]};
        color: {p["count_badge_fg"]};
        border: 1px solid {p["count_badge_border"]};
    }}

    QLabel#SectionTitle {{
        font-size: {FONT_SIZE_CAPTION}px;
        font-weight: 800;
        color: {p["section_title"]};
        font-family: '{FONT_FAMILY_MONO}', monospace;
        letter-spacing: 2px;
    }}

    QLabel#MutedLabel {{
        color: {p["muted_label"]};
        font-size: {FONT_SIZE_SMALL}px;
        font-weight: 600;
    }}

    QLabel#PanelTitle {{
        color: {p["panel_title"]};
        font-size: {FONT_SIZE_LARGE}px;
        font-weight: 700;
    }}

    QLabel#MonoValue {{
        color: {p["mono_value"]};
        font-size: {FONT_SIZE_HERO}px;
        font-weight: 800;
        font-family: '{FONT_FAMILY_MONO}', monospace;
    }}

    QPushButton#BtnContext, QPushButton#PrimaryButton, QPushButton#GhostButton {{
        border-radius: {RADIUS_SMALL}px;
        padding: 7px 12px;
        min-height: {BUTTON_HEIGHT}px;
        font-size: {FONT_SIZE_SMALL}px;
        font-weight: 700;
        font-family: '{FONT_FAMILY_MONO}', monospace;
    }}
    QPushButton#BtnContext, QPushButton#GhostButton {{
        background-color: {p["btn_context_bg"]};
        color: {p["btn_context_fg"]};
        border: 1px solid {p["btn_context_border"]};
    }}
    QPushButton#BtnContext:hover, QPushButton#GhostButton:hover {{
        background-color: {p["btn_context_hover_bg"]};
        border-color: {p["btn_context_hover_border"]};
        color: {p["btn_context_hover_fg"]};
    }}
    QPushButton#PrimaryButton {{
        background-color: {p["btn_primary_bg"]};
        color: {p["btn_primary_fg"]};
        border: 1px solid {p["btn_primary_border"]};
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {p["btn_primary_hover_bg"]};
    }}

    QLabel#HealthKey {{
        font-size: {FONT_SIZE_SMALL}px;
        color: {p["health_key"]};
    }}
    QLabel#HealthVal {{
        font-size: {FONT_SIZE_SMALL}px;
        color: {p["health_val"]};
        font-weight: 700;
        font-family: '{FONT_FAMILY_MONO}', monospace;
    }}

    QFrame#Divider {{
        background: {p["divider"]};
        max-height: 1px;
        border: none;
    }}

    QSlider::groove:horizontal {{
        background: {p["slider_groove"]};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {p["slider_fill"]};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {p["slider_handle"]};
        width: 12px;
        margin: -5px 0;
        border-radius: 6px;
        border: 1px solid {p["slider_handle_border"]};
    }}

    QSplitter::handle {{
        background-color: transparent;
    }}
    QSplitter::handle:horizontal {{
        width: 8px;
    }}
    QSplitter::handle:vertical {{
        height: 8px;
    }}
    """
