#!/usr/bin/env python3
"""Complète les corpus courts avec des entrées encyclopédiques décrites."""
from __future__ import annotations
import html, json, re, time
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'curated_lists.json'
TARGET = 40
SEARCHES = {
 'batailles_decisives':['battle','military battle history'],
 'grandes_explorations':['explorer expedition','exploration history'],
 'revolutions':['political revolution','revolution history'],
 'mers_oceans':['sea geography','ocean geography'],
 'detroits_monde':['strait geography','waterway strait'],
 'parcs_nationaux':['national park','protected area national park'],
 'architectes_majeurs':['architect','architecture'],
 'musees_monde':['museum art museum','national museum'],
}

def search(query: str):
    params = {'action':'query','list':'search','srsearch':query,'srlimit':'50','srnamespace':'0','format':'json','formatversion':'2'}
    for attempt in range(4):
        try:
            r = requests.get('https://en.wikipedia.org/w/api.php?' + urlencode(params), headers={'User-Agent':'MemoAppBuild/1.0 (educational corpus)'}, timeout=25)
            if r.status_code == 200:
                return [(item['title'], re.sub(r'<[^>]+>', '', html.unescape(item.get('snippet','')))) for item in r.json().get('query', {}).get('search', [])]
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 ** attempt)
    return []

def main():
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    for item in payload['lists']:
        if len(item['rows']) >= TARGET: continue
        seen = {str(row[2]).casefold() for row in item['rows']}
        for query in SEARCHES.get(item['id'], []):
            for title, snippet in search(query):
                if len(item['rows']) >= TARGET: break
                if title.casefold() in seen: continue
                row = [str(len(item['rows']) + 1), f'thumbs/{item["id"]}/{len(item["rows"]) + 1}.webp', title]
                while len(row) < len(item['columns']): row.append('')
                row[-1] = snippet or 'Notice encyclopédique.'
                item['rows'].append(row); seen.add(title.casefold())
            if len(item['rows']) >= TARGET: break
        print(f'{item["id"]}: {len(item["rows"])} entrées', flush=True)
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__': main()
