#!/usr/bin/env python3
"""Régénère les miniatures depuis les full HD déjà valides.

Cette passe corrige la cohérence miniature/full sans changer le sujet de l'image.
Elle ne traite que les lignes signalées possible_mismatch dont le full raster
atteint les seuils HD.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "build" / "hd_audit.csv"
MIN_LONG = 1200
MIN_SHORT = 650


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    with AUDIT.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    targets = []
    for row in rows:
        issues = set((row.get("issues") or "").split("|"))
        if "possible_mismatch" not in issues:
            continue
        if row.get("full_kind") != "raster":
            continue
        if int(row.get("full_long") or 0) < MIN_LONG or int(row.get("full_short") or 0) < MIN_SHORT:
            continue
        if not row.get("full") or not row.get("thumb"):
            continue
        targets.append(row)
    if args.limit:
        targets = targets[:args.limit]
    changed = 0
    for row in targets:
        full = ROOT / row["full"]
        thumb = ROOT / row["thumb"]
        if not full.exists():
            continue
        try:
            with Image.open(full) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((220, 170), Image.Resampling.LANCZOS)
                thumb.parent.mkdir(parents=True, exist_ok=True)
                im.save(thumb, "WEBP", quality=86, method=6)
            changed += 1
            print(f"OK {row['list_id']} #{row['key']} {thumb}")
        except Exception as exc:
            print(f"FAIL {row['list_id']} #{row['key']} {exc}")
    print(f"changed={changed}")


if __name__ == "__main__":
    main()
