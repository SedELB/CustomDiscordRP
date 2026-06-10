import customtkinter
import json
import os
import styles
import profile_editor
import window_fx
from PIL import Image, ImageDraw, ImageFont

customtkinter.set_appearance_mode("Dark")

app = customtkinter.CTk()
app.geometry("940x620")
app.minsize(820, 540)
app.title("CustomRP")
app.configure(fg_color=styles.BG_PRIMARY)
window_fx.apply_chrome(app)

# Fonts must be built after the Tk root exists.
FONT_BRAND   = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=20, weight="bold")
FONT_HEADER  = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=18, weight="bold")
FONT_TITLE   = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=15, weight="bold")
FONT_BODY    = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=14)
FONT_BOLD    = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=14, weight="bold")
FONT_SMALL   = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=12)
FONT_TINY    = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=11)

AVATAR_COLORS = ["#5865f2", "#3ba55d", "#faa81a", "#ed4245", "#eb459e", "#9b59b6", "#1abc9c", "#e67e22"]


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

load_data()

def get_data():
    return app_data

def hide_window():
    app.withdraw()


# --- avatar helpers ----------------------------------------------------------
_avatar_cache = {}

def _load_truetype(size, bold=True):
    candidates = ["segoeuib.ttf" if bold else "segoeui.ttf", "arialbd.ttf" if bold else "arial.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _rounded(img, size, radius):
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    img.putalpha(mask)
    return img

def _placeholder_avatar(title, size=48):
    letter = (title.strip()[:1] or "?").upper()
    color = AVATAR_COLORS[sum(ord(c) for c in title) % len(AVATAR_COLORS)] if title else AVATAR_COLORS[0]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.rounded_rectangle((0, 0, size - 1, size - 1), radius=14, fill=color)
    font = _load_truetype(int(size * 0.5))
    bbox = dc.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    dc.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]), letter, font=font, fill="#ffffff")
    return img

def _avatar_image(profile, size=48):
    key = (profile.get("id"), profile.get("large_image_path"), profile.get("profileTitle"))
    if key in _avatar_cache:
        return _avatar_cache[key]
    path = profile.get("large_image_path", "")
    if path and os.path.exists(path):
        try:
            img = _rounded(Image.open(path), size, 14)
        except Exception:
            img = _placeholder_avatar(profile.get("profileTitle", ""), size)
    else:
        img = _placeholder_avatar(profile.get("profileTitle", ""), size)
    ctk = customtkinter.CTkImage(img, size=(size, size))
    _avatar_cache[key] = ctk
    return ctk


def on_editor_save(profile, is_new):
    if is_new:
        app_data["profiles"].append(profile)
    save_data()
    _avatar_cache.clear()
    print(f"Profile saved! Target: {profile.get('targetExe', '')}")
    refresh_profile_list()

def open_editor(profile=None):
    profile_editor.ProfileEditor(app, profile, on_editor_save)


# --- layout: sidebar + content ----------------------------------------------
app.grid_columnconfigure(0, weight=0)
app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=1)

sidebar = customtkinter.CTkFrame(app, width=236, corner_radius=0, fg_color=styles.BG_SECONDARY)
sidebar.grid(row=0, column=0, sticky="nsew")
sidebar.grid_propagate(False)
sidebar.grid_rowconfigure(3, weight=1)

brand_row = customtkinter.CTkFrame(sidebar, fg_color="transparent")
brand_row.grid(row=0, column=0, sticky="ew", padx=20, pady=(22, 0))
customtkinter.CTkLabel(brand_row, text="●", font=FONT_BRAND, text_color=styles.ACCENT).pack(side="left")
customtkinter.CTkLabel(brand_row, text="CustomRP", font=FONT_BRAND, text_color=styles.TEXT_PRIMARY).pack(
    side="left", padx=(8, 0)
)
customtkinter.CTkLabel(
    sidebar, text="Per-app Rich Presence", font=FONT_TINY, text_color=styles.TEXT_MUTED, anchor="w"
).grid(row=1, column=0, sticky="ew", padx=20, pady=(2, 18))

customtkinter.CTkButton(
    sidebar,
    text="+   New Profile",
    command=open_editor,
    font=FONT_BOLD,
    height=42,
    corner_radius=styles.RADIUS_BUTTON,
    fg_color=styles.ACCENT,
    hover_color=styles.ACCENT_HOVER,
    text_color=styles.TEXT_PRIMARY,
    anchor="center",
).grid(row=2, column=0, sticky="ew", padx=16)

# Status / power panel pinned to the bottom of the sidebar.
customtkinter.CTkFrame(sidebar, height=1, fg_color=styles.BORDER).grid(
    row=4, column=0, sticky="ew", padx=16, pady=(0, 0)
)
status_panel = customtkinter.CTkFrame(sidebar, fg_color=styles.BG_TERTIARY, corner_radius=styles.RADIUS_CARD)
status_panel.grid(row=5, column=0, sticky="ew", padx=16, pady=(16, 6))

customtkinter.CTkLabel(
    sidebar, text="CustomRP  ·  v2.0", font=FONT_TINY, text_color=styles.TEXT_MUTED
).grid(row=6, column=0, pady=(0, 10))

status_row = customtkinter.CTkFrame(status_panel, fg_color="transparent")
status_row.pack(fill="x", padx=14, pady=(14, 8))
status_dot = customtkinter.CTkLabel(status_row, text="●", font=FONT_SMALL, text_color=styles.TEXT_MUTED)
status_dot.pack(side="left")
status_label = customtkinter.CTkLabel(
    status_row, text="Stopped", font=FONT_BOLD, text_color=styles.TEXT_PRIMARY, anchor="w"
)
status_label.pack(side="left", padx=(8, 0))

status_detail = customtkinter.CTkLabel(
    status_panel, text="Monitoring is off", font=FONT_TINY, text_color=styles.TEXT_MUTED, anchor="w"
)
status_detail.pack(fill="x", padx=14, pady=(0, 10))

power_button = customtkinter.CTkButton(
    status_panel,
    text="Start monitoring",
    font=FONT_BOLD,
    height=38,
    corner_radius=styles.RADIUS_BUTTON,
    fg_color=styles.SUCCESS,
    hover_color=styles.SUCCESS_HOVER,
    text_color=styles.TEXT_PRIMARY,
)
power_button.pack(fill="x", padx=14, pady=(0, 14))

# Content pane
content = customtkinter.CTkFrame(app, fg_color=styles.BG_PRIMARY, corner_radius=0)
content.grid(row=0, column=1, sticky="nsew")
content.grid_columnconfigure(0, weight=1)
content.grid_rowconfigure(1, weight=1)

content_header = customtkinter.CTkFrame(content, fg_color="transparent")
content_header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))
customtkinter.CTkLabel(content_header, text="Your Profiles", font=FONT_HEADER, text_color=styles.TEXT_PRIMARY).pack(
    side="left"
)
count_badge = customtkinter.CTkLabel(
    content_header,
    text="0",
    font=FONT_SMALL,
    text_color=styles.TEXT_MUTED,
    fg_color=styles.BG_TERTIARY,
    corner_radius=10,
    width=28,
    height=22,
)
count_badge.pack(side="left", padx=(10, 0))

search_var = customtkinter.StringVar()
search_entry = customtkinter.CTkEntry(
    content_header,
    textvariable=search_var,
    placeholder_text="Search profiles…",
    placeholder_text_color=styles.TEXT_MUTED,
    font=FONT_SMALL,
    width=220,
    height=34,
    corner_radius=17,
    fg_color=styles.BG_TERTIARY,
    border_color=styles.BORDER,
    border_width=1,
    text_color=styles.TEXT_PRIMARY,
)
search_entry.pack(side="right")
search_var.trace_add("write", lambda *_: refresh_profile_list())

profiles_frame = customtkinter.CTkScrollableFrame(
    content,
    fg_color="transparent",
    scrollbar_button_color=styles.BORDER,
    scrollbar_button_hover_color=styles.TEXT_MUTED,
)
profiles_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
profiles_frame.grid_columnconfigure(0, weight=1)


def _subtitle_for(profile):
    parts = []
    if profile.get("targetExe"):
        parts.append(profile["targetExe"])
    if profile.get("details"):
        parts.append(profile["details"])
    return "  •  ".join(parts) if parts else "No executable set"


def _bind_card_hover(card):
    def on_enter(_e):
        card.configure(border_color=styles.ACCENT)

    def on_leave(_e):
        # Ignore Leave events caused by moving onto a child of the card.
        x, y = card.winfo_pointerxy()
        w = card.winfo_containing(x, y)
        while w is not None:
            if w is card:
                return
            w = w.master
        card.configure(border_color=styles.BORDER)

    card.bind("<Enter>", on_enter)
    card.bind("<Leave>", on_leave)


def _make_card(profile):
    card = customtkinter.CTkFrame(
        profiles_frame, fg_color=styles.CARD_BG, corner_radius=12, border_width=1, border_color=styles.BORDER
    )
    card.grid_columnconfigure(1, weight=1)
    _bind_card_hover(card)

    open_this = lambda _e=None, p=profile: open_editor(p)
    card.bind("<Button-1>", open_this)

    avatar = customtkinter.CTkButton(
        card,
        text="",
        image=_avatar_image(profile, 48),
        width=48,
        height=48,
        fg_color="transparent",
        hover_color=styles.CARD_HOVER,
        corner_radius=14,
        command=open_this,
    )
    avatar.grid(row=0, column=0, rowspan=2, padx=(14, 12), pady=14)

    title_lbl = customtkinter.CTkLabel(
        card,
        text=profile.get("profileTitle", "Untitled"),
        font=FONT_TITLE,
        text_color=styles.TEXT_PRIMARY,
        anchor="w",
        height=24,
    )
    title_lbl.grid(row=0, column=1, sticky="ew", pady=(14, 0))

    subtitle_lbl = customtkinter.CTkLabel(
        card, text=_subtitle_for(profile), font=FONT_SMALL, text_color=styles.TEXT_MUTED, anchor="w"
    )
    subtitle_lbl.grid(row=1, column=1, sticky="ew", pady=(0, 14))

    for lbl in (title_lbl, subtitle_lbl):
        lbl.bind("<Button-1>", open_this)
        lbl.configure(cursor="hand2")

    actions = customtkinter.CTkFrame(card, fg_color="transparent")
    actions.grid(row=0, column=2, rowspan=2, padx=(8, 14))

    enabled_var = customtkinter.BooleanVar(value=profile.get("enabled", True))

    def toggle_enabled(p=profile, var=enabled_var):
        p["enabled"] = bool(var.get())
        save_data()

    customtkinter.CTkSwitch(
        actions,
        text="",
        width=40,
        variable=enabled_var,
        command=toggle_enabled,
        progress_color=styles.SUCCESS,
        button_color=styles.TEXT_PRIMARY,
        fg_color=styles.BORDER,
    ).pack(side="left", padx=(0, 8))

    customtkinter.CTkButton(
        actions,
        text="Edit",
        command=lambda p=profile: open_editor(p),
        font=FONT_SMALL,
        width=56,
        height=30,
        corner_radius=styles.RADIUS_BUTTON,
        fg_color="transparent",
        hover_color=styles.CARD_HOVER,
        text_color=styles.TEXT_MUTED,
        border_width=1,
        border_color=styles.BORDER,
    ).pack(side="left", padx=(0, 6))

    customtkinter.CTkButton(
        actions,
        text="Delete",
        command=lambda p=profile: delete_profile(p),
        font=FONT_SMALL,
        width=62,
        height=30,
        corner_radius=styles.RADIUS_BUTTON,
        fg_color="transparent",
        hover_color=styles.CARD_HOVER,
        text_color=styles.DANGER,
        border_width=1,
        border_color=styles.BORDER,
    ).pack(side="left")

    return card


def delete_profile(profile):
    if profile in app_data["profiles"]:
        app_data["profiles"].remove(profile)
        save_data()
        _avatar_cache.clear()
        refresh_profile_list()


def _matches(profile, needle):
    haystack = " ".join(
        str(profile.get(k, "")) for k in ("profileTitle", "targetExe", "details", "state", "statusName")
    ).lower()
    return needle in haystack


def refresh_profile_list():
    for widget in profiles_frame.winfo_children():
        widget.destroy()

    profiles = app_data.get("profiles", [])
    count_badge.configure(text=str(len(profiles)))

    needle = search_var.get().strip().lower()
    if needle:
        profiles = [p for p in profiles if _matches(p, needle)]
        if not profiles:
            customtkinter.CTkLabel(
                profiles_frame,
                text=f"No profiles match “{search_var.get().strip()}”",
                font=FONT_SMALL,
                text_color=styles.TEXT_MUTED,
            ).grid(row=0, column=0, pady=60)
            return

    if not profiles:
        empty = customtkinter.CTkFrame(profiles_frame, fg_color="transparent")
        empty.grid(row=0, column=0, pady=80)
        customtkinter.CTkLabel(
            empty, text="No profiles yet", font=FONT_TITLE, text_color=styles.TEXT_PRIMARY
        ).pack(pady=(0, 6))
        customtkinter.CTkLabel(
            empty,
            text="Create one to start sharing your Rich Presence.",
            font=FONT_SMALL,
            text_color=styles.TEXT_MUTED,
        ).pack(pady=(0, 16))
        customtkinter.CTkButton(
            empty,
            text="+   New Profile",
            command=open_editor,
            font=FONT_BOLD,
            height=40,
            width=180,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.ACCENT,
            hover_color=styles.ACCENT_HOVER,
            text_color=styles.TEXT_PRIMARY,
        ).pack()
        return

    for idx, profile in enumerate(profiles):
        card = _make_card(profile)
        card.grid(row=idx, column=0, sticky="ew", pady=6)


# --- live status (called from the monitor loop / power toggle) ---------------
def update_power_visual(running):
    if running:
        power_button.configure(text="Stop monitoring", fg_color=styles.DANGER, hover_color=styles.DANGER_HOVER)
        status_label.configure(text="Idle")
        status_dot.configure(text_color=styles.ACCENT)
        status_detail.configure(text="Watching for profiled apps…")
    else:
        power_button.configure(text="Start monitoring", fg_color=styles.SUCCESS, hover_color=styles.SUCCESS_HOVER)
        status_label.configure(text="Stopped")
        status_dot.configure(text_color=styles.TEXT_MUTED)
        status_detail.configure(text="Monitoring is off")


def report_activity(title):
    # Called from the monitor loop. title=None means running but idle.
    if title:
        status_label.configure(text="Active")
        status_dot.configure(text_color=styles.SUCCESS)
        status_detail.configure(text=title)
    else:
        if status_label.cget("text") != "Stopped":
            status_label.configure(text="Idle")
            status_dot.configure(text_color=styles.ACCENT)
            status_detail.configure(text="Watching for profiled apps…")


# initial list on startup
refresh_profile_list()

app.protocol('WM_DELETE_WINDOW', hide_window)
