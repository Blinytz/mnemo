#!/usr/bin/env python3
import build_images as b

TARGETS = {
    "44": ("Daedalus", "en.wikipedia.org"),
    "49": ("Pandora (mythology)", "en.wikipedia.org"),
    "54": ("Aeolus", "en.wikipedia.org"),
    "59": ("Ixion", "en.wikipedia.org"),
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


def main():
    b.load_cache()
    failures = []
    for row_num, (title, host) in TARGETS.items():
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
    b.save_cache()
    (b.BUILD_DIR / "mythologie_classical_failures.txt").write_text("\n".join(failures), encoding="utf-8")
    print(f"failures={len(failures)}")


if __name__ == "__main__":
    main()
