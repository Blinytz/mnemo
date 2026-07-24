"""
Détroits : vue satellite/aérienne montrant le PASSAGE entre deux terres.
PAS de drapeaux, PAS de cartes de pays, PAS de logos.
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FOLDER = 'detroits_monde'

# (num, name, english_wiki_title)
DETROITS = [
    (1,  'Gibraltar',         'Strait of Gibraltar'),
    (2,  'Bosphore',          'Bosphorus'),
    (3,  'Dardanelles',       'Dardanelles'),
    (4,  'Ormuz',             'Strait of Hormuz'),
    (5,  'Malacca',           'Strait of Malacca'),
    (6,  'Béring',            'Bering Strait'),
    (7,  'Magellan',          'Strait of Magellan'),
    (8,  'Bab-el-Mandeb',     'Bab-el-Mandeb'),
    (9,  'Pas-de-Calais',     'Dover Strait'),
    (10, 'Messine',           'Strait of Messina'),
    (11, 'Skagerrak',         'Skagerrak'),
    (12, 'Taïwan',            'Taiwan Strait'),
    (13, 'Corée',             'Korea Strait'),
    (14, 'Lombok',            'Lombok Strait'),
    (15, 'Bass',              'Bass Strait'),
    (16, 'Floride',           'Straits of Florida'),
    (17, 'Øresund',           'Øresund'),
    (18, 'Mozambique',        'Mozambique Channel'),
    (19, 'Singapour',         'Singapore Strait'),
    (20, 'Tsugaru',           'Tsugaru Strait'),
]

ok = 0
for num, name, title in DETROITS:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        if save_both(url, FOLDER, num, name):
            ok += 1
    else:
        print(f'  ECHEC')

print(f'\nDone: {ok}/{len(DETROITS)}')
