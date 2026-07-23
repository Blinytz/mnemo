"""Retire les entrees 24-41 du tableau DEFAULT_LISTS de base (elles doublonnent EXPANSION + CURATED)."""
import sys, re, json, pathlib
sys.stdout.reconfigure(encoding='utf-8')

REPO = pathlib.Path(__file__).parent.parent
html = open(REPO / 'memo.html', encoding='utf-8').read()

# Localiser le tableau DEFAULT_LISTS
m = re.search(r'const DEFAULT_LISTS = (\[)', html)
start = m.start(1)

# Trouver la fermeture du tableau
depth = 0
i = start
while i < len(html):
    if html[i] == '[': depth += 1
    elif html[i] == ']':
        depth -= 1
        if depth == 0: break
    i += 1
end = i + 1  # juste après le ]

base_json = html[start:end]
base_lists = json.loads(base_json)
print(f'Avant: {len(base_lists)} listes dans DEFAULT_LISTS')

BASE_IDS = {
    'chefs_etat','departements','elements','etats_usa','mythologie','os','pays',
    'peintres','rois_france','coupes_monde','xixe','xxe','litterature','guerres',
    'philosophes','mouvements_peinture','jo_ete','jo_hiver','f1_champions',
    'consoles','lunes','periodes_geologiques','films'
}

base_only = [l for l in base_lists if l['id'] in BASE_IDS]
print(f'Après: {len(base_only)} listes dans DEFAULT_LISTS')

new_json = json.dumps(base_only, ensure_ascii=False)
new_html = html[:start] + new_json + html[end:]
open(REPO / 'memo.html', 'w', encoding='utf-8', newline='').write(new_html)
print('Saved.')
