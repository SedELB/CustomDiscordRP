# CustomRP

CustomRP is a Windows system tray app that manages your Discord Rich Presence per application. It runs in the background, detects when a profiled app is running, and updates your Discord status to match — then clears it when the app closes.

![Main window](docs/images/main.png)

## Features

- Per-app profiles mapping an executable to a custom Discord status.
- Live editor with a Discord-style preview card that updates as you type.
- Logo search (free, no API key) and local image upload, both auto-hosted so they actually appear in Discord.
- Automatic detection within about two seconds; status clears when the app closes.
- Run on startup, a system tray icon with idle/active/error states, and your connected Discord account shown in the header.

## Requirements

- Windows 10 or 11
- The Discord desktop app, running
- Python 3.11 or newer (only to run from source)

## Install and run

1. Install Python 3.11+ from https://www.python.org/downloads/ and tick **Add Python to PATH** on the first screen.
2. Get the code: download this repo as a ZIP and extract it, or `git clone <repository-url>`.
3. From the project folder, install the dependencies and run:

```
py -m pip install -r requirements.txt
py main.py
```

The window opens and an icon is added to your tray. Closing the window hides it to the tray; to quit, right-click the tray icon and choose Quit.

## Get a Discord Application ID

Each profile needs a Discord Application ID so Discord knows which app the presence belongs to.

1. Go to https://discord.com/developers/applications and sign in.
2. Click **New Application**, name it (this name becomes the bold title in your status), and Create.
3. Open **General Information** and copy the **Application ID**.

You don't need to upload anything in the portal — CustomRP handles images for you.

## Create a profile

Click **New profile** to open the editor.

![Profile editor](docs/images/editor.png)

The card at the top is a live preview of exactly what Discord will show — type the application name (bold), details, and state directly on it. Then set:

- **Executable** — click Browse and pick the program's `.exe` (e.g. `SLDWORKS.exe`), or type its name. The profile is active while that process runs.
- **Application ID** — paste the Discord Application ID from above.
- **Show elapsed time** — toggle the timer on or off.

Click **Save profile**.

## Set the presence image

Click the game image on the preview card to open the chooser.

![Image chooser](docs/images/picker.png)

- **Search logos** — type a brand or app name, press Search, and click a result (free source, no API key).
- **Upload** — choose a local PNG, JPG, ICO, or WEBP.

Either way CustomRP hosts the image and fills in the URL automatically so it renders in Discord. The image is uploaded to a public host so Discord can read it.

Worth knowing:

- A local file on its own won't appear in Discord — that's why CustomRP hosts it.
- The round avatar on the card is your real Discord avatar, shown read-only. Rich Presence can't change it; only the game image is editable.

## Monitoring and startup

Click **Start monitoring** in the bottom status bar. When a profiled app is detected the indicator turns **Active** and your Discord status updates within about two seconds. Click **Stop monitoring**, or quit from the tray, to stop.

Turn on **Run on startup** to launch CustomRP into the tray with monitoring already running whenever Windows starts. Switch it back off to disable.

## Troubleshooting

- **Status doesn't appear** — make sure Discord is open and you clicked Start monitoring. The tray icon turns red and reads "Discord not detected" when Discord isn't found.
- **Image doesn't show in Discord** — set it through the chooser (which hosts it) or paste a public image URL into the large image field. A local file alone won't appear.
- **Wrong app detected, or none** — the target must match the process name exactly (e.g. `SLDWORKS.exe`). Using Browse avoids typos.
