#!/usr/bin/env python3
"""Injecte uniquement un corpus validé dans memo.html."""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'curated_lists.json'
HTML = ROOT / 'memo.html'

def main():
    check = subprocess.run([sys.executable, str(Path(__file__).with_name('validate_curated_corpus.py'))], cwd=ROOT)
    if check.returncode:
        raise SystemExit('Injection refusée: le corpus doit passer la validation.')
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    source = HTML.read_text(encoding='utf-8')
    replacement = 'const CURATED_LISTS_V3 = ' + json.dumps(payload['lists'], ensure_ascii=False) + ';\nDEFAULT_LISTS.push(...CURATED_LISTS_V3);'
    source, count = re.subn(r'const CURATED_LISTS_V3 = \[.*?\];\nDEFAULT_LISTS\.push\(\.\.\.CURATED_LISTS_V3\);', replacement, source, flags=re.S)
    if count != 1: raise SystemExit('Bloc CURATED_LISTS_V3 introuvable.')
    source = re.sub(r'const APP_DATA_VERSION = \d+;', 'const APP_DATA_VERSION = 76;', source)
    HTML.write_text(source, encoding='utf-8')
    print('Corpus injecté.')

if __name__ == '__main__': main()
