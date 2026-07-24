"""
Fix périodes géologiques :
#2 Archéen → stromatolite (premiers fossiles de vie sur Terre, typique de l'Archéen)
#31 Cénozoïque → mammifère préhistorique (mégafaune du Cénozoïque)
"""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\thumbs\periodes_geologiques')

def get_page(title):
    time.sleep(2)
    r = requests.get(URL, params={'action':'query','titles':title,'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
    for p in r.json().get('query',{}).get('pages',{}).values():
        src = p.get('thumbnail',{}).get('source','')
        if src and not src.lower().endswith('.svg'):
            return src
    return None

fixes = [
    (2, 'Archéen',
     'Stromatolite (premiers fossiles vivants de l Archéen)',
     ['Stromatolite', 'Archean', 'Precambrian']),
    (31, 'Cénozoïque',
     'Mégafaune du Cénozoïque ou Quaternaire (mammouth, etc.)',
     ['Woolly mammoth', 'Cenozoic', 'Pleistocene megafauna']),
]

for num, name, ideal, titles in fixes:
    print(f'\n#{num} {name} — {ideal}')
    for title in titles:
        src = get_page(title)
        if src:
            print(f'  [{title}] -> {src[-50:]}')
            r = requests.get(src, headers=HEADERS, timeout=20)
            img = Image.open(BytesIO(r.content)).convert('RGB')
            img = img.resize((200, 150), Image.LANCZOS)
            path = THUMBS / f'{num}.webp'
            img.save(path, 'WEBP', quality=82)
            print(f'  Sauve: {path.stat().st_size}B')
            break
    else:
        print('  ECHEC')

print('\nDone.')
