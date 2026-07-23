#!/usr/bin/env python3
"""Contrôle qualité du corpus: densité, colonnes, catégories et données utiles."""
from __future__ import annotations
import json, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / 'data' / 'curated_lists.json'
MIN_ENTRIES = 30
VALID_CATEGORIES = {'Histoire','Géographie','Arts & culture','Sciences & nature','Sports & loisirs','Langues & vocabulaire'}

def main():
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    failures = []
    for item in payload['lists']:
        name = item.get('name', item.get('id', '?'))
        rows, columns = item.get('rows', []), item.get('columns', [])
        if len(rows) < MIN_ENTRIES: failures.append(f'{name}: {len(rows)}/{MIN_ENTRIES} entrées')
        if item.get('category') not in VALID_CATEGORIES: failures.append(f'{name}: catégorie invalide')
        if not item.get('icon'): failures.append(f'{name}: icône absente')
        if len(columns) < 4: failures.append(f'{name}: schéma trop pauvre')
        for index, row in enumerate(rows, 1):
            if len(row) != len(columns): failures.append(f'{name} ligne {index}: {len(row)}/{len(columns)} cellules')
    if failures:
        print('\n'.join(failures)); sys.exit(1)
    print(f'Corpus valide: {len(payload["lists"])} listes')

if __name__ == '__main__': main()
