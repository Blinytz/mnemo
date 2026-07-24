"""Quatrième round."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, get_page_images, save_both

FIXES = [
    ('litterature',  55, 'Isaac Asimov'),
    ('peintres',      6, 'Raphael'),
    ('coupes_monde',  5, 'Switzerland national football team'),
]

for folder, num, title in FIXES:
    print(f'{folder} #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, folder, num, title)
    else: print('  ECHEC')

print('\nDone.')
