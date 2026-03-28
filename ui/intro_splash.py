from pathlib import Path

from PyQt5.QtCore import QElapsedTimer, QTimer, Qt
from PyQt5.QtGui import QColor, QMovie
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from .intro_theme import INTRO_SPLASH_THEME, intro_subtitle_font, intro_title_font


class IntroSplashScreen(QWidget):
    DISPLAY_MS = INTRO_SPLASH_THEME["display_ms"]
    TICK_MS = INTRO_SPLASH_THEME["tick_ms"]
    PROGRESS_MAX = INTRO_SPLASH_THEME["progress_max"]
    WIDTH = INTRO_SPLASH_THEME["width"]
    HEIGHT = INTRO_SPLASH_THEME["height"]

    def __init__(self, launch_callback):
        super().__init__(None)
        self._launch_callback = launch_callback
        self._main_window = None
        self._movie = None
        self._progress_clock = QElapsedTimer()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self._build_ui()
        self._load_media()
        self._center_on_screen()
        self.show()

        if self._movie is not None:
            self._movie.start()

        self._progress.setRange(0, self.DISPLAY_MS)
        self._progress.setValue(0)
        self._update_progress_style()
        self._progress_clock.start()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_progress)
        self._timer.start(self.TICK_MS)
        self._progress.setRange(0, self.PROGRESS_MAX)

    def _build_ui(self):
        self.resize(self.WIDTH, self.HEIGHT)

        root = QVBoxLayout(self)
        root.setContentsMargins(*([INTRO_SPLASH_THEME["root_margin"]] * 4))

        self._panel = QFrame(self)
        self._panel.setObjectName("SplashPanel")
        self._panel.setStyleSheet(INTRO_SPLASH_THEME["panel_stylesheet"])

        panel_shadow = QGraphicsDropShadowEffect(self._panel)
        panel_shadow.setBlurRadius(28)
        panel_shadow.setOffset(0, 12)
        panel_shadow.setColor(QColor(0, 0, 0, 150))
        self._panel.setGraphicsEffect(panel_shadow)

        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(*([INTRO_SPLASH_THEME["panel_margin"]] * 4))
        panel_layout.setSpacing(INTRO_SPLASH_THEME["panel_spacing"])

        self._media = QLabel(self._panel)
        self._media.setMinimumHeight(INTRO_SPLASH_THEME["media_min_height"])
        self._media.setAlignment(Qt.AlignCenter)
        self._media.setStyleSheet(INTRO_SPLASH_THEME["media_stylesheet"])

        self._title = QLabel(INTRO_SPLASH_THEME["title_text"], self._panel)
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setStyleSheet(f"color: {INTRO_SPLASH_THEME['title_color']};")
        self._title.setFont(intro_title_font())

        self._subtitle = QLabel(INTRO_SPLASH_THEME["subtitle_text"], self._panel)
        self._subtitle.setAlignment(Qt.AlignCenter)
        self._subtitle.setStyleSheet(f"color: {INTRO_SPLASH_THEME['subtitle_color']};")
        self._subtitle.setFont(intro_subtitle_font())

        self._status = QLabel(INTRO_SPLASH_THEME["status_text"], self._panel)
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet(f"color: {INTRO_SPLASH_THEME['status_color']}; font-size: 13px;")

        self._progress = QProgressBar(self._panel)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(INTRO_SPLASH_THEME["progress_height"])

        panel_layout.addWidget(self._media)
        panel_layout.addWidget(self._title)
        panel_layout.addWidget(self._subtitle)
        panel_layout.addWidget(self._status)
        panel_layout.addWidget(self._progress)
        root.addWidget(self._panel)

    def _load_media(self):
        asset_dir = Path("assets").resolve()
        gif_candidates = sorted(asset_dir.glob("*.gif"))
        if not gif_candidates:
            self._media.setText(INTRO_SPLASH_THEME["fallback_media_text"])
            self._media.setStyleSheet(
                self._media.styleSheet()
                + f"color: {INTRO_SPLASH_THEME['fallback_media_color']}; font-size: 16px; font-weight: 700; letter-spacing: 2px;"
            )
            return

        self._movie = QMovie(str(gif_candidates[0]))
        self._movie.setCacheMode(QMovie.CacheAll)
        self._movie.setSpeed(100)
        self._media.setMovie(self._movie)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        self.move(
            geometry.x() + (geometry.width() - self.width()) // 2,
            geometry.y() + (geometry.height() - self.height()) // 2,
        )

    def _advance_progress(self):
        elapsed = min(self.DISPLAY_MS, self._progress_clock.elapsed())
        progress = elapsed / max(1, self.DISPLAY_MS)
        if progress < 0.88:
            lead = progress / 0.88
            eased = (lead * lead * (3.0 - 2.0 * lead)) * 0.96
        else:
            tail = (progress - 0.88) / 0.12
            eased = 0.96 + (tail * tail * (3.0 - 2.0 * tail)) * 0.04

        self._progress.setValue(int(eased * self.PROGRESS_MAX))

        if elapsed >= self.DISPLAY_MS:
            self._finish()

    def _update_progress_style(self):
        self._progress.setStyleSheet(INTRO_SPLASH_THEME["progress_stylesheet"])

    def _finish(self):
        if self._timer.isActive():
            self._timer.stop()
        self._progress.setValue(self.PROGRESS_MAX)
        if self._movie is not None:
            self._movie.stop()
        if self._main_window is None:
            self._main_window = self._launch_callback()
        self.close()
