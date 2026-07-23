#!/usr/bin/env python3
"""Restore US state flags as original SVG files.

The generic SVG rasterizer made a few seal-based flags unreadable/cropped. For
this column, SVG is the safest runtime asset: small, sharp, and already local.
"""
import json
from pathlib import Path

from build_images import DATA_F, FULL, THUMBS, http_get, load_cache, save_cache, verify_image


def main():
    data = json.loads(DATA_F.read_text(encoding="utf-8"))
    states = next(lst for lst in data["DEFAULT_LISTS"] if lst["id"] == "etats_usa")
    out_t = THUMBS / "etats_usa"
    out_f = FULL / "etats_usa"
    out_t.mkdir(parents=True, exist_ok=True)
    out_f.mkdir(parents=True, exist_ok=True)

    load_cache()
    restored = 0
    failed = []
    for index, row in enumerate(states["rows"], start=1):
        url = str(row[1] or "").strip()
        if not url:
            failed.append((index, row[2] if len(row) > 2 else "", "empty-url"))
            continue
        blob, status, _ = http_get(url, is_image=True, timeout=30)
        if status != 200 or not verify_image(blob, is_svg=True):
            failed.append((index, row[2] if len(row) > 2 else "", f"status={status}"))
            continue

        for directory in (out_t, out_f):
            webp = directory / f"{index}.webp"
            if webp.exists():
                webp.unlink()
            (directory / f"{index}.svg").write_bytes(blob)
        restored += 1
        print(f"[ok] {index:02d} {row[2]} -> svg")

    save_cache()
    print(f"Restored: {restored}/50")
    if failed:
        print("Failed:")
        for item in failed:
            print("  ", item)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
