# image_search.py — online PNG candidate fetcher (DuckDuckGo scrape, Google CSE fallback)
import io
import os
import re
import requests
from PIL import Image

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": "https://duckduckgo.com/",
}

# In-memory cache for the session: query -> list of (url, PIL.Image)
_cache = {}


def fetch_png_candidates(query, n=12):
    # Returns a list of (url, PIL.Image) thumbnails. Empty list on failure.
    key = (query.strip().lower(), n)
    if key in _cache:
        return _cache[key]

    urls = _duckduckgo_png_urls(query, n * 3)
    if not urls:
        urls = _google_cse_png_urls(query, n * 3)

    results = []
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        img = _download_image(url)
        if img is not None:
            results.append((url, img))
        if len(results) >= n:
            break

    _cache[key] = results
    return results


def _duckduckgo_png_urls(query, limit):
    try:
        session = requests.Session()
        session.headers.update(_HEADERS)

        token_res = session.post("https://duckduckgo.com/", data={"q": query}, timeout=10)
        vqd = _extract_vqd(token_res.text)
        if not vqd:
            return []

        params = {
            "l": "us-en",
            "o": "json",
            "q": query,
            "vqd": vqd,
            "f": ",,,,,",
            "p": "1",
        }
        res = session.get("https://duckduckgo.com/i.js", params=params, timeout=10)
        data = res.json()
    except Exception as exc:
        print(f"DuckDuckGo image search failed: {exc}")
        return []

    urls = []
    for item in data.get("results", []):
        image_url = item.get("image", "")
        if _looks_png(image_url):
            urls.append(image_url)
        if len(urls) >= limit:
            break
    return urls


def _extract_vqd(text):
    for pattern in (r'vqd="([\d-]+)"', r"vqd='([\d-]+)'", r"vqd=([\d-]+)&"):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _google_cse_png_urls(query, limit):
    api_key = os.environ.get("GOOGLE_CSE_KEY")
    cx = os.environ.get("GOOGLE_CSE_CX")
    if not api_key or not cx:
        return []

    try:
        res = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": cx,
                "q": query,
                "searchType": "image",
                "fileType": "png",
                "num": min(10, limit),
            },
            timeout=10,
        )
        data = res.json()
    except Exception as exc:
        print(f"Google CSE image search failed: {exc}")
        return []

    return [item.get("link", "") for item in data.get("items", []) if _looks_png(item.get("link", ""))]


def _looks_png(url):
    if not url:
        return False
    clean = url.split("?")[0].lower()
    return clean.endswith(".png")


def _download_image(url):
    try:
        res = requests.get(url, headers=_HEADERS, timeout=10)
        if res.status_code != 200:
            return None
        content_type = res.headers.get("content-type", "").lower()
        if "image/png" not in content_type and not _looks_png(url):
            return None
        img = Image.open(io.BytesIO(res.content))
        img.load()
        return img.convert("RGBA")
    except Exception:
        return None
