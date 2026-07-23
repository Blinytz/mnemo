#!/usr/bin/env python3
"""Synchronise IMAGE_FILES_MAP avec les grandes images qui correspondent aux miniatures.

Pour chaque cellule image locale, le script cherche les fichiers full/<liste>/<clé>.*
existants et choisit le meilleur candidat par similarité visuelle avec la miniature.
Cela évite qu'une miniature ouvre une ancienne grande image encore présente sur disque.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
MAP_JSON = ROOT / "build" / "image_files_map.json"
RASTER = {".jpg", ".jpeg", ".png", ".webp"}
VECTOR = {".svg"}
ALL_IMAGE_EXTS = RASTER | VECTOR


def extract_lists() -> list[dict]:
    raw = subprocess.check_output(
        ["node", "build/extract_data.js", "memo.html"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    data = json.loads(raw.lstrip("\ufeff"))
    return data["DEFAULT_LISTS"]


def image_columns(columns: list[str]) -> list[int]:
    out = []
    for idx, col in enumerate(columns):
        name = str(col or "").lower()
        if any(token in name for token in ("image", "drapeau", "localisation", "logo", "photo", "portrait")):
            out.append(idx)
    return out


def key_for(row_index: int, col_index: int) -> str:
    return str(row_index + 1) if col_index == 1 else f"{row_index + 1}b"


def candidates_for(list_id: str, key: str) -> list[Path]:
    base = ROOT / "full" / list_id
    if not base.exists():
        return []
    return sorted(
        [p for p in base.glob(f"{key}.*") if p.suffix.lower() in ALL_IMAGE_EXTS],
        key=lambda p: (
            # Prefer newer corrected files when visual comparison cannot decide.
            -p.stat().st_mtime,
            p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"},
            p.name,
        ),
    )


def raster_signature(path: Path) -> Image.Image | None:
    if path.suffix.lower() not in RASTER:
        return None
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((96, 96), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (96, 96), "white")
            canvas.paste(im, ((96 - im.width) // 2, (96 - im.height) // 2))
            return canvas
    except Exception:
        return None


def visual_distance(a: Image.Image, b: Image.Image) -> float:
    diff = ImageChops.difference(a, b)
    hist = diff.histogram()
    sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(hist))
    return (sum(sq) / (96 * 96 * 3)) ** 0.5


def choose_full(thumb_path: Path, candidates: list[Path]) -> Path | None:
    if not candidates:
        return None

    if thumb_path.suffix.lower() in VECTOR:
        same_ext = [p for p in candidates if p.suffix.lower() == thumb_path.suffix.lower()]
        return same_ext[0] if same_ext else candidates[0]

    thumb_sig = raster_signature(thumb_path)
    if thumb_sig is None:
        return candidates[0]

    scored: list[tuple[float, Path]] = []
    for candidate in candidates:
        sig = raster_signature(candidate)
        if sig is not None:
            scored.append((visual_distance(thumb_sig, sig), candidate))

    if scored:
        scored.sort(key=lambda item: (item[0], -item[1].stat().st_mtime))
        return scored[0][1]

    return candidates[0]


def inject_map(data: dict[str, dict[str, str]]) -> None:
    html = HTML.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    pattern = r"const IMAGE_FILES_MAP = \{[\s\S]*?\};\s*(?:IMAGE_FILES_MAP\.constellations = [\s\S]*?\);\s*)?function localFullImageForThumb"
    repl = f"const IMAGE_FILES_MAP = {payload};\nfunction localFullImageForThumb"
    html, count = re.subn(pattern, repl, html, count=1)
    if count != 1:
        raise SystemExit("Impossible de remplacer IMAGE_FILES_MAP")
    HTML.write_text(html, encoding="utf-8", newline="")


def bump_versions(version: int) -> None:
    html = HTML.read_text(encoding="utf-8")
    html = re.sub(r"const FORCE_DEFAULT_REFRESH_VERSION = \d+;", f"const FORCE_DEFAULT_REFRESH_VERSION = {version};", html)
    html = re.sub(r"const APP_DATA_VERSION = \d+;", f"const APP_DATA_VERSION = {version};", html)
    HTML.write_text(html, encoding="utf-8", newline="")
    sw = ROOT / "sw.js"
    if sw.exists():
        text = sw.read_text(encoding="utf-8")
        text = re.sub(r"memo-v\d+", f"memo-v{version}", text)
        sw.write_text(text, encoding="utf-8", newline="")


def main() -> None:
    lists = extract_lists()
    result: dict[str, dict[str, str]] = {}
    missing = []
    chosen = []

    for lst in lists:
        list_id = lst["id"]
        cols = lst.get("columns") or []
        for ri, row in enumerate(lst.get("rows") or []):
            for ci in image_columns(cols):
                if ci >= len(row):
                    continue
                thumb = str(row[ci] or "").strip()
                if not thumb.startswith("thumbs/"):
                    continue
                key = key_for(ri, ci)
                thumb_path = ROOT / thumb
                full = choose_full(thumb_path, candidates_for(list_id, key))
                if full is None:
                    missing.append([list_id, key, thumb])
                    continue
                rel = full.relative_to(ROOT).as_posix()
                result.setdefault(list_id, {})[key] = rel
                chosen.append([list_id, key, thumb, rel])

    # Certaines listes d'extension sont construites avec des visuels injectés
    # après extraction statique. On complète donc depuis les dossiers locaux.
    full_root = ROOT / "full"
    for full_dir in sorted(p for p in full_root.iterdir() if p.is_dir()):
        list_id = full_dir.name
        thumb_dir = ROOT / "thumbs" / list_id
        keys = sorted({p.stem for p in full_dir.iterdir() if p.suffix.lower() in ALL_IMAGE_EXTS})
        for key in keys:
            if key in result.get(list_id, {}):
                continue
            thumb_candidates = []
            if thumb_dir.exists():
                thumb_candidates = sorted(
                    [p for p in thumb_dir.glob(f"{key}.*") if p.suffix.lower() in ALL_IMAGE_EXTS],
                    key=lambda p: (
                        p.suffix.lower() not in {".webp", ".jpg", ".jpeg", ".png"},
                        -p.stat().st_mtime,
                        p.name,
                    ),
                )
            full = choose_full(thumb_candidates[0], candidates_for(list_id, key)) if thumb_candidates else None
            if full is None:
                candidates = candidates_for(list_id, key)
                full = candidates[0] if candidates else None
            if full is None:
                continue
            result.setdefault(list_id, {})[key] = full.relative_to(ROOT).as_posix()

    MAP_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    inject_map(result)
    bump_versions(82)

    report = {
        "mapped": sum(len(v) for v in result.values()),
        "lists": len(result),
        "missing": len(missing),
        "missing_sample": missing[:50],
        "chosen_sample": chosen[:30],
    }
    (ROOT / "build" / "coherent_image_map_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
