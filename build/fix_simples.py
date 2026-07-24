"""
Corrections simples : une image par entrée.
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FIXES = [
    # (folder, num, label, wiki_title)
    # Grandes explorations #22 : Hillary et Tenzing → photo de l'expédition Everest 1953
    ('grandes_explorations', 22, 'Hillary et Norgay',
     'Edmund Hillary'),

    # Compositeurs #36 : Henry Purcell → portrait (peinture d'époque)
    ('compositeurs', 36, 'Henry Purcell',
     'Henry Purcell'),

    # Grands scientifiques #38 : James Watson → photo Watson-Crick avec modèle ADN
    ('grands_scientifiques', 38, 'James Watson',
     'James Watson'),

    # Mythologie #59 : Hypérion → représentation du Titan
    ('mythologie', 59, 'Hypérion',
     'Hyperion (mythology)'),

    # XIXe siècle #25 : 1825 première ligne fer → locomotive Stockton-Darlington
    ('xixe', 25, '1825 chemin de fer',
     'Stockton and Darlington Railway'),
]

print('=== FIXES SIMPLES ===')
for folder, num, label, title in FIXES:
    print(f'\n{folder} #{num} {label}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, folder, num, label)
    else:
        print('  ECHEC')

# PlayStation : console physique
print('\n=== CONSOLES ===')
# On cherche le numéro exact de la PlayStation dans les données
# D'après l'ID consoles, les années correspondent, pas les noms
# PlayStation originale = 1994 (japon), entrée #19 ou #20
for num, title in [(19, 'PlayStation (console)'), (20, 'PlayStation (console)')]:
    url = get_thumb_url(title, size=800)
    if url:
        print(f'  PlayStation url trouvé: {url[-50:]}')
        save_both(url, 'consoles', num, 'PlayStation')
        break

print('\nDone.')
