"""Dernières corrections ciblées."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, get_page_images, get_file_url, save_both
import requests, time

FIXES = [
    # Mouvements
    ('mouvements_peinture', 40, 'Street Art',      'Graffiti'),
    # Architectes
    ('architectes_majeurs', 18, 'Renzo Piano',      'Beaubourg'),
    # Musées
    ('musees_monde', 5,  'Vatican',               'Sistine Chapel'),
    ('musees_monde', 9,  'Orsay',                 'Orsay'),
    ('musees_monde', 10, 'Pompidou',              'Centre national d\'art et de culture Georges-Pompidou'),
    ('musees_monde', 21, 'Quai Branly',           'Musée du quai Branly'),
    ('musees_monde', 23, 'Nairobi',               'Nairobi National Museum'),
    # Découvertes
    ('decouvertes_scientifiques', 4,  'Alphabet', 'Alphabet'),
    ('decouvertes_scientifiques', 30, 'IA',       'Machine learning'),
]

for folder, num, name, title in FIXES:
    print(f'{folder} #{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, folder, num, name)
    else:
        print(f'  ECHEC')

# Constellation Cocher / Auriga : chercher toutes les images non-SVG de la page
print('\nconstellations #29 Cocher')
HEADERS = {'User-Agent': 'MemoApp/1.0'}
time.sleep(2)
r = requests.get('https://en.wikipedia.org/w/api.php', params={
    'action': 'query', 'titles': 'Auriga (constellation)',
    'prop': 'images', 'imlimit': 50, 'format': 'json'
}, headers=HEADERS, timeout=20)
imgs = []
for p in r.json().get('query', {}).get('pages', {}).values():
    imgs = [i['title'] for i in p.get('images', [])]
non_svg = [i for i in imgs if not i.lower().endswith('.svg') and not 'flag' in i.lower()]
print(f'  Images non-SVG: {[i.split(":")[-1][:40] for i in non_svg[:5]]}')
for img in non_svg[:6]:
    url = get_file_url(img, size=800)
    if url:
        save_both(url, 'constellations', 29, 'Cocher/Auriga')
        break

print('\nDone.')
