import requests, sys, time
sys.stdout.reconfigure(encoding='utf-8')
API = 'https://commons.wikimedia.org/w/api.php'
H = {'User-Agent': 'MemoApp/1.0'}

for q in ['Delacroix Liberty Leading People', 'Monet Water Lilies Nympheas', 'Van Gogh Starry Night']:
    r = requests.get(API, params={
        'action':'query','generator':'search',
        'gsrnamespace':6,'gsrlimit':5,'gsrsearch':q,
        'prop':'imageinfo','iiprop':'url|size','iiurlwidth':1200,
        'format':'json'
    }, headers=H, timeout=15)
    data = r.json()
    pages = data.get('query',{}).get('pages',{})
    print(f'\n== {q} ==')
    print(f'  pages found: {len(pages)}')
    for p in list(pages.values())[:3]:
        info = p.get('imageinfo',[{}])[0]
        title = p.get('title','')
        w = info.get('width',0)
        h = info.get('height',0)
        thumb = info.get('thumburl','ABSENT')
        url = info.get('url','ABSENT')
        print(f'  {title[:55]}')
        print(f'    size={w}x{h}  thumb_present={thumb!="ABSENT"}')
        # Test download
        test_url = info.get('thumburl') or info.get('url','')
        if test_url:
            try:
                resp = requests.get(test_url, headers=H, timeout=10)
                print(f'    download: HTTP {resp.status_code} {len(resp.content)} bytes')
            except Exception as e:
                print(f'    download: ERROR {e}')
    time.sleep(1)
