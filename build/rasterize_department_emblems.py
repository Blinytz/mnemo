#!/usr/bin/env python3
"""Rasterize primary department SVG emblems to WebP.

US flags stay SVG because rasterizing them caused bad crops. Department emblems
are simpler and benefit from WebP for size and audit visibility.
"""
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

from PIL import Image

REPO = Path(__file__).parent.parent
THUMBS = REPO / "thumbs" / "departements"
FULL = REPO / "full" / "departements"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def file_uri(path: Path) -> str:
    return "file:///" + quote(str(path.resolve()).replace("\\", "/"))


def screenshot_svg(svg_path: Path, png_path: Path):
    cmd = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=900,900",
        f"--screenshot={png_path}",
        file_uri(svg_path),
    ]
    subprocess.run(cmd, check=True, timeout=40, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def save_webp(png_path: Path, thumb_out: Path, full_out: Path):
    img = Image.open(png_path).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    thumb = img.copy()
    ratio = 160 / max(1, thumb.height)
    thumb = thumb.resize((max(1, int(thumb.width * ratio)), 160), Image.LANCZOS)
    thumb.save(thumb_out, "WEBP", quality=72, method=6)

    full = img.copy()
    if max(full.width, full.height) > 640:
        ratio = 640 / max(full.width, full.height)
        full = full.resize((max(1, int(full.width * ratio)), max(1, int(full.height * ratio))), Image.LANCZOS)
    full.save(full_out, "WEBP", quality=76, method=6)


def main():
    if not CHROME.exists():
        raise RuntimeError(f"Chrome introuvable: {CHROME}")
    targets = [p for p in sorted(THUMBS.glob("*.svg")) if not p.stem.endswith("b")]
    before = 0
    after = 0
    changed = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for svg_path in targets:
            full_svg = FULL / svg_path.name
            thumb_webp = svg_path.with_suffix(".webp")
            full_webp = full_svg.with_suffix(".webp")
            before += svg_path.stat().st_size + (full_svg.stat().st_size if full_svg.exists() else 0)
            png_path = tmp / f"{svg_path.stem}.png"
            try:
                screenshot_svg(svg_path, png_path)
                save_webp(png_path, thumb_webp, full_webp)
                svg_path.unlink(missing_ok=True)
                full_svg.unlink(missing_ok=True)
                after += thumb_webp.stat().st_size + full_webp.stat().st_size
                changed += 1
            except Exception as exc:
                print(f"skip {svg_path.name}: {exc}")
    print(f"converted: {changed}/{len(targets)}")
    print(f"department emblem svg: {before/1048576:.1f} Mo -> {after/1048576:.1f} Mo")


if __name__ == "__main__":
    main()
