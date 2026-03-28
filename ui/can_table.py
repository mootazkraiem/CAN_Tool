from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .theme import (
    CAN_COL_DATA,
    CAN_COL_DLC,
    CAN_COL_ID,
    CAN_COL_SIGNAL,
    CAN_COL_TIMESTAMP,
    CAN_TABLE_ROW_HEIGHT,
    FONT_FAMILY_MONO,
    FONT_SIZE_CAPTION,
    FONT_SIZE_SMALL,
    THEME_DARK,
    get_theme_palette,
)


class CanTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_name = THEME_DARK

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        viewer_card = QFrame()
        viewer_card.setObjectName("SurfaceCard")
        viewer_layout = QVBoxLayout(viewer_card)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(0)

        self.filter_bar = QFrame()
        self.filter_bar.setObjectName("SurfaceCardAlt")
        filter_layout = QHBoxLayout(self.filter_bar)
        filter_layout.setContentsMargins(14, 10, 14, 10)
        filter_layout.setSpacing(10)

        self.filter_id = QLabel("ID: 0x1A2  x")
        self.filter_signal = QLabel("Signal: Battery_Voltage  x")
        self.filter_add = QLabel("+ ADD_FILTER")

        filter_layout.addWidget(self.filter_id)
        filter_layout.addWidget(self.filter_signal)
        filter_layout.addWidget(self.filter_add)
        filter_layout.addStretch()

        self.header = QFrame()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        self.title = QLabel("CAN_FRAME_VIEWER")
        self.stats = QLabel("PACKETS_S: 1,402  |  ERR_RATE: 0.002%")

        header_layout.addWidget(self.title)
        header_layout.addStretch()
        header_layout.addWidget(self.stats)

        self.table = QTableWidget()
        self.table.setMinimumHeight(360)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["TIMESTAMP", "ID", "DLC", "DATA PAYLOAD (HEX)", "DECODED SIGNAL", "VALUE"]
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
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 4)
        viewer_card.setGraphicsEffect(shadow)

        self.table.setColumnWidth(0, CAN_COL_TIMESTAMP)
        self.table.setColumnWidth(1, CAN_COL_ID)
        self.table.setColumnWidth(2, CAN_COL_DLC)
        self.table.setColumnWidth(3, CAN_COL_DATA + 70)
        self.table.setColumnWidth(4, CAN_COL_SIGNAL + 40)

        viewer_layout.addWidget(self.header)
        viewer_layout.addWidget(self.table)
        root.addWidget(self.filter_bar)
        root.addSpacing(12)
        root.addWidget(viewer_card, 1)

        self.apply_theme(self._theme_name)

    def _make_item(self, text: str, color: str, align=Qt.AlignVCenter | Qt.AlignLeft, mono=False):
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        item.setForeground(QColor(color))
        item.setFont(QFont(FONT_FAMILY_MONO if mono else "Bahnschrift", 11 if mono else 12))
        return item

    def add_mock_data(self):
        p = get_theme_palette(self._theme_name)
        status_colors = {
            "critical": {"fg": p["critical_fg"], "bg": p["critical_bg"]},
            "warning": {"fg": p["warning_fg"], "bg": None},
            "normal": {"fg": p["normal_fg"], "bg": None},
        }
        frames = [
            ("14:20:01.0342", "0x0CF004FE", "8", "FF 3D 22 00 00 00 00 00", "Engine_Speed", "1,450 RPM", "normal"),
            ("14:20:01.0381", "0x18FEE000", "8", "AA FF 00 00 00 00 00 00", "Oil_Pressure_Critical", "8 PSI", "critical"),
            ("14:20:01.0425", "0x0CF00300", "8", "00 22 14 AA 33 00 00 00", "Throttle_Pos", "22.4 %", "normal"),
            ("14:20:01.0501", "0x18FEF111", "8", "12 44 55 66 77 88 99 00", "Cruis_Ctrl_Set", "---", "warning"),
            ("14:20:01.0622", "0x0CF004FE", "8", "FF 42 22 00 00 00 00 00", "Engine_Speed", "1,482 RPM", "normal"),
            ("14:20:01.0710", "0x1A2", "4", "0C 33 00 00", "Battery_Voltage", "14.2 V", "normal"),
        ]

        self.table.setRowCount(len(frames))
        for row, (ts, cid, dlc, data, sig, val, status) in enumerate(frames):
            cfg = status_colors.get(status, status_colors["normal"])
            items = [
                self._make_item(ts, cfg["fg"], mono=True),
                self._make_item(cid, p["normal_id"] if status == "normal" else cfg["fg"], mono=True),
                self._make_item(dlc, cfg["fg"], align=Qt.AlignCenter, mono=True),
                self._make_item(data, cfg["fg"], mono=True),
                self._make_item(sig, cfg["fg"], mono=False),
                self._make_item(val, p["normal_value"] if status == "normal" else cfg["fg"], mono=True),
            ]
            for col, item in enumerate(items):
                if cfg["bg"]:
                    item.setBackground(QColor(cfg["bg"]))
                self.table.setItem(row, col, item)
            self.table.setRowHeight(row, CAN_TABLE_ROW_HEIGHT + 6)

        self.table.selectRow(1)

    def apply_theme(self, theme_name: str):
        self._theme_name = theme_name
        p = get_theme_palette(theme_name)
        self.filter_bar.setStyleSheet(
            f"background: {p['card_bg']}; border: 1px solid {p['card_border']}; border-radius: 12px;"
        )
        chip_style = (
            f"background: {p['card_hover']};"
            f"color: {p['accent_cyan']};"
            f"border: 1px solid {p['card_border']};"
            "border-radius: 10px;"
            "padding: 10px 16px;"
            f"font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
            f"font-size: {FONT_SIZE_CAPTION}px;"
            "font-weight: 800;"
        )
        self.filter_id.setStyleSheet(chip_style)
        self.filter_signal.setStyleSheet(chip_style)
        self.header.setStyleSheet(
            f"QFrame {{ background: {p['viewer_header_bg']}; border-top-left-radius: 12px; border-top-right-radius: 12px; border-bottom: 1px solid {p['viewer_header_border']}; }}"
        )
        self.title.setStyleSheet(
            f"color: {p['viewer_title']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; letter-spacing: 1px;"
        )
        self.stats.setStyleSheet(
            f"color: {p['viewer_stats']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; font-weight: 700;"
        )
        self.filter_add.setStyleSheet(
            f"background: transparent; border: none; color: {p['viewer_stats']}; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; font-weight: 800; padding: 0 4px;"
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
        if self.table.rowCount():
            self.add_mock_data()
