from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from .theme import CARD_MARGIN_COMPACT, PAGE_MARGIN, SECTION_SPACING


class AlertsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AlertsPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        root.setSpacing(SECTION_SPACING)

        header = QLabel("AI POWERED ANOMALY DETECTION")
        header.setObjectName("SectionTitle")
        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)

        mock_alerts = [
            ("CRITICAL", "VOLTAGE INSTABILITY DETECTED", "Phase A/B voltage differential > 12V. Potential inverter failure imminent.", "12:55:01"),
            ("WARNING", "HIGH THERMAL STRESS", "Motor stator temperature reached 94.2C. Power throttling is partially active.", "12:54:12"),
            ("INFO", "SESSION OPTIMIZATION", "Regen-braking efficiency improved by 4 percent in the last 10 km.", "12:50:45"),
            ("WARNING", "ASYNC MESSAGE DETECTED", "Unexpected 0x1A2 interval deviation on CAN_1.", "12:48:30"),
        ]

        badge_map = {
            "CRITICAL": "BadgeCritical",
            "WARNING": "BadgeWarning",
            "INFO": "BadgeInfo",
        }

        for severity, title, desc, time in mock_alerts:
            card = QFrame()
            card.setObjectName(
                "AlertCard_Critical"
                if severity == "CRITICAL"
                else "AlertCard_Warning"
                if severity == "WARNING"
                else "AlertCard_Info"
            )
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(CARD_MARGIN_COMPACT, 16, CARD_MARGIN_COMPACT, 16)
            c_lay.setSpacing(10)

            h_lay = QHBoxLayout()
            h_lay.setSpacing(10)

            s_lbl = QLabel(severity)
            s_lbl.setObjectName(badge_map[severity])

            t_lbl = QLabel(title)
            t_lbl.setObjectName("AlertTitle")

            time_lbl = QLabel(time)
            time_lbl.setObjectName("AlertTime")

            h_lay.addWidget(s_lbl)
            h_lay.addWidget(t_lbl)
            h_lay.addStretch()
            h_lay.addWidget(time_lbl)

            d_lbl = QLabel(desc)
            d_lbl.setWordWrap(True)
            d_lbl.setObjectName("AlertDesc")

            c_lay.addLayout(h_lay)
            c_lay.addWidget(d_lbl)
            layout.addWidget(card)

        scroll.setWidget(content)
        root.addWidget(scroll)
