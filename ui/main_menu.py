from __future__ import annotations

import math
import socket
import threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from PyQt5.QtCore import QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer, QUrl, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap, QRadialGradient
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QLabel, QPushButton, QSizePolicy, QStyle, QVBoxLayout, QWidget

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView
    HAS_WEB_ENGINE = True
except Exception:
    QWebEngineSettings = None
    QWebEngineView = None
    HAS_WEB_ENGINE = False

BLUE = QColor("#00C8FF")
PURPLE = QColor("#7A3CFF")
PINK = QColor("#FF3CF7")
BACKGROUND = QColor("#05070A")

BUTTON_OFFSETS = {
    "dashboard": QPointF(-540, -170),
    "telemetry": QPointF(-540, -50),
    "diagnostics": QPointF(-540, 70),
    "playback": QPointF(540, -170),
    "logs": QPointF(540, -50),
    "settings": QPointF(540, 70),
    "connect_vehicle": QPointF(-110, 300),
    "start_session": QPointF(110, 300),
}

BASE_DIAMETER = 58
HOVER_DIAMETER = 68
_ASSET_SERVER = None


class _AssetRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):
        return


class _AssetServer:
    def __init__(self, asset_dir: Path):
        self.asset_dir = asset_dir
        self.httpd = None
        self.thread = None
        self.base_url = None

    def start(self) -> str:
        if self.base_url is not None:
            return self.base_url

        handler = lambda *args, **kwargs: _AssetRequestHandler(*args, directory=str(self.asset_dir), **kwargs)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        port = self.httpd.server_address[1]
        self.base_url = f"http://127.0.0.1:{port}"
        return self.base_url


def _asset_base_url() -> str:
    global _ASSET_SERVER
    asset_dir = Path(__file__).resolve().parents[1] / "assets"
    if _ASSET_SERVER is None:
        _ASSET_SERVER = _AssetServer(asset_dir)
    return _ASSET_SERVER.start()


def _tinted_icon_pixmap(widget: QWidget, standard_icon: QStyle.StandardPixmap, size: int, color: QColor) -> QPixmap:
    icon = widget.style().standardIcon(standard_icon).pixmap(size, size)
    tinted = QPixmap(icon.size())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, icon)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), color)
    painter.end()
    return tinted


class BackButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(42, 42)
        self.setCursor(Qt.PointingHandCursor)
        self.setText("")
        self.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.setIconSize(QSize(18, 18))
        self.setStyleSheet(
            """
            QPushButton {
                background: rgba(10, 15, 20, 208);
                border: 2px solid #00C8FF;
                border-radius: 21px;
            }
            QPushButton:hover {
                background: rgba(18, 25, 38, 228);
                border-color: #FF3CF7;
            }
            """
        )
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(25)
        glow.setOffset(0, 0)
        glow.setColor(BLUE)
        self.setGraphicsEffect(glow)


class GLCarWidget(QWidget):
    ready_changed = pyqtSignal(bool)

    def __init__(self, model_path: Path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent; border: none;")
        self._viewer_ready = HAS_WEB_ENGINE and self.model_path.exists()
        self._loaded = not self._viewer_ready

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if self._viewer_ready:
            self.web_view = QWebEngineView(self)
            self.web_view.setAttribute(Qt.WA_TranslucentBackground, True)
            self.web_view.setStyleSheet("background: transparent; border: none;")
            self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
            self.web_view.page().setBackgroundColor(QColor(0, 0, 0, 0))
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            base_url = _asset_base_url()
            viewer_url = QUrl(f"{base_url}/viewer.html")
            model_url = f"{base_url}/{self.model_path.name}"
            viewer_url.setQuery(f"model_url={QUrl.toPercentEncoding(model_url).data().decode('ascii')}")
            self.web_view.loadFinished.connect(self._handle_load_finished)
            self.web_view.load(viewer_url)
            layout.addWidget(self.web_view, 1)
        else:
            self.web_view = None
            self.ready_changed.emit(True)

    def _handle_load_finished(self, ok: bool):
        self._loaded = bool(ok)
        self.ready_changed.emit(self._loaded)

    def is_ready(self) -> bool:
        return self._loaded

    def focus_zone(self, zone: str):
        if self.web_view is None or not self._loaded:
            return
        self.web_view.page().runJavaScript(f"window.focusHudZone && window.focusHudZone('{zone}')")

    def paintEvent(self, event):
        if self._viewer_ready:
            super().paintEvent(event)
            return
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.transparent)
        radius = min(self.width(), self.height()) * 0.24
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        glow = QRadialGradient(center, radius * 1.6)
        glow.setColorAt(0.0, QColor(0, 200, 255, 55))
        glow.setColorAt(0.55, QColor(122, 60, 255, 35))
        glow.setColorAt(1.0, QColor(255, 60, 247, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius * 1.4, radius * 0.9)

        outline = QRectF(center.x() - radius, center.y() - radius * 0.36, radius * 2, radius * 0.72)
        painter.setBrush(QColor(8, 18, 28, 150))
        painter.setPen(QPen(QColor(0, 200, 255, 160), 2))
        painter.drawRoundedRect(outline, 22, 22)

        painter.setPen(QColor(220, 246, 255, 210))
        painter.setFont(QFont("Bahnschrift", 16, QFont.DemiBold))
        painter.drawText(outline.adjusted(0, 0, 0, -8), Qt.AlignCenter, "SUPRA MK4")
        painter.setFont(QFont("Bahnschrift", 10))
        painter.drawText(outline.adjusted(0, 28, 0, 12), Qt.AlignCenter, "Web 3D viewer unavailable")
        painter.end()


class HoloButton(QWidget):
    def __init__(self, key: str, title: str, icon: QStyle.StandardPixmap, menu: "MainMenuWidget", parent=None):
        super().__init__(parent)
        self.menu = menu
        self.key = key
        self.icon = icon
        self._diameter = 144.0
        self._glow = 0.8
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")
        self.setFixedSize(144, 94)

        self.label = QLabel(title, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background: transparent; color: #c8f7ff; font-size: 12px; font-weight: 700; border: none; letter-spacing: 1px;")
        self.label.setGeometry(10, 46, self.width() - 20, 34)
        self.label_effect = QGraphicsOpacityEffect(self.label)
        self.label_effect.setOpacity(0.9)
        self.label.setGraphicsEffect(self.label_effect)

        self.size_anim = QPropertyAnimation(self, b"diameter", self)
        self.size_anim.setDuration(180)
        self.size_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.glow_anim = QPropertyAnimation(self, b"glowStrength", self)
        self.glow_anim.setDuration(180)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.label_anim = QPropertyAnimation(self.label_effect, b"opacity", self)
        self.label_anim.setDuration(180)
        self.label_anim.setEasingCurve(QEasingCurve.OutCubic)

    def circle_rect(self) -> QRectF:
        return QRectF(0.0, 0.0, self.width(), self.height())

    def connector_anchor(self) -> QPointF:
        return QPointF(self.mapToParent(self.circle_rect().center().toPoint()))

    def set_diameter(self, value: float):
        self._diameter = value
        self.update()

    def get_diameter(self) -> float:
        return self._diameter

    diameter = pyqtProperty(float, fget=get_diameter, fset=set_diameter)

    def set_glow_strength(self, value: float):
        self._glow = value
        self.update()

    def get_glow_strength(self) -> float:
        return self._glow

    glowStrength = pyqtProperty(float, fget=get_glow_strength, fset=set_glow_strength)

    def enterEvent(self, event):
        self.menu.set_hovered_button(self.key)
        self._animate(144.0, 1.2, 1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.menu.clear_hovered_button(self.key)
        self._animate(144.0, 0.8, 0.9)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.menu.open_page_for_button(self.key)
        super().mouseReleaseEvent(event)

    def _animate(self, diameter: float, glow: float, opacity: float):
        self.size_anim.stop()
        self.size_anim.setStartValue(self._diameter)
        self.size_anim.setEndValue(float(diameter))
        self.size_anim.start()

        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._glow)
        self.glow_anim.setEndValue(glow)
        self.glow_anim.start()

        self.label_anim.stop()
        self.label_anim.setStartValue(self.label_effect.opacity())
        self.label_anim.setEndValue(opacity)
        self.label_anim.start()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.circle_rect()
        is_selected = self.menu.selected_button == self.key
        glow_rect = rect.adjusted(-8, -8, 8, 8)
        glow = QLinearGradient(glow_rect.topLeft(), glow_rect.bottomRight())
        glow.setColorAt(0.0, QColor(0, 217, 255, int((90 if not is_selected else 120) * self._glow)))
        glow.setColorAt(0.5, QColor(0, 217, 255, int(30 * self._glow)))
        glow.setColorAt(1.0, QColor(255, 47, 209, int((75 if not is_selected else 165) * self._glow)))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawRoundedRect(glow_rect, 20, 20)

        card = rect.adjusted(1, 1, -1, -1)
        card_fill = QLinearGradient(card.topLeft(), card.bottomRight())
        card_fill.setColorAt(0.0, QColor(8, 16, 24, 155))
        card_fill.setColorAt(1.0, QColor(15, 12, 22, 125))
        border = QLinearGradient(card.topLeft(), card.bottomRight())
        border.setColorAt(0.0, QColor(0, 217, 255, int((200 if not is_selected else 235) * self._glow)))
        border.setColorAt(1.0, QColor(255, 47, 209, int((185 if not is_selected else 255) * self._glow)))
        painter.setBrush(card_fill)
        painter.setPen(QPen(QBrush(border), 1.6))
        painter.drawRoundedRect(card, 14, 14)

        icon_rect = QRectF((self.width() - 32) / 2.0, 12, 32, 32)
        icon_glow = QRadialGradient(icon_rect.center(), 22)
        icon_glow.setColorAt(0.0, QColor(0, 217, 255, int((115 if not is_selected else 140) * self._glow)))
        icon_glow.setColorAt(1.0, QColor(255, 47, 209, 0))
        painter.setBrush(icon_glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(icon_rect)

        icon_color = QColor("#FFD0F4") if is_selected else QColor("#CFFFFF")
        icon = _tinted_icon_pixmap(self, self.icon, 18, icon_color)
        painter.drawPixmap(int((self.width() - 18) / 2), 19, icon)


class OverlayWidget(QWidget):
    def __init__(self, menu: "MainMenuWidget", parent=None):
        super().__init__(parent)
        self.menu = menu
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")
        self.setMouseTracking(True)

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        left_glow = QRadialGradient(QPointF(self.width() * 0.18, self.height() * 0.52), self.width() * 0.35)
        left_glow.setColorAt(0.0, QColor(0, 217, 255, 46))
        left_glow.setColorAt(1.0, QColor(0, 217, 255, 0))
        painter.setBrush(left_glow)
        painter.drawEllipse(QPointF(self.width() * 0.18, self.height() * 0.52), self.width() * 0.22, self.height() * 0.28)

        right_glow = QRadialGradient(QPointF(self.width() * 0.82, self.height() * 0.5), self.width() * 0.35)
        right_glow.setColorAt(0.0, QColor(255, 47, 209, 34))
        right_glow.setColorAt(1.0, QColor(255, 47, 209, 0))
        painter.setBrush(right_glow)
        painter.drawEllipse(QPointF(self.width() * 0.82, self.height() * 0.5), self.width() * 0.22, self.height() * 0.28)

        self._draw_scans(painter)
        self._draw_connectors(painter)
        self._draw_hud_cards(painter)

        title_font = QFont("Bahnschrift", 17)
        title_font.setWeight(QFont.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor(218, 243, 255, 105))
        painter.drawText(QRectF(0, 24, self.width(), 28), Qt.AlignHCenter, "CANVISION HOLOGRAPHIC NAVIGATION")
        painter.end()

    def _draw_scans(self, painter: QPainter):
        for idx in range(18):
            y = 96 + idx * 52 + ((self.menu.anim_time * 120) % 18)
            painter.setPen(QPen(QColor(255, 255, 255, 10), 1))
            painter.drawLine(0, int(y), self.width(), int(y))
        for idx in range(36):
            x = 40 + idx * 46
            painter.setPen(QPen(QColor(0, 217, 255, 12 if idx % 2 == 0 else 7), 1))
            painter.drawLine(int(x), 86, int(x), self.height() - 86)

    def _draw_connectors(self, painter: QPainter):
        center = QPointF(self.width() / 2.0, self.height() / 2.0 + 18)
        for key, button in self.menu.buttons.items():
            anchor = button.connector_anchor()
            active = self.menu.hovered_button == key or self.menu.selected_button == key
            line_color = QColor("#FF2FD1" if active else "#00D9FF")
            line_color.setAlpha(190 if active else 78)
            painter.setPen(QPen(line_color, 1.1))
            painter.drawLine(center, anchor)

    def _draw_hud_cards(self, painter: QPainter):
        cards = [
            (QRectF(44, 118, 220, 114), "PERFORMANCE", ["0-100  3.4s", "TOP  314 km/h", "GRIP  94%"], QColor("#00D9FF")),
            (QRectF(44, 248, 220, 114), "ENGINE / HP", ["2JZ-GTE", "842 HP", "1.18 BAR"], QColor("#00D9FF")),
            (QRectF(44, 378, 220, 114), "SUSPENSION", ["Coilovers", "Track Camber", "Ride -22 mm"], QColor("#00D9FF")),
            (QRectF(self.width() - 264, 118, 220, 114), "PAINT SELECT", ["Midnight Violet", "Pearl clear", "Reflective spec"], QColor("#FF2FD1")),
            (QRectF(self.width() - 264, 248, 220, 114), "WHEEL SETUP", ["18x11 rear", "18x9.5 front", "Semi-slick"], QColor("#FF2FD1")),
        ]
        for rect, title, lines, accent in cards:
            self._draw_card(painter, rect, title, lines, accent)

    def _draw_card(self, painter: QPainter, rect: QRectF, title: str, lines: list[str], accent: QColor):
        fill = QColor(10, 16, 24, 122)
        painter.setBrush(fill)
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1))
        painter.drawRoundedRect(rect, 16, 16)
        painter.setPen(QPen(accent, 1.2))
        painter.drawLine(rect.left() + 18, rect.top() + 18, rect.right() - 18, rect.top() + 18)
        painter.setPen(QColor("#E6F8FF"))
        painter.setFont(QFont("Bahnschrift", 10, QFont.DemiBold))
        painter.drawText(QRectF(rect.left() + 18, rect.top() + 24, rect.width() - 36, 18), Qt.AlignLeft, title)
        painter.setFont(QFont("Bahnschrift", 9))
        painter.setPen(QColor(210, 236, 244, 210))
        for idx, line in enumerate(lines):
            painter.drawText(QRectF(rect.left() + 18, rect.top() + 50 + idx * 18, rect.width() - 36, 16), Qt.AlignLeft, line)


class MainMenuWidget(QWidget):
    BUTTON_SPECS = [
        ("dashboard", "Dashboard", QStyle.SP_ComputerIcon),
        ("telemetry", "Telemetry", QStyle.SP_DriveHDIcon),
        ("diagnostics", "Diagnostics", QStyle.SP_FileDialogDetailedView),
        ("playback", "Playback", QStyle.SP_MediaPlay),
        ("logs", "Logs", QStyle.SP_FileDialogInfoView),
        ("settings", "Settings", QStyle.SP_FileDialogContentsView),
        ("connect_vehicle", "Connect Vehicle", QStyle.SP_DialogYesButton),
        ("start_session", "Start Session", QStyle.SP_MediaSeekForward),
    ]

    def __init__(self, stacked_widget, pages, actions=None, parent=None):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.pages = pages
        self.actions = actions or {}
        self.hovered_button: str | None = None
        self.selected_button: str | None = None
        self.setMouseTracking(True)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        model_path = self._resolve_model_path()
        self.carView = GLCarWidget(model_path, self)
        self.carView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.carView, 1)

        self.overlay = OverlayWidget(self, self)
        self.overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay.setStyleSheet("background: transparent; border: none;")
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.carView.lower()
        self.overlay.raise_()

        self.buttons: dict[str, HoloButton] = {}
        for key, title, icon in self.BUTTON_SPECS:
            self.buttons[key] = HoloButton(key, title, icon, self, self.overlay)
            self.buttons[key].raise_()

        self.anim_time = 0.0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._anim_tick)
        self.anim_timer.start(16)

        QTimer.singleShot(0, self._reposition_elements)

    def is_ready(self) -> bool:
        return self.carView.is_ready()

    def _resolve_model_path(self) -> Path:
        asset_root = Path(__file__).resolve().parents[1] / "assets"
        candidates = [
            asset_root / "toyota_supra_mk4_a80.glb",
            asset_root / "toyota_supra_mk4_a80" / "scene.gltf",
            asset_root / "toyota-supra-mk4-a80" / "scene.gltf",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _anim_tick(self):
        self.anim_time += 0.016 / 5.0
        self.overlay.update()
        for btn in self.buttons.values():
            btn.update()

    def set_hovered_button(self, key: str):
        self.hovered_button = key
        self.overlay.update()

    def clear_hovered_button(self, key: str):
        if self.hovered_button == key:
            self.hovered_button = None
            self.overlay.update()

    def open_page_for_button(self, page_key: str):
        self.selected_button = page_key
        zone = "center"
        if page_key in {"dashboard", "telemetry", "diagnostics"}:
            zone = "left"
        elif page_key in {"playback", "logs", "settings"}:
            zone = "right"
        self.carView.focus_zone(zone)
        action = self.actions.get(page_key)
        if action is not None:
            action()
            return
        target = self.pages.get(page_key)
        if target is not None:
            self.stacked_widget.setCurrentWidget(target)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())
        self._reposition_elements()

    def _reposition_elements(self):
        center = self.rect().center()
        for key, button in self.buttons.items():
            offset = BUTTON_OFFSETS[key]
            x = int(center.x() + offset.x() - button.width() / 2.0)
            y = int(center.y() + offset.y() - 26)
            x = max(8, min(self.width() - button.width() - 8, x))
            y = max(16, min(self.height() - button.height() - 8, y))
            button.move(x, y)

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), BACKGROUND)

        wash = QRadialGradient(QPointF(self.width() / 2.0, self.height() * 0.58), min(self.width(), self.height()) * 0.6)
        wash.setColorAt(0.0, QColor(0, 200, 255, 26))
        wash.setColorAt(0.48, QColor(122, 60, 255, 20))
        wash.setColorAt(1.0, QColor(255, 60, 247, 0))
        painter.fillRect(self.rect(), wash)
        painter.end()
