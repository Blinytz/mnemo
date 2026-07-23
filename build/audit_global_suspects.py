#!/usr/bin/env python3
from pathlib import Path
import math

from PIL import Image, ImageDraw


def is_beige_placeholder(path: Path) -> bool:
    try:
        im = Image.open(path).convert("RGB").resize((32, 32))
    except Exception:
        return False
    pixels = list(im.getdata())
    beige = sum(1 for r, g, b in pixels if r > 200 and g > 185 and b > 155 and abs(r - g) < 35)
    dark = sum(1 for r, g, b in pixels if r < 90 and g < 90 and b < 90)
    return beige > 680 and dark < 80


def main():
    suspects = []
    for path in sorted(Path("thumbs").glob("*/*.webp")):
        size = path.stat().st_size
        if size < 1700 or is_beige_placeholder(path):
            suspects.append(path)

    print(f"suspects: {len(suspects)}")
    for path in suspects:
        print(f"{path.as_posix()} {path.stat().st_size}")

    cols = 6
    cell_w, cell_h = 190, 144
    rows = max(1, math.ceil(len(suspects) / cols))
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, path in enumerate(suspects):
        im = Image.open(path).convert("RGB")
        im.thumbnail((110, 92))
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        sheet.paste(im, (x + 40, y + 4))
        label = f"{path.parent.name}/{path.stem}"
        draw.text((x + 4, y + 100), label[:28], fill=(0, 0, 0))
        draw.text((x + 4, y + 120), f"{path.stat().st_size} o", fill=(80, 80, 80))
    out = Path("build/global_suspects_sheet.jpg")
    sheet.save(out, quality=92)
    print(out)


if __name__ == "__main__":
    main()
