import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\periodes_geologiques')

def get_page(title):
    time.sleep(2)
    r = requests.get(URL, params={'action':'query','titles':title,'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
    for p in r.json().get('query',{}).get('pages',{}).values():
        src = p.get('thumbnail',{}).get('source','')
        if src and not src.lower().endswith('.svg'):
            return src
    return None

def try_save(src, path):
    try:
        r = requests.get(src, headers=HEADERS, timeout=20)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200, 150), Image.LANCZOS)
        img.save(path, 'WEBP', quality=82)
        return path.stat().st_size
    except Exception as e:
        print(f'    err: {e}')
        return 0

fixes = [
    (2, 'Archeen', ['Stromatolite', 'Archean eon', 'Precambrian']),
    (31, 'Cenozoique', ['Woolly mammoth', 'Cenozoic', 'Quaternary']),
]

for num, name, titles in fixes:
    print(f'\n#{num} {name}')
    for title in titles:
        src = get_page(title)
        if src:
            print(f'  [{title}] {src[-55:]}')
            size = try_save(src, THUMBS / f'{num}.webp')
            if size:
                print(f'  OK: {size}B')
                break
    else:
        print('  ECHEC')

print('\nDone.')
