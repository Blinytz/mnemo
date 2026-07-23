"""
Deuxième passe des corrections réfléchies.
"""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs')

# (folder, num, label, ideal, search_term)
# Pour chaque entrée : quelle est L'IMAGE LA PLUS RECONNAISSABLE et PARLANTE ?
FIXES = [
    # Marathon : la page Wikipedia "Battle of Marathon" a une image de vase athénien
    # montrant des hoplites, ou un tableau du 19e siècle
    ('batailles_decisives', 1, 'Marathon',
     'Vase athénien ou peinture néoclassique de la bataille',
     'Battle of Marathon'),

    # Roue : Le Standard d'Ur (mosaïque sumérienne ~2600 av JC) montre des chars à roues
    # C'est LA référence visuelle pour la roue ancienne
    ('inventions_majeures', 1, 'Roue',
     'Standard d Ur mosaïque sumérienne montrant chars à roues',
     'Standard of Ur chariot wheel Sumer'),

    # Leipzig : essayons avec le peintre Lejeune qui a peint cette bataille
    ('batailles_decisives', 22, 'Leipzig',
     'Tableau de la Bataille des Nations (Lejeune ou autre)',
     'Battle of Leipzig painting oil canvas 1813 Napoleon'),
]

def get_img(term, max_results=8):
    time.sleep(2.5)
    r = requests.get(URL, params={
        'action': 'query', 'list': 'search', 'srsearch': term,
        'format': 'json', 'utf8': 1, 'srlimit': max_results
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return None
    results = r.json().get('query', {}).get('search', [])
    print(f'  Résultats: {[x["title"] for x in results[:4]]}')
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
                print(f'  -> [{res["title"]}] {src[-70:]}')
                return src
    return None

for folder, num, label, ideal, term in FIXES:
    print(f'\n#{num} {label} ({folder})')
    print(f'  Idéal : {ideal}')
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
        print('  ECHEC total')

print('\nDone.')
