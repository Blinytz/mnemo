#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import build_images as b


def font(size, bold=False):
    for name in ("arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def main():
    w, h = 1200, 900
    im = Image.new("RGB", (w, h), "#111827")
    d = ImageDraw.Draw(im)

    for r, col in [(360, "#facc15"), (265, "#f59e0b"), (180, "#fde68a")]:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.ellipse((600 - r, 390 - r, 600 + r, 390 + r), fill=col + "55")
        layer = layer.filter(ImageFilter.GaussianBlur(35))
        im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
        d = ImageDraw.Draw(im)

    d.ellipse((458, 250, 742, 534), fill="#fbbf24", outline="#fff7cc", width=8)
    for a in range(0, 360, 20):
        import math
        rad = math.radians(a)
        x1 = 600 + math.cos(rad) * 178
        y1 = 392 + math.sin(rad) * 178
        x2 = 600 + math.cos(rad) * 285
        y2 = 392 + math.sin(rad) * 285
        d.line((x1, y1, x2, y2), fill="#fde68a", width=10)

    d.rectangle((470, 520, 730, 720), fill="#2f2414", outline="#fde68a", width=5)
    d.polygon([(470, 520), (600, 430), (730, 520)], fill="#3f2f18", outline="#fde68a")
    d.line((600, 430, 600, 720), fill="#fde68a", width=5)

    d.text((70, 64), "Hypérion", fill="#fff7cc", font=font(72, True))
    d.text((74, 148), "Titan de la lumière céleste", fill="#fcd34d", font=font(38))
    d.text((74, 780), "Visuel local pédagogique", fill="#d1d5db", font=font(28))

    full = Path("full/mythologie/60.png")
    full.parent.mkdir(parents=True, exist_ok=True)
    im.save(full)
    Path("thumbs/mythologie").mkdir(parents=True, exist_ok=True)
    Path("thumbs/mythologie/60.webp").write_bytes(b.to_webp_thumb(full.read_bytes()))
    print("Hyperion local -> full/mythologie/60.png")


if __name__ == "__main__":
    main()
