from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsBlurEffect, QHBoxLayout, QMainWindow, QSplitter, QStackedLayout, QStackedWidget, QVBoxLayout, QWidget

from core.ai_model import AIModel
from core.anomaly import Anomaly, RuleBasedDetector
from core.can_reader import CANReader
from core.decoder import DecodedSignal, VehicleDecoder
from core.session_data import SessionDataManager
from .ai_chat import AIChatWidget
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
from .theme import PAGE_MARGIN_LARGE, THEME_DARK, WINDOW_DEFAULT_HEIGHT, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from .topbar import TopBarWidget
from .visualization import VisualizationWidget


class MainWindow(QMainWindow):
    DASHBOARD_INDEX = 0
    LOG_PLAYBACK_INDEX = 1
    DECODER_MANAGER_INDEX = 2
    ALERTS_INDEX = 3
    ANALYTICS_INDEX = 4
    AI_CHAT_INDEX = 5
    SETTINGS_INDEX = 6

    def __init__(self):
        super().__init__()
        self.current_theme = THEME_DARK
        self.setWindowTitle("CANvision")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setGeometry(WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self._build_pipeline()
        self.init_ui()
        self.apply_style()

    def _build_pipeline(self):
        default_profile = Path(__file__).resolve().parents[1] / "profiles" / "default_vehicle.json"
        self.reader = CANReader(self)
        self.decoder = VehicleDecoder(str(default_profile), self)
        self.session_data = SessionDataManager(self)
        self.rule_detector = RuleBasedDetector(self)
        self.ai_model = AIModel(self)

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
        self.log_playback.set_session_manager(self.session_data)
        self.stack.addWidget(self.log_playback)
        self.decoder_manager = DecoderManagerWidget()
        self.stack.addWidget(self.decoder_manager)
        self.alerts_page = AlertsWidget()
        self.stack.addWidget(self.alerts_page)
        self.analytics_page = AnalyticsWidget()
        self.analytics_page.set_session_data(self.session_data)
        self.stack.addWidget(self.analytics_page)
        self.ai_chat_page = AIChatWidget()
        self.ai_chat_page.set_session_data(self.session_data)
        self.stack.addWidget(self.ai_chat_page)
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

        self.background_blur = QGraphicsBlurEffect(self)
        self.background_blur.setBlurRadius(0)
        self.app_shell.setGraphicsEffect(self.background_blur)

        self._connect_ui()
        self._connect_pipeline()
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
        self.can_table.setMinimumHeight(420)
        self.viz = VisualizationWidget()
        self.viz.set_session_manager(self.session_data)
        self.viz.setMinimumHeight(300)

        dashboard_split = QSplitter(Qt.Vertical)
        dashboard_split.setChildrenCollapsible(False)
        dashboard_split.addWidget(self.can_table)
        dashboard_split.addWidget(self.viz)
        dashboard_split.setStretchFactor(0, 7)
        dashboard_split.setStretchFactor(1, 3)
        dashboard_split.setSizes([520, 320])
        ws_layout.addWidget(dashboard_split, 1)

        self.right_panel = RightPanelWidget()
        layout.addWidget(workspace, 1)
        layout.addWidget(self.right_panel)
        return page

    def _connect_ui(self):
        self.sidebar.page_changed.connect(self.stack.setCurrentIndex)
        self.stack.currentChanged.connect(self._sync_topbar_state)
        self.topbar.connect_requested.connect(self.show_dashboard)
        self.topbar.connect_requested.connect(self._toggle_monitoring)
        self.topbar.load_log_requested.connect(self.open_load_log)
        self.topbar.export_requested.connect(self.open_export_overlay)
        self.export_overlay.closed.connect(self.close_export_overlay)
        self.export_overlay.exported.connect(self._handle_exported)
        self.import_overlay.closed.connect(self.close_import_overlay)
        self.settings_page.theme_changed.connect(self.set_theme)
        self.decoder_manager.profile_selected.connect(self.decoder.load_profile)
        self.alerts_page.analyze_requested.connect(self._focus_anomaly)
        self.alerts_page.ignore_requested.connect(self._handle_ignored_alert)
        self.viz.clear_session_requested.connect(self._clear_session)

    def _connect_pipeline(self):
        self.reader.frame_received.connect(self.decoder.decode_frame)
        self.reader.mode_changed.connect(self._handle_reader_mode)
        self.reader.error_occurred.connect(self.statusBar().showMessage)

        # SessionDataManager is the single source of truth for the active stream.
        # Every view reads from this stream-scoped store so ignore/playback/chat stay aligned.
        self.decoder.signal_decoded.connect(self.session_data.add_signal)
        self.decoder.signal_decoded.connect(self._handle_decoded_signal)
        self.decoder.profile_loaded.connect(lambda name, count: self.statusBar().showMessage(f"Loaded {name} ({count} signals)", 3000))
        self.decoder.error_occurred.connect(self.statusBar().showMessage)

        self.rule_detector.anomaly_detected.connect(self.session_data.upsert_anomaly)
        self.ai_model.anomaly_detected.connect(self.session_data.upsert_anomaly)
        self.ai_model.model_status.connect(lambda message: self.statusBar().showMessage(message, 3000))

        self.session_data.anomaly_updated.connect(self._handle_anomaly)
        self.session_data.anomaly_ignored.connect(self.alerts_page.remove_anomaly)
        self.session_data.anomaly_ignored.connect(self.right_panel.remove_anomaly)
        self.session_data.session_cleared.connect(lambda _sid: self.can_table.clear())
        self.session_data.session_cleared.connect(lambda _sid: self.viz.clear())
        self.session_data.session_cleared.connect(lambda _sid: self.alerts_page.clear())
        self.session_data.session_cleared.connect(lambda _sid: self.right_panel.clear())
        self.session_data.session_started.connect(self.log_playback.refresh_from_session)
        self.session_data.signal_added.connect(self.log_playback.refresh_from_session)

    def _handle_decoded_signal(self, signal: DecodedSignal):
        self.can_table.add_signal(signal)
        self.viz.add_signal(signal)
        self.analytics_page.add_signal(signal)
        self.right_panel.add_signal(signal)
        self.rule_detector.process_signal(signal)
        self.ai_model.process_signal(signal)

    def _handle_anomaly(self, anomaly: Anomaly):
        if not anomaly or not anomaly.title:
            return
        self.alerts_page.upsert_anomaly(anomaly)
        self.analytics_page.add_anomaly(anomaly)
        self.right_panel.upsert_anomaly(anomaly)

    def _handle_reader_mode(self, mode: str):
        self.topbar.set_connection_state(mode != "stopped")
        self.right_panel.set_reader_mode(mode)
        self.statusBar().showMessage(f"CAN reader mode: {mode}", 3000)

    def _toggle_monitoring(self):
        if self.reader.mode == "stopped":
            keep_session = self.viz.keep_session_enabled()
            # A new stream gets a fresh stream_id so repeated CAN IDs from an older run
            # never overwrite or leak into the current alert/playback state.
            stream_id = self.session_data.start_session(keep_previous=keep_session)
            self.statusBar().showMessage(f"Started stream {stream_id}", 2500)
            self.reader.start(stream_id)
        else:
            self.reader.stop()

    def _clear_session(self):
        self.session_data.clear_session()
        self.statusBar().showMessage("Session history cleared", 2500)

    def _focus_anomaly(self, anomaly: Anomaly):
        self.stack.setCurrentIndex(self.AI_CHAT_INDEX)
        self.ai_chat_page.open_analyze_prompt(anomaly)

    def _handle_ignored_alert(self, anomaly: Anomaly):
        self.session_data.ignore_anomaly(anomaly.alert_id, anomaly.stream_id)
        self.statusBar().showMessage(f"Ignored alert: {anomaly.title}", 2000)

    def apply_style(self):
        self.setStyleSheet(get_stylesheet(self.current_theme))
        self._apply_theme_to_widgets()

    def _apply_theme_to_widgets(self):
        for widget_name in ("can_table", "viz", "right_panel", "log_playback", "analytics_page"):
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

    def closeEvent(self, event):
        self.reader.stop()
        super().closeEvent(event)
