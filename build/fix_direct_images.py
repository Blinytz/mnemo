#!/usr/bin/env python3
"""Corrections ciblées d'images connues, sans relancer une liste complète."""
from build_images import (
    THUMBS, FULL, MYTHOLOGY_DIRECT_COMMONS_FILES,
    _download_commons_svg_or_thumb, to_webp_thumb, to_webp_full, verify_image,
)


def write_mythology_known():
    targets = {
        '45': 'Narcisse',
        '60': 'Hypérion',
    }
    for n_str, label in targets.items():
        filename = MYTHOLOGY_DIRECT_COMMONS_FILES[label]
        data, _kind, found = _download_commons_svg_or_thumb(filename, width=900)
        if not data or not verify_image(data):
            raise RuntimeError(f"Image introuvable pour {label}: {filename}")
        thumb = to_webp_thumb(data)
        full = to_webp_full(data)
        if not thumb or not full:
            raise RuntimeError(f"Conversion WebP impossible pour {label}: {found or filename}")
        (THUMBS / 'mythologie').mkdir(parents=True, exist_ok=True)
        (FULL / 'mythologie').mkdir(parents=True, exist_ok=True)
        (THUMBS / 'mythologie' / f'{n_str}.webp').write_bytes(thumb)
        (FULL / 'mythologie' / f'{n_str}.webp').write_bytes(full)
        print(f"{label}: {found or filename}")


if __name__ == '__main__':
    write_mythology_known()
