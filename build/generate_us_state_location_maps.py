#!/usr/bin/env python3
"""Génère les cartes SVG de localisation des États US depuis un GeoJSON réel.

Source attendue: GeoJSON des États américains (polygones lon/lat).
Le rendu est vectoriel: tous les États en gris, l'État ciblé en rouge.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
DATA = ROOT / "build" / "us-states.geojson"
MAP_JSON = ROOT / "build" / "image_files_map.json"
URLS = [
    "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json",
    "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/us-states.json",
]

FR_TO_EN = {
    "Alabama": "Alabama", "Alaska": "Alaska", "Arizona": "Arizona", "Arkansas": "Arkansas",
    "Californie": "California", "Caroline du Nord": "North Carolina", "Caroline du Sud": "South Carolina",
    "Colorado": "Colorado", "Connecticut": "Connecticut", "Dakota du Nord": "North Dakota",
    "Dakota du Sud": "South Dakota", "Delaware": "Delaware", "Floride": "Florida",
    "Géorgie": "Georgia", "Hawaï": "Hawaii", "Idaho": "Idaho", "Illinois": "Illinois",
    "Indiana": "Indiana", "Iowa": "Iowa", "Kansas": "Kansas", "Kentucky": "Kentucky",
    "Louisiane": "Louisiana", "Maine": "Maine", "Maryland": "Maryland", "Massachusetts": "Massachusetts",
    "Michigan": "Michigan", "Minnesota": "Minnesota", "Mississippi": "Mississippi",
    "Missouri": "Missouri", "Montana": "Montana", "Nebraska": "Nebraska", "Nevada": "Nevada",
    "New Hampshire": "New Hampshire", "New Jersey": "New Jersey", "New Mexico": "New Mexico",
    "New York": "New York", "Ohio": "Ohio", "Oklahoma": "Oklahoma", "Oregon": "Oregon",
    "Pennsylvanie": "Pennsylvania", "Rhode Island": "Rhode Island", "Tennessee": "Tennessee",
    "Texas": "Texas", "Utah": "Utah", "Vermont": "Vermont", "Virginie": "Virginia",
    "Virginie-Occidentale": "West Virginia", "Washington": "Washington", "Wisconsin": "Wisconsin",
    "Wyoming": "Wyoming",
}

ALIASES = {
    "District of Columbia": "District of Columbia",
}


def ensure_geojson() -> dict:
    if DATA.exists():
        return json.loads(DATA.read_text(encoding="utf-8"))
    last_error = None
    for url in URLS:
        try:
            r = requests.get(url, timeout=40)
            r.raise_for_status()
            data = r.json()
            DATA.write_text(json.dumps(data), encoding="utf-8")
            return data
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Impossible de télécharger le GeoJSON US: {last_error}")


def extract_states() -> list[tuple[int, str, str]]:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
const lists = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
const l = lists.find(x => x.id === 'etats_usa');
const ci = l.columns.indexOf('État');
console.log(JSON.stringify(l.rows.map((r, i) => [i + 1, r[ci], r[0]])));
"""
    res = subprocess.run(["node", "-e", js, str(HTML)], cwd=ROOT, check=True, text=True, encoding="utf-8", capture_output=True)
    return [(int(n), str(name), str(code)) for n, name, code in json.loads(res.stdout)]


def iter_points(geom):
    typ = geom["type"]
    coords = geom["coordinates"]
    if typ == "Polygon":
        for ring in coords:
            for lon, lat in ring:
                yield lon, lat
    elif typ == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                for lon, lat in ring:
                    yield lon, lat


def feature_name(feature: dict) -> str:
    props = feature.get("properties") or {}
    return props.get("name") or props.get("NAME") or props.get("state") or props.get("STATE_NAME") or ""


def path_for_geom(geom, project) -> str:
    parts = []
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    else:
        polys = geom["coordinates"]
    for poly in polys:
        for ring in poly:
            coords = [project(lon, lat) for lon, lat in ring]
            if not coords:
                continue
            d = [f"M{coords[0][0]:.1f},{coords[0][1]:.1f}"]
            d.extend(f"L{x:.1f},{y:.1f}" for x, y in coords[1:])
            d.append("Z")
            parts.append(" ".join(d))
    return " ".join(parts)


def main() -> None:
    geo = ensure_geojson()
    features = geo["features"]
    by_name = {feature_name(f): f for f in features}
    lower48 = [f for f in features if feature_name(f) not in {"Alaska", "Hawaii"}]
    width, height = 1200, 760
    pad = 34

    def make_project(context):
        points = [pt for f in context for pt in iter_points(f["geometry"])]
        lon_min, lon_max = min(p[0] for p in points), max(p[0] for p in points)
        lat_min, lat_max = min(p[1] for p in points), max(p[1] for p in points)
        sx = (width - pad * 2) / (lon_max - lon_min)
        sy = (height - pad * 2) / (lat_max - lat_min)
        scale = min(sx, sy)
        xoff = (width - (lon_max - lon_min) * scale) / 2
        yoff = (height - (lat_max - lat_min) * scale) / 2

        def project(lon, lat):
            return xoff + (lon - lon_min) * scale, height - (yoff + (lat - lat_min) * scale)

        return project

    lower48_project = make_project(lower48)
    thumb_dir = ROOT / "thumbs" / "etats_usa"
    full_dir = ROOT / "full" / "etats_usa"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    image_map = json.loads(MAP_JSON.read_text(encoding="utf-8")) if MAP_JSON.exists() else {}
    image_map.setdefault("etats_usa", {})
    ok = fail = 0
    for num, fr_name, _code in extract_states():
        en_name = FR_TO_EN[fr_name]
        if en_name not in by_name:
            print("FAIL missing geometry", fr_name, en_name)
            fail += 1
            continue
        context = [by_name[en_name]] if en_name in {"Alaska", "Hawaii"} else lower48
        project = make_project(context) if en_name in {"Alaska", "Hawaii"} else lower48_project
        paths = []
        for f in context:
            name = feature_name(f)
            selected = name == en_name
            fill = "#d62828" if selected else "#d8dee8"
            stroke = "#8b97a8" if not selected else "#8a1111"
            sw = "1.2" if not selected else "2.4"
            paths.append(f'<path d="{path_for_geom(f["geometry"], project)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" vector-effect="non-scaling-stroke"/>')
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Localisation de {en_name} aux États-Unis">
<rect width="{width}" height="{height}" fill="#f7fafc"/>
<g>{''.join(paths)}</g>
</svg>
'''
        key = f"{num}b"
        for folder in (thumb_dir, full_dir):
            (folder / f"{key}.svg").write_text(svg, encoding="utf-8")
            old = folder / f"{key}.webp"
            if old.exists():
                old.unlink()
        image_map["etats_usa"][key] = f"full/etats_usa/{key}.svg"
        print("OK", num, en_name)
        ok += 1
    MAP_JSON.write_text(json.dumps(image_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
