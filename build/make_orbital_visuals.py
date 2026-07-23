#!/usr/bin/env python3
"""Create high-resolution, subject-specific diagrams for unphotographed moons."""
from io import BytesIO
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from fix_visual_quality_v60 import image_map, write_replacement


TARGETS = [
    # Caliban is an irregular, distant retrograde moon of Uranus. Naïad is a
    # tiny inner moon of Neptune. The graphics make that distinction visible.
    ("42", "Caliban", "Uranus", (92, 206, 226), 7_231_000, True),
    ("44", "Naïade", "Neptune", (74, 118, 240), 48_227, False),
]


def render(name, parent, color, distance, retrograde):
    width, height = 1600, 1000
    image = Image.new("RGB", (width, height), (4, 8, 18))
    draw = ImageDraw.Draw(image)
    random.seed(name)
    for _ in range(360):
        x = random.randrange(width)
        y = random.randrange(height)
        r = random.choice((1, 1, 1, 2))
        tone = random.randrange(85, 180)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(tone, tone + 5, min(255, tone + 35)))

    # The parent planet is placed off-centre so the orbital relation stays
    # legible even in the 160px thumbnail.
    cx, cy = 560, 510
    radius = 180 if parent == "Uranus" else 210
    planet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    planet_draw = ImageDraw.Draw(planet)
    for r in range(radius, 0, -1):
        mix = r / radius
        base = tuple(int(channel * (1 - mix * 0.54)) for channel in color)
        planet_draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=base + (255,))
    planet = planet.filter(ImageFilter.GaussianBlur(0.7))
    image = Image.alpha_composite(image.convert("RGBA"), planet)
    draw = ImageDraw.Draw(image)

    if retrograde:
        orbit = (170, 150, 1490, 860)
        moon_x, moon_y = 1365, 707
        draw.ellipse(orbit, outline=color + (190,), width=7)
        # Broken outer arc signals the irregular, remote orbit.
        for angle in range(16, 330, 30):
            a = math.radians(angle)
            x = (orbit[0] + orbit[2]) / 2 + (orbit[2] - orbit[0]) / 2 * math.cos(a)
            y = (orbit[1] + orbit[3]) / 2 + (orbit[3] - orbit[1]) / 2 * math.sin(a)
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color + (220,))
    else:
        orbit = (290, 340, 845, 680)
        moon_x, moon_y = 824, 550
        draw.ellipse(orbit, outline=color + (220,), width=8)
        # A close inner orbit is intentionally compact around Neptune.
        draw.ellipse((cx - 285, cy - 174, cx + 285, cy + 174), outline=color + (85,), width=2)

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for radius_glow, alpha in ((58, 20), (40, 32), (25, 60), (15, 210)):
        glow_draw.ellipse((moon_x - radius_glow, moon_y - radius_glow, moon_x + radius_glow, moon_y + radius_glow), fill=(240, 245, 255, alpha))
    image = Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(8)))
    draw = ImageDraw.Draw(image)
    draw.ellipse((moon_x - 16, moon_y - 16, moon_x + 16, moon_y + 16), fill=(232, 237, 244))

    # The orbital guide uses only graphic cues; the adjacent app row supplies
    # the textual identity and exact numeric value.
    draw.line((moon_x, moon_y, moon_x - 185, moon_y - 95), fill=(225, 235, 255, 170), width=3)
    draw.ellipse((moon_x - 190, moon_y - 100, moon_x - 180, moon_y - 90), fill=(225, 235, 255, 210))
    out = BytesIO()
    image.convert("RGB").save(out, "PNG", optimize=True)
    return out.getvalue()


def main():
    mapping = image_map()
    for row, name, parent, color, distance, retrograde in TARGETS:
        data = render(name, parent, color, distance, retrograde)
        write_replacement(mapping, "lunes", row, data, f"local-orbital-diagram:{name}:{parent}:{distance}km")
        print(f"OK lunes/{row} <- orbital diagram {name}")


if __name__ == "__main__":
    main()
