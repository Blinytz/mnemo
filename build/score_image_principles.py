#!/usr/bin/env python3
"""Create a persistent 4-principle scorecard for every image cell in memo.html.

Scores are 1..5 for:
- pertinence: exact subject match
- coherence: thumbnail/full same subject and framing
- homogeneity: visual style matches the list
- quality: resolution/format/compression

This is deliberately conservative. Semantic relevance cannot be proven from
dimensions alone, so the output keeps confidence and review_required fields.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
OUT_JSON = ROOT / "build" / "image_principle_scores.json"
OUT_CSV = ROOT / "build" / "image_principle_scores.csv"
OUT_SUMMARY = ROOT / "build" / "image_principle_scores_summary.json"


TRUSTED_HIGH = {
    "pays",
    "etats_usa",
    "departements",
    "elements",
    "periodes_geologiques",
}

TRUSTED_MEDIUM = {
    "chefs_etat",
    "philosophes",
    "rois_france",
    "f1_champions",
    "peintres",
    "films",
    "consoles",
    "lunes",
    "mythologie",
}

LOW_CONFIDENCE_LISTS = {
    "batailles_decisives",
    "grandes_explorations",
    "revolutions",
    "mers_oceans",
    "detroits_monde",
    "parcs_nationaux",
    "architectes_majeurs",
    "musees_monde",
    "inventions_majeures",
    "decouvertes_scientifiques",
    "civilisations",
    "fleuves_monde",
    "compositeurs",
    "constellations",
    "grands_scientifiques",
}

STYLE_BY_LIST = {
    "pays": "flag",
    "etats_usa": "flag_or_map",
    "departements": "emblem_or_map",
    "chefs_etat": "portrait_or_institution",
    "philosophes": "portrait",
    "rois_france": "portrait",
    "f1_champions": "portrait",
    "peintres": "portrait_or_artwork",
    "films": "poster",
    "consoles": "product",
    "lunes": "astronomy",
    "mythologie": "character_art",
    "os": "anatomy",
    "periodes_geologiques": "diagram",
    "batailles_decisives": "battle_scene_or_map",
    "guerres": "battle_scene_or_map",
    "constellations": "star_map",
    "fleuves_monde": "map",
    "mers_oceans": "map",
    "detroits_monde": "map",
    "montagnes_monde": "landscape_or_map",
    "parcs_nationaux": "landscape",
}


def run_node_json(js: str) -> Any:
    res = subprocess.run(
        ["node", "-e", js, str(HTML)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(res.stdout)


def extract_lists() -> list[dict[str, Any]]:
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
if (start < 0 || end < 0 || end <= start) throw new Error('DEFAULT_LISTS block introuvable');
const data = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
console.log(JSON.stringify(data));
"""
    return run_node_json(js)


def extract_full_map() -> dict[str, dict[str, str]]:
    html = HTML.read_text(encoding="utf-8")
    m = re.search(r"const IMAGE_FILES_MAP = (\{[\s\S]*?\});\s*function localFullImageForThumb", html)
    if not m:
        return {}
    return json.loads(m.group(1))


def is_image_col(name: str) -> bool:
    norm = name.lower()
    return any(token in norm for token in ("image", "drapeau", "localisation", "logo", "photo", "portrait"))


def image_key(row_index: int, col_index: int) -> str:
    return str(row_index + 1) if col_index == 1 else f"{row_index + 1}b"


def label_for(row: list[Any], columns: list[str], image_ci: int) -> str:
    parts = []
    for idx, value in enumerate(row):
        if idx == image_ci:
            continue
        col = columns[idx] if idx < len(columns) else ""
        if col and str(col).lower() in {"numéro", "numero"}:
            continue
        if value:
            parts.append(str(value))
        if len(parts) >= 4:
            break
    return " / ".join(parts)


def phash(path: Path) -> str:
    with Image.open(path) as im:
        small = im.convert("RGB").resize((8, 8), Image.Resampling.LANCZOS).convert("L")
        pix = list(small.getdata())
    avg = sum(pix) / len(pix)
    return "".join("1" if p >= avg else "0" for p in pix)


def image_info(src: str) -> dict[str, Any]:
    if src.startswith("data:image/"):
        return {
            "exists": True,
            "kind": "data",
            "ext": "data",
            "bytes": len(src),
            "width": "",
            "height": "",
            "long": "",
            "short": "",
            "aspect": "",
            "hash": "",
        }
    path = ROOT / src
    if not src or not path.exists():
        return {"exists": False, "kind": "missing", "ext": Path(src).suffix.lower()}
    ext = path.suffix.lower().lstrip(".")
    if ext == "svg":
        text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
        vb = re.search(r"viewBox=['\"]([^'\"]+)['\"]", text)
        wh = re.search(r"<svg[^>]*\bwidth=['\"]([0-9.]+)[^'\"]*['\"][^>]*\bheight=['\"]([0-9.]+)", text)
        width = height = ""
        if vb:
            nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", vb.group(1))]
            if len(nums) >= 4:
                width, height = int(nums[2]), int(nums[3])
        elif wh:
            width, height = int(float(wh.group(1))), int(float(wh.group(2)))
        return {
            "exists": True,
            "kind": "svg",
            "ext": ext,
            "bytes": path.stat().st_size,
            "width": width,
            "height": height,
            "long": max(width, height) if width and height else "",
            "short": min(width, height) if width and height else "",
            "aspect": round(width / height, 3) if width and height else "",
            "hash": "",
        }
    try:
        with Image.open(path) as im:
            width, height = im.size
            stat = ImageStat.Stat(im.convert("RGB").resize((24, 24), Image.Resampling.LANCZOS))
        return {
            "exists": True,
            "kind": "raster",
            "ext": ext,
            "bytes": path.stat().st_size,
            "width": width,
            "height": height,
            "long": max(width, height),
            "short": min(width, height),
            "aspect": round(width / height, 3),
            "hash": phash(path),
            "mean_rgb": [round(v, 1) for v in stat.mean],
        }
    except Exception as exc:
        return {"exists": True, "kind": "broken", "ext": ext, "bytes": path.stat().st_size, "error": str(exc)}


def hamming(a: str, b: str) -> int | None:
    if not a or not b or len(a) != len(b):
        return None
    return sum(x != y for x, y in zip(a, b))


def quality_score(info: dict[str, Any], is_thumb: bool = False) -> tuple[int, list[str]]:
    notes: list[str] = []
    if not info.get("exists") or info.get("kind") == "broken":
        return 1, ["fichier absent ou illisible"]
    if info.get("kind") in {"svg", "data"}:
        return 5, ["vectoriel ou data-uri stable"]
    long = int(info.get("long") or 0)
    short = int(info.get("short") or 0)
    size = int(info.get("bytes") or 0)
    if is_thumb:
        if long >= 180 and short >= 90:
            return 5, ["miniature suffisante"]
        if long >= 140 and short >= 70:
            return 4, ["miniature correcte"]
        return 2, ["miniature petite"]
    if long >= 1800 and short >= 900 and size >= 100_000:
        return 5, ["HD solide"]
    if long >= 1200 and short >= 650 and size >= 45_000:
        return 4, ["HD acceptable"]
    if long >= 900 and short >= 500:
        notes.append("résolution moyenne")
        return 3, notes
    if long >= 600 and short >= 350:
        notes.append("résolution faible")
        return 2, notes
    return 1, ["résolution très faible"]


def coherence_score(thumb: dict[str, Any], full: dict[str, Any], thumb_src: str, full_src: str) -> tuple[int, list[str]]:
    if not thumb.get("exists") or not full.get("exists"):
        return 1, ["miniature ou full absent"]
    if thumb_src.startswith("data:image/") and not full_src:
        return 5, ["image unique data-uri"]
    if Path(thumb_src).stem == Path(full_src).stem and Path(thumb_src).parent.name == Path(full_src).parent.name:
        if thumb.get("kind") == "svg" or full.get("kind") == "svg":
            return 5, ["même identifiant vectoriel"]
        dist = hamming(str(thumb.get("hash") or ""), str(full.get("hash") or ""))
        if dist is None:
            return 4, ["même identifiant fichier"]
        if dist <= 12:
            return 5, [f"même cadrage probable, hash distance {dist}"]
        if dist <= 22:
            return 4, [f"même sujet probable, hash distance {dist}"]
        if dist <= 30:
            return 3, [f"cadrage possiblement différent, hash distance {dist}"]
        return 2, [f"incohérence visuelle possible, hash distance {dist}"]
    return 2, ["identifiant miniature/full différent"]


def pertinence_score(list_id: str, column: str, label: str, thumb_src: str, full_src: str) -> tuple[int, str, bool, list[str]]:
    notes: list[str] = []
    review_required = True
    confidence = "low"
    score = 3

    if list_id in TRUSTED_HIGH:
        score, confidence, review_required = 5, "high", False
        notes.append("source déterministe ou carte/drapeau local attendu")
    elif list_id in TRUSTED_MEDIUM:
        score, confidence, review_required = 4, "medium", True
        notes.append("source ciblée, revue sémantique ponctuelle recommandée")
    elif list_id in LOW_CONFIDENCE_LISTS:
        score, confidence, review_required = 2, "low", True
        notes.append("liste récemment enrichie par recherche, revue sémantique nécessaire")

    col_norm = column.lower()
    if "localisation" in col_norm or "drapeau" in col_norm:
        score = max(score, 4)
        notes.append("colonne à sujet visuel contraint")
    if not thumb_src or (not full_src and not thumb_src.startswith("data:image/")):
        return 1, "high", True, ["image absente"]
    if "placeholder" in thumb_src.lower() or "placeholder" in full_src.lower():
        return 1, "high", True, ["placeholder détecté"]
    if label:
        notes.append("libellé audité: " + label[:120])
    return score, confidence, review_required, notes


def homogeneity_score(
    list_id: str,
    column: str,
    info: dict[str, Any],
    dominant_kind: str,
    dominant_ext: str,
    dominant_aspect_bucket: str,
) -> tuple[int, list[str]]:
    if not info.get("exists"):
        return 1, ["fichier absent"]
    style = STYLE_BY_LIST.get(list_id, "mixed")
    notes = [f"style attendu: {style}"]
    score = 4
    kind = str(info.get("kind") or "")
    ext = str(info.get("ext") or "")
    aspect = float(info.get("aspect") or 0)
    bucket = aspect_bucket(aspect)

    if kind == dominant_kind:
        score += 1
    else:
        notes.append(f"type différent du dominant: {kind} vs {dominant_kind}")
        score -= 1
    if ext != dominant_ext and dominant_ext:
        notes.append(f"extension différente du dominant: {ext} vs {dominant_ext}")
        score -= 1
    if bucket != dominant_aspect_bucket and dominant_aspect_bucket != "unknown":
        notes.append(f"ratio différent du dominant: {bucket} vs {dominant_aspect_bucket}")
        score -= 1

    col = column.lower()
    if list_id in {"pays", "etats_usa"} and ("image" in col or "drapeau" in col) and kind == "svg":
        score = 5
    if "localisation" in col and kind == "svg":
        score = 5
    if list_id == "films" and aspect and aspect < 1:
        score = max(score, 4)
    return max(1, min(5, score)), notes


def aspect_bucket(aspect: float) -> str:
    if not aspect:
        return "unknown"
    if aspect < 0.75:
        return "portrait"
    if aspect > 1.35:
        return "landscape"
    return "squareish"


def main() -> None:
    lists = extract_lists()
    full_map = extract_full_map()

    raw_entries: list[dict[str, Any]] = []
    full_infos_by_list: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for lst in lists:
        list_id = lst["id"]
        columns = list(map(str, lst.get("columns") or []))
        image_cols = [i for i, c in enumerate(columns) if is_image_col(c)]
        for ri, row in enumerate(lst.get("rows") or []):
            for ci in image_cols:
                thumb_src = str(row[ci] if ci < len(row) else "").strip()
                if not thumb_src:
                    continue
                key = image_key(ri, ci)
                full_src = (full_map.get(list_id) or {}).get(key, "")
                if not full_src and thumb_src.startswith("thumbs/"):
                    candidates = sorted((ROOT / "full" / list_id).glob(f"{Path(thumb_src).stem}.*"))
                    if candidates:
                        full_src = candidates[0].relative_to(ROOT).as_posix()
                thumb_info = image_info(thumb_src)
                full_info = image_info(full_src) if full_src else image_info(thumb_src)
                full_infos_by_list[list_id].append(full_info)
                raw_entries.append({
                    "list_id": list_id,
                    "list_name": lst.get("name", ""),
                    "row_index": ri + 1,
                    "row_number": str(row[0] if row else ri + 1),
                    "column": columns[ci] if ci < len(columns) else "",
                    "key": key,
                    "label": label_for(row, columns, ci),
                    "thumb": thumb_src,
                    "full": full_src,
                    "thumb_info": thumb_info,
                    "full_info": full_info,
                })

    list_dominants: dict[str, dict[str, str]] = {}
    for list_id, infos in full_infos_by_list.items():
        kinds = Counter(str(i.get("kind") or "") for i in infos if i.get("exists"))
        exts = Counter(str(i.get("ext") or "") for i in infos if i.get("exists"))
        aspects = Counter(aspect_bucket(float(i.get("aspect") or 0)) for i in infos if i.get("exists"))
        list_dominants[list_id] = {
            "kind": kinds.most_common(1)[0][0] if kinds else "",
            "ext": exts.most_common(1)[0][0] if exts else "",
            "aspect_bucket": aspects.most_common(1)[0][0] if aspects else "unknown",
        }

    scored: list[dict[str, Any]] = []
    summary = {
        "generated_for": "memo.html",
        "principles": ["pertinence", "coherence", "homogeneity", "quality"],
        "scale": "1=très mauvais, 5=excellent",
        "total_images": 0,
        "by_list": {},
        "review_required": 0,
    }

    for entry in raw_entries:
        dom = list_dominants.get(entry["list_id"], {})
        p_score, p_conf, p_review, p_notes = pertinence_score(
            entry["list_id"], entry["column"], entry["label"], entry["thumb"], entry["full"]
        )
        c_score, c_notes = coherence_score(entry["thumb_info"], entry["full_info"], entry["thumb"], entry["full"])
        h_score, h_notes = homogeneity_score(
            entry["list_id"],
            entry["column"],
            entry["full_info"],
            dom.get("kind", ""),
            dom.get("ext", ""),
            dom.get("aspect_bucket", "unknown"),
        )
        q_score, q_notes = quality_score(entry["full_info"], is_thumb=False)
        review_required = p_review or min(p_score, c_score, h_score, q_score) <= 3
        total = round((p_score + c_score + h_score + q_score) / 4, 2)

        scored_entry = {
            "list_id": entry["list_id"],
            "list_name": entry["list_name"],
            "row_index": entry["row_index"],
            "row_number": entry["row_number"],
            "column": entry["column"],
            "key": entry["key"],
            "label": entry["label"],
            "thumb": entry["thumb"],
            "full": entry["full"],
            "scores": {
                "pertinence": p_score,
                "coherence": c_score,
                "homogeneity": h_score,
                "quality": q_score,
                "average": total,
            },
            "confidence": {
                "pertinence": p_conf,
                "coherence": "medium" if c_score >= 4 else "high",
                "homogeneity": "medium",
                "quality": "high",
            },
            "review_required": review_required,
            "notes": {
                "pertinence": p_notes,
                "coherence": c_notes,
                "homogeneity": h_notes,
                "quality": q_notes,
            },
            "image_info": {
                "thumb": entry["thumb_info"],
                "full": entry["full_info"],
            },
        }
        scored.append(scored_entry)

        summary["total_images"] += 1
        if review_required:
            summary["review_required"] += 1
        by = summary["by_list"].setdefault(entry["list_id"], {
            "total": 0,
            "review_required": 0,
            "avg_pertinence": 0.0,
            "avg_coherence": 0.0,
            "avg_homogeneity": 0.0,
            "avg_quality": 0.0,
        })
        by["total"] += 1
        if review_required:
            by["review_required"] += 1
        for k in ("pertinence", "coherence", "homogeneity", "quality"):
            by[f"avg_{k}"] += scored_entry["scores"][k]

    for by in summary["by_list"].values():
        total = max(1, int(by["total"]))
        for k in ("pertinence", "coherence", "homogeneity", "quality"):
            by[f"avg_{k}"] = round(float(by[f"avg_{k}"]) / total, 2)

    scored.sort(key=lambda e: (e["list_id"], e["row_index"], e["column"]))
    OUT_JSON.write_text(json.dumps(scored, ensure_ascii=False, indent=2), encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "list_id", "list_name", "row_index", "row_number", "column", "key", "label",
            "thumb", "full", "pertinence", "coherence", "homogeneity", "quality",
            "average", "review_required", "pertinence_confidence",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in scored:
            writer.writerow({
                "list_id": e["list_id"],
                "list_name": e["list_name"],
                "row_index": e["row_index"],
                "row_number": e["row_number"],
                "column": e["column"],
                "key": e["key"],
                "label": e["label"],
                "thumb": e["thumb"],
                "full": e["full"],
                "pertinence": e["scores"]["pertinence"],
                "coherence": e["scores"]["coherence"],
                "homogeneity": e["scores"]["homogeneity"],
                "quality": e["scores"]["quality"],
                "average": e["scores"]["average"],
                "review_required": e["review_required"],
                "pertinence_confidence": e["confidence"]["pertinence"],
            })

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "json": str(OUT_JSON.relative_to(ROOT)),
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "summary": str(OUT_SUMMARY.relative_to(ROOT)),
        "total_images": summary["total_images"],
        "review_required": summary["review_required"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
