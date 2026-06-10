import gui, rpc_manager, process_monitor, tray_icon
import time, threading, argparse, pystray

DEFAULT_CLIENT_ID = "1482109796915220491"
POLL_SECONDS = 2

running = False
background_thread = None
forced_profile_id = None


def _client_id_for(profile, data):
    return profile.get('discord_app_id') or data.get('clientId') or DEFAULT_CLIENT_ID


def _find_by_id(data, profile_id):
    for profile in data.get('profiles', []):
        if profile.get('id') == profile_id:
            return profile
    return None


def background_loop():
    global running
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
            if rpc_manager.ensure_connected(client_id):
                st = start_time if profile.get('show_elapsed', True) else None
                rpc_manager.update_from_profile(profile, st)
                tray_icon.set_state('active', f"CustomRP — {profile.get('profileTitle', 'Active')}")
            else:
                tray_icon.set_state('error', "Discord not detected")
        else:
            if rpc_manager.is_connected():
                rpc_manager.clear_presence()
            tray_icon.set_state('idle', "CustomRP — idle")

        time.sleep(POLL_SECONDS)

    rpc_manager.clear_presence()
    tray_icon.set_state('idle', "CustomRP — stopped")


def start_monitoring():
    global background_thread, running
    if running:
        return
    running = True
    background_thread = threading.Thread(target=background_loop, daemon=True)
    background_thread.start()
    print('Background thread started.')


def stop_monitoring():
    global running
    running = False
    rpc_manager.clear_presence()
    print('Background thread stopped.')


def show_window_from_tray(icon, item):
    gui.app.after(0, gui.app.deiconify)


def quit_from_tray(icon, item):
    global running
    running = False
    rpc_manager.disconnect()
    icon.stop()
    gui.app.after(0, gui.app.destroy)


tray_icon.tray_icon.menu = pystray.Menu(
    pystray.MenuItem('Show App', show_window_from_tray),
    pystray.MenuItem('Quit', quit_from_tray)
)


def on_start_clicked():
    start_monitoring()


def on_stop_clicked():
    stop_monitoring()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=str, help="Profile ID to activate on launch")
    parser.add_argument("--launch", action="store_true", help="Immediately activate profile and start monitoring")
    args, _unknown = parser.parse_known_args()
    return args


args = _parse_args()
if args.profile:
    forced_profile_id = args.profile

# Tray runs while the GUI is hidden.
task_icon_thread = threading.Thread(target=tray_icon.tray_icon.run, daemon=True)
task_icon_thread.start()

gui.startButton.configure(command=on_start_clicked)
gui.stopButton.configure(command=on_stop_clicked)

# A .bat launcher passes --launch to activate immediately without clicking Start.
if args.launch:
    start_monitoring()

gui.app.mainloop()
