from __future__ import annotations

import json
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QAbstractItemView, QComboBox, QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from .theme import CARD_MARGIN, DECODER_HEADER_HEIGHT, PAGE_MARGIN


class DecoderManagerWidget(QWidget):
    profile_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DecoderManagerPage")
        self._profiles_dir = Path(__file__).resolve().parents[1] / "profiles"
        self._build_ui()
        self.refresh_profiles()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        root.setSpacing(PAGE_MARGIN)

        left_panel = QFrame()
        left_panel.setObjectName("SurfaceCard")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        left_layout.setSpacing(16)
        title = QLabel("AVAILABLE PROFILES")
        title.setObjectName("SectionTitle")
        left_layout.addWidget(title)

        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._emit_selected_profile)
        left_layout.addWidget(self.profile_combo)
        left_layout.addStretch()

        right_panel = QFrame()
        right_panel.setObjectName("SurfaceCard")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        det_header = QFrame()
        det_header.setObjectName("SurfaceCardAlt")
        det_header.setFixedHeight(DECODER_HEADER_HEIGHT)
        det_layout = QHBoxLayout(det_header)
        det_layout.setContentsMargins(CARD_MARGIN, 0, CARD_MARGIN, 0)

        self.detail_title = QLabel("SIGNAL DEFINITIONS")
        self.detail_title.setObjectName("SectionTitle")
        det_layout.addWidget(self.detail_title)
        det_layout.addStretch()

        self.signal_table = QTableWidget(0, 6)
        self.signal_table.setHorizontalHeaderLabels(["CAN ID", "Signal", "Start Byte", "Length", "Scale", "Unit"])
        self.signal_table.horizontalHeader().setStretchLastSection(True)
        self.signal_table.verticalHeader().setVisible(False)
        self.signal_table.setShowGrid(False)
        self.signal_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.signal_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        right_layout.addWidget(det_header)
        right_layout.addWidget(self.signal_table)

        root.addWidget(left_panel, 1)
        root.addWidget(right_panel, 2)

    def refresh_profiles(self):
        profiles = sorted(self._profiles_dir.glob("*.json"))
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for profile in profiles:
            self.profile_combo.addItem(profile.name, str(profile))
        self.profile_combo.blockSignals(False)
        if profiles:
            self.profile_combo.setCurrentIndex(0)
            self._load_profile_preview(str(profiles[0]))
            self.profile_selected.emit(str(profiles[0]))

    def _emit_selected_profile(self):
        path = self.profile_combo.currentData()
        if not path:
            return
        self._load_profile_preview(path)
        self.profile_selected.emit(path)

    def _load_profile_preview(self, path: str):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.signal_table.setRowCount(len(payload))
        self.detail_title.setText(f"SIGNAL DEFINITIONS  |  {Path(path).name}")

        for row, (can_id, definition) in enumerate(payload.items()):
            values = [
                can_id,
                definition.get("signal_name", ""),
                str(definition.get("start_byte", "")),
                str(definition.get("length", "")),
                str(definition.get("scale", "")),
                str(definition.get("unit", "")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                align = Qt.AlignCenter if col != 1 else Qt.AlignLeft | Qt.AlignVCenter
                item.setTextAlignment(int(align))
                self.signal_table.setItem(row, col, item)
