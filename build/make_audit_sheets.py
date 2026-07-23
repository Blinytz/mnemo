#!/usr/bin/env python3
import json
import math
import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    import cairosvg
except Exception:
    cairosvg = None

REPO = Path(__file__).parent.parent
HTML = REPO / "memo.html"
OUT = REPO / "build" / "audit_sheets"


def extract_default_lists():
    html = HTML.read_text(encoding="utf-8")
    marker = "const DEFAULT_LISTS = "
    start = html.index(marker) + len(marker)
    i = start
    depth = 0
    in_str = False
    quote = ""
    while i < len(html):
        c = html[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                in_str = False
        else:
            if c in ("'", '"'):
                in_str = True
                quote = c
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return json.loads(html[start:i + 1])
        i += 1
    raise RuntimeError("DEFAULT_LISTS introuvable")


def norm(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", str(s or "").lower()) if unicodedata.category(c) != "Mn")


def is_image_col(name):
    n = norm(name)
    return any(k in n for k in ("image", "photo", "portrait", "drapeau", "illustration", "icone", "visuel", "flag", "localisation", "localization", "carte", "map"))


def label_for_row(lst, row):
    preferred = {
        "departements": "Nom",
        "etats_usa": "État",
        "mythologie": "Nom",
        "philosophes": "Nom",
        "films": "Titre",
        "litterature": "Titre",
        "peintres": "Nom",
        "pays": "Pays",
        "lunes": "Lune",
        "elements": "Nom",
        "consoles": "Console",
        "f1_champions": "Pilote",
        "guerres": "Conflit",
        "mouvements_peinture": "Mouvement",
        "rois_france": "Nom",
        "chefs_etat": "Nom",
    }
    cols = lst["columns"]
    want = preferred.get(lst["id"])
    if want:
        for i, col in enumerate(cols):
            if norm(col) == norm(want) and i < len(row):
                return str(row[i])
    for i, col in enumerate(cols):
        if i >= 1 and not is_image_col(col) and i < len(row) and str(row[i]).strip():
            return str(row[i])
    return str(row[0] if row else "")


def font(size=14, bold=False):
    names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def load_image(src):
    if not src:
        return None
    if src.startswith("data:image/svg"):
        return None
    path = REPO / src
    if not path.exists():
        return None
    try:
        if path.suffix.lower() == ".svg":
            if not cairosvg:
                return None
            png = cairosvg.svg2png(url=str(path), output_width=360, output_height=240)
            return Image.open(BytesIO(png)).convert("RGBA")
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def fit(img, w, h):
    if img is None:
        out = Image.new("RGBA", (w, h), "#f5f5f5")
        d = ImageDraw.Draw(out)
        d.rectangle([0, 0, w - 1, h - 1], outline="#c8c8c8")
        d.text((w / 2, h / 2), "SVG/data", anchor="mm", font=font(12), fill="#777")
        return out
    img = img.copy()
    img.thumbnail((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), "#ffffff")
    out.alpha_composite(img, ((w - img.width) // 2, (h - img.height) // 2))
    return out


def wrap_text(draw, text, max_width, fnt):
    words = str(text).split()
    lines = []
    cur = ""
    for word in words:
        test = (cur + " " + word).strip()
        if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines[:3]


def make_sheet(lst, ci, page_rows):
    cell_w, cell_h = 190, 230
    cols_count = 5
    rows_count = math.ceil(len(page_rows) / cols_count)
    title_h = 54
    sheet = Image.new("RGB", (cols_count * cell_w, title_h + rows_count * cell_h), "#f2f3f5")
    draw = ImageDraw.Draw(sheet)
    title = f"{lst['name']} - {lst['columns'][ci]}"
    draw.text((16, 16), title, font=font(22, True), fill="#222")
    small = font(12)
    label_font = font(13)
    for idx, (ri, row) in enumerate(page_rows):
        x = (idx % cols_count) * cell_w
        y = title_h + (idx // cols_count) * cell_h
        draw.rectangle([x + 6, y + 6, x + cell_w - 6, y + cell_h - 6], fill="#ffffff", outline="#d0d4da")
        src = str(row[ci] if ci < len(row) else "")
        img = fit(load_image(src), cell_w - 24, 145)
        sheet.paste(img.convert("RGB"), (x + 12, y + 12))
        label = f"{row[0]} - {label_for_row(lst, row)}"
        lines = wrap_text(draw, label, cell_w - 20, label_font)
        ty = y + 164
        for line in lines:
            draw.text((x + 10, ty), line, font=label_font, fill="#1f2933")
            ty += 17
        ext = Path(src).suffix.lower().replace(".", "") if src else "none"
        draw.text((x + 10, y + cell_h - 24), ext, font=small, fill="#667")
    return sheet


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.jpg"):
        old.unlink()
    lists = extract_default_lists()
    page_size = 40
    made = 0
    index = []
    for lst in lists:
        img_cols = [i for i, c in enumerate(lst["columns"]) if i >= 1 and is_image_col(c)]
        for ci in img_cols:
            rows = list(enumerate(lst["rows"]))
            for page_no in range(math.ceil(len(rows) / page_size)):
                chunk = rows[page_no * page_size:(page_no + 1) * page_size]
                sheet = make_sheet(lst, ci, chunk)
                out = OUT / f"{lst['id']}__{ci}_{norm(lst['columns'][ci]).replace(' ', '_')}__p{page_no + 1}.jpg"
                sheet.save(out, "JPEG", quality=88)
                index.append(str(out.relative_to(REPO)))
                made += 1
    (OUT / "index.txt").write_text("\n".join(index), encoding="utf-8")
    print(f"audit sheets: {made}")
    print(OUT)


if __name__ == "__main__":
    main()
