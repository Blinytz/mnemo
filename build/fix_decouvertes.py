"""
Remplace toutes les images full/decouvertes_scientifiques/ par des images HD
correspondant exactement aux miniatures thumbs/decouvertes_scientifiques/.
Utilise l'API Wikimedia Commons avec titres de fichiers hardcodes.
"""
import sys, time, requests
from pathlib import Path
from PIL import Image
import io

sys.stdout.reconfigure(encoding='utf-8')

FULL_DIR = Path("full/decouvertes_scientifiques")
FULL_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "memo-app-builder/1.0 (educational)"})

# Titres de fichiers Wikimedia Commons (File:...) ou URLs directes
# L'API sera utilisee pour obtenir l'URL reelle (rasterise les SVG aussi)
IMAGES = [
    (1,  "File:Andreas Cellarius Harmonia Macrocosmica, 1660 -- Scenographia Systematis Copernicani.jpg"),
    (2,  "File:Kepler laws diagram.svg"),
    (3,  "File:William Harvey (1578-1657) Wellcome L0011793.jpg"),
    (4,  "File:Portrait of Sir Isaac Newton, 1689.jpg"),
    (5,  "File:Newton's cannon large.gif"),
    (6,  "File:Benjamin Franklin Lightning Experiment 1752.jpg"),
    (7,  "File:Liquid oxygen in a beaker 2.jpg"),
    (8,  "File:James Watt by Henry Howard.jpg"),
    (9,  "File:Origin of Species title page.jpg"),
    (10, "File:EM Spectrum Properties edit.svg"),
    (11, "File:Mendeleev's 1871 periodic table.png"),
    (12, "File:Wilhelm Röntgen.jpg"),
    (13, "File:Marie Curie c1920.jpg"),
    (14, "File:Einstein 1921 by F Schmutzer - restoration.jpg"),
    (15, "File:Tectonic plates boundaries detailed-sr.png"),
    (16, "File:Hydrogen Density Plots.png"),
    (17, "File:Penicillium rubens Thom.jpg"),
    (18, "File:Nuclear fission of Uranium 235.svg"),
    (19, "File:DNA Structure+Key+Labelled.pn NoBB.png"),
    (20, "File:CMB Timeline300 no WMAP.jpg"),
    (21, "File:Quark structure proton.svg"),
    (22, "File:Exoplanet Discovery Methods Bar.png"),
    (23, "File:Higgs boson event.jpg"),
    (24, "File:LIGO measurement of gravitational waves.svg"),
]

def get_image_url(title, width=1200):
    """Obtient l'URL directe de l'image depuis son titre Wikimedia (rasterise les SVG/GIF)."""
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
                print(f"  Rate limit API, attente {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                info = page.get("imageinfo", [{}])[0]
                img_url = info.get("thumburl") or info.get("url")
                if img_url:
                    return img_url
        except Exception as e:
            print(f"  Erreur get_url (tentative {attempt+1}): {e}")
            time.sleep(5)
    return None

def download_and_save(url, dest_path):
    """Telecharge une image, la redimensionne a max 1200px, sauvegarde en JPEG q88."""
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
            print(f"  Erreur DL (tentative {attempt+1}): {e}")
            time.sleep(5)
    return False

def process_entry(num, title):
    dest = FULL_DIR / f"{num}.jpg"
    print(f"\n[{num}/24] {title[:70]}")

    url = get_image_url(title)
    if not url:
        print(f"  ECHEC: URL introuvable")
        return False
    print(f"  URL: {url[:80]}...")
    return download_and_save(url, dest)

print("=" * 60)
print("Fix decouvertes_scientifiques full/ images")
print("=" * 60)

ok = 0
fail = []

for num, title in IMAGES:
    success = process_entry(num, title)
    if success:
        ok += 1
    else:
        fail.append(num)
    time.sleep(2)

print(f"\n{'='*60}")
print(f"OK: {ok}/24")
if fail:
    print(f"ECHECS: {fail}")
print("Termine.")
