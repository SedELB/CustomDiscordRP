# CLAUDE.md — Discord Rich Presence Tray App Overhaul

## Project Overview

A Python system-tray executable that manages Discord Rich Presence per-application. It runs silently in the background, detects when a profiled `.exe` launches, and updates the user's Discord status accordingly. The overhaul focuses on four areas: UI redesign, profile management, live preview, and launcher injection.

---

## Architecture

```
discordrp/
├── main.py                  # Entry point — tray icon, app lifecycle
├── tray.py                  # System tray icon + menu (pystray)
├── monitor.py               # Process watcher loop (psutil)
├── rp_client.py             # Discord IPC / pypresence wrapper
├── profile_manager.py       # CRUD for profiles (JSON persistence)
├── image_search.py          # Online PNG fetcher (Google Custom Search or SerpAPI)
├── launcher_inject.py       # .bat / shortcut injector for profiled executables
├── ui/
│   ├── app.py               # Main window bootstrap (PyQt6 or tkinter ttk)
│   ├── profiles_page.py     # Profile list + add/edit/delete
│   ├── editor_page.py       # Profile editor with live Discord preview card
│   ├── image_picker.py      # Image search modal + local upload
│   └── styles.py            # Global Qt stylesheet (Discord dark theme tokens)
├── assets/
│   └── tray_icon.png
├── profiles/                # JSON profile store
│   └── profiles.json
└── requirements.txt
```

---

## Tech Stack

| Purpose | Library |
|---|---|
| GUI | **PyQt6** (preferred) or tkinter with ttkbootstrap |
| System tray | **pystray** |
| Process detection | **psutil** |
| Discord IPC | **pypresence** |
| HTTP / image search | **requests**, optionally **SerpAPI** or DuckDuckGo scrape |
| Image handling | **Pillow** |
| Packaging | **PyInstaller** (single `.exe` output) |

---

## Visual Design — Discord Dark Theme

All UI must match Discord's native feel. Do not use OS default widgets unstyled.

### Color Tokens

```python
# styles.py
BG_PRIMARY    = "#313338"   # main window background
BG_SECONDARY  = "#2b2d31"   # sidebar / panels
BG_TERTIARY   = "#1e1f22"   # input fields, cards
ACCENT        = "#5865f2"   # Discord blurple — buttons, active states
ACCENT_HOVER  = "#4752c4"
TEXT_PRIMARY  = "#f2f3f5"
TEXT_MUTED    = "#949ba4"
TEXT_LINK     = "#00b0f4"
DANGER        = "#ed4245"
SUCCESS       = "#23a55a"
BORDER        = "#3f4147"
CARD_BG       = "#232428"   # profile preview card background
```

### Typography

- Font: **Whitney** if available, otherwise fall back to **Noto Sans** → **Segoe UI** → system sans-serif.
- Use Qt's `setFont` globally with size 10pt body, 12pt headers.
- All labels sentence-case, never all-caps except section dividers.

### Component Rules

- All buttons: `border-radius: 3px`, `padding: 8px 16px`, no border, `background: ACCENT`.
- Input fields: `background: BG_TERTIARY`, `border: 1px solid BORDER`, `border-radius: 4px`, focus ring `ACCENT`.
- No gradients on interactive elements. Flat.
- Scrollbars: thin, `background: BG_SECONDARY`, handle `BG_PRIMARY`.

---

## Profile Schema

Each profile is stored in `profiles/profiles.json` as an array:

```json
{
  "id": "uuid4",
  "name": "SolidWorks 2024",
  "exe_path": "C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS/SLDWORKS.exe",
  "exe_name": "SLDWORKS.exe",
  "discord_app_id": "123456789012345678",
  "state": "Designing parts",
  "details": "SolidWorks 2024",
  "large_image_key": "solidworks_logo",
  "large_image_url": "https://...",
  "large_image_text": "SolidWorks",
  "small_image_key": null,
  "small_image_text": null,
  "show_elapsed": true,
  "enabled": true
}
```

- `discord_app_id` is set per-profile; user must create a Discord developer app. Guide them with a tooltip/link.
- Images are stored locally under `assets/profile_images/<id>.png` and uploaded to Discord CDN via the app's developer portal, **or** referenced by URL if pypresence supports it.

---

## Profile Editor — Live Preview Card

The editor (`editor_page.py`) is split into two columns:

**Left — Form fields:**
- Application name (text input)
- Executable path (file picker button)
- Discord App ID (text input + "How to get this" tooltip)
- State (text input, max 128 chars)
- Details (text input, max 128 chars)
- Large image (thumbnail + "Change image" button → opens `image_picker.py`)
- Large image tooltip text
- Small image (optional, same pattern)
- Show elapsed time (toggle/checkbox)
- Enable profile (toggle)

**Right — Discord Profile Preview Card:**

Render a pixel-faithful mock of Discord's "Now Playing" card using Qt widgets or a custom `QPainter` draw:

```
┌──────────────────────────────────┐
│  [large image 60×60]             │
│  ● Online                        │
│                                  │
│  PLAYING A GAME                  │
│  Details line                    │
│  State line                      │
│  00:00 elapsed                   │
└──────────────────────────────────┘
```

- Every keystroke on the left updates the card in real time via Qt signals (`textChanged`, etc.).
- The preview card background is `CARD_BG`. The "PLAYING A GAME" label is `TEXT_MUTED`, 9pt, spaced. App name bold `TEXT_PRIMARY`. Details/state `TEXT_PRIMARY` regular.
- The elapsed timer ticks live using a `QTimer` every second once the editor is open.
- If no image is selected, show a placeholder grey square with a camera icon.

---

## Image Picker (`image_picker.py`)

Opens as a modal dialog. Two tabs:

### Tab 1 — Search Online

1. User types a query (pre-filled with the profile name, e.g. "SolidWorks logo").
2. On Enter or "Search" button: call `image_search.fetch_png_candidates(query, n=12)`.
3. Display results as a 4×3 grid of thumbnails (80×80px, rounded corners, checkered background to show transparency).
4. User clicks one → it's selected and shown with a blue border.
5. "Use this image" button confirms and closes.

**`image_search.fetch_png_candidates(query, n)`:**
- Primary: DuckDuckGo Image Search scrape filtered to `filetype:png` (no API key required).
- Fallback: Google Custom Search JSON API if `GOOGLE_CSE_KEY` and `GOOGLE_CSE_CX` are set in a `.env`.
- Filter results: only URLs ending in `.png` or with `content-type: image/png`.
- Download each thumbnail as bytes, verify with Pillow, return list of `(url, PIL.Image)`.
- Cache downloads in memory for the session.

### Tab 2 — Upload from disk

- Simple file picker filtered to `.png`, `.jpg`, `.ico`, `.webp`.
- Pillow converts and crops to square, saves as `assets/profile_images/<id>.png`.
- Preview shown immediately.

---

## Launcher Injection (`launcher_inject.py`)

When the user saves a profile with an `exe_path`, the app optionally creates a launcher in the same directory as the target executable.

### Strategy: `.bat` wrapper

Create `<exe_name>_rp_launcher.bat` next to the `.exe`:

```bat
@echo off
start "" "C:\Path\To\discordrp\discordrp.exe" --profile <profile_id> --launch
start "" "%~dp0<exe_name>.exe" %*
```

- `--profile <id> --launch` tells the tray app to activate that profile immediately without waiting for process detection.
- `%*` forwards any arguments the user passed.
- Warn the user: "You'll need to run this `.bat` instead of the `.exe` directly, or pin it to your taskbar."

### Strategy: Windows Shortcut (optional enhancement)

Use `pywin32` to create a `.lnk` shortcut that calls the `.bat`. Offer this as an alternative so users can pin it to Start or taskbar with a proper icon.

### CLI args in `main.py`

```python
# main.py
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--profile", type=str, help="Profile ID to activate on launch")
parser.add_argument("--launch", action="store_true", help="Immediately activate profile and launch monitoring")
args = parser.parse_args()
```

---

## Process Monitor (`monitor.py`)

- Poll `psutil.process_iter(['name', 'exe'])` every 2 seconds.
- When a profiled `.exe` is detected as running: activate its Rich Presence via `rp_client.py`.
- When it stops: clear Rich Presence (or fall back to idle state).
- Support only one active profile at a time; if multiple profiled apps run simultaneously, the most recently started one wins.

---

## Discord RPC (`rp_client.py`)

```python
from pypresence import Presence
import time

class RPClient:
    def __init__(self, app_id: str): ...
    def connect(self): ...
    def update(self, state, details, large_image, large_text, start_time): ...
    def clear(self): ...
    def disconnect(self): ...
```

- Reconnect automatically if IPC socket drops (Discord restarts).
- Each profile has its own `app_id`; reconnect when switching profiles.

---

## Tray Icon (`tray.py`)

Menu items:
- **Open** — bring main window to front
- **Active profile: \<name\>** (greyed out, informational)
- Separator
- **Profiles** → submenu listing all profiles with enable/disable toggles
- **Settings**
- Separator
- **Quit**

Icon states: idle (grey), active (blurple), error (red).

---

## Settings

Minimal settings page:
- Run on Windows startup (add to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)
- Polling interval (1s / 2s / 5s)
- Google CSE API key + CX (optional, for image search)
- Default Discord App ID fallback

---

## Key Implementation Notes

1. **Never block the main thread.** Process polling and RPC updates go in `threading.Thread` or `QThread`. Image search runs in a `QRunnable` with signals back to the UI.

2. **Profile save is immediate.** Every field change auto-saves to `profiles.json` after a 500ms debounce. No explicit "Save" button needed (but show a subtle "Saved" flash).

3. **No internet required for core function.** Image search is a convenience feature; the app works fully offline once profiles are set up.

4. **Code style:** explicit `if` statements, flat logic, no nested ternaries. Single inline comments only, no docblock walls.

5. **Single `.exe` output** via PyInstaller `--onefile --windowed --icon=assets/tray_icon.ico`. Include `assets/` and `profiles/` in the spec file.

6. **Error handling:** if Discord is not running, the tray icon goes grey and a tooltip shows "Discord not detected." Retry every 10 seconds silently.

---

## Deliverables Checklist

- [ ] `main.py` bootstraps tray + window + process monitor
- [ ] `ui/editor_page.py` with live Discord card preview
- [ ] `ui/image_picker.py` with search grid + upload tab
- [ ] `image_search.py` DuckDuckGo PNG fetcher
- [ ] `launcher_inject.py` .bat generator
- [ ] `monitor.py` psutil polling loop
- [ ] `rp_client.py` pypresence wrapper with auto-reconnect
- [ ] `ui/styles.py` full Discord dark Qt stylesheet
- [ ] `profiles/profiles.json` schema and CRUD
- [ ] `requirements.txt`
- [ ] `discordrp.spec` PyInstaller spec