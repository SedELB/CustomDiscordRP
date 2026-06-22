import psutil as ps


def find_active_profile(profiles):
    """Return (profile, start_time) for the enabled profile whose target exe is
    running and started most recently, or (None, None) if none match."""
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
