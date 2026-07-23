"""Use PlayStation-SCPH-1000-with-Controller.png — la console originale avec manette."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_file_url, save_both

url = get_file_url('File:PlayStation-SCPH-1000-with-Controller.png', size=800)
print(f'url: {url}')
if url:
    save_both(url, 'consoles', 19, 'PlayStation')
