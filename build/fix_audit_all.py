"""
Fix complet de toutes les images cassées détectées par l'audit.
On ne touche PAS : pays (drapeaux), départements (SVG blasons).
"""
import sys, pathlib
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')

# ── Supprimer les orphelins inventions_majeures full/32-35 ──
for n in [32, 33, 34, 35]:
    for p in (BASE / 'full' / 'inventions_majeures').glob(f'{n}.*'):
        p.unlink(); print(f'Supprimé orphelin: {p.name}')

# ══════════════════════════════════════════════════
#  MANQUANT : thumb exist, full absent
# ══════════════════════════════════════════════════
MANQUANTS = [
    ('civilisations', 25, 'Mughal Empire'),
    ('grandes_explorations', 16, 'Samuel de Champlain'),
    ('grandes_explorations', 18, 'Mungo Park (explorer)'),
    ('grandes_explorations', 25, 'Valentina Tereshkova'),
    ('grands_scientifiques', 16, 'Johannes Kepler'),
]

print('\n=== MANQUANTS ===')
for folder, num, title in MANQUANTS:
    print(f'{folder} #{num}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, folder, num, title.split('(')[0].strip())
    else: print('  ECHEC')

# ══════════════════════════════════════════════════
#  LITTÉRATURE : 31 images full/ cassées
#  Image idéale = couverture ou illustration de l'œuvre
# ══════════════════════════════════════════════════
LIT = [
    (1,  'Iliad'),
    (2,  'Odyssey'),
    (3,  'Aeneid'),
    (4,  'Metamorphoses (Ovid)'),
    (5,  'Divine Comedy'),
    (6,  'Decameron'),
    (8,  'Hamlet'),
    (9,  'Romeo and Juliet'),
    (12, 'Faust (Goethe)'),
    (16, 'The Charterhouse of Parma'),
    (17, 'Père Goriot'),
    (18, 'Madame Bovary'),
    (23, 'Germinal (novel)'),
    (26, 'Wuthering Heights'),
    (29, 'In Search of Lost Time'),
    (30, 'Ulysses (novel)'),
    (31, 'Mrs Dalloway'),
    (32, 'The Magic Mountain'),
    (33, 'The Stranger (Camus novel)'),
    (34, 'Nausea (Sartre)'),
    (35, 'The Trial (novel)'),
    (36, 'The Metamorphosis'),
    (42, 'The Catcher in the Rye'),
    (43, 'On the Road'),
    (44, 'One Hundred Years of Solitude'),
    (46, 'Lolita'),
    (48, 'Beloved (novel)'),
    (49, 'The Name of the Rose'),
    (51, 'The Flowers of Evil'),
    (52, 'Journey to the End of the Night'),
    (53, "Man's Fate"),
    (55, 'Foundation (Asimov)'),
]

print('\n=== LITTÉRATURE ===')
for num, title in LIT:
    print(f'  #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, 'litterature', num, title)
    else: print('    ECHEC')

# ══════════════════════════════════════════════════
#  PEINTRES : 9 images full/ cassées
#  Image = tableau emblématique du peintre
# ══════════════════════════════════════════════════
PEINTRES = [
    (1,  'Ghent Altarpiece'),             # Jan van Eyck
    (6,  'School of Athens'),             # Raphaël
    (7,  'Venus of Urbino'),              # Titien
    (10, 'Elevation of the Cross (Rubens)'), # Rubens
    (12, 'The Night Watch'),              # Rembrandt
    (20, 'The Dance Class'),              # Degas
    (23, 'Bal du moulin de la Galette'),  # Renoir
    (28, 'The Scream'),                   # Munch
    (38, "The Harlequin's Carnival"),     # Miró
]

print('\n=== PEINTRES ===')
for num, title in PEINTRES:
    print(f'  #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, 'peintres', num, title)
    else: print('    ECHEC')

# ══════════════════════════════════════════════════
#  ROIS DE FRANCE : 3 cassés
# ══════════════════════════════════════════════════
ROIS = [
    (2,  'Chlothar I'),    # Clotaire Ier
    (44, 'Charles IV of France'),
    (50, 'Louis XI of France'),
]

print('\n=== ROIS DE FRANCE ===')
for num, title in ROIS:
    print(f'  #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, 'rois_france', num, title)
    else: print('    ECHEC')

# ══════════════════════════════════════════════════
#  LUNES : 4 cassées
# ══════════════════════════════════════════════════
LUNES = [
    (4,  'Metis (moon)'),
    (5,  'Adrastea (moon)'),
    (46, 'Despina (moon)'),
    (51, 'Nereid (moon)'),
]

print('\n=== LUNES ===')
for num, title in LUNES:
    print(f'  #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, 'lunes', num, title)
    else: print('    ECHEC')

# ══════════════════════════════════════════════════
#  DIVERS (chefs_etat, guerres, jo_ete, coupes, consoles)
# ══════════════════════════════════════════════════
DIVERS = [
    ('chefs_etat', 12, 'Eugène Cavaignac'),
    ('chefs_etat', 19, 'Jean Casimir-Perier'),
    ('guerres',    4,  'Punic Wars'),
    ('jo_ete',     17, '1968 Summer Olympics'),
    ('coupes_monde', 5,  '1954 FIFA World Cup'),
    ('coupes_monde', 16, '1998 FIFA World Cup'),
    ('consoles',   2,  'Pong'),
]

print('\n=== DIVERS ===')
for folder, num, title in DIVERS:
    print(f'  {folder} #{num} {title}')
    url = get_thumb_url(title, 800)
    if url: save_both(url, folder, num, title)
    else: print('    ECHEC')

print('\nDone.')
