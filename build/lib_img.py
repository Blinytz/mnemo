"""
Bibliothèque commune pour tous les scripts de fix.
Sauvegarde TOUJOURS thumbs/ (200x150 WebP) ET full/ (800x600 JPEG max).
"""
import requests, time, pathlib
from PIL import Image
from io import BytesIO

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
URL = 'https://en.wikipedia.org/w/api.php'
BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')

def get_thumb_url(title, size=800):
    """Get thumbnail URL from Wikipedia page title."""
    time.sleep(1.5)
    r = requests.get(URL, params={
        'action': 'query', 'titles': title,
        'prop': 'pageimages', 'pithumbsize': size,
        'format': 'json'
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return None
    for p in r.json().get('query', {}).get('pages', {}).values():
        src = p.get('thumbnail', {}).get('source', '')
        if src and not src.lower().endswith('.svg'):
            return src
    return None

def get_original_url(title):
    """Get original full-resolution image URL from Wikipedia (piprop=original).
    Preferred over pithumbsize because Wikipedia caps thumbnails at 800px for many images.
    Returns None if SVG or no image found."""
    time.sleep(1.5)
    r = requests.get(URL, params={
        'action': 'query', 'titles': title,
        'prop': 'pageimages', 'piprop': 'original',
        'format': 'json'
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return None
    for p in r.json().get('query', {}).get('pages', {}).values():
        orig = p.get('original', {})
        src = orig.get('source', '')
        if src and not src.lower().endswith('.svg'):
            return src
    return None

def get_file_url(file_title, size=800):
    """Get URL from File: title."""
    time.sleep(1)
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

def get_page_images(title, map_kw=None):
    """Get all images from a Wikipedia page, optionally filtered by keywords."""
    time.sleep(1.5)
    r = requests.get(URL, params={
        'action': 'query', 'titles': title,
        'prop': 'images', 'imlimit': 50, 'format': 'json'
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return []
    imgs = []
    for p in r.json().get('query', {}).get('pages', {}).values():
        imgs = [i['title'] for i in p.get('images', [])]
    # Filter out SVG and icons
    imgs = [i for i in imgs if not i.lower().endswith('.svg')
            and not any(x in i.lower() for x in ['icon', 'flag', 'logo', 'blank'])]
    if map_kw:
        kw_imgs = [i for i in imgs if any(k in i.lower() for k in map_kw)]
        return kw_imgs, [i for i in imgs if i not in kw_imgs]
    return imgs

def save_both(url, folder, num, label=''):
    """Download url and save to both thumbs/ and full/."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if not r.content:
            return False
        img = Image.open(BytesIO(r.content)).convert('RGB')

        # Save thumbs/ (200x150)
        thumb_dir = BASE / 'thumbs' / folder
        thumb_dir.mkdir(parents=True, exist_ok=True)
        t = img.copy()
        t.thumbnail((200, 150), Image.LANCZOS)
        # Center-crop to exactly 200x150
        tw, th = t.size
        if tw != 200 or th != 150:
            t = img.copy()
            # Resize to fit within 200x150 preserving aspect
            t.thumbnail((200, 150), Image.LANCZOS)
        t.save(thumb_dir / f'{num}.webp', 'WEBP', quality=82)

        # Save full/ (max 1200 wide, JPEG)
        full_dir = BASE / 'full' / folder
        full_dir.mkdir(parents=True, exist_ok=True)
        f = img.copy()
        f.thumbnail((1200, 1200), Image.LANCZOS)
        f.save(full_dir / f'{num}.jpg', 'JPEG', quality=88)

        tw_size = (BASE / 'thumbs' / folder / f'{num}.webp').stat().st_size
        fu_size = (BASE / 'full' / folder / f'{num}.jpg').stat().st_size
        print(f'  #{num} {label}: thumb={tw_size}B full={fu_size}B')
        return True
    except Exception as e:
        print(f'  #{num} {label}: ERREUR {e}')
        return False

def search_first(term, n=6):
    """Search Wikipedia and return first page's thumbnail URL."""
    time.sleep(2)
    r = requests.get(URL, params={
        'action': 'query', 'list': 'search', 'srsearch': term,
        'format': 'json', 'utf8': 1, 'srlimit': n
    }, headers=HEADERS, timeout=20)
    if not r.content:
        return None
    results = r.json().get('query', {}).get('search', [])
    for res in results:
        url = get_thumb_url(res['title'])
        if url:
            return url
    return None
