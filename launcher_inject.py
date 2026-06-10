# launcher_inject.py — generate a .bat (and optional .lnk) that activates a
# profile and then launches the target executable.
import os
import sys


def _app_launch_command():
    # How to invoke this app, whether frozen by PyInstaller or run from source.
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    return f'"{sys.executable}" "{main_py}"'


def make_bat_launcher(profile):
    # Returns (bat_path, error). error is None on success.
    exe_path = profile.get("exe_path", "").strip()
    if not exe_path:
        return None, "This profile has no executable path. Set one with Browse first."
    if not os.path.exists(exe_path):
        return None, f"Executable not found:\n{exe_path}"

    profile_id = profile.get("id")
    if not profile_id:
        return None, "This profile has no id. Save it first."

    target_dir = os.path.dirname(exe_path)
    exe_name = os.path.basename(exe_path)
    base = os.path.splitext(exe_name)[0]
    bat_path = os.path.join(target_dir, f"{base}_rp_launcher.bat")

    launch_cmd = _app_launch_command()
    lines = [
        "@echo off",
        f'start "" {launch_cmd} --profile {profile_id} --launch',
        f'start "" "%~dp0{exe_name}" %*',
        "",
    ]

    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as exc:
        return None, f"Could not write launcher:\n{exc}"

    return bat_path, None


def make_shortcut(bat_path):
    # Optional .lnk pointing at the .bat, so it can be pinned. Needs pywin32.
    try:
        import win32com.client  # type: ignore
    except ImportError:
        return None, "pywin32 is not installed, so a .lnk shortcut can't be created."

    lnk_path = os.path.splitext(bat_path)[0] + ".lnk"
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(lnk_path)
        shortcut.TargetPath = bat_path
        shortcut.WorkingDirectory = os.path.dirname(bat_path)
        shortcut.WindowStyle = 7  # minimized
        shortcut.save()
    except Exception as exc:
        return None, f"Could not create shortcut:\n{exc}"

    return lnk_path, None
