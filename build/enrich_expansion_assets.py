#!/usr/bin/env python3
"""Crée les assets locaux des listes ajoutées récemment.

Usage: python build/enrich_expansion_assets.py
Le script est rejouable: il conserve les WebP déjà présents et met à jour le
manifeste intégré dans memo.html uniquement pour les fichiers effectivement créés.
"""
from __future__ import annotations

import json
import re
import time
import argparse
import threading
from urllib.parse import quote
from io import BytesIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image, ImageDraw, ImageFont
import requests

import build_images as build

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / 'memo.html'
THUMBS = ROOT / 'thumbs'
FULL = ROOT / 'full'
DOWNLOAD_DELAY = 1.0
_last_download = 0.0
_download_lock = threading.Lock()

WIKI_TARGETS = {
    'constellations': [
        ('', 'Orion (constellation)'), ('', 'Ursa Major'), ('', 'Ursa Minor'), ('', 'Cassiopeia (constellation)'),
        ('', 'Cygnus (constellation)'), ('', 'Lyra'), ('', 'Aquila (constellation)'), ('', 'Scorpius'),
        ('', 'Sagittarius (constellation)'), ('', 'Taurus (constellation)'), ('', 'Gemini (constellation)'), ('', 'Leo (constellation)'),
    ],
    'civilisations': [
        ('Mésopotamie', 'Mesopotamia'), ('Égypte antique', 'Ancient Egypt'),
        ("Civilisation de l'Indus", 'Indus Valley Civilisation'), ('Dynastie Shang', 'Shang dynasty'),
        ('Grèce antique', 'Ancient Greece'), ('Rome antique', 'Ancient Rome'),
        ('Empire byzantin', 'Byzantine Empire'), ("Royaume d'Aksoum", 'Kingdom of Aksum'),
        ('Empire du Mali', 'Mali Empire'), ('Civilisation maya', 'Maya civilization'),
        ('Empire aztèque', 'Aztec Empire'), ('Empire inca', 'Inca Empire'),
    ],
    'fleuves_monde': [
        ('Nil', 'Nile'), ('Amazone', 'Amazon River'), ('Yangzi Jiang', 'Yangtze'),
        ('Mississippi-Missouri', 'Mississippi River'), ('Ienisseï', 'Yenisei'),
        ('Huang He', 'Yellow River'), ('Ob-Irtych', 'Ob River'), ('Paraná', 'Paraná River'),
        ('Congo (fleuve)', 'Congo River'), ('Amour (fleuve)', 'Amur'), ('', 'Lena (river)'),
        ('Mékong', 'Mekong'),
    ],
    'compositeurs': [
        ('Johann Sebastian Bach', 'Johann Sebastian Bach'), ('Antonio Vivaldi', 'Antonio Vivaldi'),
        ('Georg Friedrich Haendel', 'George Frideric Handel'), ('Joseph Haydn', 'Joseph Haydn'),
        ('Wolfgang Amadeus Mozart', 'Wolfgang Amadeus Mozart'), ('Ludwig van Beethoven', 'Ludwig van Beethoven'),
        ('', 'Franz Schubert'), ('Frédéric Chopin', 'Frédéric Chopin'),
        ('Giuseppe Verdi', 'Giuseppe Verdi'), ('Richard Wagner', 'Richard Wagner'),
        ('Claude Debussy', 'Claude Debussy'), ('Igor Stravinsky', 'Igor Stravinsky'),
    ],
    'grands_scientifiques': [
        ('Archimède', 'Archimedes'), ('Ibn al-Haytham', 'Ibn al-Haytham'),
        ('Nicolas Copernic', 'Nicolaus Copernicus'), ('Galilée (savant)', 'Galileo Galilei'),
        ('Isaac Newton', 'Isaac Newton'), ('Antoine Lavoisier', 'Antoine Lavoisier'),
        ('Charles Darwin', 'Charles Darwin'), ('Marie Curie', 'Marie Curie'),
        ('Albert Einstein', 'Albert Einstein'), ('', 'Rosalind Franklin'),
        ('Katherine Johnson', 'Katherine Johnson'), ('Jane Goodall', 'Jane Goodall'),
    ],
}

RIVER_MAP_QUERIES = ['Nile map', 'Amazon River map', 'Yangtze map', 'Mississippi River map', 'Yenisei map', 'Yellow River map', 'Ob River map', 'Parana River map', 'Congo River map', 'Amur River map', 'Lena River map', 'Mekong River map']

CONSTELLATIONS = {
    'Orion': [(180,420),(310,310),(440,370),(540,420),(640,470),(770,320),(900,410)],
    # Grand Chariot : casserole (Dubhe, Merak, Phecda, Megrez) + manche (Alioth, Mizar, Alkaid).
    'Grande Ourse': [(560,600),(380,580),(440,430),(620,400),(560,600),(620,400),(760,320),(900,230),(1060,170)],
    'Petite Ourse': [(190,500),(310,430),(440,390),(570,330),(710,250),(840,150),(950,90)],
    'Cassiopée': [(160,320),(330,220),(500,380),(680,210),(880,330)],
    'Cygne': [(560,120),(560,280),(320,390),(560,430),(810,390),(560,650)],
    'Lyre': [(460,160),(610,300),(760,250),(800,440),(620,520),(500,390),(610,300)],
    'Aigle': [(250,420),(500,300),(730,430)],
    'Scorpion': [(160,180),(300,260),(430,360),(540,470),(620,580),(720,650),(840,610),(900,500)],
    'Sagittaire': [(260,500),(400,350),(600,350),(760,470),(640,580),(450,580),(260,500)],
    'Taureau': [(180,260),(360,360),(520,450),(680,360),(850,250),(720,520)],
    'Gémeaux': [(300,130),(300,310),(300,520),(620,150),(620,330),(620,560)],
    'Lion': [(180,250),(350,180),(500,280),(420,420),(620,500),(780,440),(900,550)],
}

def font(size: int, bold: bool = False):
    candidates = ['arialbd.ttf', 'DejaVuSans-Bold.ttf'] if bold else ['arial.ttf', 'DejaVuSans.ttf']
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def save_pair(list_id: str, index: int, data: bytes) -> bool:
    thumb = build.to_webp_thumb(data, quality=84)
    full = build.to_webp_full(data, max_px=1800, quality=94)
    if not thumb or not full:
        return False
    (THUMBS / list_id).mkdir(parents=True, exist_ok=True)
    (FULL / list_id).mkdir(parents=True, exist_ok=True)
    (THUMBS / list_id / f'{index}.webp').write_bytes(thumb)
    (FULL / list_id / f'{index}.webp').write_bytes(full)
    return True


def wiki_hits(targets: list[tuple[str, str]]) -> list[dict | None]:
    """Résout une liste entière en deux requêtes API par langue, pas une par ligne."""
    def batch(titles, host):
        titles = [title for title in titles if title]
        if not titles: return {}
        url = f'https://{host}/w/api.php?action=query&prop=pageimages&piprop=thumbnail%7Coriginal&pithumbsize=1800&format=json&formatversion=2&titles=' + quote('|'.join(titles))
        try:
            pages = requests.get(url, headers={'User-Agent': build.WIKI_UA}, timeout=25).json().get('query', {}).get('pages', [])
            norm = lambda value: str(value).replace('_', ' ').casefold()
            return {title: {'thumb': (page.get('thumbnail') or {}).get('source', ''), 'original': (page.get('original') or {}).get('source', '')}
                    for title in titles for page in pages if norm(page.get('title')) == norm(title) and ((page.get('thumbnail') or {}).get('source') or (page.get('original') or {}).get('source'))}
        except (requests.RequestException, ValueError):
            return {}
    fr_hits = batch([fr for fr, _ in targets], 'fr.wikipedia.org')
    en_hits = batch([en for _, en in targets], 'en.wikipedia.org')
    return [fr_hits.get(fr) or en_hits.get(en) for fr, en in targets]


def download_hit(hit: dict | None) -> bytes | None:
    if not hit:
        return None
    # Le thumbnail à 1800 px demandé à l'API est suffisamment détaillé pour
    # le plein format, et évite les originaux parfois très lourds.
    url = hit.get('thumb') or hit.get('original')
    if not url:
        return None
    # Wikimedia peut temporairement limiter le CDN alors que son API reste
    # disponible. Le proxy rapatrie une copie locale puis la source directe
    # reste un second choix si ce service est indisponible.
    proxied = f'https://wsrv.nl/?url={quote(url, safe="")}&w=1800&output=jpg'
    for candidate, timeout in ((proxied, 30), (url, 20)):
        try:
            global _last_download
            with _download_lock:
                wait = DOWNLOAD_DELAY - (time.monotonic() - _last_download)
                if wait > 0:
                    time.sleep(wait)
                _last_download = time.monotonic()
            response = requests.get(candidate, headers={'User-Agent': build.WIKI_UA}, timeout=timeout)
            if response.status_code == 200 and build.verify_image(response.content):
                return response.content
        except requests.RequestException:
            continue
    return None


def commons_map(query: str) -> bytes | None:
    url = 'https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrlimit=8&prop=imageinfo&iiprop=url&iiurlwidth=1800&format=json&formatversion=2&gsrsearch=' + quote(query)
    try:
        payload = requests.get(url, headers={'User-Agent': build.WIKI_UA}, timeout=25).json()
        pages = payload.get('query', {}).get('pages', [])
        for page in pages:
            title = page.get('title', '').lower()
            info = (page.get('imageinfo') or [{}])[0]
            hit = {'thumb': info.get('thumburl') or info.get('url', '')}
            if 'map' in title or 'river' in title:
                data = download_hit(hit)
                if data:
                    return data
    except (requests.RequestException, ValueError):
        return None
    return None


def constellation_image(name: str, points: list[tuple[int, int]]) -> bytes:
    image = Image.new('RGB', (1200, 760), '#071426')
    draw = ImageDraw.Draw(image)
    for left, right in zip(points, points[1:]):
        draw.line((left, right), fill='#7dd3fc', width=5)
    for index, (x, y) in enumerate(points):
        radius = 18 if index == 0 else 12
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill='white')
    title = font(48, True)
    box = draw.textbbox((0, 0), name, font=title)
    draw.text(((1200-(box[2]-box[0]))/2, 675), name, font=title, fill='#dbeafe')
    output = BytesIO()
    image.save(output, 'PNG')
    return output.getvalue()


def river_diagram() -> bytes:
    """Schéma local de la Léna, plus pertinent qu'une photographie générique."""
    image = Image.new('RGB', (1400, 900), '#e8f3f7')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1400, 150), fill='#164e63')
    draw.text((70, 38), 'Léna', font=font(62, True), fill='white')
    draw.text((72, 116), 'Fleuve de Sibérie orientale - vers la mer des Laptev', font=font(30), fill='#bae6fd')
    route = [(260, 720), (410, 650), (520, 565), (630, 480), (780, 420), (900, 335), (1100, 255)]
    draw.line(route, fill='#0284c7', width=26, joint='curve')
    for x, y in route:
        draw.ellipse((x-10, y-10, x+10, y+10), fill='#075985')
    draw.text((110, 748), 'Source: monts Baïkal', font=font(34, True), fill='#14532d')
    draw.text((925, 200), 'Mer des Laptev', font=font(34, True), fill='#0c4a6e')
    draw.text((110, 815), '4 400 km environ', font=font(30), fill='#334155')
    output = BytesIO()
    image.save(output, 'PNG')
    return output.getvalue()


def patch_manifest(images: dict[str, dict[int, str]]):
    html = HTML.read_text(encoding='utf-8')
    payload = json.dumps(images, ensure_ascii=False, separators=(',', ':'))
    html, count = re.subn(
        r'const EXPANSION_LOCAL_IMAGES = \{.*?\};',
        f'const EXPANSION_LOCAL_IMAGES = {payload};', html, count=1
    )
    if count != 1:
        raise RuntimeError('Marqueur EXPANSION_LOCAL_IMAGES introuvable ou déjà remplacé')
    HTML.write_text(html, encoding='utf-8')


def current_manifest() -> dict[str, dict[str, str]]:
    html = HTML.read_text(encoding='utf-8')
    match = re.search(r'const EXPANSION_LOCAL_IMAGES = (\{.*?\});', html)
    return json.loads(match.group(1)) if match else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', choices=sorted(WIKI_TARGETS), help='Traite une seule liste')
    parser.add_argument('--workers', type=int, default=1, help='Téléchargements simultanés (1 par défaut)')
    parser.add_argument('--delay', type=float, default=1.0, help='Pause entre téléchargements')
    parser.add_argument('--force', action='store_true', help='Remplace les assets existants')
    args = parser.parse_args()
    global DOWNLOAD_DELAY
    DOWNLOAD_DELAY = max(0, args.delay)
    build.load_cache()
    images = current_manifest()
    targets_by_list = {args.list: WIKI_TARGETS[args.list]} if args.list else WIKI_TARGETS
    for list_id, targets in targets_by_list.items():
        images[list_id] = {} if args.force else dict(images.get(list_id, {}))
        hits = wiki_hits(targets)
        pending = {}
        for index, hit in enumerate(hits, 1):
            thumb_path = THUMBS / list_id / f'{index}.webp'
            full_path = FULL / list_id / f'{index}.webp'
            if thumb_path.exists() and full_path.exists() and not args.force:
                images[list_id][index] = f'thumbs/{list_id}/{index}.webp'
            else:
                pending[index] = hit
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = {pool.submit(download_hit, hit): index for index, hit in pending.items()}
            for future in as_completed(futures):
                index = futures[future]
                fr = targets[index - 1][0]
                try:
                    data = future.result()
                except Exception:
                    data = None
                if not data or not save_pair(list_id, index, data):
                    print(f'MANQUANT {list_id}/{index}: {fr}', flush=True)
                    continue
                images[list_id][index] = f'thumbs/{list_id}/{index}.webp'
                print(f'OK {list_id}/{index}: {fr}', flush=True)

    if not args.list or args.list == 'fleuves_monde':
        images['fleuves_monde'] = {}
        for index, query in enumerate(RIVER_MAP_QUERIES, 1):
            data = commons_map(query)
            if data and save_pair('fleuves_monde', index, data):
                images['fleuves_monde'][index] = f'thumbs/fleuves_monde/{index}.webp'
                print(f'CARTE fleuves_monde/{index}: {query}', flush=True)
            else:
                print(f'MANQUANT carte fleuves_monde/{index}: {query}', flush=True)

    build.save_cache()
    patch_manifest(images)
    print('Terminé: manifest local injecté dans memo.html')


if __name__ == '__main__':
    main()
