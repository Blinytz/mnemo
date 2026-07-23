#!/usr/bin/env python3
"""Repare les images des chefs d'Etat francais avec des pages exactes.

Regle volontaire: aucune recherche floue. Chaque ligne pointe vers un titre
Wikipedia precis. Si l'image exacte n'est pas disponible, la ligne est laissee
intacte plutot que de risquer un faux positif.
"""
from __future__ import annotations

import json
import subprocess
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
MAP_JSON = ROOT / "build" / "image_files_map.json"
LIST_ID = "chefs_etat"
UA = "memo-app-chefs-etat-exact/1.0"
HEADERS = {"User-Agent": UA}

TITLES = {
    1: ["Louis XVI"],
    2: ["Louis XVI"],
    3: ["Convention nationale"],
    4: ["Directoire"],
    5: ["Napoléon Bonaparte"],
    6: ["Napoléon Ier"],
    7: ["Louis XVIII"],
    8: ["Napoléon Ier"],
    9: ["Louis XVIII"],
    10: ["Charles X"],
    11: ["Louis-Philippe Ier"],
    12: ["Louis-Eugène Cavaignac"],
    13: ["Napoléon III"],
    14: ["Napoléon III"],
    15: ["Adolphe Thiers"],
    16: ["Patrice de Mac Mahon"],
    17: ["Jules Grévy"],
    18: ["Sadi Carnot (homme d'État)"],
    19: ["Jean Casimir-Perier"],
    20: ["Félix Faure"],
    21: ["Émile Loubet"],
    22: ["Armand Fallières"],
    23: ["Raymond Poincaré"],
    24: ["Paul Deschanel"],
    25: ["Alexandre Millerand"],
    26: ["Gaston Doumergue"],
    27: ["Paul Doumer"],
    28: ["Albert Lebrun"],
    29: ["Philippe Pétain"],
    30: ["Charles de Gaulle"],
    31: ["Félix Gouin"],
    32: ["Georges Bidault"],
    33: ["Léon Blum"],
    34: ["Vincent Auriol"],
    35: ["René Coty"],
    36: ["Charles de Gaulle"],
    37: ["Georges Pompidou"],
    38: ["Valéry Giscard d'Estaing"],
    39: ["François Mitterrand"],
    40: ["Jacques Chirac"],
    41: ["Nicolas Sarkozy"],
    42: ["François Hollande"],
    43: ["Emmanuel Macron"],
}


def extract_rows() -> list[list[str]]:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
const lists = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
console.log(JSON.stringify(lists.find(x => x.id === 'chefs_etat').rows));
"""
    res = subprocess.run(["node", "-e", js, str(HTML)], cwd=ROOT, check=True, text=True, encoding="utf-8", capture_output=True)
    return json.loads(res.stdout)


def page_image(title: str) -> tuple[str, str]:
    for host in ("fr.wikipedia.org", "en.wikipedia.org"):
        time.sleep(1.2)
        r = requests.get(
            f"https://{host}/w/api.php",
            params={
                "action": "query",
                "titles": title,
                "prop": "pageimages",
                "piprop": "original|thumbnail",
                "pithumbsize": 1800,
                "format": "json",
            },
            headers=HEADERS,
            timeout=30,
        )
        if r.status_code == 429:
            time.sleep(12)
            r = requests.get(r.url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        for page in r.json().get("query", {}).get("pages", {}).values():
            if "missing" in page:
                continue
            for key in ("original", "thumbnail"):
                src = (page.get(key) or {}).get("source", "")
                if src and not src.lower().endswith(".svg"):
                    return src, f"{host}:{page.get('title', title)}"
    return "", ""


def download_image(url: str) -> Image.Image:
    time.sleep(0.9)
    r = requests.get(url, headers=HEADERS, timeout=60)
    if r.status_code == 429:
        time.sleep(15)
        r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return ImageOps.exif_transpose(Image.open(BytesIO(r.content))).convert("RGB")


def save_pair(row_num: int, img: Image.Image) -> str:
    thumb_dir = ROOT / "thumbs" / LIST_ID
    full_dir = ROOT / "full" / LIST_ID
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    thumb = img.copy()
    thumb.thumbnail((220, 170), Image.Resampling.LANCZOS)
    thumb.save(thumb_dir / f"{row_num}.webp", "WEBP", quality=86, method=6)
    full = img.copy()
    full.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    out = full_dir / f"{row_num}.jpg"
    full.save(out, "JPEG", quality=92, optimize=True, progressive=True)
    return str(out.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    rows = extract_rows()
    image_map = json.loads(MAP_JSON.read_text(encoding="utf-8")) if MAP_JSON.exists() else {}
    image_map.setdefault(LIST_ID, {})
    ok = fail = 0
    for i, row in enumerate(rows, 1):
        label = row[2]
        replaced = False
        for title in TITLES.get(i, []):
            try:
                url, source = page_image(title)
                if not url:
                    continue
                img = download_image(url)
                if max(img.size) < 350:
                    print("SKIP small", i, label, source, img.size)
                    continue
                path = save_pair(i, img)
                image_map[LIST_ID][str(i)] = path
                print("OK", i, label, source, img.size)
                ok += 1
                replaced = True
                break
            except Exception as exc:
                print("FAIL source", i, label, title, exc)
        if not replaced:
            print("FAIL", i, label)
            fail += 1
    MAP_JSON.write_text(json.dumps(image_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
