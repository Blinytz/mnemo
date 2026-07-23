"""
Remet Évolution et Radioactivité dans decouvertes_scientifiques,
supprime les fichiers images incohérents pour forcer un rebuild propre.
"""
import sys, json, re, pathlib, shutil
sys.stdout.reconfigure(encoding='utf-8')

REPO = pathlib.Path(__file__).parent.parent
HTML = REPO / 'memo.html'
THUMBS = REPO / 'thumbs' / 'decouvertes_scientifiques'

html = open(HTML, encoding='utf-8').read()
m = re.search(r'const CURATED_LISTS_V3 = (\[[\s\S]*?\]);\s*DEFAULT_LISTS\.push', html)
curated = json.loads(m.group(1))
dec = next(l for l in curated if l['id'] == 'decouvertes_scientifiques')

print(f"Avant : {len(dec['rows'])} entrées")

# Entrées à ré-injecter avec leurs colonnes : [num, img, Découverte, Date, Domaine, Repère]
# On les insère à la bonne place chronologiquement
# Évolution (1859) : après Tableau périodique (1869) ? Non, 1859 < 1869.
# Le tri n'est pas forcément chronologique, on les ajoute à la fin et on laisse le build les numéroter.

NEW_ENTRIES = [
    # Évolution par sélection naturelle (1859)
    ['', 'thumbs/decouvertes_scientifiques/_.webp',
     'Évolution par sélection naturelle', '1859', 'Biologie',
     'Charles Darwin publie "De l\'origine des espèces", posant les bases de la théorie de l\'évolution par sélection naturelle.'],
    # Radioactivité (1896)
    ['', 'thumbs/decouvertes_scientifiques/_.webp',
     'Radioactivité', '1896', 'Physique / Chimie',
     'Henri Becquerel découvre la radioactivité naturelle en observant que l\'uranium impressionne les plaques photographiques.'],
]

rows = dec['rows']
rows.extend(NEW_ENTRIES)

# Renuméroter
for i, row in enumerate(rows):
    row[0] = str(i + 1)
    row[1] = f'thumbs/decouvertes_scientifiques/{i + 1}.webp'

dec['rows'] = rows
print(f"Après : {len(dec['rows'])} entrées")
for r in rows:
    print(f"  {r[0]}. {r[2]}")

html = html[:m.start(1)] + json.dumps(curated, ensure_ascii=False) + html[m.end(1):]
open(HTML, 'w', encoding='utf-8', newline='').write(html)
print("\nHTML sauvegardé.")

# Supprimer les images pour forcer un rebuild propre
if THUMBS.exists():
    shutil.rmtree(THUMBS)
    THUMBS.mkdir()
    print(f"Dossier {THUMBS.name} vidé — prêt pour rebuild.")
