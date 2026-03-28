from __future__ import annotations

from collections import Counter, defaultdict, deque
from statistics import mean, pstdev
from typing import Deque, Dict, List, Optional, Tuple

from PyQt5.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from core.anomaly import Anomaly
from core.decoder import DecodedSignal
from core.session_data import SessionDataManager
from .components import HAS_PYQTGRAPH, SignalHoverPlot
from .theme import CARD_MARGIN, COMPACT_SPACING, PAGE_MARGIN, SECTION_SPACING, THEME_DARK, get_theme_palette


class AnalyticsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AnalyticsPage")
        self._theme_name = THEME_DARK
        self._session_data: Optional[SessionDataManager] = None
        self._bus_load: Deque[float] = deque([0.0] * 60, maxlen=60)
        self._latency: Deque[float] = deque([0.0] * 60, maxlen=60)
        self._error_trend: Deque[float] = deque([0.0] * 60, maxlen=60)
        self._last_timestamp_by_id: Dict[int, float] = {}
        self._build_ui()
        self.apply_theme(self._theme_name)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        root.setSpacing(SECTION_SPACING)

        top = QHBoxLayout()
        title = QLabel("SESSION ANALYTICS")
        title.setObjectName("SectionTitle")
        top.addWidget(title)
        top.addStretch()
        self.range_combo = QComboBox()
        self.range_combo.addItems(["Last 30 seconds", "5 minutes", "Entire session"])
        self.range_combo.currentIndexChanged.connect(self.refresh_from_session)
        top.addWidget(self.range_combo)
        root.addLayout(top)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(COMPACT_SPACING * 2)
        metrics.setVerticalSpacing(COMPACT_SPACING * 2)
        self.metric_values = {}
        metric_titles = [
            "TOTAL MESSAGES",
            "BUS UTILIZATION",
            "ERROR FRAMES",
            "PEAK BITRATE",
            "ACTIVE SIGNALS",
            "ACTIVE ANOMALIES",
            "AVERAGE LATENCY",
            "MOST FREQUENT CAN ID",
        ]
        for index, title_text in enumerate(metric_titles):
            frame = QFrame()
            frame.setObjectName("metricCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
            label = QLabel(title_text)
            label.setObjectName("SectionTitle")
            value = QLabel("0")
            value.setObjectName("MonoValue")
            layout.addWidget(label)
            layout.addWidget(value)
            metrics.addWidget(frame, index // 4, index % 4)
            self.metric_values[title_text] = value
        root.addLayout(metrics)

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(COMPACT_SPACING * 2)
        self.bus_chart = self._make_chart_card("BUS LOAD")
        self.latency_chart = self._make_chart_card("LATENCY")
        self.error_chart = self._make_chart_card("ERROR FRAMES")
        charts_layout.addWidget(self.bus_chart)
        charts_layout.addWidget(self.latency_chart)
        charts_layout.addWidget(self.error_chart)
        root.addLayout(charts_layout)

        lower = QHBoxLayout()
        lower.setSpacing(COMPACT_SPACING * 2)
        self.noisy_ids = self._make_table_card("TOP NOISY CAN IDS", ["CAN ID", "Count"])
        self.unstable_signals = self._make_table_card("MOST UNSTABLE SIGNALS", ["Signal", "Variance"])
        lower.addWidget(self.noisy_ids)
        lower.addWidget(self.unstable_signals)
        root.addLayout(lower)

        insights_panel = QWidget()
        insights_layout = QVBoxLayout(insights_panel)
        insights_layout.setContentsMargins(0, 0, 0, 0)
        insights_layout.setSpacing(8)
        insights_head = QLabel("INSIGHTS PANEL")
        insights_head.setObjectName("SectionTitle")
        self.insights = QTextEdit()
        self.insights.setReadOnly(True)
        self.insights.setFixedHeight(140)
        insights_layout.addWidget(insights_head)
        insights_layout.addWidget(self.insights)
        root.addWidget(insights_panel)

    def _make_chart_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        plot = SignalHoverPlot() if HAS_PYQTGRAPH else QLabel("pyqtgraph not installed")
        if isinstance(plot, QLabel):
            plot.setMinimumHeight(180)
        else:
            plot.setMinimumHeight(180)
        card._plot = plot  # type: ignore[attr-defined]
        layout.addWidget(label)
        layout.addWidget(plot)
        return card

    def _make_table_card(self, title: str, headers: list[str]) -> QFrame:
        card = QFrame()
        card.setObjectName("SurfaceCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 300)
        card._table = table  # type: ignore[attr-defined]
        layout.addWidget(label)
        layout.addWidget(table)
        return card

    def set_session_data(self, session_data: SessionDataManager):
        self._session_data = session_data

    def add_signal(self, signal: DecodedSignal):
        previous_ts = self._last_timestamp_by_id.get(signal.can_id, signal.timestamp)
        latency_ms = max(0.0, (signal.timestamp - previous_ts) * 1000.0)
        self._last_timestamp_by_id[signal.can_id] = signal.timestamp
        signals = self._session_data.get_all_signals() if self._session_data else []
        elapsed = max((signals[-1].timestamp - signals[0].timestamp), 0.001) if len(signals) > 1 else 1.0
        utilization = min(100.0, (len(signals) / elapsed) * 1.8)
        error_frames = sum(1 for item in signals if item.severity == "critical")
        self._bus_load.append(utilization)
        self._latency.append(latency_ms)
        self._error_trend.append(float(error_frames))
        self.refresh_from_session()

    def add_anomaly(self, anomaly: Anomaly):
        if anomaly:
            self.refresh_from_session()

    def refresh_from_session(self, *_args):
        signals = self._session_data.get_all_signals() if self._session_data else []
        anomalies = self._session_data.get_active_anomalies() if self._session_data else []
        latest = self._session_data.get_latest_values() if self._session_data else {}

        id_counts = Counter(signal.can_id for signal in signals)
        self.metric_values["TOTAL MESSAGES"].setText(f"{len(signals):,}")
        self.metric_values["BUS UTILIZATION"].setText(f"{(self._bus_load[-1] if self._bus_load else 0.0):.1f}%")
        self.metric_values["ERROR FRAMES"].setText(str(sum(1 for signal in signals if signal.severity == "critical")))
        self.metric_values["PEAK BITRATE"].setText(f"{max((signal.can_id & 0x7FF) for signal in signals) if signals else 0:.1f} kbps")
        self.metric_values["ACTIVE SIGNALS"].setText(str(len(latest)))
        self.metric_values["ACTIVE ANOMALIES"].setText(str(len(anomalies)))
        self.metric_values["AVERAGE LATENCY"].setText(f"{(mean(self._latency) if self._latency else 0.0):.1f} ms")
        self.metric_values["MOST FREQUENT CAN ID"].setText(f"0x{id_counts.most_common(1)[0][0]:X}" if id_counts else "n/a")

        self._refresh_chart(self.bus_chart, "Bus Load", list(self._bus_load), "%")
        self._refresh_chart(self.latency_chart, "Latency", list(self._latency), "ms")
        self._refresh_chart(self.error_chart, "Error Frames", list(self._error_trend), "count")
        self._fill_top_ids(signals)
        self._fill_unstable(signals)
        self._refresh_insights(signals, anomalies)

    def apply_theme(self, theme_name: str):
        self._theme_name = theme_name
        p = get_theme_palette(theme_name)
        self.insights.setStyleSheet(
            f"QTextEdit {{ background: {p['card_bg']}; border: 1px solid {p.get('strong_border', p['card_border'])}; border-radius: 12px; padding: 10px 12px; font-size: 12px; }}"
        )
        for card in (self.bus_chart, self.latency_chart, self.error_chart):
            plot = card._plot  # type: ignore[attr-defined]
            if hasattr(plot, "apply_theme"):
                plot.apply_theme(p)
        self.refresh_from_session()

    def _refresh_chart(self, card: QFrame, name: str, values: List[float], unit: str):
        plot = card._plot  # type: ignore[attr-defined]
        if not hasattr(plot, "plot_signals"):
            return
        base_ts = list(range(len(values)))
        series = {name: [(float(index), value) for index, value in enumerate(values)]}
        units = {name: unit}
        p = get_theme_palette(self._theme_name)
        plot.plot_signals(series, units, [p["accent_cyan"] if name == "Bus Load" else p["accent_primary"] if name == "Latency" else p["warning_fg"]])

    def _fill_top_ids(self, signals: List[DecodedSignal]):
        counts = Counter(signal.can_id for signal in signals).most_common(6)
        table = self.noisy_ids._table  # type: ignore[attr-defined]
        table.setRowCount(len(counts))
        for row, (can_id, count) in enumerate(counts):
            table.setItem(row, 0, QTableWidgetItem(f"0x{can_id:X}"))
            table.setItem(row, 1, QTableWidgetItem(str(count)))

    def _fill_unstable(self, signals: List[DecodedSignal]):
        by_signal: Dict[str, List[float]] = defaultdict(list)
        for signal in signals:
            by_signal[signal.signal_name].append(signal.value)
        rows: List[Tuple[str, float]] = []
        for name, values in by_signal.items():
            if len(values) > 1:
                rows.append((name, pstdev(values)))
        rows.sort(key=lambda item: item[1], reverse=True)
        table = self.unstable_signals._table  # type: ignore[attr-defined]
        table.setRowCount(min(6, len(rows)))
        for row, (name, variance) in enumerate(rows[:6]):
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(f"{variance:.2f}"))

    def _refresh_insights(self, signals: List[DecodedSignal], anomalies: List[Anomaly]):
        if not signals:
            self.insights.setPlainText("No session data yet.")
            return
        id_counts = Counter(signal.can_id for signal in signals)
        most_id, count = id_counts.most_common(1)[0]
        lines = [
            f"CAN ID 0x{most_id:X} produced {count} messages in the current session.",
            f"{len(anomalies)} active anomalies are currently tracked.",
            f"Average latency is {(mean(self._latency) if self._latency else 0.0):.1f} ms.",
        ]
        warning_counts = Counter(anomaly.related_can_id for anomaly in anomalies if anomaly.severity == "warning")
        if warning_counts:
            warn_id, warn_count = warning_counts.most_common(1)[0]
            lines.append(f"CAN ID 0x{warn_id:X} generated {warn_count} active warnings.")
        self.insights.setPlainText("\n".join(lines))
