"""
Fix fleuves_monde images — réflexion systématique par fleuve.
Image idéale = carte du tracé OU vue satellite montrant le cours du fleuve.
PAS des photos de bateaux, de villages au bord, ou de paysages génériques.
"""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
URL_EN = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\thumbs\fleuves_monde')

# (num, fleuve, image_idéale, terme_recherche)
# Pour chaque fleuve : on cherche une carte du tracé, vue satellite ou carte hydrologique
RIVERS = [
    (1,  'Nil',             'Carte ou satellite du Nil traversant Egypte-Soudan',
                             'Nile River map course Egypt Sudan Africa'),
    (2,  'Amazone',         'Bassin amazonien vu depuis satellite ou carte',
                             'Amazon River basin map South America satellite'),
    (3,  'Yangzi Jiang',    'Carte tracé Yangzi à travers Chine',
                             'Yangtze River map course China'),
    (4,  'Mississippi',     'Carte du Mississippi-Missouri depuis les Grands Lacs au golfe',
                             'Mississippi River map watershed United States drainage'),
    (5,  'Ienisseï',        'Carte tracé Ienisseï Sibérie vers l Arctique',
                             'Yenisei River map Siberia Russia Arctic'),
    (6,  'Huang He',        'Carte ou vue du Fleuve Jaune Huang He Chine',
                             'Yellow River Huang He China map course'),
    (7,  'Ob-Irtych',       'Carte du système fluvial Ob-Irtych Sibérie',
                             'Ob River Irtysh River basin map Siberia'),
    (8,  'Paraná',          'Carte Paraná / Río de la Plata Amérique du Sud',
                             'Paraná River map La Plata basin South America'),
    (9,  'Congo',           'Carte bassin Congo Afrique centrale (2e fleuve mondial)',
                             'Congo River basin map Africa drainage'),
    (10, 'Amour',           'Carte Fleuve Amour Sibérie-Chine frontière',
                             'Amur River map China Russia border'),
    (11, 'Léna',            'Carte tracé Léna delta Arctique Sibérie',
                             'Lena River map Siberia delta Arctic satellite'),
    (12, 'Mékong',          'Carte Mékong Asie du Sud-Est Tibet Vietnam delta',
                             'Mekong River map Southeast Asia basin'),
    (13, 'Niger',           'Carte Niger Delta Afrique de l Ouest',
                             'Niger River map West Africa course delta'),
    (14, 'Mackenzie',       'Carte Mackenzie Canada delta Arctique',
                             'Mackenzie River map Canada Arctic delta'),
    (15, 'Volga',           'Carte Volga Russie mer Caspienne plus long Europe',
                             'Volga River map Russia Caspian Sea watershed'),
    (16, 'Zambèze',         'Chutes Victoria OU carte Zambèze Afrique australe',
                             'Zambezi River Victoria Falls aerial photograph'),
    (17, 'Orinoco',         'Carte Orinoco Venezuela Colombie',
                             'Orinoco River map Venezuela Colombia basin'),
    (18, 'Euphrate',        'Carte Euphrate Mésopotamie Irak Syrie',
                             'Euphrates River map Mesopotamia Iraq Syria'),
    (19, 'Tigre',           'Carte Tigre-Euphrate Mésopotamie ancienne',
                             'Tigris River map Mesopotamia Iraq basin'),
    (20, 'Gange',           'Vue satellite delta du Gange OU carte Gange Inde',
                             'Ganges River map India Himalaya Bengal delta'),
    (21, 'Indus',           'Carte Indus Pakistan depuis Himalaya',
                             'Indus River map Pakistan Himalaya basin'),
    (22, 'Murray',          'Carte Murray-Darling Australie bassin fluvial',
                             'Murray River map Australia drainage basin Murray-Darling'),
    (23, 'Danube',          'Carte Danube traversant 10 pays Europe',
                             'Danube River map Europe course countries'),
    (24, 'Saint-Laurent',   'Carte Saint-Laurent Grands Lacs Atlantique Canada',
                             'Saint Lawrence River map Great Lakes Canada Atlantic'),
    (25, 'Colorado',        'Grand Canyon OU carte Colorado fleuve USA Mexique',
                             'Colorado River Grand Canyon aerial photograph'),
    (26, 'Rio Grande',      'Carte Rio Grande USA Mexique frontière',
                             'Rio Grande map United States Mexico border river'),
    (27, 'Orange',          'Carte fleuve Orange Afrique du Sud Namibie',
                             'Orange River map South Africa Namibia'),
    (28, 'Rhin',            'Carte Rhin Alpes à Mer du Nord Europe',
                             'Rhine River map Alps North Sea Europe'),
    (29, 'Sénégal',         'Carte fleuve Sénégal Afrique de l Ouest',
                             'Senegal River map West Africa'),
    (30, 'Irrawaddy',       'Carte Irrawaddy Myanmar Birmanie vers Golfe du Bengale',
                             'Irrawaddy River map Myanmar Burma basin'),
]

def get_img(term):
    time.sleep(2.5)
    r = requests.get(URL_EN, params={
        'action': 'query', 'list': 'search', 'srsearch': term,
        'format': 'json', 'utf8': 1, 'srlimit': 6
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return None
    results = r.json().get('query', {}).get('search', [])
    for res in results:
        time.sleep(1.2)
        r2 = requests.get(URL_EN, params={
            'action': 'query', 'titles': res['title'],
            'prop': 'pageimages', 'pithumbsize': 400,
            'format': 'json'
        }, headers=HEADERS, timeout=20)
        if not r2.content:
            continue
        for p in r2.json().get('query', {}).get('pages', {}).values():
            src = p.get('thumbnail', {}).get('source', '')
            if src and not src.lower().endswith('.svg'):
                print(f'      -> [{res["title"]}]')
                return src
    return None

for num, name, ideal, term in RIVERS:
    print(f'#{num} {name}  [{ideal[:50]}]')
    src = get_img(term)
    if src:
        try:
            r = requests.get(src, headers=HEADERS, timeout=20)
            img = Image.open(BytesIO(r.content)).convert('RGB')
            img = img.resize((200, 150), Image.LANCZOS)
            path = THUMBS / f'{num}.webp'
            img.save(path, 'WEBP', quality=82)
            print(f'      Sauvé: {path.stat().st_size}B')
        except Exception as e:
            print(f'      ERREUR: {e}')
    else:
        print('      ECHEC')
    time.sleep(0.5)

print('\nDone.')
