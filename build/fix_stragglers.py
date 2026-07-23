"""Fix remaining issues: Bosphore, Pas-de-Calais, PlayStation hardware, Hypérion, doublons rois."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, get_file_url, get_page_images, save_both
import pathlib, shutil

BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app')

# ── Détroits manquants ──
print('=== DÉTROITS ──')
for num, name, title in [
    (2,  'Bosphore',     'Bosphorus'),
    (9,  'Pas-de-Calais','Strait of Dover'),
]:
    url = get_thumb_url(title, size=800)
    if not url:
        url = get_thumb_url(title.replace('Strait of ', '') + ' strait', size=800)
    if url:
        save_both(url, 'detroits_monde', num, name)
    else:
        print(f'  #{num} ECHEC')

# ── PlayStation : console hardware ──
print('\n=== PLAYSTATION ──')
# On cherche directement le fichier image de la PS1
for title in ['PlayStation (console)', 'PS1 console', 'Sony PlayStation']:
    imgs = get_page_images(title)
    if imgs:
        console_imgs = [i for i in imgs if any(k in i.lower() for k in
                        ['playstation', 'ps1', 'console', 'hardware', 'psx'])]
        print(f'  [{title}] console imgs: {[i.split(":")[-1][:50] for i in console_imgs[:3]]}')
        for img in console_imgs[:5]:
            url = get_file_url(img, size=800)
            if url and 'svg' not in url.lower():
                if save_both(url, 'consoles', 19, 'PlayStation'):
                    break
        break

# ── Hypérion (mythologie grecque) ──
print('\n=== HYPÉRION ──')
for title in ['Hyperion (mythology)', 'Hyperion (Titan)', 'Titans (mythology)']:
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, 'mythologie', 59, 'Hypérion')
        break

# ── Rois de France : fix 7 doublons ──
print('\n=== ROIS DE FRANCE DOUBLONS ──')
# Le doublon signifie que la 2e image est identique à la 1re.
# On doit replacer la 2e par une image différente.
# Paires: (to_fix_num, name, alternative_search)
DUPS = [
    (12, 'Chilpéric II',     'Chilperic II of Francia'),
    (15, 'Pépin le Bref',    'Pepin the Short'),
    (30, 'Hugues Capet',     'Hugh Capet'),
    (54, 'Henri II de France','Henry II of France'),
    (59, 'Louis XIII',       'Louis XIII of France'),
    (62, 'Louis XVI',        'Louis XVI of France'),
    (66, 'Louis-Philippe Ier','Louis Philippe I'),
]
for num, name, title in DUPS:
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, 'rois_france', num, name)
    else:
        print(f'  #{num} {name}: ECHEC')

print('\nDone.')
