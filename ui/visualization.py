from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget
import numpy as np

from .theme import (
    COMPACT_SPACING,
    FONT_FAMILY_MONO,
    FONT_SIZE_CAPTION,
    FONT_SIZE_LARGE,
    ITEM_SPACING,
    THEME_DARK,
    VISUALIZATION_COMBO_WIDTH,
    VISUALIZATION_MIN_HEIGHT,
    get_theme_palette,
    mono_font,
)

try:
    import pyqtgraph as pg

    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False


class VisualizationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_name = THEME_DARK

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(COMPACT_SPACING)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(8, 2, 8, 2)
        header_row.setSpacing(ITEM_SPACING)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("SIGNAL TREND")
        title.setObjectName("SectionTitle")
        self.title = title

        status_lbl = QLabel("LIVE TELEMETRY STREAM")
        status_lbl.setObjectName("MutedLabel")
        self.status_lbl = status_lbl

        title_layout.addWidget(title)
        title_layout.addWidget(status_lbl)

        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(14)
        self.leg1 = QLabel("RPM SENSE")
        self.leg2 = QLabel("PACK TEMP")
        legend_layout.addWidget(self.leg1)
        legend_layout.addWidget(self.leg2)

        header_row.addLayout(title_layout)
        header_row.addStretch()
        header_row.addLayout(legend_layout, 0)
        header_row.addSpacing(12)

        self.signal_combo = QComboBox()
        self.signal_combo.addItems(["Engine RPM", "Motor Temp", "Battery Level"])
        self.signal_combo.setFixedHeight(38)
        self.signal_combo.setFixedWidth(max(182, VISUALIZATION_COMBO_WIDTH + 22))
        header_row.addWidget(self.signal_combo, 0, Qt.AlignVCenter)
        root.addLayout(header_row)

        if HAS_PYQTGRAPH:
            pg.setConfigOptions(antialias=True)
            self.graph = pg.PlotWidget()
            self.graph.setMinimumHeight(VISUALIZATION_MIN_HEIGHT)

            axis_font = mono_font(FONT_SIZE_CAPTION)
            self.graph.getAxis("left").setStyle(tickFont=axis_font, tickTextOffset=10)
            self.graph.getAxis("bottom").setStyle(tickFont=axis_font, tickTextOffset=10)
            self.graph.hideAxis("top")
            self.graph.hideAxis("right")
            self.graph.showGrid(x=True, y=True, alpha=0.1)

            self._x = np.linspace(0, 10, 200)
            self._y1 = np.sin(self._x) * 10 + 50 + np.sin(self._x * 5) * 2
            self._y2 = np.cos(self._x * 0.7) * 8 + 40

            root.addWidget(self.graph)
        else:
            p = get_theme_palette(self._theme_name)
            fallback = QLabel("Install 'pyqtgraph' to enable data visualization")
            fallback.setAlignment(Qt.AlignCenter)
            fallback.setStyleSheet(
                f"color: {p['badge_warning_fg']}; font-style: italic; font-size: {FONT_SIZE_LARGE}px;"
                f"background: {p['card_bg']}; border: 1px dashed {p['card_border']}; border-radius: 14px; padding: 24px;"
            )
            root.addWidget(fallback)

        self.apply_theme(self._theme_name)

    def apply_theme(self, theme_name: str):
        self._theme_name = theme_name
        p = get_theme_palette(theme_name)

        self.leg1.setStyleSheet(
            f"color: {p['viz_leg1']}; font-family: '{FONT_FAMILY_MONO}'; font-size: {FONT_SIZE_CAPTION}px; font-weight: 800;"
        )
        self.leg2.setStyleSheet(
            f"color: {p['viz_leg2']}; font-family: '{FONT_FAMILY_MONO}'; font-size: {FONT_SIZE_CAPTION}px; font-weight: 800;"
        )
        self.signal_combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {p['viz_combo_bg']};
                color: {p['viz_combo_fg']};
                border: 1px solid {p['viz_combo_border']};
                border-radius: 10px;
                padding: 5px 32px 5px 12px;
                font-size: {FONT_SIZE_LARGE - 3}px;
            }}
            QComboBox:hover {{
                background: {p['viz_combo_hover_bg']};
                border-color: {p['viz_combo_hover_border']};
            }}
            QComboBox QAbstractItemView {{
                background: {p['viz_combo_bg']};
                color: {p['viz_combo_fg']};
                border: 1px solid {p['viz_combo_popup_border']};
                border-radius: 10px;
                padding: 4px;
                selection-background-color: {p['viz_combo_popup_selection']};
                selection-color: {p['viz_combo_fg']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {p['viz_combo_arrow']};
                margin-right: 8px;
            }}
            """
        )

        if HAS_PYQTGRAPH and hasattr(self, "graph"):
            rgb_vals = tuple(int(part.strip()) for part in p["viz_fill1"].split(","))
            self.graph.setBackground(p["viz_graph_bg"])
            self.graph.getAxis("left").setTextPen(pg.mkPen(color=p["viz_axis_fg"]))
            self.graph.getAxis("bottom").setTextPen(pg.mkPen(color=p["viz_axis_fg"]))
            self.graph.clear()
            self.graph.plot(
                self._x,
                self._y1,
                pen=pg.mkPen(color=p["viz_line1"], width=2.5),
                fillLevel=20,
                brush=pg.mkBrush(rgb_vals),
                antialias=True,
            )
            self.graph.plot(self._x, self._y2, pen=pg.mkPen(color=p["viz_line2"], width=2), antialias=True)
            self.graph.setStyleSheet(f"border: 1px solid {p['viz_graph_border']}; border-radius: 12px;")
