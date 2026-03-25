from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import *
from .theme import (
    BUTTON_HEIGHT,
    PAGE_MARGIN_LARGE,
    SETTINGS_COMBO_MIN_WIDTH,
    SETTINGS_SAVE_WIDTH,
    THEME_CHOICES,
    THEME_DARK,
    INPUT_HEIGHT,
)


class SettingsWidget(QWidget):
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        self.theme_combo = None

        root = QVBoxLayout(self)
        root.setContentsMargins(PAGE_MARGIN_LARGE, PAGE_MARGIN_LARGE, PAGE_MARGIN_LARGE, PAGE_MARGIN_LARGE)
        root.setSpacing(26)
        root.setAlignment(Qt.AlignTop)

        sections = [
            (
                "CAN INTERFACE CONFIGURATION",
                [
                    ("Bus Bitrate", ["500 kbps", "250 kbps", "1000 kbps (CAN-FD)"]),
                    ("Interface Type", ["SocketCAN (Native)", "Peak CAN", "Vector CAN"]),
                    ("Silent Mode", ["Enabled", "Disabled"]),
                ],
            ),
            (
                "VISUAL ENGINE AND UX",
                [
                    ("Glow Effects", ["High Intensity", "Balanced", "Disabled"]),
                    ("Font Scaling", ["1.0x (Standard)", "1.1x (Large)", "1.2x (Extreme)"]),
                    ("Theme", THEME_CHOICES),
                ],
            ),
        ]

        for section_title, settings in sections:
            section_card = QFrame()
            section_card.setObjectName("SurfaceCard")
            section_layout = QVBoxLayout(section_card)
            section_layout.setContentsMargins(24, 22, 24, 22)
            section_layout.setSpacing(18)

            sec_lbl = QLabel(section_title)
            sec_lbl.setObjectName("SectionTitle")
            section_layout.addWidget(sec_lbl)

            grid = QGridLayout()
            grid.setHorizontalSpacing(24)
            grid.setVerticalSpacing(16)

            for i, (label, options) in enumerate(settings):
                s_lbl = QLabel(label)
                s_lbl.setObjectName("PanelTitle")

                combo = QComboBox()
                combo.addItems(options)
                combo.setFixedHeight(INPUT_HEIGHT)
                combo.setMinimumWidth(SETTINGS_COMBO_MIN_WIDTH)
                if label == "Theme":
                    self.theme_combo = combo
                    self.theme_combo.setCurrentText(THEME_DARK)

                grid.addWidget(s_lbl, i, 0)
                grid.addWidget(combo, i, 1)

            section_layout.addLayout(grid)
            root.addWidget(section_card)

        btn_save = QPushButton("APPLY SYSTEM CONFIGURATION")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setFixedWidth(SETTINGS_SAVE_WIDTH)
        btn_save.setFixedHeight(BUTTON_HEIGHT)
        btn_save.clicked.connect(self._emit_theme_change)
        root.addWidget(btn_save)
        root.addStretch()

    def set_theme(self, theme_name: str):
        if self.theme_combo is not None:
            self.theme_combo.setCurrentText(theme_name)

    def _emit_theme_change(self):
        if self.theme_combo is not None:
            self.theme_changed.emit(self.theme_combo.currentText())
