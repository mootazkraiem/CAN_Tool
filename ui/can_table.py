from __future__ import annotations

from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.decoder import DecodedSignal
from .theme import FONT_FAMILY_MONO, FONT_SIZE_CAPTION, FONT_SIZE_SMALL, THEME_DARK, get_theme_palette


class CanTableWidget(QWidget):
    MAX_ROWS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_name = THEME_DARK
        self._signals: List[DecodedSignal] = []
        self._build_ui()
        self.apply_theme(self._theme_name)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        self.filter_bar = QFrame()
        self.filter_bar.setObjectName("SurfaceCardAlt")
        filter_layout = QHBoxLayout(self.filter_bar)
        filter_layout.setContentsMargins(14, 10, 14, 10)
        filter_layout.setSpacing(10)

        self.filter_id = QLineEdit()
        self.filter_id.setPlaceholderText("Filter CAN ID")
        self.filter_signal = QLineEdit()
        self.filter_signal.setPlaceholderText("Filter signal name")
        self.filter_severity = QComboBox()
        self.filter_severity.addItems(["All severities", "normal", "warning", "critical"])

        filter_layout.addWidget(self.filter_id, 1)
        filter_layout.addWidget(self.filter_signal, 1)
        filter_layout.addWidget(self.filter_severity)

        viewer_card = QFrame()
        viewer_card.setObjectName("SurfaceCard")
        viewer_layout = QVBoxLayout(viewer_card)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)

        self.header = QFrame()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        self.title = QLabel("CAN_FRAME_VIEWER")
        self.stats = QLabel("Signals: 0  |  Filters: none")
        header_layout.addWidget(self.title)
        header_layout.addStretch()
        header_layout.addWidget(self.stats)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Timestamp", "CAN ID", "Signal", "Value", "Unit", "Severity"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setMinimumHeight(380)
        self.table.setColumnWidth(2, 300)

        viewer_layout.addWidget(self.header)
        viewer_layout.addWidget(self.table)
        root.addWidget(self.filter_bar)
        root.addWidget(viewer_card, 1)

        self.filter_id.textChanged.connect(self._refresh_table)
        self.filter_signal.textChanged.connect(self._refresh_table)
        self.filter_severity.currentTextChanged.connect(self._refresh_table)

    def clear(self):
        self._signals.clear()
        self._refresh_table()

    def add_signal(self, signal: DecodedSignal):
        self._signals.append(signal)
        if len(self._signals) > self.MAX_ROWS:
            self._signals = self._signals[-self.MAX_ROWS :]
        self._refresh_table()

    def apply_theme(self, theme_name: str):
        self._theme_name = theme_name
        p = get_theme_palette(theme_name)

        self.filter_bar.setStyleSheet(
            f"background: {p['card_bg']}; border: 1px solid {p['card_border']}; border-radius: 12px;"
        )
        self.header.setStyleSheet(
            f"QFrame {{ background: {p['viewer_header_bg']}; border-top-left-radius: 12px; border-top-right-radius: 12px; border-bottom: 1px solid {p['viewer_header_border']}; }}"
        )
        self.title.setStyleSheet(
            f"color: {p['viewer_title']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; letter-spacing: 1px;"
        )
        self.stats.setStyleSheet(
            f"color: {p['viewer_stats']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; font-weight: 700;"
        )
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {p['viewer_table_bg']};
                border: none;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                color: {p['viewer_table_fg']};
                font-size: {FONT_SIZE_SMALL}px;
                selection-background-color: {p['viewer_table_selection_bg']};
                selection-color: {p['viewer_table_selection_fg']};
            }}
            QHeaderView::section {{
                background: {p['viewer_table_header_bg']};
                color: {p['viewer_table_header_fg']};
                border: none;
                border-bottom: 1px solid {p['viewer_header_border']};
                padding: 10px 12px;
                font-size: {FONT_SIZE_CAPTION}px;
                font-weight: 800;
                letter-spacing: 1px;
                font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;
            }}
            QTableWidget::item {{
                border: none;
                border-bottom: 1px solid {p['viewer_table_item_border']};
                padding: 8px 10px;
            }}
            """
        )
        self._refresh_table()

    def _refresh_table(self):
        p = get_theme_palette(self._theme_name)
        id_filter = self.filter_id.text().strip().lower()
        signal_filter = self.filter_signal.text().strip().lower()
        severity_filter = self.filter_severity.currentText()
        scrollbar = self.table.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()

        filtered = [signal for signal in self._signals if self._matches(signal, id_filter, signal_filter, severity_filter)]
        filtered.reverse()
        self.table.setRowCount(len(filtered))

        severity_colors = {
            "normal": p["normal_value"],
            "warning": p["warning_fg"],
            "critical": p["critical_fg"],
        }
        mono_font = QFont(FONT_FAMILY_MONO, max(10, FONT_SIZE_SMALL - 4))

        for row, signal in enumerate(filtered):
            values = [
                (f"{signal.timestamp:.3f}", p["viewer_stats"], Qt.AlignVCenter | Qt.AlignLeft, True),
                (f"0x{signal.can_id:X}", p["normal_id"], Qt.AlignCenter, True),
                (signal.signal_name, p["viewer_table_fg"], Qt.AlignVCenter | Qt.AlignLeft, False),
                (f"{signal.value:.2f}", severity_colors.get(signal.severity, p["viewer_table_fg"]), Qt.AlignRight | Qt.AlignVCenter, True),
                (signal.unit, p["viewer_stats"], Qt.AlignLeft | Qt.AlignVCenter, False),
                (signal.severity.upper(), severity_colors.get(signal.severity, p["viewer_table_fg"]), Qt.AlignCenter, True),
            ]
            for col, (text, color, align, mono) in enumerate(values):
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                item.setTextAlignment(int(align))
                if mono:
                    item.setFont(mono_font)
                self.table.setItem(row, col, item)

        active_filters = []
        if id_filter:
            active_filters.append(f"id={id_filter}")
        if signal_filter:
            active_filters.append(f"signal={signal_filter}")
        if severity_filter != "All severities":
            active_filters.append(f"severity={severity_filter}")
        self.stats.setText(f"Signals: {len(self._signals)}  |  Filters: {', '.join(active_filters) if active_filters else 'none'}")

        if was_at_bottom:
            self.table.scrollToBottom()

    def _matches(self, signal: DecodedSignal, id_filter: str, signal_filter: str, severity_filter: str) -> bool:
        if id_filter and id_filter not in f"0x{signal.can_id:X}".lower():
            return False
        if signal_filter and signal_filter not in signal.signal_name.lower():
            return False
        if severity_filter != "All severities" and signal.severity != severity_filter:
            return False
        return True
