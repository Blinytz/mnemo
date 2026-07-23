import urllib.parse, requests, json, time
WIKI_UA = 'MemoAppBuild/1.0 (memo educational PWA; contact: build-script)'

def search_commons(name):
    time.sleep(0.3)
    api = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(name + ' Position France')}&srnamespace=6&format=json&formatversion=2&srlimit=3"
    try:
        r = requests.get(api, headers={'User-Agent': WIKI_UA}, timeout=10)
        if r.status_code == 200:
            results = r.json().get('query', {}).get('search', [])
            return [r['title'].replace('File:', '') for r in results if 'Position' in r.get('title', '')]
    except Exception as e:
        return [f"ERROR: {e}"]
    return []

def test_file(fname):
    time.sleep(0.2)
    api = f"https://commons.wikimedia.org/w/api.php?action=query&titles=File:{urllib.parse.quote(fname)}&prop=imageinfo&iiprop=url&format=json&formatversion=2"
    try:
        r = requests.get(api, headers={'User-Agent': WIKI_UA}, timeout=10)
        if r.status_code == 200 and r.content:
            info = r.json()
            pages = info.get('query', {}).get('pages', [])
            for page in pages:
                iis = page.get('imageinfo', [])
                if iis:
                    return True, iis[0]['url'][:60]
    except: pass
    return False, None

for name, variants in [
    ("Côte-d'Or", ["Côte-d'Or-Position.svg", "Côte-d'Or_(département)-Position.svg", "Côte-d'Or département-Position.svg"]),
    ("Côtes-d'Armor", ["Côtes-d'Armor-Position.svg", "Cotes-d'Armor-Position.svg", "Côtes-d'Armor_(département)-Position.svg"]),
    ("Val-d'Oise", ["Val-d'Oise-Position.svg", "Val-d'Oise_(département)-Position.svg"]),
]:
    print(f"\n=== {name} ===")
    for v in variants:
        found, url = test_file(v)
        print(f"  {v!r}: {'FOUND: ' + url if found else 'missing'}")
    results = search_commons(name)
    print(f"  Search: {results}")
