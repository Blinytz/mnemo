#!/usr/bin/env python3
"""Remplace des couples thumbs/full faibles par une source HD commune.

Le script lit build/hd_audit.csv et traite d'abord les défauts objectifs:
missing_full, low_resolution, low_bytes. Pour chaque cible il cherche une image
de page Wikipedia/Commons, télécharge l'original, puis régénère:
- thumbs/<liste>/<cle>.webp
- full/<liste>/<cle>.jpg

Ce n'est pas un validateur sémantique parfait: c'est une première passe de
remise à niveau technique qui conserve miniature et full cohérents.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote

import requests
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
AUDIT = ROOT / "build" / "hd_audit.csv"
FULL_MAP_JSON = ROOT / "build" / "image_files_map.json"
LOG = ROOT / "build" / "upgrade_hd_pairs.log"
FAILS = ROOT / "build" / "upgrade_hd_pairs_fails.csv"

UA = "MemoAppHD/1.0 (personal educational archive)"
HEADERS = {"User-Agent": UA}
API_HOSTS = ("fr.wikipedia.org", "en.wikipedia.org")
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
MIN_LONG = 1200
MIN_SHORT = 650


PRIMARY_COLUMNS = {
    "chefs_etat": ["Nom"],
    "departements": ["Nom"],
    "etats_usa": ["État"],
    "mythologie": ["Nom"],
    "os": ["Nom"],
    "pays": ["Pays"],
    "peintres": ["Nom", "Œuvre principale"],
    "rois_france": ["Nom"],
    "coupes_monde": ["Année", "Pays organisateur"],
    "xixe": ["Année", "Événement 1"],
    "xxe": ["Année", "Événement 1"],
    "litterature": ["Titre", "Auteur"],
    "guerres": ["Conflit"],
    "philosophes": ["Nom"],
    "mouvements_peinture": ["Mouvement"],
    "jo_ete": ["Année", "Ville"],
    "jo_hiver": ["Année", "Ville"],
    "f1_champions": ["Pilote"],
    "consoles": ["Console"],
    "lunes": ["Lune"],
    "periodes_geologiques": ["Période", "Ère"],
    "films": ["Titre", "Réalisateur"],
    "civilisations": ["Civilisation"],
    "fleuves_monde": ["Fleuve"],
    "compositeurs": ["Compositeur"],
    "constellations": ["Constellation"],
    "grands_scientifiques": ["Scientifique"],
    "batailles_decisives": ["Bataille"],
    "grandes_explorations": ["Explorateur"],
    "revolutions": ["Événement"],
    "montagnes_monde": ["Sommet"],
    "mers_oceans": ["Étendue d’eau"],
    "detroits_monde": ["Détroit"],
    "parcs_nationaux": ["Parc"],
    "architectes_majeurs": ["Architecte", "Œuvre repère"],
    "musees_monde": ["Musée"],
    "inventions_majeures": ["Invention"],
    "decouvertes_scientifiques": ["Découverte"],
}

STYLE_SUFFIX = {
    "batailles_decisives": " battle painting",
    "guerres": " war map",
    "departements": " logo département",
    "etats_usa": " flag",
    "fleuves_monde": " map",
    "detroits_monde": " map",
    "mers_oceans": " map",
    "constellations": " constellation chart",
    "peintres": " portrait",
    "philosophes": " portrait",
    "chefs_etat": " portrait",
    "rois_france": " portrait",
    "f1_champions": " portrait",
    "compositeurs": " portrait",
    "grands_scientifiques": " portrait",
    "films": " film poster",
    "litterature": " book cover",
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
    res = subprocess.run(
        ["node", "-e", js, str(HTML)],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    return {item["id"]: item for item in json.loads(res.stdout)}


def clean_query(text: str) -> str:
    text = re.sub(r"thumbs/[^ ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -–—")


def query_for(list_id: str, row_index: int, image_key: str, lists: dict[str, dict]) -> str:
    lst = lists[list_id]
    row = lst["rows"][row_index - 1]
    cols = lst["columns"]
    wanted = PRIMARY_COLUMNS.get(list_id) or cols[2:4]
    pieces = []
    # Colonne oeuvre des peintres: la clé b correspond à l'oeuvre principale.
    if list_id == "peintres" and image_key.endswith("b"):
        wanted = ["Œuvre principale", "Nom"]
    if list_id == "departements" and image_key.endswith("b"):
        wanted = ["Nom"]
        suffix = " carte localisation département France"
    elif list_id == "etats_usa" and image_key.endswith("b"):
        wanted = ["État"]
        suffix = " location map USA state"
    else:
        suffix = STYLE_SUFFIX.get(list_id, "")
    for name in wanted:
        if name in cols:
            val = str(row[cols.index(name)] or "").strip()
            if val:
                pieces.append(val)
    return clean_query(" ".join(pieces) + suffix)


def wiki_get(host: str, params: dict) -> dict:
    time.sleep(0.35)
    r = requests.get(f"https://{host}/w/api.php", params={**params, "format": "json"}, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return r.json()


def commons_file_original(file_title: str) -> str:
    time.sleep(0.25)
    r = requests.get(COMMONS_API, params={
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "format": "json",
    }, headers=HEADERS, timeout=25)
    r.raise_for_status()
    for page in r.json().get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("url", "")
        mime = info.get("mime", "")
        if url and mime.startswith("image/") and not url.lower().endswith(".svg"):
            return url
    return ""


def page_image_original(host: str, title: str) -> str:
    data = wiki_get(host, {
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "piprop": "original|thumbnail",
        "pithumbsize": 1600,
    })
    for page in data.get("query", {}).get("pages", {}).values():
        for key in ("original", "thumbnail"):
            src = (page.get(key) or {}).get("source", "")
            if src and not src.lower().endswith(".svg"):
                return src
    return ""


def search_titles(host: str, query: str) -> list[str]:
    data = wiki_get(host, {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 5,
        "utf8": 1,
    })
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def resolve_url(query: str) -> tuple[str, str]:
    # Direct page title first, then search results.
    tried = []
    for host in API_HOSTS:
        for title in [query, *search_titles(host, query)]:
            if title in tried:
                continue
            tried.append(title)
            try:
                url = page_image_original(host, title)
                if url:
                    return url, f"{host}:{title}"
            except Exception:
                continue
    # Commons search as fallback.
    try:
        data = requests.get(COMMONS_API, params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 8,
            "format": "json",
        }, headers=HEADERS, timeout=25).json()
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            if not title.startswith("File:"):
                continue
            url = commons_file_original(title)
            if url:
                return url, f"commons:{title}"
    except Exception:
        pass
    return "", ""


def save_pair(url: str, list_id: str, key: str) -> tuple[str, dict]:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    if len(r.content) < 2500:
        raise ValueError(f"source trop petite: {len(r.content)} octets")
    img = Image.open(BytesIO(r.content))
    img = ImageOps.exif_transpose(img).convert("RGB")
    w0, h0 = img.size
    if max(w0, h0) < 700:
        raise ValueError(f"source trop petite: {w0}x{h0}")

    thumb_dir = ROOT / "thumbs" / list_id
    full_dir = ROOT / "full" / list_id
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)

    thumb = img.copy()
    thumb.thumbnail((220, 170), Image.Resampling.LANCZOS)
    thumb_path = thumb_dir / f"{key}.webp"
    thumb.save(thumb_path, "WEBP", quality=86, method=6)

    full = img.copy()
    full.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    full_path = full_dir / f"{key}.jpg"
    full.save(full_path, "JPEG", quality=92, optimize=True, progressive=True)

    return str(full_path.relative_to(ROOT)).replace("\\", "/"), {
        "source_size": f"{w0}x{h0}",
        "full_size": f"{full.size[0]}x{full.size[1]}",
        "bytes": full_path.stat().st_size,
    }


def load_targets(limit: int, only_lists: set[str]) -> list[dict]:
    with AUDIT.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    targets = []
    for row in rows:
        issues = set((row.get("issues") or "").split("|"))
        if only_lists and row["list_id"] not in only_lists:
            continue
        if "missing_full" in issues or "low_resolution" in issues or "low_bytes" in issues:
            targets.append(row)
    def score(row: dict) -> tuple:
        issues = set((row.get("issues") or "").split("|"))
        return (
            0 if "missing_full" in issues else 1,
            0 if "low_resolution" in issues else 1,
            int(row.get("full_long") or 0),
            int(row.get("full_bytes") or 0),
            row["list_id"],
            int(row["row"]),
        )
    targets.sort(key=score)
    return targets[:limit] if limit else targets


def update_full_map(updates: dict[str, dict[str, str]]) -> None:
    full_map = json.loads(FULL_MAP_JSON.read_text(encoding="utf-8")) if FULL_MAP_JSON.exists() else {}
    for list_id, entries in updates.items():
        full_map.setdefault(list_id, {}).update(entries)
    FULL_MAP_JSON.write_text(json.dumps(full_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--lists", default="", help="IDs de listes séparés par des virgules")
    args = ap.parse_args()

    lists = extract_lists()
    only_lists = {x.strip() for x in args.lists.split(",") if x.strip()}
    targets = load_targets(args.limit, only_lists)
    updates: dict[str, dict[str, str]] = {}
    failures = []

    with LOG.open("a", encoding="utf-8") as log:
        for index, target in enumerate(targets, 1):
            list_id = target["list_id"]
            row_num = int(target["row"])
            key = target["key"]
            query = query_for(list_id, row_num, key, lists)
            print(f"[{index}/{len(targets)}] {list_id} #{key}: {query}")
            try:
                url, source = resolve_url(query)
                if not url:
                    raise ValueError("aucune source trouvée")
                full_path, info = save_pair(url, list_id, key)
                updates.setdefault(list_id, {})[key] = full_path
                line = f"OK\t{list_id}\t{key}\t{query}\t{source}\t{info}\n"
                print("  OK", source, info)
                log.write(line)
                log.flush()
            except Exception as exc:
                print("  FAIL", exc)
                failures.append({
                    "list_id": list_id,
                    "key": key,
                    "query": query,
                    "error": str(exc),
                })

    if updates:
        update_full_map(updates)
    if failures:
        write_header = not FAILS.exists()
        with FAILS.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["list_id", "key", "query", "error"])
            if write_header:
                writer.writeheader()
            writer.writerows(failures)
    print(f"\nupdates={sum(len(v) for v in updates.values())} failures={len(failures)}")


if __name__ == "__main__":
    main()
