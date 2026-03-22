import customtkinter
import json
import os

app = customtkinter.CTk()
app.geometry("800x600")


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

def open_profiles_popup():
    popup = customtkinter.CTkToplevel(app)
    popup.geometry("400x300")
    popup.title("New Profile")
    popup.attributes("-topmost", True)

    targetExeEntry = customtkinter.CTkEntry(popup, placeholder_text='Target .exe')
    statusNameEntry = customtkinter.CTkEntry(popup, placeholder_text='Your custom status name...')
    statusStateEntry = customtkinter.CTkEntry(popup, placeholder_text='Your custom state...')

    targetExeEntry.pack(pady=10)
    statusNameEntry.pack(pady=10)
    statusStateEntry.pack(pady=10)

    def save_new_profile():
        new_profile = {
            "targetExe": targetExeEntry.get(),
            "statusName": statusNameEntry.get(),
            "statusState": statusStateEntry.get()
        }

        if ".exe" not in new_profile["targetExe"]:
            new_profile["targetExe"] = new_profile["targetExe"] + ".exe"
        
        app_data["profiles"].append(new_profile)
        save_data()
        print(f"Profile saved! Target: {new_profile['targetExe']}")
        popup.destroy()

    save_btn = customtkinter.CTkButton(popup, text="Save Profile", command=save_new_profile)
    save_btn.pack(pady=10)


createProfileButton = customtkinter.CTkButton(app, text="Create custom profile", command=open_profiles_popup)
createProfileButton.pack(pady=40)

startButton = customtkinter.CTkButton(app, text="Start CustomRP")
startButton.pack(pady=10)

stopButton = customtkinter.CTkButton(app, text="Stop CustomRP")
stopButton.pack(pady=10)