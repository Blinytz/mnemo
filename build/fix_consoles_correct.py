"""
Fix consoless:
- #19 = Sega Saturn → photo de la console
- #20 = PlayStation → photo de la console hardware
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_file_url, get_thumb_url, save_both

print('#19 Sega Saturn')
url = get_thumb_url('Sega Saturn', size=800)
if url:
    save_both(url, 'consoles', 19, 'Sega Saturn')
else:
    print('  ECHEC Saturn')

print('#20 PlayStation')
url = get_file_url('File:PlayStation-SCPH-1000-with-Controller.png', size=800)
if url:
    save_both(url, 'consoles', 20, 'PlayStation')
else:
    print('  ECHEC PlayStation')
print('Done.')
