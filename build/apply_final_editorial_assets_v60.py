#!/usr/bin/env python3
"""Install the last reviewed editorial assets from the visual audit."""
from io import BytesIO
from pathlib import Path
import random

from PIL import Image, ImageDraw

from fix_visual_quality_v60 import image_map, write_replacement


CONVENTION = Path(r"C:\Users\flxjr\.codex\generated_images\019ed745-e849-7581-ac12-d3ecd51088a4\exec-6a1c2173-c4c8-44a8-b788-9fcdd1a43337.png")


def original_action_painting():
    """A new gestural painting, not a reproduction of Pollock's No. 31."""
    width, height = 1800, 1200
    image = Image.new("RGB", (width, height), (24, 23, 20))
    draw = ImageDraw.Draw(image)
    random.seed("memo-v60-original-action-painting")
    colors = [(225, 216, 191), (183, 171, 145), (139, 104, 75), (106, 125, 132), (210, 83, 53), (53, 50, 43)]
    for color in colors:
        for _ in range(115):
            points = []
            x, y = random.uniform(-100, width + 100), random.uniform(-50, height + 50)
            for _ in range(random.randint(3, 9)):
                points.append((x, y))
                x += random.uniform(-240, 240)
                y += random.uniform(-180, 180)
            draw.line(points, fill=color, width=random.randint(2, 11), joint="curve")
            if random.random() < 0.44:
                px, py = points[-1]
                radius = random.randint(4, 18)
                draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=color)
    out = BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


def main():
    mapping = image_map()
    if not CONVENTION.exists():
        raise RuntimeError(f"illustration Convention absente: {CONVENTION}")
    write_replacement(mapping, "chefs_etat", "3", CONVENTION.read_bytes(), "editorial-illustration:National Convention session:1793")
    write_replacement(mapping, "peintres", "43b", original_action_painting(), "local-original-action-painting:abstract expressionism study:not a reproduction")
    print("OK chefs_etat/3 <- National Convention editorial scene")
    print("OK peintres/43b <- original action-painting study")


if __name__ == "__main__":
    main()
