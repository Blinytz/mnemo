"""Test DuckDuckGo images sur quelques entrées représentatives."""
import sys, requests
sys.stdout.reconfigure(encoding='utf-8')
from duckduckgo_search import DDGS
from PIL import Image
from io import BytesIO
import pathlib, time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')
OUT = BASE / 'build' / 'ddg_test'
OUT.mkdir(exist_ok=True)

tests = [
    ('peintres', 1, 'Jan van Eyck Ghent Altarpiece painting'),
    ('peintres', 5, 'Michelangelo Sistine Chapel painting'),
    ('montagnes_monde', 1, 'Mount Everest aerial photo'),
    ('montagnes_monde', 21, 'Matterhorn mountain photo'),
    ('batailles_decisives', 6, 'Battle of Stalingrad World War 2'),
    ('f1_champions', 20, 'Alain Prost Formula 1 racing'),
    ('musees_monde', 1, 'Louvre Museum Paris exterior'),
    ('philosophes', 1, 'Socrates ancient Greek philosopher bust'),
    ('films', 44, 'Titanic 1997 film scene'),
    ('rois_france', 60, 'Louis XIV portrait painting'),
]

ddgs = DDGS()

for folder, num, query in tests:
    print(f'\n{folder}/{num}: "{query}"')
    try:
        results = list(ddgs.images(query, max_results=5, size='Large'))
        for i, r in enumerate(results[:3]):
            url = r['image']
            w, h = r.get('width', 0), r.get('height', 0)
            print(f'  [{i+1}] {w}x{h} — {url[:80]}')
        # Télécharger le premier
        if results:
            best = max(results[:5], key=lambda r: r.get('width',0)*r.get('height',0))
            try:
                resp = requests.get(best['image'], headers=HEADERS, timeout=10)
                img = Image.open(BytesIO(resp.content)).convert('RGB')
                img.thumbnail((1200, 1200), Image.LANCZOS)
                out = OUT / f'{folder}_{num}.jpg'
                img.save(out, 'JPEG', quality=88)
                print(f'  → Sauvé: {img.size[0]}x{img.size[1]} {out.stat().st_size//1024}KB')
            except Exception as e:
                print(f'  → Téléchargement échoué: {e}')
        time.sleep(1)
    except Exception as e:
        print(f'  ERREUR: {e}')

print('\nDone. Vérifie build/ddg_test/')
