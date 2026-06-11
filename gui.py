import json
import os
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGraphicsOpacityEffect,
)
import styles
import qt_utils
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


class ProfileRow(QFrame, qt_utils.HoverColorMixin):
    def __init__(self, profile, window):
        super().__init__()
        self.profile = profile
        self.window = window
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
        text_col.setSpacing(2)
        title = _mono_label(profile.get("profileTitle", "Untitled"), size=11, bold=True)
        text_col.addWidget(title)
        subtitle = _mono_label(self._subtitle(), size=9, muted=True)
        text_col.addWidget(subtitle)
        lay.addLayout(text_col, stretch=1)

        self.switch = qt_utils.Switch(profile.get("enabled", True), self, on_change=self._toggle)
        lay.addWidget(self.switch)

        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("kind", "outline")
        edit_btn.setFixedHeight(30)
        edit_btn.clicked.connect(lambda: self.window.open_editor(self.profile))
        lay.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("kind", "danger-ghost")
        delete_btn.setFixedHeight(30)
        delete_btn.clicked.connect(self._delete)
        lay.addWidget(delete_btn)

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
            self.window, "Delete profile",
            f"Delete “{self.profile.get('profileTitle', 'Untitled')}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            if self.profile in app_data["profiles"]:
                app_data["profiles"].remove(self.profile)
                save_data()
            self.window.refresh_profiles()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            if not isinstance(child, (QPushButton, qt_utils.Switch)):
                self.window.open_editor(self.profile)
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CustomRP")
        self.setWindowIcon(qt_utils.app_icon())
        self.resize(960, 640)
        self.setMinimumSize(840, 540)
        self._editors = []

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), stretch=1)

        self.refresh_profiles()
        self.update_power_visual(False)

    # --- sidebar -------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(16, 20, 16, 14)
        lay.setSpacing(0)

        brand_row = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(qt_utils.logo_pixmap(28))
        logo.setFixedSize(28, 28)
        brand_row.addWidget(logo)
        brand = _mono_label("CustomRP", size=13, bold=True)
        brand_row.addWidget(brand)
        brand_row.addStretch()
        lay.addLayout(brand_row)

        tagline = _mono_label("Per-app Rich Presence", size=8, muted=True)
        lay.addSpacing(2)
        lay.addWidget(tagline)
        lay.addSpacing(18)

        new_btn = QPushButton("+  New Profile")
        new_btn.setFixedHeight(40)
        new_btn.clicked.connect(lambda: self.open_editor(None))
        lay.addWidget(new_btn)

        lay.addStretch()

        panel = QFrame()
        panel.setObjectName("darkPanel")
        panel_lay = QVBoxLayout(panel)
        panel_lay.setContentsMargins(14, 12, 14, 12)
        panel_lay.setSpacing(4)

        status_row = QHBoxLayout()
        self.status_dot = _mono_label("●", size=9)
        status_row.addWidget(self.status_dot)
        self.status_label = _mono_label("Stopped", size=10, bold=True)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        panel_lay.addLayout(status_row)

        self.status_detail = _mono_label("Monitoring is off", size=8, muted=True)
        self.status_detail.setWordWrap(True)
        panel_lay.addWidget(self.status_detail)
        panel_lay.addSpacing(6)

        self.power_button = QPushButton("Start monitoring")
        self.power_button.setProperty("kind", "success")
        self.power_button.setFixedHeight(36)
        panel_lay.addWidget(self.power_button)

        lay.addWidget(panel)
        version = _mono_label("CustomRP  ·  v2.0", size=8, muted=True)
        version.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(8)
        lay.addWidget(version)
        return sidebar

    # --- content -------------------------------------------------------------
    def _build_content(self):
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(28, 22, 28, 20)
        lay.setSpacing(14)

        header = QHBoxLayout()
        header.addWidget(_mono_label("Your Profiles", size=14, bold=True))
        self.count_chip = QLabel("0")
        self.count_chip.setObjectName("countChip")
        header.addWidget(self.count_chip)
        header.addStretch()

        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("Search profiles…")
        self.search.setFixedWidth(230)
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _t: self.refresh_profiles(animate=False))
        header.addWidget(self.search)
        lay.addLayout(header)

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
                btn = QPushButton("+  New Profile")
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
            self.status_dot.setStyleSheet(f"color: {styles.ACCENT};")
            self.status_detail.setText("Watching for profiled apps…")
        else:
            self.power_button.setText("Start monitoring")
            self.power_button.setProperty("kind", "success")
            self.status_label.setText("Stopped")
            self.status_dot.setStyleSheet(f"color: {styles.TEXT_MUTED};")
            self.status_detail.setText("Monitoring is off")
        self.power_button.style().unpolish(self.power_button)
        self.power_button.style().polish(self.power_button)

    def report_activity(self, title):
        if title:
            self.status_label.setText("Active")
            self.status_dot.setStyleSheet(f"color: {styles.SUCCESS};")
            self.status_detail.setText(title)
        else:
            if self.status_label.text() != "Stopped":
                self.status_label.setText("Idle")
                self.status_dot.setStyleSheet(f"color: {styles.ACCENT};")
                self.status_detail.setText("Watching for profiled apps…")

    # --- window behaviour ----------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        qt_utils.animate_open(self)

    def closeEvent(self, event):
        # Hide to tray instead of quitting.
        event.ignore()
        self.hide()
