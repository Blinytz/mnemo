#!/usr/bin/env python3
"""Injecte build/image_files_map.json dans const IMAGE_FILES_MAP de memo.html."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
MAP = ROOT / "build" / "image_files_map.json"


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    data = json.loads(MAP.read_text(encoding="utf-8"))
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    pattern = r"const IMAGE_FILES_MAP = \{[\s\S]*?\};\s*function localFullImageForThumb"
    repl = f"const IMAGE_FILES_MAP = {payload};\nfunction localFullImageForThumb"
    new_html, count = re.subn(pattern, repl, html, count=1)
    if count != 1:
        raise SystemExit("IMAGE_FILES_MAP introuvable ou ambigu")
    HTML.write_text(new_html, encoding="utf-8", newline="")
    print(f"IMAGE_FILES_MAP synchronisé: {sum(len(v) for v in data.values())} entrées")


if __name__ == "__main__":
    main()
