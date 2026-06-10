# window_fx.py — shared window chrome (app icon) for all CustomRP windows
from PIL import Image, ImageDraw, ImageTk
import styles

_icon_refs = []  # keep PhotoImage references alive for the app lifetime


def _logo(size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 4, fill=styles.BG_TERTIARY)
    margin = size // 5
    dc.ellipse((margin, margin, size - margin, size - margin), fill=styles.ACCENT)
    inner = int(size * 0.36)
    dc.ellipse((inner, inner, size - inner, size - inner), fill=styles.BG_TERTIARY)
    return img


def apply_chrome(window):
    # CTk/CTkToplevel re-set their default icon ~200ms after creation, so ours
    # must land after that to stick.
    def set_icon():
        try:
            photo = ImageTk.PhotoImage(_logo(64))
            _icon_refs.append(photo)
            window.iconphoto(False, photo)
        except Exception:
            pass

    window.after(300, set_icon)
