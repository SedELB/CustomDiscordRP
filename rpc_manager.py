import json
import struct

from pypresence import Presence
from pypresence.exceptions import (
    DiscordNotFound, PipeClosed, InvalidPipe, InvalidID, DiscordError,
)
from pypresence.types import ActivityType
from pypresence.utils import get_ipc_path

RPC = None
_connected = False
_current_client_id = None
_user = None             # local Discord user from the RPC handshake (id, username, avatar, …)
_notified_missing = False  # throttle the "Discord not running" log to once per outage


class _UserPresence(Presence):
    """pypresence parses the handshake READY payload and discards it. We override
    the handshake to keep the `user` object it carries — that's the Discord
    account currently running the local client (no OAuth needed)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    async def handshake(self):
        ipc_path = get_ipc_path(self.pipe)
        if not ipc_path:
            raise DiscordNotFound

        await self.create_reader_writer(ipc_path)
        self.send_data(0, {"v": 1, "client_id": self.client_id})
        preamble = await self.sock_reader.read(8)
        if len(preamble) < 8:
            raise InvalidPipe
        code, length = struct.unpack("<ii", preamble)
        data = json.loads(await self.sock_reader.read(length))
        if "code" in data:
            if data.get("message") == "Invalid Client ID":
                raise InvalidID
            raise DiscordError(data["code"], data["message"])
        try:
            self.user = data.get("data", {}).get("user")
        except Exception:
            self.user = None
        if self._events_on:
            self.sock_reader.feed_data = self.on_event


def connect(client_id):
    global RPC, _connected, _current_client_id, _user, _notified_missing
    try:
        RPC = _UserPresence(client_id)
        RPC.connect()
        _connected = True
        _current_client_id = client_id
        _notified_missing = False
        if getattr(RPC, "user", None):
            _user = RPC.user
        return True
    except DiscordNotFound:
        if not _notified_missing:
            print("Discord client not running.")
            _notified_missing = True
        _connected = False
        _current_client_id = None
        _user = None
        return False
    except Exception as exc:
        print(f"RPC connect failed: {exc}")
        _connected = False
        _current_client_id = None
        return False


def is_connected():
    return _connected


def get_user():
    return _user


def ensure_connected(client_id):
    """(Re)connect if disconnected or the app id changed (profile switch / Discord restart)."""
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
    """Clear the activity but keep the connection alive."""
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
