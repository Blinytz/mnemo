#!/usr/bin/env python3
from pathlib import Path

REPO = Path(__file__).parent.parent

COPIES = [
    # Main/pied : utiliser les schémas de groupe déjà corrigés pour les sous-os proches.
    ("os", "71", ["72", "74", "75"]),
    ("os", "107", ["106", "108"]),
    ("os", "110", ["77", "79", "80", "83", "85", "86", "89", "112", "115", "116", "118", "121", "122"]),
]


def copy_pair(lid, src, dst):
    thumbs = REPO / "thumbs" / lid
    full = REPO / "full" / lid
    st = thumbs / f"{src}.webp"
    if st.exists():
        (thumbs / f"{dst}.webp").write_bytes(st.read_bytes())
    for ext in ("jpg", "png", "webp", "svg"):
        sf = full / f"{src}.{ext}"
        if sf.exists():
            (full / f"{dst}.{ext}").write_bytes(sf.read_bytes())
            print(f"{lid}/{dst}: copied {src}.{ext}")
            return
    print(f"missing source {lid}/{src}")


def main():
    for lid, src, dsts in COPIES:
        for dst in dsts:
            copy_pair(lid, src, dst)


if __name__ == "__main__":
    main()
