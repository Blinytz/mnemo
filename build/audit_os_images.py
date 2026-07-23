#!/usr/bin/env python3
from pathlib import Path
import math

from PIL import Image, ImageDraw


def main():
    thumb_dir = Path("thumbs/os")
    suspects = []
    for path in sorted(thumb_dir.glob("*.webp"), key=lambda p: int(p.stem)):
        if path.stat().st_size < 2200:
            suspects.append(int(path.stem))

    print("suspects:", ", ".join(map(str, suspects)))
    cols = 6
    cell_w, cell_h = 150, 132
    rows = max(1, math.ceil(len(suspects) / cols))
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)

    for idx, n in enumerate(suspects):
        path = thumb_dir / f"{n}.webp"
        im = Image.open(path).convert("RGB")
        im.thumbnail((100, 100))
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        sheet.paste(im, (x + 25, y + 4))
        draw.text((x + 4, y + 108), f"{n}  {path.stat().st_size} o", fill=(0, 0, 0))

    out = Path("build/os_suspects_sheet.jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=92)
    print(out)


if __name__ == "__main__":
    main()
