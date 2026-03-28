from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.decoder import DecodedSignal
from core.session_data import SessionDataManager
from .components import HAS_PYQTGRAPH, SignalHoverPlot
from .theme import FONT_FAMILY_MONO, FONT_SIZE_CAPTION, FONT_SIZE_MICRO, THEME_DARK, VISUALIZATION_COMBO_WIDTH, VISUALIZATION_MIN_HEIGHT, get_theme_palette


class VisualizationWidget(QWidget):
    clear_session_requested = pyqtSignal()
    MAX_POINTS = 100
    HISTORY_ROWS = 20
    DEFAULT_SIGNALS = ["Battery Voltage", "Motor Temperature", "Engine RPM"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_name = THEME_DARK
        self._session_manager: Optional[SessionDataManager] = None
        self._build_ui()
        self.apply_theme(self._theme_name)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(8, 2, 8, 2)
        header_row.setSpacing(10)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        self.title = QLabel("SIGNAL_TREND")
        self.title.setObjectName("SectionTitle")
        self.status_lbl = QLabel("LIVE TELEMETRY STREAM")
        self.status_lbl.setObjectName("MutedLabel")
        title_layout.addWidget(self.title)
        title_layout.addWidget(self.status_lbl)
        header_row.addLayout(title_layout)
        header_row.addStretch()

        self.signal_combo = QComboBox()
        self.signal_combo.addItems(["Default signals"])
        self.signal_combo.setFixedHeight(34)
        self.signal_combo.setFixedWidth(max(180, VISUALIZATION_COMBO_WIDTH + 24))
        self.signal_combo.currentIndexChanged.connect(self._refresh_views)
        header_row.addWidget(self.signal_combo, 0, Qt.AlignVCenter)

        self.keep_session = QCheckBox("Keep Session")
        self.clear_button = QPushButton("Clear Session")
        self.clear_button.setObjectName("GhostButton")
        self.clear_button.clicked.connect(self.clear_session_requested.emit)
        header_row.addWidget(self.keep_session, 0, Qt.AlignVCenter)
        header_row.addWidget(self.clear_button, 0, Qt.AlignVCenter)
        root.addLayout(header_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(10)

        graph_panel = QFrame()
        graph_panel.setObjectName("SurfaceCard")
        graph_layout = QVBoxLayout(graph_panel)
        graph_layout.setContentsMargins(12, 10, 12, 10)
        graph_layout.setSpacing(8)

        self.graph = SignalHoverPlot() if HAS_PYQTGRAPH else None
        if self.graph is not None:
            self.graph.setMinimumHeight(VISUALIZATION_MIN_HEIGHT)
            graph_layout.addWidget(self.graph)
        else:
            fallback = QLabel("Install 'pyqtgraph' to enable data visualization")
            fallback.setAlignment(Qt.AlignCenter)
            graph_layout.addWidget(fallback)

        history_panel = QFrame()
        history_panel.setObjectName("SurfaceCard")
        history_panel.setFixedWidth(250)
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(12, 10, 12, 10)
        history_layout.setSpacing(8)

        history_title = QLabel("RECENT HISTORY")
        history_title.setObjectName("SectionTitle")
        self.history_table = QTableWidget(0, 2)
        self.history_table.setHorizontalHeaderLabels(["Timestamp", "Value"])
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setShowGrid(False)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.history_table.setMinimumHeight(VISUALIZATION_MIN_HEIGHT)

        history_layout.addWidget(history_title)
        history_layout.addWidget(self.history_table)

        content_row.addWidget(graph_panel, 1)
        content_row.addWidget(history_panel, 0)
        root.addLayout(content_row)

    def set_session_manager(self, session_manager: SessionDataManager):
        self._session_manager = session_manager
        self._sync_signal_selector()
        self._refresh_views()

    def keep_session_enabled(self) -> bool:
        return self.keep_session.isChecked()

    def clear(self):
        self._sync_signal_selector()
        self._refresh_views()

    def add_signal(self, signal: DecodedSignal):
        self._sync_signal_selector()
        selected = self.signal_combo.currentText()
        if selected == "Default signals" or selected == signal.signal_name:
            self._refresh_views()

    def apply_theme(self, theme_name: str):
        self._theme_name = theme_name
        p = get_theme_palette(theme_name)
        self.status_lbl.setStyleSheet(
            f"color: {p['muted_label']}; font-family: '{FONT_FAMILY_MONO}'; font-size: {FONT_SIZE_MICRO}px; font-weight: 700;"
        )
        self.signal_combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {p['card_bg']};
                color: {p['viz_combo_fg']};
                border: 1px solid {p['viz_combo_border']};
                border-radius: 10px;
                padding: 4px 28px 4px 10px;
                font-size: 12px;
            }}
            QComboBox:hover {{
                background: {p['viz_combo_hover_bg']};
                border-color: {p['viz_combo_hover_border']};
            }}
            """
        )
        self.keep_session.setStyleSheet(f"color: {p['window_fg']}; font-size: 12px;")
        self.history_table.setStyleSheet(
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
                border-bottom: 1px solid {p['viewer_header_border']};
                padding: 6px;
                font-size: {FONT_SIZE_CAPTION}px;
                font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;
            }}
            """
        )
        if self.graph is not None:
            self.graph.apply_theme(p)
        self._refresh_views()

    def _sync_signal_selector(self):
        current = self.signal_combo.currentText()
        names = self._session_manager.get_signal_names() if self._session_manager else []
        options = ["Default signals"] + names
        self.signal_combo.blockSignals(True)
        self.signal_combo.clear()
        self.signal_combo.addItems(options)
        index = self.signal_combo.findText(current)
        self.signal_combo.setCurrentIndex(index if index >= 0 else 0)
        self.signal_combo.blockSignals(False)

    def _selected_signals(self) -> List[str]:
        selected = self.signal_combo.currentText()
        if selected == "Default signals":
            return [name for name in self.DEFAULT_SIGNALS if self._session_manager and self._session_manager.get_signal_history(name)]
        return [selected]

    def _refresh_views(self):
        self._redraw_plot()
        self._refresh_history_table()

    def _redraw_plot(self):
        if self.graph is None or not self._session_manager:
            return
        p = get_theme_palette(self._theme_name)
        colors = [p["viz_leg1"], p["viz_leg2"], p["accent_primary"]]
        series: Dict[str, List[Tuple[float, float]]] = {}
        units: Dict[str, str] = {}
        for signal_name in self._selected_signals():
            history = self._session_manager.get_signal_history(signal_name)[-self.MAX_POINTS :]
            if not history:
                continue
            series[signal_name] = [(item.timestamp, item.value) for item in history]
            units[signal_name] = history[-1].unit
        self.graph.plot_signals(series, units, colors)

    def _refresh_history_table(self):
        if not self._session_manager:
            self.history_table.setRowCount(0)
            return

        selected = self.signal_combo.currentText()
        signal_name = self.DEFAULT_SIGNALS[0] if selected == "Default signals" else selected
        history = list(reversed(self._session_manager.get_signal_history(signal_name)[-self.HISTORY_ROWS :]))
        self.history_table.setRowCount(len(history))
        for row, item in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(f"{item.timestamp:.3f}"))
            self.history_table.setItem(row, 1, QTableWidgetItem(f"{item.value:.2f} {item.unit}"))
