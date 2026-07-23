"""
Fix fleuves_monde : on veut des CARTES (tracé du fleuve), pas des photos.
Stratégie : récupérer TOUTES les images d'un article Wikipedia,
filtrer celles dont le nom contient map/basin/course/watershed/drainage/locator,
prendre la première en PNG/JPG non-SVG.
Fallback : chercher "[River] basin" ou "[River] watershed" article.
"""
import sys, requests, time, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\fleuves_monde')

MAP_KEYWORDS = ['map', 'basin', 'course', 'watershed', 'drainage', 'locator', 'location',
                'route', 'river_system', 'catchment', 'tributary', 'delta', 'carte']

def is_map_image(filename):
    fn = filename.lower()
    return any(k in fn for k in MAP_KEYWORDS)

def get_all_images(title, thumb_size=400):
    """Récupère toutes les images d'une page Wikipedia, filtre les cartes."""
    time.sleep(1.5)
    r = requests.get(URL, params={
        'action': 'query', 'titles': title,
        'prop': 'images', 'imlimit': 50,
        'format': 'json'
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return []
    pages = r.json().get('query', {}).get('pages', {})
    imgs = []
    for p in pages.values():
        imgs = [i['title'] for i in p.get('images', [])]

    # Filter map images, exclude SVG and icons
    map_imgs = [i for i in imgs
                if is_map_image(i)
                and not i.lower().endswith('.svg')
                and not any(x in i.lower() for x in ['icon', 'flag', 'logo', 'blank', 'commons'])]

    # Also collect non-map raster images as fallback
    photo_imgs = [i for i in imgs
                  if not i.lower().endswith('.svg')
                  and not any(x in i.lower() for x in ['icon', 'flag', 'logo', 'blank'])
                  and i not in map_imgs]

    return map_imgs, photo_imgs

def fetch_thumb(file_title, size=400):
    """Fetch thumbnail URL for a File: title."""
    time.sleep(1)
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

def download_save(url, path):
    r = requests.get(url, headers=HEADERS, timeout=20)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img = img.resize((200, 150), Image.LANCZOS)
    img.save(path, 'WEBP', quality=82)
    return path.stat().st_size

# (num, name, wiki_article, fallback_articles)
RIVERS = [
    (1,  'Nil',           'Nile',                  ['Nile basin', 'Nile River']),
    (2,  'Amazone',       'Amazon River',           ['Amazon basin', 'Amazon drainage basin']),
    (3,  'Yangzi',        'Yangtze',                ['Yangtze River basin', 'Chang Jiang']),
    (4,  'Mississippi',   'Mississippi River',      ['Mississippi River watershed', 'Missouri River basin']),
    (5,  'Ienisseï',      'Yenisei',                ['Yenisei River', 'Yenisei basin']),
    (6,  'Huang He',      'Yellow River',           ['Yellow River basin', 'Huang He']),
    (7,  'Ob-Irtych',     'Ob River',               ['Ob basin', 'Irtysh River']),
    (8,  'Paraná',        'Paraná River',           ['La Plata basin', 'Río de la Plata Basin']),
    (9,  'Congo',         'Congo River',            ['Congo Basin', 'Congo River basin']),
    (10, 'Amour',         'Amur River',             ['Amur basin', 'Amur watershed']),
    (11, 'Léna',          'Lena River',             ['Lena basin', 'Lena delta']),
    (12, 'Mékong',        'Mekong',                 ['Mekong River', 'Mekong basin']),
    (13, 'Niger',         'Niger River',            ['Niger basin', 'Niger drainage basin']),
    (14, 'Mackenzie',     'Mackenzie River',        ['Mackenzie River basin', 'Mackenzie watershed']),
    (15, 'Volga',         'Volga River',            ['Volga basin', 'Volga drainage basin']),
    (16, 'Zambèze',       'Zambezi River',          ['Zambezi basin', 'Zambezi watershed']),
    (17, 'Orinoco',       'Orinoco',                ['Orinoco basin', 'Orinoco River']),
    (18, 'Euphrate',      'Euphrates',              ['Euphrates River', 'Tigris-Euphrates river system']),
    (19, 'Tigre',         'Tigris',                 ['Tigris River', 'Tigris-Euphrates']),
    (20, 'Gange',         'Ganges',                 ['Ganges basin', 'Ganges River']),
    (21, 'Indus',         'Indus River',            ['Indus basin', 'Indus watershed']),
    (22, 'Murray',        'Murray River',           ['Murray-Darling basin', 'Murray-Darling Basin']),
    (23, 'Danube',        'Danube',                 ['Danube basin', 'Danube watershed']),
    (24, 'Saint-Laurent', 'Saint Lawrence River',   ['Great Lakes-Saint Lawrence River basin']),
    (25, 'Colorado',      'Colorado River',         ['Colorado River basin', 'Colorado watershed']),
    (26, 'Rio Grande',    'Rio Grande',             ['Rio Grande basin', 'Rio Grande watershed']),
    (27, 'Orange',        'Orange River',           ['Orange River basin', 'Orange-Vaal basin']),
    (28, 'Rhin',          'Rhine',                  ['Rhine basin', 'Rhine watershed']),
    (29, 'Sénégal',       'Senegal River',          ['Senegal River basin']),
    (30, 'Irrawaddy',     'Irrawaddy River',        ['Irrawaddy basin', 'Irrawaddy drainage']),
]

success = 0
for num, name, main_article, fallbacks in RIVERS:
    print(f'\n#{num} {name}')
    found_url = None

    # Try main article first
    for article in [main_article] + fallbacks:
        map_imgs, photo_imgs = get_all_images(article)
        print(f'  [{article}] maps:{len(map_imgs)} photos:{len(photo_imgs)}')
        if map_imgs:
            print(f'    Maps: {[m.split(":")[-1][:50] for m in map_imgs[:3]]}')
            # Try first map image
            for mi in map_imgs[:5]:
                url = fetch_thumb(mi)
                if url and not url.lower().endswith('.svg'):
                    found_url = url
                    print(f'    -> {mi.split(":")[-1][:60]}')
                    break
        if found_url:
            break

    # Last resort: use photo
    if not found_url and photo_imgs:
        url = fetch_thumb(photo_imgs[0])
        if url:
            found_url = url
            print(f'  FALLBACK photo: {photo_imgs[0].split(":")[-1][:50]}')

    if found_url:
        try:
            size = download_save(found_url, THUMBS / f'{num}.webp')
            print(f'  Sauvé: {size}B')
            success += 1
        except Exception as e:
            print(f'  ERREUR: {e}')
    else:
        print(f'  ECHEC total')

print(f'\nDone: {success}/30')
