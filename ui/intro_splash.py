from pathlib import Path

try:
    from PyQt6.QtCore import QElapsedTimer, QTimer, Qt, QUrl
    from PyQt6.QtGui import QColor, QMovie
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    from PyQt6.QtWidgets import QApplication, QFrame, QGraphicsDropShadowEffect, QLabel, QProgressBar, QVBoxLayout, QWidget
    PYQT6 = True
    HAS_VIDEO = True
except ImportError:
    from PyQt5.QtCore import QElapsedTimer, QTimer, Qt, QUrl
    from PyQt5.QtGui import QColor, QMovie
    try:
        from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
        from PyQt5.QtMultimediaWidgets import QVideoWidget
        QAudioOutput = None
        HAS_VIDEO = True
    except ImportError:
        QMediaContent = None
        QMediaPlayer = None
        QVideoWidget = None
        QAudioOutput = None
        HAS_VIDEO = False
    from PyQt5.QtWidgets import QApplication, QFrame, QGraphicsDropShadowEffect, QLabel, QProgressBar, QVBoxLayout, QWidget
    PYQT6 = False

from .intro_theme import INTRO_SPLASH_THEME, intro_subtitle_font, intro_title_font


class IntroSplashScreen(QWidget):
    DISPLAY_MS = INTRO_SPLASH_THEME["display_ms"]
    TICK_MS = INTRO_SPLASH_THEME["tick_ms"]
    PROGRESS_MAX = INTRO_SPLASH_THEME["progress_max"]
    WIDTH = INTRO_SPLASH_THEME["width"]
    HEIGHT = INTRO_SPLASH_THEME["height"]

    def __init__(self, launch_callback, preload_callback=None):
        super().__init__(None)
        self._launch_callback = launch_callback
        self._preload_callback = preload_callback
        self._main_window = None
        self._movie = None
        self._player = None
        self._audio_output = None
        self._video_widget = None
        self._progress_clock = QElapsedTimer()

        if PYQT6:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.SplashScreen)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_DeleteOnClose, True)

        self._build_ui()
        self._load_media()
        self._center_on_screen()
        self.show()

        if self._movie is not None:
            self._movie.start()
        elif self._player is not None:
            self._player.play()

        self._progress.setRange(0, self.DISPLAY_MS)
        self._progress.setValue(0)
        self._update_progress_style()
        self._progress_clock.start()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_progress)
        self._timer.start(self.TICK_MS)
        self._progress.setRange(0, self.PROGRESS_MAX)
        if self._preload_callback is not None:
            QTimer.singleShot(80, self._preload_main_window)

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
        self._media.setAlignment(Qt.AlignmentFlag.AlignCenter if PYQT6 else Qt.AlignCenter)
        self._media.setStyleSheet(INTRO_SPLASH_THEME["media_stylesheet"])

        self._title = QLabel(INTRO_SPLASH_THEME["title_text"], self._panel)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter if PYQT6 else Qt.AlignCenter)
        self._title.setStyleSheet(f"color: {INTRO_SPLASH_THEME['title_color']};")
        self._title.setFont(intro_title_font())

        self._subtitle = QLabel(INTRO_SPLASH_THEME["subtitle_text"], self._panel)
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter if PYQT6 else Qt.AlignCenter)
        self._subtitle.setStyleSheet(f"color: {INTRO_SPLASH_THEME['subtitle_color']};")
        self._subtitle.setFont(intro_subtitle_font())

        self._status = QLabel(INTRO_SPLASH_THEME["status_text"], self._panel)
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter if PYQT6 else Qt.AlignCenter)
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
        video_candidates = [
            asset_dir / "intro_pyqt.mp4",
            asset_dir / "intro_mpeg4.mp4",
            asset_dir / "intro.mp4",
            asset_dir / "intro_wmv.wmv",
        ]
        for candidate in video_candidates:
            if candidate.exists() and self._try_load_video(candidate):
                return

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

    def _try_load_video(self, path: Path) -> bool:
        if not HAS_VIDEO or QMediaPlayer is None or QVideoWidget is None:
            return False

        panel_layout = self._panel.layout()
        if panel_layout is None:
            return False

        self._video_widget = QVideoWidget(self._panel)
        self._video_widget.setMinimumHeight(INTRO_SPLASH_THEME["media_min_height"])
        self._video_widget.setStyleSheet(INTRO_SPLASH_THEME["media_stylesheet"])
        panel_layout.replaceWidget(self._media, self._video_widget)
        self._media.hide()

        self._player = QMediaPlayer(self)
        if PYQT6:
            self._audio_output = QAudioOutput(self)
            self._audio_output.setVolume(0.0)
            self._player.setAudioOutput(self._audio_output)
            self._player.setVideoOutput(self._video_widget)
            self._player.setSource(QUrl.fromLocalFile(str(path)))
        else:
            self._player.setVideoOutput(self._video_widget)
            self._player.setMedia(QMediaContent(QUrl.fromLocalFile(str(path))))
            self._player.setVolume(0)
        return True

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
        if self._player is not None:
            self._player.stop()
        try:
            self._main_window = self._launch_callback()
            app = QApplication.instance()
            if app is not None:
                app.setQuitOnLastWindowClosed(True)
        except Exception:
            import traceback
            try:
                from PyQt6.QtWidgets import QMessageBox
            except ImportError:
                from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Launch Error", traceback.format_exc())
            return
        self.close()

    def _preload_main_window(self):
        if self._main_window is not None or self._preload_callback is None:
            return
        try:
            self._status.setText("Loading interface...")
            self._main_window = self._preload_callback()
        except Exception:
            self._status.setText(INTRO_SPLASH_THEME["status_text"])
