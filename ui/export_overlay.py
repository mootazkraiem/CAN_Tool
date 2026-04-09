from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPdfWriter, QPagedPaintDevice
from PyQt5.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .theme import (
    BUTTON_HEIGHT,
    EXPORT_CLOSE_BUTTON,
    EXPORT_FILENAME_WIDTH,
    EXPORT_FOOTER_HEIGHT,
    EXPORT_PREVIEW_BAR_HEIGHT,
    FONT_FAMILY_MONO,
    FONT_SIZE_CAPTION,
    FONT_SIZE_HERO,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    FONT_SIZE_TITLE,
    INPUT_HEIGHT,
    OVERLAY_MARGIN,
)


class ExportOverlay(QWidget):
    closed = pyqtSignal()
    exported = pyqtSignal(str)
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(5, 8, 12, 150);")
        self.hide()
        self._build_ui()
        self._refresh_timestamp()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(OVERLAY_MARGIN, OVERLAY_MARGIN, OVERLAY_MARGIN, OVERLAY_MARGIN)
        root.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setObjectName("ExportCard")
        self.card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.card.setStyleSheet(
            """
            QFrame#ExportCard {
                background: rgba(36, 36, 39, 238);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 16px;
            }
            QFrame#ExportHeader {
                background: rgba(255, 255, 255, 0.02);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
            QFrame#PreviewPanel {
                background: #101215;
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 10px;
            }
            QFrame#PreviewBar {
                border: none;
                border-radius: 3px;
            }
            QFrame#ExportFooter {
                background: rgba(255, 255, 255, 0.04);
                border-top: 1px solid rgba(255, 255, 255, 0.04);
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }
            """
        )

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(42)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("ExportHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 12)
        header_layout.setSpacing(10)

        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(3)

        title = QLabel("Export Preview")
        title.setStyleSheet(
            f"color: #E6FAFF; font-size: {FONT_SIZE_TITLE}px; font-weight: 700;"
        )

        subtitle = QLabel("FILENAME:")
        subtitle.setStyleSheet(
            f"color: #677382; font-size: {FONT_SIZE_MEDIUM}px; font-weight: 800; letter-spacing: 1px; "
            f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
        )

        self.filename_input = QLineEdit("ANOMALY_REPORT_PY992.PDF")
        self.filename_input.setFixedSize(EXPORT_FILENAME_WIDTH, INPUT_HEIGHT)
        self.filename_input.setStyleSheet(
            f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.015);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 0 10px;
                color: #AAB5C2;
                font-size: {FONT_SIZE_LARGE}px;
                font-weight: 700;
                font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(86, 215, 240, 0.55);
                background: rgba(255, 255, 255, 0.03);
            }}
            """
        )

        title_wrap.addWidget(title)
        title_wrap.addWidget(subtitle)
        title_wrap.addWidget(self.filename_input)

        self.close_btn = QPushButton("x")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedSize(EXPORT_CLOSE_BUTTON, EXPORT_CLOSE_BUTTON)
        self.close_btn.setStyleSheet(
            f"QPushButton {{ color: #E7EEF7; background: transparent; border: none; min-height: 0px; font-size: {FONT_SIZE_HERO}px; }}"
            "QPushButton:hover { color: #FFFFFF; }"
        )
        self.close_btn.clicked.connect(self.close_overlay)

        self.back_btn = QPushButton("<")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedSize(EXPORT_CLOSE_BUTTON, EXPORT_CLOSE_BUTTON)
        self.back_btn.setStyleSheet(
            "QPushButton { color: #8FE8FF; background: rgba(10, 22, 34, 190); border: 1px solid rgba(0, 200, 255, 110); border-radius: 16px; min-height: 0px; font-size: 18px; font-weight: 700; }"
            "QPushButton:hover { color: #FFFFFF; border-color: rgba(255, 60, 247, 160); }"
        )
        self.back_btn.clicked.connect(self.back_requested.emit)

        header_layout.addWidget(self.back_btn, alignment=Qt.AlignTop)
        header_layout.addLayout(title_wrap)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn, alignment=Qt.AlignTop)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 18, 18, 12)
        body_layout.setSpacing(14)

        preview = QFrame()
        preview.setObjectName("PreviewPanel")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(16, 14, 16, 14)
        preview_layout.setSpacing(12)

        top_line = QHBoxLayout()
        top_line.setSpacing(10)

        left_meta = QVBoxLayout()
        left_meta.setSpacing(2)

        system_lbl = QLabel("KINETIC_DIAGNOSTICS_SYSTEMS")
        system_lbl.setStyleSheet(
            f"color: #708192; font-size: {FONT_SIZE_MEDIUM}px; font-weight: 800; letter-spacing: 1px; "
            f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
        )

        report_lbl = QLabel("ANOMALY SUMMARY REPORT")
        report_lbl.setStyleSheet(
            f"color: #EDF3F9; font-size: {FONT_SIZE_HERO}px; font-weight: 800;"
        )

        left_meta.addWidget(system_lbl)
        left_meta.addWidget(report_lbl)

        right_meta = QVBoxLayout()
        right_meta.setSpacing(2)

        generated_key = QLabel("GENERATED_ON")
        generated_key.setAlignment(Qt.AlignRight)
        generated_key.setStyleSheet(
            f"color: #708192; font-size: {FONT_SIZE_MEDIUM}px; font-weight: 800; letter-spacing: 1px; "
            f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
        )

        self.generated_value = QLabel()
        self.generated_value.setAlignment(Qt.AlignRight)
        self.generated_value.setStyleSheet(
            f"color: #D2DBE5; font-size: {FONT_SIZE_LARGE}px; font-weight: 700; "
            f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
        )

        right_meta.addWidget(generated_key)
        right_meta.addWidget(self.generated_value)

        top_line.addLayout(left_meta)
        top_line.addStretch()
        top_line.addLayout(right_meta)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(255, 255, 255, 0.06); border: none;")

        metric_rows = QVBoxLayout()
        metric_rows.setSpacing(8)
        for label, value, color in [
            ("TOTAL_DATA_POINTS_SCANNED", "142,901,442", "#D6DDE6"),
            ("CRITICAL_FAILURES_DETECTED", "03", "#F5AF8B"),
            ("WARNINGS_LOGGED", "85", "#C9BCD5"),
            ("SIGNAL_INTEGRITY_SCORE", "94.2/100", "#82E3AA"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(8)

            key = QLabel(label)
            key.setStyleSheet(
                f"color: #7B8795; font-size: {FONT_SIZE_LARGE}px; font-weight: 700; "
                f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
            )
            val = QLabel(value)
            val.setStyleSheet(
                f"color: {color}; font-size: {FONT_SIZE_LARGE}px; font-weight: 800; "
                f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
            )

            row.addWidget(key)
            row.addStretch()
            row.addWidget(val)
            metric_rows.addLayout(row)

        bars = QHBoxLayout()
        bars.setSpacing(5)
        for color in ["#7D9AA4", "#7A959C", "#8D6B68", "#738A90", "#7C6F95", "#7A998F"]:
            block = QFrame()
            block.setObjectName("PreviewBar")
            block.setFixedHeight(EXPORT_PREVIEW_BAR_HEIGHT)
            block.setStyleSheet(f"QFrame#PreviewBar {{ background: {color}; }}")
            bars.addWidget(block)

        preview_layout.addLayout(top_line)
        preview_layout.addWidget(divider)
        preview_layout.addLayout(metric_rows)
        preview_layout.addSpacing(2)
        preview_layout.addLayout(bars)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.edit_btn = QPushButton("EDIT METADATA")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedHeight(BUTTON_HEIGHT)
        self.edit_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: #2F3033;
                color: #C0C8D1;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                padding: 0 20px;
                font-size: {FONT_SIZE_LARGE}px;
                font-weight: 800;
                font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;
            }}
            """
        )
        self.edit_btn.clicked.connect(self._focus_filename)

        self.confirm_btn = QPushButton("CONFIRM & DOWNLOAD")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setFixedHeight(BUTTON_HEIGHT)
        self.confirm_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #57D8EF, stop:1 #35C9F5);
                color: #06212A;
                border: none;
                border-radius: 8px;
                padding: 0 22px;
                font-size: {FONT_SIZE_LARGE}px;
                font-weight: 900;
                font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;
            }}
            QPushButton:hover {{
                background: #7BE7FF;
            }}
            """
        )
        self.confirm_btn.clicked.connect(self.export_report)

        button_row.addWidget(self.edit_btn)
        button_row.addWidget(self.confirm_btn)

        footer = QFrame()
        footer.setObjectName("ExportFooter")
        footer.setFixedHeight(EXPORT_FOOTER_HEIGHT)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 0, 16, 0)

        footer_label = QLabel("@ ENCRYPTED_EXPORT_CHANNEL_ACTIVE_AES_256")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet(
            f"color: #7B8692; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; "
            f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
        )
        footer_layout.addWidget(footer_label)

        body_layout.addWidget(preview)
        body_layout.addLayout(button_row)

        card_layout.addWidget(header)
        card_layout.addWidget(body, 1)
        card_layout.addWidget(footer)

        root.addWidget(self.card, alignment=Qt.AlignCenter)

    def _refresh_timestamp(self):
        self.generated_value.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def _focus_filename(self):
        self.filename_input.setFocus()
        self.filename_input.selectAll()

    def open_overlay(self):
        self._refresh_timestamp()
        self.show()
        self.raise_()
        self.setFocus()

    def close_overlay(self):
        self.hide()
        self.closed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = max(760, int(self.width() * 0.62))
        height = max(560, int(self.height() * 0.68))
        width = min(width, self.width() - 80)
        height = min(height, self.height() - 80)
        self.card.setFixedSize(width, height)

    def mousePressEvent(self, event):
        if not self.card.geometry().contains(event.pos()):
            self.close_overlay()
            return
        super().mousePressEvent(event)

    def export_report(self):
        filename = self.filename_input.text().strip() or "ANOMALY_REPORT.PDF"
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Anomaly Report",
            filename,
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        self._write_pdf(Path(path))
        self.exported.emit(path)
        self.close_overlay()

    def _write_pdf(self, path: Path):
        writer = QPdfWriter(str(path))
        writer.setPageSize(QPagedPaintDevice.A4)
        writer.setResolution(120)

        painter = QPainter(writer)
        try:
            page_width = writer.width()
            page_height = writer.height()

            painter.fillRect(0, 0, page_width, page_height, QColor("#0C0E12"))

            painter.setPen(QColor("#65E5FF"))
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(80, 120, "KINETIC_DIAGNOSTICS")

            painter.setPen(QColor("#EAF1F8"))
            painter.setFont(QFont("Arial", 24, QFont.Bold))
            painter.drawText(80, 210, "Anomaly Summary Report")

            painter.setPen(QColor("#7C8794"))
            painter.setFont(QFont("Courier New", 10))
            painter.drawText(80, 260, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            painter.drawText(80, 285, f"Filename: {path.name}")

            panel_y = 340
            painter.fillRect(80, panel_y, page_width - 160, 300, QColor("#14181F"))
            painter.setPen(QColor("#222933"))
            painter.drawRect(80, panel_y, page_width - 160, 300)

            metrics = [
                ("Total data points scanned", "142,901,420"),
                ("Critical failures detected", "03"),
                ("Warnings logged", "98"),
                ("Signal integrity score", "94.2 / 100"),
            ]
            painter.setFont(QFont("Courier New", 11))
            row_y = panel_y + 70
            for label, value in metrics:
                painter.setPen(QColor("#93A0AF"))
                painter.drawText(110, row_y, label.upper())
                painter.setPen(QColor("#EAF1F8"))
                painter.drawText(page_width - 250, row_y, value)
                row_y += 46

            painter.setPen(QColor("#65E5FF"))
            painter.setFont(QFont("Arial", 14, QFont.Bold))
            painter.drawText(80, 700, "Analyst Notes")
            painter.setPen(QColor("#AAB6C2"))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(
                80,
                740,
                "Pattern analysis indicates intermittent bus flooding and voltage instability spikes.\n"
                "Recommend validating inverter thermal safeguards and replaying the affected capture window.",
            )
        finally:
            painter.end()
