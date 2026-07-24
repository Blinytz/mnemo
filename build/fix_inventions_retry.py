"""Retry des images inventions qui ont échoué au premier run."""
import sys, json, re, pathlib, requests, time
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

THUMBS = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\thumbs')
HEADERS = {'User-Agent': 'memo-app-fix/1.0 (educational)'}

def wiki_image(terms, lang='en'):
    url = f'https://{lang}.wikipedia.org/w/api.php'
    for term in terms:
        time.sleep(3)
        try:
            r = requests.get(url, params={
                'action': 'query', 'list': 'search', 'srsearch': term,
                'format': 'json', 'utf8': 1, 'srlimit': 5
            }, headers=HEADERS, timeout=15)
            r.raise_for_status()
            results = r.json().get('query', {}).get('search', [])
            for result in results:
                title = result['title']
                time.sleep(1)
                r2 = requests.get(url, params={
                    'action': 'query', 'titles': title,
                    'prop': 'pageimages', 'pithumbsize': 400,
                    'format': 'json'
                }, headers=HEADERS, timeout=15)
                pages = r2.json().get('query', {}).get('pages', {})
                for p in pages.values():
                    src = p.get('thumbnail', {}).get('source')
                    if src:
                        print(f"  [{term}] → {title}")
                        return src
        except Exception as e:
            print(f"  Erreur: {e}")
    return None

def save_webp(url, path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200, 150), Image.LANCZOS)
        img.save(path, 'WEBP', quality=82)
        print(f"  → {path.name}")
        return True
    except Exception as e:
        print(f"  Erreur: {e}")
        return False

FIXES = [
    ('inventions_majeures', 21, ['Crawford Long ether anesthesia', 'Ether anaesthesia surgery history'], 'en'),
    ('inventions_majeures', 26, ['Guglielmo Marconi wireless telegraph', 'Marconi inventor radio'], 'en'),
    ('inventions_majeures', 27, ['Cinématographe Lumière 1895', 'Louis Lumière cinema invention'], 'en'),
    ('inventions_majeures', 28, ['Wright Flyer Kitty Hawk 1903 first flight', 'Wright brothers airplane'], 'en'),
]

for lst, num, terms, lang in FIXES:
    path = THUMBS / lst / f'{num}.webp'
    print(f"\n[{lst}] #{num}")
    src = wiki_image(terms, lang)
    if src:
        save_webp(src, path)
    else:
        print(f"  ÉCHEC")
    time.sleep(3)

print("\nDone.")
