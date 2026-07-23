"""Fix architectes restants + Bosphore + Hypérion + Auriga constellation."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

# Architectes restants avec titres directs des bâtiments
FIXES = [
    ('architectes_majeurs', 16, 'Niemeyer',       'Oscar Niemeyer'),
    ('architectes_majeurs', 18, 'Renzo Piano',    'Georges Pompidou National Center of Art and Culture'),
    ('architectes_majeurs', 23, 'Rem Koolhaas',   'CCTV Headquarters'),
    ('architectes_majeurs', 25, 'Herzog',          "Beijing National Stadium"),
    # Constellation Cocher
    ('constellations', 29, 'Cocher',              'Auriga (constellation)'),
    # Bosphore détroit
    ('detroits_monde', 2, 'Bosphore',             'Istanbul'),
    # Hypérion
    ('mythologie', 59, 'Hypérion',                'Titan (mythology)'),
]

for folder, num, name, title in FIXES:
    print(f'{folder} #{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, folder, num, name)
    else:
        print(f'  ECHEC')

print('Done.')
