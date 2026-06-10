# styles.py — Discord dark theme tokens, adapted for customtkinter

# Color tokens (from CLAUDE.md spec)
BG_PRIMARY    = "#313338"   # main window background
BG_SECONDARY  = "#2b2d31"   # sidebar / panels
BG_TERTIARY   = "#1e1f22"   # input fields, cards
ACCENT        = "#5865f2"   # Discord blurple — buttons, active states
ACCENT_HOVER  = "#4752c4"
TEXT_PRIMARY  = "#f2f3f5"
TEXT_MUTED    = "#949ba4"
TEXT_LINK     = "#00b0f4"
DANGER        = "#ed4245"
DANGER_HOVER  = "#c93b3e"
SUCCESS       = "#23a55a"
SUCCESS_HOVER = "#1d8e4d"
BORDER        = "#3f4147"
CARD_BG       = "#232428"   # profile preview card background
CARD_HOVER    = "#2e3035"

# Typography — Whitney/Noto Sans are rarely installed on Windows; Segoe UI is the
# reliable fallback. customtkinter resolves the first available family.
FONT_FAMILY   = "Segoe UI"
SIZE_BODY     = 14
SIZE_HEADER   = 18
SIZE_SMALL    = 12

# Shared widget geometry
RADIUS_BUTTON = 4
RADIUS_INPUT  = 4
RADIUS_CARD   = 6
