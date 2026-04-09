from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .log_import import LogImportWidget
from .theme import (
    EXPORT_CLOSE_BUTTON,
    EXPORT_FOOTER_HEIGHT,
    FONT_FAMILY_MONO,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    FONT_SIZE_TITLE,
    IMPORT_CARD_INNER_MARGIN,
    IMPORT_CARD_MAX_HEIGHT,
    IMPORT_CARD_MAX_WIDTH,
    IMPORT_CARD_MIN_HEIGHT,
    IMPORT_CARD_MIN_WIDTH,
    OVERLAY_CARD_MARGIN,
    OVERLAY_MARGIN,
)


class ImportOverlay(QWidget):
    closed = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(5, 8, 12, 150);")
        self.hide()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(OVERLAY_MARGIN, OVERLAY_MARGIN, OVERLAY_MARGIN, OVERLAY_MARGIN)

        self.card = QFrame()
        self.card.setObjectName("ImportCard")
        self.card.setStyleSheet(
            """
            QFrame#ImportCard {
                background: rgba(36, 36, 39, 238);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 16px;
            }
            QFrame#ImportHeader {
                background: rgba(255, 255, 255, 0.02);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
            QFrame#ImportFooter {
                background: rgba(255, 255, 255, 0.04);
                border-top: 1px solid rgba(255, 255, 255, 0.04);
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }
            """
        )

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(0, 0, 0, 175))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        header_frame = QFrame()
        header_frame.setObjectName("ImportHeader")
        header = QHBoxLayout(header_frame)
        header.setContentsMargins(18, 14, 18, 12)
        header.setSpacing(10)

        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(3)

        title = QLabel("Load Log")
        title.setStyleSheet(f"color: #E6FAFF; font-size: {FONT_SIZE_TITLE}px; font-weight: 700;")

        subtitle = QLabel("IMPORT PREVIEW:")
        subtitle.setStyleSheet(
            f"color: #677382; font-size: {FONT_SIZE_MEDIUM}px; font-weight: 800; letter-spacing: 1px; "
            f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
        )

        title_wrap.addWidget(title)
        title_wrap.addWidget(subtitle)

        self.back_btn = QPushButton("<")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedSize(EXPORT_CLOSE_BUTTON, EXPORT_CLOSE_BUTTON)
        self.back_btn.setStyleSheet(
            "QPushButton { color: #8FE8FF; background: rgba(10, 22, 34, 190); border: 1px solid rgba(0, 200, 255, 110); border-radius: 16px; min-height: 0px; font-size: 18px; font-weight: 700; }"
            "QPushButton:hover { color: #FFFFFF; border-color: rgba(255, 60, 247, 160); }"
        )
        self.back_btn.clicked.connect(self.back_requested.emit)

        self.close_btn = QPushButton("x")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedSize(EXPORT_CLOSE_BUTTON, EXPORT_CLOSE_BUTTON)
        self.close_btn.setStyleSheet(
            "QPushButton { color: #E7EEF7; background: transparent; border: none; min-height: 0px; font-size: 28px; }"
            "QPushButton:hover { color: #FFFFFF; }"
        )
        self.close_btn.clicked.connect(self.close_overlay)
        header.addWidget(self.back_btn)
        header.addLayout(title_wrap)
        header.addWidget(self.close_btn)
        header.setStretch(1, 1)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(IMPORT_CARD_INNER_MARGIN, IMPORT_CARD_INNER_MARGIN, IMPORT_CARD_INNER_MARGIN, 12)
        body_layout.setSpacing(12)

        self.import_widget = LogImportWidget()
        body_layout.addWidget(self.import_widget)

        footer = QFrame()
        footer.setObjectName("ImportFooter")
        footer.setFixedHeight(EXPORT_FOOTER_HEIGHT)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 0, 16, 0)

        footer_label = QLabel("@ IMPORT_CHANNEL_READY_DECODER_SYNC")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet(
            f"color: #7B8692; font-size: {FONT_SIZE_SMALL}px; font-weight: 800; "
            f"font-family: '{FONT_FAMILY_MONO}', 'JetBrains Mono', monospace;"
        )
        footer_layout.addWidget(footer_label)

        card_layout.addWidget(header_frame)
        card_layout.addWidget(body, 1)
        card_layout.addWidget(footer)
        root.addWidget(self.card)

    def open_overlay(self, auto_prompt: bool = True):
        self.show()
        self.raise_()
        self.setFocus()
        self._position_card()
        if auto_prompt:
            self.import_widget.prompt_import_log()

    def close_overlay(self):
        self.hide()
        self.closed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_card()

    def _position_card(self):
        margin = OVERLAY_CARD_MARGIN
        width = max(IMPORT_CARD_MIN_WIDTH, self.width() - margin * 2)
        height = max(IMPORT_CARD_MIN_HEIGHT, self.height() - margin * 2)
        width = min(width, IMPORT_CARD_MAX_WIDTH)
        height = min(height, IMPORT_CARD_MAX_HEIGHT)
        self.card.setGeometry(
            (self.width() - width) // 2,
            (self.height() - height) // 2,
            width,
            height,
        )

    def mousePressEvent(self, event):
        if not self.card.geometry().contains(event.pos()):
            self.close_overlay()
            return
        super().mousePressEvent(event)
