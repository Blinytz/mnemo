#!/usr/bin/env python3
"""Force classical wiki images for mythology rows still showing Hades icons."""
from build_images import FULL, THUMBS, to_webp_full, to_webp_thumb, wiki_batch, wiki_download


TARGETS = [
    ("27", "Atlas", [("Atlas (mythology)", "en.wikipedia.org"), ("Atlas (mythologie)", "fr.wikipedia.org")]),
    ("44", "Dédale", [("Daedalus", "en.wikipedia.org"), ("Dédale", "fr.wikipedia.org")]),
    ("59", "Ixion", [("Ixion", "en.wikipedia.org"), ("Ixion", "fr.wikipedia.org")]),
]


def write(stem, data):
    for directory in (THUMBS / "mythologie", FULL / "mythologie"):
        for ext in ("webp", "svg"):
            (directory / f"{stem}.{ext}").unlink(missing_ok=True)
    (THUMBS / "mythologie" / f"{stem}.webp").write_bytes(to_webp_thumb(data))
    (FULL / "mythologie" / f"{stem}.webp").write_bytes(to_webp_full(data))


def main():
    failed = []
    for stem, label, candidates in TARGETS:
        done = False
        for title, host in candidates:
            hit = wiki_batch([title], host=host).get(title)
            if not hit:
                continue
            thumb, full = wiki_download(hit)
            data = full or thumb
            if not data:
                continue
            write(stem, data)
            print(f"[ok] {stem} {label} <- {host}:{title}")
            done = True
            break
        if not done:
            failed.append((stem, label))
    if failed:
        raise SystemExit(f"Missing mythology direct fixes: {failed}")


if __name__ == "__main__":
    main()
