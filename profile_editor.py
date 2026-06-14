import io
import os
import uuid
from PIL import Image
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QCursor, QPainter, QColor, QBrush
from PyQt6.QtWidgets import (
    QDialog, QWidget, QFrame, QLabel, QPushButton, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QScrollArea, QMessageBox,
)
import styles
import qt_utils
import qt_net
import image_picker
import launcher_inject

MAX_FIELD = 128


def _label(text, size=None, bold=False, muted=False):
    label = QLabel(text)
    font = label.font()
    if size:
        font.setPointSize(size)
    font.setBold(bold)
    label.setFont(font)
    if muted:
        label.setProperty("muted", True)
    return label


def _hint(text):
    hint = _label(text, size=8, muted=True)
    hint.setWordWrap(True)
    return hint


def _field(placeholder, value=""):
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setText(value)
    return edit


def _card_edit(placeholder, value="", point_size=10, bold=False):
    # Inline edit that lives directly on the presence card.
    edit = QLineEdit()
    edit.setProperty("cardEdit", True)
    edit.setPlaceholderText(placeholder)
    edit.setText(value)
    edit.setMaxLength(MAX_FIELD)
    font = edit.font()
    font.setPointSize(point_size)
    font.setBold(bold)
    edit.setFont(font)
    return edit


class _AvatarDot(QWidget):
    # Circular avatar with a Discord-style online dot, drawn over the banner edge.
    def __init__(self, pixmap, size=64, parent=None):
        super().__init__(parent)
        self._pix = pixmap
        self._size = size
        self.setFixedSize(size + 8, size + 8)

    def setPixmap(self, pixmap):
        self._pix = pixmap
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # ring matching the card background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(styles.CARD_BG)))
        p.drawEllipse(0, 0, self._size + 8, self._size + 8)
        path_rect = self.rect().adjusted(4, 4, -4, -4)
        p.setBrush(QBrush(QColor(styles.BG_TERTIARY)))
        p.drawEllipse(path_rect)
        if self._pix is not None:
            # Scale in device pixels and tag the ratio so high-DPI screens stay sharp.
            dpr = self.devicePixelRatioF()
            target = max(1, round(self._size * dpr))
            scaled = QPixmap(self._pix).scaled(
                target, target,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            scaled.setDevicePixelRatio(dpr)
            p.setClipping(True)
            clip = self.rect().adjusted(4, 4, -4, -4)
            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            path.addEllipse(clip.toRectF())
            p.setClipPath(path)
            p.drawPixmap(4, 4, scaled)
            p.setClipping(False)
        # online dot
        dot = 18
        p.setBrush(QBrush(QColor(styles.CARD_BG)))
        p.drawEllipse(self.width() - dot - 2, self.height() - dot - 2, dot, dot)
        p.setBrush(QBrush(QColor(styles.SUCCESS)))
        p.drawEllipse(self.width() - dot + 1, self.height() - dot + 1, dot - 6, dot - 6)
        p.end()


class ProfileEditor(QDialog):
    def __init__(self, parent, profile, on_save):
        super().__init__(parent)
        self._net = qt_net.Net(self)
        self.on_save = on_save
        self.is_new = profile is None
        self.profile = {} if profile is None else profile
        if "id" not in self.profile:
            self.profile["id"] = str(uuid.uuid4())

        self.setWindowTitle("New Profile" if self.is_new else "Edit Profile")
        self.setWindowIcon(qt_utils.app_icon())
        self.setFixedWidth(540)
        self.resize(540, 780)

        self.large_image_path = self.profile.get("large_image_path", "")
        self._elapsed = 0
        self._placeholder_pm = qt_utils.placeholder_pixmap(60)
        self._url_fetch_timer = None
        self._opened = False

        self._build_ui()
        self._refresh_card_image()
        self._update_image_status()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

    # --- ui ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = qt_utils.SmoothScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        body = QVBoxLayout(host)
        body.setContentsMargins(24, 20, 24, 20)
        body.setSpacing(12)
        scroll.setWidget(host)
        outer.addWidget(scroll, stretch=1)
        outer.addWidget(self._build_bottom_bar())

        body.addWidget(_label("New Profile" if self.is_new else "Edit Profile", size=15, bold=True))
        sub = _hint("Live preview. Type on the card, and click the game image to set what Discord shows.")
        body.addWidget(sub)
        body.addSpacing(4)
        body.addWidget(self._build_popout())
        body.addSpacing(8)

        body.addWidget(self._build_app_section())
        body.addWidget(self._build_discord_section())
        body.addWidget(self._build_images_section())
        body.addWidget(self._build_behavior_section())
        body.addStretch()

    def _build_popout(self):
        # Discord profile-popout replica: banner, avatar, then the activity block.
        card = QFrame()
        card.setObjectName("presenceCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 16)
        lay.setSpacing(0)

        banner = QFrame()
        banner.setFixedHeight(56)
        banner.setStyleSheet(
            f"background: {styles.ACCENT}; border-top-left-radius: 8px; border-top-right-radius: 8px;"
        )
        lay.addWidget(banner)

        # Generic Discord account avatar over the banner edge. This represents
        # your Discord profile picture, which Rich Presence can't change — only
        # the activity image below is editable.
        self._avatar = _AvatarDot(qt_utils.pil_to_pixmap(qt_utils.discord_avatar_pil(128)), 64, parent=card)
        self._avatar.move(14, 56 - 36)
        self._avatar.raise_()
        self._avatar.setToolTip("Your Discord avatar. Rich Presence cannot change this.")
        lay.addSpacing(42)

        content = QVBoxLayout()
        content.setContentsMargins(16, 6, 16, 0)
        content.setSpacing(4)

        self.edit_title = _card_edit("Profile name", self.profile.get("profileTitle", ""), 12, bold=True)
        content.addLayout(self._tight(self.edit_title))

        content.addSpacing(8)
        activity = QFrame()
        activity.setObjectName("darkPanel")
        act_lay = QVBoxLayout(activity)
        act_lay.setContentsMargins(12, 10, 12, 12)
        act_lay.setSpacing(6)

        act_lay.addWidget(_label("PLAYING A GAME", size=8, bold=True, muted=True))

        act_row = QHBoxLayout()
        act_row.setSpacing(12)
        self._game_image = QLabel()
        self._game_image.setFixedSize(60, 60)
        self._game_image.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._game_image.mouseReleaseEvent = lambda _e: self._open_image_picker()
        self._game_image.setToolTip("Click to choose an image")
        act_row.addWidget(self._game_image, alignment=Qt.AlignmentFlag.AlignTop)

        lines = QVBoxLayout()
        lines.setSpacing(1)
        self.edit_name = _card_edit("Application name", self.profile.get("statusName", ""), 10, bold=True)
        self.edit_details = _card_edit("What are you doing?", self.profile.get("details", ""), 9)
        self.edit_state = _card_edit("More details…", self.profile.get("state", ""), 9)
        lines.addWidget(self.edit_name)
        lines.addWidget(self.edit_details)
        lines.addWidget(self.edit_state)
        self.lbl_elapsed = _label("00:00 elapsed", size=9, muted=True)
        self.lbl_elapsed.setContentsMargins(4, 1, 0, 0)
        lines.addWidget(self.lbl_elapsed)
        act_row.addLayout(lines, stretch=1)
        act_lay.addLayout(act_row)

        content.addWidget(activity)

        self._img_status = _label("", size=8)
        self._img_status.setContentsMargins(2, 6, 0, 0)
        content.addWidget(self._img_status)

        lay.addLayout(content)
        return card

    @staticmethod
    def _tight(widget):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(widget)
        return row

    def _section(self, title):
        panel = QFrame()
        panel.setObjectName("panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(8)
        section_label = _label(title, size=8, bold=True)
        section_label.setProperty("role", "section")
        lay.addWidget(section_label)
        return panel, lay

    def _build_app_section(self):
        panel, lay = self._section("APPLICATION")

        lay.addWidget(_label("Executable", size=9, bold=True))
        exe_row = QHBoxLayout()
        exe_row.setSpacing(8)
        self.edit_exe = _field("SLDWORKS.exe", self.profile.get("targetExe", ""))
        exe_row.addWidget(self.edit_exe, stretch=1)
        browse = QPushButton("Browse")
        browse.setProperty("kind", "outline")
        browse.clicked.connect(self._pick_exe)
        exe_row.addWidget(browse)
        lay.addLayout(exe_row)
        lay.addWidget(_hint("Pick the .exe or type its name. The profile activates while it runs."))

        self.exe_path = self.profile.get("exe_path", "")

        bat = QPushButton("Create .bat launcher")
        bat.setProperty("kind", "outline")
        bat.clicked.connect(self._create_launcher)
        lay.addWidget(bat)
        lay.addWidget(_hint("Generates a .bat next to the .exe that activates this profile, then launches the app."))
        return panel

    def _build_discord_section(self):
        panel, lay = self._section("DISCORD")
        lay.addWidget(_label("Application ID", size=9, bold=True))
        self.edit_app_id = _field("123456789012345678", self.profile.get("discord_app_id", ""))
        lay.addWidget(self.edit_app_id)
        link = QLabel(
            f'Create an app at <a style="color:{styles.TEXT_LINK};" '
            f'href="https://discord.com/developers/applications">discord.com/developers</a> '
            "→ copy its Application ID."
        )
        link.setOpenExternalLinks(True)
        link.setProperty("muted", True)
        font = link.font()
        font.setPointSize(8)
        link.setFont(font)
        lay.addWidget(link)
        return panel

    def _build_images_section(self):
        panel, lay = self._section("IMAGES")
        lay.addWidget(_label("Large image (asset key or URL)", size=9, bold=True))
        self.edit_large_key = _field(
            "Asset name from the dev portal, or an https:// image URL",
            self.profile.get("large_image_url") or self.profile.get("large_image_key") or "",
        )
        self.edit_large_key.textChanged.connect(self._schedule_url_preview)
        self.edit_large_key.textChanged.connect(self._update_image_status)
        lay.addWidget(self.edit_large_key)
        lay.addWidget(_hint(
            "This is what Discord actually displays. Click the card image to search a logo "
            "or upload one (auto-hosted), or paste an asset key / public image URL here."
        ))

        lay.addWidget(_label("Large image tooltip", size=9, bold=True))
        self.edit_large_text = _field("Hover text for the large image", self.profile.get("large_image_text", ""))
        lay.addWidget(self.edit_large_text)

        lay.addWidget(_label("Small image (asset key or URL)", size=9, bold=True))
        self.edit_small_key = _field(
            "Optional corner badge image",
            self.profile.get("small_image_url") or self.profile.get("small_image_key") or "",
        )
        lay.addWidget(self.edit_small_key)

        lay.addWidget(_label("Small image tooltip", size=9, bold=True))
        self.edit_small_text = _field("Hover text for the small image", self.profile.get("small_image_text", ""))
        lay.addWidget(self.edit_small_text)
        return panel

    def _build_behavior_section(self):
        panel, lay = self._section("BEHAVIOR")

        row1 = QHBoxLayout()
        row1.addWidget(_label("Show elapsed time", size=9))
        row1.addStretch()
        self.switch_elapsed = qt_utils.Switch(self.profile.get("show_elapsed", True), on_change=self._elapsed_toggled)
        row1.addWidget(self.switch_elapsed)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(_label("Enable profile", size=9))
        row2.addStretch()
        self.switch_enabled = qt_utils.Switch(self.profile.get("enabled", True))
        row2.addWidget(self.switch_enabled)
        lay.addLayout(row2)
        return panel

    def _build_bottom_bar(self):
        bar = QFrame()
        bar.setObjectName("bottomBar")
        bar.setFixedHeight(64)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setProperty("kind", "ghost")
        cancel.clicked.connect(self.close)
        lay.addWidget(cancel)
        save = QPushButton("Save Profile")
        save.setFixedWidth(150)
        save.clicked.connect(self._save)
        lay.addWidget(save)
        return bar

    # --- behaviour -----------------------------------------------------------
    def keyPressEvent(self, event):
        # Prevent QDialog from treating Enter/Return as an implicit Accept, which
        # would close the dialog without saving. Only the Save button should save.
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            focused = self.focusWidget()
            if isinstance(focused, QLineEdit):
                focused.clearFocus()
                return
        super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._opened:
            self._opened = True
            qt_utils.animate_open(self)

    def _tick(self):
        mins, secs = divmod(self._elapsed, 60)
        self.lbl_elapsed.setText(f"{mins:02d}:{secs:02d} elapsed")
        self._elapsed += 1

    def _elapsed_toggled(self, checked):
        self.lbl_elapsed.setVisible(checked)

    def _open_image_picker(self):
        # Brandfetch matches brand names, so search the app name itself.
        default_query = (self.edit_name.text() or self.edit_title.text() or "").strip()
        picker = image_picker.ImagePicker(self, self.profile["id"], default_query, self._on_image_picked)
        picker.exec()

    def _on_image_picked(self, path, url):
        if path:
            self.large_image_path = path
        if url:
            # Auto-fill the field so the image actually renders in Discord.
            self.edit_large_key.setText(url)
        self._refresh_card_image()
        self._update_image_status()

    def _update_image_status(self):
        value = self.edit_large_key.text().strip()
        if value:
            self._img_status.setText("This image will show in Discord.")
            self._img_status.setStyleSheet(f"color: {styles.SUCCESS};")
        elif self.large_image_path:
            self._img_status.setText("Preview only. Search or upload an image, or paste a URL so Discord shows it.")
            self._img_status.setStyleSheet(f"color: {styles.TEXT_MUTED};")
        else:
            self._img_status.setText("")

    def _refresh_card_image(self):
        # Only the activity (RP) image changes; the avatar stays the generic one.
        if self.large_image_path and os.path.exists(self.large_image_path):
            try:
                img = Image.open(self.large_image_path)
                self._game_image.setPixmap(qt_utils.crisp_from_pil(img, 60, radius=10))
                return
            except Exception:
                pass
        self._game_image.setPixmap(self._placeholder_pm)

    def _pick_exe(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select executable", "", "Executables (*.exe);;All files (*.*)")
        if not path:
            return
        self.exe_path = path
        self.edit_exe.setText(os.path.basename(path))

    def _create_launcher(self):
        profile = {"id": self.profile["id"], "exe_path": self.exe_path}
        bat_path, error = launcher_inject.make_bat_launcher(profile)
        if error:
            QMessageBox.warning(self, "Launcher", error)
            return
        QMessageBox.information(
            self, "Launcher created",
            f"Created:\n{bat_path}\n\nRun this .bat instead of the .exe directly, or pin it to your taskbar.",
        )

    # URL → live preview on the card
    def _schedule_url_preview(self):
        if self._url_fetch_timer is not None:
            self._url_fetch_timer.stop()
        self._url_fetch_timer = QTimer(self)
        self._url_fetch_timer.setSingleShot(True)
        self._url_fetch_timer.timeout.connect(self._fetch_url_preview)
        self._url_fetch_timer.start(700)

    def _fetch_url_preview(self):
        if self.large_image_path:
            return  # a locally picked image owns the thumbnail
        url = self.edit_large_key.text().strip()
        if not url.lower().startswith(("http://", "https://")):
            return
        self._net.get(url, self._on_url_bytes)

    def _on_url_bytes(self, data):
        # Runs on the main thread (Qt async). Decode + paint here.
        if data is None or self.large_image_path:
            return
        try:
            pil = Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception:
            return
        self._game_image.setPixmap(qt_utils.crisp_from_pil(pil, 60, radius=10))

    # --- save ----------------------------------------------------------------
    @staticmethod
    def _split_key_or_url(value):
        value = value.strip()
        if value.lower().startswith(("http://", "https://")):
            return None, value
        return (value or None), None

    @staticmethod
    def _normalize_exe(value):
        value = value.strip()
        if value and not value.lower().endswith(".exe"):
            value = value + ".exe"
        return value

    def _save(self):
        p = self.profile
        p["profileTitle"] = self.edit_title.text().strip() or "Untitled"
        p["targetExe"] = self._normalize_exe(self.edit_exe.text())
        p["exe_path"] = self.exe_path.strip()
        p["discord_app_id"] = self.edit_app_id.text().strip()
        p["statusName"] = self.edit_name.text().strip()[:MAX_FIELD]
        p["details"] = self.edit_details.text().strip()[:MAX_FIELD]
        p["state"] = self.edit_state.text().strip()[:MAX_FIELD]
        p["large_image_text"] = self.edit_large_text.text().strip()
        p["small_image_text"] = self.edit_small_text.text().strip()
        p["large_image_key"], p["large_image_url"] = self._split_key_or_url(self.edit_large_key.text())
        p["small_image_key"], p["small_image_url"] = self._split_key_or_url(self.edit_small_key.text())
        p["large_image_path"] = self.large_image_path
        p["show_elapsed"] = self.switch_elapsed.isChecked()
        p["enabled"] = self.switch_enabled.isChecked()

        self.on_save(p, self.is_new)
        self.close()
