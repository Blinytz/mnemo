#!/usr/bin/env python3
"""Download rendered IAU constellation charts via Commons thumburl."""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageOps
import socket


ROOT = Path(__file__).resolve().parent.parent
THUMBS = ROOT / "thumbs" / "constellations"
FULL = ROOT / "full" / "constellations"
UA = "memo-app-local-constellation-audit/1.0 (thumburl; personal offline use)"
socket.setdefaulttimeout(20)

CONSTELLATIONS = [
    ("Orion", "Orion"),
    ("Grande Ourse", "Ursa Major"),
    ("Petite Ourse", "Ursa Minor"),
    ("Cassiopée", "Cassiopeia"),
    ("Cygne", "Cygnus"),
    ("Lyre", "Lyra"),
    ("Aigle", "Aquila"),
    ("Scorpion", "Scorpius"),
    ("Sagittaire", "Sagittarius"),
    ("Taureau", "Taurus"),
    ("Gémeaux", "Gemini"),
    ("Lion", "Leo"),
    ("Persée", "Perseus"),
    ("Andromède", "Andromeda"),
    ("Hercule", "Hercules"),
    ("Vierge", "Virgo"),
    ("Balance", "Libra"),
    ("Verseau", "Aquarius"),
    ("Bélier", "Aries"),
    ("Cancer", "Cancer"),
    ("Capricorne", "Capricornus"),
    ("Poissons", "Pisces"),
    ("Centaure", "Centaurus"),
    ("Croix du Sud", "Crux"),
    ("Dragon", "Draco"),
    ("Pégase", "Pegasus"),
    ("Grand Chien", "Canis Major"),
    ("Petit Chien", "Canis Minor"),
    ("Cocher", "Auriga"),
    ("Bouvier", "Boötes"),
    ("Couronne boréale", "Corona Borealis"),
    ("Ophiuchus", "Ophiuchus"),
    ("Hydre", "Hydra"),
    ("Éridain", "Eridanus"),
    ("Corbeau", "Corvus"),
    ("Lièvre", "Lepus"),
    ("Phénix", "Phoenix"),
    ("Serpent", "Serpens"),
]

ALIASES = {
    "Boötes": ["Boötes", "Bootes"],
}


def request_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=45) as resp:
        return resp.read()


def request_json(url: str) -> dict:
    return json.loads(request_bytes(url).decode("utf-8"))


def imageinfo(filename: str) -> dict | None:
    params = {
        "action": "query",
        "format": "json",
        "titles": "File:" + filename,
        "prop": "imageinfo",
        "iiprop": "url|mime|size|thumburl",
        "iiurlwidth": "1600",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urlencode(params)
    data = request_json(url)
    for page in data.get("query", {}).get("pages", {}).values():
        infos = page.get("imageinfo") or []
        if infos:
            return infos[0]
    return None


def search_filename(latin: str) -> str | None:
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srnamespace": "6",
        "srlimit": "5",
        "srsearch": f'"{latin}" "IAU" svg',
    }
    data = request_json("https://commons.wikimedia.org/w/api.php?" + urlencode(params))
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        if title.lower().endswith("iau.svg"):
            return title.replace("File:", "", 1)
    return None


def filenames_for(latin: str) -> list[str]:
    names = ALIASES.get(latin, [latin])
    out = []
    for name in names:
        out.extend([
            f"{name} IAU.svg",
            f"{name}_IAU.svg",
            f"{name} constellation map.svg",
            f"{name}_constellation_map.svg",
        ])
    return out


def save_pair(idx: int, data: bytes, source_ext: str) -> None:
    FULL.mkdir(parents=True, exist_ok=True)
    THUMBS.mkdir(parents=True, exist_ok=True)
    full_path = FULL / f"{idx}.png"
    thumb_path = THUMBS / f"{idx}.webp"
    full_path.write_bytes(data)
    with Image.open(full_path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        # Full image is kept as downloaded PNG; thumbnail is derived from it.
        thumb = im.copy()
        thumb.thumbnail((220, 160), Image.Resampling.LANCZOS)
        thumb.save(thumb_path, "WEBP", quality=84, method=6)


def main() -> None:
    results = []
    failures = []
    for idx, (french, latin) in enumerate(CONSTELLATIONS, start=1):
        if (FULL / f"{idx}.png").exists() and (THUMBS / f"{idx}.webp").exists():
            results.append({"row": idx, "name": french, "latin": latin, "source": "already-present", "url": ""})
            continue
        tried = []
        info = None
        source = None
        for filename in filenames_for(latin):
            tried.append(filename)
            try:
                info = imageinfo(filename)
            except Exception as exc:
                failures.append({"row": idx, "name": french, "candidate": filename, "stage": "imageinfo", "error": str(exc)})
                info = None
            if info and (info.get("thumburl") or info.get("url")):
                source = filename
                break
            time.sleep(0.25)
        if not info:
            found = None
            try:
                found = search_filename(latin)
            except Exception:
                found = None
            if found:
                source = found
                info = imageinfo(found)
        if not info:
            failures.append({"row": idx, "name": french, "latin": latin, "stage": "not_found", "tried": tried})
            continue
        url = info.get("thumburl") or info.get("url")
        ok = False
        for attempt in range(4):
            try:
                data = request_bytes(url)
                save_pair(idx, data, ".png")
                results.append({"row": idx, "name": french, "latin": latin, "source": source, "url": url})
                ok = True
                break
            except Exception as exc:
                if attempt == 3:
                    failures.append({"row": idx, "name": french, "latin": latin, "source": source, "url": url, "stage": "download", "error": str(exc)})
                time.sleep(2 + attempt * 3)
        time.sleep(0.8 if ok else 1.5)
    report = {"downloaded": len(results), "failures": failures, "results": results}
    (ROOT / "build" / "constellations_iau_thumb_sources.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"downloaded": len(results), "failures": len(failures)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
