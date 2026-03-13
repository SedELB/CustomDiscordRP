import psutil as ps

def is_process_running(exe_name: str) -> bool:
    for process in ps.process_iter(attrs=['name']):
        if process.info['name'] == exe_name:
            return True
            
    return False

