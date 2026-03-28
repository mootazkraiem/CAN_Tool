import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .theme import (
    BUTTON_HEIGHT,
    FONT_FAMILY_MONO,
    PLAYBACK_BAR_HEIGHT,
    PLAYBACK_CAPTION,
    PLAYBACK_LARGE,
    PLAYBACK_PLAY_BUTTON,
    PLAYBACK_SMALL,
    PLAYBACK_SMALL_BUTTON,
    PLAYBACK_SPEED_BUTTON_HEIGHT,
    PLAYBACK_TABLE_COL_BUS,
    PLAYBACK_TABLE_COL_ID,
    PLAYBACK_TABLE_COL_LABEL,
    PLAYBACK_TABLE_COL_LEN,
    PLAYBACK_TABLE_COL_PAYLOAD,
    PLAYBACK_TABLE_COL_RAW,
    PLAYBACK_TABLE_COL_TIMESTAMP,
    PLAYBACK_TABLE_ROW_HEIGHT,
    PLAYBACK_XL,
    THEME_DARK,
    get_theme_palette,
)


class PlaybackMetricCard(QFrame):
    def __init__(self, title: str, value: str, unit: str, accent_key: str, parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.title_text = title
        self.value_text = value
        self.unit_text = unit
        self.accent_key = accent_key

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.title_lbl = QLabel(title)
        self.value_lbl = QLabel(value)
        self.unit_lbl = QLabel(unit)
        self.divider = QFrame()
        self.divider.setFixedHeight(3)

        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        value_row.addWidget(self.value_lbl)
        value_row.addWidget(self.unit_lbl)
        value_row.addStretch()

        layout.addWidget(self.title_lbl)
        layout.addLayout(value_row)
        layout.addWidget(self.divider)

    def apply_theme(self, theme_name: str):
        p = get_theme_palette(theme_name)
        accent = p["health_cpu"] if self.accent_key == "cpu" else p["health_mem"]
        self.setStyleSheet(
            f"""
            QFrame#metricCard {{
                background: {p['card_alt_bg']};
                border: 1px solid {p['card_border']};
                border-left: 4px solid {accent};
                border-radius: 16px;
            }}
            """
        )
        self.title_lbl.setStyleSheet(
            f"color: {p['viewer_stats']}; font-size: {PLAYBACK_CAPTION}px; font-weight: 800; letter-spacing: 1px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        self.value_lbl.setStyleSheet(
            f"color: {accent}; font-size: {PLAYBACK_XL}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        self.unit_lbl.setStyleSheet(
            f"color: {p['muted_label']}; font-size: {PLAYBACK_SMALL}px; font-weight: 700; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; padding-top: 10px;"
        )
        self.divider.setStyleSheet(f"background: {accent}; border: none; border-radius: 2px;")


class PlaybackFramesTable(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_name = THEME_DARK

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["TIMESTAMP", "ID (HEX)", "BUS", "LEN", "DATA PAYLOAD (HEX)", "", "LABEL"]
        )
        self.table.setAlternatingRowColors(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.table.setGraphicsEffect(shadow)

        self.table.setColumnWidth(0, PLAYBACK_TABLE_COL_TIMESTAMP)
        self.table.setColumnWidth(1, PLAYBACK_TABLE_COL_ID)
        self.table.setColumnWidth(2, PLAYBACK_TABLE_COL_BUS)
        self.table.setColumnWidth(3, PLAYBACK_TABLE_COL_LEN)
        self.table.setColumnWidth(4, PLAYBACK_TABLE_COL_PAYLOAD)
        self.table.setColumnWidth(5, PLAYBACK_TABLE_COL_RAW)
        self.table.setColumnWidth(6, PLAYBACK_TABLE_COL_LABEL)

        root.addWidget(self.table)
        self.apply_theme(self._theme_name)
        self._populate()

    def _item(self, text: str, color: str = "#C5CCD7", mono: bool = False, align=None):
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        item.setTextAlignment(align or (Qt.AlignLeft | Qt.AlignVCenter))
        item.setFont(QFont(FONT_FAMILY_MONO if mono else "Bahnschrift", PLAYBACK_SMALL))
        return item

    def _populate(self):
        p = get_theme_palette(self._theme_name)
        rows = [
            ("12:45:01.042", "0x1F2", "CAN_1", "8", "00 FF A2 B4 00 00 12 C4", "", "MOTOR_RPM", p["viewer_stats"]),
            ("12:45:01.048", "0x0C4", "CAN_1", "8", "FF 42 00 00 E1 D4 00 80", "", "VOLT_SENSE", p["health_cpu"]),
            ("12:45:01.054", "0x211", "CAN_1", "4", "02 1A FF DD", "", "GEN_STAT", p["muted_label"]),
            ("12:45:01.060", "0x7FF", "CAN_ERR", "1", "EF", "", "BUS_FLOOD_WARN", p["badge_critical_fg"]),
            ("12:45:01.066", "0x1F2", "CAN_1", "8", "00 FF A2 B4 00 00 12 C4", "", "MOTOR_RPM", p["viewer_stats"]),
            ("12:45:01.072", "0x4A4", "CAN_2", "8", "12 44 88 90 80 FF 11 02", "", "HVAC_CTL", p["muted_label"]),
            ("12:45:01.080", "0x1F2", "CAN_1", "8", "00 FF A2 B4 00 00 12 C4", "", "MOTOR_RPM", p["viewer_stats"]),
        ]

        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            ts, frame_id, bus, length, payload, raw, label, label_color = row
            values = [
                self._item(ts, p["viewer_stats"], True),
                self._item(frame_id, p["header_fg"], True),
                self._item(bus, p["muted_label"], True),
                self._item(length, p["viewer_stats"], True, Qt.AlignCenter),
                self._item(payload, p["window_fg"], True),
                self._item(raw, p["muted_label"], True),
                self._item(label, label_color, True),
            ]
            for col, item in enumerate(values):
                self.table.setItem(row_index, col, item)
            self.table.setRowHeight(row_index, PLAYBACK_TABLE_ROW_HEIGHT)

        self.table.selectRow(1)

    def apply_theme(self, theme_name: str):
        self._theme_name = theme_name
        p = get_theme_palette(theme_name)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {p['viewer_table_bg']};
                border: 1px solid {p['card_border']};
                border-radius: 12px;
                color: {p['viewer_table_fg']};
                font-size: {PLAYBACK_SMALL}px;
                selection-background-color: {p['table_selection_bg']};
                selection-color: {p['table_selection_fg']};
            }}
            QHeaderView::section {{
                background: {p['viewer_table_header_bg']};
                color: {p['viewer_table_header_fg']};
                border: none;
                border-bottom: 1px solid {p['viewer_header_border']};
                padding: 10px 12px;
                font-size: {PLAYBACK_CAPTION}px;
                font-weight: 800;
                letter-spacing: 1px;
            }}
            QTableWidget::item {{
                border: none;
                border-bottom: 1px solid {p['viewer_table_item_border']};
                padding: 8px 10px;
            }}
            """
        )
        if self.table.rowCount():
            self._populate()


class LogPlaybackWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogPlaybackPage")
        self._theme_name = THEME_DARK
        self._build_ui()
        self.apply_theme(self._theme_name)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 10, 18, 14)
        root.setSpacing(10)

        self.content = QFrame()
        self.content.setObjectName("PlaybackContent")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(12)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        self.chart_container = QFrame()
        chart_layout = QVBoxLayout(self.chart_container)
        chart_layout.setContentsMargins(14, 12, 14, 12)
        chart_layout.setSpacing(10)

        chart_header = QHBoxLayout()
        chart_header.setSpacing(12)

        self.status_label = QLabel("LIVE_TELEMETRY_STREAM")
        chart_header.addWidget(self.status_label)
        chart_header.addStretch()

        self.legend1 = QLabel("BATT_VOLT")
        self.legend2 = QLabel("MOTOR_TEMP")
        chart_header.addWidget(self.legend1)
        chart_header.addWidget(self.legend2)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("transparent")
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_widget.hideAxis("left")
        self.plot_widget.hideAxis("bottom")
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.getPlotItem().setContentsMargins(4, 4, 4, 4)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.12)

        self._x = np.linspace(0, 100, 220)
        self._y1 = 0.9 * np.sin(self._x / 7.2) + 0.4 * np.cos(self._x / 3.9) + np.linspace(0.1, -0.25, self._x.size)
        self._y2 = 0.7 * np.cos(self._x / 9.5 + 0.9) - 0.35 * np.sin(self._x / 5.8)

        axis_row = QHBoxLayout()
        axis_row.setSpacing(0)
        self.axis_ticks = []
        for index, label in enumerate(["T-00:45:12", "T-00:30:33", "T-00:15:00", "T-00:00:00"]):
            tick = QLabel(label)
            self.axis_ticks.append(tick)
            axis_row.addWidget(tick)
            if index < 3:
                axis_row.addStretch()

        chart_layout.addLayout(chart_header)
        chart_layout.addWidget(self.plot_widget, 1)
        chart_layout.addLayout(axis_row)

        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(12)
        self.max_card = PlaybackMetricCard("MAX_VOLTAGE", "384.2", "V DC", "cpu")
        self.temp_card = PlaybackMetricCard("INVERTER_TEMP", "64.5", "C", "mem")
        cards_layout.addWidget(self.max_card)
        cards_layout.addWidget(self.temp_card)
        cards_layout.addStretch()

        top_layout.addWidget(self.chart_container, 5)
        top_layout.addLayout(cards_layout, 2)

        self.frames_table = PlaybackFramesTable()
        content_layout.addLayout(top_layout, 4)
        content_layout.addWidget(self.frames_table, 5)

        self.playback_bar = self._build_playback_bar()

        root.addWidget(self.content, 1)
        root.addWidget(self.playback_bar)

    def _build_playback_bar(self):
        playback_bar = QFrame()
        playback_bar.setFixedHeight(PLAYBACK_BAR_HEIGHT)

        layout = QHBoxLayout(playback_bar)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.btn_back = QPushButton("<")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setFixedSize(PLAYBACK_SMALL_BUTTON, PLAYBACK_SMALL_BUTTON)

        self.btn_play = QPushButton(">")
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.setFixedSize(PLAYBACK_PLAY_BUTTON, PLAYBACK_PLAY_BUTTON)

        self.btn_fwd = QPushButton(">")
        self.btn_fwd.setCursor(Qt.PointingHandCursor)
        self.btn_fwd.setFixedSize(PLAYBACK_SMALL_BUTTON, PLAYBACK_SMALL_BUTTON)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(46)

        markers = QHBoxLayout()
        markers.setSpacing(0)
        self.marker_dots = []
        for _ in ["a", "b", "c"]:
            dot = QLabel(".")
            self.marker_dots.append(dot)
            markers.addWidget(dot)
            markers.addSpacing(36)

        speed_group = QButtonGroup(playback_bar)
        self.speed_widget = QFrame()
        speed_layout = QHBoxLayout(self.speed_widget)
        speed_layout.setContentsMargins(4, 4, 4, 4)
        speed_layout.setSpacing(4)
        self.speed_buttons = []
        for index, label in enumerate(["1x", "2x"]):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(PLAYBACK_SPEED_BUTTON_HEIGHT)
            if index == 1:
                btn.setChecked(True)
            speed_group.addButton(btn)
            speed_layout.addWidget(btn)
            self.speed_buttons.append(btn)

        self.time_current = QLabel("12:45:01.048")
        self.time_total = QLabel("/ 12:58:33.912")
        self.filters = QLabel("FILTERS_ACTIVE")

        self.save_btn = QPushButton("SAVE")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedHeight(BUTTON_HEIGHT)

        layout.addWidget(self.btn_back)
        layout.addWidget(self.btn_play)
        layout.addWidget(self.btn_fwd)
        layout.addSpacing(4)
        layout.addWidget(self.slider, 1)
        layout.addLayout(markers)
        layout.addWidget(self.speed_widget)
        layout.addSpacing(6)
        layout.addWidget(self.time_current)
        layout.addWidget(self.time_total)
        layout.addStretch()
        layout.addWidget(self.filters)
        layout.addSpacing(8)
        layout.addWidget(self.save_btn)

        return playback_bar

    def apply_theme(self, theme_name: str):
        self._theme_name = theme_name
        p = get_theme_palette(theme_name)

        self.content.setStyleSheet(
            "QFrame#PlaybackContent { background: transparent; border: none; }"
        )
        self.chart_container.setStyleSheet(
            f"QFrame {{ background: {p['card_bg']}; border: 1px solid {p['card_border']}; border-radius: 12px; }}"
        )
        self.status_label.setStyleSheet(
            f"color: {p['window_fg']}; font-size: {PLAYBACK_SMALL}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        self.legend1.setStyleSheet(
            f"color: {p['health_cpu']}; font-size: {PLAYBACK_CAPTION}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        self.legend2.setStyleSheet(
            f"color: {p['health_mem']}; font-size: {PLAYBACK_CAPTION}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        for tick in self.axis_ticks:
            tick.setStyleSheet(
                f"color: {p['muted_label']}; font-size: {PLAYBACK_CAPTION}px; font-weight: 700; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
            )

        self.plot_widget.getPlotItem().vb.setBackgroundColor(QColor(p["card_bg"]))
        self.plot_widget.clear()
        self.plot_widget.plot(self._x, self._y1, pen=pg.mkPen(color=QColor(p["health_cpu"]), width=1.8), antialias=True)
        self.plot_widget.plot(self._x, self._y2, pen=pg.mkPen(color=QColor(p["health_mem"]), width=1.8), antialias=True)

        self.max_card.apply_theme(theme_name)
        self.temp_card.apply_theme(theme_name)
        self.frames_table.apply_theme(theme_name)

        self.playback_bar.setStyleSheet(
            f"QFrame {{ background: {p['card_alt_bg']}; border: 1px solid {p['card_border']}; border-radius: 10px; }}"
        )
        self.btn_back.setStyleSheet(
            f"QPushButton {{ color: {p['muted_label']}; background: transparent; border: none; min-height: 0px; font-size: {PLAYBACK_SMALL}px; }}"
        )
        self.btn_play.setStyleSheet(
            f"QPushButton {{ background: {p['status_live_bg']}; color: {p['status_live_fg']}; border: none; min-height: 0px; border-radius: 10px; font-size: {PLAYBACK_LARGE}px; font-weight: 800; }}"
        )
        self.btn_fwd.setStyleSheet(
            f"QPushButton {{ color: {p['muted_label']}; background: transparent; border: none; min-height: 0px; font-size: {PLAYBACK_SMALL}px; }}"
        )
        self.slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                background: {p['slider_groove']};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {p['slider_fill']};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {p['slider_handle']};
                width: 12px;
                margin: -6px 0;
                border-radius: 6px;
                border: 1px solid {p['slider_handle_border']};
            }}
            """
        )
        for dot, color in zip(self.marker_dots, [p["health_cpu"], p["badge_critical_fg"], p["health_mem"]]):
            dot.setStyleSheet(f"color: {color}; font-size: {PLAYBACK_LARGE}px;")
        self.speed_widget.setStyleSheet(
            f"QFrame {{ background: {p['btn_context_bg']}; border: 1px solid {p['btn_context_border']}; border-radius: 8px; }}"
        )
        for btn in self.speed_buttons:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    color: {p['muted_label']};
                    background: transparent;
                    border: none;
                    min-height: 0px;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: {PLAYBACK_CAPTION}px;
                    font-weight: 800;
                    font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;
                }}
                QPushButton:checked {{
                    color: {p['window_fg']};
                    background: {p['dropdown_selection_bg']};
                }}
                """
            )
        self.time_current.setStyleSheet(
            f"color: {p['window_fg']}; font-size: {PLAYBACK_CAPTION}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        self.time_total.setStyleSheet(
            f"color: {p['muted_label']}; font-size: {PLAYBACK_CAPTION}px; font-weight: 700; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        self.filters.setStyleSheet(
            f"color: {p['muted_label']}; font-size: {PLAYBACK_CAPTION}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        self.save_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {p['btn_context_bg']};
                color: {p['btn_context_fg']};
                border: 1px solid {p['btn_context_border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: {PLAYBACK_CAPTION}px;
                font-weight: 800;
                font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;
            }}
            """
        )
