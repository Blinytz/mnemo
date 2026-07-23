#!/usr/bin/env python3
"""Replace confirmed visual mismatches while retaining every previous asset."""
import json
import os
import re
import shutil
import argparse
from html import unescape
from io import BytesIO
from pathlib import Path

from PIL import Image

import build_images as b


ROOT = Path(__file__).parent.parent
HTML = ROOT / "memo.html"
BACKUP = ROOT / "build" / "asset_backups" / "v60"
REPORT = ROOT / "build" / "quality_replacements_v60.json"


WIKI_TARGETS = [
    # Artist primary-work column.
    ("peintres", "5b", "Sistine Chapel ceiling", "en.wikipedia.org"),
    ("peintres", "10b", "The Descent from the Cross (Rubens)", "en.wikipedia.org"),
    ("peintres", "21b", "Mont Sainte-Victoire (Cezanne)", "en.wikipedia.org"),
    ("peintres", "32b", "Guernica (Picasso)", "en.wikipedia.org"),
    ("peintres", "35b", "Man at the Crossroads", "en.wikipedia.org"),
    ("peintres", "37b", "The Melancholy and Mystery of a Street", "en.wikipedia.org"),
    ("peintres", "41b", "The Two Fridas", "en.wikipedia.org"),
    ("peintres", "42b", "Three Studies of Lucian Freud", "en.wikipedia.org"),
    ("peintres", "43b", "Number 31 (Jackson Pollock)", "en.wikipedia.org"),
    ("peintres", "46b", "Untitled (Skull)", "en.wikipedia.org"),
    ("peintres", "47b", "Girl with Balloon", "en.wikipedia.org"),
    # Historic timelines and state heads.
    ("periodes_geologiques", "13", "Tonian", "en.wikipedia.org"),
    ("periodes_geologiques", "22", "Triassic", "en.wikipedia.org"),
    ("xixe", "47", "On the Origin of Species", "en.wikipedia.org"),
    ("xixe", "71", "Wilhelm Rontgen", "en.wikipedia.org"),
    ("xxe", "3", "Second Boer War", "en.wikipedia.org"),
    ("xxe", "44", "Allied invasion of Sicily", "en.wikipedia.org"),
    ("chefs_etat", "3", "National Convention", "en.wikipedia.org"),
    ("chefs_etat", "4", "Directoire", "fr.wikipedia.org"),
    ("chefs_etat", "16", "Patrice de MacMahon", "fr.wikipedia.org"),
    # Medieval rulers: portrait, manuscript, coin, or seal are all preferable
    # to a generic genealogy diagram.
    ("rois_france", "4", "Clotaire II", "fr.wikipedia.org"),
    ("rois_france", "7", "Clotaire III", "fr.wikipedia.org"),
    ("rois_france", "10", "Childebert III", "fr.wikipedia.org"),
    ("rois_france", "21", "Carloman II", "fr.wikipedia.org"),
    ("rois_france", "25", "Robert Ier de France", "fr.wikipedia.org"),
    ("rois_france", "26", "Raoul de France", "fr.wikipedia.org"),
    ("rois_france", "28", "Lothaire de France", "fr.wikipedia.org"),
    # A book list should show a book, not its author.
    ("litterature", "56", "The Hitchhiker's Guide to the Galaxy", "en.wikipedia.org"),
    # Astronomical objects: source pages have an actual observation or an
    # orbital/system view, both more relevant than mythology art.
    ("lunes", "12", "Leda (moon)", "en.wikipedia.org"),
    ("lunes", "13", "Himalia (moon)", "en.wikipedia.org"),
    ("lunes", "16", "Ananke (moon)", "en.wikipedia.org"),
    ("lunes", "17", "Carme (moon)", "en.wikipedia.org"),
    ("lunes", "18", "Pasiphae (moon)", "en.wikipedia.org"),
    ("lunes", "19", "Sinope (moon)", "en.wikipedia.org"),
    ("lunes", "22", "Prometheus (moon)", "en.wikipedia.org"),
    ("lunes", "23", "Pandora (moon)", "en.wikipedia.org"),
    ("lunes", "27", "Telesto (moon)", "en.wikipedia.org"),
    ("lunes", "28", "Calypso (moon)", "en.wikipedia.org"),
    ("lunes", "29", "Dione (moon)", "en.wikipedia.org"),
    ("lunes", "31", "Rhea (moon)", "en.wikipedia.org"),
    ("lunes", "32", "Titan (moon)", "en.wikipedia.org"),
    ("lunes", "36", "Puck (moon)", "en.wikipedia.org"),
    ("lunes", "42", "Caliban (moon)", "en.wikipedia.org"),
    ("lunes", "44", "Naiad (moon)", "en.wikipedia.org"),
]


TMDB_TARGETS = [
    ("15", "Le Christ marchant sur les eaux", "1899", "Georges Melies"),
    ("23", "La Vie d'un joueur", "1902", "Pathe Freres"),
    ("27", "Le Vol d'un tableau", "1903", "Pathe Freres"),
    ("51", "Feat of Clay", "1911", "Otis Turner"),
]

PAGE_FILE_TARGETS = [
    # PageImages returns a portrait for these pages. The requested file must
    # instead contain the named work itself.
    ("peintres", "32b", "Guernica (Picasso)", ["guernica"]),
    ("peintres", "41b", "The Two Fridas", ["two fridas"]),
    ("peintres", "42b", "Three Studies of Lucian Freud", ["three studies", "lucian freud"]),
    ("peintres", "43b", "Number 31 (Jackson Pollock)", ["number 31", "no. 31"]),
    ("peintres", "46b", "Untitled (Skull)", ["untitled", "skull"]),
    ("peintres", "47b", "Girl with Balloon", ["girl", "balloon"]),
    ("litterature", "56", "The Hitchhiker's Guide to the Galaxy", ["hitchhiker", "guide"]),
    # These two political bodies need a historical scene rather than a
    # diagram or a flag.
    ("chefs_etat", "3", "National Convention", ["convention", "assembly", "1792"]),
    ("chefs_etat", "4", "French Directory", ["directory", "directoire", "five"]),
]

COMMONS_FILE_TARGETS = [
    # Direct Commons filenames, inspected via the search API. They avoid the
    # mythology pages' misleading default paintings for these astronomical
    # objects and the genealogy fallback for Carloman II.
    ("rois_france", "21", "Carloman II of France.jpg"),
    ("peintres", "43b", "Peddler by Jackson Pollock.jpg"),
    ("lunes", "12", "Leda WISE-W3.jpg"),
    ("lunes", "18", "Pasiphae-WISE.gif"),
    ("lunes", "22", "PIA12593 Prometheus2.jpg"),
    ("lunes", "23", "Pandora moon.jpg"),
    ("lunes", "28", "Calypso (moon).jpg"),
    ("lunes", "42", "Caliban discovery full.jpg"),
]

DIRECT_IMAGE_TARGETS = [
    ("peintres", "32b", "https://en.wikipedia.org/wiki/Special:FilePath/PicassoGuernica.jpg"),
    ("peintres", "41b", "https://en.wikipedia.org/wiki/Special:FilePath/The%20Two%20Fridas.jpg"),
    ("peintres", "42b", "https://francis-bacon-prod.fra1.cdn.digitaloceanspaces.com/s3fs-public/decade_images/69-07%20FB%20b-centre%20RGB.jpg"),
]

OPEN_GRAPH_TARGETS = [
    ("peintres", "43b", "https://www.moma.org/collection/works/78386"),
]


def image_map():
    html = HTML.read_text(encoding="utf-8")
    match = re.search(r"const IMAGE_FILES_MAP = (\{.*?\});\nfunction localFullImageForThumb", html, re.S)
    if not match:
        raise RuntimeError("IMAGE_FILES_MAP introuvable")
    return json.loads(match.group(1))


def mapped_full_path(mapping, list_id, stem):
    rel = mapping.get(list_id, {}).get(str(stem))
    if not rel:
        raise RuntimeError(f"plein format non mappe: {list_id}/{stem}")
    return ROOT / rel


def backup(list_id, stem, full_path):
    for path in [ROOT / "thumbs" / list_id / f"{stem}.webp", full_path]:
        if path.exists():
            destination = BACKUP / path.relative_to(ROOT)
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)


def encode_full(data, suffix):
    image = Image.open(BytesIO(data)).convert("RGBA")
    if max(image.size) > 1800:
        scale = 1800 / max(image.size)
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)
    out = BytesIO()
    suffix = suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        background.save(out, "JPEG", quality=94, optimize=True)
    elif suffix == ".png":
        image.save(out, "PNG", optimize=True)
    else:
        image.save(out, "WEBP", quality=94, method=6)
    return out.getvalue()


def write_replacement(mapping, list_id, stem, data, source):
    if not data or not b.verify_image(data):
        raise RuntimeError("donnees image invalides")
    full_path = mapped_full_path(mapping, list_id, stem)
    backup(list_id, stem, full_path)
    thumb = b.to_webp_thumb(data)
    if not thumb:
        raise RuntimeError("conversion miniature impossible")
    full_path.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "thumbs" / list_id / f"{stem}.webp").write_bytes(thumb)
    full_path.write_bytes(encode_full(data, full_path.suffix))
    return {
        "list": list_id,
        "row": str(stem),
        "source": source,
        "thumb": str((Path("thumbs") / list_id / f"{stem}.webp").as_posix()),
        "full": str(full_path.relative_to(ROOT).as_posix()),
    }


def download_wiki(title, host):
    hit = b.wiki_batch([title], host=host, thumb_size=1800).get(title)
    if not hit:
        hit = b.wiki_search(title, host=host, thumb_size=1800)
    if not hit:
        return None
    thumb, full = b.wiki_download(hit)
    return full or thumb


def download_tmdb(title, year, director):
    thumb, full = b.resolve_tmdb(title, year, director, b.TMDB_KEY)
    return full or thumb


def download_commons_file(filename):
    data, kind, _ = b._download_commons_svg_or_thumb(filename, width=1800)
    if kind != "image":
        return None
    return data


def download_direct_image(url):
    data, status, _ = b.http_get(url, headers={"User-Agent": b.UA}, is_image=True, timeout=20)
    return data if status == 200 and b.verify_image(data) else None


def download_open_graph_image(page_url):
    raw, status, _ = b.http_get(page_url, headers={"User-Agent": b.UA}, timeout=15)
    if status != 200:
        return None, None
    text = raw.decode("utf-8", errors="ignore")
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]
    url = ""
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            url = unescape(match.group(1))
            break
    if not url:
        return None, None
    return download_direct_image(url), url


def normalized(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def download_page_file(title, terms, host="en.wikipedia.org"):
    params = {
        "action": "query",
        "titles": title,
        "prop": "images",
        "imlimit": "max",
        "format": "json",
        "formatversion": "2",
        "origin": "*",
    }
    api = f"https://{host}/w/api.php?{b.urllib.parse.urlencode(params)}"
    raw, status, _ = b.http_get(api, headers={"User-Agent": b.WIKI_UA})
    if status != 200:
        return None, None
    try:
        pages = json.loads(raw).get("query", {}).get("pages", [])
        names = [item.get("title", "").replace("File:", "") for page in pages for item in page.get("images", [])]
    except Exception:
        return None, None
    wanted = [normalized(term) for term in terms]
    candidates = [name for name in names if all(term in normalized(name) for term in wanted)]
    if not candidates:
        candidates = [name for name in names if any(term in normalized(name) for term in wanted)]
    for name in candidates:
        info_params = {
            "action": "query",
            "titles": f"File:{name}",
            "prop": "imageinfo",
            "iiprop": "url|thumburl",
            "iiurlwidth": "1800",
            "format": "json",
            "formatversion": "2",
            "origin": "*",
        }
        info_api = f"https://{host}/w/api.php?{b.urllib.parse.urlencode(info_params)}"
        info_raw, info_status, _ = b.http_get(info_api, headers={"User-Agent": b.WIKI_UA})
        if info_status != 200:
            continue
        try:
            page = json.loads(info_raw).get("query", {}).get("pages", [])[0]
            imageinfo = page.get("imageinfo", [])[0]
            url = imageinfo.get("thumburl") or imageinfo.get("url")
        except Exception:
            url = ""
        if not url:
            continue
        data, image_status, _ = b.http_get(url, headers={"User-Agent": b.UA}, is_image=True)
        if image_status == 200 and b.verify_image(data):
            return data, name
    return None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--section",
        choices=("paintings", "history", "royals", "moons", "files", "commons", "direct", "films", "all"),
        default="all",
        help="Run a bounded quality batch.",
    )
    args = parser.parse_args()
    b.TMDB_KEY = b.TMDB_KEY or os.environ.get("TMDB_API_KEY")
    b.load_cache()
    original_http_get = b.http_get

    # Wikimedia may occasionally hold a connection open. Quality batches should
    # fail a single candidate promptly instead of blocking the full review.
    def bounded_http_get(url, headers=None, timeout=25, cache=True, is_image=False):
        return original_http_get(url, headers=headers, timeout=min(timeout, 8), cache=cache, is_image=is_image)

    b.http_get = bounded_http_get
    mapping = image_map()
    completed = []
    failures = []

    sections = {
        "paintings": {"peintres"},
        "history": {"periodes_geologiques", "xixe", "xxe", "chefs_etat", "litterature"},
        "royals": {"rois_france"},
        "moons": {"lunes"},
    }
    wanted_lists = None if args.section == "all" else sections.get(args.section, set())
    wiki_targets = WIKI_TARGETS if wanted_lists is None else [t for t in WIKI_TARGETS if t[0] in wanted_lists]
    for list_id, stem, title, host in wiki_targets:
        try:
            data = download_wiki(title, host)
            if not data:
                raise RuntimeError(f"page sans image: {title}")
            completed.append(write_replacement(mapping, list_id, stem, data, f"wiki:{host}:{title}"))
            print(f"OK {list_id}/{stem} <- {title}")
        except Exception as exc:
            failures.append({"list": list_id, "row": stem, "requested": title, "error": str(exc)})
            print(f"FAIL {list_id}/{stem}: {exc}")

    tmdb_targets = TMDB_TARGETS if args.section in ("all", "films") else []
    for stem, title, year, director in tmdb_targets:
        try:
            data = download_tmdb(title, year, director)
            if not data:
                raise RuntimeError(f"TMDB sans poster: {title}")
            completed.append(write_replacement(mapping, "films", stem, data, f"tmdb:{title}:{year}"))
            print(f"OK films/{stem} <- {title}")
        except Exception as exc:
            failures.append({"list": "films", "row": stem, "requested": title, "error": str(exc)})
            print(f"FAIL films/{stem}: {exc}")

    page_file_targets = PAGE_FILE_TARGETS if args.section in ("all", "files") else []
    for list_id, stem, title, terms in page_file_targets:
        try:
            data, filename = download_page_file(title, terms)
            if not data:
                raise RuntimeError(f"fichier cible absent: {title}")
            completed.append(write_replacement(mapping, list_id, stem, data, f"wiki-file:en.wikipedia.org:{filename}"))
            print(f"OK {list_id}/{stem} <- {filename}")
        except Exception as exc:
            failures.append({"list": list_id, "row": stem, "requested": title, "error": str(exc)})
            print(f"FAIL {list_id}/{stem}: {exc}")

    commons_targets = COMMONS_FILE_TARGETS if args.section in ("all", "commons") else []
    for list_id, stem, filename in commons_targets:
        try:
            data = download_commons_file(filename)
            if not data:
                raise RuntimeError(f"fichier Commons absent: {filename}")
            completed.append(write_replacement(mapping, list_id, stem, data, f"commons:{filename}"))
            print(f"OK {list_id}/{stem} <- {filename}")
        except Exception as exc:
            failures.append({"list": list_id, "row": stem, "requested": filename, "error": str(exc)})
            print(f"FAIL {list_id}/{stem}: {exc}")

    direct_targets = DIRECT_IMAGE_TARGETS if args.section in ("all", "direct") else []
    for list_id, stem, url in direct_targets:
        try:
            data = download_direct_image(url)
            if not data:
                raise RuntimeError(f"image directe indisponible: {url}")
            completed.append(write_replacement(mapping, list_id, stem, data, f"direct:{url}"))
            print(f"OK {list_id}/{stem} <- {url}")
        except Exception as exc:
            failures.append({"list": list_id, "row": stem, "requested": url, "error": str(exc)})
            print(f"FAIL {list_id}/{stem}: {exc}")

    og_targets = OPEN_GRAPH_TARGETS if args.section in ("all", "direct") else []
    for list_id, stem, page_url in og_targets:
        try:
            data, image_url = download_open_graph_image(page_url)
            if not data:
                raise RuntimeError(f"og:image indisponible: {page_url}")
            completed.append(write_replacement(mapping, list_id, stem, data, f"og:{page_url}:{image_url}"))
            print(f"OK {list_id}/{stem} <- {page_url}")
        except Exception as exc:
            failures.append({"list": list_id, "row": stem, "requested": page_url, "error": str(exc)})
            print(f"FAIL {list_id}/{stem}: {exc}")

    b.save_cache()
    report_data = {"section": args.section, "completed": completed, "failures": failures}
    report_path = REPORT.with_name(f"{REPORT.stem}_{args.section}{REPORT.suffix}")
    report_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"completed={len(completed)} failures={len(failures)} report={report_path}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
