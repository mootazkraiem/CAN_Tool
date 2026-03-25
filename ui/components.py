from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from .theme import (
    CARD_MARGIN,
    FONT_FAMILY_MONO,
    FONT_SIZE_HERO,
    FONT_SIZE_LARGE,
    FONT_SIZE_CAPTION,
    INFO_BLOCK_BAR_HEIGHT,
)

class MetricCard(QFrame):
    def __init__(self, title, value, unit, color_hex):
        super().__init__()
        self.setObjectName("MetricCard")
        # Apply glowing border and rounded corners
        self.setStyleSheet(f"""
            #MetricCard {{
                background: #0A0D12;
                border: 1px solid {color_hex}40;
                border-radius: 12px;
            }}
            #MetricCard:hover {{
                border: 1px solid {color_hex}90;
                background: #0D1118;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: #94A3B8; font-size: {FONT_SIZE_CAPTION}px; font-weight: 700; letter-spacing: 1px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")
        
        val_layout = QHBoxLayout()
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color: #F8FAFC; font-size: {FONT_SIZE_HERO}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")
        unit_lbl = QLabel(unit)
        unit_lbl.setStyleSheet(f"color: #64748B; font-size: {FONT_SIZE_LARGE}px; font-weight: 700; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; padding-top: 12px;")
        
        val_layout.addWidget(val_lbl)
        val_layout.addWidget(unit_lbl)
        val_layout.addStretch()
        
        bar = QFrame()
        bar.setFixedHeight(INFO_BLOCK_BAR_HEIGHT)
        bar.setStyleSheet(f"background: {color_hex}; border-radius: 1px; border: none;")
        
        layout.addWidget(title_lbl)
        layout.addLayout(val_layout)
        layout.addStretch()
        layout.addWidget(bar)
