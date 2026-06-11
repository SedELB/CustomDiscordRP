import argparse
import sys
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication

import styles
import qt_utils
import rpc_manager
import process_monitor

DEFAULT_CLIENT_ID = "1482109796915220491"
POLL_SECONDS = 2

running = False
forced_profile_id = None


class Bridge(QObject):
    # Thread-safe channel from the monitor thread into the UI.
    activity = pyqtSignal(object)        # profile title or None
    tray_state = pyqtSignal(str, str)    # state, tooltip


bridge = Bridge()


def _client_id_for(profile, data):
    return profile.get('discord_app_id') or data.get('clientId') or DEFAULT_CLIENT_ID


def _find_by_id(data, profile_id):
    for profile in data.get('profiles', []):
        if profile.get('id') == profile_id:
            return profile
    return None


def background_loop():
    global running
    import gui
    while running:
        data = gui.get_data()  # re-read each pass so edits apply live

        profile, start_time = process_monitor.find_active_profile(data.get('profiles', []))

        # --launch override: activate the requested profile even before its exe is seen.
        if profile is None and forced_profile_id:
            forced = _find_by_id(data, forced_profile_id)
            if forced:
                profile = forced
                start_time = time.time()

        if profile:
            client_id = _client_id_for(profile, data)
            title = profile.get('profileTitle', 'Active')
            if rpc_manager.ensure_connected(client_id):
                st = start_time if profile.get('show_elapsed', True) else None
                rpc_manager.update_from_profile(profile, st)
                bridge.tray_state.emit('active', f"CustomRP — {title}")
                bridge.activity.emit(title)
            else:
                bridge.tray_state.emit('error', "Discord not detected")
                bridge.activity.emit(None)
        else:
            if rpc_manager.is_connected():
                rpc_manager.clear_presence()
            bridge.tray_state.emit('idle', "CustomRP — idle")
            bridge.activity.emit(None)

        time.sleep(POLL_SECONDS)

    rpc_manager.clear_presence()
    bridge.tray_state.emit('idle', "CustomRP — stopped")


def start_monitoring():
    global running
    if running:
        return
    running = True
    threading.Thread(target=background_loop, daemon=True).start()


def stop_monitoring():
    global running
    running = False
    rpc_manager.clear_presence()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=str, help="Profile ID to activate on launch")
    parser.add_argument("--launch", action="store_true", help="Immediately activate profile and start monitoring")
    args, _unknown = parser.parse_known_args()
    return args


def main():
    global forced_profile_id

    args = _parse_args()
    if args.profile:
        forced_profile_id = args.profile

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(qt_utils.app_icon())
    app.setFont(QFont(styles.FONT_FAMILY, 10))
    app.setStyleSheet(styles.QSS)

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(styles.TEXT_MUTED))
    app.setPalette(palette)

    import gui
    import tray_icon

    window = gui.MainWindow()

    def quit_app():
        stop_monitoring()
        rpc_manager.disconnect()
        app.quit()

    tray = tray_icon.Tray(window, quit_app)
    tray.show()

    def toggle_power():
        if running:
            stop_monitoring()
        else:
            start_monitoring()
        window.update_power_visual(running)

    window.power_button.clicked.connect(toggle_power)
    bridge.activity.connect(window.report_activity)
    bridge.tray_state.connect(tray.set_state)

    if args.launch:
        # Launched from a .bat wrapper: start monitoring immediately, stay in the tray.
        start_monitoring()
        window.update_power_visual(True)
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
