# ui/sidebar.py

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from .theme import (
    SIDEBAR_BUTTON_HEIGHT,
    SIDEBAR_ICON_WIDTH,
    SIDEBAR_LOGO_HEIGHT,
    SIDEBAR_WIDTH,
)

# Nav item: (label, icon_char)
NAV_ITEMS = [
    ("Dashboard",        "⊞"),
    ("Log Playback",     "▶"),
    ("Decoder Manager",  "⚙"),
    ("AI Alerts",        "⚡"),
    ("Analytics",        "◈"),
    ("Settings",         "≡"),
]

class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarBtn")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(SIDEBAR_BUTTON_HEIGHT)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(14)

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setFixedWidth(SIDEBAR_ICON_WIDTH)
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._icon_lbl.setObjectName("MutedLabel")

        self._text_lbl = QLabel(label)
        self._text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout.addWidget(self._icon_lbl)
        layout.addWidget(self._text_lbl)
        layout.addStretch()

        self.setText("")


class SidebarWidget(QFrame):
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Logo area ────────────────────────────────
        logo_frame = QFrame()
        logo_frame.setFixedHeight(SIDEBAR_LOGO_HEIGHT)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        logo_layout.setContentsMargins(20, 0, 20, 0)
        logo_layout.setSpacing(6)

        brand = QLabel("CAN_BUS_MASTER")
        brand.setObjectName("SidebarBrand")

        sub = QLabel("V2.4.0-STABLE")
        sub.setObjectName("SidebarVersionTag")

        logo_layout.addWidget(brand)
        logo_layout.addWidget(sub)

        # ── Nav section label ─────────────────────────
        nav_label = QLabel("NAVIGATION")
        nav_label.setObjectName("SectionTitle")
        nav_label.setContentsMargins(14, 20, 0, 8)

        # ── Buttons ──────────────────────────────────
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.buttons = []

        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(10, 0, 10, 0)
        nav_layout.setSpacing(4)

        for i, (label, icon) in enumerate(NAV_ITEMS):
            btn = NavButton(icon, label)
            if i == 0:
                btn.setChecked(True)
            self.btn_group.addButton(btn, i)
            nav_layout.addWidget(btn)
            self.buttons.append(btn)

        self.btn_group.idClicked.connect(self.page_changed.emit)

        # ── Version footer ────────────────────────────
        version_label = QLabel("v2.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setObjectName("SidebarFooter")

        outer.addWidget(logo_frame)
        outer.addWidget(nav_label)
        outer.addWidget(nav_container)
        outer.addStretch()
        outer.addWidget(version_label)
