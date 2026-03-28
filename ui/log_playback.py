from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.decoder import DecodedSignal
from core.session_data import SessionDataManager
from .components import HAS_PYQTGRAPH, SignalHoverPlot
from .theme import FONT_FAMILY_MONO, PLAYBACK_CAPTION, PLAYBACK_SMALL, THEME_DARK, get_theme_palette


class TelemetryMiniCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SurfaceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        self.title = QLabel(title.upper())
        self.title.setObjectName("SectionTitle")
        self.value = QLabel("--")
        self.value.setObjectName("MonoValue")
        self.sub = QLabel("Waiting for playback")
        self.sub.setObjectName("MutedLabel")
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.sub)

    def update_value(self, signal: Optional[DecodedSignal]):
        if signal is None:
            self.value.setText("--")
            self.sub.setText("Waiting for playback")
            return
        self.value.setText(f"{signal.value:.2f} {signal.unit}")
        self.sub.setText(f"0x{signal.can_id:X} | {signal.severity.upper()}")


class LogPlaybackWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogPlaybackPage")
        self._theme_name = THEME_DARK
        self._session_manager: Optional[SessionDataManager] = None
        self._signals: List[DecodedSignal] = []
        self._filtered: List[DecodedSignal] = []
        self._index = 0
        self._playing = False
        self._speed = 1.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._build_ui()
        self.apply_theme(self._theme_name)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 12, 18, 14)
        root.setSpacing(10)

        filters = QFrame()
        filters.setObjectName("SurfaceCard")
        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(8)

        self.filter_id = QLineEdit()
        self.filter_id.setPlaceholderText("CAN ID")
        self.filter_signal = QLineEdit()
        self.filter_signal.setPlaceholderText("Signal")
        self.filter_severity = QComboBox()
        self.filter_severity.addItems(["All severities", "normal", "warning", "critical"])
        self.filter_anomaly = QCheckBox("Anomaly only")
        self.export_format = QComboBox()
        self.export_format.addItems(["JSON", "CSV"])
        self.save_btn = QPushButton("Export")
        self.save_btn.setObjectName("GhostButton")
        self.save_btn.clicked.connect(self._export_filtered)

        for widget in (self.filter_id, self.filter_signal):
            widget.setFixedHeight(34)
        for widget in (self.filter_severity, self.export_format):
            widget.setFixedHeight(34)

        filters_layout.addWidget(self.filter_id)
        filters_layout.addWidget(self.filter_signal)
        filters_layout.addWidget(self.filter_severity)
        filters_layout.addWidget(self.filter_anomaly)
        filters_layout.addWidget(self.export_format)
        filters_layout.addWidget(self.save_btn)
        root.addWidget(filters)

        middle = QHBoxLayout()
        middle.setSpacing(10)

        chart_card = QFrame()
        chart_card.setObjectName("SurfaceCard")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 10, 12, 10)
        chart_layout.setSpacing(8)

        chart_head = QHBoxLayout()
        self.status_label = QLabel("PLAYBACK_IDLE")
        self.legend = QLabel("BATTERY / TEMPERATURE / RPM")
        chart_head.addWidget(self.status_label)
        chart_head.addStretch()
        chart_head.addWidget(self.legend)
        chart_layout.addLayout(chart_head)

        self.plot_widget = SignalHoverPlot() if HAS_PYQTGRAPH else None
        if self.plot_widget is not None:
            self.plot_widget.setMinimumHeight(300)
            chart_layout.addWidget(self.plot_widget, 1)
        else:
            chart_layout.addWidget(QLabel("pyqtgraph not installed"))

        self.metric_label = QLabel("No playback data loaded.")
        self.metric_label.setObjectName("MutedLabel")
        chart_layout.addWidget(self.metric_label)

        side = QVBoxLayout()
        side.setSpacing(10)
        self.telemetry_cards = {
            "Battery Voltage": TelemetryMiniCard("Battery Voltage"),
            "Motor Temperature": TelemetryMiniCard("Motor Temperature"),
            "Engine RPM": TelemetryMiniCard("Engine RPM"),
            "State of Charge": TelemetryMiniCard("State of Charge"),
        }
        for card in self.telemetry_cards.values():
            side.addWidget(card)
        side.addStretch()

        middle.addWidget(chart_card, 5)
        middle.addLayout(side, 2)
        root.addLayout(middle, 1)

        viewer_card = QFrame()
        viewer_card.setObjectName("SurfaceCard")
        viewer_layout = QVBoxLayout(viewer_card)
        viewer_layout.setContentsMargins(12, 10, 12, 10)
        viewer_layout.setSpacing(8)
        table_title = QLabel("STREAM VIEWER")
        table_title.setObjectName("SectionTitle")
        self.frames_table = QTableWidget(0, 5)
        self.frames_table.setHorizontalHeaderLabels(["Timestamp", "CAN ID", "Signal", "Value", "Severity"])
        self.frames_table.verticalHeader().setVisible(False)
        self.frames_table.horizontalHeader().setStretchLastSection(True)
        self.frames_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.frames_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.frames_table.setColumnWidth(2, 300)
        self.frames_table.setMinimumHeight(220)
        viewer_layout.addWidget(table_title)
        viewer_layout.addWidget(self.frames_table)
        root.addWidget(viewer_card)

        controls = QFrame()
        controls.setObjectName("SurfaceCard")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(8)

        self.btn_back = QPushButton("<")
        self.btn_play = QPushButton("Play")
        self.btn_fwd = QPushButton(">")
        for btn in (self.btn_back, self.btn_play, self.btn_fwd):
            btn.setObjectName("GhostButton")
            btn.setFixedHeight(32)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self._set_index)
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1x", "2x", "4x"])
        self.speed_combo.setCurrentText("1x")
        self.speed_combo.setFixedHeight(32)
        self.speed_combo.currentTextChanged.connect(self._set_speed)
        self.time_current = QLabel("00:00:00.000")

        self.btn_back.clicked.connect(lambda: self._step(-1))
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_fwd.clicked.connect(lambda: self._step(1))

        controls_layout.addWidget(self.btn_back)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_fwd)
        controls_layout.addWidget(self.slider, 1)
        controls_layout.addWidget(self.speed_combo)
        controls_layout.addWidget(self.time_current)
        root.addWidget(controls)

        self.filter_id.textChanged.connect(self.refresh_from_session)
        self.filter_signal.textChanged.connect(self.refresh_from_session)
        self.filter_severity.currentTextChanged.connect(self.refresh_from_session)
        self.filter_anomaly.toggled.connect(self.refresh_from_session)

    def set_session_manager(self, session_manager: SessionDataManager):
        self._session_manager = session_manager
        self.refresh_from_session()

    def refresh_from_session(self, *_args):
        self._signals = self._session_manager.get_all_signals() if self._session_manager else []
        self._filtered = [signal for signal in self._signals if self._matches(signal)]
        self.slider.blockSignals(True)
        self.slider.setRange(0, max(0, len(self._filtered) - 1))
        self.slider.setValue(min(self._index, max(0, len(self._filtered) - 1)))
        self.slider.blockSignals(False)
        self._index = min(self._index, max(0, len(self._filtered) - 1))
        self._render_state()

    def apply_theme(self, theme_name: str):
        self._theme_name = theme_name
        p = get_theme_palette(theme_name)
        self.status_label.setStyleSheet(
            f"color: {p['window_fg']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: 12px; font-weight: 800;"
        )
        self.legend.setStyleSheet(
            f"color: {p['viewer_stats']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {PLAYBACK_CAPTION - 2}px;"
        )
        self.time_current.setStyleSheet(
            f"color: {p['viewer_stats']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {PLAYBACK_CAPTION - 2}px;"
        )
        self.frames_table.setStyleSheet(
            f"""
            QTableWidget {{
                background: transparent;
                border: none;
                color: {p['viewer_table_fg']};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: {p['viewer_table_header_bg']};
                color: {p['viewer_table_header_fg']};
                border: none;
                padding: 6px;
                font-size: {PLAYBACK_CAPTION - 2}px;
            }}
            """
        )
        if self.plot_widget is not None:
            self.plot_widget.apply_theme(p)
        self._render_state()

    def _matches(self, signal: DecodedSignal) -> bool:
        id_filter = self.filter_id.text().strip().lower()
        signal_filter = self.filter_signal.text().strip().lower()
        severity_filter = self.filter_severity.currentText()
        if id_filter and id_filter not in f"0x{signal.can_id:X}".lower():
            return False
        if signal_filter and signal_filter not in signal.signal_name.lower():
            return False
        if severity_filter != "All severities" and signal.severity != severity_filter:
            return False
        if self.filter_anomaly.isChecked() and signal.severity == "normal":
            return False
        return True

    def _toggle_play(self):
        self._playing = not self._playing
        self.btn_play.setText("Pause" if self._playing else "Play")
        if self._playing:
            self._timer.start(max(40, int(180 / self._speed)))
        else:
            self._timer.stop()

    def _advance(self):
        if self._index >= len(self._filtered) - 1:
            self._playing = False
            self._timer.stop()
            self.btn_play.setText("Play")
            return
        self._index += 1
        self.slider.blockSignals(True)
        self.slider.setValue(self._index)
        self.slider.blockSignals(False)
        self._render_state()

    def _step(self, delta: int):
        self._index = max(0, min(self._index + delta, max(0, len(self._filtered) - 1)))
        self.slider.blockSignals(True)
        self.slider.setValue(self._index)
        self.slider.blockSignals(False)
        self._render_state()

    def _set_index(self, value: int):
        self._index = value
        self._render_state()

    def _set_speed(self, text: str):
        self._speed = float(text.replace("x", ""))
        if self._playing:
            self._timer.start(max(40, int(180 / self._speed)))

    def _render_state(self):
        visible = self._filtered[: self._index + 1]
        self.status_label.setText("PLAYBACK_RUNNING" if self._playing else "PLAYBACK_PAUSED")
        latest = visible[-1] if visible else None
        if latest:
            self.metric_label.setText(f"{latest.signal_name}: {latest.value:.2f} {latest.unit} | {latest.severity.upper()}")
            self.time_current.setText(self._format_timestamp(latest.timestamp))
        else:
            self.metric_label.setText("No playback data loaded.")
            self.time_current.setText("00:00:00.000")

        self._render_table(visible)
        self._render_chart(visible)
        self._render_telemetry(visible)

    def _render_table(self, visible: List[DecodedSignal]):
        rows = list(reversed(visible[-120:]))
        self.frames_table.setRowCount(len(rows))
        for row_index, signal in enumerate(rows):
            values = [
                f"{signal.timestamp:.3f}",
                f"0x{signal.can_id:X}",
                signal.signal_name,
                f"{signal.value:.2f} {signal.unit}",
                signal.severity.upper(),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(int(Qt.AlignVCenter | (Qt.AlignLeft if col == 2 else Qt.AlignCenter)))
                self.frames_table.setItem(row_index, col, item)

    def _render_chart(self, visible: List[DecodedSignal]):
        if self.plot_widget is None:
            return
        p = get_theme_palette(self._theme_name)
        by_name: Dict[str, List[Tuple[float, float]]] = {}
        units: Dict[str, str] = {}
        for signal in visible[-100:]:
            by_name.setdefault(signal.signal_name, []).append((signal.timestamp, signal.value))
            units[signal.signal_name] = signal.unit
        ordered = dict(list(by_name.items())[:3])
        self.plot_widget.plot_signals(ordered, units, [p["health_cpu"], p["health_mem"], p["accent_primary"]])

    def _render_telemetry(self, visible: List[DecodedSignal]):
        latest_by_signal: Dict[str, DecodedSignal] = {}
        for signal in visible:
            latest_by_signal[signal.signal_name] = signal
        for signal_name, card in self.telemetry_cards.items():
            card.update_value(latest_by_signal.get(signal_name))

    def _format_timestamp(self, timestamp: float) -> str:
        seconds = int(timestamp)
        millis = int((timestamp - seconds) * 1000)
        hours = (seconds // 3600) % 24
        minutes = (seconds // 60) % 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def _export_filtered(self):
        if not self._filtered:
            return
        suffix = "json" if self.export_format.currentText() == "JSON" else "csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export Playback Data", f"playback_export.{suffix}", f"*.{suffix}")
        if not path:
            return
        if suffix == "json":
            payload = [
                {
                    "timestamp": signal.timestamp,
                    "stream_id": signal.stream_id,
                    "can_id": f"0x{signal.can_id:X}",
                    "signal_name": signal.signal_name,
                    "value": signal.value,
                    "unit": signal.unit,
                    "severity": signal.severity,
                }
                for signal in self._filtered
            ]
            Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        else:
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["timestamp", "stream_id", "can_id", "signal_name", "value", "unit", "severity"])
                for signal in self._filtered:
                    writer.writerow([signal.timestamp, signal.stream_id, f"0x{signal.can_id:X}", signal.signal_name, signal.value, signal.unit, signal.severity])
