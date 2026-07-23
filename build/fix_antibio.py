import sys, pathlib, requests, time
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\inventions_majeures')
HEADERS = {'User-Agent': 'memo-app-fix/1.0'}
URL = 'https://en.wikipedia.org/w/api.php'

def get_img(terms):
    for term in terms:
        time.sleep(2)
        r = requests.get(URL, params={'action':'query','list':'search','srsearch':term,'format':'json','utf8':1,'srlimit':5}, headers=HEADERS, timeout=15)
        for res in r.json().get('query',{}).get('search',[]):
            time.sleep(1)
            r2 = requests.get(URL, params={'action':'query','titles':res['title'],'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=15)
            for p in r2.json().get('query',{}).get('pages',{}).values():
                src = p.get('thumbnail',{}).get('source','')
                if src and not src.lower().endswith('.svg'):
                    print(f"  [{term}] → {res['title']}")
                    return src
    return None

src = get_img(['Alexander Fleming penicillium mold petri dish', 'Penicillin Fleming mold culture', 'Fleming penicillin discovery 1928'])
if src:
    r = requests.get(src, headers=HEADERS, timeout=15)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img = img.resize((200, 150), Image.LANCZOS)
    img.save(THUMBS / '29.webp', 'WEBP', quality=82)
    print(f"  → 29.webp ({(THUMBS/'29.webp').stat().st_size} bytes)")
else:
    print("ÉCHEC")
