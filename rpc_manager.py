from pypresence import Presence, DiscordNotFound
from pypresence.types import ActivityType, StatusDisplayType
import time
RPC = None
_connected = False

def connect_to_discord(clientId):
    global RPC, _connected
    try: 
        RPC = Presence(clientId)
        RPC.connect()
        _connected = True
        return True
    except (DiscordNotFound, Exception):
        print('Error: Discord client not running.')
        _connected = False
        return False

def is_rpc_connected():
    global _connected
    return _connected


def update_presence(name, details, state, large_image_name):
    global RPC
    if RPC is None or not _connected:
        return
        
    RPC.update(
        name=name,
        details=details,
        state=state,
        activity_type=ActivityType.LISTENING,
        large_image=large_image_name,
    )

def clear_presence():
    global RPC, _connected
    if RPC is not None and _connected:
        RPC.clear()
        RPC.close()
        _connected = False







