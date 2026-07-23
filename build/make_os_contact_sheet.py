#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw


def sheet(nums, name):
    out = Image.new("RGB", (len(nums) * 150, 132), "white")
    draw = ImageDraw.Draw(out)
    for i, n in enumerate(nums):
        p = Path("thumbs/os") / f"{n}.webp"
        im = Image.open(p).convert("RGB")
        im.thumbnail((110, 100))
        x = i * 150
        out.paste(im, (x + 20, 4))
        draw.text((x + 5, 110), str(n), fill=(0, 0, 0))
    out.save(Path("build") / name, quality=92)


def main():
    sheet(range(63, 71), "os_carpes_sheet.jpg")
    sheet(range(97, 104), "os_tarse_sheet.jpg")
    sheet(range(109, 123), "os_phalanges_pied_sheet.jpg")


if __name__ == "__main__":
    main()
