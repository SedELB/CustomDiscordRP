import customtkinter

def button_callback():
    print("button clicked")

def get_data():
    data = {}

    data['clientId'] = clientIdEntry.get()
    data['targetExe'] = targetExeEntry.get()
    data['statusName'] = statusNameEntry.get()
    data['statusState'] = statusStateEntry.get()

    print(data)
    return data

app = customtkinter.CTk()
app.geometry("800x600")

startButton = customtkinter.CTkButton(app, text="Start")
stopButton = customtkinter.CTkButton(app, text="Stop")

clientIdEntry = customtkinter.CTkEntry(app, placeholder_text='Client ID')
targetExeEntry = customtkinter.CTkEntry(app, placeholder_text='Target .exe')

statusNameEntry = customtkinter.CTkEntry(app, placeholder_text='Your custom status name...')
statusStateEntry = customtkinter.CTkEntry(app, placeholder_text='Your custom state...')

startButton.pack()
stopButton.pack()

clientIdEntry.pack()
targetExeEntry.pack()

statusNameEntry.pack()
statusStateEntry.pack()