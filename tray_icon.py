import pystray
from pystray import Menu, MenuItem
from PIL import Image, ImageDraw
import styles


def create_image(width, height, bg, fg):
    image = Image.new('RGB', (width, height), bg)
    dc = ImageDraw.Draw(image)
    # Simple rounded "RP" mark on a Discord-blurple background.
    margin = width // 6
    dc.ellipse((margin, margin, width - margin, height - margin), fill=fg)
    inner = width // 3
    dc.ellipse((inner, inner, width - inner, height - inner), fill=bg)
    return image


tray_icon = pystray.Icon(
    'CustomRP',
    create_image(64, 64, styles.BG_TERTIARY, styles.ACCENT),
    title='CustomRP',
)
