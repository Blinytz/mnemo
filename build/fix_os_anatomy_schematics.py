#!/usr/bin/env python3
from pathlib import Path
import shutil
import math

from PIL import Image, ImageDraw, ImageFont

import build_images as b


W, H = 1200, 900
THUMBS = Path("thumbs/os")
FULL = Path("full/os")

NAMES = {
    8: "Zygomatique",
    11: "Palatin",
    15: "Marteau",
    18: "Os hyoïde",
    63: "Scaphoïde",
    64: "Lunatum",
    65: "Triquétrum",
    66: "Pisiforme",
    67: "Trapèze",
    68: "Trapézoïde",
    69: "Grand os (capitatum)",
    70: "Hamatum",
    97: "Calcanéum",
    98: "Talus (astragale)",
    99: "Naviculaire",
    100: "Cunéiforme médial",
    101: "Cunéiforme intermédiaire",
    102: "Cunéiforme latéral",
    103: "Cuboïde",
    109: "Phalange prox. gros orteil",
    110: "Phalange dist. gros orteil",
    111: "Phalange prox. 2e orteil",
    112: "Phalange méd. 2e orteil",
    113: "Phalange dist. 2e orteil",
    114: "Phalange prox. 3e orteil",
    115: "Phalange méd. 3e orteil",
    116: "Phalange dist. 3e orteil",
    117: "Phalange prox. 4e orteil",
    118: "Phalange méd. 4e orteil",
    119: "Phalange dist. 4e orteil",
    120: "Phalange prox. 5e orteil",
    121: "Phalange méd. 5e orteil",
    122: "Phalange dist. 5e orteil",
    16: "Enclume",
    23: "C5",
    24: "C6",
    26: "T1",
    27: "T2",
    28: "T3",
    30: "T5",
    31: "T6",
    32: "T7",
    33: "T8",
    34: "T9",
    35: "T10",
    36: "T11",
    39: "L2",
    46: "Cote 1",
    47: "Cote 2",
    48: "Cote 3",
    49: "Cote 4",
    50: "Cote 5",
    51: "Cote 6",
    52: "Cote 7",
    53: "Cote 8",
    54: "Cote 9",
    55: "Cote 10",
    56: "Cote 11 (flottante)",
    57: "Cote 12 (flottante)",
    73: "Metacarpien 3",
    76: "Phalange prox. pouce",
    78: "Phalange prox. index",
    81: "Phalange prox. majeur",
    82: "Phalange med. majeur",
    84: "Phalange prox. annulaire",
    87: "Phalange prox. auriculaire",
    88: "Phalange med. auriculaire",
}

CARPALS = {
    63: (420, 360, 110, 92), 64: (540, 350, 100, 92), 65: (648, 365, 112, 90), 66: (746, 458, 70, 62),
    67: (404, 470, 106, 92), 68: (516, 472, 96, 86), 69: (622, 462, 116, 102), 70: (744, 372, 110, 96),
}

TARSALS = {
    97: (725, 492, 170, 104), 98: (615, 382, 126, 96), 99: (505, 408, 104, 78),
    100: (412, 455, 84, 62), 101: (480, 470, 80, 60), 102: (552, 482, 84, 64), 103: (642, 500, 118, 82),
}

TOES = {
    109: (370, 435, 58, 112), 110: (370, 315, 54, 92),
    111: (468, 448, 52, 100), 112: (468, 352, 48, 82), 113: (468, 270, 44, 68),
    114: (558, 455, 50, 98), 115: (558, 360, 46, 80), 116: (558, 280, 42, 66),
    117: (642, 470, 48, 88), 118: (642, 382, 44, 70), 119: (642, 308, 40, 58),
    120: (720, 492, 44, 76), 121: (720, 418, 40, 58), 122: (720, 356, 36, 48),
}


def font(size, bold=False):
    names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def base(title, group):
    im = Image.new("RGB", (W, H), "#f7fafc")
    d = ImageDraw.Draw(im)
    rounded(d, (54, 54, W - 54, H - 54), 42, "#ffffff", "#c9d7e6", 4)
    d.text((100, 90), "Anatomie osseuse", fill="#64748b", font=font(34, True))
    d.text((100, 142), title, fill="#172033", font=font(58, True))
    d.text((100, 215), group, fill="#41546e", font=font(30))
    d.line((100, 258, W - 100, 258), fill="#dbe5ef", width=3)
    return im, d


def legend(d):
    d.ellipse((104, 780, 136, 812), fill="#e11d48")
    d.text((152, 778), "os ciblé", fill="#172033", font=font(30, True))
    d.text((152, 820), "schéma local homogène", fill="#64748b", font=font(24))


def bone_ellipse(d, box, target=False, label=None):
    fill = "#e11d48" if target else "#d8dee8"
    outline = "#8b9aaf" if not target else "#9f1239"
    d.ellipse(box, fill=fill, outline=outline, width=4)
    if label:
        cx = (box[0] + box[2]) / 2
        cy = (box[1] + box[3]) / 2
        d.text((cx, cy), label, anchor="mm", fill="#172033", font=font(20, True))


def draw_carpal(n):
    im, d = base(NAMES[n], "Main - carpe")
    d.line((610, 270, 610, 610), fill="#b8c4d4", width=20)
    d.line((470, 610, 750, 610), fill="#b8c4d4", width=18)
    d.text((500, 625), "radius", fill="#64748b", font=font(24))
    d.text((690, 625), "ulna", fill="#64748b", font=font(24))
    for k, (x, y, w, h) in CARPALS.items():
        bone_ellipse(d, (x, y, x + w, y + h), k == n)
    d.text((425, 700), "rangée distale", fill="#64748b", font=font(24))
    d.text((640, 300), "rangée proximale", fill="#64748b", font=font(24))
    legend(d)
    return im


def draw_tarsal(n):
    im, d = base(NAMES[n], "Pied - tarse")
    d.line((315, 670, 860, 610), fill="#b8c4d4", width=18)
    for k, (x, y, w, h) in TARSALS.items():
        bone_ellipse(d, (x, y, x + w, y + h), k == n)
    for x in (380, 465, 550, 635, 720):
        d.line((x, 550, x - 70, 705), fill="#d8dee8", width=20)
    d.text((700, 640), "talon", fill="#64748b", font=font(24))
    d.text((330, 720), "avant-pied", fill="#64748b", font=font(24))
    legend(d)
    return im


def draw_toe(n):
    im, d = base(NAMES[n], "Pied - phalanges")
    for x in (370, 468, 558, 642, 720):
        d.line((x, 540, x, 690), fill="#cbd5e1", width=34)
    for k, (x, y, w, h) in TOES.items():
        rounded(d, (x - w // 2, y - h // 2, x + w // 2, y + h // 2), 24, "#e11d48" if k == n else "#d8dee8", "#9f1239" if k == n else "#8b9aaf", 4)
    d.text((320, 715), "gros orteil", fill="#64748b", font=font(24))
    d.text((640, 715), "orteils latéraux", fill="#64748b", font=font(24))
    legend(d)
    return im


def draw_face(n):
    im, d = base(NAMES[n], "Face")
    d.ellipse((410, 280, 790, 670), fill="#e7ebf0", outline="#8b9aaf", width=5)
    d.ellipse((485, 395, 565, 475), fill="#ffffff", outline="#8b9aaf", width=4)
    d.ellipse((635, 395, 715, 475), fill="#ffffff", outline="#8b9aaf", width=4)
    d.polygon([(600, 455), (560, 565), (640, 565)], fill="#d8dee8", outline="#8b9aaf")
    d.rectangle((535, 590, 665, 645), fill="#d8dee8", outline="#8b9aaf", width=4)
    if n == 8:
        d.ellipse((430, 455, 520, 545), fill="#e11d48", outline="#9f1239", width=4)
        d.ellipse((680, 455, 770, 545), fill="#e11d48", outline="#9f1239", width=4)
    else:
        d.polygon([(540, 560), (600, 525), (660, 560), (640, 610), (560, 610)], fill="#e11d48", outline="#9f1239")
    legend(d)
    return im


def draw_other(n):
    title = NAMES[n]
    group = "Oreille moyenne" if n in (15, 16) else "Gorge"
    im, d = base(title, group)
    if n in (15, 16):
        d.arc((400, 320, 760, 680), 200, 520, fill="#94a3b8", width=32)
        if n == 15:
            d.ellipse((528, 430, 676, 548), fill="#e11d48", outline="#9f1239", width=5)
            d.line((650, 520, 750, 610), fill="#e11d48", width=22)
        else:
            d.ellipse((495, 425, 565, 495), fill="#e11d48", outline="#9f1239", width=5)
            d.ellipse((615, 425, 685, 495), fill="#e11d48", outline="#9f1239", width=5)
            d.line((560, 460, 620, 460), fill="#e11d48", width=22)
        d.text((450, 700), "osselet de l'oreille moyenne", fill="#64748b", font=font(28))
    else:
        d.arc((420, 360, 780, 610), 0, 180, fill="#94a3b8", width=26)
        d.arc((475, 445, 725, 650), 180, 360, fill="#94a3b8", width=26)
        d.line((600, 410, 600, 660), fill="#cbd5e1", width=24)
        d.arc((480, 480, 720, 700), 200, 340, fill="#e11d48", width=32)
        d.text((450, 705), "os suspendu à la base de la langue", fill="#64748b", font=font(28))
    legend(d)
    return im


def draw_spine(n):
    title = NAMES[n]
    group = "Colonne - cervicale" if title.startswith("C") else "Colonne - dorsale" if title.startswith("T") else "Colonne - lombaire"
    im, d = base(title, group)
    levels = [f"C{i}" for i in range(1, 8)] + [f"T{i}" for i in range(1, 13)] + [f"L{i}" for i in range(1, 6)]
    y0 = 304
    target = title
    for i, level in enumerate(levels):
        y = y0 + i * 20
        if level.startswith("C"):
            x, width = 545, 110
        elif level.startswith("T"):
            x, width = 510, 180
        else:
            x, width = 495, 210
        active = level == target
        rounded(d, (x, y, x + width, y + 17), 7, "#e11d48" if active else "#d8dee8",
                "#9f1239" if active else "#8b9aaf", 2)
        if active:
            d.text((735, y - 10), level, fill="#9f1239", font=font(30, True))
    d.text((220, 324), "cervicales", fill="#64748b", font=font(24))
    d.text((220, 510), "dorsales", fill="#64748b", font=font(24))
    d.text((220, 766), "lombaires", fill="#64748b", font=font(24))
    legend(d)
    return im


def draw_rib(n):
    title = NAMES[n]
    number = n - 45
    im, d = base(title, "Cage thoracique")
    d.ellipse((430, 285, 770, 735), outline="#a8b5c5", width=8)
    d.line((600, 280, 600, 746), fill="#b8c4d4", width=30)
    d.rectangle((565, 365, 635, 610), fill="#d8dee8", outline="#8b9aaf", width=4)
    for i in range(12):
        y = 340 + i * 27
        active = i + 1 == number
        color = "#e11d48" if active else "#d8dee8"
        outline = "#9f1239" if active else "#8b9aaf"
        d.arc((315, y - 65, 600, y + 65), 72, 288, fill=color, width=18)
        d.arc((600, y - 65, 885, y + 65), 252, 108, fill=color, width=18)
        if active:
            d.text((910, y - 18), str(number), fill="#9f1239", font=font(30, True))
    d.text((380, 755), "cotes flottantes : 11 et 12", fill="#64748b", font=font(25))
    legend(d)
    return im


def draw_hand(n):
    title = NAMES[n]
    im, d = base(title, "Main")
    fingers = [
        (385, "pouce", [76, 77]),
        (500, "index", [78, 79, 80]),
        (615, "majeur", [81, 82, 83]),
        (730, "annulaire", [84, 85, 86]),
        (845, "auriculaire", [87, 88, 89]),
    ]
    for x, label, segments in fingers:
        for i, key in enumerate(segments):
            y = 500 - i * 105
            active = key == n
            rounded(d, (x - 28, y - 42, x + 28, y + 42), 20,
                    "#e11d48" if active else "#d8dee8",
                    "#9f1239" if active else "#8b9aaf", 3)
        d.text((x, 650), label, anchor="mm", fill="#64748b", font=font(22))
    for i, key in enumerate([71, 72, 73, 74, 75]):
        x = 385 + i * 115
        active = key == n
        rounded(d, (x - 32, 570, x + 32, 710), 18, "#e11d48" if active else "#d8dee8",
                "#9f1239" if active else "#8b9aaf", 3)
    d.text((610, 745), "metacarpiens", anchor="mm", fill="#64748b", font=font(25))
    legend(d)
    return im


def make(n):
    if 63 <= n <= 70:
        return draw_carpal(n)
    if 97 <= n <= 103:
        return draw_tarsal(n)
    if 109 <= n <= 122:
        return draw_toe(n)
    if n in (8, 11):
        return draw_face(n)
    if n in (23, 24, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 39):
        return draw_spine(n)
    if 46 <= n <= 57:
        return draw_rib(n)
    if n in (73, 76, 78, 81, 82, 84, 87, 88):
        return draw_hand(n)
    return draw_other(n)


def backup_existing(n):
    root = Path("build/asset_backups/v60")
    for directory in (THUMBS, FULL):
        for path in directory.glob(f"{n}.*"):
            destination = root / path
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)


def main():
    nums = [8, 11, 15, 18, 63, 64, 65, 66, 67, 68, 69, 70, 97, 98, 99, 100, 101, 102, 103,
            109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122,
            16, 23, 24, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 39,
            46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
            73, 76, 78, 81, 82, 84, 87, 88]
    THUMBS.mkdir(parents=True, exist_ok=True)
    FULL.mkdir(parents=True, exist_ok=True)
    for n in nums:
        im = make(n)
        backup_existing(n)
        full = FULL / f"{n}.webp"
        from io import BytesIO
        buf = BytesIO()
        im.save(buf, "WEBP", quality=94, method=6)
        full.write_bytes(buf.getvalue())
        THUMBS.joinpath(f"{n}.webp").write_bytes(b.to_webp_thumb(buf.getvalue()))
        print(f"os/{n}: {NAMES[n]}")


if __name__ == "__main__":
    main()
