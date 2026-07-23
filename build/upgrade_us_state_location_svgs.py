#!/usr/bin/env python3
"""Remplace les localisations des États US par des SVG Commons.

Les cartes raster b.webp sont trop petites pour l'agrandi. Les SVG Commons
résolvent le problème de qualité et gardent une homogénéité de style.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
import gzip

import requests


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
MAP_JSON = ROOT / "build" / "image_files_map.json"
COMMONS = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "MemoAppHD/1.0 (personal educational archive)"}

FR_TO_EN = {
    "Alabama": "Alabama",
    "Alaska": "Alaska",
    "Arizona": "Arizona",
    "Arkansas": "Arkansas",
    "Californie": "California",
    "Caroline du Nord": "North Carolina",
    "Caroline du Sud": "South Carolina",
    "Colorado": "Colorado",
    "Connecticut": "Connecticut",
    "Dakota du Nord": "North Dakota",
    "Dakota du Sud": "South Dakota",
    "Delaware": "Delaware",
    "Floride": "Florida",
    "Géorgie": "Georgia",
    "Hawaï": "Hawaii",
    "Idaho": "Idaho",
    "Illinois": "Illinois",
    "Indiana": "Indiana",
    "Iowa": "Iowa",
    "Kansas": "Kansas",
    "Kentucky": "Kentucky",
    "Louisiane": "Louisiana",
    "Maine": "Maine",
    "Maryland": "Maryland",
    "Massachusetts": "Massachusetts",
    "Michigan": "Michigan",
    "Minnesota": "Minnesota",
    "Mississippi": "Mississippi",
    "Missouri": "Missouri",
    "Montana": "Montana",
    "Nebraska": "Nebraska",
    "Nevada": "Nevada",
    "New Hampshire": "New Hampshire",
    "New Jersey": "New Jersey",
    "New Mexico": "New Mexico",
    "New York": "New York",
    "Ohio": "Ohio",
    "Oklahoma": "Oklahoma",
    "Oregon": "Oregon",
    "Pennsylvanie": "Pennsylvania",
    "Rhode Island": "Rhode Island",
    "Tennessee": "Tennessee",
    "Texas": "Texas",
    "Utah": "Utah",
    "Vermont": "Vermont",
    "Virginie": "Virginia",
    "Virginie-Occidentale": "West Virginia",
    "Washington": "Washington",
    "Wisconsin": "Wisconsin",
    "Wyoming": "Wyoming",
}


def extract_states() -> list[tuple[int, str]]:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
const lists = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
const l = lists.find(x => x.id === 'etats_usa');
const ci = l.columns.indexOf('État');
console.log(JSON.stringify(l.rows.map((r, i) => [i + 1, r[ci]])));
"""
    res = subprocess.run(["node", "-e", js, str(HTML)], cwd=ROOT, check=True, text=True, encoding="utf-8", capture_output=True)
    return [(int(n), str(name)) for n, name in json.loads(res.stdout)]


def commons_file_url(title: str) -> str:
    time.sleep(1.2)
    r = requests.get(COMMONS, params={
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "format": "json",
    }, headers=HEADERS, timeout=25)
    r.raise_for_status()
    for page in r.json().get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("url", "")
        if url.lower().endswith(".svg"):
            return url
    return ""


def commons_search(query: str) -> list[str]:
    time.sleep(1.5)
    r = requests.get(COMMONS, params={
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 12,
        "format": "json",
    }, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return [x["title"] for x in r.json().get("query", {}).get("search", []) if x.get("title", "").lower().endswith(".svg")]


def find_svg(en_name: str) -> tuple[str, str]:
    candidates = [
        f"File:{en_name} in United States.svg",
        f"File:{en_name} in the United States.svg",
        f"File:{en_name} in United States (zoom).svg",
        f"File:{en_name} in United States (US48).svg",
        f"File:Map of USA {en_name}.svg",
        f"File:Map of {en_name} in the United States.svg",
    ]
    for title in candidates:
        url = commons_file_url(title)
        if url:
            return title, url
    patterns = [
        f'intitle:"{en_name} in United States" filetype:svg',
        f'intitle:"{en_name}" intitle:"United States" filetype:svg map',
        f'"{en_name} in United States" svg',
    ]
    for query in patterns:
        for title in commons_search(query):
            low = title.lower()
            if en_name.lower() in low and ("united_states" in low or "united states" in low or "usa" in low):
                url = commons_file_url(title)
                if url:
                    return title, url
    return "", ""


def main() -> None:
    thumb_dir = ROOT / "thumbs" / "etats_usa"
    full_dir = ROOT / "full" / "etats_usa"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    image_map = json.loads(MAP_JSON.read_text(encoding="utf-8")) if MAP_JSON.exists() else {}
    image_map.setdefault("etats_usa", {})
    ok = fail = 0
    for num, fr_name in extract_states():
        en_name = FR_TO_EN.get(fr_name, fr_name)
        key = f"{num}b"
        if (full_dir / f"{key}.svg").exists():
            image_map["etats_usa"][key] = f"full/etats_usa/{key}.svg"
            ok += 1
            continue
        print(f"[{num}] {fr_name} -> {en_name}")
        try:
            title, url = find_svg(en_name)
            if not url:
                raise ValueError("SVG Commons introuvable")
            resp = requests.get(url, headers={**HEADERS, "Accept-Encoding": "identity"}, timeout=40)
            resp.raise_for_status()
            data = resp.content
            if data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            probe = data.lstrip()[:3000].lower()
            if b"<svg" not in probe:
                raise ValueError("contenu non SVG")
            for folder in (thumb_dir, full_dir):
                (folder / f"{key}.svg").write_bytes(data)
            # Supprime l'ancien raster pour éviter les ambiguïtés de map.
            for folder in (thumb_dir, full_dir):
                old = folder / f"{key}.webp"
                if old.exists():
                    old.unlink()
            image_map["etats_usa"][key] = f"full/etats_usa/{key}.svg"
            print(f"  OK {title}")
            ok += 1
        except Exception as exc:
            print(f"  FAIL {exc}")
            fail += 1
    MAP_JSON.write_text(json.dumps(image_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
