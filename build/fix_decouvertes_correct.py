"""
Découvertes scientifiques - liste RÉELLE de l'app (24 entrées).
Mise à jour COMPLÈTE thumbs/ ET full/.
Image idéale = la plus visuelle et représentative de la découverte.
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FOLDER = 'decouvertes_scientifiques'

# (num, label, wiki_title)
# Choix : ce qui montre LE MIEUX la découverte (schéma, expérience, artefact)
DECOUVERTES = [
    (1,  'Héliocentrisme',       'Heliocentrism'),               # Schéma soleil au centre
    (2,  'Lois de Kepler',       "Kepler's laws of planetary motion"), # Orbites elliptiques
    (3,  'Circulation sanguine', 'William Harvey'),              # Portrait + schéma
    (4,  'Calcul différentiel',  'Calculus'),                    # Newton/Leibniz, équations
    (5,  'Gravitation univ.',    "Newton's law of universal gravitation"), # Pomme de Newton
    (6,  'Électricité/paratonnerre', 'Lightning rod'),           # Paratonnerre Franklin
    (7,  'Oxygène',              'Oxygen'),                      # Molécule O2
    (8,  'Thermodynamique',      'Thermodynamics'),              # Moteur à vapeur/entropie
    (9,  'Évolution',            'On the Origin of Species'),    # Couverture du livre Darwin
    (10, 'Ondes EM',             'Electromagnetic spectrum'),    # Spectre électromagnétique
    (11, 'Tableau périodique',   'Periodic table'),              # Le tableau lui-même
    (12, 'Rayons X',             'Wilhelm Röntgen'),             # Radiographie main Röntgen
    (13, 'Radioactivité',        'Marie Curie'),                 # Portrait Marie Curie
    (14, 'Relativité restreinte','Special relativity'),          # E=mc², Albert Einstein
    (15, 'Tectonique des plaques','Plate tectonics'),            # Carte des plaques
    (16, 'Mécanique quantique',  'Quantum mechanics'),           # Modèle atomique
    (17, 'Pénicilline',          'Penicillin'),                  # Champignon Penicillium
    (18, 'Fission nucléaire',    'Nuclear fission'),             # Schéma réaction en chaîne
    (19, "Structure de l'ADN",   'DNA'),                         # Double hélice
    (20, 'Big Bang',             'Big Bang'),                    # Timeline / fond diffus
    (21, 'Quarks',               'Quark'),                       # Schéma des quarks
    (22, 'Exoplanètes',          'Exoplanet'),                   # Vue d'artiste
    (23, 'Boson de Higgs',       'Higgs boson'),                 # Événement CMS/CERN
    (24, 'Ondes grav.',          'Gravitational wave'),          # Visualisation LIGO
]

ok = 0
for num, name, title in DECOUVERTES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url and save_both(url, FOLDER, num, name):
        ok += 1
    else:
        print(f'  ECHEC')

print(f'\nDone: {ok}/{len(DECOUVERTES)}')
