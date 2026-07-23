#!/usr/bin/env python3
import json
import urllib.parse

from build_images import FULL, THUMBS, WIKI_UA, http_get, to_webp_full, to_webp_thumb, verify_image


FILENAME = "Département Alpes-Maritimes logo 2.svg"


def frwiki_thumb_url(filename):
    api = (
        "https://fr.wikipedia.org/w/api.php?action=query"
        f"&titles=File:{urllib.parse.quote(filename)}"
        "&prop=imageinfo&iiprop=url|thumburl&iiurlwidth=900"
        "&format=json&formatversion=2"
    )
    data, status, _ = http_get(api, headers={"User-Agent": WIKI_UA}, timeout=20)
    if status != 200:
        return None
    info = json.loads(data)
    for page in info.get("query", {}).get("pages", []):
        for image_info in page.get("imageinfo", []):
            return image_info.get("thumburl") or image_info.get("url")
    return None


def main():
    url = frwiki_thumb_url(FILENAME)
    if not url:
        raise SystemExit("missing frwiki imageinfo URL")
    data, status, _ = http_get(url, is_image=True, timeout=30)
    if status != 200 or not verify_image(data):
        raise SystemExit(f"download failed: status={status}")
    for directory in (THUMBS / "departements", FULL / "departements"):
        for ext in ("webp", "svg"):
            (directory / f"6.{ext}").unlink(missing_ok=True)
    (THUMBS / "departements" / "6.webp").write_bytes(to_webp_thumb(data))
    (FULL / "departements" / "6.webp").write_bytes(to_webp_full(data))
    print("[ok] 6 Alpes-Maritimes -> Wikipedia FR logo")


if __name__ == "__main__":
    main()
