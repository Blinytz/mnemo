#!/usr/bin/env python3
"""Audit HD des couples thumbs/full utilisés par memo.html.

Objectif: repérer ce qui empêche une couverture 100% HD:
- miniature absente
- image full absente
- full raster trop petite
- full raster très compressée
- miniature/full probablement incohérentes
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
OUT_CSV = ROOT / "build" / "hd_audit.csv"
OUT_JSON = ROOT / "build" / "hd_audit_summary.json"

MIN_LONG = 1200
MIN_SHORT = 650
MIN_BYTES_RASTER = 35_000


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
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    return json.loads(res.stdout)


def extract_full_map() -> dict:
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r"const IMAGE_FILES_MAP = (\{[\s\S]*?\});\s*function localFullImageForThumb", html)
    return json.loads(m.group(1)) if m else {}


def is_image_col(name: str) -> bool:
    return bool(re.search(r"image|drapeau|localisation|logo", name or "", re.I))


def key_for_cell(row_index: int, ci: int) -> str:
    return str(row_index + 1) if ci == 1 else f"{row_index + 1}b"


_IMAGE_INFO_CACHE: dict[str, dict] = {}


def image_info(path: Path) -> dict:
    cache_key = str(path)
    if cache_key in _IMAGE_INFO_CACHE:
        return _IMAGE_INFO_CACHE[cache_key]
    if not path.exists():
        info = {"exists": False}
        _IMAGE_INFO_CACHE[cache_key] = info
        return info
    if path.suffix.lower() == ".svg":
        info = {
            "exists": True,
            "kind": "svg",
            "bytes": path.stat().st_size,
            "width": "",
            "height": "",
            "long": "",
            "short": "",
            "hash": "",
            "mean": "",
        }
        _IMAGE_INFO_CACHE[cache_key] = info
        return info
    try:
        with Image.open(path) as im:
            w, h = im.size
            rgb = im.convert("RGB")
            small = rgb.resize((8, 8), Image.Resampling.LANCZOS).convert("L")
            pix = list(small.getdata())
            avg = sum(pix) / len(pix)
            bits = "".join("1" if p >= avg else "0" for p in pix)
            stat = ImageStat.Stat(rgb.resize((32, 32), Image.Resampling.LANCZOS))
            mean = tuple(round(x, 1) for x in stat.mean)
        info = {
            "exists": True,
            "kind": "raster",
            "bytes": path.stat().st_size,
            "width": w,
            "height": h,
            "long": max(w, h),
            "short": min(w, h),
            "hash": bits,
            "mean": mean,
        }
        _IMAGE_INFO_CACHE[cache_key] = info
        return info
    except Exception as exc:
        info = {"exists": True, "kind": "broken", "bytes": path.stat().st_size, "error": str(exc)}
        _IMAGE_INFO_CACHE[cache_key] = info
        return info


def hamming(a: str, b: str) -> int | str:
    if not a or not b or len(a) != len(b):
        return ""
    return sum(c1 != c2 for c1, c2 in zip(a, b))


def main() -> None:
    lists = extract_lists()
    full_map = extract_full_map()
    rows = []
    summary = {
        "image_cells": 0,
        "ok": 0,
        "issues": 0,
        "missing_thumb": 0,
        "missing_full": 0,
        "low_resolution": 0,
        "low_bytes": 0,
        "possible_mismatch": 0,
        "by_list": {},
    }

    for lst in lists:
        list_id = lst["id"]
        columns = lst.get("columns") or []
        image_cols = [i for i, name in enumerate(columns) if is_image_col(str(name))]
        for ri, row in enumerate(lst.get("rows") or []):
            label = " / ".join(str(x) for x in row[2:5] if x)[:180]
            for ci in image_cols:
                thumb_raw = str(row[ci] if ci < len(row) else "").strip()
                if not thumb_raw or thumb_raw.startswith("data:image/"):
                    continue
                if not thumb_raw.startswith("thumbs/"):
                    continue

                key = key_for_cell(ri, ci)
                full_raw = (full_map.get(list_id) or {}).get(key, "")
                if not full_raw:
                    # Fallback naturel si la map est absente.
                    stem = Path(thumb_raw).stem
                    candidates = sorted((ROOT / "full" / list_id).glob(f"{stem}.*"))
                    full_raw = str(candidates[0].relative_to(ROOT)).replace("\\", "/") if candidates else ""

                thumb_path = ROOT / thumb_raw
                full_path = ROOT / full_raw if full_raw else ROOT / "__missing__"
                tinfo = image_info(thumb_path)
                finfo = image_info(full_path)

                issues = []
                if not tinfo.get("exists"):
                    issues.append("missing_thumb")
                    summary["missing_thumb"] += 1
                if not full_raw or not finfo.get("exists"):
                    issues.append("missing_full")
                    summary["missing_full"] += 1
                if finfo.get("kind") == "raster":
                    if int(finfo["long"]) < MIN_LONG or int(finfo["short"]) < MIN_SHORT:
                        issues.append("low_resolution")
                        summary["low_resolution"] += 1
                    if int(finfo["bytes"]) < MIN_BYTES_RASTER:
                        issues.append("low_bytes")
                        summary["low_bytes"] += 1
                    dist = hamming(str(tinfo.get("hash", "")), str(finfo.get("hash", "")))
                    if isinstance(dist, int) and dist > 26:
                        issues.append("possible_mismatch")
                        summary["possible_mismatch"] += 1
                else:
                    dist = ""

                status = "ok" if not issues else "issue"
                summary["image_cells"] += 1
                if status == "ok":
                    summary["ok"] += 1
                else:
                    summary["issues"] += 1
                by = summary["by_list"].setdefault(list_id, {"total": 0, "issues": 0})
                by["total"] += 1
                if issues:
                    by["issues"] += 1

                rows.append({
                    "status": status,
                    "issues": "|".join(issues),
                    "list_id": list_id,
                    "row": ri + 1,
                    "column": columns[ci],
                    "key": key,
                    "label": label,
                    "thumb": thumb_raw,
                    "full": full_raw,
                    "thumb_kind": tinfo.get("kind", ""),
                    "thumb_w": tinfo.get("width", ""),
                    "thumb_h": tinfo.get("height", ""),
                    "thumb_bytes": tinfo.get("bytes", ""),
                    "full_kind": finfo.get("kind", ""),
                    "full_w": finfo.get("width", ""),
                    "full_h": finfo.get("height", ""),
                    "full_long": finfo.get("long", ""),
                    "full_short": finfo.get("short", ""),
                    "full_bytes": finfo.get("bytes", ""),
                    "hash_distance": dist,
                })

    rows.sort(key=lambda r: (
        0 if r["status"] == "issue" else 1,
        r["list_id"],
        int(r["row"]),
        r["key"],
    ))
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nCSV: {OUT_CSV}")
    print(f"JSON: {OUT_JSON}")


if __name__ == "__main__":
    main()
