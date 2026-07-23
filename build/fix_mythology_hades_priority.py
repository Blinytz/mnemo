#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

import build_images as b


def extract_html_data(path="memo_v46_images.html"):
    out = subprocess.check_output(["node", "build/extract_data.js", path], text=True, encoding="utf-8")
    return json.loads(out)


def write_raster(row_num: str, data: bytes, source: str):
    thumb = b.to_webp_thumb(data)
    if not thumb:
        raise RuntimeError(f"thumb impossible: mythologie/{row_num}")
    ext = b.raster_ext(data)
    (b.THUMBS / "mythologie").mkdir(parents=True, exist_ok=True)
    (b.FULL / "mythologie").mkdir(parents=True, exist_ok=True)
    (b.THUMBS / "mythologie" / f"{row_num}.webp").write_bytes(thumb)
    (b.FULL / "mythologie" / f"{row_num}.{ext}").write_bytes(data)
    print(f"mythologie/{row_num}: {source} -> full/mythologie/{row_num}.{ext}")


def main():
    data = extract_html_data()
    hades_files = data.get("HADES_OFFICIAL_FILES", {})

    current = extract_html_data("memo.html")
    myth = next(l for l in current["DEFAULT_LISTS"] if l["id"] == "mythologie")
    img_idx = myth["columns"].index("Image")
    name_idx = myth["columns"].index("Nom")

    b.load_cache()
    failures = []
    applied = 0
    for row in myth["rows"]:
        name = str(row[name_idx])
        row_num = Path(str(row[img_idx])).stem
        files = hades_files.get(name) or hades_files.get(b.strip_accents(name)) or []
        if not files:
            continue
        ok = False
        for filename in files:
            try:
                data_bytes, kind = b.resolve_hades_file(filename)
                if data_bytes:
                    write_raster(row_num, data_bytes, filename)
                    applied += 1
                    ok = True
                    break
            except Exception as exc:
                failures.append(f"{name} / {filename}: {exc}")
        if not ok:
            failures.append(f"{name}: téléchargement Hadès impossible ({', '.join(files)})")
    b.save_cache()
    report = b.BUILD_DIR / "mythologie_hades_failures.txt"
    report.write_text("\n".join(failures), encoding="utf-8")
    print(f"applied={applied} failures={len(failures)} report={report}")


if __name__ == "__main__":
    main()
