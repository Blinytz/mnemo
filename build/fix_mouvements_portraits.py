"""
Fix mouvements picturaux où j'ai mis des portraits d'artistes au lieu d'œuvres.
On utilise la page Wikipedia du MOUVEMENT (pas de l'artiste) qui montre
toujours une œuvre en image principale.
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FOLDER = 'mouvements_peinture'

# Entrées avec portraits d'artistes → remplacer par page du MOUVEMENT
# ou par la page d'une œuvre spécifique avec son titre exact Wikipedia
FIXES = [
    # #22 Pointillisme - Seurat portrait → Sunday on La Grande Jatte
    (22, 'Pointillisme',          'Pointillism'),
    # #23 Symbolisme - Böcklin portrait → symbolisme comme mouvement
    (23, 'Symbolisme',            'Symbolism (arts)'),
    # #25 Fauvisme - Matisse portrait → page du fauvisme (montre une œuvre)
    (25, 'Fauvisme',              'Fauvism'),
    # #31 De Stijl - Mondrian portrait → page De Stijl (montre Composition)
    (31, 'De Stijl',              'De Stijl'),
    # #34 Expressionnisme abstrait - Pollock portrait → page du mouvement
    (34, 'Expressionnisme abstrait', 'Abstract expressionism'),
    # #38 Hyperréalisme - Chuck Close portrait → page du mouvement
    (38, 'Hyperréalisme',         'Hyperrealism (visual arts)'),
    # #39 Néo-expressionnisme - Basquiat portrait → page du mouvement
    (39, 'Néo-expressionnisme',   'Neo-expressionism'),
]

ok = 0
for num, name, title in FIXES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url and save_both(url, FOLDER, num, name):
        ok += 1
    else:
        print(f'  ECHEC')

print(f'\nDone: {ok}/{len(FIXES)}')
