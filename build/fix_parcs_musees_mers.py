"""
Parcs nationaux : photos de paysage/faune du parc (pas des portraits de personnes)
Musées : photos EXTÉRIEURES du bâtiment
Mers/Océans : cartes ou vues satellite montrant l'étendue d'eau
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

# ── PARCS NATIONAUX ──
PARCS = [
    (1,  'Yellowstone',             'Yellowstone National Park'),
    (2,  'Yosemite',                'Yosemite National Park'),
    (3,  'Banff',                   'Banff National Park'),
    (4,  'Kruger',                  'Kruger National Park'),
    (5,  'Serengeti',               'Serengeti National Park'),
    (6,  'Torres del Paine',        'Torres del Paine National Park'),
    (7,  'Fiordland',               'Fiordland National Park'),
    (8,  'Kakadu',                  'Kakadu National Park'),
    (9,  'Grand Canyon',            'Grand Canyon National Park'),
    (10, 'Galápagos',               'Galápagos National Park'),
    (11, 'Iguaçu',                  'Iguazu National Park'),
    (12, 'Everglades',              'Everglades National Park'),
    (13, 'Grande Barrière',         'Great Barrier Reef Marine Park'),
    (14, 'Vanoise',                 'Vanoise National Park'),
    (15, 'Grand Paradis',           'Gran Paradiso National Park'),
    (16, 'Virunga',                 'Virunga National Park'),
    (17, 'Sagarmatha',              'Sagarmatha National Park'),
    (18, 'Jiuzhaigou',              'Jiuzhaigou National Park'),
    (19, 'Sundarbans',              'Sundarbans National Park'),
    (20, 'Kaziranga',               'Kaziranga National Park'),
    (21, 'Denali',                  'Denali National Park and Preserve'),
    (22, 'Cévennes',                'Parc national des Cévennes'),
    (23, 'Pyrénées',                'Pyrenees National Park'),
    (24, 'Pantanal',                'Pantanal Matogrossense National Park'),
    (25, 'Okavango',                'Okavango Delta'),
    (26, 'Białowieża',              'Białowieża National Park'),
    (27, 'Simien',                  'Simien Mountains National Park'),
    (28, 'Bwindi',                  'Bwindi Impenetrable National Park'),
    (29, 'Wrangell-Saint-Élias',    'Wrangell–St. Elias National Park and Preserve'),
    (30, 'Dolomites',               'Dolomites'),
]

# ── MUSÉES (photos extérieures) ──
MUSEES = [
    (1,  'Louvre',             'Louvre'),
    (2,  'Met New York',       'Metropolitan Museum of Art'),
    (3,  'Prado',              'Museo del Prado'),
    (4,  'British Museum',     'British Museum'),
    (5,  'Musées du Vatican',  'Vatican Museums'),
    (6,  'Offices Florence',   'Uffizi'),
    (7,  'MoMA',               'Museum of Modern Art'),
    (8,  'Ermitage',           'Hermitage Museum'),
    (9,  'Orsay',              "Musée d'Orsay"),
    (10, 'Pompidou',           'Centre Georges Pompidou'),
    (11, 'Rijksmuseum',        'Rijksmuseum'),
    (12, 'Van Gogh',           'Van Gogh Museum'),
    (13, 'Kunsthistorisches',  'Kunsthistorisches Museum'),
    (14, 'Musée national Chine','National Museum of China'),
    (15, 'Smithsonian',        'Smithsonian Institution'),
    (16, 'Acropole',           'Acropolis Museum'),
    (17, 'Egyptien Caire',     'Egyptian Museum'),
    (18, 'Antropologia Mexico','National Museum of Anthropology'),
    (19, 'Tate Modern',        'Tate Modern'),
    (20, 'Guggenheim Bilbao',  'Guggenheim Museum Bilbao'),
    (21, 'Quai Branly',        "Musée du quai Branly–Jacques Chirac"),
    (22, 'Tokyo National',     'Tokyo National Museum'),
    (23, 'Nairobi National',   'Nairobi National Museum'),
    (24, 'Bargello',           'Bargello'),
    (25, 'Rodin',              'Musée Rodin'),
]

# ── MERS ET OCÉANS ──
MERS = [
    (1,  'Océan Pacifique',          'Pacific Ocean'),
    (2,  'Océan Atlantique',         'Atlantic Ocean'),
    (3,  'Océan Indien',             'Indian Ocean'),
    (4,  'Océan Arctique',           'Arctic Ocean'),
    (5,  'Mer Méditerranée',         'Mediterranean Sea'),
    (6,  'Mer des Caraïbes',         'Caribbean Sea'),
    (7,  'Mer Rouge',                'Red Sea'),
    (8,  'Mer Baltique',             'Baltic Sea'),
    (9,  'Océan Austral',            'Southern Ocean'),
    (10, 'Mer de Chine méridionale', 'South China Sea'),
    (11, 'Mer de Corail',            'Coral Sea'),
    (12, 'Mer de Tasman',            'Tasman Sea'),
    (13, "Mer d'Arabie",             'Arabian Sea'),
    (14, "Mer d'Oman",               'Gulf of Oman'),
    (15, 'Golfe du Mexique',         'Gulf of Mexico'),
    (16, 'Golfe Persique',           'Persian Gulf'),
    (17, 'Mer du Nord',              'North Sea'),
    (18, 'Mer Noire',                'Black Sea'),
    (19, 'Mer Caspienne',            'Caspian Sea'),
    (20, 'Mer Égée',                 'Aegean Sea'),
]

print('=== PARCS NATIONAUX ===')
ok_p = 0
for num, name, title in PARCS:
    url = get_thumb_url(title, size=800)
    if url and save_both(url, 'parcs_nationaux', num, name):
        ok_p += 1
    else:
        print(f'  #{num} {name}: ECHEC')
print(f'Parcs: {ok_p}/{len(PARCS)}')

print('\n=== MUSÉES ===')
ok_m = 0
for num, name, title in MUSEES:
    url = get_thumb_url(title, size=800)
    if url and save_both(url, 'musees_monde', num, name):
        ok_m += 1
    else:
        print(f'  #{num} {name}: ECHEC')
print(f'Musées: {ok_m}/{len(MUSEES)}')

print('\n=== MERS ET OCÉANS ===')
ok_mer = 0
for num, name, title in MERS:
    url = get_thumb_url(title, size=800)
    if url and save_both(url, 'mers_oceans', num, name):
        ok_mer += 1
    else:
        print(f'  #{num} {name}: ECHEC')
print(f'Mers: {ok_mer}/{len(MERS)}')

print('\nDone.')
