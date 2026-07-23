#!/usr/bin/env python3
"""Trim excess white margins around department emblem WebPs."""
from pathlib import Path

from PIL import Image, ImageChops

REPO = Path(__file__).parent.parent


def trim_white(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    diff = ImageChops.difference(rgba, bg).convert("L")
    mask = diff.point(lambda p: 255 if p > 12 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return rgba
    left, top, right, bottom = bbox
    pad = 8
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(rgba.width, right + pad)
    bottom = min(rgba.height, bottom + pad)
    return rgba.crop((left, top, right, bottom))


def save_versions(src: Path, full_path: Path):
    img = trim_white(Image.open(src))
    thumb = img.copy()
    ratio = 160 / max(1, thumb.height)
    thumb = thumb.resize((max(1, int(thumb.width * ratio)), 160), Image.LANCZOS)
    thumb.save(src, "WEBP", quality=72, method=6)

    full = img.copy()
    if max(full.width, full.height) > 640:
        ratio = 640 / max(full.width, full.height)
        full = full.resize((max(1, int(full.width * ratio)), max(1, int(full.height * ratio))), Image.LANCZOS)
    full.save(full_path, "WEBP", quality=76, method=6)


def main():
    changed = 0
    for thumb in sorted((REPO / "thumbs" / "departements").glob("*.webp")):
        if thumb.stem.endswith("b"):
            continue
        full = REPO / "full" / "departements" / thumb.name
        if not full.exists():
            continue
        before = thumb.stat().st_size + full.stat().st_size
        save_versions(thumb, full)
        after = thumb.stat().st_size + full.stat().st_size
        if after != before:
            changed += 1
    print(f"trimmed department emblems: {changed}")


if __name__ == "__main__":
    main()
