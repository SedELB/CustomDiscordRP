# styles.py — Discord dark theme tokens + global Qt stylesheet

# Color tokens (from CLAUDE.md spec)
BG_PRIMARY    = "#313338"   # main window background
BG_SECONDARY  = "#2b2d31"   # panels
BG_TERTIARY   = "#1e1f22"   # input fields, titlebar, deep cards
BG_TITLEBAR   = "#1e1f22"   # custom titlebar background
BG_STATUSBAR  = "#232428"   # bottom statusbar surface
ACCENT        = "#5865f2"   # Discord blurple — buttons, active states
ACCENT_HOVER  = "#4752c4"
ACCENT_DOWN   = "#3c45a5"
TEXT_HEADING  = "#f2f3f5"   # headings, profile names
TEXT_PRIMARY  = "#f2f3f5"   # primary text
TEXT_MUTED    = "#949ba4"   # secondary text, labels, placeholders
TEXT_FAINT    = "#4e5058"   # small labels / version
TEXT_LINK     = "#00b0f4"
ICON_DEFAULT  = "#b5bac1"   # default icon color
ICON_MUTED    = "#4e5058"   # disabled / muted icon
DANGER        = "#da373c"
DANGER_HOVER  = "#b32d30"
SUCCESS       = "#23a55a"
SUCCESS_HOVER = "#1a9050"
TOGGLE_OFF    = "#4e5058"   # toggle switch OFF track
DOT_ONLINE    = "#23a55a"
DOT_IDLE      = "#f0b232"
DOT_OFFLINE   = "#80848e"
BORDER        = "#3f4147"
CARD_BG       = "#232428"   # presence preview card background
ROW_BG        = "#2b2d31"   # profile list row
ROW_HOVER     = "#3f4147"

FONT_FAMILY = "Segoe UI"    # Whitney/gg sans are rarely installed; Segoe is the Windows fallback

QSS = f"""
* {{
    font-family: "gg sans", "Noto Sans", "{FONT_FAMILY}";
    color: {TEXT_PRIMARY};
}}
QMainWindow, QDialog {{
    background: {BG_PRIMARY};
}}
QLabel {{
    background: transparent;
}}
QLabel[muted="true"] {{
    color: {TEXT_MUTED};
}}
QLabel[role="section"] {{
    color: {TEXT_MUTED};
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLineEdit {{
    background: {BG_TERTIARY};
    border: 1px solid {BG_TERTIARY};
    border-radius: 4px;
    padding: 9px 10px;
    selection-background-color: {ACCENT};
    color: {TEXT_PRIMARY};
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}
QLineEdit::placeholder {{
    color: {TEXT_MUTED};
}}

/* Inline edits that live on the presence card */
QLineEdit[cardEdit="true"] {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 1px 4px;
}}
QLineEdit[cardEdit="true"]:hover {{
    background: rgba(255, 255, 255, 0.04);
}}
QLineEdit[cardEdit="true"]:focus {{
    background: {BG_TERTIARY};
    border: 1px solid {ACCENT};
}}

QLineEdit#search {{
    border-radius: 4px;
    padding: 7px 12px;
    background: {BG_TERTIARY};
    border: 1px solid {BG_TERTIARY};
}}
QLineEdit#search:focus {{
    background: #111214;
    border: 1px solid {BG_TERTIARY};
}}

QPushButton {{
    background: {ACCENT};
    border: 1px solid {ACCENT_DOWN};
    border-radius: 4px;
    padding: 9px 16px;
    font-weight: 600;
    color: #ffffff;
}}
QPushButton:hover {{ background: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background: {ACCENT_DOWN}; }}
QPushButton:disabled {{ background: {BORDER}; border-color: {BORDER}; color: {TEXT_MUTED}; }}
QPushButton[compact="true"] {{ padding: 5px 14px; font-weight: 600; }}

QPushButton[kind="ghost"] {{
    background: transparent;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    font-weight: 500;
}}
QPushButton[kind="ghost"]:hover {{
    background: rgba(255, 255, 255, 0.06);
    color: {TEXT_PRIMARY};
}}
QPushButton[kind="outline"] {{
    background: transparent;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    font-weight: 500;
}}
QPushButton[kind="outline"]:hover {{
    background: rgba(255, 255, 255, 0.06);
}}
QPushButton[kind="danger-ghost"] {{
    background: transparent;
    color: {DANGER};
    border: 1px solid {DANGER};
    font-weight: 500;
}}
QPushButton[kind="danger-ghost"]:hover {{
    background: rgba(218, 55, 60, 0.14);
}}
QPushButton[kind="success"] {{ background: {SUCCESS}; border: 1px solid {SUCCESS_HOVER}; }}
QPushButton[kind="success"]:hover {{ background: {SUCCESS_HOVER}; }}
QPushButton[kind="danger"] {{ background: {DANGER}; border: 1px solid {DANGER_HOVER}; }}
QPushButton[kind="danger"]:hover {{ background: {DANGER_HOVER}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BG_TERTIARY};
    border-radius: 3px;
    min-height: 36px;
}}
QScrollBar::handle:vertical:hover {{ background: {BORDER}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QToolTip {{
    background: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 6px 8px;
    border-radius: 4px;
}}
QMenu {{
    background: {BG_SECONDARY};
    border: 1px solid {BG_TERTIARY};
    border-radius: 6px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 28px 7px 12px;
    border-radius: 3px;
}}
QMenu::item:selected {{ background: {ACCENT}; color: #ffffff; }}
QMenu::item:disabled {{ color: {TEXT_MUTED}; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 5px 8px; }}

QMessageBox {{ background: {BG_PRIMARY}; }}

QTabWidget::pane {{ border: none; }}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 8px 18px;
    margin-right: 4px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover {{ color: {TEXT_PRIMARY}; }}

QRadioButton {{
    color: {TEXT_PRIMARY};
    spacing: 6px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 8px;
    border: 2px solid {BORDER};
    background: transparent;
}}
QRadioButton::indicator:hover {{ border-color: {TEXT_MUTED}; }}
QRadioButton::indicator:checked {{ border: 4px solid {ACCENT}; background: transparent; }}

QPushButton[kind="thumb"] {{
    background: {BG_TERTIARY};
    border: 2px solid {BG_TERTIARY};
    border-radius: 8px;
    padding: 0;
}}
QPushButton[kind="thumb"]:hover {{ border: 2px solid {BORDER}; }}
QPushButton[kind="thumb"]:checked {{ border: 2px solid {ACCENT}; }}

/* --- custom window chrome ------------------------------------------------ */
#titlebar {{ background: {BG_TITLEBAR}; }}
#titlebar QLabel {{ color: {TEXT_MUTED}; }}

/* Min / maximize window buttons */
QPushButton[kind="win"] {{
    background: transparent;
    border: none;
    border-radius: 0;
    color: {ICON_DEFAULT};
    padding: 0;
}}
QPushButton[kind="win"]:hover {{ background: #36373d; color: {TEXT_HEADING}; }}
QPushButton[kind="win"]:pressed {{ background: #2f3035; }}
/* Close button — red on hover, Discord style */
QPushButton[kind="winClose"] {{
    background: transparent;
    border: none;
    border-radius: 0;
    color: {ICON_DEFAULT};
    padding: 0;
}}
QPushButton[kind="winClose"]:hover {{ background: #c03537; color: #ffffff; }}
QPushButton[kind="winClose"]:pressed {{ background: #a32b2d; color: #ffffff; }}

#statusBar {{ background: {BG_STATUSBAR}; border-top: 1px solid {BG_TITLEBAR}; }}
#statusBar QLabel[role="statusText"] {{ color: {TEXT_HEADING}; font-weight: 600; }}

/* Named containers */
#panel {{ background: {BG_SECONDARY}; border-radius: 8px; }}
#darkPanel {{ background: {BG_TERTIARY}; border-radius: 8px; }}
#presenceCard {{ background: {CARD_BG}; border-radius: 8px; }}
#row {{ background: {ROW_BG}; border-radius: 8px; }}
#bottomBar {{ background: {BG_SECONDARY}; }}
#countChip {{
    background: {BG_TERTIARY};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 1px 8px;
    font-size: 9pt;
    font-weight: 700;
}}
"""
