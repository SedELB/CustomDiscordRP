import io
import json
import os
from PIL import Image
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGraphicsOpacityEffect,
)
import styles
import qt_utils
import qt_net
import startup
import chrome
import discord_user
import profile_editor

app_data = {
    "clientId": "1482109796915220491",
    "profiles": []
}


def load_data():
    global app_data
    if os.path.exists('config.json'):
        with open('config.json', 'r', encoding='utf-8') as f:
            app_data = json.load(f)


def save_data():
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(app_data, f, indent=4)


def get_data():
    return app_data


load_data()


def _mono_label(text, size=None, bold=False, muted=False, parent=None):
    label = QLabel(text, parent)
    font = label.font()
    if size:
        font.setPointSize(size)
    font.setBold(bold)
    label.setFont(font)
    if muted:
        label.setProperty("muted", True)
    return label


class ProfileRow(qt_utils.HoverColorMixin, QFrame):
    def __init__(self, profile, window):
        super().__init__()
        self.profile = profile
        self.main_window = window
        self.setObjectName("row")
        self.init_hover(styles.ROW_BG, styles.ROW_HOVER, radius=8)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(76)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(12)

        avatar = QLabel()
        avatar.setPixmap(qt_utils.avatar_pixmap(profile, 44))
        avatar.setFixedSize(44, 44)
        lay.addWidget(avatar)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.addStretch()
        title = _mono_label(profile.get("profileTitle", "Untitled"), size=11, bold=True)
        text_col.addWidget(title)
        subtitle = _mono_label(self._subtitle(), size=9, muted=True)
        text_col.addWidget(subtitle)
        text_col.addStretch()
        lay.addLayout(text_col, stretch=1)

        self.switch = qt_utils.Switch(profile.get("enabled", True), self, on_change=self._toggle)
        self.switch.setToolTip("Enable this profile")
        lay.addWidget(self.switch, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addSpacing(4)

        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("kind", "outline")
        edit_btn.setProperty("compact", True)
        edit_btn.setFixedHeight(34)
        edit_btn.setMinimumWidth(64)
        edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_btn.clicked.connect(lambda: self.main_window.open_editor(self.profile))
        lay.addWidget(edit_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("kind", "danger-ghost")
        delete_btn.setProperty("compact", True)
        delete_btn.setFixedHeight(34)
        delete_btn.setMinimumWidth(72)
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.clicked.connect(self._delete)
        lay.addWidget(delete_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    def _subtitle(self):
        parts = []
        if self.profile.get("targetExe"):
            parts.append(self.profile["targetExe"])
        if self.profile.get("details"):
            parts.append(self.profile["details"])
        return "  •  ".join(parts) if parts else "No executable set"

    def _toggle(self, checked):
        self.profile["enabled"] = checked
        save_data()

    def _delete(self):
        answer = QMessageBox.question(
            self.main_window, "Delete profile",
            f"Delete “{self.profile.get('profileTitle', 'Untitled')}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            if self.profile in app_data["profiles"]:
                app_data["profiles"].remove(self.profile)
                save_data()
            self.main_window.refresh_profiles()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            if not isinstance(child, (QPushButton, qt_utils.Switch)):
                self.main_window.open_editor(self.profile)
        super().mouseReleaseEvent(event)


class IdentityView(QFrame):
    # Avatar + username + connection status for the logged-in Discord account.
    def __init__(self):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        col = QVBoxLayout()
        col.setSpacing(0)
        col.addStretch()
        self.name_lbl = _mono_label("Not connected", size=10, bold=True)
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_lbl = _mono_label("Disconnected from Discord", size=8, muted=True)
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        col.addWidget(self.name_lbl)
        col.addWidget(self.status_lbl)
        col.addStretch()
        lay.addLayout(col)

        self.avatar = QLabel()
        self.avatar.setFixedSize(34, 34)
        self._generic = qt_utils.crisp_from_pil(qt_utils.discord_avatar_pil(120), 34, radius=17)
        self.avatar.setPixmap(self._generic)
        lay.addWidget(self.avatar, alignment=Qt.AlignmentFlag.AlignVCenter)

    def set_identity(self, connected, name):
        if connected:
            self.name_lbl.setText(name or "Discord user")
            self.status_lbl.setText("Connected to Discord")
            self.status_lbl.setStyleSheet(f"color: {styles.SUCCESS};")
        else:
            self.name_lbl.setText(name or "Not connected")
            self.status_lbl.setText("Disconnected from Discord")
            self.status_lbl.setStyleSheet(f"color: {styles.TEXT_MUTED};")

    def set_avatar(self, pixmap):
        self.avatar.setPixmap(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CustomRP")
        self.setWindowIcon(qt_utils.app_icon())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(960, 640)
        self.setMinimumSize(720, 480)
        self._editors = []
        self._maximized = False
        self._normal_geometry = None
        self._net = qt_net.Net(self)
        self._discord_user = None
        self._avatar_url = None
        self.discord_avatar_pixmap = None   # raw square avatar QPixmap (for editors)
        self.discord_username = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.titlebar = chrome.TitleBar(self)
        root.addWidget(self.titlebar)
        root.addWidget(self._build_content(), stretch=1)

        self.statusbar = chrome.StatusBar(self._on_startup_toggle, startup.is_enabled())
        root.addWidget(self.statusbar)

        # expose the controls main.py and the rest of the app expect
        self.power_button = self.statusbar.power_button
        self.status_label = self.statusbar.status_label
        self.status_detail = self.statusbar.status_detail
        self.startup_switch = self.statusbar.startup_switch
        self.pulse = self.statusbar.pulse

        self._grips = chrome.ResizeGrips(self)

        self.refresh_profiles()
        self.update_power_visual(False)

    # --- content -------------------------------------------------------------
    def _build_content(self):
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(32, 22, 32, 18)
        lay.setSpacing(16)

        # Heading: title + count badge (subtitle beneath) on the left,
        # the Discord identity on the right.
        top = QHBoxLayout()
        top.setSpacing(12)
        head_col = QVBoxLayout()
        head_col.setSpacing(2)
        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(_mono_label("Your profiles", size=15, bold=True))
        self.count_chip = QLabel("0")
        self.count_chip.setObjectName("countChip")
        header.addWidget(self.count_chip, alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()
        head_col.addLayout(header)
        head_col.addWidget(_mono_label("Manage your Rich Presence profiles per app", size=9, muted=True))
        top.addLayout(head_col, stretch=1)
        self.identity_view = IdentityView()
        top.addWidget(self.identity_view, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(top)

        # Toolbar: search (flex) + new profile
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("Search profiles…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedHeight(36)
        self.search.textChanged.connect(lambda _t: self.refresh_profiles(animate=False))
        toolbar.addWidget(self.search, stretch=1)

        new_btn = QPushButton("+  New profile")
        new_btn.setFixedHeight(36)
        new_btn.setMinimumWidth(140)
        new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        new_btn.clicked.connect(lambda: self.open_editor(None))
        toolbar.addWidget(new_btn)
        lay.addLayout(toolbar)

        scroll = qt_utils.SmoothScrollArea()
        scroll.setWidgetResizable(True)
        self.list_host = QWidget()
        self.list_lay = QVBoxLayout(self.list_host)
        self.list_lay.setContentsMargins(0, 0, 6, 0)
        self.list_lay.setSpacing(8)
        self.list_lay.addStretch()
        scroll.setWidget(self.list_host)
        lay.addWidget(scroll, stretch=1)
        return content

    # --- frameless window controls -------------------------------------------
    def is_maximized(self):
        return self._maximized

    def toggle_max_restore(self):
        if self._maximized:
            self._maximized = False
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
        else:
            self._normal_geometry = self.geometry()
            self._maximized = True
            screen = self.screen() or QApplication.primaryScreen()
            if screen is not None:
                self.setGeometry(screen.availableGeometry())
        self.titlebar.set_maximized(self._maximized)
        self._grips.set_visible(not self._maximized)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_grips"):
            self._grips.reposition()

    def _apply_win11_corners(self):
        # Best-effort: ask DWM to round the window corners on Windows 11.
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = int(self.winId())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            value = ctypes.c_int(DWMWCP_ROUND)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd), DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(value), ctypes.sizeof(value),
            )
        except Exception:
            pass

    # --- profile list --------------------------------------------------------
    def refresh_profiles(self, animate=True):
        while self.list_lay.count() > 1:
            item = self.list_lay.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        profiles = app_data.get("profiles", [])
        self.count_chip.setText(str(len(profiles)))

        needle = self.search.text().strip().lower() if hasattr(self, "search") else ""
        if needle:
            profiles = [p for p in profiles if self._matches(p, needle)]

        if not profiles:
            empty = QWidget()
            empty_lay = QVBoxLayout(empty)
            empty_lay.setContentsMargins(0, 70, 0, 0)
            empty_lay.setSpacing(6)
            if needle:
                msg = _mono_label(f"No profiles match “{self.search.text().strip()}”", size=10, muted=True)
                msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                empty_lay.addWidget(msg)
            else:
                title = _mono_label("No profiles yet", size=12, bold=True)
                title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                empty_lay.addWidget(title)
                sub = _mono_label("Create one to start sharing your Rich Presence.", size=9, muted=True)
                sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                empty_lay.addWidget(sub)
                empty_lay.addSpacing(10)
                btn_row = QHBoxLayout()
                btn_row.addStretch()
                btn = QPushButton("+  New profile")
                btn.setFixedSize(170, 40)
                btn.clicked.connect(lambda: self.open_editor(None))
                btn_row.addWidget(btn)
                btn_row.addStretch()
                empty_lay.addLayout(btn_row)
            self.list_lay.insertWidget(0, empty)
            return

        for idx, profile in enumerate(profiles):
            row = ProfileRow(profile, self)
            self.list_lay.insertWidget(idx, row)
            if animate:
                self._fade_in(row, delay=idx * 35)

    @staticmethod
    def _fade_in(row, delay=0):
        effect = QGraphicsOpacityEffect(row)
        effect.setOpacity(0.0)
        row.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", row)
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: row.setGraphicsEffect(None))
        QTimer.singleShot(delay, anim.start)

    @staticmethod
    def _matches(profile, needle):
        haystack = " ".join(
            str(profile.get(k, "")) for k in ("profileTitle", "targetExe", "details", "state", "statusName")
        ).lower()
        return needle in haystack

    # --- editor --------------------------------------------------------------
    def open_editor(self, profile=None):
        editor = profile_editor.ProfileEditor(self, profile, self._on_editor_save)
        self._editors.append(editor)
        editor.destroyed.connect(lambda: self._editors.remove(editor) if editor in self._editors else None)
        editor.show()

    def _on_editor_save(self, profile, is_new):
        if is_new:
            app_data["profiles"].append(profile)
        save_data()
        self.refresh_profiles()

    # --- live status ---------------------------------------------------------
    def update_power_visual(self, running):
        if running:
            self.power_button.setText("Stop monitoring")
            self.power_button.setProperty("kind", "danger")
            self.status_label.setText("Idle")
            self.status_detail.setText("Watching for profiled apps…")
            self.pulse.set_state("idle")
        else:
            self.power_button.setText("Start monitoring")
            self.power_button.setProperty("kind", "success")
            self.status_label.setText("Stopped")
            self.status_detail.setText("Monitoring is off")
            self.pulse.set_state("off")
        self.power_button.style().unpolish(self.power_button)
        self.power_button.style().polish(self.power_button)

    def _on_startup_toggle(self, enabled):
        ok = startup.set_enabled(enabled)
        # If the registry write failed, snap the switch back to the real state.
        if not ok or startup.is_enabled() != enabled:
            self.startup_switch.setChecked(startup.is_enabled(), animate=True)

    def report_activity(self, title):
        if title:
            self.status_label.setText("Active")
            self.status_detail.setText(title)
            self.pulse.set_state("active")
        else:
            if self.status_label.text() != "Stopped":
                self.status_label.setText("Idle")
                self.status_detail.setText("Watching for profiled apps…")
                self.pulse.set_state("idle")

    # --- discord identity ----------------------------------------------------
    def report_identity(self, connected, user):
        if connected and user:
            self._discord_user = user
            self.discord_username = discord_user.display_name(user)
        self.identity_view.set_identity(connected, self.discord_username)
        if connected and user:
            url = discord_user.avatar_url(user, 128)
            if url and url != self._avatar_url:
                self._avatar_url = url
                self._net.get(url, self._on_avatar_bytes)

    def _on_avatar_bytes(self, data):
        if not data:
            return
        try:
            img = Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception:
            return
        self.discord_avatar_pixmap = qt_utils.pil_to_pixmap(img)
        self.identity_view.set_avatar(qt_utils.crisp_from_pil(img, 34, radius=17))
        # push the real avatar into any open editors
        for editor in self._editors:
            if hasattr(editor, "apply_discord_avatar"):
                editor.apply_discord_avatar(self.discord_avatar_pixmap, self.discord_username)

    # --- window behaviour ----------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._apply_win11_corners()
        self._grips.reposition()
        qt_utils.animate_open(self)

    def closeEvent(self, event):
        # Hide to tray instead of quitting.
        event.ignore()
        self.hide()
