#!/usr/bin/env python3
import re
from pathlib import Path

REPO = Path(__file__).parent.parent


def minify_svg(data: bytes) -> bytes:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r">\s+<", "><", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip().encode("utf-8")


def main():
    files = list((REPO / "thumbs").rglob("*.svg")) + list((REPO / "full").rglob("*.svg"))
    before = sum(p.stat().st_size for p in files)
    changed = 0
    for path in files:
        old = path.read_bytes()
        new = minify_svg(old)
        if len(new) < len(old):
            path.write_bytes(new)
            changed += 1
    after = sum(p.stat().st_size for p in files if p.exists())
    print(f"svg minified: {changed}/{len(files)}")
    print(f"svg: {before/1048576:.1f} Mo -> {after/1048576:.1f} Mo")


if __name__ == "__main__":
    main()
