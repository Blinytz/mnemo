"""Fix PlayStation: photo de la console hardware, pas du logo."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_page_images, get_file_url, save_both
import requests, time

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'

# Chercher dans la page PlayStation toutes les images de console hardware
title = 'PlayStation (console)'
time.sleep(2)
r = requests.get(URL, params={
    'action': 'query', 'titles': title,
    'prop': 'images', 'imlimit': 50, 'format': 'json'
}, headers=HEADERS, timeout=20)

pages = r.json().get('query', {}).get('pages', {})
all_imgs = []
for p in pages.values():
    all_imgs = [i['title'] for i in p.get('images', [])]

print(f'Toutes les images de la page PlayStation:')
for img in all_imgs:
    print(f'  {img}')

# Prioriser les images avec hardware/console/gray/grey/psone
GOOD_KW = ['scph', 'ps1', 'psx', 'playstation_1', 'playstation1', 'psone',
           'hardware', 'gray', 'grey', 'dtlh', 'original_console', 'platform']
BAD_KW = ['logo', 'svg', 'icon', 'symbol', 'flag', 'controller', 'pad',
          'joystick', 'dualshock']

console_imgs = []
for img in all_imgs:
    fl = img.lower()
    if any(b in fl for b in BAD_KW):
        continue
    if fl.endswith('.svg'):
        continue
    if any(g in fl for g in GOOD_KW):
        console_imgs.insert(0, img)
    elif not any(b in fl for b in ['memory', 'card', 'cable']):
        console_imgs.append(img)

print(f'\nImages candidates (filtrées):')
for img in console_imgs[:10]:
    print(f'  {img}')

# Essayer les 5 premières
for img in console_imgs[:8]:
    url = get_file_url(img, size=800)
    if url and 'svg' not in url.lower():
        print(f'\n→ Essai: {img.split(":")[-1][:60]}')
        if save_both(url, 'consoles', 19, 'PlayStation'):
            print('OK!')
            break
