#!/usr/bin/env python3
import requests

import build_images as b

URL = "https://upload.wikimedia.org/wikipedia/commons/9/94/Hyperion_true.jpg"


def write(data: bytes):
    thumb = b.to_webp_thumb(data)
    if not thumb:
        raise RuntimeError("thumb impossible: Hyperion")
    ext = b.raster_ext(data)
    (b.THUMBS / "mythologie").mkdir(parents=True, exist_ok=True)
    (b.FULL / "mythologie").mkdir(parents=True, exist_ok=True)
    (b.THUMBS / "mythologie" / "60.webp").write_bytes(thumb)
    (b.FULL / "mythologie" / f"60.{ext}").write_bytes(data)
    print(f"Hyperion -> full/mythologie/60.{ext}")


def main():
    r = requests.get(URL, headers={"User-Agent": b.UA}, timeout=35)
    r.raise_for_status()
    if not b.verify_image(r.content):
        raise RuntimeError("image Hyperion invalide")
    write(r.content)


if __name__ == "__main__":
    main()
