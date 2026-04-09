from __future__ import annotations

from pathlib import Path

from .qt_compat import QWidget, pyqtProperty, pyqtSignal

try:
    from PyQt6.QtCore import QObject, QPointF, QRectF, QTimer, QUrl
    from PyQt6.QtGui import QColor
    from PyQt6.QtQuickWidgets import QQuickWidget
except ImportError:
    from PyQt5.QtCore import QObject, QPointF, QRectF, QTimer, QUrl
    from PyQt5.QtGui import QColor
    from PyQt5.QtQuickWidgets import QQuickWidget


def _preferred_model_path() -> Path:
    candidates = [
        Path("assets/toyota_supra_mk4_a80/scene.gltf"),
        Path("assets/toyota_supra_mk4_a80.glb"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError("No supported sports-car model was found in assets/")


def _background_image_path() -> Path:
    candidates = sorted(Path("assets").glob("ChatGPT Image*.png"))
    if candidates:
        return candidates[0].resolve()
    raise FileNotFoundError("Background image matching 'ChatGPT Image*.png' was not found in assets/")


class GarageSceneBridge(QObject):
    modeChanged = pyqtSignal()
    cameraChanged = pyqtSignal()
    modelUrlChanged = pyqtSignal()
    backgroundUrlChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode_name = "Dashboard"
        self._camera_yaw = 28.0
        self._camera_pitch = 12.0
        self._model_url = QUrl.fromLocalFile(str(_preferred_model_path())).toString()
        self._background_url = QUrl.fromLocalFile(str(_background_image_path())).toString()

    def get_mode_name(self) -> str:
        return self._mode_name

    def set_mode_name(self, value: str):
        if self._mode_name == value:
            return
        self._mode_name = value
        self.modeChanged.emit()

    def get_camera_yaw(self) -> float:
        return self._camera_yaw

    def set_camera_yaw(self, value: float):
        value = float(value)
        if abs(self._camera_yaw - value) < 0.0001:
            return
        self._camera_yaw = value
        self.cameraChanged.emit()

    def get_camera_pitch(self) -> float:
        return self._camera_pitch

    def set_camera_pitch(self, value: float):
        value = float(value)
        if abs(self._camera_pitch - value) < 0.0001:
            return
        self._camera_pitch = value
        self.cameraChanged.emit()

    def get_model_url(self) -> str:
        return self._model_url

    def get_background_url(self) -> str:
        return self._background_url

    modeName = pyqtProperty(str, get_mode_name, set_mode_name, notify=modeChanged)
    cameraYaw = pyqtProperty(float, get_camera_yaw, set_camera_yaw, notify=cameraChanged)
    cameraPitch = pyqtProperty(float, get_camera_pitch, set_camera_pitch, notify=cameraChanged)
    modelUrl = pyqtProperty(str, get_model_url, notify=modelUrlChanged)
    backgroundUrl = pyqtProperty(str, get_background_url, notify=backgroundUrlChanged)


class GarageSceneWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setStyleSheet("background:#03070b; border:none;")

        self.bridge = GarageSceneBridge(self)
        self.view = QQuickWidget(self)
        self.view.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView if hasattr(QQuickWidget, "ResizeMode") else QQuickWidget.SizeRootObjectToView)
        try:
            self.view.setClearColor(QColor(0, 0, 0, 0))
        except Exception:
            pass
        self.view.rootContext().setContextProperty("garageSceneBridge", self.bridge)
        qml_path = Path(__file__).resolve().parent / "garage_scene.qml"
        self.view.setSource(QUrl.fromLocalFile(str(qml_path)))

        self._root = None
        self._camera_yaw = 28.0
        self._camera_pitch = 12.0

        self._sync_timer = QTimer(self)
        self._sync_timer.timeout.connect(self._sync_from_qml)
        self._sync_timer.start(16)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.setGeometry(self.rect())

    def set_mode(self, mode_name: str):
        self.bridge.set_mode_name(mode_name)
        if self._root is not None:
            self._root.setProperty("modeName", mode_name)

    def _sync_from_qml(self):
        if self._root is None:
            self._root = self.view.rootObject()
            if self._root is None:
                return
        yaw = self._root.property("currentYaw")
        pitch = self._root.property("currentPitch")
        if yaw is not None:
            self._camera_yaw = float(yaw)
            self.bridge.set_camera_yaw(self._camera_yaw)
        if pitch is not None:
            self._camera_pitch = float(pitch)
            self.bridge.set_camera_pitch(self._camera_pitch)

    def part_positions(self) -> dict[str, QPointF]:
        scale = min(self.width(), self.height()) * 0.22
        cx = self.width() * 0.5
        cy = self.height() * 0.57 - self._camera_pitch * 3.2

        import math

        def project(point: tuple[float, float, float]) -> QPointF:
            x, y, z = point
            yaw = math.radians(self._camera_yaw)
            xr = x * math.cos(yaw) - z * math.sin(yaw)
            zr = x * math.sin(yaw) + z * math.cos(yaw)
            depth = 8.8 + zr * 0.42
            px = cx + xr * scale / depth
            py = cy - y * scale / depth
            return QPointF(px, py)

        return {
            "engine": project((0.0, 1.25, 1.85)),
            "roof": project((0.0, 2.05, 0.0)),
            "front_left_wheel": project((-1.85, 0.55, 1.92)),
            "front_right_wheel": project((1.85, 0.55, 1.92)),
            "rear_left_wheel": project((-1.85, 0.55, -1.92)),
            "rear_right_wheel": project((1.85, 0.55, -1.92)),
        }

    def interactive_region(self) -> QRectF:
        return QRectF(self.rect())
