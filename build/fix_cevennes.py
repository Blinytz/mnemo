"""Cévennes : carte → photo de paysage."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Bureau\memo-app\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_page_images, get_file_url, get_thumb_url, save_both
import requests, time

HEADERS = {'User-Agent': 'MemoApp/1.0'}
print('Cévennes - recherche photo paysage')

# Chercher images de la page Cévennes et trouver une photo (pas une carte)
time.sleep(1.5)
r = requests.get('https://en.wikipedia.org/w/api.php', params={
    'action': 'query', 'titles': 'Cévennes National Park',
    'prop': 'images', 'imlimit': 30, 'format': 'json'
}, headers=HEADERS, timeout=20)
imgs = []
for p in r.json().get('query', {}).get('pages', {}).values():
    imgs = [i['title'] for i in p.get('images', [])]

EXCLUDE = ['map', 'carte', 'location', 'svg', 'flag', 'logo', 'icon', 'locator']
GOOD = ['jpg', 'jpeg', 'png', 'webp']

photo_imgs = [i for i in imgs
              if not any(e in i.lower() for e in EXCLUDE)
              and any(i.lower().endswith(g) for g in GOOD)]

print(f'Photos candidates: {[i.split(":")[-1][:40] for i in photo_imgs[:6]]}')

for img in photo_imgs[:8]:
    url = get_file_url(img, 800)
    if url and 'svg' not in url.lower():
        if save_both(url, 'parcs_nationaux', 22, 'Cévennes'):
            print('OK')
            break
else:
    # Fallback sur la page française
    url = get_thumb_url('Cévennes National Park', 800)
    if url:
        save_both(url, 'parcs_nationaux', 22, 'Cévennes')
    else:
        print('ECHEC')
