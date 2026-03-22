import customtkinter
import json
import os

app = customtkinter.CTk()
app.geometry("400x600")


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

def open_profiles_popup():
    popup = customtkinter.CTkToplevel(app)
    popup.geometry("400x600")
    popup.title("New Profile")
    popup.attributes("-topmost", True)

    profileNameLabel = customtkinter.CTkLabel(popup, text="Profile Title")
    profileNameLabel.pack(pady=(10, 0))
    profileNameEntry = customtkinter.CTkEntry(popup, placeholder_text='Profile Title')
    profileNameEntry.pack(pady=10)

    targetLabel = customtkinter.CTkLabel(popup, text="Executable name")
    targetLabel.pack(pady=(10, 0))
    targetExeEntry = customtkinter.CTkEntry(popup, placeholder_text='Target .exe')
    targetExeEntry.pack(pady=10)

    statusNameLabel = customtkinter.CTkLabel(popup, text="Name of the application")
    statusNameLabel.pack(pady=(10, 0))
    statusNameEntry = customtkinter.CTkEntry(popup, placeholder_text='e.g. Playing X')
    statusNameEntry.pack(pady=10)

    detailsLabel = customtkinter.CTkLabel(popup, text="Details")
    detailsLabel.pack(pady=(10, 0))
    detailsEntry = customtkinter.CTkEntry(popup, placeholder_text='e.g. Working on a file')
    detailsEntry.pack(pady=10)

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
        refresh_profile_list()  # <--- Update the UI immediately!
        popup.destroy()

    save_btn = customtkinter.CTkButton(popup, text="Save Profile", command=save_new_profile)
    save_btn.pack(pady=10)


# Scrollable List
profiles_frame = customtkinter.CTkScrollableFrame(app, label_text="Saved Profiles", width=500, height=300)
profiles_frame.pack(pady=20, padx=20, fill="both", expand=True)

def refresh_profile_list():
    for widget in profiles_frame.winfo_children():
        widget.destroy()

    for idx, profile in enumerate(app_data.get('profiles', [])):
        # Container frame for the profile
        item_frame = customtkinter.CTkFrame(profiles_frame)
        item_frame.pack(pady=5, padx=5, fill="x")

        header_btn = customtkinter.CTkButton(
            item_frame, 
            text=profile["profileTitle"], 
            fg_color="transparent", 
            border_width=1,
            text_color=("gray10", "#DCE4EE"),
            anchor="w"
        )
        
        header_btn.pack(fill="x", padx=5, pady=5)

        # hidden details frame
        details_frame = customtkinter.CTkFrame(item_frame, fg_color="transparent")
        customtkinter.CTkLabel(details_frame, text=f"Target executable name: {profile['targetExe']}", anchor="w").pack(fill="x", padx=20)
        customtkinter.CTkLabel(details_frame, text=f"Details of the rich presence: {profile.get('details', 'None')}", anchor="w").pack(fill="x", padx=20)
        customtkinter.CTkButton(details_frame, text="Delete profile", command=lambda: delete_profile(profile)).pack(fill="x", padx=20)
        

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
                    frame_to_toggle.pack(fill="x", padx=5, pady=(0, 5))
            return toggle
            
        header_btn.configure(command=make_toggle(details_frame))

# initial list on startup
refresh_profile_list()

bottom_frame = customtkinter.CTkFrame(app, fg_color="transparent")
bottom_frame.pack(pady=20, fill="x")

createProfileButton = customtkinter.CTkButton(bottom_frame, text="Create Profile", command=open_profiles_popup)
createProfileButton.pack(side="left", padx=20, expand=True)

startButton = customtkinter.CTkButton(bottom_frame, text="Start", fg_color="#2b8a3e", hover_color="#237032")
startButton.pack(side="left", padx=10, expand=True)

stopButton = customtkinter.CTkButton(bottom_frame, text="Stop", fg_color="#c92a2a", hover_color="#a61e1e")
stopButton.pack(side="left", padx=10, expand=True)

app.protocol('WM_DELETE_WINDOW', hide_window)