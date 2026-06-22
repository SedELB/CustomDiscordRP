# Helpers for the local Discord account surfaced by the RPC handshake.
# The user dict looks like {"id", "username", "global_name", "avatar"}.
CDN = "https://cdn.discordapp.com"


def display_name(user):
    if not user:
        return None
    return user.get("global_name") or user.get("username")


def avatar_url(user, size=128):
    """Build the CDN URL for a user's avatar, falling back to Discord's default
    colored avatar when the account has no custom one."""
    if not user:
        return None
    uid = user.get("id")
    avatar = user.get("avatar")
    if uid and avatar:
        ext = "gif" if str(avatar).startswith("a_") else "png"
        return f"{CDN}/avatars/{uid}/{avatar}.{ext}?size={size}"
    if uid:
        try:
            index = (int(uid) >> 22) % 6
        except (TypeError, ValueError):
            index = 0
        return f"{CDN}/embed/avatars/{index}.png"
    return None
