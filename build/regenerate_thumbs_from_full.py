#!/usr/bin/env python3
"""Regenerate local thumbnails from their matching full-size image.

This enforces the thumbnail/full coherence principle mechanically: when the
full image is a raster image, the thumbnail becomes a crop/resize of that exact
same file, regardless of what a previous scraper downloaded.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
THUMB_MAX = (220, 160)


def extract_lists() -> list[dict]:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
if (start < 0 || end < 0 || end <= start) throw new Error('DEFAULT_LISTS block introuvable');
const data = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
console.log(JSON.stringify(data));
"""
    res = subprocess.run(
        ["node", "-e", js, str(HTML)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(res.stdout)


def extract_full_map() -> dict:
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r"const IMAGE_FILES_MAP = (\{[\s\S]*?\});\s*function localFullImageForThumb", html)
    return json.loads(m.group(1)) if m else {}


def is_image_col(name: str) -> bool:
    n = (name or "").lower()
    return any(token in n for token in ("image", "drapeau", "localisation", "logo", "photo", "portrait"))


def key_for(row_index: int, col_index: int) -> str:
    return str(row_index + 1) if col_index == 1 else f"{row_index + 1}b"


def make_thumb(full_path: Path, thumb_path: Path) -> bool:
    if full_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        return False
    if thumb_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        return False
    with Image.open(full_path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail(THUMB_MAX, Image.Resampling.LANCZOS)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        save_kwargs = {"quality": 82, "method": 6}
        if thumb_path.suffix.lower() == ".png":
            im.save(thumb_path, "PNG", optimize=True)
        elif thumb_path.suffix.lower() in {".jpg", ".jpeg"}:
            im.save(thumb_path, "JPEG", quality=86, optimize=True, progressive=True)
        else:
            im.save(thumb_path, "WEBP", **save_kwargs)
    return True


def main() -> None:
    lists = extract_lists()
    full_map = extract_full_map()
    updated = []
    skipped = []
    for lst in lists:
        list_id = lst["id"]
        cols = lst.get("columns") or []
        image_cols = [i for i, c in enumerate(cols) if is_image_col(str(c))]
        for ri, row in enumerate(lst.get("rows") or []):
            for ci in image_cols:
                thumb = str(row[ci] if ci < len(row) else "").strip()
                if not thumb.startswith("thumbs/"):
                    continue
                full = (full_map.get(list_id) or {}).get(key_for(ri, ci), "")
                if not full:
                    continue
                thumb_path = ROOT / thumb
                full_path = ROOT / full
                if not thumb_path.exists() or not full_path.exists():
                    skipped.append([list_id, ri + 1, thumb, full, "missing"])
                    continue
                try:
                    if make_thumb(full_path, thumb_path):
                        updated.append([list_id, ri + 1, thumb, full])
                    else:
                        skipped.append([list_id, ri + 1, thumb, full, "non-raster-or-svg-thumb"])
                except Exception as exc:
                    skipped.append([list_id, ri + 1, thumb, full, str(exc)])
    print(json.dumps({
        "updated": len(updated),
        "skipped": len(skipped),
        "updated_sample": updated[:20],
        "skipped_sample": skipped[:20],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
