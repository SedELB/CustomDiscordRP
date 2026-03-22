import gui, rpc_manager, process_monitor, tray_icon
import time, threading, json, os, pystray
DEFAULT_CLIENT_ID = "1482109796915220491"
running = False
background_thread = None

def background_loop(data):
    clientId = data.get('clientId', DEFAULT_CLIENT_ID)
    
    while running:
        active_profile = None
        for profile in data.get('profiles', []):
            if process_monitor.is_process_running(profile['targetExe']):
                active_profile = profile
                break
                
        if active_profile and not rpc_manager.is_rpc_connected():
            rpc_manager.connect_to_discord(clientId)
            
        if active_profile and rpc_manager.is_rpc_connected():
            rpc_manager.update_presence(active_profile['statusName'], active_profile['details'], 'dog')
        
        if not active_profile and rpc_manager.is_rpc_connected():
            rpc_manager.clear_presence()

        time.sleep(15)

    rpc_manager.clear_presence()

def show_window_from_tray(icon, item):
    gui.app.after(0, gui.app.deiconify)

def quit_from_tray(icon, item):
    icon.stop()
    gui.app.after(0, gui.app.destroy)

tray_icon.tray_icon.menu = pystray.Menu(
    pystray.MenuItem('Show App', show_window_from_tray),
    pystray.MenuItem('Quit', quit_from_tray)
)


def on_start_clicked():
    global background_thread, running
    data = gui.get_data()

    if not running:
        running = True
        background_thread = threading.Thread(target=background_loop, args=(data,), daemon=True)
        background_thread.start()
        print('Background thread started.')

def on_stop_clicked():
    global running
    running = False
    rpc_manager.clear_presence()
    print('Background thread stopped.')

# Thread running while GUI is closed
task_icon_thread = threading.Thread(target=tray_icon.tray_icon.run, daemon=True)
task_icon_thread.start()

gui.startButton.configure(command=on_start_clicked)
gui.stopButton.configure(command=on_stop_clicked)
gui.app.mainloop()