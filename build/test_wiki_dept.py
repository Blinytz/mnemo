import urllib.parse, requests, json, time
WIKI_UA = 'MemoAppBuild/1.0 (memo educational PWA; contact: build-script)'

names = ["Côte-d'Or", "Côtes-d'Armor", "Ain", "Bouches-du-Rhône"]
api_url = "https://fr.wikipedia.org/w/api.php"
params = {
    'action': 'query',
    'prop': 'pageimages|images',
    'piprop': 'thumbnail|name',
    'pithumbsize': 800,
    'pilimit': 5,
    'imlimit': 10,
    'format': 'json',
    'formatversion': '2',
    'titles': '|'.join(names),
}
r = requests.get(api_url, params=params, headers={'User-Agent': WIKI_UA}, timeout=15)
print("Status:", r.status_code)
info = r.json()
for page in info.get('query', {}).get('pages', []):
    title = page.get('title', '')
    thumb = page.get('thumbnail', {}).get('source', 'NO_THUMB')
    page_image = page.get('pageimage', 'NO_IMAGE')
    imgs = [i['title'] for i in page.get('images', [])][:5]
    print(f"\n{title}")
    print(f"  thumb: {thumb[:60] if thumb != 'NO_THUMB' else 'NONE'}")
    print(f"  pageimage: {page_image}")
    print(f"  images: {imgs}")
