"""Troisième round : derniers échecs."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FIXES = [
    ('litterature',  55, 'Foundation (novel)'),
    ('peintres',      6, 'Raffaello Sanzio'),
    ('lunes',         5, 'Amalthea (moon)'),     # fallback: Amalthée proche d'Adrastée
    ('lunes',        51, 'Triton (moon)'),        # fallback: Triton, lune phare Neptune
    ('coupes_monde',  5, 'Wankdorfstadion'),      # stade 1954 Suisse
]

for folder, num, title in FIXES:
    print(f'{folder} #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, folder, num, title)
    else: print('  ECHEC')

print('\nDone.')
