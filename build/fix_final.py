"""
Fix final : tout ce qui reste.
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FIXES = [
    # Mouvements
    ('mouvements_peinture', 10, 'Haute Renaissance',  'Leonardo da Vinci'),
    ('mouvements_peinture', 40, 'Street Art',         'Street art'),
    # Architectes
    ('architectes_majeurs', 18, 'Renzo Piano',        'Pompidou Centre'),
    # Constellation Cocher/Auriga
    ('constellations', 29, 'Cocher',                  'Capella (star)'),  # Étoile principale d'Auriga
    # Mythologie Hypérion
    ('mythologie', 59, 'Hypérion Titan',               'Greek mythology'),
    # Parcs manquants
    ('parcs_nationaux', 11, 'Iguaçu',                  'Iguazu Falls'),
    ('parcs_nationaux', 18, 'Jiuzhaigou',               'Jiuzhaigou'),
    ('parcs_nationaux', 22, 'Cévennes',                 'Cévennes'),
    ('parcs_nationaux', 23, 'Pyrénées',                 'Pyrenees'),
    # Musées manquants
    ('musees_monde', 5,  'Vatican',                    'Vatican Museums'),
    ('musees_monde', 9,  'Orsay',                      'Musée d\'Orsay'),
    ('musees_monde', 10, 'Pompidou musée',             'Centre Pompidou'),
    ('musees_monde', 18, 'Mexico Antropologia',        'National Museum of Anthropology (Mexico)'),
    ('musees_monde', 21, 'Quai Branly',                "Musée du quai Branly"),
    ('musees_monde', 23, 'Nairobi National',           'Nairobi National Museum'),
    # Découvertes
    ('decouvertes_scientifiques', 3,  'Écriture',       'Cuneiform'),
    ('decouvertes_scientifiques', 4,  'Alphabet',        'Phoenician alphabet'),
    ('decouvertes_scientifiques', 6,  'Astronomie ant.', 'Antikythera mechanism'),
    ('decouvertes_scientifiques', 11, 'Gravitation',     'Gravity'),
    ('decouvertes_scientifiques', 12, 'Électricité',     'Benjamin Franklin'),
    ('decouvertes_scientifiques', 18, 'Électromagn.',    'Michael Faraday'),
    ('decouvertes_scientifiques', 22, 'Pénicilline',     'Alexander Fleming'),
    ('decouvertes_scientifiques', 30, 'IA',              'Artificial neural network'),
]

ok = 0
for folder, num, name, title in FIXES:
    print(f'{folder} #{num} {name}')
    url = get_thumb_url(title, size=800)
    if url and save_both(url, folder, num, name):
        ok += 1
    else:
        print(f'  ECHEC')

print(f'\nDone: {ok}/{len(FIXES)}')
