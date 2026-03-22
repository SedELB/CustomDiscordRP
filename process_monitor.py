import psutil as ps

def is_process_running(exe_name: str) -> bool:
    for process in ps.process_iter(attrs=['name']):
        if process.info['name'] == exe_name:
            return True
            
    return False


def get_running_target(exe_list):
    running_processes = []
    for executable in exe_list:
        if is_process_running(executable):
            running_processes.append(executable)
    
    return running_processes



