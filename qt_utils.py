# qt_utils.py — shared Qt helpers: crisp pixmaps, avatars, app icon, switch, animations
import io
import os
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QRectF, QPropertyAnimation, QVariantAnimation,
    QEasingCurve, QAbstractAnimation, pyqtProperty,
)
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QBrush, QGuiApplication
from PyQt6.QtWidgets import QWidget, QScrollArea
import styles

AVATAR_COLORS = ["#5865f2", "#3ba55d", "#faa81a", "#ed4245", "#eb459e", "#9b59b6", "#1abc9c", "#e67e22"]

SS = 4  # supersampling factor — PIL shape drawing is aliased, so draw big and downscale


def device_ratio():
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return 1.0
    return float(screen.devicePixelRatio())


def pil_to_pixmap(img, dpr=None):
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, "PNG")
    pixmap = QPixmap()
    pixmap.loadFromData(buf.getvalue(), "PNG")
    if dpr:
        pixmap.setDevicePixelRatio(dpr)
    return pixmap


def _load_truetype(size, bold=True):
    candidates = ["segoeuib.ttf" if bold else "segoeui.ttf", "arialbd.ttf" if bold else "arial.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def rounded_pil(img, size, radius):
    # Antialiased rounded crop: build the mask supersampled, then downscale.
    img = img.convert("RGBA").resize((size * SS, size * SS), Image.LANCZOS)
    mask = Image.new("L", (size * SS, size * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * SS, size * SS), radius=radius * SS, fill=255)
    img.putalpha(mask)
    return img.resize((size, size), Image.LANCZOS)


def initial_avatar_pil(title, size=48, radius=None):
    if radius is None:
        radius = size // 3
    big = size * SS
    letter = (title.strip()[:1] or "?").upper()
    color = AVATAR_COLORS[sum(ord(c) for c in title) % len(AVATAR_COLORS)] if title else AVATAR_COLORS[0]
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rounded_rectangle((0, 0, big - 1, big - 1), radius=radius * SS, fill=color)
    font = _load_truetype(int(big * 0.46))
    bbox = dc.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    dc.text(((big - tw) / 2 - bbox[0], (big - th) / 2 - bbox[1]), letter, font=font, fill="#ffffff")
    return img.resize((size, size), Image.LANCZOS)


def avatar_pixmap(profile, size=48):
    dpr = device_ratio()
    phys = max(1, round(size * dpr))
    path = profile.get("large_image_path", "")
    if path and os.path.exists(path):
        try:
            return pil_to_pixmap(rounded_pil(Image.open(path), phys, phys // 3), dpr)
        except Exception:
            pass
    return pil_to_pixmap(initial_avatar_pil(profile.get("profileTitle", ""), phys), dpr)


def crisp_from_pil(img, logical_size, radius=None):
    # Convert any PIL image to a DPI-sharp pixmap at the given logical size.
    dpr = device_ratio()
    phys = max(1, round(logical_size * dpr))
    if radius is not None:
        pil = rounded_pil(img, phys, max(1, round(radius * dpr)))
    else:
        pil = img.convert("RGBA").resize((phys, phys), Image.LANCZOS)
    return pil_to_pixmap(pil, dpr)


def discord_avatar_pil(size=64):
    # Generic Discord "new user" avatar: blurple circle + white Clyde mark.
    big = size * SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.ellipse((0, 0, big - 1, big - 1), fill=styles.ACCENT)

    # Clyde logo, centred. Body is a rounded "controller" with two feet + two eyes.
    lw, lh = big * 0.60, big * 0.46
    lx, ly = (big - lw) / 2, (big - lh) / 2
    white = "#ffffff"
    # head / body
    dc.rounded_rectangle((lx, ly, lx + lw, ly + lh * 0.84), radius=lh * 0.42, fill=white)
    # feet (rounded protrusions at the bottom corners)
    foot_w = lw * 0.34
    dc.ellipse((lx, ly + lh * 0.40, lx + foot_w, ly + lh), fill=white)
    dc.ellipse((lx + lw - foot_w, ly + lh * 0.40, lx + lw, ly + lh), fill=white)
    # eyes (blurple vertical pills)
    eye_w, eye_h = lw * 0.135, lh * 0.40
    eye_y = ly + lh * 0.30
    dc.rounded_rectangle(
        (lx + lw * 0.26, eye_y, lx + lw * 0.26 + eye_w, eye_y + eye_h), radius=eye_w / 2, fill=styles.ACCENT
    )
    dc.rounded_rectangle(
        (lx + lw * 0.605, eye_y, lx + lw * 0.605 + eye_w, eye_y + eye_h), radius=eye_w / 2, fill=styles.ACCENT
    )
    return img.resize((size, size), Image.LANCZOS)


def placeholder_image_pil(size=60):
    # Grey rounded square with a camera glyph, used when no image is set.
    big = size * SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rounded_rectangle((0, 0, big - 1, big - 1), radius=big // 6, fill="#1e1f22")
    body_top = big * 0.38
    dc.rounded_rectangle((big * 0.18, body_top, big * 0.82, big * 0.78), radius=big // 12, fill="#4e5058")
    dc.rectangle((big * 0.40, body_top - big * 0.08, big * 0.60, body_top), fill="#4e5058")
    dc.ellipse((big * 0.40, big * 0.46, big * 0.62, big * 0.68), fill="#1e1f22")
    return img.resize((size, size), Image.LANCZOS)


def placeholder_pixmap(size=60):
    dpr = device_ratio()
    phys = max(1, round(size * dpr))
    return pil_to_pixmap(placeholder_image_pil(phys), dpr)


def logo_pil(size=64):
    big = size * SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rounded_rectangle((0, 0, big - 1, big - 1), radius=big // 4, fill=styles.BG_TERTIARY)
    margin = big // 5
    dc.ellipse((margin, margin, big - margin, big - margin), fill=styles.ACCENT)
    inner = int(big * 0.36)
    dc.ellipse((inner, inner, big - inner, big - inner), fill=styles.BG_TERTIARY)
    return img.resize((size, size), Image.LANCZOS)


def logo_pixmap(size=64):
    dpr = device_ratio()
    phys = max(1, round(size * dpr))
    return pil_to_pixmap(logo_pil(phys), dpr)


def app_icon():
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(pil_to_pixmap(logo_pil(size)))
    return icon


def animate_open(widget):
    # Fade + rise-in for dialogs/windows. Keep refs on the widget.
    widget.setWindowOpacity(0.0)
    fade = QPropertyAnimation(widget, b"windowOpacity", widget)
    fade.setDuration(170)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.Type.OutCubic)

    pos = widget.pos()
    rise = QPropertyAnimation(widget, b"pos", widget)
    rise.setDuration(200)
    rise.setStartValue(pos + QPoint(0, 16))
    rise.setEndValue(pos)
    rise.setEasingCurve(QEasingCurve.Type.OutCubic)

    widget._open_anims = (fade, rise)
    fade.start()
    rise.start()


class SmoothScrollArea(QScrollArea):
    # Wheel scrolling animated with easing instead of hard steps.
    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim = QPropertyAnimation(self.verticalScrollBar(), b"value", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._target = None

    def wheelEvent(self, event):
        bar = self.verticalScrollBar()
        if bar.maximum() == 0:
            event.ignore()
            return
        if self._anim.state() == QAbstractAnimation.State.Running and self._target is not None:
            base = self._target
        else:
            base = bar.value()
        target = max(0, min(bar.maximum(), base - event.angleDelta().y()))
        self._target = target
        self._anim.stop()
        self._anim.setStartValue(bar.value())
        self._anim.setEndValue(target)
        self._anim.start()
        event.accept()


class Switch(QWidget):
    # Discord-style animated toggle switch.
    def __init__(self, checked=False, parent=None, on_change=None):
        super().__init__(parent)
        self._checked = checked
        self._pos = 1.0 if checked else 0.0
        self.on_change = on_change
        self.setFixedSize(QSize(40, 24))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(130)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_pos(self):
        return self._pos

    def _set_pos(self, value):
        self._pos = value
        self.update()

    pos = pyqtProperty(float, fget=_get_pos, fset=_set_pos)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked, animate=False):
        self._checked = bool(checked)
        if animate:
            self._anim.stop()
            self._anim.setEndValue(1.0 if self._checked else 0.0)
            self._anim.start()
        else:
            self._set_pos(1.0 if self._checked else 0.0)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked, animate=True)
            if self.on_change:
                self.on_change(self._checked)
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track_off = QColor(styles.TOGGLE_OFF)
        track_on = QColor(styles.SUCCESS)
        track = QColor(
            int(track_off.red() + (track_on.red() - track_off.red()) * self._pos),
            int(track_off.green() + (track_on.green() - track_off.green()) * self._pos),
            int(track_off.blue() + (track_on.blue() - track_off.blue()) * self._pos),
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track))
        p.drawRoundedRect(QRectF(0, 2, 40, 20), 10.0, 10.0)
        # knob: 16px wide, 4px margins -> travel = 40 - 16 - 2*4 = 16
        x = 4.0 + self._pos * 16.0
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QRectF(x, 4.0, 16.0, 16.0))
        p.end()


class HoverColorMixin:
    # Animated background-color hover for QFrame-based rows.
    def init_hover(self, base_hex, hover_hex, radius=8):
        self._hover_base = QColor(base_hex)
        self._hover_target = QColor(hover_hex)
        self._hover_radius = radius
        self._hover_current = QColor(base_hex)
        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(120)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim.valueChanged.connect(self._apply_hover_color)
        self._apply_hover_color(self._hover_base)

    def _animate_hover(self, to_color):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_current)
        self._hover_anim.setEndValue(to_color)
        self._hover_anim.start()

    def _apply_hover_color(self, color):
        self._hover_current = QColor(color)
        self.setStyleSheet(
            f"#{self.objectName()} {{ background: {self._hover_current.name()}; "
            f"border-radius: {self._hover_radius}px; }}"
        )

    def enterEvent(self, event):
        self._animate_hover(self._hover_target)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(self._hover_base)
        super().leaveEvent(event)
