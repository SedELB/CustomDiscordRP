import customtkinter
import json
import os
import styles

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


# Styled input helpers — keep the create-profile form consistent with the theme.
def add_field_label(parent, text):
    label = customtkinter.CTkLabel(parent, text=text, font=FONT_BOLD, text_color=styles.TEXT_PRIMARY, anchor="w")
    label.pack(fill="x", padx=24, pady=(14, 2))
    return label

def add_field_entry(parent, placeholder):
    entry = customtkinter.CTkEntry(
        parent,
        placeholder_text=placeholder,
        font=FONT_BODY,
        height=36,
        corner_radius=styles.RADIUS_INPUT,
        fg_color=styles.BG_TERTIARY,
        border_color=styles.BORDER,
        border_width=1,
        text_color=styles.TEXT_PRIMARY,
    )
    entry.pack(fill="x", padx=24)
    return entry


def open_profiles_popup():
    popup = customtkinter.CTkToplevel(app)
    popup.geometry("420x560")
    popup.title("New Profile")
    popup.configure(fg_color=styles.BG_PRIMARY)
    popup.attributes("-topmost", True)

    customtkinter.CTkLabel(
        popup, text="Create Profile", font=FONT_HEADER, text_color=styles.TEXT_PRIMARY, anchor="w"
    ).pack(fill="x", padx=24, pady=(20, 4))

    add_field_label(popup, "Profile Title")
    profileNameEntry = add_field_entry(popup, 'Profile Title')

    add_field_label(popup, "Executable name")
    targetExeEntry = add_field_entry(popup, 'Target .exe')

    add_field_label(popup, "Name of the application")
    statusNameEntry = add_field_entry(popup, 'e.g. Playing X')

    add_field_label(popup, "Details")
    detailsEntry = add_field_entry(popup, 'e.g. Working on a file')

    def save_new_profile():
        new_profile = {
            "profileTitle": profileNameEntry.get(),
            "targetExe": targetExeEntry.get(),
            "statusName": statusNameEntry.get(),
            "details": detailsEntry.get()
        }

        if ".exe" not in new_profile["targetExe"]:
            new_profile["targetExe"] = new_profile["targetExe"] + ".exe"

        app_data["profiles"].append(new_profile)
        save_data()
        print(f"Profile saved! Target: {new_profile['targetExe']}")
        refresh_profile_list()
        popup.destroy()

    save_btn = customtkinter.CTkButton(
        popup,
        text="Save Profile",
        command=save_new_profile,
        font=FONT_BOLD,
        height=40,
        corner_radius=styles.RADIUS_BUTTON,
        fg_color=styles.ACCENT,
        hover_color=styles.ACCENT_HOVER,
        text_color=styles.TEXT_PRIMARY,
    )
    save_btn.pack(fill="x", padx=24, pady=24, side="bottom")


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
        ).pack(fill="x", padx=16, pady=(0, 8))
        customtkinter.CTkButton(
            details_frame,
            text="Delete profile",
            command=lambda p=profile: delete_profile(p),
            font=FONT_SMALL,
            height=32,
            corner_radius=styles.RADIUS_BUTTON,
            fg_color=styles.DANGER,
            hover_color=styles.DANGER_HOVER,
            text_color=styles.TEXT_PRIMARY,
        ).pack(fill="x", padx=16, pady=(0, 12))

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
    command=open_profiles_popup,
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
