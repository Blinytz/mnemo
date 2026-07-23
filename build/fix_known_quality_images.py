#!/usr/bin/env python3
"""Targeted replacements for visually bad but technically valid thumbnails."""
from pathlib import Path

from build_images import (
    FULL,
    THUMBS,
    _commons_search_files,
    resolve_commons_file,
    to_webp_full,
    to_webp_thumb,
    wiki_batch,
    wiki_download,
)


TARGETS = [
    ("philosophes", "42", "Jacques Derrida", [
        "Jacques Derrida at EGS.jpg",
        "Jacques Derrida 2.jpg",
    ], [
        "wiki:Jacques Derrida",
        "Jacques Derrida portrait",
        "Jacques Derrida photograph",
    ]),
    ("mythologie", "26", "Atlas", [
        "Farnese_Atlas_MAN_Napoli_Inv6374.jpg",
        "Farnese_Atlas,_Museo_Archeologico_Nazionale_di_Napoli.jpg",
    ], [
        "Farnese Atlas sculpture",
        "Atlas Titan sculpture",
    ]),
    ("mythologie", "43", "Dédale", [
        "Daedalus_and_Icarus_MET_DT84.jpg",
        "Daedalus_and_Icarus_by_Charles_Paul_Landon.jpg",
    ], [
        "Daedalus Icarus painting",
        "Daedalus sculpture",
    ]),
    ("mythologie", "58", "Ixion", [
        "Ixion_Ribera.jpg",
        "Jusepe_de_Ribera_-_Ixion_-_WGA19439.jpg",
    ], [
        "Ixion painting",
        "Ixion mythology",
    ]),
]


def write_webp(lid: str, stem: str, blob: bytes):
    thumb_dir = THUMBS / lid
    full_dir = FULL / lid
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    for directory in (thumb_dir, full_dir):
        svg = directory / f"{stem}.svg"
        if svg.exists():
            svg.unlink()
    (thumb_dir / f"{stem}.webp").write_bytes(to_webp_thumb(blob))
    (full_dir / f"{stem}.webp").write_bytes(to_webp_full(blob))


def find_image(filenames, queries):
    for query in queries:
        if not query.startswith("wiki:"):
            continue
        title = query.split(":", 1)[1]
        for host in ("fr.wikipedia.org", "en.wikipedia.org"):
            hit = wiki_batch([title], host=host).get(title)
            if not hit:
                continue
            _thumb, full = wiki_download(hit)
            if full:
                return full, f"{host}:{title}"
    for filename in filenames:
        data, kind = resolve_commons_file(filename, width=900)
        if data and kind == "image":
            return data, filename
    for query in queries:
        if query.startswith("wiki:"):
            continue
        for filename in _commons_search_files(query, limit=12):
            low = filename.lower()
            if not low.endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            if any(nope in low for nope in ("book", "cover", "map", "logo", "icon")):
                continue
            data, kind = resolve_commons_file(filename, width=900)
            if data and kind == "image":
                return data, filename
    return None, None


def main():
    failed = []
    for lid, stem, label, filenames, queries in TARGETS:
        data, source = find_image(filenames, queries)
        if not data:
            failed.append((lid, stem, label))
            print(f"[miss] {lid}/{stem} {label}")
            continue
        write_webp(lid, stem, data)
        print(f"[ok] {lid}/{stem} {label} <- {source}")
    if failed:
        raise SystemExit(f"Missing replacements: {failed}")


if __name__ == "__main__":
    main()
