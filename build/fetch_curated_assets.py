#!/usr/bin/env python3
"""Télécharge les assets locaux des listes curatoriales depuis Wikipédia/Commons."""
from pathlib import Path
from io import BytesIO
from urllib.parse import quote
import time
import requests

import add_curated_lists as data
import build_images as image

ROOT = Path(__file__).resolve().parent.parent

def api_hits(titles):
    url = 'https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&piprop=thumbnail%7Coriginal&pithumbsize=1800&format=json&formatversion=2&titles=' + quote('|'.join(titles))
    pages = requests.get(url, headers={'User-Agent': image.WIKI_UA}, timeout=30).json().get('query', {}).get('pages', [])
    norm = lambda v: str(v).casefold().replace('_', ' ')
    return {title:(page.get('thumbnail') or {}).get('source') or (page.get('original') or {}).get('source')
            for title in titles for page in pages if norm(title) == norm(page.get('title'))}

def download(url):
    proxy = f'https://wsrv.nl/?url={quote(url, safe="")}&w=1800&output=jpg'
    response = requests.get(proxy, headers={'User-Agent': image.WIKI_UA}, timeout=45)
    return response.content if response.status_code == 200 and image.verify_image(response.content) else None

def main():
    for list_id, _, _, _, rows in data.LISTS:
        titles = [row[0] for row in rows]
        hits = api_hits(titles)
        for index, title in enumerate(titles, 1):
            thumb = ROOT/'thumbs'/list_id/f'{index}.webp'
            full = ROOT/'full'/list_id/f'{index}.webp'
            if thumb.exists() and full.exists():
                continue
            url = hits.get(title)
            if not url:
                print(f'MANQUANT {list_id}/{index}: {title}', flush=True); continue
            raw = download(url)
            if not raw:
                print(f'ECHEC {list_id}/{index}: {title}', flush=True); continue
            thumb.parent.mkdir(parents=True, exist_ok=True); full.parent.mkdir(parents=True, exist_ok=True)
            thumb.write_bytes(image.to_webp_thumb(raw, quality=84))
            full.write_bytes(image.to_webp_full(raw, max_px=1800, quality=94))
            print(f'OK {list_id}/{index}: {title}', flush=True)
            time.sleep(.5)

if __name__ == '__main__': main()
