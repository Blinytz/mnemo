"""
Retry des échecs via DuckDuckGo Images (serveurs Britannica, Getty, etc.)
au lieu de Wikimedia qui est rate-limité.
"""
import sys, pathlib, requests, time, csv
from PIL import Image
from io import BytesIO

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app')
FULL = BASE / 'full'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120',
    'Accept': 'image/webp,image/*,*/*;q=0.8',
}
Image.MAX_IMAGE_PIXELS = None

# Lire les deux sources d'échecs
fails = []
for fname in ['commons_fails.txt', 'still_fails.txt']:
    fp = BASE / 'build' / fname
    if not fp.exists():
        continue
    with open(fp, encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                folder, num, name, query = parts[0], int(parts[1]), parts[2], parts[3]
                fails.append((folder, num, name, query))

# Dédupliquer
seen = set()
uniq_fails = []
for item in fails:
    key = (item[0], item[1])
    if key not in seen:
        seen.add(key)
        uniq_fails.append(item)
fails = uniq_fails
print(f'{len(fails)} entrées à rattraper via DuckDuckGo\n')

LOG = open(BASE/'build'/'retry_results.csv','w',newline='',encoding='utf-8')
csv_w = csv.writer(LOG)
csv_w.writerow(['folder','num','query','source_url','width','height','kb','score'])
STILL = open(BASE/'build'/'still_fails.txt','w',encoding='utf-8')

def ddg_search(query):
    """Cherche sur DuckDuckGo, retourne liste de (w,h,url)."""
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        results = list(ddgs.images(query, max_results=8, size='Large'))
        time.sleep(5)
        if not results:
            results = list(ddgs.images(query, max_results=6))
            time.sleep(5)
        return [(r.get('width',0), r.get('height',0), r['image'])
                for r in results if r.get('image')]
    except Exception as e:
        msg = str(e)
        if '429' in msg or 'Ratelimit' in msg:
            print(f'  DDG rate-limited, attente 30s...')
            time.sleep(30)
        return []

def try_download(url):
    """Télécharge une image depuis une URL tierce."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        time.sleep(2)
        if resp.status_code != 200:
            return None
        if len(resp.content) < 5000:
            return None
        img = Image.open(BytesIO(resp.content)).convert('RGB')
        if max(img.size) < 300:
            return None
        return img
    except Exception:
        return None

ok = fail = 0
for idx, (folder, num, name, query) in enumerate(fails):
    print(f'[{idx+1}/{len(fails)}] {folder}/{num} — {name}')

    # Recherche DDG
    results = ddg_search(query)
    if not results:
        short = ' '.join(query.split()[:4])
        results = ddg_search(short)

    if not results:
        print(f'  RIEN')
        STILL.write(f'{folder}\t{num}\t{name}\t{query}\tno DDG results\n')
        STILL.flush()
        fail += 1
        continue

    # Trier par résolution
    results.sort(key=lambda r: r[0]*r[1], reverse=True)

    saved = False
    for w, h, url in results[:5]:
        print(f'  essai {w}x{h} {url[:60]}...')
        img = try_download(url)
        if img:
            w0, h0 = img.size
            img.thumbnail((1200, 1200), Image.LANCZOS)
            for old in (FULL/folder).glob(f'{num}.*'):
                old.unlink()
            out = FULL/folder/f'{num}.jpg'
            img.save(out, 'JPEG', quality=88, optimize=True)
            fw, fh = img.size
            kb = out.stat().st_size // 1024
            score = min(10, max(fw,fh)//120)
            note = '✓' if score>=8 else '~'
            print(f'  {note} {fw}x{fh} {kb}KB')
            csv_w.writerow([folder,num,query,url,fw,fh,kb,score])
            LOG.flush()
            ok += 1; saved = True; break

    if not saved:
        print(f'  ECHEC définitif')
        STILL.write(f'{folder}\t{num}\t{name}\t{query}\tDDG failed\n')
        STILL.flush()
        fail += 1

LOG.close()
STILL.close()
print(f'\n╔═══════════════════════════╗')
print(f'║ Récupérés : {ok:4d}           ║')
print(f'║ Encore KO : {fail:4d}           ║')
print(f'╚═══════════════════════════╝')
