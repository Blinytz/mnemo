import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\fleuves_monde')

def get_page(title):
    time.sleep(2)
    r = requests.get(URL, params={'action':'query','titles':title,'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
    for p in r.json().get('query',{}).get('pages',{}).values():
        src = p.get('thumbnail',{}).get('source','')
        print(f'  [{title}] -> {src[-60:] if src else "NONE"}')
        return src if src and not src.lower().endswith('.svg') else None
    return None

# Try several page titles for Zambezi
for title in ['Victoria Falls', 'Zambezi', 'Zambezi River']:
    src = get_page(title)
    if src:
        r = requests.get(src, headers=HEADERS, timeout=20)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200,150), Image.LANCZOS)
        path = THUMBS / '16.webp'
        img.save(path, 'WEBP', quality=82)
        print(f'  Sauvé 16.webp: {path.stat().st_size}B')
        break
