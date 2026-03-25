from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from .theme import (
    BUTTON_HEIGHT,
    CARD_MARGIN_COMPACT,
    CARD_MARGIN_TIGHT,
    FONT_FAMILY_MONO,
    FONT_SIZE_CAPTION,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_MICRO,
    FONT_SIZE_SMALL,
    FONT_SIZE_XL,
    INFO_BLOCK_KEY_SIZE,
    INFO_BLOCK_VALUE_SIZE,
    INPUT_HEIGHT,
    PAGE_MARGIN,
    VALIDATION_LOG_HEIGHT,
)


class InfoBlock(QFrame):
    def __init__(self, label: str, value: str, accent: str = "#00E5FF", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            QFrame {{
                background: #101215;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
            }}
            QLabel#Value {{
                color: {accent};
                font-size: {INFO_BLOCK_VALUE_SIZE}px;
                font-weight: 800;
                font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;
            }}
            QLabel#Key {{
                color: #64748B;
                font-size: {INFO_BLOCK_KEY_SIZE}px;
                font-weight: 700;
                letter-spacing: 1px;
                font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CARD_MARGIN_TIGHT, 12, CARD_MARGIN_TIGHT, 12)
        layout.setSpacing(8)

        key = QLabel(label)
        key.setObjectName("Key")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("Value")

        layout.addWidget(key)
        layout.addWidget(self.value_label)


class LogImportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tree_payloads = {}
        self._build_ui()
        self._seed_mock_state()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        root.setSpacing(PAGE_MARGIN)

        self.left_panel = self._build_library_panel()
        self.center_panel = self._build_details_panel()
        self.right_panel = self._build_preview_panel()

        root.addWidget(self.left_panel, 3)
        root.addWidget(self.center_panel, 4)
        root.addWidget(self.right_panel, 3)

    def _build_library_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background: #101215; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 14px; }")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("LOG_SOURCES")
        title.setStyleSheet(f"color: #E2E8F0; font-size: {FONT_SIZE_CAPTION}px; font-weight: 800; letter-spacing: 1px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

        self.import_btn = QPushButton("IMPORT LOG")
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #57D8EF, stop:1 #35C9F5);
                color: #06212A;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                min-height: {BUTTON_HEIGHT}px;
                font-size: {FONT_SIZE_CAPTION}px;
                font-weight: 800;
                font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;
            }}
            QPushButton:hover {{ background: #7BE7FF; }}
            """
        )
        self.import_btn.clicked.connect(self.prompt_import_log)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.import_btn)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setStyleSheet(
            """
            QTreeWidget {
                background: #0D1014;
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }
            QTreeWidget::item {
                color: #CBD5E1;
                padding: 8px 6px;
                margin: 2px 0;
                border-radius: 6px;
            }
            QTreeWidget::item:selected {
                background: rgba(87, 216, 239, 0.16);
                color: #F8FAFC;
            }
            """
        )
        self.tree.itemSelectionChanged.connect(self._apply_selected_payload)

        footer = QLabel("READY_FOR_DECODER_MAPPING")
        footer.setStyleSheet(f"color: #82E3AA; font-size: {FONT_SIZE_MICRO}px; font-weight: 800; letter-spacing: 1px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

        layout.addLayout(header)
        layout.addWidget(self.tree, 1)
        layout.addWidget(footer)
        return panel

    def _build_details_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background: #101215; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 14px; }")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(INPUT_HEIGHT + 22)
        header.setStyleSheet("QFrame { background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid rgba(255, 255, 255, 0.05); border-top-left-radius: 14px; border-top-right-radius: 14px; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(CARD_MARGIN_COMPACT, 0, CARD_MARGIN_COMPACT, 0)

        self.detail_title = QLabel("SIGNAL_PARAMETERS")
        self.detail_title.setStyleSheet(f"color: #E2E8F0; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; letter-spacing: 1px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

        self.detail_badge = QLabel("READY")
        self.detail_badge.setStyleSheet(f"color: #82E3AA; background: rgba(130, 227, 170, 0.10); border: 1px solid rgba(130, 227, 170, 0.22); border-radius: 10px; padding: 5px 10px; font-size: {FONT_SIZE_MICRO}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

        header_layout.addWidget(self.detail_title)
        header_layout.addStretch()
        header_layout.addWidget(self.detail_badge)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT)
        body_layout.setSpacing(PAGE_MARGIN)

        self.signal_name = QLabel("SIG_CELL_V_MAX")
        self.signal_name.setStyleSheet(f"color: #57D8EF; font-size: {FONT_SIZE_XL}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

        self.detail_grid = QGridLayout()
        self.detail_grid.setHorizontalSpacing(16)
        self.detail_grid.setVerticalSpacing(14)

        self.detail_values = {}
        fields = [
            ("SOURCE", "source"),
            ("FORMAT", "format"),
            ("LINES", "lines"),
            ("SIZE", "size"),
            ("DELIMITER", "delimiter"),
            ("FIRST_FRAME", "first_frame"),
        ]
        for index, (label, key) in enumerate(fields):
            row = (index // 2) * 2
            col = index % 2
            heading = QLabel(label)
            heading.setStyleSheet(f"color: #708192; font-size: {FONT_SIZE_MICRO}px; font-weight: 800; letter-spacing: 1px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

            value = QLabel("--")
            value.setStyleSheet(f"color: #F8FAFC; background: #0E1116; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 12px; font-size: {FONT_SIZE_SMALL}px; font-weight: 700; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")
            self.detail_values[key] = value

            self.detail_grid.addWidget(heading, row, col)
            self.detail_grid.addWidget(value, row + 1, col)

        mode_row = QHBoxLayout()
        for label, active in [("Intel (Little)", True), ("Motorola (Big)", False)]:
            button = QPushButton(label)
            button.setEnabled(False)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: #171B21;
                    color: #64748B;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: {FONT_SIZE_CAPTION}px;
                    font-weight: 700;
                }}
                """
                if not active
                else
                f"""
                QPushButton {{
                    background: rgba(87, 216, 239, 0.14);
                    color: #E2F8FF;
                    border: 1px solid #57D8EF;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: {FONT_SIZE_CAPTION}px;
                    font-weight: 700;
                }}
                """
            )
            mode_row.addWidget(button)

        self.logic_box = QPlainTextEdit()
        self.logic_box.setReadOnly(True)
        self.logic_box.setStyleSheet(f"QPlainTextEdit {{ background: #0E1116; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; color: #94A3B8; padding: 12px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; }}")
        self.logic_box.setPlainText(
            "transform(frame):\n"
            "  scale = 0.00125\n"
            "  offset = 0.0\n"
            "  return raw_value * scale + offset"
        )

        body_layout.addWidget(self.signal_name)
        body_layout.addLayout(self.detail_grid)
        body_layout.addLayout(mode_row)
        body_layout.addWidget(self.logic_box, 1)

        layout.addWidget(header)
        layout.addWidget(body, 1)
        return panel

    def _build_preview_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background: #101215; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 14px; }")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT, CARD_MARGIN_COMPACT)
        layout.setSpacing(16)

        preview_header = QHBoxLayout()
        title = QLabel("LIVE_DECODING_PREVIEW")
        title.setStyleSheet(f"color: #E2E8F0; font-size: {FONT_SIZE_CAPTION}px; font-weight: 800; letter-spacing: 1px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

        badge = QLabel("HEX")
        badge.setStyleSheet(f"color: #708192; background: #171B21; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 4px 8px; font-size: {FONT_SIZE_MICRO}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

        preview_header.addWidget(title)
        preview_header.addStretch()
        preview_header.addWidget(badge)

        self.frame_strip = QLabel("FF  00  A2  E4  12  BC  00  88")
        self.frame_strip.setStyleSheet(f"color: #CBD5E1; background: #0E1116; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 14px; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;")

        stats = QHBoxLayout()
        self.max_value = InfoBlock("MAX_VAL", "0xA2E4")
        self.calc_value = InfoBlock("CALC_OUT", "3.942V", "#8BE9FD")
        stats.addWidget(self.max_value)
        stats.addWidget(self.calc_value)

        self.preview_text = QPlainTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(f"QPlainTextEdit {{ background: #0E1116; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; color: #CBD5E1; padding: 12px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_CAPTION}px; }}")

        self.validation_log = QPlainTextEdit()
        self.validation_log.setReadOnly(True)
        self.validation_log.setFixedHeight(VALIDATION_LOG_HEIGHT)
        self.validation_log.setStyleSheet(f"QPlainTextEdit {{ background: #0E1116; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; color: #708192; padding: 12px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; font-size: {FONT_SIZE_MICRO}px; }}")

        layout.addLayout(preview_header)
        layout.addWidget(self.frame_strip)
        layout.addLayout(stats)
        layout.addWidget(self.preview_text, 1)
        layout.addWidget(self.validation_log)
        return panel

    def _seed_mock_state(self):
        sample = {
            "label": "SIG_CELL_V_MAX",
            "source": "BMS_PACK_01.log",
            "format": "ASCII CAN",
            "lines": "12,942",
            "size": "1.8 MB",
            "delimiter": "space",
            "first_frame": "0x18FF50E5",
            "preview": (
                "12:51:01.048  CAN1  18FF50E5  [8]  FF 00 A2 E4 12 BC 00 88\n"
                "12:51:01.062  CAN1  18FF50E5  [8]  FF 00 A2 D1 11 B6 00 86\n"
                "12:51:01.076  CAN1  18FF50E5  [8]  FE 00 A2 C0 10 B4 00 85\n"
                "12:51:01.091  CAN1  18FF50E5  [8]  FE 00 A2 BE 10 B2 00 84"
            ),
            "validation": (
                "[OK] Source discovered and indexed\n"
                "[OK] Frame timing normalized\n"
                "[OK] Candidate decoder profile attached\n"
                "[SYS] Preview mode active"
            ),
            "frame": "FF  00  A2  E4  12  BC  00  88",
            "max": "0xA2E4",
            "calc": "3.942V",
        }

        self.tree.clear()
        root = QTreeWidgetItem(["BMS_PACK_01.log"])
        child = QTreeWidgetItem(["SIG_CELL_V_MAX"])
        root.addChild(child)
        root.setExpanded(True)
        self.tree.addTopLevelItem(root)

        self._tree_payloads[id(root)] = sample
        self._tree_payloads[id(child)] = sample
        self.tree.setCurrentItem(child)

    def prompt_import_log(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import CAN Log",
            "",
            "CAN Logs (*.log *.asc *.csv *.txt);;All Files (*.*)",
        )
        if path:
            self.load_log_file(path)

    def load_log_file(self, path: str):
        file_path = Path(path)
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""
        lines = [line for line in text.splitlines() if line.strip()]
        preview_lines = lines[:8]
        first_line = preview_lines[0] if preview_lines else "No frame data available"

        suffix = file_path.suffix.lower() or ".txt"
        format_name = {
            ".asc": "Vector ASC",
            ".csv": "CSV",
            ".log": "ASCII LOG",
            ".txt": "Text Capture",
        }.get(suffix, suffix.upper().lstrip("."))

        delimiter = "comma" if suffix == ".csv" else "space"
        signal_name = file_path.stem.upper().replace("-", "_").replace(" ", "_")

        payload = {
            "label": signal_name,
            "source": file_path.name,
            "format": format_name,
            "lines": f"{len(lines):,}",
            "size": f"{file_path.stat().st_size / 1024:.1f} KB",
            "delimiter": delimiter,
            "first_frame": self._extract_first_frame(first_line),
            "preview": "\n".join(preview_lines) if preview_lines else "No preview available.",
            "validation": (
                "[OK] File imported successfully\n"
                f"[OK] Detected format: {format_name}\n"
                f"[OK] Total frames indexed: {len(lines):,}\n"
                "[SYS] Decoder attachment pending"
            ),
            "frame": self._extract_frame_bytes(first_line),
            "max": self._extract_hex_chunk(first_line),
            "calc": f"{min(len(lines) / 1000.0, 9.999):.3f}V",
        }

        self.tree.clear()
        root = QTreeWidgetItem([file_path.name])
        child = QTreeWidgetItem([signal_name])
        root.addChild(child)
        root.setExpanded(True)
        self.tree.addTopLevelItem(root)

        self._tree_payloads = {id(root): payload, id(child): payload}
        self.tree.setCurrentItem(child)

    def _extract_first_frame(self, line: str) -> str:
        for token in line.split():
            if token.upper().startswith("0X"):
                return token.upper()
            if len(token) >= 3 and token.isalnum() and any(ch.isdigit() for ch in token):
                return token.upper()
        return "UNKNOWN"

    def _extract_frame_bytes(self, line: str) -> str:
        tokens = [token.upper() for token in line.split() if len(token) == 2 and all(ch in "0123456789ABCDEFabcdef" for ch in token)]
        return "  ".join(tokens[:8]) if tokens else "--  --  --  --  --  --  --  --"

    def _extract_hex_chunk(self, line: str) -> str:
        bytes_ = [token.upper() for token in line.split() if len(token) == 2 and all(ch in "0123456789ABCDEFabcdef" for ch in token)]
        if len(bytes_) >= 4:
            return f"0x{bytes_[2]}{bytes_[3]}"
        if bytes_:
            return f"0x{''.join(bytes_[:2])}"
        return "0x0000"

    def _apply_selected_payload(self):
        item = self.tree.currentItem()
        if item is None:
            return

        payload = self._tree_payloads.get(id(item))
        if payload is None:
            return

        self.signal_name.setText(payload["label"])
        self.detail_title.setText(f"SIGNAL_PARAMETERS  //  {payload['source']}")
        self.detail_badge.setText("IMPORTED")

        for key, widget in self.detail_values.items():
            widget.setText(payload.get(key, "--"))

        self.frame_strip.setText(payload["frame"])
        self.preview_text.setPlainText(payload["preview"])
        self.validation_log.setPlainText(payload["validation"])

        self.max_value.value_label.setText(payload["max"])
        self.calc_value.value_label.setText(payload["calc"])
