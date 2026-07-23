"""Fix mouvements restants avec portraits."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FOLDER = 'mouvements_peinture'

FIXES = [
    # #23 Symbolisme → L'Île des Morts de Böcklin, page de l'œuvre
    (23, 'Symbolisme',            'The Isle of the Dead (Böcklin)'),
    # #34 Expressionnisme abstrait → Blue Poles de Pollock (domaine public non)
    # Essai via la page du mouvement avec terme plus précis
    (34, 'Expressionnisme abstrait', 'Abstract expressionism in the United States'),
    # #38 Hyperréalisme → page Photorealism qui montre une peinture hyper-réaliste
    (38, 'Hyperréalisme',         'Photorealism'),
    # #39 Néo-expressionnisme → page avec une œuvre visible
    (39, 'Néo-expressionnisme',   'Anselm Kiefer'),
]

for num, name, title in FIXES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url and save_both(url, FOLDER, num, name):
        pass
    else:
        print(f'  ECHEC')
print('Done.')
