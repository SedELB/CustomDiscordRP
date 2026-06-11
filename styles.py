# styles.py — Discord dark theme tokens + global Qt stylesheet

# Color tokens (from CLAUDE.md spec)
BG_PRIMARY    = "#313338"   # main window background
BG_SECONDARY  = "#2b2d31"   # sidebar / panels
BG_TERTIARY   = "#1e1f22"   # input fields, cards
ACCENT        = "#5865f2"   # Discord blurple — buttons, active states
ACCENT_HOVER  = "#4752c4"
ACCENT_DOWN   = "#3c45a5"
TEXT_PRIMARY  = "#f2f3f5"
TEXT_MUTED    = "#949ba4"
TEXT_LINK     = "#00b0f4"
DANGER        = "#ed4245"
DANGER_HOVER  = "#c93b3e"
SUCCESS       = "#23a55a"
SUCCESS_HOVER = "#1d8e4d"
BORDER        = "#3f4147"
CARD_BG       = "#232428"   # presence preview card background
ROW_BG        = "#2b2d31"   # profile list row
ROW_HOVER     = "#35373d"

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
    border-radius: 15px;
    padding: 6px 14px;
    background: {BG_TERTIARY};
    border: 1px solid {BG_TERTIARY};
}}
QLineEdit#search:focus {{
    border: 1px solid {ACCENT};
}}

QPushButton {{
    background: {ACCENT};
    border: none;
    border-radius: 4px;
    padding: 9px 16px;
    font-weight: 600;
    color: #ffffff;
}}
QPushButton:hover {{ background: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background: {ACCENT_DOWN}; }}
QPushButton:disabled {{ background: {BORDER}; color: {TEXT_MUTED}; }}

QPushButton[kind="ghost"] {{
    background: transparent;
    color: {TEXT_MUTED};
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
    font-weight: 500;
}}
QPushButton[kind="danger-ghost"]:hover {{
    background: rgba(237, 66, 69, 0.12);
}}
QPushButton[kind="success"] {{ background: {SUCCESS}; }}
QPushButton[kind="success"]:hover {{ background: {SUCCESS_HOVER}; }}
QPushButton[kind="danger"] {{ background: {DANGER}; }}
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

/* Named containers */
#sidebar {{ background: {BG_SECONDARY}; }}
#panel {{ background: {BG_SECONDARY}; border-radius: 8px; }}
#darkPanel {{ background: {BG_TERTIARY}; border-radius: 8px; }}
#presenceCard {{ background: {CARD_BG}; border-radius: 8px; }}
#row {{ background: {ROW_BG}; border-radius: 8px; }}
#bottomBar {{ background: {BG_SECONDARY}; }}
#countChip {{
    background: {BG_TERTIARY};
    color: {TEXT_MUTED};
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 9pt;
    font-weight: 600;
}}
"""
