"""Fix Pompidou musée et Nairobi via fichiers directs."""
import sys, time
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_file_url, get_thumb_url, save_both

print('Pompidou')
for ft in ['File:CentrePompidou.jpg', 'File:Centre Pompidou.jpg',
           'File:Paris 07 Juillet 2007 - Centre Pompidou.jpg']:
    time.sleep(1)
    url = get_file_url(ft, 800)
    print(f'  {ft.split(":")[-1][:40]}: {url and url[-30:]}')
    if url and 'svg' not in url.lower():
        save_both(url, 'musees_monde', 10, 'Pompidou')
        break
else:
    # Fallback: try Modern art museum
    url = get_thumb_url('Museum of Modern Art Paris', 800)
    if url:
        save_both(url, 'musees_monde', 10, 'Pompidou')

print('\nNairobi')
for ft in ['File:National Museum of Kenya Nairobi.jpg',
           'File:Nairobi Museum - panoramio.jpg']:
    time.sleep(1)
    url = get_file_url(ft, 800)
    print(f'  {ft.split(":")[-1][:40]}: {url and url[-30:]}')
    if url and 'svg' not in url.lower():
        save_both(url, 'musees_monde', 23, 'Nairobi')
        break
else:
    url = get_thumb_url('National Museums of Kenya', 800)
    if url:
        save_both(url, 'musees_monde', 23, 'Nairobi')

print('Done.')
