#!/usr/bin/env python3
import re
from io import BytesIO
from pathlib import Path

from PIL import Image

REPO = Path(__file__).parent.parent
THUMBS = REPO / "thumbs"
FULL = REPO / "full"

THUMB_H = 160
FULL_MAX = 720
THUMB_Q = 54
FULL_Q = 60


def is_raster(data: bytes) -> bool:
    return data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8") or data.startswith(b"RIFF")


def is_svg_text(data: bytes) -> bool:
    head = data[:500].lstrip().lower()
    return head.startswith(b"<svg") or head.startswith(b"<?xml") or b"<svg" in head


def open_image(data: bytes) -> Image.Image:
    return Image.open(BytesIO(data)).convert("RGBA")


def webp_thumb(data: bytes) -> bytes:
    img = open_image(data)
    ratio = THUMB_H / max(1, img.height)
    img = img.resize((max(1, int(img.width * ratio)), THUMB_H), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, "WEBP", quality=THUMB_Q, method=6)
    return buf.getvalue()


def webp_full(data: bytes) -> bytes:
    img = open_image(data)
    if max(img.width, img.height) > FULL_MAX:
        ratio = FULL_MAX / max(img.width, img.height)
        img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, "WEBP", quality=FULL_Q, method=6)
    return buf.getvalue()


def minify_svg_text(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r">\s+<", "><", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def optimize_pair(thumb_path: Path, full_path: Path, stats: dict):
    data_t = thumb_path.read_bytes()
    data_f = full_path.read_bytes() if full_path.exists() else data_t

    if thumb_path.suffix.lower() == ".svg" and is_raster(data_t):
        out_t = thumb_path.with_suffix(".webp")
        out_f = full_path.with_suffix(".webp")
        out_t.write_bytes(webp_thumb(data_t))
        out_f.write_bytes(webp_full(data_f if is_raster(data_f) else data_t))
        thumb_path.unlink(missing_ok=True)
        if full_path.exists():
            full_path.unlink(missing_ok=True)
        stats["fake_svg_to_webp"] += 1
        return

    if thumb_path.suffix.lower() == ".webp" and is_raster(data_t):
        before = thumb_path.stat().st_size
        new_t = webp_thumb(data_t)
        if len(new_t) < before:
            thumb_path.write_bytes(new_t)
            stats["thumb_webp_recompressed"] += 1

    if full_path.exists() and full_path.suffix.lower() == ".webp":
        data_full = full_path.read_bytes()
        if is_raster(data_full):
            before = full_path.stat().st_size
            new_f = webp_full(data_full)
            if len(new_f) < before:
                full_path.write_bytes(new_f)
                stats["full_webp_recompressed"] += 1

    if thumb_path.suffix.lower() == ".svg" and is_svg_text(data_t):
        try:
            text = data_t.decode("utf-8")
            mini = minify_svg_text(text).encode("utf-8")
            if len(mini) < len(data_t):
                thumb_path.write_bytes(mini)
                stats["svg_minified"] += 1
        except UnicodeDecodeError:
            pass
    if full_path.exists() and full_path.suffix.lower() == ".svg":
        data_full = full_path.read_bytes()
        if is_svg_text(data_full):
            try:
                text = data_full.decode("utf-8")
                mini = minify_svg_text(text).encode("utf-8")
                if len(mini) < len(data_full):
                    full_path.write_bytes(mini)
                    stats["svg_minified"] += 1
            except UnicodeDecodeError:
                pass


def dir_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def main():
    before_t = dir_size(THUMBS)
    before_f = dir_size(FULL)
    stats = {
        "fake_svg_to_webp": 0,
        "thumb_webp_recompressed": 0,
        "full_webp_recompressed": 0,
        "svg_minified": 0,
    }

    for thumb_path in sorted(THUMBS.rglob("*")):
        if not thumb_path.is_file():
            continue
        rel = thumb_path.relative_to(THUMBS)
        full_path = FULL / rel
        optimize_pair(thumb_path, full_path, stats)

    after_t = dir_size(THUMBS)
    after_f = dir_size(FULL)
    print("Optimisation terminée")
    for k, v in stats.items():
        print(f"{k}: {v}")
    print(f"thumbs: {before_t/1048576:.1f} Mo -> {after_t/1048576:.1f} Mo")
    print(f"full:   {before_f/1048576:.1f} Mo -> {after_f/1048576:.1f} Mo")
    print(f"total:  {(before_t+before_f)/1048576:.1f} Mo -> {(after_t+after_f)/1048576:.1f} Mo")


if __name__ == "__main__":
    main()
