#!/usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

from PIL import Image

REPO = Path(__file__).parent.parent
THUMBS = REPO / "thumbs"
FULL = REPO / "full"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
MIN_BYTES = 120_000


def file_uri(path: Path) -> str:
    return "file:///" + quote(str(path.resolve()).replace("\\", "/"))


def screenshot_svg(svg_path: Path, png_path: Path, width=1000, height=720):
    subprocess.run(
        [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={width},{height}",
            f"--screenshot={png_path}",
            file_uri(svg_path),
        ],
        check=True,
        timeout=40,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def save_webps(png_path: Path, thumb_out: Path, full_out: Path):
    img = Image.open(png_path).convert("RGBA")
    if img.getbbox():
        img = img.crop(img.getbbox())

    thumb = img.copy()
    ratio = 160 / max(1, thumb.height)
    thumb = thumb.resize((max(1, int(thumb.width * ratio)), 160), Image.LANCZOS)
    thumb.save(thumb_out, "WEBP", quality=68, method=6)

    full = img.copy()
    if max(full.width, full.height) > 720:
        ratio = 720 / max(full.width, full.height)
        full = full.resize((max(1, int(full.width * ratio)), max(1, int(full.height * ratio))), Image.LANCZOS)
    full.save(full_out, "WEBP", quality=72, method=6)


def main():
    if not CHROME.exists():
        raise RuntimeError(f"Chrome introuvable: {CHROME}")
    targets = [p for p in sorted(THUMBS.rglob("*.svg")) if p.stat().st_size >= MIN_BYTES]
    before = 0
    after = 0
    changed = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for svg_path in targets:
            rel = svg_path.relative_to(THUMBS)
            full_svg = FULL / rel
            thumb_webp = svg_path.with_suffix(".webp")
            full_webp = full_svg.with_suffix(".webp")
            before += svg_path.stat().st_size + (full_svg.stat().st_size if full_svg.exists() else 0)
            png_path = tmp / f"{svg_path.parent.name}_{svg_path.stem}.png"
            try:
                screenshot_svg(svg_path, png_path)
                save_webps(png_path, thumb_webp, full_webp)
                svg_path.unlink(missing_ok=True)
                full_svg.unlink(missing_ok=True)
                after += thumb_webp.stat().st_size + full_webp.stat().st_size
                changed += 1
                if changed % 20 == 0:
                    print(f"converted {changed}/{len(targets)}")
            except Exception as exc:
                print(f"skip {rel}: {exc}")
    print(f"converted: {changed}/{len(targets)}")
    print(f"large svg: {before/1048576:.1f} Mo -> {after/1048576:.1f} Mo")


if __name__ == "__main__":
    main()
