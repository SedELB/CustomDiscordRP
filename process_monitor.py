import psutil as ps

def is_process_running(exe_name: str) -> bool:
    for process in ps.process_iter(attrs=['name']):
        if process.info['name'] == exe_name:
            print('Process found !')
            return True

    print('Process not found')
    return False

