"""
Injecte les variantes de qualité directement dans les full/ peintres
pour test en conditions réelles dans l'app.
  #1  Jan van Eyck   → A : Ghent Altarpiece   800px q88  (actuel)
  #12 Rembrandt      → B : Night Watch        1200px q88
  #23 Renoir         → C : Moulin Galette     1600px q92
"""
import sys, pathlib, requests, time
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

BASE    = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app')
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
API     = 'https://en.wikipedia.org/w/api.php'

def get_url(title, size):
    time.sleep(1.5)
    r = requests.get(API, params={
        'action': 'query', 'titles': title,
        'prop': 'pageimages', 'pithumbsize': size,
        'format': 'json'
    }, headers=HEADERS, timeout=20)
    for p in r.json().get('query', {}).get('pages', {}).values():
        src = p.get('thumbnail', {}).get('source', '')
        if src and not src.lower().endswith('.svg'):
            return src
    return None

def save_full(url, num, max_px, quality):
    r = requests.get(url, headers=HEADERS, timeout=30)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    out = BASE / 'full' / 'peintres' / f'{num}.jpg'
    img.save(out, 'JPEG', quality=quality)
    print(f'  #{num}: {img.size[0]}×{img.size[1]} q{quality} → {out.stat().st_size//1024} KB')

TESTS = [
    (1,  'Ghent Altarpiece',           800,  88),  # A actuel
    (12, 'The Night Watch',           1200,  88),  # B moyen
    (23, 'Bal du moulin de la Galette', 1600, 92), # C HD
]

for num, title, max_px, quality in TESTS:
    print(f'#{num} {title} ({max_px}px q{quality})')
    url = get_url(title, max_px)
    if url:
        save_full(url, num, max_px, quality)
    else:
        print('  ECHEC')

print('\nDone. Va dans Peintres et clique sur Jan van Eyck (A), Rembrandt (B), Renoir (C).')
