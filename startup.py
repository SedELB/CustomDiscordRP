# startup.py — manage the "run on Windows startup" entry (HKCU Run key, no admin).
import os
import sys

try:
    import winreg
except ImportError:  # non-Windows; toggle becomes a no-op
    winreg = None

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "CustomRP"


def _launch_command():
    # Command Windows runs at login. --startup => hidden in tray + monitoring on.
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --startup'
    # Prefer pythonw.exe so no console window pops up on boot.
    py = sys.executable
    pyw = os.path.join(os.path.dirname(py), "pythonw.exe")
    exe = pyw if os.path.exists(pyw) else py
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    return f'"{exe}" "{main_py}" --startup'


def is_enabled():
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, _VALUE_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable():
    if winreg is None:
        return False
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _launch_command())
        return True
    except OSError as exc:
        print(f"startup enable failed: {exc}")
        return False


def disable():
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, _VALUE_NAME)
        return True
    except FileNotFoundError:
        return True  # already absent
    except OSError as exc:
        print(f"startup disable failed: {exc}")
        return False


def set_enabled(enabled):
    return enable() if enabled else disable()
