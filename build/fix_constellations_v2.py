"""
Constellations : images complètement refaites.
Image idéale = schéma d'agencement des étoiles (fond noir, étoiles et lignes).
On utilise les noms ANGLAIS des articles Wikipedia pour éviter les homonymes français
(Aigle = Eagle bird, Lyre = instrument, Cancer = maladie, etc.)
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
import requests, time
from lib_img import get_thumb_url, get_file_url, get_page_images, save_both

FOLDER = 'constellations'
CHART_KW = ['iau', 'constellation', 'chart', 'stars', 'starfield', 'sky', 'map', 'figure']
EXCLUDE = ['mythology', 'myth', 'zodiac_sign', 'symbol', 'glyph', 'tarot',
           'horoscope', 'astrology', 'sign', 'drawing', 'illustration_of']

# (num, French name, English Wikipedia title, fallback titles)
CONSTELLATIONS = [
    (1,  'Orion',            'Orion (constellation)',       ['Orion (constellation)']),
    (2,  'Grande Ourse',     'Ursa Major',                  ['Ursa Major']),
    (3,  'Petite Ourse',     'Ursa Minor',                  ['Ursa Minor']),
    (4,  'Cassiopée',        'Cassiopeia (constellation)',  ['Cassiopeia (constellation)']),
    (5,  'Cygne',            'Cygnus (constellation)',      ['Cygnus (constellation)']),
    (6,  'Lyre',             'Lyra',                        ['Lyra constellation']),
    (7,  'Aigle',            'Aquila (constellation)',      ['Aquila (constellation)']),
    (8,  'Scorpion',         'Scorpius',                    ['Scorpius constellation']),
    (9,  'Sagittaire',       'Sagittarius (constellation)', ['Sagittarius (constellation)']),
    (10, 'Taureau',          'Taurus (constellation)',      ['Taurus (constellation)']),
    (11, 'Gémeaux',          'Gemini (constellation)',      ['Gemini (constellation)']),
    (12, 'Lion',             'Leo (constellation)',          ['Leo (constellation)']),
    (13, 'Persée',           'Perseus (constellation)',     ['Perseus (constellation)']),
    (14, 'Andromède',        'Andromeda (constellation)',   ['Andromeda (constellation)']),
    (15, 'Hercule',          'Hercules (constellation)',    ['Hercules (constellation)']),
    (16, 'Vierge',           'Virgo (constellation)',       ['Virgo (constellation)']),
    (17, 'Balance',          'Libra (constellation)',       ['Libra (constellation)']),
    (18, 'Verseau',          'Aquarius (constellation)',    ['Aquarius (constellation)']),
    (19, 'Bélier',           'Aries (constellation)',       ['Aries (constellation)']),
    (20, 'Cancer',           'Cancer (constellation)',      ['Cancer (constellation)']),
    (21, 'Capricorne',       'Capricornus',                 ['Capricornus constellation']),
    (22, 'Poissons',         'Pisces (constellation)',      ['Pisces (constellation)']),
    (23, 'Centaure',         'Centaurus',                   ['Centaurus constellation']),
    (24, 'Croix du Sud',     'Crux',                        ['Crux constellation']),
    (25, 'Dragon',           'Draco (constellation)',       ['Draco (constellation)']),
    (26, 'Pégase',           'Pegasus (constellation)',     ['Pegasus (constellation)']),
    (27, 'Grand Chien',      'Canis Major',                 ['Canis Major constellation']),
    (28, 'Petit Chien',      'Canis Minor',                 ['Canis Minor constellation']),
    (29, 'Cocher',           'Auriga (constellation)',      ['Auriga (constellation)']),
    (30, 'Bouvier',          'Boötes',                      ['Bootes constellation']),
    (31, 'Couronne boréale', 'Corona Borealis',             ['Corona Borealis constellation']),
    (32, 'Ophiuchus',        'Ophiuchus',                   ['Ophiuchus constellation']),
    (33, 'Hydre',            'Hydra (constellation)',       ['Hydra (constellation)']),
    (34, 'Éridain',          'Eridanus (constellation)',    ['Eridanus (constellation)']),
    (35, 'Corbeau',          'Corvus (constellation)',      ['Corvus (constellation)']),
    (36, 'Lièvre',           'Lepus (constellation)',       ['Lepus (constellation)']),
    (37, 'Phénix',           'Phoenix (constellation)',     ['Phoenix (constellation)']),
    (38, 'Serpent',          'Serpens',                     ['Serpens constellation']),
]

def best_constellation_img(title):
    """Get best star-chart image from a constellation Wikipedia page."""
    imgs = get_page_images(title)
    if not imgs:
        return None
    # Score: prefer IAU charts, star fields, avoid mythology art
    def score(fn):
        fl = fn.lower()
        if any(e in fl for e in EXCLUDE):
            return -1
        s = 0
        for k in ['iau', 'constellation', 'stars', 'starfield', 'cc.jpg', 'cc.png']:
            if k in fl: s += 10
        for k in ['chart', 'sky', 'map', 'figure']:
            if k in fl: s += 3
        # Prefer images with the constellation name in them
        if title.split('(')[0].strip().lower().replace('ö','o') in fl:
            s += 5
        return s
    scored = [(score(i), i) for i in imgs if score(i) >= 0]
    scored.sort(reverse=True)
    if not scored:
        return None
    for _, img_title in scored[:8]:
        url = get_file_url(img_title, size=800)
        if url and not url.lower().endswith('.svg'):
            return url
    return None

ok = 0
for num, fr_name, en_title, fallbacks in CONSTELLATIONS:
    print(f'#{num} {fr_name}')
    url = best_constellation_img(en_title)
    if not url:
        # Fallback: direct page thumbnail
        url = get_thumb_url(en_title, size=800)
    if url:
        if save_both(url, FOLDER, num, fr_name):
            ok += 1
    else:
        print(f'  ECHEC')

print(f'\nDone: {ok}/{len(CONSTELLATIONS)}')
