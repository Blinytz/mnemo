"""Fix images for batailles_decisives — use specific battle painting/map terms"""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\thumbs\batailles_decisives')
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
URL_EN = 'https://en.wikipedia.org/w/api.php'

# (num, name, search_term)
TERMS = [
    (1,  'Marathon',          'Battle of Marathon 490 BC Athenians Persians'),
    (2,  'Hastings',          'Battle of Hastings 1066 Bayeux Tapestry Norman conquest'),
    (3,  'Bouvines',          'Battle of Bouvines 1214 medieval painting France'),
    (4,  'Waterloo',          'Battle of Waterloo 1815 Napoleon painting cavalry'),
    (5,  'Verdun',            'Battle of Verdun 1916 WWI trench soldiers'),
    (6,  'Stalingrad',        'Battle of Stalingrad 1942 WWII Soviet Union ruins'),
    (7,  'Midway',            'Battle of Midway 1942 aircraft carrier US Navy Pacific'),
    (8,  'Dien Bien Phu',     'Battle of Dien Bien Phu 1954 French Indochina siege'),
    (9,  'Gaugameles',        'Battle of Gaugamela Alexander the Great Persian Darius'),
    (10, 'Cannae',            'Battle of Cannae 216 BC Hannibal Roman Republic'),
    (11, 'Actium',            'Battle of Actium 31 BC Roman fleet Octavian Antony'),
    (12, 'Chalons',           'Battle of Chalons Attila the Hun 451 AD Roman'),
    (13, 'Yarmouk',           'Battle of Yarmouk 636 Byzantine Arab Muslim conquest'),
    (14, 'Poitiers',          'Battle of Tours Poitiers 732 Charles Martel Arab'),
    (15, 'Lepante',           'Battle of Lepanto 1571 Christian fleet Ottoman'),
    (16, 'Rocroi',            'Battle of Rocroi 1643 French Conde Spanish tercios'),
    (17, 'Poltava',           'Battle of Poltava 1709 Peter the Great Sweden Charles XII'),
    (18, 'Plassey',           'Battle of Plassey 1757 Clive East India Company Bengal'),
    (19, 'Yorktown',          'Battle of Yorktown 1781 American Revolution Cornwallis surrender'),
    (20, 'Valmy',             'Battle of Valmy 1792 French Revolution cannonade'),
    (21, 'Austerlitz',        'Battle of Austerlitz 1805 Napoleon three emperors'),
    (22, 'Leipzig',           'Battle of Leipzig 1813 Nations Napoleon defeat'),
    (23, 'Tsushima',          'Battle of Tsushima 1905 Russian Japanese fleet'),
    (24, 'Marne',             'Battle of the Marne 1914 WWI Western Front France'),
    (25, 'Somme',             'Battle of the Somme 1916 WWI British troops'),
    (26, 'El-Alamein',        'Battle of El Alamein 1942 Montgomery Rommel desert'),
    (27, 'Koursk',            'Battle of Kursk 1943 tank greatest WWII Eastern Front'),
    (28, 'Normandie',         'D-Day Normandy landings 1944 Omaha Beach soldiers'),
    (29, 'Berlin',            'Battle of Berlin 1945 Soviet Red Army Reichstag'),
    (30, 'Inchon',            'Battle of Inchon 1950 Korean War MacArthur landing'),
    (31, 'Kippour',           'Yom Kippur War 1973 tank battle Sinai Egypt Israel'),
    (32, 'Falklands',         'Falklands War 1982 British warship Argentina'),
    (33, 'Golfe Persique',    'Gulf War 1991 Operation Desert Storm tank M1 Abrams'),
]

def get_img(term, url=URL_EN):
    time.sleep(2.5)
    r = requests.get(url, params={'action':'query','list':'search','srsearch':term,'format':'json','utf8':1,'srlimit':5}, headers=HEADERS, timeout=20)
    if not r.content: return None
    for res in r.json().get('query',{}).get('search',[]):
        time.sleep(1.2)
        r2 = requests.get(url, params={'action':'query','titles':res['title'],'prop':'pageimages','pithumbsize':400,'format':'json'}, headers=HEADERS, timeout=20)
        if not r2.content: continue
        for p in r2.json().get('query',{}).get('pages',{}).values():
            src = p.get('thumbnail',{}).get('source','')
            if src and not src.lower().endswith('.svg'):
                print(f'  [{term[:40]}] -> {res["title"]}')
                return src
    return None

for num, label, term in TERMS:
    print(f'#{num} {label}')
    src = get_img(term)
    if src:
        try:
            r = requests.get(src, headers=HEADERS, timeout=20)
            img = Image.open(BytesIO(r.content)).convert('RGB')
            img = img.resize((200, 150), Image.LANCZOS)
            path = THUMBS / f'{num}.webp'
            img.save(path, 'WEBP', quality=82)
            print(f'  -> {path.name} ({path.stat().st_size}B)')
        except Exception as e:
            print(f'  ERREUR save: {e}')
    else:
        print('  ECHEC')

print('\nDone.')
