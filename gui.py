import customtkinter
import json
import os
import styles
import profile_editor

customtkinter.set_appearance_mode("Dark")

app = customtkinter.CTk()
app.geometry("440x640")
app.title("CustomRP")
app.configure(fg_color=styles.BG_PRIMARY)

# Fonts must be built after the Tk root exists.
FONT_HEADER = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_HEADER, weight="bold")
FONT_BODY   = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_BODY)
FONT_BOLD   = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_BODY, weight="bold")
FONT_SMALL  = customtkinter.CTkFont(family=styles.FONT_FAMILY, size=styles.SIZE_SMALL)


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


def on_editor_save(profile, is_new):
    if is_new:
        app_data["profiles"].append(profile)
    save_data()
    print(f"Profile saved! Target: {profile.get('targetExe', '')}")
    refresh_profile_list()

def open_editor(profile=None):
    profile_editor.ProfileEditor(app, profile, on_editor_save)


# Header
header = customtkinter.CTkLabel(app, text="CustomRP", font=FONT_HEADER, text_color=styles.TEXT_PRIMARY, anchor="w")
header.pack(fill="x", padx=24, pady=(20, 0))

subtitle = customtkinter.CTkLabel(
    app, text="Per-app Discord Rich Presence", font=FONT_SMALL, text_color=styles.TEXT_MUTED, anchor="w"
)
subtitle.pack(fill="x", padx=24, pady=(0, 12))

# Scrollable profile list
profiles_frame = customtkinter.CTkScrollableFrame(
    app,
    label_text="Saved Profiles",
    label_font=FONT_BOLD,
    label_text_color=styles.TEXT_MUTED,
    fg_color=styles.BG_SECONDARY,
    label_fg_color=styles.BG_SECONDARY,
    corner_radius=styles.RADIUS_CARD,
)
profiles_frame.pack(pady=(0, 16), padx=16, fill="both", expand=True)

def refresh_profile_list():
    for widget in profiles_frame.winfo_children():
        widget.destroy()

    profiles = app_data.get('profiles', [])

    if not profiles:
        customtkinter.CTkLabel(
            profiles_frame,
            text="No profiles yet.\nClick “Create Profile” to add one.",
            font=FONT_BODY,
            text_color=styles.TEXT_MUTED,
            justify="center",
        ).pack(pady=40)
        return

    for idx, profile in enumerate(profiles):
        # Discord-style card per profile
        item_frame = customtkinter.CTkFrame(
            profiles_frame,
            fg_color=styles.CARD_BG,
            corner_radius=styles.RADIUS_CARD,
            border_width=1,
            border_color=styles.BORDER,
        )
        item_frame.pack(pady=6, padx=4, fill="x")

        header_btn = customtkinter.CTkButton(
            item_frame,
            text=profile["profileTitle"],
            font=FONT_BOLD,
            fg_color="transparent",
            hover_color=styles.CARD_HOVER,
            text_color=styles.TEXT_PRIMARY,
            corner_radius=styles.RADIUS_CARD,
            anchor="w",
            height=40,
        )
        header_btn.pack(fill="x", padx=4, pady=4)

        # hidden details frame
        details_frame = customtkinter.CTkFrame(item_frame, fg_color="transparent")
        customtkinter.CTkLabel(
            details_frame,
            text=f"Target executable:  {profile['targetExe']}",
            font=FONT_SMALL,
            text_color=styles.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 2))
        customtkinter.CTkLabel(
            details_frame,
            text=f"Details:  {profile.get('details', 'None')}",
            font=FONT_SMALL,
            text_color=styles.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 2))
        if profile.get('state'):
            customtkinter.CTkLabel(
                details_frame,
                text=f"State:  {profile['state']}",
                font=FONT_SMALL,
                text_color=styles.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 6))

        button_row = customtkinter.CTkFrame(details_frame, fg_color="transparent")
        button_row.pack(fill="x", padx=16, pady=(2, 12))
        customtkinter.CTkButton(
            button_row,
            text="Edit",
            command=lambda p=profile: open_editor(p),
            font=FONT_SMALL,
            height=32,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.ACCENT,
            hover_color=styles.ACCENT_HOVER,
            text_color=styles.TEXT_PRIMARY,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        customtkinter.CTkButton(
            button_row,
            text="Delete",
            command=lambda p=profile: delete_profile(p),
            font=FONT_SMALL,
            height=32,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.DANGER,
            hover_color=styles.DANGER_HOVER,
            text_color=styles.TEXT_PRIMARY,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        def delete_profile(profile):
            app_data["profiles"].remove(profile)
            save_data()
            refresh_profile_list()

        # toggling the hidden frame
        def make_toggle(frame_to_toggle):
            def toggle():
                if frame_to_toggle.winfo_ismapped():
                    frame_to_toggle.pack_forget()
                else:
                    frame_to_toggle.pack(fill="x", padx=4, pady=(0, 4))
            return toggle

        header_btn.configure(command=make_toggle(details_frame))

# initial list on startup
refresh_profile_list()

bottom_frame = customtkinter.CTkFrame(app, fg_color="transparent")
bottom_frame.pack(pady=(0, 20), padx=16, fill="x")

createProfileButton = customtkinter.CTkButton(
    bottom_frame,
    text="Create Profile",
    command=open_editor,
    font=FONT_BOLD,
    height=40,
    corner_radius=styles.RADIUS_BUTTON,
    fg_color=styles.ACCENT,
    hover_color=styles.ACCENT_HOVER,
    text_color=styles.TEXT_PRIMARY,
)
createProfileButton.pack(fill="x", pady=(0, 10))

controls_frame = customtkinter.CTkFrame(bottom_frame, fg_color="transparent")
controls_frame.pack(fill="x")

startButton = customtkinter.CTkButton(
    controls_frame,
    text="Start",
    font=FONT_BOLD,
    height=40,
    corner_radius=styles.RADIUS_BUTTON,
    fg_color=styles.SUCCESS,
    hover_color=styles.SUCCESS_HOVER,
    text_color=styles.TEXT_PRIMARY,
)
startButton.pack(side="left", expand=True, fill="x", padx=(0, 5))

stopButton = customtkinter.CTkButton(
    controls_frame,
    text="Stop",
    font=FONT_BOLD,
    height=40,
    corner_radius=styles.RADIUS_BUTTON,
    fg_color=styles.DANGER,
    hover_color=styles.DANGER_HOVER,
    text_color=styles.TEXT_PRIMARY,
)
stopButton.pack(side="left", expand=True, fill="x", padx=(5, 0))

app.protocol('WM_DELETE_WINDOW', hide_window)
