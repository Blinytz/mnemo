#!/usr/bin/env python3
"""Télécharge une image manquante spécifique via Wikipedia."""
import sys, pathlib, requests, time
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

REPO = pathlib.Path(__file__).parent.parent
THUMBS = REPO / 'thumbs'

def wiki_image(search_term, lang='fr'):
    headers = {'User-Agent': 'memo-app-build/1.0'}
    # Search
    url = f'https://{lang}.wikipedia.org/w/api.php'
    r = requests.get(url, params={
        'action': 'query', 'list': 'search', 'srsearch': search_term,
        'format': 'json', 'utf8': 1
    }, headers=headers, timeout=15)
    results = r.json().get('query', {}).get('search', [])
    if not results:
        return None
    title = results[0]['title']
    # Get main image
    r2 = requests.get(url, params={
        'action': 'query', 'titles': title,
        'prop': 'pageimages', 'pithumbsize': 400,
        'format': 'json'
    }, headers=headers, timeout=15)
    pages = r2.json().get('query', {}).get('pages', {})
    for p in pages.values():
        src = p.get('thumbnail', {}).get('source')
        if src:
            print(f'  Found: {title} -> {src}')
            return src
    return None

def download_webp(url, out_path):
    headers = {'User-Agent': 'memo-app-build/1.0'}
    r = requests.get(url, headers=headers, timeout=15)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img = img.resize((200, 150), Image.LANCZOS)
    img.save(out_path, 'WEBP', quality=82)
    print(f'  Saved: {out_path}')

# Mer de Chine méridionale = entry 10 in mers_oceans
out = THUMBS / 'mers_oceans' / '10.webp'
if out.exists():
    print('Déjà présente.')
else:
    for term in ['South China Sea', 'Mer de Chine méridionale carte', 'South China Sea map']:
        src = wiki_image(term, 'en')
        if src:
            download_webp(src, out)
            break
        time.sleep(1)
    else:
        print('Échec.')
