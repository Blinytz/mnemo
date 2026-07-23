"""Fix anesthésie #21 et cinéma #27 : éviter les SVG."""
import sys, pathlib, requests, time
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\thumbs')
HEADERS = {'User-Agent': 'memo-app-fix/1.0'}

def wiki_image_jpg(search_terms, lang='en', skip_exts=('.svg',)):
    url = f'https://{lang}.wikipedia.org/w/api.php'
    for term in search_terms:
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
                    low = src.lower()
                    if src and not any(low.endswith(e) for e in skip_exts):
                        print(f"  [{term}] → {title} ({src[-40:]})")
                        return src
        except Exception as e:
            print(f"  Erreur: {e}")
    return None

def save(url, path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200, 150), Image.LANCZOS)
        img.save(path, 'WEBP', quality=82)
        print(f"  → {path.name} OK")
    except Exception as e:
        print(f"  Erreur: {e}")

# #21 Anesthésie
print("[inventions] #21 Anesthésie")
src = wiki_image_jpg(['Ether anesthesia operation 19th century', 'William Morton ether 1846', 'Sulphuric ether anesthesia'], 'en')
if src: save(src, THUMBS / 'inventions_majeures' / '21.webp')

time.sleep(3)

# #27 Cinéma
print("\n[inventions] #27 Cinéma")
src = wiki_image_jpg(['Cinematograph Lumiere brothers film 1895', 'Cinematographe device 1895', 'First film screening history'], 'en')
if src: save(src, THUMBS / 'inventions_majeures' / '27.webp')
