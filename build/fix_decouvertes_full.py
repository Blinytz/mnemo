"""
Découvertes scientifiques : les miniatures (thumbs/) ont été mises à jour
mais PAS les images agrandies (full/). On redownload tout à 800px.
On utilise les MÊMES titres Wikipedia que pour les thumbs.
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FOLDER = 'decouvertes_scientifiques'

# Titres Wikipedia pour chaque entrée (même ordre que la liste)
DECOUVERTES = [
    (1,  'Feu',                          'Control of fire by early humans'),
    (2,  'Roue',                         'Wheel'),
    (3,  'Écriture',                     'History of writing'),
    (4,  'Alphabet',                     'Alphabet'),
    (5,  'Mathématiques',                'History of mathematics'),
    (6,  'Astronomie antique',           'Ancient astronomy'),
    (7,  'Acier',                        'Steel'),
    (8,  'Boussole',                     'Compass'),
    (9,  'Imprimerie',                   'Printing press'),
    (10, 'Héliocentrisme',               'Heliocentrism'),
    (11, 'Gravitation',                  'Newton\'s law of universal gravitation'),
    (12, 'Électricité',                  'History of electromagnetic theory'),
    (13, 'Machine à vapeur',             'Steam engine'),
    (14, 'Vaccin',                       'Vaccine'),
    (15, 'Photographie',                 'History of photography'),
    (16, 'Évolution',                    'Evolution'),
    (17, 'Tableau périodique',           'Periodic table'),
    (18, 'Électromagnétisme',            'Electromagnetism'),
    (19, 'Radioactivité',                'Radioactive decay'),
    (20, 'Relativité',                   'Theory of relativity'),
    (21, 'Mécanique quantique',          'Quantum mechanics'),
    (22, 'Pénicilline',                  'Penicillin'),
    (23, 'ADN',                          'DNA'),
    (24, 'Transistor',                   'Transistor'),
    (25, 'Lasers',                       'Laser'),
    (26, 'Internet',                     'History of the Internet'),
    (27, 'Séquençage génome',            'Human Genome Project'),
    (28, 'Physique des particules',      'Higgs boson'),
    (29, 'Ondes gravitationnelles',      'Gravitational wave'),
    (30, 'Intelligence artificielle',    'Artificial intelligence'),
]

ok = 0
for num, name, title in DECOUVERTES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url and save_both(url, FOLDER, num, name):
        ok += 1
    else:
        print(f'  ECHEC')

print(f'\nDone: {ok}/{len(DECOUVERTES)}')
