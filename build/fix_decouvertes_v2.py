"""
Rattrapage des 7 echecs de fix_decouvertes.py
"""
import sys, time, requests
from pathlib import Path
from PIL import Image
import io

sys.stdout.reconfigure(encoding='utf-8')

FULL_DIR = Path("full/decouvertes_scientifiques")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "memo-app-builder/1.0 (educational)"})

# Titres alternatifs pour les 7 echecs
FIXES = [
    (1,  [
        "File:Planisphaerium Copernicanum.jpg",
        "File:Harmonia Macrocosmica - Plate 1 - Scenographia Systematis Copernicani.jpg",
        "File:Cellarius harmonia macrocosmica planisphaerium copernicanum.jpg",
    ]),
    (3,  [
        "File:William Harvey 1578-1657.jpg",
        "File:William Harvey physician.jpg",
        "File:Willam Harvey.jpg",
        "File:Portrait of William Harvey (1578-1657).jpg",
    ]),
    (5,  [
        "File:Newton's cannon.png",
        "File:Newton cannon mountain.gif",
        "File:Newtons cannon.jpg",
    ]),
    (11, [
        "File:Mendeleev's periodic table 1871.jpg",
        "File:Mendeleev Periodic Table 1871.jpg",
        "File:Periodic table Mendeleev 1871.jpg",
        "File:Mendeleev first periodic table.jpg",
    ]),
    (17, [
        "File:Penicillium sp. (50742597423).jpg",
        "File:Penicillium under microscope.jpg",
        "File:Penicillium notatum.jpg",
        "File:Penicilium microscopy.jpg",
    ]),
    (18, [
        "File:Nuclear fission.svg",
        "File:Fission chain reaction.svg",
        "File:Nuclear fission chain reaction.jpg",
    ]),
    (23, [
        "File:CMS Higgs-event.jpg",
        "File:Higgs-event.jpg",
        "File:Higgs boson decay to four muons.png",
        "File:Higgs boson event ATLAS.jpg",
    ]),
]

def get_image_url(title, width=1200):
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|size",
        "iiurlwidth": width,
        "format": "json"
    }
    for attempt in range(3):
        try:
            r = SESSION.get(url, params=params, timeout=20)
            if r.status_code == 429:
                wait = 30 * (attempt + 1)
                print(f"  Rate limit, attente {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                if page.get("pageid", -1) == -1:
                    return None  # fichier inexistant
                info = page.get("imageinfo", [{}])[0]
                img_url = info.get("thumburl") or info.get("url")
                if img_url:
                    return img_url
        except Exception as e:
            print(f"  Erreur get_url: {e}")
            time.sleep(5)
    return None

def download_and_save(url, dest_path):
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=30, stream=True)
            if r.status_code == 429:
                wait = 30 * (attempt + 1)
                print(f"  Rate limit DL, attente {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            if img.mode in ('RGBA', 'P', 'LA'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            w, h = img.size
            if max(w, h) > 1200:
                if w >= h:
                    img = img.resize((1200, int(h * 1200 / w)), Image.LANCZOS)
                else:
                    img = img.resize((int(w * 1200 / h), 1200), Image.LANCZOS)
            img.save(str(dest_path), "JPEG", quality=88)
            w2, h2 = img.size
            size_kb = dest_path.stat().st_size // 1024
            print(f"  OK {w2}x{h2} {size_kb}KB -> {dest_path.name}")
            return True
        except Exception as e:
            print(f"  Erreur DL: {e}")
            time.sleep(5)
    return False

print("=" * 60)
print("Rattrapage 7 echecs decouvertes_scientifiques")
print("=" * 60)

ok = 0
fail = []

for num, titles in FIXES:
    dest = FULL_DIR / f"{num}.jpg"
    print(f"\n[{num}] Tentatives:")
    success = False
    for title in titles:
        print(f"  -> {title}")
        url = get_image_url(title)
        if url:
            print(f"     URL: {url[:80]}")
            if download_and_save(url, dest):
                success = True
                break
        time.sleep(1)
    if success:
        ok += 1
    else:
        fail.append(num)
    time.sleep(2)

print(f"\n{'='*60}")
print(f"OK: {ok}/7")
if fail:
    print(f"ECHECS: {fail}")
print("Termine.")
