from __future__ import annotations

from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout

from core.anomaly import Anomaly
from core.decoder import DecodedSignal
from .theme import FONT_FAMILY_MONO, FONT_SIZE_CAPTION, FONT_SIZE_MICRO, FONT_SIZE_SMALL, RIGHT_PANEL_WIDTH, THEME_DARK, get_theme_palette


class DashboardAlertCard(QFrame):
    def __init__(self, anomaly: Anomaly, parent=None):
        super().__init__(parent)
        self.anomaly = anomaly
        self.setObjectName(self._card_name(anomaly))
        self.setMinimumHeight(92)
        self.setMaximumHeight(108)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.badge = QLabel()
        self.conf = QLabel()
        self.conf.setObjectName("AlertTime")
        self.more_btn = QPushButton("...")
        self.more_btn.setObjectName("GhostButton")
        self.more_btn.setFixedSize(28, 28)
        top.addWidget(self.badge, 0, Qt.AlignLeft)
        top.addStretch()
        top.addWidget(self.conf, 0, Qt.AlignRight)
        top.addWidget(self.more_btn, 0, Qt.AlignRight)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("AlertTitle")
        self.title_lbl.setWordWrap(False)

        self.desc_lbl = QLabel()
        self.desc_lbl.setObjectName("AlertDesc")
        self.desc_lbl.setWordWrap(False)

        root.addLayout(top)
        root.addWidget(self.title_lbl)
        root.addWidget(self.desc_lbl)
        self.update_anomaly(anomaly)

    def update_anomaly(self, anomaly: Anomaly):
        self.anomaly = anomaly
        self.setObjectName(self._card_name(anomaly))
        severity_key = anomaly.severity.upper()
        self.badge.setText(severity_key)
        self.badge.setObjectName("BadgeCritical" if severity_key == "CRITICAL" else "BadgeWarning" if severity_key == "WARNING" else "BadgeInfo")
        self.conf.setText(f"{anomaly.confidence * 100:.1f}%")
        self.title_lbl.setText(anomaly.title)
        self.desc_lbl.setText(self._compact_description(anomaly.description))
        self.style().unpolish(self)
        self.style().polish(self)
        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)

    @staticmethod
    def _card_name(anomaly: Anomaly) -> str:
        severity_key = anomaly.severity.upper()
        return "AlertCard_Critical" if severity_key == "CRITICAL" else "AlertCard_Warning" if severity_key == "WARNING" else "AlertCard_Info"

    @staticmethod
    def _compact_description(description: str) -> str:
        cleaned = " ".join((description or "").split())
        return cleaned[:72] + "..." if len(cleaned) > 75 else cleaned


class HealthMiniCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HealthCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(7)

        self.title = QLabel("SYSTEM HEALTH")
        self.sub = QLabel("Reader idle")
        self.cpu = QLabel("CPU LOAD 32%")
        self.mem = QLabel("MEM BUFFER 48%")

        root.addWidget(self.title)
        root.addWidget(self.sub)
        root.addWidget(self.cpu)
        root.addWidget(self.mem)
        self.apply_theme(THEME_DARK)

    def update_status(self, mode: str, signal_count: int):
        if mode == "live":
            self.sub.setText(f"Live CAN ingest active | {signal_count} decoded")
        elif mode == "simulation":
            self.sub.setText(f"Simulation mode active | {signal_count} decoded")
        else:
            self.sub.setText("Reader idle")

    def apply_theme(self, theme_name: str):
        p = get_theme_palette(theme_name)
        self.title.setStyleSheet(
            f"color: {p['health_title']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; font-weight: 800;"
        )
        self.sub.setStyleSheet(
            f"color: {p['health_sub']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_MICRO}px; font-weight: 700;"
        )
        for label in (self.cpu, self.mem):
            label.setStyleSheet(
                f"color: {p['viewer_stats']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_MICRO}px;"
            )


class RightPanelWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RightPanel")
        self.setFixedWidth(RIGHT_PANEL_WIDTH)
        self._counts: Dict[str, int] = {"critical": 0, "warning": 0, "info": 0}
        self._anomalies: Dict[str, Anomaly] = {}
        self._decoded_count = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        self.title = QLabel("AI_ANOMALY_ENGINE")
        self.summary = QLabel("Critical: 0 | Warning: 0 | Info: 0")

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.cards_host = QFrame()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.scroll.setWidget(self.cards_host)

        self.health_card = HealthMiniCard()

        root.addWidget(self.title)
        root.addWidget(self.summary)
        root.addWidget(self.scroll, 1)
        root.addWidget(self.health_card)
        self.apply_theme(THEME_DARK)
        self._render_cards()

    def add_signal(self, signal: DecodedSignal):
        self._decoded_count += 1

    def upsert_anomaly(self, anomaly: Anomaly):
        if not anomaly or not anomaly.title:
            return
        self._anomalies[anomaly.alert_id] = anomaly
        self._refresh_counts()
        self._render_cards()

    def remove_anomaly(self, alert_id: str):
        self._anomalies.pop(alert_id, None)
        self._refresh_counts()
        self._render_cards()

    def clear(self):
        self._anomalies.clear()
        self._refresh_counts()
        self._render_cards()

    def set_reader_mode(self, mode: str):
        self.health_card.update_status(mode, self._decoded_count)

    def apply_theme(self, theme_name: str):
        p = get_theme_palette(theme_name)
        self.title.setStyleSheet(
            f"color: {p['viewer_title']}; font-family: '{FONT_FAMILY_MONO}'; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; letter-spacing: 1px;"
        )
        self.summary.setStyleSheet(
            f"color: {p['viewer_stats']}; font-family: '{FONT_FAMILY_MONO}'; font-size: {FONT_SIZE_MICRO}px; font-weight: 700;"
        )
        self.health_card.apply_theme(theme_name)

    def _refresh_counts(self):
        self._counts = {"critical": 0, "warning": 0, "info": 0}
        for anomaly in self._anomalies.values():
            severity = anomaly.severity if anomaly.severity in self._counts else "info"
            self._counts[severity] += 1
        self.summary.setText(
            f"Critical: {self._counts['critical']} | Warning: {self._counts['warning']} | Info: {self._counts['info']}"
        )

    def _render_cards(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        anomalies: List[Anomaly] = sorted(self._anomalies.values(), key=lambda item: item.timestamp, reverse=True)[:8]
        if not anomalies:
            empty = QLabel("No active anomalies.")
            empty.setObjectName("MutedLabel")
            self.cards_layout.addWidget(empty)
            return

        for anomaly in anomalies:
            self.cards_layout.addWidget(DashboardAlertCard(anomaly))
        self.cards_layout.addStretch()
