"""Fix remaining rois doublons and Bosphore."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

print('=== ROIS MANQUANTS ===')
FIXES = [
    ('rois_france', 12, 'Chilpéric II',   'Chilperic II'),
    ('rois_france', 59, 'Louis XIII',     'Louis XIII'),
    ('rois_france', 62, 'Louis XVI',      'Louis XVI'),
    ('detroits_monde', 2, 'Bosphore',     'Bosphorus strait'),
    ('mythologie', 59, 'Hypérion',        'Hyperion'),
]
for folder, num, name, title in FIXES:
    print(f'{folder} #{num} {name}')
    url = get_thumb_url(title, size=800)
    if url:
        save_both(url, folder, num, name)
    else:
        # Try alternate title
        alt = title + ' king' if 'Louis' in title or 'Chilp' in title else title
        url = get_thumb_url(alt, size=800)
        if url:
            save_both(url, folder, num, f'{name} (alt)')
        else:
            print(f'  ECHEC')

print('\nDone.')
