"""Fix architectes qui ont échoué — titres alternatifs."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FIXES = [
    (16, 'Niemeyer',   'National Congress of Brazil'),
    (18, 'Renzo Piano', 'Pompidou Centre'),
    (23, 'Koolhaas',   'CCTV Headquarters Beijing'),
    (25, 'Herzog de Meuron', "National Stadium Beijing"),  # Bird's Nest
    (28, 'Scarpa',     'Castelvecchio Museum'),
]
for num, name, title in FIXES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, 'architectes_majeurs', num, name)
    else:
        print(f'  ECHEC')
print('Done.')
