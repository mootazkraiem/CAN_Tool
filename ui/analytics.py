from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import numpy as np
from .theme import CARD_MARGIN, COMPACT_SPACING, PAGE_MARGIN, SECTION_SPACING, THEME_DARK, get_theme_palette


class AnalyticsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AnalyticsPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        root.setSpacing(SECTION_SPACING)
        p = get_theme_palette(THEME_DARK)

        tiles_layout = QHBoxLayout()
        tiles_layout.setSpacing(COMPACT_SPACING * 2)

        tile_data = [
            ("TOTAL MESSAGES", "1,245,802", "MSG", p["accent_cyan"]),
            ("BUS UTILIZATION", "42.8", "%", p["accent_primary"]),
            ("ERROR FRAMES", "14", "ERR", p["badge_warning_fg"]),
            ("PEAK BITRATE", "501.2", "kbps", p["accent_cyan"]),
        ]

        for title, val, unit, color in tile_data:
            tile = QFrame()
            tile.setObjectName("metricCard")
            l = QVBoxLayout(tile)
            l.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)

            t_lbl = QLabel(title)
            t_lbl.setObjectName("SectionTitle")

            v_layout = QHBoxLayout()
            v_lbl = QLabel(val)
            v_lbl.setObjectName("MonoValue")
            v_lbl.setStyleSheet(f"color: {color};")

            u_lbl = QLabel(unit)
            u_lbl.setObjectName("MutedLabel")

            v_layout.addWidget(v_lbl)
            v_layout.addWidget(u_lbl)
            v_layout.addStretch()

            l.addWidget(t_lbl)
            l.addLayout(v_layout)
            tiles_layout.addWidget(tile)

        root.addLayout(tiles_layout)

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(COMPACT_SPACING * 2)

        for title, accent in [("BUS LOAD TREND", p["accent_cyan"]), ("RESPONSE LATENCY", p["accent_primary"])]:
            c_panel = QFrame()
            c_panel.setObjectName("SurfaceCard")
            c_lay = QVBoxLayout(c_panel)
            c_lay.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)

            h = QLabel(title)
            h.setObjectName("SectionTitle")

            bar_container = QWidget()
            bar_lay = QHBoxLayout(bar_container)
            bar_lay.setContentsMargins(0, COMPACT_SPACING + 4, 0, 0)
            bar_lay.setSpacing(4)
            bar_lay.setAlignment(Qt.AlignBottom)

            for _ in range(30):
                b = QFrame()
                h_val = np.random.randint(10, 80)
                b.setFixedHeight(h_val)
                b.setFixedWidth(6)
                base = p["card_hover"] if h_val < 60 else accent
                b.setStyleSheet(f"background: {base}; border-radius: 3px;")
                bar_lay.addWidget(b)

            c_lay.addWidget(h)
            c_lay.addWidget(bar_container)
            charts_layout.addWidget(c_panel)

        root.addLayout(charts_layout)

        log_panel = QWidget()
        log_lay = QVBoxLayout(log_panel)
        log_lay.setContentsMargins(0, 0, 0, 0)
        log_lay.setSpacing(10)

        log_head = QLabel("ANALYTICS EVENT LOG")
        log_head.setObjectName("SectionTitle")

        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setFixedHeight(168)
        log_text.setText(
            """
[12:55:01] INFO: Bus utilization spiked to 82% during burst capture.
[12:55:12] WARNING: 4 error frames detected on CAN_2 (ID: 0x7FF).
[12:56:04] SUCCESS: CSV session export completed (24.2 MB).
[12:57:30] ANALYTICS: Peak data rate reached 501.2 kbps.
            """.strip()
        )
        log_text.setStyleSheet(
            f"QTextEdit {{ background: {p['card_bg']}; border: 1px solid {p.get('strong_border', p['card_border'])}; border-radius: 12px; padding: 12px 14px; }}"
        )

        log_lay.addWidget(log_head)
        log_lay.addWidget(log_text)
        root.addWidget(log_panel)
