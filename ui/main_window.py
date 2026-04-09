from __future__ import annotations

from dataclasses import dataclass
from .native_viewer import GarageSceneWidget
from .qt_compat import (
    QColor,
    QFont,
    QLinearGradient,
    QMainWindow,
    QPainter,
    QPen,
    QRectF,
    QSurfaceFormat,
    QTimer,
    QWidget,
    Qt,
    align_center,
    no_brush,
    no_pen,
    widget_attribute_translucent,
)

try:
    from PyQt6.QtGui import QRegion
except ImportError:
    from PyQt5.QtGui import QRegion


CYAN = QColor("#00E5FF")
MAGENTA = QColor("#B100FF")
TEXT = QColor("#EAF8FF")


def configure_opengl():
    fmt = QSurfaceFormat()
    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    fmt.setVersion(3, 3)
    try:
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    except Exception:
        pass
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setAlphaBufferSize(8)
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)


def _font(families: tuple[str, ...], size: int, weight: int = 50) -> QFont:
    for family in families:
        font = QFont(family, size)
        if font.family():
            font.setWeight(weight)
            return font
    fallback = QFont("Bahnschrift", size)
    fallback.setWeight(weight)
    return fallback


def _orbitron(size: int, weight: int = 57) -> QFont:
    return _font(("Orbitron SemiBold", "Orbitron", "Eurostile", "Bahnschrift"), size, weight)


@dataclass(frozen=True)
class Section:
    title: str


class GarageOverlay(QWidget):
    SECTIONS = [
        Section("Dashboard"),
        Section("Telemetry"),
        Section("Diagnostics"),
        Section("Log Playback"),
        Section("Analytics"),
        Section("Settings"),
    ]

    def __init__(self, scene: GarageSceneWidget, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.setAttribute(widget_attribute_translucent(), True)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)

        self.current_index = 0.0
        self.target_index = 0.0
        self._hover_index = -1
        self._drag_active = False
        self._drag_origin_x = 0.0
        self._drag_origin_index = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def _tick(self):
        self.current_index += (self.target_index - self.current_index) * 0.30
        self._update_input_mask()
        self.update()

    def _menu_hit_rect(self) -> QRectF:
        width = min(self.width() * 0.74, 1020.0)
        return QRectF((self.width() - width) / 2.0, 24.0, width, 62.0)

    def _tab_rects(self) -> list[QRectF]:
        menu_rect = self._menu_hit_rect()
        inset = 14.0
        gap = 8.0
        count = len(self.SECTIONS)
        tab_w = (menu_rect.width() - inset * 2.0 - gap * (count - 1)) / count
        rects = []
        x = menu_rect.left() + inset
        y = menu_rect.top() + 8.0
        h = menu_rect.height() - 16.0
        for _ in self.SECTIONS:
            rects.append(QRectF(x, y, tab_w, h))
            x += tab_w + gap
        return rects

    def _tab_index_at(self, pos) -> int:
        for idx, rect in enumerate(self._tab_rects()):
            if rect.contains(pos):
                return idx
        return -1

    def _set_current_section(self, index: float):
        self.target_index = max(0.0, min(len(self.SECTIONS) - 1, index))
        self.scene.set_mode(self.SECTIONS[int(round(self.target_index))].title)
        self.update()

    def mousePressEvent(self, event):
        pos = event.position() if hasattr(event, "position") else event.localPos()
        if self._menu_hit_rect().contains(pos):
            hit = self._tab_index_at(pos)
            if hit >= 0:
                self._set_current_section(hit)
                self._drag_active = True
                self._drag_origin_x = pos.x()
                self._drag_origin_index = self.target_index
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, "position") else event.localPos()
        self._hover_index = self._tab_index_at(pos)
        if self._drag_active:
            delta = (self._drag_origin_x - pos.x()) / 140.0
            self._set_current_section(self._drag_origin_index + delta)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_active:
            self._drag_active = False
            self._set_current_section(round(self.target_index))
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self._hover_index = -1
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_input_mask()

    def _update_input_mask(self):
        if self.width() <= 0 or self.height() <= 0:
            return
        self.setMask(QRegion(self._menu_hit_rect().toRect()))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        menu_rect = self._menu_hit_rect()
        fill = QLinearGradient(menu_rect.topLeft(), menu_rect.bottomLeft())
        fill.setColorAt(0.0, QColor(12, 18, 28, 156))
        fill.setColorAt(1.0, QColor(6, 10, 16, 128))
        painter.setPen(no_pen())
        painter.setBrush(fill)
        painter.drawRoundedRect(menu_rect, 18, 18)

        painter.setPen(QPen(QColor(255, 255, 255, 22), 1.0))
        painter.setBrush(no_brush())
        painter.drawRoundedRect(menu_rect.adjusted(0.5, 0.5, -0.5, -0.5), 18, 18)
        painter.setPen(QPen(QColor(0, 229, 255, 85), 1.0))
        painter.drawRoundedRect(menu_rect.adjusted(1.5, 1.5, -1.5, -1.5), 18, 18)

        active = int(round(self.current_index))
        for idx, rect in enumerate(self._tab_rects()):
            is_active = idx == active
            is_hover = idx == self._hover_index

            if is_active or is_hover:
                painter.setPen(QPen(QColor(0, 229, 255, 165 if is_active else 78), 1.0))
                painter.setBrush(QColor(255, 255, 255, 8 if is_active else 4))
                painter.drawRoundedRect(rect, 11, 11)

            underline = QRectF(rect.left() + 16, rect.bottom() - 4, rect.width() - 32, 2.6 if is_active else 1.0)
            painter.setPen(no_pen())
            painter.setBrush(QColor(0, 229, 255, 240 if is_active else 90 if is_hover else 0))
            painter.drawRoundedRect(underline, 1.3, 1.3)

            painter.setPen(QColor(234, 248, 255, 255 if is_active else 212 if is_hover else 144))
            painter.setFont(_orbitron(11 if is_active else 10, 63 if is_active else 50))
            painter.drawText(rect, align_center(), self.SECTIONS[idx].title.upper())


class GarageExperience(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = GarageSceneWidget(self)
        self.overlay = GarageOverlay(self.scene, self)
        self.overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scene.setGeometry(self.rect())
        self.overlay.setGeometry(self.rect())
        self.overlay.raise_()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CANvision Nexus Garage")
        self.resize(1600, 940)
        self.setMinimumSize(1320, 820)
        self.setCentralWidget(GarageExperience(self))
