#!/usr/bin/env python3
"""Rebuild constellation images from open astronomical line/star data.

Source data:
- d3-celestial constellations.lines.json
- d3-celestial stars.6.json

The output is intentionally pedagogical: a clean dark chart with the target
constellation highlighted, nearby stars kept subdued, and thumbnails generated
from the exact same full image.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent.parent
FULL = ROOT / "full" / "constellations"
THUMBS = ROOT / "thumbs" / "constellations"
MAP_JSON = ROOT / "build" / "image_files_map.json"
HTML = ROOT / "memo.html"
SW = ROOT / "sw.js"

UA = {"User-Agent": "memo-app personal constellation rebuild"}
LINES_URL = "https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/constellations.lines.json"
STARS_URL = "https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/stars.6.json"

ROWS = [
    ("Orion", "Ori"),
    ("Grande Ourse", "UMa"),
    ("Petite Ourse", "UMi"),
    ("Cassiopée", "Cas"),
    ("Cygne", "Cyg"),
    ("Lyre", "Lyr"),
    ("Aigle", "Aql"),
    ("Scorpion", "Sco"),
    ("Sagittaire", "Sgr"),
    ("Taureau", "Tau"),
    ("Gémeaux", "Gem"),
    ("Lion", "Leo"),
    ("Persée", "Per"),
    ("Andromède", "And"),
    ("Hercule", "Her"),
    ("Vierge", "Vir"),
    ("Balance", "Lib"),
    ("Verseau", "Aqr"),
    ("Bélier", "Ari"),
    ("Cancer", "Cnc"),
    ("Capricorne", "Cap"),
    ("Poissons", "Psc"),
    ("Centaure", "Cen"),
    ("Croix du Sud", "Cru"),
    ("Dragon", "Dra"),
    ("Pégase", "Peg"),
    ("Grand Chien", "CMa"),
    ("Petit Chien", "CMi"),
    ("Cocher", "Aur"),
    ("Bouvier", "Boo"),
    ("Couronne boréale", "CrB"),
    ("Ophiuchus", "Oph"),
    ("Hydre", "Hya"),
    ("Éridan", "Eri"),
    ("Corbeau", "Crv"),
    ("Lièvre", "Lep"),
    ("Phénix", "Phe"),
    ("Serpent", "Ser"),
]


def load_json(url: str) -> dict:
    cache = ROOT / "build" / ("source_" + url.rsplit("/", 1)[-1])
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    data = requests.get(url, timeout=30, headers=UA).json()
    cache.write_text(json.dumps(data), encoding="utf-8")
    return data


def unwrap_ra(value: float, center: float) -> float:
    while value - center > 180:
        value -= 360
    while value - center < -180:
        value += 360
    return value


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            pass
    return ImageFont.load_default()


def flatten_lines(feature: dict) -> list[list[tuple[float, float]]]:
    return [[tuple(p) for p in line] for line in feature["geometry"]["coordinates"]]


def chart_bounds(lines: list[list[tuple[float, float]]]) -> tuple[float, float, float, float, float]:
    points = [p for line in lines for p in line]
    raw_center = sum(p[0] for p in points) / len(points)
    xs = [unwrap_ra(p[0], raw_center) for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x
    height = max_y - min_y
    pad_x = max(6.0, width * 0.35)
    pad_y = max(5.0, height * 0.35)
    return min_x - pad_x, max_x + pad_x, min_y - pad_y, max_y + pad_y, raw_center


def render_chart(name: str, abbr: str, lines_feature: dict, stars: list[dict], out: Path) -> None:
    W, H = 1600, 1000
    plot = (110, 90, W - 110, H - 170)
    lines = flatten_lines(lines_feature)
    min_x, max_x, min_y, max_y, center = chart_bounds(lines)

    # Keep the constellation shape comfortable even for very wide/flat figures.
    span_x = max_x - min_x
    span_y = max_y - min_y
    target_ratio = (plot[2] - plot[0]) / (plot[3] - plot[1])
    if span_x / max(span_y, 0.001) > target_ratio:
        need_y = span_x / target_ratio
        mid = (min_y + max_y) / 2
        min_y, max_y = mid - need_y / 2, mid + need_y / 2
    else:
        need_x = span_y * target_ratio
        mid = (min_x + max_x) / 2
        min_x, max_x = mid - need_x / 2, mid + need_x / 2

    def xy(ra: float, dec: float) -> tuple[float, float]:
        x = unwrap_ra(ra, center)
        px = plot[0] + (x - min_x) / (max_x - min_x) * (plot[2] - plot[0])
        py = plot[3] - (dec - min_y) / (max_y - min_y) * (plot[3] - plot[1])
        return px, py

    img = Image.new("RGB", (W, H), "#07111f")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    gdraw = ImageDraw.Draw(glow)

    # Subtle grid, useful for orientation without clutter.
    for t in range(1, 5):
        x = plot[0] + t * (plot[2] - plot[0]) / 5
        y = plot[1] + t * (plot[3] - plot[1]) / 5
        draw.line([(x, plot[1]), (x, plot[3])], fill="#13263c", width=1)
        draw.line([(plot[0], y), (plot[2], y)], fill="#13263c", width=1)

    target_points = {(round(unwrap_ra(ra, center), 4), round(dec, 4)) for line in lines for ra, dec in line}

    for star in stars:
        ra, dec = star["geometry"]["coordinates"]
        x = unwrap_ra(ra, center)
        if not (min_x <= x <= max_x and min_y <= dec <= max_y):
            continue
        mag = float(star["properties"].get("mag", 6.0))
        if mag > 6.2:
            continue
        px, py = xy(ra, dec)
        if px < plot[0] or px > plot[2] or py < plot[1] or py > plot[3]:
            continue
        radius = max(1.2, 5.8 - mag * 0.75)
        color = "#dbeafe" if mag < 3.5 else "#8fa8c6"
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=color)

    for line in lines:
        pts = [xy(ra, dec) for ra, dec in line]
        if len(pts) >= 2:
            gdraw.line(pts, fill=(125, 211, 252, 130), width=18, joint="curve")
            draw.line(pts, fill="#67e8f9", width=7, joint="curve")

    img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(12)))
    draw = ImageDraw.Draw(img)
    for line in lines:
        pts = [xy(ra, dec) for ra, dec in line]
        if len(pts) >= 2:
            draw.line(pts, fill="#7dd3fc", width=7, joint="curve")
        for ra, dec in line:
            px, py = xy(ra, dec)
            key = (round(unwrap_ra(ra, center), 4), round(dec, 4))
            r = 10 if key in target_points else 8
            draw.ellipse((px - r, py - r, px + r, py + r), fill="#fff7cc", outline="#fbbf24", width=3)

    draw.rectangle((0, H - 118, W, H), fill="#0b1626")
    draw.text((W / 2, H - 86), name, font=font(42, bold=True), fill="#f8fafc", anchor="mm")
    draw.text((W / 2, H - 38), f"Tracé officiel {abbr} - données d3-celestial / catalogue étoiles mag <= 6",
              font=font(21), fill="#9fb3c8", anchor="mm")
    draw.rectangle(plot, outline="#1d3654", width=2)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG", optimize=True)


def make_thumb(full: Path, thumb: Path) -> None:
    with Image.open(full) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((220, 160), Image.Resampling.LANCZOS)
        thumb.parent.mkdir(parents=True, exist_ok=True)
        im.save(thumb, "WEBP", quality=84, method=6)


def update_app_mapping() -> None:
    data = json.loads(MAP_JSON.read_text(encoding="utf-8").lstrip("\ufeff")) if MAP_JSON.exists() else {}
    data.setdefault("constellations", {})
    for i in range(1, len(ROWS) + 1):
        data["constellations"][str(i)] = f"full/constellations/{i}.png"
    MAP_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = HTML.read_text(encoding="utf-8")
    html = re.sub(r"const IMAGE_FILES_MAP = \{[\s\S]*?\};\s*function localFullImageForThumb",
                  f"const IMAGE_FILES_MAP = {payload};\nfunction localFullImageForThumb", html, count=1)
    html = re.sub(r"const FORCE_DEFAULT_REFRESH_VERSION = \d+;", "const FORCE_DEFAULT_REFRESH_VERSION = 85;", html)
    html = re.sub(r"const APP_DATA_VERSION = \d+;", "const APP_DATA_VERSION = 85;", html)
    HTML.write_text(html, encoding="utf-8", newline="")

    sw = SW.read_text(encoding="utf-8")
    sw = re.sub(r"memo-v\d+", "memo-v85", sw)
    SW.write_text(sw, encoding="utf-8", newline="")


def main() -> None:
    lines_data = load_json(LINES_URL)
    stars_data = load_json(STARS_URL)
    line_features = {f["id"]: f for f in lines_data["features"]}
    stars = stars_data["features"]

    missing = [abbr for _, abbr in ROWS if abbr not in line_features]
    if missing:
        raise SystemExit(f"Constellations absentes de la source: {missing}")

    built = []
    for idx, (name, abbr) in enumerate(ROWS, 1):
        full = FULL / f"{idx}.png"
        thumb = THUMBS / f"{idx}.webp"
        render_chart(name, abbr, line_features[abbr], stars, full)
        make_thumb(full, thumb)
        built.append({"row": idx, "name": name, "abbr": abbr, "full": full.relative_to(ROOT).as_posix(), "thumb": thumb.relative_to(ROOT).as_posix()})

    update_app_mapping()
    report = {
        "source": {
            "lines": LINES_URL,
            "stars": STARS_URL,
        },
        "version": 85,
        "built": built,
    }
    (ROOT / "build" / "constellations_clean_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"built": len(built), "version": 85, "missing": 0}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
