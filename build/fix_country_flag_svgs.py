#!/usr/bin/env python3
"""Remplace les quelques drapeaux pays restés en WebP par des SVG FlagCDN."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "memo.html"
MAP_JSON = ROOT / "build" / "image_files_map.json"


def extract_pays():
    js = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('const DEFAULT_LISTS =');
const end = html.indexOf('const APP_DATA_VERSION');
const lists = new Function(html.slice(start, end) + '\nreturn DEFAULT_LISTS;')();
const l = lists.find(x => x.id === 'pays');
const ci = l.columns.indexOf('Pays');
console.log(JSON.stringify({rows:l.rows.map((r,i)=>[i+1,r[ci],r[1]]), map:l.flagCodeMap || {}}));
"""
    res = subprocess.run(["node", "-e", js, str(HTML)], cwd=ROOT, check=True, text=True, encoding="utf-8", capture_output=True)
    return json.loads(res.stdout)


def main() -> None:
    data = extract_pays()
    image_map = json.loads(MAP_JSON.read_text(encoding="utf-8")) if MAP_JSON.exists() else {}
    image_map.setdefault("pays", {})
    html = HTML.read_text(encoding="utf-8")
    ok = fail = 0
    for num, country, img in data["rows"]:
        if not str(img).endswith(".webp"):
            continue
        clean_country = re.sub(r"[\U0001F1E6-\U0001F1FF]+", "", country).strip()
        code = data["map"].get(country) or data["map"].get(clean_country)
        if not code:
            print("FAIL no code", num, country)
            fail += 1
            continue
        url = f"https://flagcdn.com/{code.lower()}.svg"
        try:
            r = requests.get(url, timeout=25)
            r.raise_for_status()
            content = r.content
            if b"<svg" not in content[:1000].lower():
                raise ValueError("non SVG")
            for folder in ("thumbs", "full"):
                out = ROOT / folder / "pays" / f"{num}.svg"
                out.write_bytes(content)
                old = ROOT / folder / "pays" / f"{num}.webp"
                if old.exists():
                    old.unlink()
            html = html.replace(f"thumbs/pays/{num}.webp", f"thumbs/pays/{num}.svg")
            image_map["pays"][str(num)] = f"full/pays/{num}.svg"
            print("OK", num, clean_country, code)
            ok += 1
        except Exception as exc:
            print("FAIL", num, country, exc)
            fail += 1
    MAP_JSON.write_text(json.dumps(image_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    HTML.write_text(html, encoding="utf-8", newline="")
    print(f"ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
