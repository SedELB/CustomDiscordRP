from pypresence import Presence
from pypresence.types import ActivityType, StatusDisplayType
import time

client_id = '1482109796915220491'
RPC = Presence(client_id)
RPC.connect()

print('Discord RPC connected')

def update_presence(name, details, state, large_image_name):
    RPC.update(
        name=name,
        details=details,
        state=state,
        activity_type=ActivityType.LISTENING,
        large_image=large_image_name,
    )

    while True:
        time.sleep(15)

def clear_presence():
    RPC.clear()

    







