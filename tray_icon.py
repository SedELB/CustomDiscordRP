# tray_icon.py — Qt system tray with idle/active/error states
from PIL import Image, ImageDraw
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
import qt_utils
import styles

_STATE_COLORS = {
    'idle': styles.TEXT_MUTED,
    'active': styles.ACCENT,
    'error': styles.DANGER,
}


def _state_icon(state):
    color = _STATE_COLORS.get(state, styles.TEXT_MUTED)
    size, ss = 64, qt_utils.SS
    big = size * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rounded_rectangle((0, 0, big - 1, big - 1), radius=big // 4, fill=styles.BG_TERTIARY)
    margin = big // 5
    dc.ellipse((margin, margin, big - margin, big - margin), fill=color)
    inner = int(big * 0.36)
    dc.ellipse((inner, inner, big - inner, big - inner), fill=styles.BG_TERTIARY)
    return QIcon(qt_utils.pil_to_pixmap(img.resize((size, size), Image.LANCZOS)))


class Tray(QSystemTrayIcon):
    def __init__(self, window, on_quit, parent=None):
        super().__init__(parent)
        self.window = window
        self.setIcon(_state_icon('idle'))
        self.setToolTip("CustomRP")

        menu = QMenu()
        open_action = QAction("Open CustomRP", menu)
        open_action.triggered.connect(self._show_window)
        menu.addAction(open_action)

        self.status_action = QAction("Stopped", menu)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)

        menu.addSeparator()
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(on_quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def set_state(self, state, tooltip=None):
        self.setIcon(_state_icon(state))
        if tooltip:
            self.setToolTip(tooltip)
            self.status_action.setText(tooltip.replace("CustomRP — ", ""))
