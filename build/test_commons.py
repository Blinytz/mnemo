import requests, sys, time
sys.stdout.reconfigure(encoding='utf-8')
API = 'https://commons.wikimedia.org/w/api.php'
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}

queries = [
    'Matterhorn mountain Switzerland',
    'Alain Prost Formula 1 racing',
    'Battle of Waterloo painting',
    'Louvre Museum Paris exterior',
    'Monet Water Lilies painting',
    'Mount Everest aerial',
]

for q in queries:
    r = requests.get(API, params={
        'action':'query','generator':'search',
        'gsrnamespace':6,'gsrlimit':8,'gsrsearch':q,
        'prop':'imageinfo','iiprop':'url|size','iiurlwidth':2000,
        'format':'json'
    }, headers=HEADERS, timeout=15)
    pages = r.json().get('query',{}).get('pages',{})
    valid = []
    for p in pages.values():
        info = p.get('imageinfo',[{}])[0]
        w, h = info.get('width',0), info.get('height',0)
        url = info.get('thumburl','')
        title = p.get('title','')
        if w>500 and h>500 and url and '.svg' not in url.lower():
            valid.append((w*h, w, h, url, title))
    valid.sort(reverse=True)
    if valid:
        _, w, h, url, title = valid[0]
        print(f'{q}: {w}x{h}')
        print(f'  {title}')
        print(f'  {url[:100]}')
    else:
        print(f'{q}: RIEN')
    time.sleep(0.5)
if False:
    names = [
        "Côte-d'Or-Position.svg",
    "Côtes-d'Armor-Position.svg",
    "Val-d'Oise-Position.svg",
    "Paris-Position.svg",
    "Ain-Position.svg",
]
for fname in names:
    api = f"https://commons.wikimedia.org/w/api.php?action=query&titles=File:{urllib.parse.quote(fname)}&prop=imageinfo&iiprop=url&format=json&formatversion=2"
    try:
        r = requests.get(api, headers={'User-Agent': WIKI_UA}, timeout=10)
        info = r.json()
        pages = info.get('query', {}).get('pages', [])
        for page in pages:
            iis = page.get('imageinfo', [])
            missing = page.get('missing', True)
            if iis:
                print(f"FOUND: {fname!r} -> {iis[0]['url'][:60]}")
            else:
                print(f"MISSING: {fname!r} (missing={missing})")
    except Exception as e:
        print(f"ERROR: {fname!r} -> {e}")
