"""Deuxième round : titres alternatifs pour les echecs du round 1."""
import sys, pathlib
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both, get_file_url

BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')

# ══ LITTÉRATURE (échecs round 1) ══
LIT2 = [
    (4,  'Ovid'),                              # Metamorphoses → portrait Ovide + manuscrit
    (6,  'The Decameron'),
    (12, 'Faust, Part One'),
    (34, 'Jean-Paul Sartre'),
    (35, 'The Trial'),
    (44, 'Gabriel García Márquez'),
    (49, 'Umberto Eco'),
    (51, 'Charles Baudelaire'),
    (52, 'Louis-Ferdinand Céline'),
    (53, 'André Malraux'),
    (55, 'Foundation series'),
]
print('=== LITTÉRATURE round 2 ===')
for num, title in LIT2:
    print(f'  #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, 'litterature', num, title)
    else: print('    ECHEC')

# ══ PEINTRES (échecs round 1) ══
PEINTRES2 = [
    (6,  'Raphael (painter)'),     # Raphaël portrait
    (10, 'Peter Paul Rubens'),     # Rubens
    (20, 'Edgar Degas'),           # Degas
]
print('\n=== PEINTRES round 2 ===')
for num, title in PEINTRES2:
    print(f'  #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, 'peintres', num, title)
    else: print('    ECHEC')

# ══ ROIS DE FRANCE ══
print('\n=== ROIS DE FRANCE round 2 ===')
url = get_thumb_url('Louis XI', 800)
if url: save_both(url, 'rois_france', 50, 'Louis XI')
else: print('  ECHEC Louis XI')

# ══ LUNES petites (images trop petites → fallback sur planète hôte) ══
LUNES2 = [
    (4,  'Moons of Jupiter'),        # Metis: carte des lunes de Jupiter
    (5,  'Inner moons of Jupiter'),  # Adrastea
    (46, 'Moons of Neptune'),        # Despina
    (51, 'Nereid (moon)'),           # Nereid: essayer une autre variante
]
print('\n=== LUNES (fallback planète hôte) ===')
for num, title in LUNES2:
    print(f'  #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, 'lunes', num, title)
    else: print('    ECHEC')

# ══ DIVERS (échecs round 1) ══
DIVERS2 = [
    ('chefs_etat', 12, 'Eugène Cavaignac'),
    ('jo_ete',     17, '1968 Summer Olympics'),
    ('coupes_monde', 5,  '1954 FIFA World Cup'),
    ('coupes_monde', 16, '1998 FIFA World Cup'),
]
print('\n=== DIVERS round 2 ===')
DIVERS2_ALTS = [
    ('chefs_etat', 12, 'Louis-Eugène Cavaignac'),
    ('jo_ete',     17, 'Mexico City'),
    ('coupes_monde', 5,  '1954 FIFA World Cup'),
    ('coupes_monde', 16, 'Stade de France'),
]
for folder, num, title in DIVERS2_ALTS:
    print(f'  {folder} #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, folder, num, title)
    else: print('    ECHEC')

print('\nDone.')
