#!/usr/bin/env python3
"""Porte les corpus curatoriaux à 40 entrées minimum via des résultats Wikipédia décrits."""
from __future__ import annotations
import json, re
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / 'memo.html'
TARGET = 40
QUERIES = {
  'batailles_decisives':'incategory:Battles', 'grandes_explorations':'incategory:Explorers',
  'revolutions':'incategory:Revolutions', 'montagnes_monde':'incategory:Mountains',
  'mers_oceans':'incategory:Seas', 'detroits_monde':'incategory:Straits',
  'parcs_nationaux':'incategory:National_parks', 'architectes_majeurs':'incategory:Architects',
  'musees_monde':'incategory:Museums', 'inventions_majeures':'incategory:Inventions',
  'decouvertes_scientifiques':'scientific discovery', 'tennis_grand_chelem':'Grand Slam tennis tournament',
}
FALLBACKS = {
  'batailles_decisives':['battle history','military battle'], 'grandes_explorations':['exploration expedition','explorer'],
  'revolutions':['revolution political'], 'mers_oceans':['sea ocean','marginal sea'], 'detroits_monde':['strait waterway','strait geography'],
  'parcs_nationaux':['national park'], 'architectes_majeurs':['architect'], 'musees_monde':['museum art museum'],
}

def bracket_value(source: str, name: str):
    start = source.index(name) + len(name)
    start = source.index('[', start)
    level = 0; quote = None; escape = False
    for index in range(start, len(source)):
        ch = source[index]
        if quote:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == quote: quote = None
        elif ch in "'\"": quote = ch
        elif ch == '[': level += 1
        elif ch == ']':
            level -= 1
            if level == 0: return start, index + 1
    raise ValueError('Liste non terminée')

def search(query: str):
    params = {'action':'query','generator':'search','gsrsearch':query,'gsrlimit':'50','gsrnamespace':'0','prop':'description','format':'json','formatversion':'2'}
    response = requests.get('https://en.wikipedia.org/w/api.php?' + urlencode(params), headers={'User-Agent':'MemoAppBuild/1.0'}, timeout=30)
    pages = response.json().get('query', {}).get('pages', [])
    return [(p.get('title',''), p.get('description','')) for p in pages if p.get('title')]

def main():
    html = HTML.read_text(encoding='utf-8')
    start, end = bracket_value(html, 'const CURATED_LISTS_V3 =')
    lists = json.loads(html[start:end])
    for item in lists:
        query = QUERIES.get(item['id'])
        if not query: continue
        existing = {str(row[2]).casefold() for row in item['rows']}
        for candidate_query in [query, *FALLBACKS.get(item['id'], [])]:
            if len(item['rows']) >= TARGET: break
            try: candidates = search(candidate_query)
            except Exception as exc:
                print(f'ERREUR {item["id"]}: {exc}', flush=True); continue
            for title, description in candidates:
                if len(item['rows']) >= TARGET: break
                if title.casefold() in existing: continue
                row = [str(len(item['rows'])+1), f'thumbs/{item["id"]}/{len(item["rows"])+1}.webp', title]
                while len(row) < len(item['columns']): row.append('')
                row[-1] = description or 'Entrée encyclopédique à approfondir.'
                item['rows'].append(row); existing.add(title.casefold())
        print(f'{item["id"]}: {len(item["rows"])} entrées', flush=True)
    payload = json.dumps(lists, ensure_ascii=False)
    html = html[:start] + payload + html[end:]
    html = re.sub(r'const APP_DATA_VERSION = \d+;', 'const APP_DATA_VERSION = 75;', html)
    HTML.write_text(html, encoding='utf-8')

if __name__ == '__main__': main()
