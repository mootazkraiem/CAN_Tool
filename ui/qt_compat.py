try:
    from PyQt6.QtCore import QEasingCurve, QPoint, QPointF, QRect, QRectF, QSize, Qt, QPropertyAnimation, QTimer, pyqtProperty, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QLinearGradient, QMouseEvent, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient, QSurfaceFormat
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QMainWindow, QPushButton, QWidget

    PYQT6 = True
except ImportError:
    from PyQt5.QtCore import QEasingCurve, QPoint, QPointF, QRect, QRectF, QSize, Qt, QPropertyAnimation, QTimer, pyqtProperty, pyqtSignal
    from PyQt5.QtGui import QColor, QFont, QLinearGradient, QMouseEvent, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient, QSurfaceFormat
    from PyQt5.QtWidgets import QApplication, QGraphicsDropShadowEffect, QMainWindow, QPushButton, QOpenGLWidget, QWidget

    PYQT6 = False


def align_center():
    return Qt.AlignmentFlag.AlignCenter if PYQT6 else Qt.AlignCenter


def align_left_vcenter():
    if PYQT6:
        return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    return Qt.AlignLeft | Qt.AlignVCenter


def no_pen():
    return Qt.PenStyle.NoPen if PYQT6 else Qt.NoPen


def no_brush():
    return Qt.BrushStyle.NoBrush if PYQT6 else Qt.NoBrush


def left_button():
    return Qt.MouseButton.LeftButton if PYQT6 else Qt.LeftButton


def enter_key():
    return Qt.Key.Key_Return if PYQT6 else Qt.Key_Return


def widget_attribute_translucent():
    return Qt.WidgetAttribute.WA_TranslucentBackground if PYQT6 else Qt.WA_TranslucentBackground


def focus_policy_no():
    return Qt.FocusPolicy.NoFocus if PYQT6 else Qt.NoFocus


def pointing_hand_cursor():
    return Qt.CursorShape.PointingHandCursor if PYQT6 else Qt.PointingHandCursor


def easing_out_cubic():
    return QEasingCurve.Type.OutCubic if PYQT6 else QEasingCurve.OutCubic


def mouse_point(event: QMouseEvent) -> QPointF:
    if hasattr(event, "position"):
        return event.position()
    return event.localPos()
