"""
Test qualité full/ : compare 3 variantes pour 5 images représentatives.
  A = actuel    : source 800px  → JPEG max 800px q88
  B = moyen     : source 1200px → JPEG max 1200px q88
  C = hd        : source 1600px → JPEG max 1600px q92
Sortie : full_test/{slug}_A.jpg, _B.jpg, _C.jpg
"""
import sys, pathlib, requests, time
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

BASE    = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')
OUTDIR  = BASE / 'full_test'
OUTDIR.mkdir(exist_ok=True)
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
API     = 'https://en.wikipedia.org/w/api.php'

VARIANTS = [
    ('A', 800,  800,  88),   # actuel
    ('B', 1200, 1200, 88),   # moyen
    ('C', 1600, 1600, 92),   # hd
]

SUBJECTS = [
    ('night_watch',        'The Night Watch'),            # peinture détaillée
    ('moulin_galette',     'Bal du moulin de la Galette'),# peinture colorée
    ('divine_comedy',      'Divine Comedy'),               # illustration/enluminure
    ('mughal_empire',      'Mughal Empire'),               # miniature
    ('1998_world_cup',     '1998 FIFA World Cup'),         # photo
]

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

def download_variant(slug, title, variant, src_size, max_px, quality):
    url = get_url(title, src_size)
    if not url:
        print(f'  {variant}: ECHEC')
        return None
    r = requests.get(url, headers=HEADERS, timeout=30)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    out = OUTDIR / f'{slug}_{variant}.jpg'
    img.save(out, 'JPEG', quality=quality)
    size_kb = out.stat().st_size // 1024
    print(f'  {variant} ({src_size}px src → {img.size[0]}x{img.size[1]} q{quality}): {size_kb} KB → {out.name}')
    return out

for slug, title in SUBJECTS:
    print(f'\n{title}')
    for variant, src_size, max_px, quality in VARIANTS:
        download_variant(slug, title, variant, src_size, max_px, quality)

print('\nDone. Images dans full_test/')
