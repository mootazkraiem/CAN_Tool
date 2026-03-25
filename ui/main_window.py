# ui/main_window.py

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGraphicsBlurEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .alerts import AlertsWidget
from .analytics import AnalyticsWidget
from .can_table import CanTableWidget
from .decoder_manager import DecoderManagerWidget
from .export_overlay import ExportOverlay
from .import_overlay import ImportOverlay
from .log_playback import LogPlaybackWidget
from .right_panel import RightPanelWidget
from .settings import SettingsWidget
from .sidebar import SidebarWidget
from .styles import get_stylesheet
from .theme import (
    PAGE_MARGIN_LARGE,
    PLACEHOLDER_ICON_SIZE,
    PLACEHOLDER_SUBTITLE_SIZE,
    PLACEHOLDER_TITLE_SIZE,
    THEME_DARK,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_DEFAULT_X,
    WINDOW_DEFAULT_Y,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from .topbar import TopBarWidget
from .visualization import VisualizationWidget


class MainWindow(QMainWindow):
    DASHBOARD_INDEX = 0
    LOG_PLAYBACK_INDEX = 1
    DECODER_MANAGER_INDEX = 2
    ALERTS_INDEX = 3
    ANALYTICS_INDEX = 4
    SETTINGS_INDEX = 5

    def __init__(self):
        super().__init__()
        self.current_theme = THEME_DARK
        self.setWindowTitle("CAN MASTER - Diagnostics Suite")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setGeometry(WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.init_ui()
        self.apply_style()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        overlay_stack = QStackedLayout(central)
        overlay_stack.setContentsMargins(0, 0, 0, 0)
        overlay_stack.setStackingMode(QStackedLayout.StackAll)

        self.app_shell = QWidget()
        overlay_stack.addWidget(self.app_shell)

        root = QHBoxLayout(self.app_shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = SidebarWidget()

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.topbar = TopBarWidget()

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_dashboard())
        self.log_playback = LogPlaybackWidget()
        self.stack.addWidget(self.log_playback)
        self.stack.addWidget(DecoderManagerWidget())
        self.stack.addWidget(AlertsWidget())
        self.stack.addWidget(AnalyticsWidget())
        self.settings_page = SettingsWidget()
        self.stack.addWidget(self.settings_page)

        center_layout.addWidget(self.topbar)
        center_layout.addWidget(self.stack)

        root.addWidget(self.sidebar)
        root.addWidget(center)

        self.export_overlay = ExportOverlay(central)
        self.export_overlay.hide()
        overlay_stack.addWidget(self.export_overlay)

        self.import_overlay = ImportOverlay(central)
        self.import_overlay.hide()
        overlay_stack.addWidget(self.import_overlay)

        self.sidebar.page_changed.connect(self.stack.setCurrentIndex)
        self.stack.currentChanged.connect(self._sync_topbar_state)
        self.topbar.connect_requested.connect(self.show_dashboard)
        self.topbar.load_log_requested.connect(self.open_load_log)
        self.topbar.export_requested.connect(self.open_export_overlay)
        self.export_overlay.closed.connect(self.close_export_overlay)
        self.export_overlay.exported.connect(self._handle_exported)
        self.import_overlay.closed.connect(self.close_import_overlay)
        self.settings_page.theme_changed.connect(self.set_theme)

        self.background_blur = QGraphicsBlurEffect(self)
        self.background_blur.setBlurRadius(0)
        self.app_shell.setGraphicsEffect(self.background_blur)

        self._sync_topbar_state(self.stack.currentIndex())
        self.settings_page.set_theme(self.current_theme)

    def _build_dashboard(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        workspace = QWidget()
        ws_layout = QVBoxLayout(workspace)
        ws_layout.setContentsMargins(PAGE_MARGIN_LARGE, PAGE_MARGIN_LARGE, PAGE_MARGIN_LARGE, PAGE_MARGIN_LARGE)
        ws_layout.setSpacing(18)

        self.can_table = CanTableWidget()
        self.can_table.add_mock_data()
        self.can_table.setMinimumHeight(460)

        self.viz = VisualizationWidget()
        self.viz.setMinimumHeight(340)

        ws_layout.addWidget(self.can_table, 6)
        ws_layout.addWidget(self.viz, 4)

        self.right_panel = RightPanelWidget()

        layout.addWidget(workspace, 1)
        layout.addWidget(self.right_panel)
        return page

    def _build_placeholder(self, name: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        icon = QLabel("[]")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size: {PLACEHOLDER_ICON_SIZE}px; color: #2d3340;")

        title = QLabel(name)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: {PLACEHOLDER_TITLE_SIZE}px; font-weight: 700; color: #eef4fb; letter-spacing: 1px;"
        )

        sub = QLabel("This section is under construction.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size: {PLACEHOLDER_SUBTITLE_SIZE}px; color: #7a8598;")

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(sub)
        return page

    def apply_style(self):
        self.setStyleSheet(get_stylesheet(self.current_theme))
        self._apply_theme_to_widgets()

    def _apply_theme_to_widgets(self):
        for widget_name in ("can_table", "viz", "right_panel", "log_playback"):
            widget = getattr(self, widget_name, None)
            if widget is not None and hasattr(widget, "apply_theme"):
                widget.apply_theme(self.current_theme)

    def set_theme(self, theme_name: str):
        self.current_theme = theme_name
        self.settings_page.set_theme(theme_name)
        self.apply_style()

    def show_dashboard(self):
        self.stack.setCurrentIndex(self.DASHBOARD_INDEX)

    def open_load_log(self):
        self.topbar.set_active_tab("load")
        self.background_blur.setBlurRadius(18)
        self.import_overlay.setGeometry(self.centralWidget().rect())
        self.import_overlay.open_overlay(auto_prompt=False)

    def open_export_overlay(self):
        self.topbar.set_active_tab("export")
        self.background_blur.setBlurRadius(18)
        self.export_overlay.setGeometry(self.centralWidget().rect())
        self.export_overlay.open_overlay()

    def close_import_overlay(self):
        self.background_blur.setBlurRadius(0)
        self._sync_topbar_state(self.stack.currentIndex())

    def close_export_overlay(self):
        self.background_blur.setBlurRadius(0)
        self._sync_topbar_state(self.stack.currentIndex())

    def _handle_exported(self, path: str):
        self.statusBar().setStyleSheet("")
        self.statusBar().showMessage(f"Exported report to {path}", 5000)

    def _sync_topbar_state(self, index: int):
        if self.import_overlay.isVisible():
            active_tab = "load"
        elif self.export_overlay.isVisible():
            active_tab = "export"
        else:
            active_tab = "connect"
        self.topbar.set_active_tab(active_tab)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "export_overlay"):
            self.export_overlay.setGeometry(self.centralWidget().rect())
        if hasattr(self, "import_overlay"):
            self.import_overlay.setGeometry(self.centralWidget().rect())
