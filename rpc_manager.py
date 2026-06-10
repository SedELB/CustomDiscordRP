from pypresence import Presence
from pypresence.exceptions import DiscordNotFound, PipeClosed, InvalidPipe
from pypresence.types import ActivityType

RPC = None
_connected = False
_current_client_id = None


def connect(client_id):
    global RPC, _connected, _current_client_id
    try:
        RPC = Presence(client_id)
        RPC.connect()
        _connected = True
        _current_client_id = client_id
        return True
    except DiscordNotFound:
        print("Discord client not running.")
        _connected = False
        _current_client_id = None
        return False
    except Exception as exc:
        print(f"RPC connect failed: {exc}")
        _connected = False
        _current_client_id = None
        return False


def is_connected():
    return _connected


def ensure_connected(client_id):
    # (Re)connect if disconnected or the app id changed (profile switch / Discord restart).
    global _current_client_id
    if _connected and _current_client_id == client_id:
        return True
    if _connected and _current_client_id != client_id:
        disconnect()
    return connect(client_id)


def update_from_profile(profile, start_time=None):
    global _connected
    if RPC is None or not _connected:
        return False

    kwargs = {}
    name = profile.get("statusName") or None
    if name:
        kwargs["name"] = name
        kwargs["activity_type"] = ActivityType.PLAYING

    details = profile.get("details") or None
    if details:
        kwargs["details"] = details

    state = profile.get("state") or None
    if state:
        kwargs["state"] = state

    # Discord needs an asset key (uploaded to the dev portal) or a URL — a local
    # path won't render, so only forward a key/url when one is set.
    large_image = profile.get("large_image_key") or profile.get("large_image_url")
    if large_image:
        kwargs["large_image"] = large_image
        if profile.get("large_image_text"):
            kwargs["large_text"] = profile["large_image_text"]

    small_image = profile.get("small_image_key") or profile.get("small_image_url")
    if small_image:
        kwargs["small_image"] = small_image
        if profile.get("small_image_text"):
            kwargs["small_text"] = profile["small_image_text"]

    if start_time:
        kwargs["start"] = int(start_time)

    try:
        RPC.update(**kwargs)
        return True
    except (PipeClosed, InvalidPipe, BrokenPipeError, ConnectionResetError, OSError) as exc:
        # Socket dropped (Discord restarted/closed) — drop the connection so the
        # monitor loop reconnects on its next pass.
        print(f"RPC update failed, will reconnect: {exc}")
        _connected = False
        return False
    except Exception as exc:
        print(f"RPC update error: {exc}")
        return False


def clear_presence():
    # Clear the activity but keep the connection alive.
    global _connected
    if RPC is None or not _connected:
        return
    try:
        RPC.clear()
    except (PipeClosed, InvalidPipe, BrokenPipeError, ConnectionResetError, OSError):
        _connected = False
    except Exception as exc:
        print(f"RPC clear error: {exc}")


def disconnect():
    global RPC, _connected, _current_client_id
    if RPC is not None:
        try:
            RPC.close()
        except Exception:
            pass
    RPC = None
    _connected = False
    _current_client_id = None
