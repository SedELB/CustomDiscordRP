# discord_user.py — helpers for the local Discord account surfaced by the RPC
# handshake (see rpc_manager._UserPresence). The user dict looks like:
#   {"id": "...", "username": "...", "global_name": "...", "avatar": "<hash>"}
CDN = "https://cdn.discordapp.com"


def display_name(user):
    if not user:
        return None
    return user.get("global_name") or user.get("username")


def handle(user):
    # The @username (new system has discriminator "0").
    if not user:
        return None
    name = user.get("username")
    disc = user.get("discriminator")
    if name and disc and disc != "0":
        return f"{name}#{disc}"
    return name


def avatar_url(user, size=128):
    if not user:
        return None
    uid = user.get("id")
    avatar = user.get("avatar")
    if uid and avatar:
        ext = "gif" if str(avatar).startswith("a_") else "png"
        return f"{CDN}/avatars/{uid}/{avatar}.{ext}?size={size}"
    # No custom avatar — fall back to Discord's default colored avatar.
    if uid:
        try:
            index = (int(uid) >> 22) % 6
        except (TypeError, ValueError):
            index = 0
        return f"{CDN}/embed/avatars/{index}.png"
    return None
