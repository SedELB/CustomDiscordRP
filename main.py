import gui, rpc_manager, process_monitor, tray_icon
import time
import threading
import json
import os
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
            rpc_manager.update_presence(active_profile['statusName'], 'Details Here', active_profile['statusState'], 'dog')
        
        if not active_profile and rpc_manager.is_rpc_connected():
            rpc_manager.clear_presence()

        time.sleep(15)

    rpc_manager.clear_presence()



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
    print('Background thread stopped.')


gui.startButton.configure(command=on_start_clicked)
gui.stopButton.configure(command=on_stop_clicked)
gui.app.mainloop()