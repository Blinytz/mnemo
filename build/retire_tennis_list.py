#!/usr/bin/env python3
"""Retire la liste de démonstration Grand Chelem des listes par défaut."""
import json, re
from pathlib import Path

path = Path(__file__).resolve().parent.parent / 'memo.html'
html = path.read_text(encoding='utf-8')
match = re.search(r'const CURATED_LISTS_V3 = (\[.*?\]);\nDEFAULT_LISTS\.push', html, re.S)
if not match:
    raise SystemExit('Corpus CURATED_LISTS_V3 introuvable')
lists = json.loads(match.group(1))
icons = {
    'batailles_decisives':'⚔️','grandes_explorations':'🧭','revolutions':'✊',
    'montagnes_monde':'⛰️','mers_oceans':'🌊','detroits_monde':'🗺️','parcs_nationaux':'🌲',
    'architectes_majeurs':'🏛️','musees_monde':'🖼️','inventions_majeures':'⚙️','decouvertes_scientifiques':'🧬',
}
lists = [item for item in lists if item['id'] != 'tennis_grand_chelem']
for item in lists:
    item['icon'] = icons[item['id']]
replacement = 'const CURATED_LISTS_V3 = ' + json.dumps(lists, ensure_ascii=False) + ';\nDEFAULT_LISTS.push'
html = html[:match.start()] + replacement + html[match.end():]
html = re.sub(r'const APP_DATA_VERSION = \d+;', 'const APP_DATA_VERSION = 74;', html)
path.write_text(html, encoding='utf-8')
