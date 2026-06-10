import pystray
from pystray import Menu, MenuItem
from PIL import Image, ImageDraw
import styles


def create_image(width, height, bg, fg):
    image = Image.new('RGB', (width, height), bg)
    dc = ImageDraw.Draw(image)
    # Simple ring mark on a dark background, tinted by state.
    margin = width // 6
    dc.ellipse((margin, margin, width - margin, height - margin), fill=fg)
    inner = width // 3
    dc.ellipse((inner, inner, width - inner, height - inner), fill=bg)
    return image


_STATE_COLORS = {
    'idle': styles.TEXT_MUTED,
    'active': styles.ACCENT,
    'error': styles.DANGER,
}


def _icon_for(state):
    color = _STATE_COLORS.get(state, styles.TEXT_MUTED)
    return create_image(64, 64, styles.BG_TERTIARY, color)


tray_icon = pystray.Icon('CustomRP', _icon_for('idle'), title='CustomRP')


def set_state(state, tooltip=None):
    try:
        tray_icon.icon = _icon_for(state)
        if tooltip is not None:
            tray_icon.title = tooltip
    except Exception:
        pass
