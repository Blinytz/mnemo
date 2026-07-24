"""Derniers échecs."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FIXES = [
    ('decouvertes_scientifiques', 4,  'Alphabet',  'Latin alphabet'),
    ('decouvertes_scientifiques', 22, 'Pénicilline','Beta-lactam antibiotic'),
]
for folder, num, name, title in FIXES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, folder, num, name)
    else:
        print(f'  ECHEC')
print('Done.')
