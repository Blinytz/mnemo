#!/usr/bin/env python3
"""Exporte le corpus curatoriel embarqué vers une source JSON versionnée."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / 'memo.html'
OUT = ROOT / 'data' / 'curated_lists.json'

def find_array(source: str, marker: str) -> tuple[int, int]:
    start = source.index(marker) + len(marker)
    start = source.index('[', start)
    depth = 0; quoted = None; escaped = False
    for pos in range(start, len(source)):
        char = source[pos]
        if quoted:
            if escaped: escaped = False
            elif char == '\\': escaped = True
            elif char == quoted: quoted = None
        elif char == '"': quoted = char
        elif char == '[': depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0: return start, pos + 1
    raise RuntimeError('Corpus JSON non terminé')

def main():
    source = HTML.read_text(encoding='utf-8')
    start, end = find_array(source, 'const CURATED_LISTS_V3 =')
    lists = json.loads(source[start:end])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'schemaVersion': 1, 'lists': lists}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{OUT}: {len(lists)} listes exportées')

if __name__ == '__main__': main()
