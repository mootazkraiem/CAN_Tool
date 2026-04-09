try:
    from PyQt6.QtGui import QFont
    FONT_BOLD = QFont.Weight.Bold
    FONT_DEMIBOLD = QFont.Weight.DemiBold
    LETTER_SPACING_ABSOLUTE = QFont.SpacingType.AbsoluteSpacing
except ImportError:
    from PyQt5.QtGui import QFont
    FONT_BOLD = QFont.Bold
    FONT_DEMIBOLD = QFont.DemiBold
    LETTER_SPACING_ABSOLUTE = QFont.AbsoluteSpacing


INTRO_SPLASH_THEME = {
    "display_ms": 2600,
    "tick_ms": 16,
    "progress_max": 1000,
    "width": 860,
    "height": 520,
    "root_margin": 14,
    "panel_margin": 18,
    "panel_spacing": 14,
    "panel_radius": 14,
    "media_min_height": 320,
    "media_radius": 12,
    "progress_height": 12,
    "progress_radius": 6,
    "title_text": "CAN MASTER",
    "subtitle_text": "Diagnostics Suite",
    "status_text": "Loading workspace...",
    "fallback_media_text": "INITIALIZING VEHICLE DIAGNOSTICS",
    "panel_stylesheet": """
        QFrame#SplashPanel {
            background-color: rgba(12, 14, 18, 244);
            border: 1px solid rgba(120, 160, 220, 28);
            border-radius: 14px;
        }
    """,
    "media_stylesheet": """
        QLabel {
            background-color: rgba(4, 8, 14, 180);
            border-radius: 12px;
            border: 1px solid rgba(120, 160, 220, 22);
        }
    """,
    "progress_stylesheet": """
        QProgressBar {
            background-color: rgba(14, 18, 28, 235);
            border: 1px solid rgba(70, 96, 150, 0.34);
            border-radius: 6px;
        }
        QProgressBar::chunk {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #22D3EE,
                stop: 0.3 #38BDF8,
                stop: 0.68 #7C3AED,
                stop: 1 #A855F7
            );
            border-radius: 6px;
        }
    """,
    "title_color": "#E7F7FF",
    "subtitle_color": "#7FE7FF",
    "status_color": "#7F97AE",
    "fallback_media_color": "#CFE8FF",
}


def intro_title_font() -> QFont:
    font = QFont("Rajdhani", 28, FONT_BOLD)
    if font.family() == "Rajdhani":
        font.setLetterSpacing(LETTER_SPACING_ABSOLUTE, 2)
    return font


def intro_subtitle_font() -> QFont:
    return QFont("Bahnschrift", 16, FONT_DEMIBOLD)
