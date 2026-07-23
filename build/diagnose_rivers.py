"""Diagnostique les images disponibles dans les articles problématiques."""
import sys, requests, time
sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational)'}
URL = 'https://en.wikipedia.org/w/api.php'

ARTICLES = [
    'Yangtze',
    'Tigris',
    'Orange River',
    'Rhine',
    'Zambezi',
    'Euphrates',
]

for title in ARTICLES:
    time.sleep(1.5)
    r = requests.get(URL, params={
        'action': 'query', 'titles': title,
        'prop': 'images', 'imlimit': 50, 'format': 'json'
    }, headers=HEADERS, timeout=20)
    pages = r.json().get('query', {}).get('pages', {})
    for p in pages.values():
        imgs = [i['title'].split(':',1)[-1] for i in p.get('images', [])]
        # Show all PNG/JPG with map/basin keywords
        relevant = [i for i in imgs if any(k in i.lower() for k in ['map','basin','course','river']) and not i.lower().endswith('.svg')]
        print(f'\n[{title}] — {len(imgs)} images, {len(relevant)} pertinentes:')
        for i in relevant:
            print(f'  {i[:80]}')
