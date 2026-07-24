"""Découvertes #3, #4, #12, #18, #22, #30 — nouveaux titres."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FIXES = [
    (3,  'Écriture',        'Cuneiform'),
    (4,  'Alphabet',        'Phoenician alphabet'),
    (12, 'Électricité',     'Alessandro Volta'),
    (18, 'Électromagn.',    'James Clerk Maxwell'),
    (22, 'Pénicilline',     'Penicillin'),
    (30, 'IA',              'Deep learning'),
]

for num, name, title in FIXES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, 'decouvertes_scientifiques', num, name)
    else:
        print(f'  ECHEC')
print('Done.')
