# image_search.py — pure helpers for logo search results (no network here).
# All HTTP goes through qt_net.Net so it runs on Qt's event loop; this module
# only parses responses and rewrites Brandfetch icon URLs.
import json


def parse_logo_results(json_bytes, query="", n=8):
    # Returns a list of {name, url} from a Brandfetch search response.
    if not json_bytes:
        return []
    try:
        data = json.loads(json_bytes)
    except Exception:
        return []

    results = []
    for brand in data:
        icon = brand.get("icon")
        if not icon:
            continue
        results.append({
            "name": brand.get("name") or brand.get("domain") or query,
            "url": hires_png(icon),
        })
        if len(results) >= n:
            break
    return results


def hires_png(icon_url):
    # Bump Brandfetch's 128px webp thumbnail to a larger transparent PNG.
    url = icon_url.replace("/w/128/h/128/", "/w/400/h/400/")
    url = url.replace("/fallback/lettermark/", "/fallback/transparent/")
    url = url.replace("/icon.webp", "/icon.png")
    return url
