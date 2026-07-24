"""Fix Battle of Marathon image and #13 Yarmouk"""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\thumbs\batailles_decisives')
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
URL = 'https://en.wikipedia.org/w/api.php'

fixes = [
    (1, 'Marathon', 'Battle of Marathon Wikipedia article ancient Greek'),
    (13, 'Yarmouk', 'Battle of Yarmouk 636 Byzantine Arab armies illustration'),
]

def get_img(term):
    time.sleep(2.5)
    r = requests.get(URL, params={'action':'query','list':'search','srsearch':term,'format':'json','utf8':1,'srlimit':5}, headers=HEADERS, timeout=20)
    if not r.content: return None
    for res in r.json().get('query',{}).get('search',[]):
        time.sleep(1.2)
        r2 = requests.get(URL, params={'action':'query','titles':res['title'],'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
        if not r2.content: continue
        for p in r2.json().get('query',{}).get('pages',{}).values():
            src = p.get('thumbnail',{}).get('source','')
            if src and not src.lower().endswith('.svg'):
                print(f'  [{term[:40]}] -> {res["title"]}')
                return src
    return None

for num, label, term in fixes:
    print(f'#{num} {label}')
    src = get_img(term)
    if src:
        r = requests.get(src, headers=HEADERS, timeout=20)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200, 150), Image.LANCZOS)
        path = THUMBS / f'{num}.webp'
        img.save(path, 'WEBP', quality=82)
        print(f'  -> {path.name} ({path.stat().st_size}B)')
    else:
        print('  ECHEC')
print('Done.')
