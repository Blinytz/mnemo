"""Vérifie visuellement les titres Wikipedia des images téléchargées via EXIF/metadata."""
import sys, pathlib, json, re
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

REPO = pathlib.Path(__file__).parent.parent
HTML = REPO / 'memo.html'
THUMBS = REPO / 'thumbs' / 'decouvertes_scientifiques'

html = open(HTML, encoding='utf-8').read()
m = re.search(r'const CURATED_LISTS_V3 = (\[[\s\S]*?\]);\s*DEFAULT_LISTS\.push', html)
curated = json.loads(m.group(1))
dec = next(l for l in curated if l['id'] == 'decouvertes_scientifiques')

print(f"{len(dec['rows'])} entrées:")
for row in dec['rows']:
    num = row[0]
    titre = row[2]
    path = THUMBS / f'{num}.webp'
    if path.exists():
        size = path.stat().st_size
        try:
            img = Image.open(path)
            w, h = img.size
            status = f"{w}x{h} {size}B"
        except:
            status = f"ERREUR {size}B"
    else:
        status = "MANQUANT"
    flag = " ⚠" if path.exists() and path.stat().st_size < 2000 else ""
    print(f"  {num:2}. {titre:<45} {status}{flag}")
