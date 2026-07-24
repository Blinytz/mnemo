"""Troisième passe sur les fleuves suspects — fichiers trop petits."""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\thumbs\fleuves_monde')

# Pour chaque fleuve : image idéale raisonnée
# Volga : célèbre peinture Repin "Haleurs de la Volga" OU photo panoramique
# Niger : delta intérieur du Mali vu du ciel OU le fleuve traversant Niamey
# Orange : canyon/gorges du fleuve Orange en Afrique du Sud
# Sénégal : fleuve avec végétation tropicale
FIXES = [
    (15, 'Volga', 'Barge Haulers on the Volga Repin painting iconic', 'Barge Haulers on the Volga'),
    (13, 'Niger', 'Niger River inland delta Mali aerial', 'Niger Inland Delta'),
    (27, 'Orange River', 'Augrabies Falls Orange River gorge South Africa', 'Augrabies Falls'),
    (29, 'Senegal River', 'Senegal River West Africa landscape', 'Senegal River'),
]

def get_page_img(title):
    time.sleep(2)
    r = requests.get(URL, params={'action':'query','titles':title,'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
    for p in r.json().get('query',{}).get('pages',{}).values():
        src = p.get('thumbnail',{}).get('source','')
        if src and not src.lower().endswith('.svg'):
            return src
    return None

for num, name, ideal, title in FIXES:
    print(f'\n#{num} {name}')
    print(f'  Idéal: {ideal}')
    src = get_page_img(title)
    if src:
        print(f'  src: {src[-60:]}')
        r = requests.get(src, headers=HEADERS, timeout=20)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200,150), Image.LANCZOS)
        path = THUMBS / f'{num}.webp'
        img.save(path, 'WEBP', quality=82)
        print(f'  Sauvé: {path.stat().st_size}B')
    else:
        print('  ECHEC')

print('\nDone.')
