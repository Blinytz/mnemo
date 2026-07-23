#!/usr/bin/env python3
"""Retire les ajouts de recherche générique et restaure le noyau éditorial propre."""
from __future__ import annotations
import json, re
from pathlib import Path

import add_curated_lists as seed

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / 'memo.html'
DATA = ROOT / 'data' / 'curated_lists.json'
ICONS = {
    'batailles_decisives':'⚔️','grandes_explorations':'🧭','revolutions':'✊',
    'montagnes_monde':'⛰️','mers_oceans':'🌊','detroits_monde':'🗺️','parcs_nationaux':'🌲',
    'architectes_majeurs':'🏛️','musees_monde':'🖼️','inventions_majeures':'⚙️','decouvertes_scientifiques':'🧬',
}

def make_lists():
    out = []
    for ident, name, category, columns, rows in seed.LISTS:
        if ident == 'tennis_grand_chelem':
            continue
        out.append({
            'id': ident, 'name': name, 'icon': ICONS[ident], 'category': category,
            'columns': ['Numéro', 'Image', *columns],
            'rows': [[str(index + 1), f'thumbs/{ident}/{index + 1}.webp', *row] for index, row in enumerate(rows)],
        })
    return out

def find_array(source, marker):
    start = source.index(marker) + len(marker)
    start = source.index('[', start)
    depth = 0; quote = None; escaped = False
    for pos in range(start, len(source)):
        char = source[pos]
        if quote:
            if escaped: escaped = False
            elif char == '\\': escaped = True
            elif char == quote: quote = None
        elif char == '"': quote = char
        elif char == '[': depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0: return start, pos + 1
    raise RuntimeError('Bloc CURATED_LISTS_V3 non terminé')

def main():
    lists = make_lists()
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps({'schemaVersion': 1, 'lists': lists}, ensure_ascii=False, indent=2), encoding='utf-8')
    source = HTML.read_text(encoding='utf-8')
    start, end = find_array(source, 'const CURATED_LISTS_V3 =')
    source = source[:start] + json.dumps(lists, ensure_ascii=False) + source[end:]
    source = re.sub(r'const APP_DATA_VERSION = \d+;', 'const APP_DATA_VERSION = 77;', source)
    HTML.write_text(source, encoding='utf-8')
    print(f'{len(lists)} listes restaurées, sans résultats de recherche génériques.')

if __name__ == '__main__': main()
