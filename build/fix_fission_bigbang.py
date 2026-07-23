"""Corrige Fission nucléaire (#16) et Big Bang (#18) dans decouvertes_scientifiques."""
import sys, pathlib, requests, time
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs\decouvertes_scientifiques')
HEADERS = {'User-Agent': 'memo-app-fix/1.0'}

def wiki_image(terms, lang='en', skip_exts=('.svg',)):
    url = f'https://{lang}.wikipedia.org/w/api.php'
    for term in terms:
        time.sleep(2)
        try:
            r = requests.get(url, params={
                'action': 'query', 'list': 'search', 'srsearch': term,
                'format': 'json', 'utf8': 1, 'srlimit': 5
            }, headers=HEADERS, timeout=15)
            for result in r.json().get('query', {}).get('search', []):
                title = result['title']
                time.sleep(1)
                r2 = requests.get(url, params={
                    'action': 'query', 'titles': title,
                    'prop': 'pageimages', 'pithumbsize': 400,
                    'format': 'json'
                }, headers=HEADERS, timeout=15)
                pages = r2.json().get('query', {}).get('pages', {})
                for p in pages.values():
                    src = p.get('thumbnail', {}).get('source', '')
                    if src and not any(src.lower().endswith(e) for e in skip_exts):
                        print(f"  [{term}] → {title}")
                        return src
        except Exception as e:
            print(f"  Erreur: {e}")
    return None

def save(url, path):
    r = requests.get(url, headers=HEADERS, timeout=15)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img = img.resize((200, 150), Image.LANCZOS)
    img.save(path, 'WEBP', quality=82)
    sz = path.stat().st_size
    print(f"  → {path.name} ({sz} bytes)")

# #16 Fission nucléaire
print("#16 Fission nucléaire")
src = wiki_image([
    'Nuclear fission chain reaction diagram',
    'Hahn Strassmann nuclear fission 1938',
    'Uranium fission atomic bomb Manhattan',
], 'en')
if src: save(src, THUMBS / '16.webp')

time.sleep(3)

# #18 Big Bang preuves
print("\n#18 Big Bang preuves")
src = wiki_image([
    'Cosmic microwave background radiation Planck',
    'CMB cosmic microwave background map',
    'Penzias Wilson cosmic background radiation 1964',
], 'en')
if src: save(src, THUMBS / '18.webp')

print("\nDone.")
