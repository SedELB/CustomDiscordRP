# chrome.py — custom window chrome for the frameless main window:
# draggable titlebar with window controls, an animated status pulse dot,
# the bottom statusbar, and edge grips that make a frameless window resizable.
from PyQt6.QtCore import Qt, QSize, QRectF, QPointF, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QCursor
from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
)
import styles
import qt_utils

DRAG_THRESHOLD = 4


def _label(text, size=None, bold=False, muted=False):
    lbl = QLabel(text)
    font = lbl.font()
    if size:
        font.setPointSize(size)
    font.setBold(bold)
    lbl.setFont(font)
    if muted:
        lbl.setProperty("muted", True)
    return lbl


# --- window control buttons --------------------------------------------------
class _WinButton(QPushButton):
    """Flat 46x36 button that paints a crisp line glyph (min/max/close) over the
    stylesheet-painted background."""
    def __init__(self, glyph, parent=None):
        super().__init__(parent)
        self._glyph = glyph
        self._restore = False  # max button toggles to a "restore" icon
        self.setProperty("kind", "winClose" if glyph == "close" else "win")
        self.setFixedSize(46, 36)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def setRestore(self, restore):
        self._restore = bool(restore)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)  # stylesheet paints the (hover) background
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#ffffff") if self.underMouse() else QColor(styles.ICON_DEFAULT)
        pen = QPen(color, 1.1)
        p.setPen(pen)
        cx, cy = self.width() / 2, self.height() / 2
        r = 5  # glyph half-size

        if self._glyph == "min":
            p.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        elif self._glyph == "max":
            if self._restore:  # two overlapping squares
                p.drawRect(QRectF(cx - r + 2, cy - r, 2 * r - 2, 2 * r - 2))
                p.setBrush(QBrush(self._bg_for_restore()))
                p.drawRect(QRectF(cx - r, cy - r + 2, 2 * r - 2, 2 * r - 2))
            else:
                p.drawRect(QRectF(cx - r, cy - r, 2 * r, 2 * r))
        else:  # close
            p.drawLine(QPointF(cx - r, cy - r), QPointF(cx + r, cy + r))
            p.drawLine(QPointF(cx - r, cy + r), QPointF(cx + r, cy - r))
        p.end()

    def _bg_for_restore(self):
        return QColor("#36373d") if self.underMouse() else QColor(styles.BG_TITLEBAR)


class TitleBar(QFrame):
    """Custom draggable titlebar with window controls for the frameless window."""
    def __init__(self, window):
        super().__init__()
        self._window = window
        self.setObjectName("titlebar")
        self.setFixedHeight(36)
        self._press_pos = None
        self._dragging = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 0, 0)
        lay.setSpacing(8)

        logo = QLabel()
        logo.setPixmap(qt_utils.logo_pixmap(16))
        logo.setFixedSize(16, 16)
        lay.addWidget(logo)

        brand = _label("CustomRP", size=9, bold=True)
        brand.setStyleSheet(f"color: {styles.TEXT_HEADING};")
        lay.addWidget(brand)
        lay.addStretch()

        self.btn_min = _WinButton("min")
        self.btn_min.clicked.connect(window.showMinimized)
        self.btn_max = _WinButton("max")
        self.btn_max.clicked.connect(window.toggle_max_restore)
        self.btn_close = _WinButton("close")
        self.btn_close.clicked.connect(window.close)
        for b in (self.btn_min, self.btn_max, self.btn_close):
            lay.addWidget(b)

    def set_maximized(self, maximized):
        self.btn_max.setRestore(maximized)

    # drag handling — defer startSystemMove until the cursor actually moves so
    # double-clicks (maximize toggle) still register.
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos is not None and not self._dragging:
            moved = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
            if moved >= DRAG_THRESHOLD:
                self._dragging = True
                handle = self._window.windowHandle()
                if handle is not None:
                    if self._window.is_maximized():
                        self._window.toggle_max_restore()  # restore before dragging
                    handle.startSystemMove()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._press_pos = None
        self._dragging = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._window.toggle_max_restore()
        super().mouseDoubleClickEvent(event)


# --- animated status pulse dot ----------------------------------------------
class PulseDot(QWidget):
    """Status dot with an expanding/fading ring when running; red and static when off."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(22, 22))
        self._phase = 0.0
        self._color = QColor(styles.DANGER)
        self._running = False
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(1600)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_phase)

    def _on_phase(self, value):
        self._phase = float(value)
        self.update()

    def set_state(self, state):
        # state: "off" (stopped), "idle" (watching), "active" (presence shown)
        if state == "off":
            self._color = QColor(styles.DANGER)
            self._set_running(False)
        elif state == "active":
            self._color = QColor(styles.SUCCESS)
            self._set_running(True)
        else:  # idle
            self._color = QColor(styles.DOT_IDLE)
            self._set_running(True)
        self.update()

    def _set_running(self, running):
        if running == self._running:
            return
        self._running = running
        if running:
            self._anim.start()
        else:
            self._anim.stop()
            self._phase = 0.0

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        core = 5.0  # core dot radius

        if self._running:
            ring_r = core + self._phase * 6.0
            alpha = int(150 * (1.0 - self._phase))
            ring = QColor(self._color)
            ring.setAlpha(max(0, alpha))
            p.setPen(QPen(ring, 2.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._color))
        p.drawEllipse(QRectF(cx - core, cy - core, core * 2, core * 2))
        p.end()


# --- bottom statusbar --------------------------------------------------------
class StatusBar(QFrame):
    def __init__(self, on_startup_toggle, startup_enabled, version="v3.2.0"):
        super().__init__()
        self.setObjectName("statusBar")
        self.setFixedHeight(56)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 16, 0)
        lay.setSpacing(10)

        # left: pulse + status text
        self.pulse = PulseDot()
        lay.addWidget(self.pulse, alignment=Qt.AlignmentFlag.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.addStretch()
        self.status_label = _label("Stopped", size=10, bold=True)
        self.status_label.setProperty("role", "statusText")
        self.status_detail = _label("Monitoring is off", size=8, muted=True)
        text_col.addWidget(self.status_label)
        text_col.addWidget(self.status_detail)
        text_col.addStretch()
        lay.addLayout(text_col)
        lay.addStretch()

        # right: startup toggle + monitor button + version
        startup_lbl = _label("Run on startup", size=9, muted=True)
        startup_lbl.setToolTip("Launch CustomRP in the tray when Windows starts")
        lay.addWidget(startup_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.startup_switch = qt_utils.Switch(startup_enabled, on_change=on_startup_toggle)
        self.startup_switch.setToolTip("Launch CustomRP automatically when Windows starts")
        lay.addWidget(self.startup_switch, alignment=Qt.AlignmentFlag.AlignVCenter)

        lay.addSpacing(8)
        self.power_button = QPushButton("Start monitoring")
        self.power_button.setProperty("kind", "success")
        self.power_button.setProperty("compact", True)
        self.power_button.setFixedHeight(36)
        self.power_button.setMinimumWidth(168)
        self.power_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        lay.addWidget(self.power_button, alignment=Qt.AlignmentFlag.AlignVCenter)

        lay.addSpacing(4)
        version_lbl = _label(version, size=8)
        version_lbl.setStyleSheet(f"color: {styles.TEXT_FAINT};")
        lay.addWidget(version_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)


# --- frameless resize grips --------------------------------------------------
class _Grip(QWidget):
    def __init__(self, window, edges, cursor_shape):
        super().__init__(window)
        self._window = window
        self._edges = edges
        self.setCursor(QCursor(cursor_shape))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._window.windowHandle()
            if handle is not None and not self._window.is_maximized():
                handle.startSystemResize(self._edges)


class ResizeGrips:
    """Eight edge/corner overlay widgets that make a frameless window resizable."""
    M = 6   # edge thickness
    C = 12  # corner size

    def __init__(self, window):
        self._window = window
        E = Qt.Edge
        self.grips = {
            "top":    _Grip(window, E.TopEdge, Qt.CursorShape.SizeVerCursor),
            "bottom": _Grip(window, E.BottomEdge, Qt.CursorShape.SizeVerCursor),
            "left":   _Grip(window, E.LeftEdge, Qt.CursorShape.SizeHorCursor),
            "right":  _Grip(window, E.RightEdge, Qt.CursorShape.SizeHorCursor),
            "tl":     _Grip(window, E.TopEdge | E.LeftEdge, Qt.CursorShape.SizeFDiagCursor),
            "tr":     _Grip(window, E.TopEdge | E.RightEdge, Qt.CursorShape.SizeBDiagCursor),
            "bl":     _Grip(window, E.BottomEdge | E.LeftEdge, Qt.CursorShape.SizeBDiagCursor),
            "br":     _Grip(window, E.BottomEdge | E.RightEdge, Qt.CursorShape.SizeFDiagCursor),
        }

    def reposition(self):
        w, h = self._window.width(), self._window.height()
        M, C = self.M, self.C
        g = self.grips
        g["top"].setGeometry(C, 0, w - 2 * C, M)
        g["bottom"].setGeometry(C, h - M, w - 2 * C, M)
        g["left"].setGeometry(0, C, M, h - 2 * C)
        g["right"].setGeometry(w - M, C, M, h - 2 * C)
        g["tl"].setGeometry(0, 0, C, C)
        g["tr"].setGeometry(w - C, 0, C, C)
        g["bl"].setGeometry(0, h - C, C, C)
        g["br"].setGeometry(w - C, h - C, C, C)
        for grip in g.values():
            grip.raise_()

    def set_visible(self, visible):
        for grip in self.grips.values():
            grip.setVisible(visible)
