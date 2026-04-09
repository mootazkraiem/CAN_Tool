import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
_QTWEBENGINE_DIR = Path(os.environ.get("TEMP", str(_PROJECT_ROOT / ".tmp_py"))) / "CANvision_qtwebengine"
_QTWEBENGINE_DIR.mkdir(parents=True, exist_ok=True)
(_QTWEBENGINE_DIR / "cache").mkdir(parents=True, exist_ok=True)
(_QTWEBENGINE_DIR / "userdata").mkdir(parents=True, exist_ok=True)

_PYQT_BIN = Path(r"C:\Users\benkr\AppData\Local\Programs\Python\Python313\Lib\site-packages\PyQt6\Qt6\bin\QtWebEngineProcess.exe")
if _PYQT_BIN.exists():
    os.environ.setdefault("QTWEBENGINEPROCESS_PATH", str(_PYQT_BIN))

os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    " ".join(
        [
            "--disable-gpu-sandbox",
            "--no-sandbox",
            "--disable-features=RendererCodeIntegrity,OutOfProcessRasterization",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-direct-composition",
            f"--user-data-dir={_QTWEBENGINE_DIR / 'userdata'}",
            f"--disk-cache-dir={_QTWEBENGINE_DIR / 'cache'}",
        ]
    ),
)

from ui.intro_splash import IntroSplashScreen
from ui.main_window import MainWindow, configure_opengl
from ui.qt_compat import QApplication, QFont, Qt


def _app_font() -> QFont:
    font = QFont("Orbitron", 12)
    if not font.exactMatch():
        font = QFont("Bahnschrift", 12)
    return font


def main() -> int:
    configure_opengl()

    if hasattr(QApplication, "setAttribute"):
        try:
            use_pixmaps = Qt.ApplicationAttribute.AA_UseHighDpiPixmaps
        except AttributeError:
            use_pixmaps = getattr(Qt, "AA_UseHighDpiPixmaps", None)
        if use_pixmaps is not None:
            QApplication.setAttribute(use_pixmaps, True)

    app = QApplication(sys.argv)
    app.setFont(_app_font())

    windows = {"main": None}

    def build_main():
        if windows["main"] is None:
            windows["main"] = MainWindow()
        return windows["main"]

    def launch_main():
        window = build_main()
        window.showMaximized()
        window.raise_()
        window.activateWindow()
        return window

    app.setQuitOnLastWindowClosed(False)
    app._main_window_ref = windows  # type: ignore[attr-defined]
    app._splash_ref = IntroSplashScreen(launch_callback=launch_main, preload_callback=None)  # type: ignore[attr-defined]
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
