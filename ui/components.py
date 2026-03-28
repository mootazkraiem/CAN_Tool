from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from .theme import CARD_MARGIN, FONT_FAMILY_MONO, FONT_SIZE_CAPTION, FONT_SIZE_HERO, FONT_SIZE_LARGE, INFO_BLOCK_BAR_HEIGHT, mono_font

try:
    import pyqtgraph as pg

    HAS_PYQTGRAPH = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_PYQTGRAPH = False


class MetricCard(QFrame):
    def __init__(self, title, value, unit, color_hex):
        super().__init__()
        self.setObjectName("MetricCard")
        self.setStyleSheet(
            f"""
            #MetricCard {{
                background: #0A0D12;
                border: 1px solid {color_hex}40;
                border-radius: 12px;
            }}
            #MetricCard:hover {{
                border: 1px solid {color_hex}90;
                background: #0D1118;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: #94A3B8; font-size: {FONT_SIZE_CAPTION}px; font-weight: 700; letter-spacing: 1px; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )

        val_layout = QHBoxLayout()
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"color: #F8FAFC; font-size: {FONT_SIZE_HERO}px; font-weight: 800; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace;"
        )
        unit_lbl = QLabel(unit)
        unit_lbl.setStyleSheet(
            f"color: #64748B; font-size: {FONT_SIZE_LARGE}px; font-weight: 700; font-family: '{FONT_FAMILY_MONO}', 'Consolas', monospace; padding-top: 12px;"
        )

        val_layout.addWidget(val_lbl)
        val_layout.addWidget(unit_lbl)
        val_layout.addStretch()

        bar = QFrame()
        bar.setFixedHeight(INFO_BLOCK_BAR_HEIGHT)
        bar.setStyleSheet(f"background: {color_hex}; border-radius: 1px; border: none;")

        layout.addWidget(title_lbl)
        layout.addLayout(val_layout)
        layout.addStretch()
        layout.addWidget(bar)


class SignalHoverPlot(pg.PlotWidget if HAS_PYQTGRAPH else QFrame):
    def __init__(self, parent=None):
        if HAS_PYQTGRAPH:
            super().__init__(parent=parent)
        else:
            super().__init__(parent)
        self._series: Dict[str, List[Tuple[float, float]]] = {}
        self._series_units: Dict[str, str] = {}
        self._theme = {}
        self._crosshair_items_ready = False
        if HAS_PYQTGRAPH:
            pg.setConfigOptions(antialias=True, background=None)
            self.hideAxis("top")
            self.hideAxis("right")
            axis_font = mono_font(10)
            self.getAxis("left").setStyle(tickFont=axis_font, tickTextOffset=8)
            self.getAxis("bottom").setStyle(tickFont=axis_font, tickTextOffset=8)
            self.showGrid(x=True, y=True, alpha=0.12)
            self.setMouseEnabled(x=True, y=False)
            self._v_line = pg.InfiniteLine(angle=90, movable=False)
            self._h_line = pg.InfiniteLine(angle=0, movable=False)
            self._cursor_tip = pg.TextItem(anchor=(0, 1))
            self._x_label = pg.TextItem(anchor=(0.5, 0))
            self._y_label = pg.TextItem(anchor=(1, 0.5))
            for item in (self._v_line, self._h_line, self._cursor_tip, self._x_label, self._y_label):
                self.addItem(item, ignoreBounds=True)
            self.scene().sigMouseMoved.connect(self._handle_mouse_move)
            self._crosshair_items_ready = True

    def apply_theme(self, palette: dict):
        self._theme = dict(palette)
        if not HAS_PYQTGRAPH:
            return
        axis_pen = pg.mkPen(color=palette["viz_axis_fg"], width=1)
        guide_pen = pg.mkPen(color=palette["strong_border"], width=1)
        text_color = palette["window_fg"]
        fill = QColor(palette["card_bg"])
        fill.setAlpha(245)
        self.setBackground((0, 0, 0, 0))
        self.getAxis("left").setTextPen(axis_pen)
        self.getAxis("bottom").setTextPen(axis_pen)
        self.getAxis("left").setPen(axis_pen)
        self.getAxis("bottom").setPen(axis_pen)
        self._v_line.setPen(guide_pen)
        self._h_line.setPen(guide_pen)
        for item in (self._cursor_tip, self._x_label, self._y_label):
            item.setColor(text_color)
            item.fill = fill
            item.border = guide_pen

    def plot_signals(self, series: Dict[str, List[Tuple[float, float]]], units: Dict[str, str], colors: Iterable[str]):
        if not HAS_PYQTGRAPH:
            return
        self._series = {name: list(points) for name, points in series.items()}
        self._series_units = dict(units)
        self.clear()
        for item in (self._v_line, self._h_line, self._cursor_tip, self._x_label, self._y_label):
            self.addItem(item, ignoreBounds=True)
        self.setBackground((0, 0, 0, 0))
        for index, (name, points) in enumerate(self._series.items()):
            if not points:
                continue
            x_axis = list(range(len(points)))
            y_axis = [value for _, value in points]
            color_list = list(colors)
            pen = pg.mkPen(color=color_list[index % len(color_list)], width=2)
            self.plot(x_axis, y_axis, pen=pen, name=name)
        self._hide_hover()

    def _handle_mouse_move(self, position):
        if not HAS_PYQTGRAPH or not self._series:
            return
        vb = self.getPlotItem().vb
        if not self.sceneBoundingRect().contains(position):
            self._hide_hover()
            return
        mouse_point = vb.mapSceneToView(position)
        index = int(round(mouse_point.x()))
        nearest = None
        series_name = ""
        for name, points in self._series.items():
            if 0 <= index < len(points):
                timestamp, value = points[index]
                if nearest is None or abs(value - mouse_point.y()) < abs(nearest[1] - mouse_point.y()):
                    nearest = (timestamp, value, index)
                    series_name = name
        if nearest is None:
            self._hide_hover()
            return

        timestamp, value, index = nearest
        self._v_line.setVisible(True)
        self._h_line.setVisible(True)
        self._cursor_tip.setVisible(True)
        self._x_label.setVisible(True)
        self._y_label.setVisible(True)
        self._v_line.setPos(index)
        self._h_line.setPos(value)

        stamp_text = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
        unit = self._series_units.get(series_name, "")
        self._cursor_tip.setText(f"{series_name}\n{value:.2f} {unit}\n{stamp_text}")
        self._cursor_tip.setPos(index + 0.4, value)
        self._x_label.setText(stamp_text)
        self._x_label.setPos(index, self.viewRange()[1][0])
        self._y_label.setText(f"{value:.2f}")
        self._y_label.setPos(self.viewRange()[0][0], value)

    def _hide_hover(self):
        if not HAS_PYQTGRAPH or not self._crosshair_items_ready:
            return
        self._v_line.setVisible(False)
        self._h_line.setVisible(False)
        self._cursor_tip.setVisible(False)
        self._x_label.setVisible(False)
        self._y_label.setVisible(False)
