#!/usr/bin/env python3
"""Download homogeneous IAU constellation charts from Wikimedia Commons."""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
THUMBS = ROOT / "thumbs" / "constellations"
FULL = ROOT / "full" / "constellations"
UA = "memo-app-local-constellation-audit/1.0"

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
    ("Bouvier", "Bootes"),
    ("Couronne boréale", "Corona Borealis"),
    ("Ophiuchus", "Ophiuchus"),
    ("Hydre", "Hydra"),
    ("Éridain", "Eridanus"),
    ("Corbeau", "Corvus"),
    ("Lièvre", "Lepus"),
    ("Phénix", "Phoenix"),
    ("Serpent", "Serpens"),
]


def get_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=45) as resp:
        return resp.read()


def commons_file_url(filename: str) -> str | None:
    params = {
        "action": "query",
        "format": "json",
        "titles": "File:" + filename,
        "prop": "imageinfo",
        "iiprop": "url",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urlencode(params)
    data = get_json(url)
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if infos and infos[0].get("url"):
            return infos[0]["url"]
    return None


def candidate_filenames(latin: str) -> list[str]:
    return [
        f"{latin} IAU.svg",
        f"{latin}_IAU.svg",
        f"{latin} constellation map.svg",
        f"{latin}_constellation_map.svg",
    ]


def main() -> None:
    THUMBS.mkdir(parents=True, exist_ok=True)
    FULL.mkdir(parents=True, exist_ok=True)
    results = []
    failures = []
    for idx, (french, latin) in enumerate(CONSTELLATIONS, start=1):
        found = None
        source_name = ""
        for filename in candidate_filenames(latin):
            try:
                found = commons_file_url(filename)
            except Exception:
                found = None
            if found:
                source_name = filename
                break
            time.sleep(0.1)
        if not found:
            failures.append({"row": idx, "name": french, "latin": latin, "reason": "no_commons_file"})
            continue
        try:
            data = get_bytes(found)
            if not data.lstrip().startswith(b"<svg") and b"<svg" not in data[:500]:
                failures.append({"row": idx, "name": french, "latin": latin, "reason": "not_svg", "url": found})
                continue
            for base in (THUMBS, FULL):
                (base / f"{idx}.svg").write_bytes(data)
            results.append({"row": idx, "name": french, "latin": latin, "source": source_name, "url": found})
        except Exception as exc:
            failures.append({"row": idx, "name": french, "latin": latin, "reason": str(exc), "url": found})
        time.sleep(0.15)
    report = {"downloaded": len(results), "failures": failures, "results": results}
    (ROOT / "build" / "constellations_iau_sources.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
