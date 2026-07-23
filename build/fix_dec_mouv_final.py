"""Derniers échecs découvertes + mouvements."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

print('=== DÉCOUVERTES ===')
DEC_FIXES = [
    # #4 Calcul différentiel → Newton ou Leibniz
    (4,  'Calcul différentiel',   'Isaac Newton'),
    # #5 Gravitation → Apple de Newton ou le canon de Newton
    (5,  'Gravitation univ.',     'Newton\'s cannonball'),
    # #8 Thermodynamique trop petit → James Watt ou moteur vapeur
    (8,  'Thermodynamique',       'James Watt'),
    # #17 Pénicilline toujours brisée
    (17, 'Pénicilline',           'Penicillium'),
    # #22 Exoplanètes (936B trop petit) → vue artiste plus visible
    (22, 'Exoplanètes',           'Methods of detecting exoplanets'),
]

for num, name, title in DEC_FIXES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, 'decouvertes_scientifiques', num, name)
    else:
        print(f'  ECHEC')

print('\n=== MOUVEMENTS ===')
MOUV_FIXES = [
    # #23 Symbolisme → L'Île des Morts (page correcte)
    (23, 'Symbolisme',            'The Isle of the Dead (painting)'),
    # #34 Expressionnisme abstrait → Willem de Kooning
    (34, 'Expressionnisme abstrait', 'Willem de Kooning'),
    # #39 Néo-expressionnisme → Georg Baselitz (peintre œuvre reconnaissable)
    (39, 'Néo-expressionnisme',   'Georg Baselitz'),
]

for num, name, title in MOUV_FIXES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, 'mouvements_peinture', num, name)
    else:
        print(f'  ECHEC')

print('\nDone.')
