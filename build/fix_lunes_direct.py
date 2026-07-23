#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_images as b

TARGETS = {
    15: ("Elara", "Elara (moon)", "en.wikipedia.org"),
    19: ("Sinopé", "Sinope (moon)", "en.wikipedia.org"),
    50: ("Triton", "Triton (moon)", "en.wikipedia.org"),
    54: ("Nix", "Nix (moon)", "en.wikipedia.org"),
}

def main():
    b.load_cache()
    out_t = b.THUMBS / "lunes"
    out_f = b.FULL / "lunes"
    out_t.mkdir(parents=True, exist_ok=True)
    out_f.mkdir(parents=True, exist_ok=True)
    for row, (label, title, host) in TARGETS.items():
        hit = b.wiki_batch([title], host=host, thumb_size=1600).get(title)
        if not hit:
            raise RuntimeError(f"Aucun hit pour {label}: {title}")
        tdata, fdata = b.wiki_download(hit)
        if not tdata or not fdata:
            raise RuntimeError(f"Téléchargement impossible pour {label}: {hit}")
        thumb = b.to_webp_thumb(tdata)
        if not thumb:
            raise RuntimeError(f"Miniature impossible pour {label}")
        full_ext = b.raster_ext(fdata)
        (out_t / f"{row}.webp").write_bytes(thumb)
        (out_f / f"{row}.{full_ext}").write_bytes(fdata)
        print(f"{row}: {label} -> full/lunes/{row}.{full_ext}")
    b.save_cache()

if __name__ == "__main__":
    main()
