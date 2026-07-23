#!/usr/bin/env python3
"""
build_images.py — Build des images locales pour memo.html
Rejouable : ne retélécharge pas l'existant.

Usage:
    cd build
    python build_images.py [--force] [--list LIST_ID] [--no-patch] [--verify-only]

Variables d'environnement:
    TMDB_API_KEY  — clé API TMDB (obligatoire pour la liste films)
"""
import os, sys, re, json, time, pickle, shutil, csv, urllib.parse, subprocess, unicodedata, argparse, traceback
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

# ── Chemins ────────────────────────────────────────────────────────────────────
REPO      = Path(__file__).parent.parent
HTML_SRC  = REPO / 'memo_v46_images.html'
HTML_DST  = REPO / 'memo.html'
BUILD_DIR = Path(__file__).parent
THUMBS    = REPO / 'thumbs'
FULL      = REPO / 'full'
MANIFEST  = BUILD_DIR / 'manifest.json'
MISSING   = BUILD_DIR / 'rapport_manquants.csv'
CACHE_F   = BUILD_DIR / '.cache.pkl'
DATA_F    = BUILD_DIR / 'extracted_data.json'
EXTRACTOR = BUILD_DIR / 'extract_data.js'

TMDB_KEY  = os.environ.get('TMDB_API_KEY', '')
THUMB_H   = 160
FULL_MAX  = 1600
DELAY     = 0.18
DELAY_IMG = 0.08  # délai réduit pour les téléchargements d'images (CDN)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36 MemoAppBuild/1.0'
WIKI_UA   = 'MemoAppBuild/1.0 (memo educational PWA; contact: build-script)'

MYTHOLOGY_DIRECT_COMMONS_FILES = {
    'Narcisse': 'Narcissus-Caravaggio_(1594-96)_edited.jpg',
    'Hypérion': 'Hyperion_sculpture_01.jpg',
}

# ── Cache HTTP disque ──────────────────────────────────────────────────────────
_cache: dict = {}

def load_cache():
    global _cache
    if CACHE_F.exists():
        try: _cache = pickle.load(open(CACHE_F,'rb'))
        except: _cache = {}

def save_cache():
    try: pickle.dump(_cache, open(CACHE_F,'wb'))
    except: pass

_last_req = 0.0
def http_get(url, headers=None, timeout=25, cache=True, is_image=False):
    global _last_req
    h = {'User-Agent': UA}
    if headers: h.update(headers)
    key = url + str(sorted((headers or {}).items()))
    if cache and key in _cache:
        return _cache[key]
    delay = DELAY_IMG if is_image else DELAY
    elapsed = time.time() - _last_req
    if elapsed < delay: time.sleep(delay - elapsed)
    _last_req = time.time()
    for attempt in range(3):
        try:
            r = requests.get(url, headers=h, timeout=timeout, allow_redirects=True)
            if r.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"  429 rate-limit, attente {wait}s …")
                time.sleep(wait); continue
            result = (r.content, r.status_code, dict(r.headers))
            if cache and r.status_code < 400:
                _cache[key] = result
                if len(_cache) % 50 == 0: save_cache()
            return result
        except Exception as e:
            if attempt == 2: return (b'', 0, {})
            time.sleep(1.5)
    return (b'', 0, {})

# ── Normalisation ──────────────────────────────────────────────────────────────
def nfc(s): return unicodedata.normalize('NFC', str(s or ''))
def strip_accents(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')
def norm(s): return strip_accents(str(s or '')).lower().strip()

def is_image_col(name):
    n = norm(name)
    return any(k in n for k in ['image','photo','portrait','drapeau','illustration','icone','visuel','flag','localisation','localization','carte','map'])

def strip_emoji(s):
    s = str(s or '')
    # Remove leading emoji-like chars
    s = re.sub(r'^[\U0001F000-\U0001FFFF\U00002000-\U00003000☀-⛿✀-➿]+\s*', '', s)
    return s.strip()

def wiki_title(label):
    s = strip_emoji(str(label or ''))
    # Remove parenthetical suffixes
    s = re.sub(r'\s*\([^)]*\)\s*', ' ', s).strip()
    return s

# ── Transformation ensureNumberImageColumns ────────────────────────────────────
def ensure_img_cols(lst):
    cols = lst['columns']
    rows = lst['rows']
    # 1) Numéro en col 0
    num_idx = next((i for i,c in enumerate(cols) if norm(c) == 'numero'), -1)
    if num_idx == -1:
        cols.insert(0, 'Numéro')
        for i,r in enumerate(rows): r.insert(0, str(i+1))
    elif num_idx != 0:
        col = cols.pop(num_idx); cols.insert(0, col)
        for i,r in enumerate(rows):
            v = r.pop(num_idx) if len(r) > num_idx else str(i+1)
            r.insert(0, v or str(i+1))
    # 2) Image en col 1
    img_idx = next((i for i,c in enumerate(cols) if i != 0 and is_image_col(c)), -1)
    if img_idx == -1:
        cols.insert(1, 'Image')
        for r in rows: r.insert(1, '')
    elif img_idx != 1:
        col = cols.pop(img_idx); cols.insert(1, col)
        for r in rows:
            v = r.pop(img_idx) if len(r) > img_idx else ''
            r.insert(1, v)
    # Padding
    for i,r in enumerate(rows):
        while len(r) < len(cols): r.append('')
        if not str(r[0]).strip(): r[0] = str(i+1)
    return lst

def ensure_geo_image_cols(lst):
    """Deux visuels pour les listes géographiques : symbole puis localisation."""
    if lst.get('id') not in ('departements', 'etats_usa'):
        return lst
    ensure_img_cols(lst)
    cols = lst['columns']
    rows = lst['rows']
    if len(cols) > 1:
        cols[1] = 'Image'
    loc_idx = next((i for i, c in enumerate(cols) if norm(c) in ('localisation', 'localization')), -1)
    if loc_idx == -1:
        cols.insert(2, 'Localisation')
        for r in rows:
            r.insert(2, '')
    elif loc_idx != 2:
        col = cols.pop(loc_idx)
        cols.insert(2, col)
        for r in rows:
            v = r.pop(loc_idx) if len(r) > loc_idx else ''
            r.insert(2, v)
    for r in rows:
        while len(r) < len(cols):
            r.append('')
    return lst

def col_idx(lst, name):
    n = norm(name)
    for i,c in enumerate(lst['columns']):
        if norm(c) == n: return i
    return -1

# ── Conversion image → WebP ────────────────────────────────────────────────────
def to_webp_thumb(data: bytes, h=THUMB_H, quality=82) -> bytes | None:
    try:
        img = Image.open(BytesIO(data)).convert('RGBA')
        ratio = h / img.height
        w = max(1, int(img.width * ratio))
        img = img.resize((w, h), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, 'WEBP', quality=quality, method=4)
        return buf.getvalue()
    except Exception as e:
        print(f"    [WebP thumb] {e}")
        return None

def to_webp_full(data: bytes, max_px=FULL_MAX, quality=92) -> bytes | None:
    try:
        img = Image.open(BytesIO(data)).convert('RGBA')
        if max(img.width, img.height) > max_px:
            ratio = max_px / max(img.width, img.height)
            img = img.resize((max(1,int(img.width*ratio)), max(1,int(img.height*ratio))), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, 'WEBP', quality=quality, method=4)
        return buf.getvalue()
    except Exception as e:
        print(f"    [WebP full] {e}")
        return None

def save_image(data: bytes, path: Path, is_svg=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def raster_ext(data: bytes) -> str:
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'webp'
    return 'webp'

def verify_image(data: bytes, is_svg=False) -> bool:
    if not data: return False
    if is_svg:
        return b'<svg' in data[:500].lower() or b'<?xml' in data[:100]
    try:
        img = Image.open(BytesIO(data))
        img.verify()
        return True
    except:
        return False

def _placeholder_webp(label: str, subtitle: str, size=(640, 800), quality=84) -> bytes:
    """Image locale de secours pour éviter les URL externes ou cellules vides."""
    img = Image.new('RGB', size, '#f4efe6')
    draw = ImageDraw.Draw(img)
    w, h = size
    try:
        title_font = ImageFont.truetype('arial.ttf', 54)
        sub_font = ImageFont.truetype('arial.ttf', 28)
        small_font = ImageFont.truetype('arial.ttf', 22)
    except Exception:
        title_font = sub_font = small_font = ImageFont.load_default()

    draw.rectangle([0, 0, w, h], fill='#f4efe6')
    draw.rectangle([34, 34, w - 34, h - 34], outline='#b98b3a', width=4)
    draw.rectangle([54, 54, w - 54, h - 54], outline='#2f4454', width=2)

    for y, color in [(150, '#d6b36a'), (170, '#2f4454'), (190, '#d6b36a')]:
        draw.line([150, y, w - 150, y], fill=color, width=3)
        draw.line([150, h - y, w - 150, h - y], fill=color, width=3)

    def centered(text, y, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((w - (bbox[2] - bbox[0])) / 2, y), text, font=font, fill=fill)

    centered(label, h * 0.42, title_font, '#26323a')
    centered(subtitle, h * 0.52, sub_font, '#5a4a35')
    centered('Image locale', h * 0.67, small_font, '#6f7a80')

    buf = BytesIO()
    img.save(buf, 'WEBP', quality=quality, method=4)
    return buf.getvalue()

def ensure_local_placeholder(lid: str, n_str: str, label: str, subtitle='Mythologie grecque'):
    thumb_path = THUMBS / lid / f'{n_str}.webp'
    full_path = FULL / lid / f'{n_str}.webp'
    if thumb_path.exists() and full_path.exists():
        return
    full_data = _placeholder_webp(label, subtitle, size=(640, 800), quality=84)
    thumb_data = to_webp_thumb(full_data) or full_data
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    thumb_path.write_bytes(thumb_data)
    full_path.write_bytes(full_data)

def clean_lists_for_app(all_lists: list):
    """Corrections de données appliquées après l'association aux fichiers locaux."""
    for lst in all_lists:
        cols = lst.get('columns', [])
        rows = lst.get('rows', [])

        if lst.get('id') == 'mythologie':
            name_idx = col_idx(lst, 'Nom')
            num_idx = col_idx(lst, 'Numéro')
            if name_idx >= 0:
                # Chronos/Cronos est un doublon fonctionnel dans cette liste.
                lst['rows'] = [r for r in rows if str(r[name_idx]).strip().lower() != 'cronos']
                if num_idx >= 0:
                    for i, row in enumerate(lst['rows'], start=1):
                        row[num_idx] = str(i)

        if lst.get('id') == 'os':
            group_idx = col_idx(lst, 'Groupe')
            name_idx = col_idx(lst, 'Nom')
            if group_idx >= 0 and name_idx >= 0 and group_idx < name_idx:
                cols[group_idx], cols[name_idx] = cols[name_idx], cols[group_idx]
                for row in rows:
                    row[group_idx], row[name_idx] = row[name_idx], row[group_idx]

        if lst.get('id') == 'films':
            title_idx = col_idx(lst, 'Titre')
            director_idx = col_idx(lst, 'Réalisateur')
            actors_idx = col_idx(lst, 'Acteurs principaux')
            year_idx = col_idx(lst, 'Année')
            by_num = {str(r[0]): r for r in rows if r}
            film_fixes = {
                '219': {'year': '1967', 'title': 'Bonnie and Clyde', 'director': 'Arthur Penn', 'actors': 'Warren Beatty, Faye Dunaway'},
                '288': {'year': '1990', 'title': 'Dances with Wolves', 'director': 'Kevin Costner', 'actors': 'Kevin Costner, Mary McDonnell'},
                '368': {'year': '2017', 'title': "Faute d'amour", 'director': 'Andrey Zvyagintsev', 'actors': 'Maryana Spivak, Alexey Rozin'},
                '84': {'year': '1922', 'title': 'Häxan', 'director': 'Benjamin Christensen', 'actors': 'Benjamin Christensen, Maren Pedersen'},
                '94': {'year': '1926', 'title': 'A Page of Madness', 'director': 'Teinosuke Kinugasa', 'actors': 'Masao Inoue, Yoshie Nakagawa'},
                '121': {'year': '1935', 'title': 'A Night at the Opera', 'director': 'Sam Wood', 'actors': 'Groucho Marx, Chico Marx, Harpo Marx'},
                '125': {'year': '1936', 'title': 'Fury', 'director': 'Fritz Lang', 'actors': 'Spencer Tracy, Sylvia Sidney'},
                '181': {'year': '1955', 'title': 'Pather Panchali', 'director': 'Satyajit Ray', 'actors': 'Subir Banerjee, Kanu Banerjee'},
                '230': {'year': '1971', 'title': 'The Last Picture Show', 'director': 'Peter Bogdanovich', 'actors': 'Timothy Bottoms, Jeff Bridges, Cybill Shepherd'},
            }
            for num, fix in film_fixes.items():
                row = by_num.get(num)
                if not row:
                    continue
                if year_idx >= 0: row[year_idx] = fix['year']
                if title_idx >= 0: row[title_idx] = fix['title']
                if director_idx >= 0: row[director_idx] = fix['director']
                if actors_idx >= 0: row[actors_idx] = fix['actors']

def preferred_exts(lid: str, ci: int, col_name: str):
    n = norm(col_name)
    if lid == 'etats_usa' and ci == 1:
        return ('svg', 'webp')
    if n in ('localisation', 'localization'):
        return ('svg', 'webp')
    return ('webp', 'jpg', 'jpeg', 'png', 'svg')

def existing_pair(lid: str, n_str: str, ci: int, col_name: str):
    """Retourne les chemins thumb/full existants, même si leurs extensions diffèrent."""
    thumb_path = None
    thumb_ext = None
    for ext in preferred_exts(lid, ci, col_name):
        tp = THUMBS / lid / f"{n_str}.{ext}"
        if tp.exists():
            thumb_path = tp
            thumb_ext = ext
            break
    if not thumb_path:
        return None, None, None, None

    if thumb_ext == 'svg':
        preferred_full_exts = ['svg', 'png', 'jpg', 'jpeg', 'webp']
    else:
        preferred_full_exts = ['jpg', 'jpeg', 'png', 'webp', 'svg']
    for ext in dict.fromkeys(preferred_full_exts):
        fp = FULL / lid / f"{n_str}.{ext}"
        if fp.exists():
            return thumb_path, fp, thumb_ext, ext
    return None, None, None, None

# ── Résolveurs par source ──────────────────────────────────────────────────────

def resolve_flag_svg(code: str):
    url = f"https://flagcdn.com/{code.lower()}.svg"
    data, status, _ = http_get(url, is_image=True)
    if status == 200 and verify_image(data, is_svg=True): return data, 'svg'
    return None, None

def resolve_commons_url(url: str, as_svg=False):
    data, status, _ = http_get(url, is_image=True)
    if status == 200 and verify_image(data, is_svg=as_svg): return data, 'svg' if as_svg else 'image'
    return None, None

def resolve_commons_file(filename: str, width=900):
    clean = filename.strip()
    is_svg = clean.lower().endswith('.svg')
    if is_svg:
        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(clean)}"
    else:
        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(clean)}?width={width}"
    data, status, _ = http_get(url, is_image=True)
    if status == 200 and verify_image(data, is_svg=is_svg): return data, 'svg' if is_svg else 'image'
    return None, None

def resolve_hades_file(filename: str):
    """Télécharge un fichier du wiki Hades via API imageinfo."""
    fname = urllib.parse.quote(filename)
    # Utiliser l'API imageinfo pour obtenir l'URL CDN directe
    api = (f"https://hades.fandom.com/api.php?action=query&titles=File:{fname}"
           f"&prop=imageinfo&iiprop=url&format=json&formatversion=2")
    api_data, api_status, _ = http_get(api, headers={'User-Agent': UA})
    if api_status == 200:
        try:
            info = json.loads(api_data)
            pages = info.get('query', {}).get('pages', [])
            for page in pages:
                for ii in page.get('imageinfo', []):
                    img_url = ii.get('url', '')
                    if img_url:
                        d, s, _ = http_get(img_url, headers={'User-Agent': UA}, is_image=True)
                        if s == 200 and verify_image(d): return d, 'image'
        except: pass
    # Fallback : Special:Redirect
    url = f"https://hades.fandom.com/wiki/Special:Redirect/file/{fname}"
    data, status, _ = http_get(url, headers={'User-Agent': UA}, is_image=True)
    if status == 200 and verify_image(data):
        return data, 'image'
    return None, None

def resolve_hades_for_row(name: str, hades_files: dict, wiki_aliases: dict):
    clean = re.sub(r'\s*\([^)]*\)', '', name).strip()
    alias = wiki_aliases.get(name) or wiki_aliases.get(clean) or clean
    for key in [name, clean, alias]:
        files = hades_files.get(key, [])
        for f in files:
            data, kind = resolve_hades_file(f)
            if data: return data, kind, 'hades'
    # Recherche API wiki Hades
    search_name = alias or clean
    api = (f"https://hades.fandom.com/api.php?action=query&generator=search"
           f"&gsrsearch={urllib.parse.quote(search_name)}&gsrnamespace=6"
           f"&prop=imageinfo&iiprop=url&format=json&formatversion=2&gsrlimit=5")
    api_data, api_status, _ = http_get(api, headers={'User-Agent': UA})
    if api_status == 200:
        try:
            info = json.loads(api_data)
            pages = info.get('query', {}).get('pages', [])
            for page in sorted(pages, key=lambda p: p.get('index', 99)):
                title = page.get('title', '')
                # Préférer pages dont le titre correspond exactement
                base_title = title.replace('File:', '').replace('Fichier:', '').split('.')[0]
                for ii in page.get('imageinfo', []):
                    img_url = ii.get('url', '')
                    if img_url:
                        d, s, _ = http_get(img_url, headers={'User-Agent': UA})
                        if s == 200 and verify_image(d): return d, 'image', 'hades-search'
        except: pass
    return None, None, None

def _commons_api_url(filename: str):
    """Utilise l'API Commons pour obtenir l'URL CDN d'un fichier SVG (évite Special:FilePath)."""
    api = (f"https://commons.wikimedia.org/w/api.php?action=query"
           f"&titles=File:{urllib.parse.quote(filename)}&prop=imageinfo&iiprop=url"
           f"&format=json&formatversion=2")
    data, status, _ = http_get(api, headers={'User-Agent': WIKI_UA}, timeout=8)
    if status != 200: return None
    try:
        info = json.loads(data)
        pages = info.get('query', {}).get('pages', [])
        for page in pages:
            for ii in page.get('imageinfo', []):
                url = ii.get('url', '')
                if url: return url
    except: pass
    return None

def _commons_thumb_url(filename: str, width=800):
    """Obtient l'URL d'une miniature PNG d'un SVG Commons (800px de large)."""
    api = (f"https://commons.wikimedia.org/w/api.php?action=query"
           f"&titles=File:{urllib.parse.quote(filename)}&prop=imageinfo"
           f"&iiprop=url|thumburl&iiurlwidth={width}"
           f"&format=json&formatversion=2")
    data, status, _ = http_get(api, headers={'User-Agent': WIKI_UA})
    if status != 200: return None, None
    try:
        info = json.loads(data)
        pages = info.get('query', {}).get('pages', [])
        for page in pages:
            for ii in page.get('imageinfo', []):
                cdn = ii.get('url', '')
                thumb = ii.get('thumburl', '')
                return cdn, thumb
    except: pass
    return None, None

def _commons_search_files(query: str, limit=8):
    api = (f"https://commons.wikimedia.org/w/api.php?action=query&list=search"
           f"&srnamespace=6&srlimit={limit}&srsearch={urllib.parse.quote(query)}"
           f"&format=json&formatversion=2")
    data, status, _ = http_get(api, headers={'User-Agent': WIKI_UA}, timeout=10)
    if status != 200:
        return []
    try:
        rows = json.loads(data).get('query', {}).get('search', [])
        return [r.get('title', '').replace('File:', '').replace('Fichier:', '') for r in rows if r.get('title')]
    except Exception:
        return []

def _download_commons_svg_or_thumb(filename: str, width=800):
    is_svg = filename.lower().endswith('.svg')
    if is_svg:
        cdn = _commons_api_url(filename)
        if cdn:
            data, status, _ = http_get(cdn, is_image=True, timeout=20)
            if status == 200 and verify_image(data, is_svg=True):
                return data, 'svg', filename
    cdn, thumb = _commons_thumb_url(filename, width=width)
    url = thumb or cdn
    if url:
        data, status, _ = http_get(url, is_image=True, timeout=20)
        if status == 200 and verify_image(data, is_svg=False):
            return data, 'image', filename
    return None, None, None

def resolve_dept_emblem(dept_name: str):
    n = dept_name.replace("’", "'").replace("‘", "'")
    variants = [
        f"Blason département fr {n}.svg",
        f"Blason departement fr {n}.svg",
        f"Blason {n}.svg",
        f"Logo Département {n}.svg",
        f"Logo departement {n}.svg",
    ]
    for filename in dict.fromkeys(variants):
        data, kind, found = _download_commons_svg_or_thumb(filename)
        if data:
            return data, kind, found
    queries = [
        f'"Blason département fr {n}.svg"',
        f'Blason département {n} svg',
        f'Blason {n} département svg',
        f'Logo département {n} svg',
    ]
    for q in queries:
        for filename in _commons_search_files(q, limit=10):
            low = filename.lower()
            if not low.endswith(('.svg', '.png', '.jpg', '.jpeg', '.webp')):
                continue
            if not any(k in low for k in ('blason', 'logo', 'armoiries')):
                continue
            data, kind, found = _download_commons_svg_or_thumb(filename)
            if data:
                return data, kind, found
    return None, None, None

US_STATE_MAP_QUERIES = {
    'Alabama': ['Map of USA highlighting Alabama.svg', 'Alabama in United States.svg'],
    'Alaska': ['Map of USA highlighting Alaska.svg', 'Alaska in United States.svg'],
    'Arizona': ['Map of USA highlighting Arizona.svg', 'Arizona in United States.svg'],
    'Arkansas': ['Map of USA highlighting Arkansas.svg', 'Arkansas in United States.svg'],
    'Californie': ['Map of USA highlighting California.svg', 'California in United States.svg'],
    'Caroline du Nord': ['Map of USA highlighting North Carolina.svg', 'North Carolina in United States.svg'],
    'Caroline du Sud': ['Map of USA highlighting South Carolina.svg', 'South Carolina in United States.svg'],
    'Colorado': ['Map of USA highlighting Colorado.svg', 'Colorado in United States.svg'],
    'Connecticut': ['Map of USA highlighting Connecticut.svg', 'Connecticut in United States.svg'],
    'Dakota du Nord': ['Map of USA highlighting North Dakota.svg', 'North Dakota in United States.svg'],
    'Dakota du Sud': ['Map of USA highlighting South Dakota.svg', 'South Dakota in United States.svg'],
    'Delaware': ['Map of USA highlighting Delaware.svg', 'Delaware in United States.svg'],
    'Floride': ['Map of USA highlighting Florida.svg', 'Florida in United States.svg'],
    'Géorgie': ['Map of USA highlighting Georgia.svg', 'Georgia in United States.svg'],
    'Hawaï': ['Map of USA highlighting Hawaii.svg', 'Hawaii in United States.svg'],
    'Idaho': ['Map of USA highlighting Idaho.svg', 'Idaho in United States.svg'],
    'Illinois': ['Map of USA highlighting Illinois.svg', 'Illinois in United States.svg'],
    'Indiana': ['Map of USA highlighting Indiana.svg', 'Indiana in United States.svg'],
    'Iowa': ['Map of USA highlighting Iowa.svg', 'Iowa in United States.svg'],
    'Kansas': ['Map of USA highlighting Kansas.svg', 'Kansas in United States.svg'],
    'Kentucky': ['Map of USA highlighting Kentucky.svg', 'Kentucky in United States.svg'],
    'Louisiane': ['Map of USA highlighting Louisiana.svg', 'Louisiana in United States.svg'],
    'Maine': ['Map of USA highlighting Maine.svg', 'Maine in United States.svg'],
    'Maryland': ['Map of USA highlighting Maryland.svg', 'Maryland in United States.svg'],
    'Massachusetts': ['Map of USA highlighting Massachusetts.svg', 'Massachusetts in United States.svg'],
    'Michigan': ['Map of USA highlighting Michigan.svg', 'Michigan in United States.svg'],
    'Minnesota': ['Map of USA highlighting Minnesota.svg', 'Minnesota in United States.svg'],
    'Mississippi': ['Map of USA highlighting Mississippi.svg', 'Mississippi in United States.svg'],
    'Missouri': ['Map of USA highlighting Missouri.svg', 'Missouri in United States.svg'],
    'Montana': ['Map of USA highlighting Montana.svg', 'Montana in United States.svg'],
    'Nebraska': ['Map of USA highlighting Nebraska.svg', 'Nebraska in United States.svg'],
    'Nevada': ['Map of USA highlighting Nevada.svg', 'Nevada in United States.svg'],
    'New Hampshire': ['Map of USA highlighting New Hampshire.svg', 'New Hampshire in United States.svg'],
    'New Jersey': ['Map of USA highlighting New Jersey.svg', 'New Jersey in United States.svg'],
    'Nouveau-Mexique': ['Map of USA highlighting New Mexico.svg', 'New Mexico in United States.svg'],
    'New York': ['Map of USA highlighting New York.svg', 'New York in United States.svg'],
    'Ohio': ['Map of USA highlighting Ohio.svg', 'Ohio in United States.svg'],
    'Oklahoma': ['Map of USA highlighting Oklahoma.svg', 'Oklahoma in United States.svg'],
    'Oregon': ['Map of USA highlighting Oregon.svg', 'Oregon in United States.svg'],
    'Pennsylvanie': ['Map of USA highlighting Pennsylvania.svg', 'Pennsylvania in United States.svg'],
    'Rhode Island': ['Map of USA highlighting Rhode Island.svg', 'Rhode Island in United States.svg'],
    'Tennessee': ['Map of USA highlighting Tennessee.svg', 'Tennessee in United States.svg'],
    'Texas': ['Map of USA highlighting Texas.svg', 'Texas in United States.svg'],
    'Utah': ['Map of USA highlighting Utah.svg', 'Utah in United States.svg'],
    'Vermont': ['Map of USA highlighting Vermont.svg', 'Vermont in United States.svg'],
    'Virginie': ['Map of USA highlighting Virginia.svg', 'Virginia in United States.svg'],
    'Virginie-Occidentale': ['Map of USA highlighting West Virginia.svg', 'West Virginia in United States.svg'],
    'Washington': ['Map of USA highlighting Washington.svg', 'Washington in United States.svg'],
    'Wisconsin': ['Map of USA highlighting Wisconsin.svg', 'Wisconsin in United States.svg'],
    'Wyoming': ['Map of USA highlighting Wyoming.svg', 'Wyoming in United States.svg'],
}

def resolve_us_state_map(state_name: str):
    candidates = US_STATE_MAP_QUERIES.get(state_name, [])
    for filename in candidates:
        data, kind, found = _download_commons_svg_or_thumb(filename)
        if data:
            return data, kind, found
    english = candidates[0].replace('Map of USA highlighting ', '').replace('.svg', '') if candidates else state_name
    queries = [
        f'"Map of USA highlighting {english}.svg"',
        f'"{english} in United States.svg"',
        f'USA highlighting {english} svg',
        f'{english} United States location map svg',
    ]
    for q in queries:
        for filename in _commons_search_files(q, limit=10):
            low = filename.lower()
            if not low.endswith('.svg'):
                continue
            if not any(k in low for k in ('highlighting', 'united states', 'usa', 'location')):
                continue
            data, kind, found = _download_commons_svg_or_thumb(filename)
            if data:
                return data, kind, found
    return None, None, None

def resolve_dept_map(dept_name: str):
    """Carte de localisation Wikimedia Commons pour un département.
    Essaie Commons SVG d'abord, puis Wikipédia (pageimages) en fallback."""
    n = dept_name
    # Variantes de nommage pour le fichier Position.svg
    ascii_n = unicodedata.normalize('NFD', n).encode('ascii', 'ignore').decode('ascii')
    variants = [f"{n}-Position.svg", f"{ascii_n}-Position.svg"]
    n2 = n.replace("‘", "'").replace("’", "'")
    if n2 != n: variants.append(f"{n2}-Position.svg")
    ascii_n2 = ascii_n.replace("‘", "'").replace("’", "'")
    if ascii_n2 != ascii_n: variants.append(f"{ascii_n2}-Position.svg")
    # Cas spéciaux
    if "Armor" in n:
        variants.extend(["Cotes-d'Armor-Position.svg"])
    if "Val" in n and "Oise" in n:
        variants.append("Val-d'Oise-Position.svg")

    seen = set()
    for v in variants:
        if v in seen: continue
        seen.add(v)
        cdn_url = _commons_api_url(v)
        if cdn_url:
            data, status, _ = http_get(cdn_url, is_image=True, timeout=15)
            if status == 200 and verify_image(data, is_svg=True):
                return data, 'svg', v

    # Recherche Commons plus souple pour les variantes typographiques.
    search_queries = [
        f'"{n}" "Position.svg"',
        f'"{ascii_n}" "Position.svg"',
        f'{n} département France position svg',
        f'{ascii_n} departement France position svg',
        f'{n} location map svg France department',
    ]
    for q in search_queries:
        for filename in _commons_search_files(q, limit=12):
            low = filename.lower()
            if not low.endswith('.svg'):
                continue
            if not any(k in low for k in ('position', 'location', 'map')):
                continue
            data, kind, found = _download_commons_svg_or_thumb(filename)
            if data:
                return data, kind, found

    # Fallback : Wikipedia fr pageimages (plus fiable que Commons search)
    wiki_title = f"{dept_name} (département)"
    api = (f"https://fr.wikipedia.org/w/api.php?action=query"
           f"&titles={urllib.parse.quote(wiki_title)}"
           f"&prop=pageimages&piprop=thumbnail&pithumbsize=800"
           f"&format=json&formatversion=2")
    data, status, _ = http_get(api, headers={'User-Agent': WIKI_UA}, timeout=8)
    if status == 200:
        try:
            pages = json.loads(data).get('query', {}).get('pages', [])
            for page in pages:
                thumb = page.get('thumbnail', {}).get('source', '')
                if thumb:
                    img_data, img_status, _ = http_get(thumb, is_image=True, timeout=15)
                    if img_status == 200 and verify_image(img_data):
                        return img_data, 'image', wiki_title
        except: pass

    return None, None, None

def resolve_tmdb(titre: str, annee: str='', realisateur: str='', tmdb_key: str=''):
    if not tmdb_key: return None, None
    base = "https://api.themoviedb.org/3"
    params = {'query': titre, 'language': 'fr-FR', 'api_key': tmdb_key}
    if annee: params['year'] = annee
    data, status, _ = http_get(f"{base}/search/movie?{urllib.parse.urlencode(params)}", cache=True)
    results = []
    if status == 200:
        try: results = json.loads(data).get('results', [])
        except: pass
    if not results and annee:
        params2 = {k:v for k,v in params.items() if k != 'year'}
        data2, s2, _ = http_get(f"{base}/search/movie?{urllib.parse.urlencode(params2)}")
        if s2 == 200:
            try: results = json.loads(data2).get('results', [])
            except: pass
    if not results: return None, None
    movie = results[0]
    poster = movie.get('poster_path', '')
    if not poster: return None, None
    thumb_url = f"https://image.tmdb.org/t/p/w342{poster}"
    full_url  = f"https://image.tmdb.org/t/p/original{poster}"
    t_data, t_s, _ = http_get(thumb_url, is_image=True)
    if t_s != 200 or not verify_image(t_data): return None, None
    f_data, f_s, _ = http_get(full_url, is_image=True)
    if f_s != 200 or not verify_image(f_data): f_data = t_data
    return t_data, f_data

def resolve_open_library(titre: str, auteur: str=''):
    params = {'limit': '3'}
    if titre: params['title'] = titre
    if auteur: params['author'] = auteur
    url = f"https://openlibrary.org/search.json?{urllib.parse.urlencode(params)}"
    data, status, _ = http_get(url, headers={'User-Agent': WIKI_UA})
    if status != 200: return None
    try:
        docs = json.loads(data).get('docs', [])
        for doc in docs:
            cover_id = doc.get('cover_i')
            if cover_id:
                img_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                idata, is_, _ = http_get(img_url)
                if is_ == 200 and verify_image(idata): return idata
    except: pass
    return None

def resolve_google_books(titre: str, auteur: str=''):
    q = f"intitle:{titre}"
    if auteur: q += f"+inauthor:{auteur}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(q)}&maxResults=3"
    data, status, _ = http_get(url, headers={'User-Agent': WIKI_UA})
    if status != 200: return None
    try:
        items = json.loads(data).get('items', [])
        for item in items:
            links = item.get('volumeInfo', {}).get('imageLinks', {})
            img_url = links.get('thumbnail') or links.get('smallThumbnail')
            if img_url:
                img_url = img_url.replace('http://', 'https://')
                idata, is_, _ = http_get(img_url)
                if is_ == 200 and verify_image(idata): return idata
    except: pass
    return None

def wiki_batch(title_list, host='fr.wikipedia.org', thumb_size=800):
    out = {}
    seen = list(dict.fromkeys(t for t in title_list if t))
    for i in range(0, len(seen), 50):
        chunk = seen[i:i+50]
        params = urllib.parse.urlencode({
            'action': 'query', 'prop': 'pageimages',
            'piprop': 'thumbnail|original', 'pithumbsize': str(thumb_size),
            'titles': '|'.join(chunk), 'redirects': '1',
            'format': 'json', 'formatversion': '2', 'origin': '*'
        })
        url = f"https://{host}/w/api.php?{params}"
        data, status, _ = http_get(url, headers={'User-Agent': WIKI_UA})
        if status != 200: continue
        try:
            resp = json.loads(data)
            norm_map = {n['from']: n['to'] for n in resp.get('query', {}).get('normalized', [])}
            red_map  = {r['from']: r['to'] for r in resp.get('query', {}).get('redirects', [])}
            def final(t):
                cur = norm_map.get(t, t)
                seen2 = set()
                while cur in red_map and cur not in seen2: seen2.add(cur); cur = red_map[cur]
                return cur
            by_title = {p['title']: p for p in resp.get('query', {}).get('pages', []) if not p.get('missing')}
            for t in chunk:
                p = by_title.get(final(t))
                if not p: continue
                thumb = (p.get('thumbnail') or {}).get('source', '')
                orig  = (p.get('original') or {}).get('source', '')
                if thumb or orig:
                    out[t] = {'thumb': thumb or orig, 'original': orig or upscale(thumb), 'host': host}
        except Exception as e:
            print(f"  [wiki_batch] {host} erreur: {e}")
    return out

def wiki_search(query: str, host='fr.wikipedia.org', thumb_size=800):
    params = urllib.parse.urlencode({
        'action': 'query', 'generator': 'search', 'gsrsearch': query, 'gsrlimit': '5',
        'gsrnamespace': '0', 'prop': 'pageimages', 'piprop': 'thumbnail|original',
        'pithumbsize': str(thumb_size), 'format': 'json', 'formatversion': '2', 'origin': '*'
    })
    url = f"https://{host}/w/api.php?{params}"
    data, status, _ = http_get(url, headers={'User-Agent': WIKI_UA})
    if status != 200: return None
    try:
        pages = sorted(json.loads(data).get('query', {}).get('pages', []), key=lambda p: p.get('index', 99))
        for p in pages:
            thumb = (p.get('thumbnail') or {}).get('source', '')
            orig  = (p.get('original') or {}).get('source', '')
            if thumb or orig:
                return {'thumb': thumb or orig, 'original': orig or upscale(thumb), 'host': host}
    except: pass
    return None

def upscale(url, size=1200):
    if not url: return url
    return re.sub(r'/\d+px-([^/?#]+)$', f'/{size}px-\\1', url)

def wiki_download(hit: dict):
    """Télécharge une image Wikipedia. Retourne (thumb_bytes, full_bytes).
    Les miniatures restent légères, mais le plein format utilise l'original
    quand il est disponible afin d'éviter les zooms pixellisés."""
    thumb_url = hit.get('thumb', '')
    full_url = hit.get('original', '') or upscale(thumb_url, FULL_MAX)
    if not thumb_url and not full_url:
        return None, None

    t_data = None
    if thumb_url:
        data, status, _ = http_get(thumb_url, headers={'User-Agent': UA}, is_image=True)
        if status == 200 and verify_image(data):
            t_data = data

    f_data = None
    if full_url and not full_url.endswith('.svg'):
        data, status, _ = http_get(full_url, headers={'User-Agent': UA}, is_image=True)
        if status == 200 and verify_image(data):
            f_data = data

    if not t_data and f_data:
        t_data = f_data
    if not f_data and t_data:
        f_data = t_data
    return t_data, f_data

# ── Résolution d'une ligne ─────────────────────────────────────────────────────

def resolve_row_image(lst_id, row, cols, ci, hades_files, wiki_aliases, philosopher_files, flag_code_map, tmdb_key, wiki_hits_cache):
    """
    Retourne (thumb_bytes, full_bytes, kind, source_tag, label_used)
    kind = 'webp' | 'svg'
    """
    def fail(): return None, None, None, None, ''

    if lst_id == 'elements':
        # Générer data-URI inline, pas de fichier
        return None, None, 'datauri', 'element-svg', ''

    # ── Label de référence pour cette cellule ──────────────────────────────────
    if ci == 1:
        label = _ref_label(lst_id, row, cols)
    else:
        # Colonne secondaire → valeur de la colonne texte précédente
        label = ''
        for k in range(ci - 1, 0, -1):
            v = strip_emoji(str(row[k] or ''))
            if v and not is_image_col(cols[k]):
                label = v; break
        if not label: label = _ref_label(lst_id, row, cols)

    if not label: return fail()

    col_name_norm = norm(cols[ci] if ci < len(cols) else '')

    # ── etats_usa : drapeau + localisation ───────────────────────────────────
    if lst_id == 'etats_usa' and ci == 1:
        existing = str(row[ci] or '').strip()
        if existing.startswith('http'):
            is_svg = existing.lower().endswith('.svg') or 'svg' in existing.lower()
            data, status, _ = http_get(existing)
            if status == 200 and verify_image(data, is_svg=is_svg):
                return data, data, 'svg' if is_svg else 'image', 'commons-existing', existing
        return fail()
    if lst_id == 'etats_usa' and col_name_norm in ('localisation', 'localization'):
        state_idx = col_idx({'columns': cols}, 'État')
        state = strip_emoji(str(row[state_idx] if state_idx >= 0 else row[3] or ''))
        data, kind, fname = resolve_us_state_map(state)
        if data:
            return data, data, 'svg' if kind == 'svg' else 'image', 'commons-us-location', fname or state
        return fail()

    # ── pays : flagcdn ─────────────────────────────────────────────────────────
    if lst_id == 'pays' and ci == 1:
        # Col Pays
        pays_idx = next((i for i,c in enumerate(cols) if norm(c) == 'pays'), -1)
        pays_name = strip_emoji(str(row[pays_idx] if pays_idx >= 0 else row[2] or ''))
        code = flag_code_map.get(pays_name, '')
        if code:
            data, kind = resolve_flag_svg(code)
            if data: return data, data, 'svg', 'flagcdn', pays_name
        return fail()

    # ── mythologie : Hades en priorité ────────────────────────────────────────
    if lst_id == 'mythologie' and ci == 1:
        name_idx = col_idx({'columns': cols}, 'Nom')
        name = strip_emoji(str(row[name_idx] if name_idx >= 0 else row[2] or ''))
        data, kind, src_tag = resolve_hades_for_row(name, hades_files, wiki_aliases)
        if data:
            thumb = to_webp_thumb(data)
            full  = data
            if thumb and full: return thumb, full, 'webp', src_tag or 'hades', name
        # Repli Wikipédia
        alias = wiki_aliases.get(name, '') or wiki_title(name)
        for title, host in [(alias, 'en.wikipedia.org'), (name, 'fr.wikipedia.org')]:
            if not title: continue
            key = (title, host)
            hit = wiki_hits_cache.get(key) or wiki_batch([title], host=host).get(title)
            if hit:
                wiki_hits_cache[key] = hit
                tdata, fdata = wiki_download(hit)
                if tdata:
                    th = to_webp_thumb(tdata); fu = fdata or tdata
                    if th and fu: return th, fu, 'webp', f'wiki-{host.split(".")[0]}', title
        direct_file = MYTHOLOGY_DIRECT_COMMONS_FILES.get(name)
        if direct_file:
            data, kind, found = _download_commons_svg_or_thumb(direct_file, width=900)
            if data:
                th = to_webp_thumb(data); fu = data
                if th and fu:
                    return th, fu, 'webp', 'mythology-direct', found or name
        return fail()

    # ── departements : blason/logo + localisation ────────────────────────────
    if lst_id == 'departements' and ci == 1:
        nom_idx = col_idx({'columns': cols}, 'Nom')
        dept = strip_emoji(str(row[nom_idx] if nom_idx >= 0 else row[2] or ''))
        data, kind, fname = resolve_dept_emblem(dept)
        if data:
            if kind == 'svg':
                return data, data, 'svg', 'wikimedia-emblem', fname or dept
            th = to_webp_thumb(data); fu = data
            if th and fu:
                return th, fu, 'webp', 'wikimedia-emblem', fname or dept
        return fail()
    if lst_id == 'departements' and col_name_norm in ('localisation', 'localization'):
        nom_idx = col_idx({'columns': cols}, 'Nom')
        dept = strip_emoji(str(row[nom_idx] if nom_idx >= 0 else row[3] or ''))
        data, kind, fname = resolve_dept_map(dept)
        if data:
            return data, data, 'svg' if kind == 'svg' else 'image', 'wikimedia-position', fname or dept
        return fail()

    # ── philosophes ───────────────────────────────────────────────────────────
    if lst_id == 'philosophes' and ci == 1:
        nom_idx = col_idx({'columns': cols}, 'Nom')
        name = strip_emoji(str(row[nom_idx] if nom_idx >= 0 else row[2] or ''))
        fname = philosopher_files.get(name, '')
        if fname:
            data, kind = resolve_commons_file(fname)
            if data:
                is_svg = fname.lower().endswith('.svg')
                if is_svg: return data, data, 'svg', 'commons-philosopher', name
                th = to_webp_thumb(data); fu = data
                if th and fu: return th, fu, 'webp', 'commons-philosopher', name
        # Repli Wikipédia
        hit = wiki_batch([name], host='fr.wikipedia.org').get(name)
        if not hit: hit = wiki_batch([name], host='en.wikipedia.org').get(name)
        if hit:
            tdata, fdata = wiki_download(hit)
            if tdata:
                th = to_webp_thumb(tdata); fu = fdata or tdata
                if th and fu: return th, fu, 'webp', 'wiki-fr', name
        return fail()

    # ── films : TMDB ──────────────────────────────────────────────────────────
    if lst_id == 'films' and ci == 1:
        titre_idx = col_idx({'columns': cols}, 'Titre')
        year_idx  = col_idx({'columns': cols}, 'Année')
        real_idx  = col_idx({'columns': cols}, 'Réalisateur')
        titre = strip_emoji(str(row[titre_idx] if titre_idx >= 0 else row[2] or ''))
        annee = strip_emoji(str(row[year_idx] if year_idx >= 0 else row[2] or ''))
        real  = strip_emoji(str(row[real_idx] if real_idx >= 0 else '' or ''))
        if tmdb_key and titre:
            tdata, fdata = resolve_tmdb(titre, annee, real, tmdb_key)
            if tdata:
                th = to_webp_thumb(tdata); fu = fdata or tdata
                if th and fu: return th, fu, 'webp', 'tmdb', titre
        # Repli Wikipédia en
        t = wiki_title(titre)
        for candidate in [f"{t} (film)", t, f"{t} (film, {annee})"]:
            hit = wiki_batch([candidate], host='en.wikipedia.org').get(candidate)
            if hit:
                tdata, fdata = wiki_download(hit)
                if tdata:
                    th = to_webp_thumb(tdata); fu = fdata or tdata
                    if th and fu: return th, fu, 'webp', 'wiki-en', candidate
        return fail()

    # ── litterature : Open Library → Google Books → Wikipedia ─────────────────
    if lst_id == 'litterature' and ci == 1:
        titre_idx  = col_idx({'columns': cols}, 'Titre')
        auteur_idx = col_idx({'columns': cols}, 'Auteur')
        titre  = strip_emoji(str(row[titre_idx]  if titre_idx  >= 0 else row[2] or ''))
        auteur = strip_emoji(str(row[auteur_idx] if auteur_idx >= 0 else '' or ''))
        idata = resolve_open_library(titre, auteur)
        if not idata and auteur:
            idata = resolve_open_library(titre)  # sans auteur
        if not idata: idata = resolve_google_books(titre, auteur)
        if idata:
            th = to_webp_thumb(idata); fu = idata
            if th and fu: return th, fu, 'webp', 'openlibrary', titre
        # Repli Wikipédia
        t = wiki_title(titre)
        hit = wiki_batch([t], host='fr.wikipedia.org').get(t)
        if not hit: hit = wiki_batch([t], host='en.wikipedia.org').get(t)
        if hit:
            tdata, fdata = wiki_download(hit)
            if tdata:
                th = to_webp_thumb(tdata); fu = fdata or tdata
                if th and fu: return th, fu, 'webp', 'wiki-fr', t
        return fail()

    # ── Toutes les autres listes : Wikipédia ──────────────────────────────────
    candidates = _wiki_candidates(lst_id, row, cols, label, wiki_aliases)
    # Batch par lot
    for title, host in candidates:
        key = (title, host)
        hit = wiki_hits_cache.get(key)
        if hit is None:
            batch = wiki_batch([title], host=host)
            hit = batch.get(title)
            wiki_hits_cache[key] = hit  # peut être None
        if hit:
            tdata, fdata = wiki_download(hit)
            if tdata:
                th = to_webp_thumb(tdata); fu = fdata or tdata
                if th and fu: return th, fu, 'webp', f'wiki-{host.split(".")[0]}', title
    # Recherche plein texte
    ctx = _context_for(lst_id)
    for host in ['fr.wikipedia.org', 'en.wikipedia.org']:
        q = f"{wiki_title(label)} {ctx}".strip()
        hit = wiki_search(q, host=host)
        if hit:
            tdata, fdata = wiki_download(hit)
            if tdata:
                th = to_webp_thumb(tdata); fu = fdata or tdata
                if th and fu: return th, fu, 'webp', f'wiki-search-{host.split(".")[0]}', q
    return fail()


def _ref_label(lst_id, row, cols):
    cfg = {
        'chefs_etat': ('Nom', ''),
        'departements': ('Nom', ''),
        'etats_usa': ('État', ''),
        'mythologie': ('Nom', ''),
        'os': ('Nom', ''),
        'pays': ('Pays', ''),
        'peintres': ('Nom', ''),
        'rois_france': ('Nom', ''),
        'coupes_monde': ('Année', 'Pays organisateur'),
        'xixe': ('Événement 1', ''),
        'xxe': ('Événement 1', ''),
        'litterature': ('Titre', 'Auteur'),
        'guerres': ('Conflit', ''),
        'philosophes': ('Nom', ''),
        'mouvements_peinture': ('Mouvement', ''),
        'jo_ete': ('Ville', 'Année'),
        'jo_hiver': ('Ville', 'Année'),
        'f1_champions': ('Pilote', ''),
        'consoles': ('Console', ''),
        'lunes': ('Lune', 'Planète'),
        'periodes_geologiques': ('Période', ''),
        'films': ('Titre', 'Réalisateur'),
    }
    main_col, extra_col = cfg.get(lst_id, ('', ''))
    label = ''
    if main_col:
        idx = next((i for i,c in enumerate(cols) if norm(c) == norm(main_col)), -1)
        if idx >= 0: label = strip_emoji(str(row[idx] or ''))
    if not label and extra_col:
        idx = next((i for i,c in enumerate(cols) if norm(c) == norm(extra_col)), -1)
        if idx >= 0: label = strip_emoji(str(row[idx] or ''))
    if not label:
        for i in range(2, len(cols)):
            v = strip_emoji(str(row[i] or ''))
            if v and not is_image_col(cols[i]): label = v; break
    return label

def _wiki_candidates(lst_id, row, cols, label, wiki_aliases):
    clean = wiki_title(label)
    alias = wiki_aliases.get(label, '') or wiki_aliases.get(clean, '')
    cands = []
    def push(t, h='fr.wikipedia.org'):
        t = str(t or '').strip()
        if t and (t, h) not in cands: cands.append((t, h))

    if lst_id == 'departements':
        push(f"{clean} (département)"); push(clean)
    elif lst_id == 'lunes':
        push(f"{clean} (lune)"); push(clean); push(f"{clean} (satellite)")
    elif lst_id == 'coupes_monde':
        year_idx = next((i for i,c in enumerate(cols) if norm(c) == 'annee'), -1)
        year = strip_emoji(str(row[year_idx] if year_idx >= 0 else ''))
        if year:
            push(f"Coupe du monde de football {year}")
            push(f"Coupe du monde de football de {year}")
            push(f"{year} FIFA World Cup", 'en.wikipedia.org')
    elif lst_id == 'jo_ete':
        year_idx = next((i for i,c in enumerate(cols) if norm(c) == 'annee'), -1)
        year = strip_emoji(str(row[year_idx] if year_idx >= 0 else ''))
        if year:
            push(f"Jeux olympiques d'été de {year}")
            push(f"{year} Summer Olympics", 'en.wikipedia.org')
    elif lst_id == 'jo_hiver':
        year_idx = next((i for i,c in enumerate(cols) if norm(c) == 'annee'), -1)
        year = strip_emoji(str(row[year_idx] if year_idx >= 0 else ''))
        if year:
            push(f"Jeux olympiques d'hiver de {year}")
            push(f"{year} Winter Olympics", 'en.wikipedia.org')
    elif lst_id == 'films':
        year_idx = next((i for i,c in enumerate(cols) if norm(c) == 'annee'), -1)
        year = strip_emoji(str(row[year_idx] if year_idx >= 0 else ''))
        push(clean); push(f"{clean} (film)"); push(f"{clean} (film, {year})" if year else '')
        push(clean, 'en.wikipedia.org')
    elif lst_id == 'mythologie':
        if alias: push(alias, 'en.wikipedia.org')
        push(clean)
    elif lst_id in ('consoles', 'f1_champions'):
        if alias: push(alias); push(alias, 'en.wikipedia.org')
        push(clean)
    elif lst_id == 'os':
        push(f"Os {clean}"); push(clean); push(f"{clean} (os)"); push(f"Os {clean}", 'en.wikipedia.org')
    else:
        if alias: push(alias)
        push(clean)
    return cands

def _context_for(lst_id):
    ctx = {
        'chefs_etat': 'chef État français portrait',
        'rois_france': 'roi France portrait',
        'os': 'os anatomie',
        'guerres': 'guerre bataille',
        'xixe': 'histoire XIXe siècle',
        'xxe': 'histoire XXe siècle',
        'mouvements_peinture': 'mouvement artistique peinture',
        'f1_champions': 'Formula One driver',
        'consoles': 'video game console',
        'lunes': 'satellite naturel',
        'periodes_geologiques': 'période géologique',
    }
    return ctx.get(lst_id, '')

# ── Génération data-URI pour éléments chimiques ────────────────────────────────
FAMILY_COLORS = {
    'Non-métal':'#4a8fe0','Gaz noble':'#9b59b6','Métal alcalin':'#e67e22',
    'Métal alcalino-terreux':'#f1c40f','Métalloïde':'#2ecc71','Halogène':'#1abc9c',
    'Métal de transition':'#e74c3c','Métal post-transition':'#3498db',
    'Lanthanide':'#e91e63','Actinide':'#ff5722','Métal':'#3498db',
}
def element_svg(num='', symbol='', name='', family=''):
    def esc(x): return str(x or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
    color = FAMILY_COLORS.get(family, '#3f6ed8')
    n,sym,nm,fam = esc(num),esc(symbol or '?'),esc(name or symbol or 'Élément'),esc(family or '')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="620" viewBox="0 0 900 620">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f8fcff"/><stop offset="1" stop-color="#dcecff"/></linearGradient>
<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="{color}" flood-opacity=".18"/></filter></defs>
<rect width="900" height="620" rx="46" fill="url(#bg)"/>
<rect x="58" y="54" width="784" height="512" rx="38" fill="#fff" filter="url(#sh)" stroke="#b8cdec" stroke-width="3"/>
<text x="112" y="128" font-size="46" font-family="Arial,sans-serif" font-weight="700" fill="#86a4cc">{n}</text>
<g transform="translate(450 270)">
<ellipse rx="210" ry="72" fill="none" stroke="{color}" stroke-width="9" opacity=".75" transform="rotate(0)"/>
<ellipse rx="210" ry="72" fill="none" stroke="{color}" stroke-width="9" opacity=".55" transform="rotate(60)"/>
<ellipse rx="210" ry="72" fill="none" stroke="{color}" stroke-width="9" opacity=".55" transform="rotate(120)"/>
<circle r="84" fill="{color}"/>
<text y="24" text-anchor="middle" font-size="78" font-family="Arial,sans-serif" font-weight="800" fill="#ffffff">{sym}</text>
<circle cx="210" cy="0" r="18" fill="#213957"/>
<circle cx="-105" cy="-182" r="14" fill="#213957"/>
<circle cx="-105" cy="182" r="14" fill="#213957"/>
</g>
<text x="450" y="492" text-anchor="middle" font-size="46" font-family="Arial,sans-serif" font-weight="800" fill="#1d3148">{nm}</text>
<text x="450" y="532" text-anchor="middle" font-size="24" font-family="Arial,sans-serif" fill="#6d86a8">{fam}</text></svg>'''
    return 'data:image/svg+xml;charset=utf-8,' + urllib.parse.quote(svg)

# ── Traitement d'une liste complète ───────────────────────────────────────────

def process_list(lst, hades_files, wiki_aliases, philosopher_files, tmdb_key, args, wiki_hits_cache):
    lst_id = lst['id']
    ensure_img_cols(lst)
    ensure_geo_image_cols(lst)
    # Ajouter colonne "Image œuvre" pour peintres
    if lst_id == 'peintres' and 'Image œuvre' not in lst['columns']:
        oeuvre_idx = next((i for i,c in enumerate(lst['columns']) if norm(c) == norm('Œuvre principale')), -1)
        if oeuvre_idx >= 0:
            lst['columns'].insert(oeuvre_idx + 1, 'Image œuvre')
            for r in lst['rows']: r.insert(oeuvre_idx + 1, '')

    cols = lst['columns']
    rows = lst['rows']
    image_col_indices = [i for i,c in enumerate(cols) if i >= 1 and is_image_col(c)]
    flag_code_map = lst.get('flagCodeMap', {})

    results = []  # (row_idx, ci, local_path_thumb, local_path_full, source)
    missing = []  # (row_idx, ci, label, causes)

    total = len(rows) * len(image_col_indices)
    done = 0

    # Elements : data-URI inline
    if lst_id == 'elements':
        num_idx = col_idx(lst, 'Numéro')
        sym_idx = col_idx(lst, 'Symbole')
        nom_idx = col_idx(lst, 'Nom')
        fam_idx = col_idx(lst, 'Famille')
        for ri, row in enumerate(rows):
            n   = str(row[num_idx] if num_idx >= 0 else ri+1 or '')
            sym = str(row[sym_idx] if sym_idx >= 0 else '' or '')
            nm  = str(row[nom_idx] if nom_idx >= 0 else '' or '')
            fam = str(row[fam_idx] if fam_idx >= 0 else '' or '')
            uri = element_svg(n, sym, nm, fam)
            row[1] = uri
            results.append((ri, 1, uri, uri, 'element-svg'))
        return results, missing

    # Batch Wikipédia pré-chargement pour les listes concernées
    if lst_id not in ('pays','etats_usa','mythologie','departements','philosophes','films','litterature','elements'):
        _prefetch_wiki_batch(lst, cols, rows, wiki_aliases, wiki_hits_cache)

    for ri, row in enumerate(rows):
        for ci in image_col_indices:
            done += 1
            n_str = str(ri + 1) if ci == 1 else f"{ri+1}b"
            label = _ref_label(lst_id, row, cols) if ci == 1 else ''
            if ci != 1:
                for k in range(ci-1,0,-1):
                    v = strip_emoji(str(row[k] or ''))
                    if v and not is_image_col(cols[k]): label = v; break
                if not label: label = _ref_label(lst_id, row, cols)

            ext = 'webp'
            full_ext = 'webp'
            thumb_path = THUMBS / lst_id / f"{n_str}.webp"
            full_path  = FULL   / lst_id / f"{n_str}.webp"
            pair = existing_pair(lst_id, n_str, ci, cols[ci])
            if pair[0] and pair[1]:
                thumb_path, full_path, ext, full_ext = pair

            # Déjà traité ?
            if not args.force and thumb_path.exists() and full_path.exists():
                local = f"thumbs/{lst_id}/{n_str}.{ext}"
                row[ci] = local
                results.append((ri, ci, local, f"full/{lst_id}/{n_str}.{full_ext}", 'cached'))
                if done % 50 == 0: print(f"  [{lst_id}] {done}/{total} (cache)")
                continue

            th, fu, kind, src_tag, lbl = resolve_row_image(
                lst_id, row, cols, ci,
                hades_files, wiki_aliases, philosopher_files, flag_code_map, tmdb_key,
                wiki_hits_cache
            )

            if kind == 'datauri':
                # Elements déjà gérés plus haut
                continue

            if th and fu:
                if kind == 'svg':
                    thumb_path = THUMBS / lst_id / f"{n_str}.svg"
                    full_path  = FULL   / lst_id / f"{n_str}.svg"
                    save_image(th, thumb_path, is_svg=True)
                    save_image(fu, full_path,  is_svg=True)
                    local = f"thumbs/{lst_id}/{n_str}.svg"
                else:
                    full_ext = raster_ext(fu)
                    full_path = FULL / lst_id / f"{n_str}.{full_ext}"
                    save_image(th, thumb_path)
                    save_image(fu, full_path)
                    local = f"thumbs/{lst_id}/{n_str}.webp"
                row[ci] = local
                results.append((ri, ci, local, f"full/{lst_id}/{n_str}.{'svg' if kind=='svg' else full_ext}", src_tag))
                if done % 20 == 0 or done == total:
                    print(f"  [{lst_id}] {done}/{total} ✓ {lbl[:30] if lbl else ''} [{src_tag}]")
            else:
                causes = f"Aucune image trouvée (label={label!r}, src_tag={src_tag})"
                missing.append((ri, ci, label, causes))
                row[ci] = ''
                if done % 10 == 0:
                    print(f"  [{lst_id}] {done}/{total} ✗ {label[:30]} — {causes}")

    print(f"  [{lst_id}] terminé : {len(results)} résolus, {len(missing)} manquants")
    return results, missing

def _prefetch_wiki_batch(lst, cols, rows, wiki_aliases, cache):
    """Pré-charge les images Wikipedia par lot de 50 pour une liste."""
    lst_id = lst['id']
    all_candidates = []
    for ri, row in enumerate(rows):
        label = _ref_label(lst_id, row, cols)
        if label:
            cands = _wiki_candidates(lst_id, row, cols, label, wiki_aliases)
            all_candidates.extend(cands)

    fr_titles = list(dict.fromkeys(t for t,h in all_candidates if h == 'fr.wikipedia.org'))
    en_titles = list(dict.fromkeys(t for t,h in all_candidates if h == 'en.wikipedia.org'))

    if fr_titles:
        hits = wiki_batch(fr_titles, host='fr.wikipedia.org')
        for t, hit in hits.items():
            cache[(t, 'fr.wikipedia.org')] = hit
    if en_titles:
        hits = wiki_batch(en_titles, host='en.wikipedia.org')
        for t, hit in hits.items():
            cache[(t, 'en.wikipedia.org')] = hit

# ── Patch du HTML ──────────────────────────────────────────────────────────────

def patch_html(data: dict, all_results: dict, all_lists: list):
    """Lit HTML_SRC (ou HTML_DST si absent), injecte les chemins locaux, écrit HTML_DST."""
    print("\n[patch] Lecture du HTML source…")
    src = HTML_SRC if HTML_SRC.exists() else HTML_DST
    html = src.read_text(encoding='utf-8')

    # 1) Remplacer DEFAULT_LISTS par la version patchée
    print("[patch] Injection des chemins locaux dans DEFAULT_LISTS…")
    start_marker = 'const DEFAULT_LISTS = ['
    si = html.find(start_marker)
    if si == -1: raise RuntimeError("DEFAULT_LISTS introuvable dans le HTML")

    # Trouver la fin du tableau
    depth = 0
    i = si + len(start_marker) - 1  # position de '['
    in_str = False; str_char = ''
    while i < len(html):
        c = html[i]
        if in_str:
            if c == '\\': i += 2; continue
            if c == str_char: in_str = False
        else:
            if c in ('"', "'", '`'): in_str = True; str_char = c
            elif c == '[': depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0: break
        i += 1
    end_i = i + 1  # après le ']'

    # Chercher le ';' suivant
    j = end_i
    while j < len(html) and html[j] in ' \t\r\n': j += 1
    if html[j] == ';': end_i = j + 1

    # Filtrer sur les 23 listes de base uniquement — EXPANSION et CURATED sont
    # injectés séparément dans le HTML via leurs propres DEFAULT_LISTS.push().
    BASE_IDS = {
        'chefs_etat','departements','elements','etats_usa','mythologie','os','pays',
        'peintres','rois_france','coupes_monde','xixe','xxe','litterature','guerres',
        'philosophes','mouvements_peinture','jo_ete','jo_hiver','f1_champions',
        'consoles','lunes','periodes_geologiques','films'
    }
    base_lists = [l for l in all_lists if l['id'] in BASE_IDS]
    new_lists_js = _serialize_lists_js(base_lists)
    html = html[:si] + f"const DEFAULT_LISTS = {new_lists_js}" + html[end_i:]

    # 2) Bumper APP_DATA_VERSION — ne jamais rétrograder sous la valeur existante
    # incomplets/cassés à reprendre les listes embarquées dans ce build.
    html = re.sub(r'(const APP_DATA_VERSION\s*=\s*)(\d+)', lambda m: m.group(1) + str(max(75, int(m.group(2)))), html)
    html = re.sub(
        r"const DB_PREFIX\s*=\s*'[^']*';",
        "const DB_PREFIX = 'memo_v62_local_';",
        html,
        count=1
    )
    old_db = """const DB = {
  get: k => { try { return JSON.parse(localStorage.getItem(DB_PREFIX+k)); } catch { return null; } },
  set: (k,v) => localStorage.setItem(DB_PREFIX+k, JSON.stringify(v)),
  clear: () => Object.keys(localStorage).filter(k=>k.startsWith(DB_PREFIX)).forEach(k=>localStorage.removeItem(k))
};"""
    new_db = """function cleanupOldMemoStorage() {
  try {
    Object.keys(localStorage)
      .filter(k => /^memo_v\\d+_/.test(k) && !k.startsWith(DB_PREFIX))
      .forEach(k => localStorage.removeItem(k));
  } catch {}
}
const DB = {
  get: k => { try { return JSON.parse(localStorage.getItem(DB_PREFIX+k)); } catch { return null; } },
  set: (k,v) => {
    try {
      localStorage.setItem(DB_PREFIX+k, JSON.stringify(v));
    } catch (err) {
      cleanupOldMemoStorage();
      try { localStorage.setItem(DB_PREFIX+k, JSON.stringify(v)); } catch {}
    }
  },
  clear: () => Object.keys(localStorage).filter(k=>k.startsWith(DB_PREFIX)).forEach(k=>localStorage.removeItem(k))
};
cleanupOldMemoStorage();"""
    html = html.replace(old_db, new_db, 1)

    # 3) Adapter le runtime aux chemins locaux.
    old_is_image_value = """function isImageValue(v) {
  if (!v) return false;
  const str = String(v).trim();
  return str.startsWith('data:image/') || /^https?:\\/\\/.+/i.test(str);
}"""
    new_is_image_value = """function isImageValue(v) {
  if (!v) return false;
  const str = String(v).trim();
  return str.startsWith('data:image/')
    || /^https?:\\/\\/.+/i.test(str)
    || /^(thumbs|full)\\//i.test(str)
    || /\\.(webp|png|jpe?g|gif|svg)(\\?.*)?$/i.test(str);
}"""
    html = html.replace(old_is_image_value, new_is_image_value, 1)
    html = html.replace(
        "    const shouldReplace = force || !cur || generated || info.status === 'flag' || info.status === 'official-department-map' || info.status === 'hades-official' || info.status === 'official-stylized' || info.status === 'official-portrait';",
        "    const shouldReplace = force || !cur || generated || !isImageValue(cur);",
        1
    )
    html = html.replace(
        "function isGeneratedLocalImageValue(v, meta=null) {\n"
        "  const str = String(v || '').trim();\n"
        "  return str.startsWith('data:image/svg+xml') || meta?.host === 'local' || meta?.status === 'local-visual' || meta?.status === 'generic' || meta?.status === 'failed';\n"
        "}",
        "function isGeneratedLocalImageValue(v, meta=null) {\n"
        "  const str = String(v || '').trim();\n"
        "  if (/^(thumbs|full)\\//i.test(str)) return false;\n"
        "  return str.startsWith('data:image/svg+xml') || meta?.host === 'local' || meta?.status === 'local-visual' || meta?.status === 'generic' || meta?.status === 'failed';\n"
        "}",
        1
    )
    html = html.replace(
        "      const n = applyDeterministicImagesForList(l, {force:true});",
        "      const n = applyDeterministicImagesForList(l, {force:false});",
        1
    )
    html = html.replace(
        "  const isFlag = className.includes('flag-img');\n  const loadingMode = isFlag ? 'eager' : 'lazy';",
        "  const isFlag = className.includes('flag-img');\n  const isLocal = /^(thumbs|full)\\//i.test(raw);\n  const isEmbeddedLocal = raw.startsWith('data:image/');\n  const loadingMode = (isFlag || isLocal || isEmbeddedLocal) ? 'eager' : 'lazy';",
        1
    )
    html = html.replace(
        "return ['image','photo','portrait','illustration','icone','icon','visuel','drapeau','flag'].some(k => n.includes(k));",
        "return ['image','photo','portrait','illustration','icone','icon','visuel','drapeau','flag','localisation','localization','carte','map'].some(k => n.includes(k));",
        1
    )
    html = html.replace(
        "  const sortedLists = [...lists].sort((a,b) => a.name.localeCompare(b.name, 'fr'));",
        "  if (!Array.isArray(lists) || !lists.length) lists = cloneDefaultLists();\n"
        "  lists = lists.filter(l => l && Array.isArray(l.columns) && Array.isArray(l.rows)).map((l, i) => ({\n"
        "    ...l,\n"
        "    id: l.id || `list_${i + 1}`,\n"
        "    name: String(l.name || l.id || `Liste ${i + 1}`),\n"
        "    icon: l.icon || '📋'\n"
        "  }));\n"
        "  if (!lists.length) lists = cloneDefaultLists();\n"
        "  const sortedLists = [...lists].sort((a,b) => String(a.name || '').localeCompare(String(b.name || ''), 'fr'));",
        1
    )
    html = html.replace(
        "save();\nrenderHome();\nmaybeAutoUpdateImagesOnce();\nif(notifEnabled) scheduleNotif();",
        "renderHome();\nsave();\nmaybeAutoUpdateImagesOnce();\nif(notifEnabled) scheduleNotif();",
        1
    )
    html = html.replace(
        "function getDefaultList(id){ return cloneDefaultLists().find(l => l.id === id); }\n\nfunction normalizeStoredLists(stored){",
        "function getDefaultList(id){ return cloneDefaultLists().find(l => l.id === id); }\n"
        "function isCompatibleDefaultList(item, fresh){\n"
        "  if (!item || !fresh || !Array.isArray(item.columns) || !Array.isArray(fresh.columns)) return false;\n"
        "  if (!Array.isArray(item.rows) || item.columns.length !== fresh.columns.length) return false;\n"
        "  return fresh.columns.every((col, idx) => String(item.columns[idx] || '') === String(col || ''));\n"
        "}\n\n"
        "function normalizeStoredLists(stored){",
        1
    )
    html = html.replace(
        "      out.push(storedVersion < APP_DATA_VERSION && fresh ? fresh : {...item, _source:'default', _defaultVersion:item._defaultVersion || storedVersion || 1});",
        "      const useFresh = fresh && (storedVersion < APP_DATA_VERSION || !isCompatibleDefaultList(item, fresh));\n"
        "      out.push(useFresh ? fresh : {...item, _source:'default', _defaultVersion:item._defaultVersion || storedVersion || 1});",
        1
    )
    html = html.replace(
        "function openTable(id) {\n  currentListId = id;",
        "let homeScrollBeforeTable = 0;\n\nfunction openTable(id) {\n  homeScrollBeforeTable = $('main') ? $('main').scrollTop : 0;\n  currentListId = id;",
        1
    )
    html = re.sub(
        r"\n\s*// M8: Remove Num[^\n]*\n\s*const f1 = lists\.find\(l => l\.id === 'f1_champions'\);\n\s*if \(f1 && f1\.columns\[0\] === 'Num[^\n]*\n\s*f1\.columns\.splice\(0, 1\);\n\s*f1\.rows\.forEach\(r => r\.splice\(0, 1\)\);\n\s*changed = true;\n\s*}\n",
        "\n",
        html,
        count=1
    )
    html = html.replace(
        "$('back-from-table').addEventListener('click', () => {\n  $('view-table').classList.remove('active');\n  navigate('home');\n});",
        "$('back-from-table').addEventListener('click', () => {\n  $('view-table').classList.remove('active');\n  navigate('home');\n  requestAnimationFrame(() => {\n    const main = $('main');\n    if (main) main.scrollTop = homeScrollBeforeTable || 0;\n  });\n});",
        1
    )

    # 4) Ne pas stubber les fonctions runtime ici.
    # Le précédent stubber découpait mal le JS et supprimait renderHome().
    # Les listes pointent déjà vers des chemins locaux; les résolutions réseau
    # ne se lancent que si l'utilisateur utilise explicitement les fonctions.

    # 5) Ajouter migration v47 (localStorage)
    migration_js = _migration_v47_js(all_lists)
    # Injecter après la définition de lists
    inject_marker = 'let lists        = normalizeStoredLists(DB.get(\'lists\'));'
    inject_pos = html.find(inject_marker)
    if inject_pos != -1:
        inject_end = inject_pos + len(inject_marker)
        html = html[:inject_end] + '\n' + migration_js + html[inject_end:]

    # 6) Zoom modal : table thumb -> full, extensions différentes acceptées.
    image_files_map = {}
    for lid, results in all_results.items():
        files = {}
        for ri, ci, local_t, local_f, _src in results:
            if isinstance(local_t, str) and local_t.startswith('thumbs/') and isinstance(local_f, str) and local_f.startswith('full/'):
                n_str = str(ri + 1) if ci == 1 else f"{ri + 1}b"
                files[n_str] = local_f
        image_files_map[lid] = files

    image_files_js = json.dumps(image_files_map, ensure_ascii=False, separators=(',', ':'))
    helper_js = f"""
const IMAGE_FILES_MAP = {image_files_js};
function localFullImageForThumb(src, listId = currentListId, ci = editCi, ri = editRi) {{
  const raw = String(src || '').trim();
  if (!raw.startsWith('thumbs/')) return '';
  const m = raw.match(/^thumbs\\/([^/]+)\\/([^/.]+)\\.[a-z0-9]+$/i);
  const lid = listId || (m && m[1]) || '';
  let key = (m && m[2]) || '';
  if (!key && Number.isFinite(ri)) key = ci === 1 ? String(ri + 1) : `${{ri + 1}}b`;
  return (IMAGE_FILES_MAP[lid] && IMAGE_FILES_MAP[lid][key]) || '';
}}
"""
    html = re.sub(r'\nconst IMAGE_FILES_MAP\s*=\s*\{.*?\};\s*\nfunction localFullImageForThumb\(.*?\n\}\s*\n', '\n', html, flags=re.S)
    insert_pt = html.rfind('</script>')
    if insert_pt != -1:
        html = html[:insert_pt] + helper_js + html[insert_pt:]

    old_zoom = "const zoomSrc = (editCi === 1 ? meta?.original : meta?.extraOriginals?.[editCi])\n      || imgUpscaleThumb(curVal) || curVal;"
    new_zoom = "const zoomSrc = localFullImageForThumb(curVal, l.id, editCi, editRi)\n      || (editCi === 1 ? meta?.original : meta?.extraOriginals?.[editCi])\n      || imgUpscaleThumb(curVal) || curVal;"
    html = html.replace(old_zoom, new_zoom, 1)

    HTML_DST.write_text(html, encoding='utf-8')
    print(f"[patch] {HTML_DST} écrit ({len(html)//1024} Ko)")

def _serialize_lists_js(all_lists):
    """Sérialise la liste de listes en JavaScript (compatible avec le HTML source)."""
    import json
    lines = ['[\n']
    for lst in all_lists:
        # Utiliser json.dumps : tous les champs sont des types JSON simples
        entry = json.dumps(lst, ensure_ascii=False, separators=(',', ':'))
        lines.append(f"  {entry},\n")
    if lines[-1].endswith(',\n'):
        lines[-1] = lines[-1][:-2] + '\n'
    lines.append(']')
    return ''.join(lines)

def _migration_v47_js(all_lists):
    """Génère le code JS de migration localStorage v47."""
    # Construire une table rowIndex → localPath pour chaque liste
    migration_data = {}
    for lst in all_lists:
        lid = lst['id']
        if lid == 'elements': continue
        entry = {}
        cols = lst['columns']
        rows = lst['rows']
        for ri, row in enumerate(rows):
            for ci, col in enumerate(cols):
                if ci >= 1 and is_image_col(col):
                    v = str(row[ci] or '').strip()
                    if v and (v.startswith('thumbs/') or v.startswith('data:')):
                        n_str = str(ri+1) if ci == 1 else f"{ri+1}b"
                        entry[n_str] = v
        migration_data[lid] = entry

    md_json = json.dumps(migration_data, ensure_ascii=False)
    return f"""
/* ── Migration v47 : images locales ── */
(function migrateLocalImages() {{
  const V47_DATA = {md_json};
  const stored = DB.get('lists');
  if (!Array.isArray(stored)) return;
  let changed = false;
  for (const sl of stored) {{
    if (!sl || !sl.id) continue;
    const map = V47_DATA[sl.id];
    if (!map) continue;
    if (!Array.isArray(sl.columns) || !Array.isArray(sl.rows)) continue;
    const imgCols = sl.columns
      .map((col, idx) => idx >= 1 && /image|photo|portrait|drapeau|flag|localisation/i.test(String(col || '')) ? idx : -1)
      .filter(idx => idx >= 0);
    for (let ri = 0; ri < sl.rows.length; ri++) {{
      const row = sl.rows[ri];
      for (const ci of imgCols) {{
        const n_str = ci === 1 ? String(ri+1) : (ri+1)+'b';
        const localPath = map[n_str];
        if (!localPath) continue;
        const cur = String(row[ci] || '').trim();
        // Conserver les uploads personnels (data:image/ non-SVG)
        if (cur.startsWith('data:image/') && !cur.startsWith('data:image/svg')) continue;
        if (cur !== localPath) {{ row[ci] = localPath; changed = true; }}
      }}
    }}
    // Purger imageMeta obsolète
    delete sl.imageMeta;
  }}
  if (changed) {{ DB.set('lists', stored); console.info('[MEMO v47] Migration images locales appliquée'); }}
}})();
lists = normalizeStoredLists(DB.get('lists'));
"""

# ── Vérification ───────────────────────────────────────────────────────────────

def verify(all_lists, all_results_by_list, all_missing_by_list):
    print("\n" + "="*60)
    print("VÉRIFICATION FINALE")
    print("="*60)

    total_cells = 0
    total_ok = 0
    total_missing = 0
    total_size_thumb = 0
    total_size_full = 0
    oversized = []
    report_rows = []

    # Compter par liste
    for lst in all_lists:
        lid = lst['id']
        results = all_results_by_list.get(lid, [])
        missing = all_missing_by_list.get(lid, [])
        rows_count = len(lst['rows'])
        img_cols = [i for i,c in enumerate(lst['columns']) if i >= 1 and is_image_col(c)]
        cells = rows_count * len(img_cols)
        ok = len([r for r in results if r[4] != 'cached' or True])
        # Recompter les cellules réellement remplies
        ok_real = 0
        for ri, row in enumerate(lst['rows']):
            for ci in img_cols:
                v = str(row[ci] or '').strip()
                if v: ok_real += 1
        miss = cells - ok_real
        total_cells += cells
        total_ok += ok_real
        total_missing += miss

        # Sources
        sources = {}
        for r in results:
            src = r[4] if len(r) > 4 else 'unknown'
            sources[src] = sources.get(src, 0) + 1
        src_str = ', '.join(f"{k}:{v}" for k,v in sources.items())

        pct = 100 * ok_real / cells if cells else 0
        status = '✓' if pct >= 98 else ('⚠' if pct >= 80 else '✗')
        print(f"  {status} {lid:25s} {ok_real:4d}/{cells:4d} ({pct:5.1f}%) [{src_str}]")
        report_rows.append({'liste': lid, 'ok': ok_real, 'total': cells, 'pct': f"{pct:.1f}", 'sources': src_str, 'manquants': miss})

    # Vérification fichiers
    print("\nVérification intégrité des fichiers…")
    broken = []
    for lst in all_lists:
        lid = lst['id']
        for ri, row in enumerate(lst['rows']):
            for ci, col in enumerate(lst['columns']):
                if ci >= 1 and is_image_col(col):
                    v = str(row[ci] or '').strip()
                    if v.startswith('thumbs/'):
                        p = REPO / v
                        if not p.exists():
                            broken.append(f"{lid} ligne {ri+1}: {v} manquant")
                        else:
                            sz = p.stat().st_size
                            total_size_thumb += sz
                            if sz > 300_000:
                                oversized.append(f"{v} ({sz//1024} Ko)")
                        fp = REPO / v.replace('thumbs/','full/',1)
                        if not fp.exists():
                            broken.append(f"{lid} ligne {ri+1}: full/{v.split('/',2)[-1]} manquant")
                        else:
                            total_size_full += fp.stat().st_size

    if broken:
        print(f"  ✗ {len(broken)} fichiers manquants ou cassés:")
        for b in broken[:10]: print(f"    - {b}")
        if len(broken) > 10: print(f"    ... et {len(broken)-10} autres")
    else:
        print("  ✓ Tous les fichiers référencés existent")

    if oversized:
        print(f"  ⚠ {len(oversized)} images > 300 Ko:")
        for o in oversized[:5]: print(f"    - {o}")

    total_mb = (total_size_thumb + total_size_full) / 1_048_576
    print(f"\n  Poids total : thumbs={total_size_thumb//1024} Ko, full={total_size_full//1024} Ko → total={total_mb:.1f} Mo")
    if total_mb > 60: print("  ⚠ Objectif < 60 Mo dépassé!")
    else: print("  ✓ Poids dans l'objectif")

    # Vérification URLs externes dans les données
    print("\nRecherche d'URLs externes résiduelles dans les données…")
    ext_pattern = re.compile(r'https?://(?!thumbs/|full/)(?:wikipedia|wikimedia|fandom|flagcdn|tmdb|openlibrary)', re.I)
    ext_found = []
    for lst in all_lists:
        for ri, row in enumerate(lst['rows']):
            for ci, v in enumerate(row):
                if ci >= 1 and is_image_col(lst['columns'][ci] if ci < len(lst['columns']) else ''):
                    if ext_pattern.search(str(v or '')):
                        ext_found.append(f"{lst['id']} ligne {ri+1} col {ci}: {str(v)[:60]}")

    if ext_found:
        print(f"  ✗ {len(ext_found)} URLs externes trouvées dans les données:")
        for e in ext_found[:10]: print(f"    - {e}")
    else:
        print("  ✓ Aucune URL externe dans les cellules de données")

    # Vérification cohérence mythologie / departements
    print("\nVérification cohérence des sources spéciales…")
    mythologie_lst = next((l for l in all_lists if l['id'] == 'mythologie'), None)
    if mythologie_lst:
        results = all_results_by_list.get('mythologie', [])
        hades_count = sum(1 for r in results if 'hades' in str(r[4] if len(r)>4 else ''))
        total_myt = len(mythologie_lst['rows'])
        print(f"  mythologie: {hades_count}/{total_myt} depuis Hades")

    dept_lst = next((l for l in all_lists if l['id'] == 'departements'), None)
    if dept_lst:
        results = all_results_by_list.get('departements', [])
        pos_count = sum(1 for r in results if 'position' in str(r[4] if len(r)>4 else '').lower() or 'wikimedia' in str(r[4] if len(r)>4 else '').lower())
        total_dept = len(dept_lst['rows'])
        print(f"  departements: {pos_count}/{total_dept} cartes Position")

    # Résumé final
    global_pct = 100 * total_ok / total_cells if total_cells else 0
    print(f"\n{'='*60}")
    print(f"RÉSULTAT GLOBAL : {total_ok}/{total_cells} cellules ({global_pct:.1f}%)")
    print(f"  Manquantes : {total_missing}")
    print(f"  Fichiers cassés : {len(broken)}")
    print(f"{'='*60}")

    return {
        'global_pct': global_pct,
        'total_ok': total_ok,
        'total_cells': total_cells,
        'broken': len(broken),
        'report_rows': report_rows,
    }

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Build images locales pour memo.html')
    parser.add_argument('--force', action='store_true', help='Retélécharger même si déjà présent')
    parser.add_argument('--list', help='Traiter une seule liste (ID)')
    parser.add_argument('--no-patch', action='store_true', help='Ne pas modifier le HTML')
    parser.add_argument('--verify-only', action='store_true', help='Vérification uniquement (pas de téléchargement)')
    parser.add_argument('--patch-only', action='store_true', help='Patcher le HTML avec les fichiers existants (pas de téléchargement)')
    args = parser.parse_args()

    if not TMDB_KEY and not args.verify_only:
        print("⚠ TMDB_API_KEY non définie — les films utiliseront uniquement Wikipedia comme repli")

    # ── Extraction des données ────────────────────────────────────────────────
    print("Extraction des données depuis le HTML…")
    if True:  # toujours re-extraire — le HTML change entre les builds
        src_for_extract = HTML_SRC if HTML_SRC.exists() else HTML_DST
        result = subprocess.run(
            ['node', str(EXTRACTOR), str(src_for_extract)],
            capture_output=True, encoding='utf-8'
        )
        if result.returncode != 0:
            print(f"Erreur extract_data.js: {result.stderr}")
            sys.exit(1)
        DATA_F.write_text(result.stdout, encoding='utf-8')
    data = json.loads(DATA_F.read_text(encoding='utf-8'))

    default_lists    = data['DEFAULT_LISTS']
    hades_files      = data.get('HADES_OFFICIAL_FILES', {})
    wiki_aliases     = data.get('WIKI_IMAGE_ALIASES', {})
    philosopher_files= data.get('PHILOSOPHER_COMMONS_FILES', {})

    # ── Appliquer ensureNumberImageColumns ───────────────────────────────────
    for lst in default_lists:
        ensure_img_cols(lst)
        ensure_geo_image_cols(lst)
        # Ajouter Image œuvre pour peintres
        if lst['id'] == 'peintres' and 'Image œuvre' not in lst['columns']:
            oeuvre_idx = next((i for i,c in enumerate(lst['columns']) if norm(c) == norm('Œuvre principale')), -1)
            if oeuvre_idx >= 0:
                lst['columns'].insert(oeuvre_idx + 1, 'Image œuvre')
                for r in lst['rows']: r.insert(oeuvre_idx + 1, '')

    ensure_local_placeholder('mythologie', '45', 'Narcisse')
    ensure_local_placeholder('mythologie', '60', 'Hypérion')

    if args.patch_only or args.verify_only:
        # Construire all_results depuis les fichiers sur disque
        all_results_by_list = {}
        all_missing_by_list = {}
        for lst in default_lists:
            lid = lst['id']
            cols = lst['columns']
            rows = lst['rows']
            results = []
            missing = []
            if lid == 'elements':
                # data-URI : régénérer
                num_idx = col_idx(lst, 'Numéro'); sym_idx = col_idx(lst, 'Symbole')
                nom_idx = col_idx(lst, 'Nom'); fam_idx = col_idx(lst, 'Famille')
                for ri, row in enumerate(rows):
                    n=str(row[num_idx] if num_idx>=0 else ri+1 or '')
                    sym=str(row[sym_idx] if sym_idx>=0 else '' or '')
                    nm=str(row[nom_idx] if nom_idx>=0 else '' or '')
                    fam=str(row[fam_idx] if fam_idx>=0 else '' or '')
                    uri = element_svg(n, sym, nm, fam)
                    row[1] = uri
                    results.append((ri, 1, uri, uri, 'element-svg'))
            else:
                img_cols = [i for i,c in enumerate(cols) if i>=1 and is_image_col(c)]
                for ri, row in enumerate(rows):
                    for ci in img_cols:
                        n_str = str(ri+1) if ci==1 else f"{ri+1}b"
                        pair = existing_pair(lid, n_str, ci, cols[ci])
                        found = bool(pair[0] and pair[1])
                        if found:
                            tp, fp, thumb_ext, full_ext = pair
                            local = f"thumbs/{lid}/{n_str}.{thumb_ext}"
                            row[ci] = local
                            results.append((ri, ci, local, f"full/{lid}/{n_str}.{full_ext}", 'disk'))
                        if not found:
                            label = _ref_label(lid, row, cols) or str(row[0] if row else f"Ligne {ri+1}")
                            row[ci] = ''
                            missing.append((ri, ci, label, 'Fichier local manquant'))
            all_results_by_list[lid] = results
            all_missing_by_list[lid] = missing
        clean_lists_for_app(default_lists)
        if args.verify_only:
            verify(default_lists, all_results_by_list, all_missing_by_list)
            return
        # patch_only : générer le HTML
        print("Patching HTML avec les fichiers existants…")
        src = HTML_SRC if HTML_SRC.exists() else HTML_DST
        html = src.read_text(encoding='utf-8')
        patch_html(html, all_results_by_list, default_lists)
        print("✓ memo.html généré")
        return

    if False and args.verify_only:
        # Charger les résultats existants depuis les fichiers
        all_results_by_list = {}
        all_missing_by_list = {}
        for lst in default_lists:
            lid = lst['id']
            results = []
            for ri, row in enumerate(lst['rows']):
                for ci, col in enumerate(lst['columns']):
                    if ci >= 1 and is_image_col(col):
                        v = str(row[ci] or '').strip()
                        if v: results.append((ri, ci, v, '', 'existing'))
            all_results_by_list[lid] = results
            all_missing_by_list[lid] = []
        verify(default_lists, all_results_by_list, all_missing_by_list)
        return

    load_cache()
    wiki_hits_cache = {}

    # ── Traitement par liste ──────────────────────────────────────────────────
    all_results_by_list = {}
    all_missing_by_list = {}
    manifest_entries = []
    missing_rows_csv = []

    lists_to_process = default_lists
    if args.list:
        lists_to_process = [l for l in default_lists if l['id'] == args.list]
        if not lists_to_process:
            print(f"Liste {args.list!r} introuvable")
            sys.exit(1)

    for lst in lists_to_process:
        lid = lst['id']
        print(f"\n── {lst['name']} ({lid}) ── {len(lst['rows'])} lignes ──")
        try:
            results, missing = process_list(
                lst, hades_files, wiki_aliases, philosopher_files,
                TMDB_KEY, args, wiki_hits_cache
            )
            all_results_by_list[lid] = results
            all_missing_by_list[lid] = missing

            # Manifest
            for ri, ci, local_t, local_f, src in results:
                label = _ref_label(lid, lst['rows'][ri], lst['columns']) if ci == 1 else ''
                manifest_entries.append({
                    'liste': lid, 'ligne': ri+1, 'col': ci,
                    'thumb': local_t, 'full': local_f,
                    'source': src, 'label': label
                })
            for ri, ci, label, cause in missing:
                missing_rows_csv.append({
                    'liste': lid, 'ligne': ri+1, 'col': ci,
                    'label': label, 'cause': cause
                })
        except Exception as e:
            print(f"  ERREUR pour {lid}: {e}")
            traceback.print_exc()
            all_results_by_list[lid] = []
            all_missing_by_list[lid] = []

    clean_lists_for_app(default_lists)

    save_cache()

    # ── Écriture des rapports ─────────────────────────────────────────────────
    MANIFEST.write_text(json.dumps(manifest_entries, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\nManifest écrit : {len(manifest_entries)} entrées")

    with open(MISSING, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['liste','ligne','col','label','cause'])
        w.writeheader(); w.writerows(missing_rows_csv)
    print(f"Rapport manquants : {len(missing_rows_csv)} lignes → {MISSING}")

    # ── Patch HTML ────────────────────────────────────────────────────────────
    if not args.no_patch:
        patch_html(data, all_results_by_list, default_lists)

    # ── Vérification ─────────────────────────────────────────────────────────
    report = verify(default_lists, all_results_by_list, all_missing_by_list)

    print("\n✓ Build terminé.")
    if report['global_pct'] < 98:
        print(f"⚠ Couverture {report['global_pct']:.1f}% < objectif 98% — voir rapport_manquants.csv")

if __name__ == '__main__':
    main()
