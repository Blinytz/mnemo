import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\fleuves_monde')

# Essayer différents titres de page pour trouver une belle image du Niger
titles = ['Niger River', 'Niger (river)', 'Inner Niger Delta', 'Timbuktu', 'Djenne']

for title in titles:
    time.sleep(2)
    r = requests.get(URL, params={'action':'query','titles':title,'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
    for p in r.json().get('query',{}).get('pages',{}).values():
        src = p.get('thumbnail',{}).get('source','')
        exists = src and not src.lower().endswith('.svg')
        print(f'[{title}] -> {src[-60:] if src else "NONE"} {"OK" if exists else "SVG/skip"}')
        if exists:
            r2 = requests.get(src, headers=HEADERS, timeout=20)
            img = Image.open(BytesIO(r2.content)).convert('RGB')
            img = img.resize((200,150), Image.LANCZOS)
            path = THUMBS / '13.webp'
            img.save(path, 'WEBP', quality=82)
            print(f'  Sauvé: {path.stat().st_size}B')
            import sys; sys.exit(0)

print('Tous en echec')
