#!/usr/bin/env python3
"""Direct fixes for department image cells that generic Commons search misses."""
from build_images import (
    FULL,
    THUMBS,
    _download_commons_svg_or_thumb,
    to_webp_full,
    to_webp_thumb,
    wiki_batch,
    wiki_download,
)


TARGETS = [
    ("4", "Alpes-de-Haute-Provence", [
        "Blason département Alpes-de-Haute-Provence.svg",
        "Drapeau fr département Alpes-de-Haute-Provence.svg",
        "Logo Alpes-de-Haute-Provence - 2015.svg",
    ], ["Alpes-de-Haute-Provence"]),
    ("5", "Hautes-Alpes", [
        "Logo_Hautes_Alpes.svg",
        "Blason département Hautes-Alpes.svg",
    ], ["Hautes-Alpes"]),
    ("6", "Alpes-Maritimes", [
        "Département Alpes-Maritimes logo 2.svg",
        "Departement Alpes-Maritimes logo 2.svg",
        "Blason département Alpes-Maritimes.svg",
    ], ["Alpes-Maritimes"]),
    ("97", "Guadeloupe", [
        "Flag of Guadeloupe (local).svg",
        "Flag of Guadeloupe.svg",
        "Logo Département Guadeloupe.svg",
        "Logo du conseil départemental de la Guadeloupe.svg",
    ], ["Conseil départemental de la Guadeloupe", "Guadeloupe"]),
    ("98", "Martinique", [
        "Logotype de la collectivité territoriale de Martinique.svg",
        "Logo cg Martinique.jpg",
        "Flag-of-Martinique.svg",
    ], ["Martinique"]),
    ("99", "Guyane", [
        "Collectivité_territoriale_de_Guyane_(logo).svg",
        "Coat of arms of French Guiana, according to the original displayed at the Museum Franconie, at Cayenne.svg",
        "Blason département fr Guyane.svg",
        "Blason département Guyane.svg",
        "Blason de la Guyane.svg",
    ], []),
    ("100", "La Réunion", [
        "Armoiries_Réunion.svg",
        "BlasonRéunion.svg",
        "Blason département fr La Réunion.svg",
        "Blason département La Réunion.svg",
        "Blason Réunion.svg",
    ], []),
]


def clear_existing(stem):
    for directory in (THUMBS / "departements", FULL / "departements"):
        for ext in ("webp", "svg"):
            path = directory / f"{stem}.{ext}"
            path.unlink(missing_ok=True)


def write_asset(stem, data, kind):
    clear_existing(stem)
    thumb_dir = THUMBS / "departements"
    full_dir = FULL / "departements"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    if kind == "svg":
        (thumb_dir / f"{stem}.svg").write_bytes(data)
        (full_dir / f"{stem}.svg").write_bytes(data)
        return "svg"
    (thumb_dir / f"{stem}.webp").write_bytes(to_webp_thumb(data))
    (full_dir / f"{stem}.webp").write_bytes(to_webp_full(data))
    return "webp"


def resolve(filenames, wiki_titles):
    for filename in filenames:
        data, kind, found = _download_commons_svg_or_thumb(filename, width=900)
        if data:
            return data, kind, found
    for title in wiki_titles:
        hit = wiki_batch([title], host="fr.wikipedia.org").get(title)
        if not hit:
            hit = wiki_batch([title], host="en.wikipedia.org").get(title)
        if hit:
            _thumb, full = wiki_download(hit)
            if full:
                return full, "image", f"wiki:{title}"
    return None, None, None


def main():
    failed = []
    for stem, label, filenames, wiki_titles in TARGETS:
        data, kind, source = resolve(filenames, wiki_titles)
        if not data:
            failed.append((stem, label))
            print(f"[miss] {stem} {label}")
            continue
        ext = write_asset(stem, data, kind)
        print(f"[ok] {stem} {label} -> {ext} ({source})")
    if failed:
        raise SystemExit(f"Missing department direct fixes: {failed}")


if __name__ == "__main__":
    main()
