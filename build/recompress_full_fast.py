#!/usr/bin/env python3
from io import BytesIO
from pathlib import Path

from PIL import Image

REPO = Path(__file__).parent.parent
FULL = REPO / "full"
MAX_DIM = 640
QUALITY = 52


def recompress(path: Path) -> bool:
    data = path.read_bytes()
    if not data.startswith(b"RIFF"):
        return False
    img = Image.open(BytesIO(data)).convert("RGBA")
    if max(img.width, img.height) > MAX_DIM:
        ratio = MAX_DIM / max(img.width, img.height)
        img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, "WEBP", quality=QUALITY, method=4)
    out = buf.getvalue()
    if len(out) < len(data):
        path.write_bytes(out)
        return True
    return False


def main():
    files = list(FULL.rglob("*.webp"))
    before = sum(p.stat().st_size for p in files)
    changed = 0
    for p in files:
        if recompress(p):
            changed += 1
    after = sum(p.stat().st_size for p in files)
    print(f"full webp recompressed: {changed}/{len(files)}")
    print(f"full webp: {before/1048576:.1f} Mo -> {after/1048576:.1f} Mo")


if __name__ == "__main__":
    main()
