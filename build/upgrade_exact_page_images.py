#!/usr/bin/env python3
"""Upgrade HD images from exact encyclopedia page titles.

This is intentionally stricter than upgrade_hd_pairs.py: it does not use
free-text search. For each target row it builds one or more exact page titles,
asks Wikipedia for that page image, and only replaces the asset when the source
is technically better than the current full image.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
AUDIT = ROOT / "build" / "hd_audit.csv"
MAP_JSON = ROOT / "build" / "image_files_map.json"
LOG = ROOT / "build" / "upgrade_exact_page_images.log"
UA = "memo-app-exact-image-upgrade/1.0"
HEADERS = {"User-Agent": UA}


TITLE_COLUMNS = {
    "philosophes": ["Nom"],
    "f1_champions": ["Pilote"],
    "chefs_etat": ["Nom"],
    "rois_france": ["Nom"],
    "compositeurs": ["Compositeur"],
    "grands_scientifiques": ["Scientifique"],
    "architectes_majeurs": ["Architecte"],
    "lunes": ["Lune"],
    "peintres": ["Nom"],
}

HOSTS = {
    "philosophes": ["fr.wikipedia.org", "en.wikipedia.org"],
    "f1_champions": ["en.wikipedia.org", "fr.wikipedia.org"],
    "chefs_etat": ["fr.wikipedia.org", "en.wikipedia.org"],
    "rois_france": ["fr.wikipedia.org", "en.wikipedia.org"],
    "compositeurs": ["fr.wikipedia.org", "en.wikipedia.org"],
    "grands_scientifiques": ["fr.wikipedia.org", "en.wikipedia.org"],
    "architectes_majeurs": ["fr.wikipedia.org", "en.wikipedia.org"],
    "lunes": ["fr.wikipedia.org", "en.wikipedia.org"],
    "peintres": ["fr.wikipedia.org", "en.wikipedia.org"],
}

TITLE_ALIASES = {
    ("rois_france", "Robert Ier"): ["Robert Ier (roi des Francs)", "Robert I of France"],
    ("f1_champions", "Jenson Button"): ["Jenson Button"],
    ("lunes", "Europe"): ["Europe (lune)", "Europa (moon)"],
    ("lunes", "Prométhée"): ["Prométhée (lune)", "Prometheus (moon)"],
    ("lunes", "Titan"): ["Titan (lune)", "Titan (moon)"],
    ("lunes", "Charon"): ["Charon (lune)", "Charon (moon)"],
    ("lunes", "Hydra"): ["Hydra (lune)", "Hydra (moon)"],
    ("lunes", "Nix"): ["Nix (lune)", "Nix (moon)"],
    ("peintres", "La Naissance de Vénus"): ["La Naissance de Vénus (Botticelli)", "The Birth of Venus"],
    ("peintres", "Autoportrait à la fourrure"): ["Autoportrait (Dürer, Munich)", "Self-Portrait at Twenty-Eight"],
    ("peintres", "L'Assomption de la Vierge"): ["L'Assomption de la Vierge (Titien)", "Assumption of the Virgin (Titian)"],
    ("peintres", "Les Chasseurs dans la neige"): ["Chasseurs dans la neige", "The Hunters in the Snow"],
    ("peintres", "La Vocation de saint Matthieu"): ["La Vocation de saint Matthieu (Caravage)", "The Calling of St Matthew"],
    ("peintres", "Les Bergers d'Arcadie"): ["Les Bergers d'Arcadie", "Et in Arcadia ego"],
}


def extract_lists() -> dict[str, dict]:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
const data = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
console.log(JSON.stringify(data));
"""
    res = subprocess.run(["node", "-e", js, str(HTML)], cwd=ROOT, check=True, text=True, encoding="utf-8", capture_output=True)
    return {item["id"]: item for item in json.loads(res.stdout)}


def title_for(row: dict, lists: dict[str, dict]) -> list[str]:
    lst = lists[row["list_id"]]
    if row["list_id"] == "peintres" and row.get("key", "").endswith("b"):
        cols = lst["columns"]
        if "Œuvre principale" in cols:
            title = str(lst["rows"][int(row["row"]) - 1][cols.index("Œuvre principale")]).strip()
            return [title]
    values = []
    for col in TITLE_COLUMNS.get(row["list_id"], []):
        if col in lst["columns"]:
            values.append(str(lst["rows"][int(row["row"]) - 1][lst["columns"].index(col)]).strip())
    base = " ".join(v for v in values if v)
    return TITLE_ALIASES.get((row["list_id"], base), [base])


def wiki_page_image(host: str, title: str) -> tuple[str, str]:
    time.sleep(1.0)
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
        time.sleep(8)
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


def source_image(url: str) -> Image.Image:
    time.sleep(0.8)
    r = requests.get(url, headers=HEADERS, timeout=60)
    if r.status_code == 429:
        time.sleep(10)
        r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return ImageOps.exif_transpose(Image.open(BytesIO(r.content))).convert("RGB")


def save_pair(img: Image.Image, list_id: str, key: str) -> tuple[str, str]:
    thumb_dir = ROOT / "thumbs" / list_id
    full_dir = ROOT / "full" / list_id
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    thumb = img.copy()
    thumb.thumbnail((220, 170), Image.Resampling.LANCZOS)
    thumb.save(thumb_dir / f"{key}.webp", "WEBP", quality=86, method=6)
    full = img.copy()
    full.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    out = full_dir / f"{key}.jpg"
    full.save(out, "JPEG", quality=92, optimize=True, progressive=True)
    return str(out.relative_to(ROOT)).replace("\\", "/"), f"{img.size[0]}x{img.size[1]} -> {full.size[0]}x{full.size[1]}"


def load_targets(lists_filter: set[str], limit: int, min_row: int) -> list[dict]:
    with AUDIT.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["status"] == "issue"]
    rows = [r for r in rows if r["list_id"] in lists_filter and (r["column"] == "Image" or r["list_id"] == "peintres")]
    rows = [r for r in rows if int(r["row"]) >= min_row]
    rows.sort(key=lambda r: (r["list_id"], int(r["row"])))
    return rows[:limit] if limit else rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lists", required=True)
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--min-row", type=int, default=1)
    args = ap.parse_args()
    list_filter = {x.strip() for x in args.lists.split(",") if x.strip()}
    lists = extract_lists()
    targets = load_targets(list_filter, args.limit, args.min_row)
    image_map = json.loads(MAP_JSON.read_text(encoding="utf-8")) if MAP_JSON.exists() else {}
    ok = fail = skipped = 0

    with LOG.open("a", encoding="utf-8") as log:
        for i, row in enumerate(targets, 1):
            titles = title_for(row, lists)
            print(f"[{i}/{len(targets)}] {row['list_id']} #{row['key']} {titles}")
            replaced = False
            for title in titles:
                for host in HOSTS.get(row["list_id"], ["fr.wikipedia.org", "en.wikipedia.org"]):
                    try:
                        url, source = wiki_page_image(host, title)
                        if not url:
                            continue
                        img = source_image(url)
                        if max(img.size) <= int(row.get("full_long") or 0) and min(img.size) <= int(row.get("full_short") or 0):
                            print("  skip not better", source, img.size)
                            skipped += 1
                            continue
                        path, size = save_pair(img, row["list_id"], row["key"])
                        image_map.setdefault(row["list_id"], {})[row["key"]] = path
                        print("  OK", source, size)
                        log.write(f"OK\t{row['list_id']}\t{row['key']}\t{titles[0]}\t{source}\t{size}\n")
                        log.flush()
                        ok += 1
                        replaced = True
                        break
                    except Exception as exc:
                        print("  fail", host, title, exc)
                if replaced:
                    break
            if not replaced:
                fail += 1

    MAP_JSON.write_text(json.dumps(image_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"ok={ok} skipped={skipped} fail={fail}")


if __name__ == "__main__":
    main()
