"""Corrections finales ciblées par nom de fichier exact."""
import sys, requests, time, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'
THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\fleuves_monde')

TARGETS = [
    (3,  'File:Yangtze river map.png'),                  # Carte du Yangzi exact
    (16, 'File:ISS009-E-7622- Zambezi river near Mongu.jpg'),  # Vue ISS du Zambèze
    (18, 'File:Euphrates River.jpg'),                    # Photo fleuve Euphrate (pas de carte dispo)
    (19, 'File:TigrisRiver.JPG'),                        # Photo fleuve Tigre (pas de carte dispo)
    (27, 'File:OrangeRiver L7 11apr01.jpg'),             # Landsat du fleuve Orange
    (28, 'File:Map of the annual average discharge of Rhine and Maas 2000-2011 (EN).png'),  # Carte Rhin
]

def fetch_thumb(file_title, size=400):
    time.sleep(1.5)
    r = requests.get(URL, params={
        'action': 'query', 'titles': file_title,
        'prop': 'imageinfo', 'iiprop': 'url',
        'iiurlwidth': size, 'format': 'json'
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return None
    for p in r.json().get('query', {}).get('pages', {}).values():
        info = p.get('imageinfo', [{}])[0]
        return info.get('thumburl') or info.get('url')
    return None

for num, file_title in TARGETS:
    print(f'#{num} {file_title.split(":")[-1][:60]}')
    url = fetch_thumb(file_title)
    if url and not url.lower().endswith('.svg'):
        print(f'  url: {url[-60:]}')
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            img = Image.open(BytesIO(r.content)).convert('RGB')
            img = img.resize((200, 150), Image.LANCZOS)
            path = THUMBS / f'{num}.webp'
            img.save(path, 'WEBP', quality=82)
            print(f'  Sauvé: {path.stat().st_size}B')
        except Exception as e:
            print(f'  ERREUR: {e}')
    else:
        print(f'  ECHEC (url={url})')

print('\nDone.')
