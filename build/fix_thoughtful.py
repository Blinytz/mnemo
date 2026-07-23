"""
Fix images with thoughtful term selection.
For each entry, we ask: what is the MOST ICONIC/RECOGNIZABLE image for this?
"""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs')

# Format: (folder, num, label, ideal_image_description, search_term)
FIXES = [
    # Batailles décisives
    # Marathon : la stèle funéraire ou la représentation de hoplites — pas la ville moderne
    ('batailles_decisives', 1, 'Marathon',
     'Hoplites grecs / stèle tumulus Marathon',
     'Battle of Marathon Greek hoplites Persian Wars 490 BC artwork'),

    # Yarmouk : bataille entre Byzantins et Arabes, cavalerie
    ('batailles_decisives', 13, 'Yarmouk',
     'Cavalerie arabe vs Byzantine 636',
     'Battle of Yarmouk 636 AD Muslim Arab conquest Byzantine'),

    # Leipzig : peinture de la bataille des Nations (pas le monument)
    ('batailles_decisives', 22, 'Leipzig',
     'Peinture battle of Nations 1813 (pas le monument)',
     'Battle of Leipzig 1813 painting Napoleon defeat nations'),

    # La Marne : les fameux taxis de la Marne OU soldats français en attaque 1914
    ('batailles_decisives', 24, 'La Marne',
     'Taxis de la Marne OU soldats français 1914',
     'Battle of Marne 1914 First World War French soldiers attack'),

    # Découvertes scientifiques
    # Evolution : portrait Darwin par John Collier 1881 (LE portrait iconique)
    ('decouvertes_scientifiques', 9, 'Evolution',
     'Portrait Charles Darwin John Collier 1881',
     'Charles Darwin portrait 1881 John Collier naturalist'),

    # Inventions majeures
    # Roue : représentation ancienne, char sumérien d'Ur ou poterie à roue
    ('inventions_majeures', 1, 'Roue',
     'Char sumérien d Ur ou poterie à roue ancienne Mésopotamie',
     'Standard of Ur ancient Sumerian wheel chariot 2600 BC'),
]

def get_img(term):
    time.sleep(2.5)
    r = requests.get(URL, params={
        'action': 'query', 'list': 'search', 'srsearch': term,
        'format': 'json', 'utf8': 1, 'srlimit': 8
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return None
    results = r.json().get('query', {}).get('search', [])
    for res in results:
        time.sleep(1.2)
        r2 = requests.get(URL, params={
            'action': 'query', 'titles': res['title'],
            'prop': 'pageimages', 'pithumbsize': 400,
            'format': 'json'
        }, headers=HEADERS, timeout=20)
        if not r2.content:
            continue
        for p in r2.json().get('query', {}).get('pages', {}).values():
            src = p.get('thumbnail', {}).get('source', '')
            if src and not src.lower().endswith('.svg'):
                print(f'    -> [{res["title"]}] {src[-50:]}')
                return src
    return None

for folder, num, label, ideal, term in FIXES:
    print(f'\n#{num} {label} ({folder})')
    print(f'  Idéal : {ideal}')
    print(f'  Terme : {term}')
    src = get_img(term)
    if src:
        try:
            r = requests.get(src, headers=HEADERS, timeout=20)
            img = Image.open(BytesIO(r.content)).convert('RGB')
            img = img.resize((200, 150), Image.LANCZOS)
            path = THUMBS / folder / f'{num}.webp'
            img.save(path, 'WEBP', quality=82)
            print(f'  Sauvé: {num}.webp ({path.stat().st_size}B)')
        except Exception as e:
            print(f'  ERREUR: {e}')
    else:
        print('  ECHEC')

print('\nDone.')
