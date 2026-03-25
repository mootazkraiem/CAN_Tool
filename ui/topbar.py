# ui/topbar.py

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from .theme import FONT_FAMILY_MONO, FONT_SIZE_SMALL, TOPBAR_HEIGHT


class TopBarWidget(QFrame):
    connect_requested = pyqtSignal()
    load_log_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(TOPBAR_HEIGHT)
        self._connected = False

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 0, 20, 0)
        root.setSpacing(16)
        root.setAlignment(Qt.AlignVCenter)

        self.kinetics_label = QLabel("KINETIC_DIAGNOSTICS")
        self.kinetics_label.setObjectName("TopbarTitle")
        root.addWidget(self.kinetics_label)

        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setObjectName("BtnTopBarTabActive")
        self.btn_connect.setCursor(Qt.PointingHandCursor)

        self.btn_load = QPushButton("Load Log")
        self.btn_load.setObjectName("BtnTopBarTab")
        self.btn_load.setCursor(Qt.PointingHandCursor)

        self.btn_export = QPushButton("Export")
        self.btn_export.setObjectName("BtnTopBarTab")
        self.btn_export.setCursor(Qt.PointingHandCursor)

        root.addWidget(self.btn_connect)
        root.addWidget(self.btn_load)
        root.addWidget(self.btn_export)

        root.addStretch()

        self.connection_wrap = QFrame()
        connection_layout = QHBoxLayout(self.connection_wrap)
        connection_layout.setContentsMargins(18, 9, 18, 9)
        connection_layout.setSpacing(0)

        self.connection_label = QLabel()
        connection_layout.addWidget(self.connection_label)

        root.addWidget(self.connection_wrap, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.set_connection_state(False)

        self.btn_connect.clicked.connect(self._handle_connect_clicked)
        self.btn_load.clicked.connect(self._handle_load_clicked)
        self.btn_export.clicked.connect(self.export_requested.emit)

    def set_active_tab(self, tab_name: str):
        tabs = {
            "connect": self.btn_connect,
            "load": self.btn_load,
            "export": self.btn_export,
        }
        for name, button in tabs.items():
            button.setObjectName("BtnTopBarTabActive" if name == tab_name else "BtnTopBarTab")
            button.style().unpolish(button)
            button.style().polish(button)

    def set_connection_state(self, connected: bool):
        self._connected = connected
        label = "LIVE_CAPTURE_ON" if connected else "SYSTEM_OFFLINE"
        self.connection_label.setText(label)
        self.connection_wrap.setObjectName("TopStatusLive" if connected else "TopStatusOffline")
        self.connection_label.setStyleSheet(
            f"font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; letter-spacing: 1px;"
        )
        self.connection_wrap.style().unpolish(self.connection_wrap)
        self.connection_wrap.style().polish(self.connection_wrap)

    def _handle_connect_clicked(self):
        self.set_connection_state(not self._connected)
        self.connect_requested.emit()

    def _handle_load_clicked(self):
        self.load_log_requested.emit()
