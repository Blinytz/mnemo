#!/usr/bin/env python3
"""Genere des frises SVG vectorielles pour les periodes geologiques."""
from __future__ import annotations

import html
import json
import math
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
MAP_JSON = ROOT / "build" / "image_files_map.json"
LIST_ID = "periodes_geologiques"


def extract_list() -> dict:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
const lists = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
console.log(JSON.stringify(lists.find(x => x.id === 'periodes_geologiques')));
"""
    res = subprocess.run(["node", "-e", js, str(HTML)], cwd=ROOT, check=True, text=True, encoding="utf-8", capture_output=True)
    return json.loads(res.stdout)


def parse_ma(value: str) -> float:
    return float(str(value).replace(" ", "").replace(",", "."))


def x_for_age(age: float, width: int, pad: int) -> float:
    # Non-linear scale: old Precambrian remains visible, recent Phanerozoic not crushed.
    max_age = 4600.0
    t = 1.0 - math.sqrt(max(0.0, min(max_age, age)) / max_age)
    return pad + t * (width - pad * 2)


def color_for_eon(eon: str) -> str:
    return {
        "Hadéen": "#586f7c",
        "Archéen": "#8e6c88",
        "Protérozoïque": "#2f7d6d",
        "Phanérozoïque": "#b06c2f",
    }.get(eon, "#667085")


def svg_for(row: list[str], rows: list[list[str]], cols: list[str]) -> str:
    idx = {name: cols.index(name) for name in cols}
    width, height = 1400, 820
    pad = 86
    track_y = 365
    track_h = 118
    eon = row[idx["Éon"]]
    era = row[idx["Ère"]]
    period = row[idx["Période"]]
    start = parse_ma(row[idx["Début (Ma)"]])
    end = parse_ma(row[idx["Fin (Ma)"]])
    events = row[idx["Événements clés"]]

    bands = []
    for other in rows:
        o_start = parse_ma(other[idx["Début (Ma)"]])
        o_end = parse_ma(other[idx["Fin (Ma)"]])
        x1 = x_for_age(o_start, width, pad)
        x2 = x_for_age(o_end, width, pad)
        fill = color_for_eon(other[idx["Éon"]])
        opacity = "0.95" if other is row else "0.30"
        stroke = "#111827" if other is row else "#ffffff"
        sw = "4" if other is row else "1.2"
        bands.append(
            f'<rect x="{min(x1, x2):.1f}" y="{track_y}" width="{abs(x2-x1):.1f}" '
            f'height="{track_h}" rx="10" fill="{fill}" opacity="{opacity}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )

    ticks = []
    for age in [4600, 4000, 3000, 2500, 1600, 1000, 541, 252, 66, 0]:
        x = x_for_age(age, width, pad)
        label = "0" if age == 0 else f"{age:g}"
        ticks.append(f'<line x1="{x:.1f}" y1="{track_y+track_h+8}" x2="{x:.1f}" y2="{track_y+track_h+30}" stroke="#344054" stroke-width="2"/>')
        ticks.append(f'<text x="{x:.1f}" y="{track_y+track_h+58}" text-anchor="middle" font-size="24" fill="#344054">{label}</text>')

    x_start = x_for_age(start, width, pad)
    x_end = x_for_age(end, width, pad)
    mid = (x_start + x_end) / 2
    safe_period = html.escape(period)
    safe_era = html.escape(era)
    safe_eon = html.escape(eon)
    safe_events = html.escape(events)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{safe_period}">
<rect width="{width}" height="{height}" fill="#f8fafc"/>
<text x="{pad}" y="95" font-family="Inter, Arial, sans-serif" font-size="56" font-weight="800" fill="#101828">{safe_period}</text>
<text x="{pad}" y="148" font-family="Inter, Arial, sans-serif" font-size="30" fill="#475467">{safe_eon} · {safe_era} · {start:g} à {end:g} Ma</text>
<rect x="{pad}" y="188" width="{width - pad * 2}" height="108" rx="18" fill="#ffffff" stroke="#d0d5dd"/>
<text x="{pad + 32}" y="232" font-family="Inter, Arial, sans-serif" font-size="25" font-weight="700" fill="#344054">Repère</text>
<text x="{pad + 32}" y="272" font-family="Inter, Arial, sans-serif" font-size="25" fill="#344054">{safe_events}</text>
<text x="{pad}" y="{track_y - 34}" font-family="Inter, Arial, sans-serif" font-size="28" font-weight="700" fill="#344054">Temps géologique, de la formation de la Terre au présent</text>
<g>{''.join(bands)}</g>
<line x1="{pad}" y1="{track_y + track_h + 8}" x2="{width - pad}" y2="{track_y + track_h + 8}" stroke="#344054" stroke-width="3"/>
<g>{''.join(ticks)}</g>
<text x="{mid:.1f}" y="{track_y - 22}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="30" font-weight="800" fill="#101828">{safe_period}</text>
<path d="M{mid:.1f},{track_y - 8} L{mid - 16:.1f},{track_y - 32} L{mid + 16:.1f},{track_y - 32} Z" fill="#101828"/>
<text x="{pad}" y="700" font-family="Inter, Arial, sans-serif" font-size="23" fill="#667085">Échelle non linéaire pour rendre lisibles les périodes récentes.</text>
<text x="{width - pad}" y="700" text-anchor="end" font-family="Inter, Arial, sans-serif" font-size="23" fill="#667085">Ma = millions d'années</text>
</svg>
'''


def replace_html_paths(count: int) -> None:
    text = HTML.read_text(encoding="utf-8")
    for i in range(1, count + 1):
        text = text.replace(f"thumbs/{LIST_ID}/{i}.webp", f"thumbs/{LIST_ID}/{i}.svg")
        text = text.replace(f"full/{LIST_ID}/{i}.webp", f"full/{LIST_ID}/{i}.svg")
        text = text.replace(f"full/{LIST_ID}/{i}.jpg", f"full/{LIST_ID}/{i}.svg")
        text = text.replace(f"full/{LIST_ID}/{i}.png", f"full/{LIST_ID}/{i}.svg")
    HTML.write_text(text, encoding="utf-8")


def main() -> None:
    lst = extract_list()
    cols = lst["columns"]
    rows = lst["rows"]
    thumb_dir = ROOT / "thumbs" / LIST_ID
    full_dir = ROOT / "full" / LIST_ID
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    image_map = json.loads(MAP_JSON.read_text(encoding="utf-8")) if MAP_JSON.exists() else {}
    image_map.setdefault(LIST_ID, {})
    for i, row in enumerate(rows, 1):
        svg = svg_for(row, rows, cols)
        for folder in (thumb_dir, full_dir):
            (folder / f"{i}.svg").write_text(svg, encoding="utf-8")
            for ext in (".webp", ".jpg", ".jpeg", ".png"):
                old = folder / f"{i}{ext}"
                if old.exists():
                    old.unlink()
        image_map[LIST_ID][str(i)] = f"full/{LIST_ID}/{i}.svg"
        print("OK", i, row[cols.index("Période")])
    MAP_JSON.write_text(json.dumps(image_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    replace_html_paths(len(rows))


if __name__ == "__main__":
    main()
