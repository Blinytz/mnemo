#!/usr/bin/env python3
"""Install reviewed editorial illustrations for rare lost/unillustrated films."""
from pathlib import Path

from fix_visual_quality_v60 import image_map, write_replacement


GENERATED = Path(r"C:\Users\flxjr\.codex\generated_images\019ed745-e849-7581-ac12-d3ecd51088a4")
TARGETS = [
    ("15", "exec-b0ea1feb-b755-4598-99a1-cdce1a9b13ba.png", "editorial-illustration:Christ walking on water:1899 silent cinema"),
    ("23", "exec-4f99793a-fd25-41c1-b80c-483a216b76af.png", "editorial-illustration:La Vie d'un joueur:1902 silent cinema"),
    ("27", "exec-65a6fa42-1b2a-4903-9f04-029e10df46eb.png", "editorial-illustration:Le Vol d'un tableau:1903 silent cinema"),
    ("51", "exec-32d2ab98-13dd-423f-8b9e-d33d7a4b2d2a.png", "editorial-illustration:Feat of Clay:1911 silent cinema"),
]


def main():
    mapping = image_map()
    for row, filename, source in TARGETS:
        path = GENERATED / filename
        if not path.exists():
            raise RuntimeError(f"image generee absente: {path}")
        write_replacement(mapping, "films", row, path.read_bytes(), source)
        print(f"OK films/{row} <- {filename}")


if __name__ == "__main__":
    main()
