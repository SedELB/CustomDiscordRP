import psutil as ps


def is_process_running(exe_name: str) -> bool:
    target = (exe_name or "").lower()
    if not target:
        return False
    for process in ps.process_iter(attrs=['name']):
        if (process.info.get('name') or '').lower() == target:
            return True
    return False


def get_running_target(exe_list):
    running_processes = []
    for executable in exe_list:
        if is_process_running(executable):
            running_processes.append(executable)
    return running_processes


def find_active_profile(profiles):
    # Among enabled profiles whose target exe is running, pick the one whose
    # process started most recently. Returns (profile, start_time) or (None, None).
    targets = {}
    for profile in profiles:
        if not profile.get('enabled', True):
            continue
        exe = (profile.get('targetExe') or '').lower()
        if exe:
            targets[exe] = profile

    if not targets:
        return None, None

    best_profile = None
    best_start = -1.0
    for process in ps.process_iter(attrs=['name', 'create_time']):
        name = (process.info.get('name') or '').lower()
        if name in targets:
            start = process.info.get('create_time') or 0.0
            if start > best_start:
                best_start = start
                best_profile = targets[name]

    if best_profile is None:
        return None, None
    return best_profile, best_start
