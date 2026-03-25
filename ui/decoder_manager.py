from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QFont
from .theme import (
    BUTTON_HEIGHT,
    DECODER_HEADER_HEIGHT,
    DECODER_SEARCH_WIDTH,
    INPUT_HEIGHT,
    PAGE_MARGIN,
    CARD_MARGIN,
)


class DecoderManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DecoderManagerPage")

        root = QHBoxLayout(self)
        root.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        root.setSpacing(PAGE_MARGIN)

        left_panel = QFrame()
        left_panel.setObjectName("SurfaceCard")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        left_layout.setSpacing(16)

        lbl_list = QLabel("ACTIVE DECODERS")
        lbl_list.setObjectName("SectionTitle")

        self.decoder_list = QListWidget()
        self.decoder_list.addItems(
            ["J1939_Main_Bus.dbc", "Motor_Controller_V2.dbc", "Battery_Management.dbc"]
        )

        btn_load = QPushButton("LOAD NEW DBC")
        btn_load.setObjectName("PrimaryButton")
        btn_load.setFixedHeight(BUTTON_HEIGHT)

        left_layout.addWidget(lbl_list)
        left_layout.addWidget(self.decoder_list)
        left_layout.addStretch()
        left_layout.addWidget(btn_load)

        right_panel = QFrame()
        right_panel.setObjectName("SurfaceCard")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        det_header = QFrame()
        det_header.setObjectName("SurfaceCardAlt")
        det_header.setFixedHeight(DECODER_HEADER_HEIGHT)
        det_h_layout = QHBoxLayout(det_header)
        det_h_layout.setContentsMargins(CARD_MARGIN, 0, CARD_MARGIN, 0)

        lbl_det = QLabel("SIGNAL DEFINITIONS  |  J1939_Main_Bus.dbc")
        lbl_det.setObjectName("SectionTitle")

        self.search_signals = QLineEdit()
        self.search_signals.setPlaceholderText("Search signals...")
        self.search_signals.setFixedWidth(DECODER_SEARCH_WIDTH)
        self.search_signals.setFixedHeight(INPUT_HEIGHT)

        det_h_layout.addWidget(lbl_det)
        det_h_layout.addStretch()
        det_h_layout.addWidget(self.search_signals)

        self.signal_table = QTableWidget(6, 4)
        self.signal_table.setHorizontalHeaderLabels(
            ["SIGNAL NAME", "START BIT", "LENGTH", "UNIT"]
        )
        self.signal_table.horizontalHeader().setStretchLastSection(True)
        self.signal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.signal_table.verticalHeader().setVisible(False)
        self.signal_table.setShowGrid(False)
        self.signal_table.setAlternatingRowColors(True)
        self.signal_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.signal_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        mono_font = QFont("Consolas", 10)
        mock_data = [
            ("WheelSpeed", "0", "16", "km/h"),
            ("EngineTorque", "16", "8", "%"),
            ("OilPressure", "24", "8", "kPa"),
            ("CoolantTemp", "32", "8", "C"),
            ("FuelLevel", "40", "8", "%"),
            ("Odometry", "48", "32", "km"),
        ]
        for r, (name, start, length, unit) in enumerate(mock_data):
            values = [name, start, length, unit]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setForeground(QColor("#8fefff") if c == 0 else QColor("#b5c1d2"))
                if c > 0:
                    item.setFont(mono_font)
                    item.setTextAlignment(Qt.AlignCenter)
                self.signal_table.setItem(r, c, item)

        right_layout.addWidget(det_header)
        right_layout.addWidget(self.signal_table)

        root.addWidget(left_panel, stretch=1)
        root.addWidget(right_panel, stretch=2)
