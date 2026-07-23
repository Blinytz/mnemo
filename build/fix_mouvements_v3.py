"""
Fix mouvements échoués - titres alternatifs avec images libres de droits.
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FOLDER = 'mouvements_peinture'

# Alternatives libres de droits pour les tableaux sous copyright
FIXES = [
    # Art grec - Frise du Parthénon → bas-reliefs du musée de l'Acropole
    (3,  'Art grec antique',     'Parthenon'),
    # Quattrocento - Naissance de Vénus public domain
    (9,  'Quattrocento',         'The Birth of Venus'),
    # Haute Renaissance - La Cène de Léonard
    (10, 'Haute Renaissance',    'The Last Supper'),
    # Classicisme - David peintre, pas l'Oath qui échoue
    (14, 'Classicisme français', 'Jacques-Louis David'),
    # Pointillisme - Seurat Grande Jatte (domaine public)
    (22, 'Pointillisme',         'Georges Seurat'),
    # Symbolisme - Arnold Böcklin Isle of the Dead
    (23, 'Symbolisme',           'Arnold Böcklin'),
    # Fauvisme - Matisse peintre
    (25, 'Fauvisme',             'Henri Matisse'),
    # De Stijl - Mondrian peintre
    (31, 'De Stijl',             'Piet Mondrian'),
    # Surréalisme - Salvador Dalí
    (33, 'Surréalisme',          'Surrealism'),
    # Expressionnisme abstrait - Jackson Pollock
    (34, 'Expressionnisme abstrait', 'Jackson Pollock'),
    # Minimalisme - Donald Judd sculpture
    (36, 'Minimalisme',          'Minimalism'),
    # Hyperréalisme - Chuck Close
    (38, 'Hyperréalisme',        'Chuck Close'),
    # Street Art - Banksy art
    (40, 'Street Art',           'Banksy'),
    # Art numérique - Digital art
    (41, 'Art numérique',        'Digital art'),
]

for num, name, title in FIXES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, FOLDER, num, name)
    else:
        print(f'  ECHEC')

print('Done.')
