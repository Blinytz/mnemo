import requests, pathlib, time
from PIL import Image
from io import BytesIO
HEADERS = {'User-Agent': 'MemoApp/1.0'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\lunes')

# La Lune : photo NASA pleine lune — PAS la carte de tarot
for title in ['Moon', 'Full moon', 'Lunar surface']:
    time.sleep(2)
    r = requests.get(URL, params={'action':'query','titles':title,'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
    for p in r.json().get('query',{}).get('pages',{}).values():
        src = p.get('thumbnail',{}).get('source','')
        short = src[-60:] if src else 'NONE'
        print(f'[{title}] -> {short}')
        if src and not src.lower().endswith('.svg'):
            r2 = requests.get(src, headers=HEADERS, timeout=20)
            img = Image.open(BytesIO(r2.content)).convert('RGB')
            img = img.resize((200,150), Image.LANCZOS)
            path = THUMBS / '1.webp'
            img.save(path, 'WEBP', quality=82)
            print(f'Sauve: {path.stat().st_size}B')
            import sys; sys.exit(0)
print('Echec')
