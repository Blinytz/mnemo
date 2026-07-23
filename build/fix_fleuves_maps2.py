"""
Passe 2 : corriger les mauvais matches et les échecs.
Priorité dans les noms de fichier : *rivermap* > *basinmap* > *basin* > *map*
Éviter : peintures, cartes historiques >200 ans, affluents secondaires.
"""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\fleuves_monde')

EXCLUDE = ['1561', '1619', '1681', '1697', '1750', '1800', '1850', '1897', '1413',
           'perrot', 'hondius', 'ruscelli', 'viladestes', 'painting', 'album',
           'breaches', 'marquette', 'jolliet', 'ancient_courses', 'meander',
           'maas', 'delta1', 'dongting', 'gan river', 'hanshui']

MAP_PRIORITY = ['rivermap', 'river_map', 'basinmap', 'basin_map', 'watershedmap',
                'watershed_map', 'river basin', 'river_basin', 'basin.png', 'map.png']
MAP_KEYWORDS = ['map', 'basin', 'watershed', 'drainage', 'catchment', 'course']

def score_img(fn):
    fn = fn.lower()
    if any(e in fn for e in EXCLUDE):
        return -1
    if fn.endswith('.svg') or any(x in fn for x in ['icon','flag','logo','blank']):
        return -1
    score = 0
    for p in MAP_PRIORITY:
        if p in fn:
            score += 10
    for k in MAP_KEYWORDS:
        if k in fn:
            score += 1
    return score

def get_best_map(titles):
    """Try multiple article titles, return best map image URL."""
    for title in titles:
        time.sleep(1.5)
        r = requests.get(URL, params={
            'action': 'query', 'titles': title,
            'prop': 'images', 'imlimit': 50, 'format': 'json'
        }, headers=HEADERS, timeout=20)
        if not r.content:
            continue
        pages = r.json().get('query', {}).get('pages', {})
        for p in pages.values():
            imgs = [i['title'] for i in p.get('images', [])]
            scored = [(score_img(i), i) for i in imgs]
            scored = [(s, i) for s, i in scored if s > 0]
            scored.sort(reverse=True)
            if scored:
                print(f'  [{title}] best: {scored[0][1].split(":")[-1][:60]} (score {scored[0][0]})')
                for _, img_title in scored[:5]:
                    url = fetch_thumb(img_title)
                    if url and not url.lower().endswith('.svg'):
                        return url
    return None

def fetch_thumb(file_title, size=400):
    time.sleep(0.8)
    r = requests.get(URL, params={
        'action': 'query', 'titles': file_title,
        'prop': 'imageinfo', 'iiprop': 'url',
        'iiurlwidth': size, 'format': 'json'
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return None
    for p in r.json().get('query', {}).get('pages', {}).values():
        info = p.get('imageinfo', [{}])[0]
        return info.get('thumburl') or info.get('url')
    return None

def save(url, num):
    r = requests.get(url, headers=HEADERS, timeout=20)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img = img.resize((200, 150), Image.LANCZOS)
    path = THUMBS / f'{num}.webp'
    img.save(path, 'WEBP', quality=82)
    return path.stat().st_size

# Entries to redo: bad matches + all failures
REDO = [
    # Bad matches from pass 1
    (1,  'Nil',           ['Nile basin', 'Nile River', 'Nile']),  # got 1619 map
    (3,  'Yangzi',        ['Yangtze', 'Yangtze River basin', 'Three Gorges']),  # got Dongting tributary
    (6,  'Huang He',      ['Yellow River', 'Yellow River basin']),  # got painting
    (28, 'Rhin',          ['Rhine', 'Rhine basin', 'Rhine watershed']),  # got Maas delta

    # Failures
    (7,  'Ob-Irtych',     ['Ob–Irtysh river system', 'Ob River', 'Irtysh', 'West Siberia']),
    (10, 'Amour',         ['Amur', 'Amur River', 'Amur basin', 'Manchuria']),
    (15, 'Volga',         ['Volga', 'Volga River', 'Volga-Ural basin', 'Caspian Sea basin']),
    (16, 'Zambèze',       ['Zambezi', 'Zambezi River', 'Zambezi basin', 'Zambia']),
    (18, 'Euphrate',      ['Euphrates', 'Tigris-Euphrates', 'Mesopotamia', 'Fertile Crescent']),
    (19, 'Tigre',         ['Tigris', 'Tigris-Euphrates river system', 'Mesopotamia']),
    (22, 'Murray',        ['Murray–Darling basin', 'Murray-Darling Basin', 'Murray River']),
    (24, 'Saint-Laurent', ['Saint Lawrence River', 'Great Lakes', 'Saint Lawrence Seaway']),
    (27, 'Orange',        ['Orange River', 'Orange-Vaal system', 'Northern Cape']),
]

for num, name, articles in REDO:
    print(f'\n#{num} {name}')
    url = get_best_map(articles)
    if url:
        try:
            size = save(url, num)
            print(f'  -> Sauvé: {size}B')
        except Exception as e:
            print(f'  ERREUR: {e}')
    else:
        print('  ECHEC')

print('\nDone.')
