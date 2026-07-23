#!/usr/bin/env python3
"""RÃ©gÃ©nÃ¨re les couples thumbs/full des films depuis TMDB.

Source structurÃ©e: titre + annÃ©e -> poster TMDB.
Cela respecte mieux les critÃ¨res utilisateur pour cette liste:
- pertinent: affiche du film recherchÃ©
- cohÃ©rent: thumb et full issus du mÃªme poster
- homogÃ¨ne: affiches de films
- qualitÃ©: poster original TMDB, redimensionnÃ© proprement
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import re
import subprocess
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
AUDIT = ROOT / "build" / "hd_audit.csv"
FULL_MAP_JSON = ROOT / "build" / "image_files_map.json"
LOG = ROOT / "build" / "upgrade_films_tmdb_hd.log"
FAILS = ROOT / "build" / "upgrade_films_tmdb_hd_fails.csv"
TMDB_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_KEY:
    raise RuntimeError("TMDB_API_KEY doit Ãªtre dÃ©fini dans .env ou dans l'environnement.")
def extract_films() -> dict[int, dict]:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
const lists = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
const films = lists.find(x => x.id === 'films');
console.log(JSON.stringify(films));
"""
    res = subprocess.run(
        ["node", "-e", js, str(HTML)],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    films = json.loads(res.stdout)
    cols = films["columns"]
    idx_year = cols.index("AnnÃ©e")
    idx_title = cols.index("Titre")
    idx_director = cols.index("RÃ©alisateur")
    return {
        i + 1: {
            "year": str(row[idx_year]).strip(),
            "title": str(row[idx_title]).strip(),
            "director": str(row[idx_director]).strip(),
        }
        for i, row in enumerate(films["rows"])
    }


def film_targets(limit: int) -> list[int]:
    with AUDIT.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["list_id"] == "films"]
    out = []
    for row in rows:
        issues = set((row.get("issues") or "").split("|"))
        if {"missing_full", "low_resolution", "low_bytes", "possible_mismatch"} & issues:
            out.append(row)
    out.sort(key=lambda r: (
        0 if "missing_full" in r["issues"] else 1,
        0 if "low_resolution" in r["issues"] else 1,
        int(r.get("full_long") or 0),
        int(r["row"]),
    ))
    nums = [int(r["row"]) for r in out]
    return nums[:limit] if limit else nums


def tmdb_search(title: str, year: str) -> dict | None:
    params = {
        "api_key": TMDB_KEY,
        "query": title,
        "include_adult": "false",
        "language": "fr-FR",
    }
    if year and year[:4].isdigit():
        params["year"] = year[:4]
    time.sleep(0.25)
    r = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=25)
    r.raise_for_status()
    results = r.json().get("results") or []
    if not results and year:
        params.pop("year", None)
        time.sleep(0.25)
        r = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=25)
        r.raise_for_status()
        results = r.json().get("results") or []
    results = [x for x in results if x.get("poster_path")]
    if not results:
        return None
    y = year[:4] if year and year[:4].isdigit() else ""
    if y:
        same_year = [x for x in results if str(x.get("release_date", ""))[:4] == y]
        if same_year:
            results = same_year
        else:
            return None
    for hit in results:
        if title_match(title, hit):
            return hit
    return None


def norm_title(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9Ã€-Ã¿]+", " ", text)
    text = re.sub(r"\b(le|la|les|l|the|a|an|un|une|des|de|du|of|and|et)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_match(query: str, hit: dict) -> bool:
    q = norm_title(query)
    candidates = [norm_title(str(hit.get("title") or "")), norm_title(str(hit.get("original_title") or ""))]
    if q in candidates:
        return True
    # For long titles, translated titles often differ slightly.
    if len(q) >= 10 and any(difflib.SequenceMatcher(None, q, c).ratio() >= 0.72 for c in candidates):
        return True
    return False


def save_pair(poster_path: str, num: int) -> str:
    url = f"https://image.tmdb.org/t/p/original{poster_path}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content))
    img = ImageOps.exif_transpose(img).convert("RGB")
    w0, h0 = img.size
    if max(w0, h0) < 900:
        raise ValueError(f"poster trop petit {w0}x{h0}")

    thumb_dir = ROOT / "thumbs" / "films"
    full_dir = ROOT / "full" / "films"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)

    thumb = img.copy()
    thumb.thumbnail((220, 170), Image.Resampling.LANCZOS)
    thumb.save(thumb_dir / f"{num}.webp", "WEBP", quality=86, method=6)

    full = img.copy()
    full.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    full_path = full_dir / f"{num}.jpg"
    full.save(full_path, "JPEG", quality=92, optimize=True, progressive=True)
    return str(full_path.relative_to(ROOT)).replace("\\", "/")


def update_map(updates: dict[str, str]) -> None:
    m = json.loads(FULL_MAP_JSON.read_text(encoding="utf-8")) if FULL_MAP_JSON.exists() else {}
    m.setdefault("films", {}).update(updates)
    FULL_MAP_JSON.write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    args = ap.parse_args()

    films = extract_films()
    targets = film_targets(args.limit)
    updates = {}
    failures = []
    with LOG.open("a", encoding="utf-8") as log:
        for i, num in enumerate(targets, 1):
            item = films[num]
            print(f"[{i}/{len(targets)}] #{num} {item['year']} {item['title']}")
            try:
                hit = tmdb_search(item["title"], item["year"])
                if not hit:
                    raise ValueError("TMDB: aucun poster")
                full = save_pair(hit["poster_path"], num)
                updates[str(num)] = full
                line = f"OK\t{num}\t{item['year']}\t{item['title']}\t{hit.get('title')}\t{hit.get('release_date')}\t{full}\n"
                log.write(line)
                log.flush()
                print("  OK", hit.get("title"), hit.get("release_date"))
            except Exception as exc:
                failures.append({"num": num, **item, "error": str(exc)})
                print("  FAIL", exc)

    if updates:
        update_map(updates)
    if failures:
        write_header = not FAILS.exists()
        with FAILS.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["num", "year", "title", "director", "error"])
            if write_header:
                writer.writeheader()
            writer.writerows(failures)
    print(f"\nupdates={len(updates)} failures={len(failures)}")


if __name__ == "__main__":
    main()
