import gui
import rpc_manager
import process_monitor
import time
import threading
import json

running = False
background_thread = None

def background_loop(data):
    exe_name = data['targetExe']
    clientId = data['clientId']
    statusName = data['statusName']
    statusState = data['statusState']

    while running:
        if process_monitor.is_process_running(exe_name) and not rpc_manager.is_rpc_connected():
            rpc_manager.connect_to_discord(clientId)
            rpc_manager.update_presence(statusName, 'Take 2...', statusState, 'dog')
        
        if not process_monitor.is_process_running(exe_name) and rpc_manager.is_rpc_connected():
            rpc_manager.clear_presence()

        time.sleep(15)

    rpc_manager.clear_presence()


def on_start_clicked():
    global background_thread, running
    data = gui.get_data()
    save_to_json(data)


    if not running:
        running = True
        background_thread = threading.Thread(target=background_loop, args=(data,), daemon=True)
        background_thread.start()
        print('Background thread started.')

def on_stop_clicked():
    global running
    running = False
    print('Background thread stopped.')


def save_to_json(data):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


gui.startButton.configure(command=on_start_clicked)
gui.stopButton.configure(command=on_stop_clicked)
gui.app.mainloop()






