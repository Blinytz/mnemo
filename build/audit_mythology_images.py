#!/usr/bin/env python3
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


def extract_lists():
    out = subprocess.check_output(["node", "build/extract_data.js", "memo.html"], text=True, encoding="utf-8")
    return json.loads(out)["DEFAULT_LISTS"]


def main():
    lists = extract_lists()
    myth = next(l for l in lists if l["id"] == "mythologie")
    img_idx = myth["columns"].index("Image")
    name_idx = myth["columns"].index("Nom")
    entries = []
    for row in myth["rows"]:
        path = Path(row[img_idx])
        entries.append((str(row[0]), str(row[name_idx]), path))

    cols = 5
    cell_w, cell_h = 210, 150
    sheet = Image.new("RGB", (cols * cell_w, math.ceil(len(entries) / cols) * cell_h), "white")
    draw = ImageDraw.Draw(sheet)

    for idx, (num, name, path) in enumerate(entries):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        if path.exists():
            im = Image.open(path).convert("RGB")
            im.thumbnail((120, 104))
            sheet.paste(im, (x + 45, y + 4))
            size = path.stat().st_size
        else:
            draw.rectangle((x + 45, y + 4, x + 165, y + 108), fill="#f8d7da", outline="#842029")
            size = 0
        draw.text((x + 4, y + 112), f"{num}. {name}"[:30], fill=(0, 0, 0))
        draw.text((x + 4, y + 132), f"{path.name} {size} o", fill=(80, 80, 80))

    out = Path("build/mythologie_sheet.jpg")
    sheet.save(out, quality=92)
    print(out)


if __name__ == "__main__":
    main()
