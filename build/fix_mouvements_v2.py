"""
Mouvements picturaux : une ŒUVRE représentative du mouvement.
Cohérent : toujours une peinture/œuvre, jamais un portrait d'artiste.
Fix : doublons (fauvisme=cubisme, dadaïsme=néo-expressionnisme=pointillisme),
futurisme (vieille photo russe).
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FOLDER = 'mouvements_peinture'

# (num, movement, wiki_title_of_representative_work)
# Idéal = UN tableau iconique du mouvement, reconnaissable immédiatement
MOUVEMENTS = [
    (1,  'Art rupestre',         'Cave of Altamira'),           # Bisons d'Altamira
    (2,  'Art égyptien',         'Book of the Dead'),           # Papyrus illustré
    (3,  'Art grec antique',     'Parthenon frieze'),           # Frise du Parthénon
    (4,  'Art romain',           'Augustus of Prima Porta'),   # Auguste de Prima Porta
    (5,  'Art byzantin',         'Hagia Sophia'),               # Mosaïque Hagia Sophia
    (6,  'Art roman',            'Bayeux Tapestry'),            # Tapisserie de Bayeux
    (7,  'Art gothique',         'Notre-Dame de Paris'),        # Rose gothique
    (8,  'Primitifs flamands',   'Ghent Altarpiece'),           # Retable de Gand
    (9,  'Quattrocento',         'Birth of Venus'),             # Naissance de Vénus (Botticelli)
    (10, 'Haute Renaissance',    'The Last Supper (Leonardo da Vinci)'), # Cène de Léonard
    (11, 'Maniérisme',           'Madonna with the Long Neck'), # Parmesan
    (12, 'Renaissance nordique', 'Arnolfini Portrait'),         # Jan van Eyck
    (13, 'Baroque',              'The Night Watch'),            # Ronde de nuit Rembrandt
    (14, 'Classicisme français', 'The Oath of the Horatii'),   # Serment des Horaces David
    (15, 'Rococo',               "The Swing (Fragonard)"),      # L'Escarpolette
    (16, 'Néoclassicisme',       'Wanderer above the Sea of Fog'), # Friedrich
    (17, 'Romantisme',           'Liberty Leading the People'), # Delacroix
    (18, 'Réalisme',             'The Gleaners'),               # Les Glaneuses Millet
    (19, 'Préraphaélisme',       'Ophelia (painting)'),         # Millais Ophélia
    (20, 'Impressionnisme',      'Impression, Sunrise'),        # Monet
    (21, 'Post-impressionnisme', 'The Starry Night'),           # Van Gogh
    (22, 'Pointillisme',         'A Sunday on La Grande Jatte'), # Seurat
    (23, 'Symbolisme',           'The Isle of the Dead (painting)'), # Böcklin
    (24, 'Art nouveau',          'The Kiss (Klimt)'),           # Klimt
    (25, 'Fauvisme',             'The Woman with a Hat'),       # Matisse
    (26, 'Expressionnisme',      'The Scream'),                 # Munch
    (27, 'Cubisme',              'Les Demoiselles d\'Avignon'), # Picasso
    (28, 'Futurisme',            'Dynamism of a Dog on a Leash'), # Balla futuriste
    (29, 'Dadaïsme',             'L.H.O.O.Q.'),                # Duchamp Mona Lisa
    (30, 'Constructivisme',      'Beat the Whites with the Red Wedge'), # Lissitzky
    (31, 'De Stijl',             'Composition II in Red, Blue, and Yellow'), # Mondrian
    (32, 'Bauhaus',              'Bauhaus Dessau'),             # Bâtiment Bauhaus
    (33, 'Surréalisme',          'The Persistence of Memory'), # Dalí
    (34, 'Expressionnisme abstrait', "Number 31 (painting)"),  # Pollock drip
    (35, 'Pop Art',              "Campbell's Soup Cans"),      # Warhol
    (36, 'Minimalisme',          'Voice of Fire'),              # Newman
    (37, 'Art conceptuel',       'Fountain (Duchamp)'),        # Duchamp urinoir
    (38, 'Hyperréalisme',        "Close Chuck (1969)"),        # Chuck Close
    (39, 'Néo-expressionnisme',  'Jean-Michel Basquiat'),      # Basquiat
    (40, 'Street Art',           'Balloon Girl (Banksy)'),     # Banksy
    (41, 'Art numérique',        'Everydays: the First 5000 Days'), # Beeple NFT
]

ok = 0
for num, name, title in MOUVEMENTS:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url and save_both(url, FOLDER, num, name):
        ok += 1
    else:
        print(f'  ECHEC')

print(f'\nDone: {ok}/{len(MOUVEMENTS)}')
