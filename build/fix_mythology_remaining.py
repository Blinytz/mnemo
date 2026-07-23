#!/usr/bin/env python3
from pathlib import Path

import requests

import build_images as b

HADES_URLS = {
    "18": "https://static.wikia.nocookie.net/hades_gamepedia_en/images/4/41/Portraits_Chronos_Battle_01.png/revision/latest?cb=2024",
    "26": "https://static.wikia.nocookie.net/hades_gamepedia_en/images/e/e2/Prometheus_HadesII.png/revision/latest?cb=2024101705503",
    "42": "https://static.wikia.nocookie.net/hades_gamepedia_en/images/3/36/Medusa_Confident.png/revision/latest?cb=20200708160331",
    "43": "https://static.wikia.nocookie.net/hades_gamepedia_en/images/b/b0/Icarus_Olympus.png/revision/latest?cb=20250616041436",
    "45": "https://static.wikia.nocookie.net/hades_gamepedia_en/images/c/c4/Portraits_Narcissus_01.png/revision/latest?cb=202506171",
    "46": "https://static.wikia.nocookie.net/hades_gamepedia_en/images/9/97/Echo_HadesII.png/revision/latest?cb=20241017100304",
    "56": "https://static.wikia.nocookie.net/hades_gamepedia_en/images/2/25/Medea_HadesII.png/revision/latest?cb=20241017061747",
}

WIKI_TARGETS = {
    "24": ("Eros", "en.wikipedia.org"),
    "25": ("Nike (mythology)", "en.wikipedia.org"),
    "27": ("Atlas (mythology)", "en.wikipedia.org"),
    "44": ("Daedalus", "en.wikipedia.org"),
    "49": ("Pandora", "en.wikipedia.org"),
    "51": ("Helios", "en.wikipedia.org"),
    "53": ("Tyche", "en.wikipedia.org"),
    "54": ("Aeolus", "en.wikipedia.org"),
    "60": ("Hyperion (Titan)", "en.wikipedia.org"),
}


def write_raster(row_num: str, data: bytes, source: str):
    thumb = b.to_webp_thumb(data)
    if not thumb:
        raise RuntimeError(f"thumb impossible: mythologie/{row_num}")
    ext = b.raster_ext(data)
    (b.THUMBS / "mythologie").mkdir(parents=True, exist_ok=True)
    (b.FULL / "mythologie").mkdir(parents=True, exist_ok=True)
    (b.THUMBS / "mythologie" / f"{row_num}.webp").write_bytes(thumb)
    (b.FULL / "mythologie" / f"{row_num}.{ext}").write_bytes(data)
    print(f"mythologie/{row_num}: {source} -> full/mythologie/{row_num}.{ext}")


def get_url(url: str) -> bytes:
    r = requests.get(url, headers={"User-Agent": b.UA}, timeout=35, allow_redirects=True)
    r.raise_for_status()
    data = r.content
    if not b.verify_image(data):
        raise RuntimeError(f"image invalide: {url}")
    return data


def write_hades():
    failures = []
    for row_num, url in HADES_URLS.items():
        try:
            write_raster(row_num, get_url(url), "hades-search")
        except Exception as exc:
            failures.append(f"{row_num} {url}: {exc}")
    return failures


def write_wiki():
    failures = []
    for row_num, (title, host) in WIKI_TARGETS.items():
        try:
            hit = b.wiki_batch([title], host=host, thumb_size=1600).get(title)
            if not hit:
                hit = b.wiki_search(title, host=host, thumb_size=1600)
            if not hit:
                raise RuntimeError(f"wiki introuvable: {title}")
            tdata, fdata = b.wiki_download(hit)
            data = fdata or tdata
            if not data:
                raise RuntimeError(f"download impossible: {title}")
            write_raster(row_num, data, f"wiki:{title}")
        except Exception as exc:
            failures.append(f"{row_num} {title}: {exc}")
    return failures


def main():
    b.load_cache()
    failures = write_hades()
    failures.extend(write_wiki())
    b.save_cache()
    report = b.BUILD_DIR / "mythologie_remaining_failures.txt"
    report.write_text("\n".join(failures), encoding="utf-8")
    print(f"failures={len(failures)} report={report}")


if __name__ == "__main__":
    main()
