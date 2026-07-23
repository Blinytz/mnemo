#!/usr/bin/env python3
"""Genere les cartes SVG de localisation des departements francais.

Les cartes utilisent un GeoJSON reel des departements. Pour la metropole,
le cadre est la France metropolitaine; pour l'outre-mer, le cadre est local
afin que le departement reste lisible au lieu d'etre perdu dans une carte
mondiale.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
DATA = ROOT / "build" / "departements.geojson"
MAP_JSON = ROOT / "build" / "image_files_map.json"
URLS = [
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-avec-outre-mer.geojson",
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson",
    "https://raw.githubusercontent.com/datasets-fr/geojson-code-insee/master/departements.geojson",
]
OVERSEAS_CODES = {"971", "972", "973", "974", "976"}


def ensure_geojson() -> dict:
    if DATA.exists():
        data = json.loads(DATA.read_text(encoding="utf-8"))
        codes = {feature_code(f) for f in data.get("features", [])}
        if OVERSEAS_CODES.issubset(codes):
            return data
    last_error = None
    for url in URLS:
        try:
            r = requests.get(url, timeout=45)
            r.raise_for_status()
            data = r.json()
            DATA.write_text(json.dumps(data), encoding="utf-8")
            return data
        except Exception as exc:  # pragma: no cover - diagnostic path
            last_error = exc
    raise RuntimeError(f"Impossible de telecharger le GeoJSON departements: {last_error}")


def extract_departments() -> list[tuple[int, str, str]]:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
const lists = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
const l = lists.find(x => x.id === 'departements');
const codeIdx = l.columns.indexOf('Numero') >= 0 ? l.columns.indexOf('Numero') : 0;
const nameIdx = l.columns.indexOf('Nom');
console.log(JSON.stringify(l.rows.map((r, i) => [i + 1, r[codeIdx], r[nameIdx]])));
"""
    res = subprocess.run(
        ["node", "-e", js, str(HTML)],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    return [(int(n), str(code), str(name)) for n, code, name in json.loads(res.stdout)]


def feature_code(feature: dict) -> str:
    props = feature.get("properties") or {}
    for key in ("code", "CODE_DEPT", "code_dept", "INSEE_DEP", "dep"):
        val = props.get(key)
        if val is not None:
            return str(val).zfill(2) if str(val).isdigit() and len(str(val)) < 3 else str(val)
    return ""


def feature_name(feature: dict) -> str:
    props = feature.get("properties") or {}
    for key in ("nom", "NOM_DEPT", "nom_dept", "name"):
        if props.get(key):
            return str(props[key])
    return ""


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


def path_for_geom(geom, project) -> str:
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    parts = []
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


def make_projector(features: list[dict], width: int, height: int, pad: int):
    points = [pt for f in features for pt in iter_points(f["geometry"])]
    lon_min, lon_max = min(p[0] for p in points), max(p[0] for p in points)
    lat_min, lat_max = min(p[1] for p in points), max(p[1] for p in points)
    if math.isclose(lon_min, lon_max):
        lon_min -= 0.01
        lon_max += 0.01
    if math.isclose(lat_min, lat_max):
        lat_min -= 0.01
        lat_max += 0.01
    sx = (width - pad * 2) / (lon_max - lon_min)
    sy = (height - pad * 2) / (lat_max - lat_min)
    scale = min(sx, sy)
    xoff = (width - (lon_max - lon_min) * scale) / 2
    yoff = (height - (lat_max - lat_min) * scale) / 2

    def project(lon, lat):
        return xoff + (lon - lon_min) * scale, height - (yoff + (lat - lat_min) * scale)

    return project


def replace_paths_in_html(replacements: dict[str, str]) -> None:
    html = HTML.read_text(encoding="utf-8")
    for old, new in replacements.items():
        html = html.replace(old, new)
    HTML.write_text(html, encoding="utf-8")


def main() -> None:
    geo = ensure_geojson()
    all_features = geo["features"]
    by_code = {feature_code(f): f for f in all_features}
    metro_features = [f for f in all_features if feature_code(f) not in OVERSEAS_CODES]
    width, height = 1200, 900
    metro_project = make_projector(metro_features, width, height, 36)

    thumb_dir = ROOT / "thumbs" / "departements"
    full_dir = ROOT / "full" / "departements"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    full_dir.mkdir(parents=True, exist_ok=True)
    image_map = json.loads(MAP_JSON.read_text(encoding="utf-8")) if MAP_JSON.exists() else {}
    image_map.setdefault("departements", {})
    replacements = {}
    ok = fail = 0

    for num, code, name in extract_departments():
        feature = by_code.get(code)
        if not feature:
            print("FAIL missing geometry", num, code, name)
            fail += 1
            continue
        is_overseas = code in OVERSEAS_CODES
        context = [feature] if is_overseas else metro_features
        project = make_projector(context, width, height, 42) if is_overseas else metro_project
        paths = []
        for f in context:
            selected = feature_code(f) == code
            fill = "#d62828" if selected else "#d8dee8"
            stroke = "#8b97a8" if not selected else "#8a1111"
            sw = "1.1" if not selected else "2.8"
            paths.append(
                f'<path d="{path_for_geom(f["geometry"], project)}" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="{sw}" vector-effect="non-scaling-stroke"/>'
            )
        label = f"Localisation du departement {name}"
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{label}">\n'
            f'<rect width="{width}" height="{height}" fill="#f7fafc"/>\n'
            f'<g>{"".join(paths)}</g>\n'
            f'</svg>\n'
        )
        key = f"{num}b"
        for folder in (thumb_dir, full_dir):
            (folder / f"{key}.svg").write_text(svg, encoding="utf-8")
            for ext in (".webp", ".png", ".jpg", ".jpeg"):
                old = folder / f"{key}{ext}"
                if old.exists():
                    old.unlink()
        image_map["departements"][key] = f"full/departements/{key}.svg"
        replacements[f"thumbs/departements/{key}.webp"] = f"thumbs/departements/{key}.svg"
        replacements[f"full/departements/{key}.webp"] = f"full/departements/{key}.svg"
        replacements[f"full/departements/{key}.png"] = f"full/departements/{key}.svg"
        print("OK", num, code, name)
        ok += 1

    MAP_JSON.write_text(json.dumps(image_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    replace_paths_in_html(replacements)
    print(f"ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
