import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\fleuves_monde')

def search_img(term, n=5):
    time.sleep(2)
    r = requests.get(URL, params={'action':'query','list':'search','srsearch':term,'format':'json','utf8':1,'srlimit':n}, headers=HEADERS, timeout=20)
    results = r.json().get('query',{}).get('search',[])
    titles = [x['title'] for x in results[:4]]
    print(f'  Résultats: {titles}')
    for res in results:
        time.sleep(1)
        r2 = requests.get(URL, params={'action':'query','titles':res['title'],'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
        for p in r2.json().get('query',{}).get('pages',{}).values():
            src = p.get('thumbnail',{}).get('source','')
            if src and not src.lower().endswith('.svg'):
                print(f'  -> {res["title"]}')
                return src
    return None

fixes = [
    (15, 'Volga Russia longest European river'),
    (16, 'Victoria Falls Zambezi waterfall aerial'),
]

for num, term in fixes:
    print(f'\n#{num} -- {term}')
    src = search_img(term)
    if src:
        r = requests.get(src, headers=HEADERS, timeout=20)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200,150), Image.LANCZOS)
        path = THUMBS / f'{num}.webp'
        img.save(path, 'WEBP', quality=82)
        print(f'  OK: {path.stat().st_size}B')
    else:
        print('  ECHEC')

print('Done.')
