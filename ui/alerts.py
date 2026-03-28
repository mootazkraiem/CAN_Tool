from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from core.anomaly import Anomaly
from .theme import CARD_MARGIN_COMPACT, PAGE_MARGIN, SECTION_SPACING


class AlertCardWidget(QFrame):
    analyze_requested = pyqtSignal(object)
    ignore_requested = pyqtSignal(object)

    def __init__(self, anomaly: Anomaly, parent=None):
        super().__init__(parent)
        self.anomaly = anomaly
        self.setObjectName(self._card_name(anomaly))

        root = QVBoxLayout(self)
        root.setContentsMargins(CARD_MARGIN_COMPACT, 16, CARD_MARGIN_COMPACT, 16)
        root.setSpacing(10)

        head = QHBoxLayout()
        self.badge = QLabel()
        self.title = QLabel()
        self.title.setObjectName("AlertTitle")
        self.title.setWordWrap(True)
        self.confidence = QLabel()
        self.confidence.setObjectName("AlertTime")
        head.addWidget(self.badge)
        head.addWidget(self.title, 1)
        head.addWidget(self.confidence)

        self.desc = QLabel()
        self.desc.setWordWrap(True)
        self.desc.setObjectName("AlertDesc")

        footer = QHBoxLayout()
        self.timestamp = QLabel()
        self.timestamp.setObjectName("AlertTime")
        self.analyze = QPushButton("Analyze")
        self.analyze.setObjectName("BtnContext")
        self.ignore = QPushButton("Ignore")
        self.ignore.setObjectName("GhostButton")
        self.analyze.clicked.connect(lambda: self.analyze_requested.emit(self.anomaly))
        self.ignore.clicked.connect(lambda: self.ignore_requested.emit(self.anomaly))
        footer.addWidget(self.timestamp)
        footer.addStretch()
        footer.addWidget(self.analyze)
        footer.addWidget(self.ignore)

        root.addLayout(head)
        root.addWidget(self.desc)
        root.addLayout(footer)
        self.update_anomaly(anomaly)

    def update_anomaly(self, anomaly: Anomaly):
        self.anomaly = anomaly
        severity = anomaly.severity.upper()
        self.setObjectName(self._card_name(anomaly))
        self.badge.setText(severity)
        self.badge.setObjectName("BadgeCritical" if severity == "CRITICAL" else "BadgeWarning" if severity == "WARNING" else "BadgeInfo")
        self.title.setText(anomaly.title)
        suffix = f"  x{anomaly.occurrences}" if anomaly.occurrences > 1 else ""
        self.desc.setText(f"{anomaly.description}{suffix}")
        self.confidence.setText(f"{anomaly.confidence * 100:.1f}%")
        self.timestamp.setText(datetime.fromtimestamp(anomaly.timestamp).strftime("%H:%M:%S"))
        self.style().unpolish(self)
        self.style().polish(self)
        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)

    @staticmethod
    def _card_name(anomaly: Anomaly) -> str:
        severity = anomaly.severity.upper()
        return "AlertCard_Critical" if severity == "CRITICAL" else "AlertCard_Warning" if severity == "WARNING" else "AlertCard_Info"


class AlertsWidget(QWidget):
    analyze_requested = pyqtSignal(object)
    ignore_requested = pyqtSignal(object)
    MAX_ALERTS = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alerts: Dict[str, Anomaly] = {}
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

        self.content = QWidget()
        self.layout = QVBoxLayout(self.content)
        self.layout.setSpacing(16)
        self.layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.content)
        root.addWidget(scroll)
        self._render()

    def upsert_anomaly(self, anomaly: Anomaly):
        if not anomaly or not anomaly.title:
            return
        self._alerts[anomaly.alert_id] = anomaly
        if len(self._alerts) > self.MAX_ALERTS:
            oldest = sorted(self._alerts.values(), key=lambda item: item.timestamp)[: len(self._alerts) - self.MAX_ALERTS]
            for item in oldest:
                self._alerts.pop(item.alert_id, None)
        self._render()

    def remove_anomaly(self, alert_id: str):
        self._alerts.pop(alert_id, None)
        self._render()

    def clear(self):
        self._alerts.clear()
        self._render()

    def _render(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        alerts: List[Anomaly] = sorted(self._alerts.values(), key=lambda item: item.timestamp, reverse=True)
        if not alerts:
            empty = QLabel("No anomalies detected yet.")
            empty.setObjectName("MutedLabel")
            self.layout.addWidget(empty)
            return

        for anomaly in alerts:
            card = AlertCardWidget(anomaly)
            card.analyze_requested.connect(self.analyze_requested.emit)
            card.ignore_requested.connect(self.ignore_requested.emit)
            self.layout.addWidget(card)
        self.layout.addStretch()
