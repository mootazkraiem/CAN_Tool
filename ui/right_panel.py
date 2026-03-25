from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .theme import (
    CARD_MARGIN_COMPACT,
    FONT_FAMILY_MONO,
    FONT_SIZE_CAPTION,
    FONT_SIZE_SMALL,
    RIGHT_PANEL_WIDTH,
    THEME_DARK,
    get_theme_palette,
)


class DashboardAlertCard(QFrame):
    def __init__(self, severity, confidence, title, description, action_text, log_callback, parent=None):
        super().__init__(parent)
        self._log_callback = log_callback

        severity_key = severity.upper()
        self.setObjectName(
            "AlertCard_Critical"
            if severity_key == "CRITICAL"
            else "AlertCard_Warning"
            if severity_key == "WARNING"
            else "AlertCard_Info"
        )

        badge_name = {
            "CRITICAL": "BadgeCritical",
            "WARNING": "BadgeWarning",
            "INFO": "BadgeInfo",
        }[severity_key]

        root = QVBoxLayout(self)
        root.setContentsMargins(CARD_MARGIN_COMPACT, 16, CARD_MARGIN_COMPACT, 16)
        root.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        badge = QLabel(severity_key)
        badge.setObjectName(badge_name)

        conf = QLabel(confidence)
        conf.setObjectName("AlertTime")

        top.addWidget(badge)
        top.addStretch()
        top.addWidget(conf)

        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setObjectName("AlertTitle")

        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setObjectName("AlertDesc")

        actions = QHBoxLayout()
        actions.setSpacing(8)

        action_btn = QPushButton(action_text)
        action_btn.setObjectName("BtnContext")
        action_btn.clicked.connect(lambda: self._log_callback(f"[ACTION] {action_text} executed for {title}"))

        more_btn = QPushButton("...")
        more_btn.setObjectName("BtnContext")
        more_btn.setFixedWidth(40)
        more_btn.clicked.connect(lambda: self._log_callback(f"[DETAIL] Expanded anomaly details for {title}"))

        actions.addWidget(action_btn, 1)
        actions.addWidget(more_btn)

        root.addLayout(top)
        root.addWidget(title_lbl)
        root.addWidget(desc_lbl)
        root.addLayout(actions)


class HealthMiniCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SurfaceCardAlt")

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(8)

        self.icon = QLabel("o")
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setFixedSize(26, 26)

        self.title = QLabel("SYSTEM HEALTH")
        self.sub = QLabel("All subsystems nominal")

        head.addWidget(self.icon, 0, Qt.AlignVCenter)
        head.addWidget(self.title, 0, Qt.AlignVCenter)
        head.addStretch()

        self.bar_labels = []
        self.bar_tracks = []
        self.bar_fills = []

        bars = QHBoxLayout()
        bars.setSpacing(10)
        for name, width in [("CPU LOAD", 40), ("MEM BUFFER", 34)]:
            col = QVBoxLayout()
            col.setSpacing(4)

            label = QLabel(name)
            self.bar_labels.append(label)

            track = QFrame()
            track.setFixedHeight(8)
            self.bar_tracks.append(track)
            track_layout = QHBoxLayout(track)
            track_layout.setContentsMargins(0, 0, 0, 0)

            fill = QFrame()
            fill.setFixedWidth(width)
            self.bar_fills.append(fill)

            track_layout.addWidget(fill, 0, Qt.AlignLeft)
            track_layout.addStretch()

            col.addWidget(label)
            col.addWidget(track)
            bars.addLayout(col)

        root.addLayout(head)
        root.addWidget(self.sub)
        root.addLayout(bars)
        self.apply_theme(THEME_DARK)

    def apply_theme(self, theme_name: str):
        p = get_theme_palette(theme_name)
        self.icon.setStyleSheet(
            f"color: {p['health_icon_fg']}; background: {p['health_icon_bg']}; border: none; border-radius: 13px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; font-weight: 900;"
        )
        self.title.setStyleSheet(
            f"color: {p['health_title']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; font-weight: 800; letter-spacing: 1px;"
        )
        self.sub.setStyleSheet(
            f"color: {p['health_sub']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; font-weight: 700;"
        )
        for label in self.bar_labels:
            label.setStyleSheet(
                f"color: {p['health_label']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; font-weight: 700;"
            )
        for track in self.bar_tracks:
            track.setStyleSheet(f"QFrame {{ background: {p['health_track']}; border: none; border-radius: 4px; }}")
        for fill, color in zip(self.bar_fills, [p["health_cpu"], p["health_mem"]]):
            fill.setStyleSheet(f"background: {color}; border-radius: 4px;")


class RightPanelWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RightPanel")
        self.setFixedWidth(RIGHT_PANEL_WIDTH)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        self.title = QLabel("AI_ANOMALY_ENGINE")
        root.addWidget(self.title)

        cards = [
            (
                "CRITICAL",
                "98.4% CONF",
                "UNEXPECTED_TORQUE_DROP",
                "Detected atypical sequence on 0x0CF004FE. Potential physical layer degradation or injector mismatch.",
                "ISOLATE",
            ),
            (
                "WARNING",
                "72.1% CONF",
                "LATENCY_DRIFT_DETECTED",
                "Packet interval increasing on node 0x1A2. Jitter detected in 40ms window.",
                "ANALYZE_NODE",
            ),
        ]

        for severity, confidence, title_text, desc, action in cards:
            root.addWidget(DashboardAlertCard(severity, confidence, title_text, desc, action, self._append_log))

        self.health_card = HealthMiniCard()
        root.addWidget(self.health_card)
        root.addStretch()
        self.apply_theme(THEME_DARK)

    def _append_log(self, line: str):
        return

    def apply_theme(self, theme_name: str):
        p = get_theme_palette(theme_name)
        self.title.setStyleSheet(
            f"color: {p['viewer_title']}; font-family: '{FONT_FAMILY_MONO}'; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; letter-spacing: 1px;"
        )
        self.health_card.apply_theme(theme_name)
