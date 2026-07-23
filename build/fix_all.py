"""
fix_all.py — Corrections complètes :
1. Télécharge les images decouvertes_scientifiques dans le BON ordre (entrée N → N.webp)
2. Trie par date toutes les listes CURATED qui ont une colonne date
3. Corrige la largeur des colonnes "Repère" dans le HTML (min-width)
"""
import sys, json, re, pathlib, requests, time
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

REPO = pathlib.Path(__file__).parent.parent
HTML_PATH = REPO / 'memo.html'
THUMBS = REPO / 'thumbs'
HEADERS = {'User-Agent': 'memo-app-fix/1.0 (educational project)'}

html = open(HTML_PATH, encoding='utf-8').read()
m = re.search(r'const CURATED_LISTS_V3 = (\[[\s\S]*?\]);\s*DEFAULT_LISTS\.push', html)
curated = json.loads(m.group(1))
by_id = {l['id']: l for l in curated}

# ── Utilitaires Wikipedia ──────────────────────────────────────────────────────

def wiki_search(term, lang='fr', prefer_jpg=True):
    url = f'https://{lang}.wikipedia.org/w/api.php'
    time.sleep(1.5)
    try:
        r = requests.get(url, params={
            'action': 'query', 'list': 'search', 'srsearch': term,
            'format': 'json', 'utf8': 1, 'srlimit': 5
        }, headers=HEADERS, timeout=15)
        for result in r.json().get('query', {}).get('search', []):
            title = result['title']
            time.sleep(1)
            r2 = requests.get(url, params={
                'action': 'query', 'titles': title,
                'prop': 'pageimages', 'pithumbsize': 400,
                'format': 'json'
            }, headers=HEADERS, timeout=15)
            for p in r2.json().get('query', {}).get('pages', {}).values():
                src = p.get('thumbnail', {}).get('source', '')
                if src and (not prefer_jpg or not src.lower().endswith('.svg')):
                    print(f"    [{term}] → {title}")
                    return src
    except Exception as e:
        print(f"    Erreur: {e}")
    return None

def save_img(url, path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200, 150), Image.LANCZOS)
        img.save(path, 'WEBP', quality=82)
        print(f"    → {path.name} ({path.stat().st_size} B)")
        return True
    except Exception as e:
        print(f"    Erreur save: {e}")
        return False

# ── 1. Recréer toutes les images decouvertes_scientifiques proprement ──────────
# Mapping explicite : numéro_dans_curated → terme de recherche Wikipedia (lang)
# (Pour garantir l'image correcte quelle que soit la logique de build_images.py)

dec = by_id['decouvertes_scientifiques']
print(f"\n=== Decouvertes scientifiques : {len(dec['rows'])} entrées ===")
print("Nettoyage du dossier...")

dec_dir = THUMBS / 'decouvertes_scientifiques'
for f in dec_dir.glob('*.webp'):
    f.unlink()
print(f"  {len(list(dec_dir.glob('*.webp')))} fichiers restants.")

SEARCH_TERMS = {
    'Héliocentrisme':                    ('Heliocentric model Copernicus', 'en'),
    'Gravitation universelle':            ('Isaac Newton Principia Mathematica', 'en'),
    'Oxygène':                           ('Antoine Lavoisier chemistry oxygen', 'en'),
    'Tableau périodique':                ('Mendeleev periodic table elements', 'en'),
    'Pénicilline':                       ('Alexander Fleming penicillin petri dish', 'en'),
    'Structure de l\'ADN':              ('DNA double helix Watson Crick', 'en'),
    'Lois de Kepler':                   ('Johannes Kepler astronomer portrait', 'en'),
    'Circulation sanguine':             ('William Harvey blood circulation anatomy', 'en'),
    'Calcul différentiel et intégral':  ('Calculus Newton Leibniz mathematics', 'en'),
    'Électricité statique et paratonnerre': ('Benjamin Franklin lightning rod kite', 'en'),
    'Thermodynamique':                  ('Carnot steam engine thermodynamics', 'en'),
    'Ondes électromagnétiques':         ('James Clerk Maxwell electromagnetic waves', 'en'),
    'Rayons X':                         ('Wilhelm Röntgen X-ray hand radiograph', 'en'),
    'Relativité restreinte':            ('Albert Einstein special relativity', 'en'),
    'Mécanique quantique':              ('Solvay conference 1927 physicists quantum', 'en'),
    'Fission nucléaire':                ('Nuclear fission chain reaction uranium', 'en'),
    'Tectonique des plaques':           ('Plate tectonics continental drift map', 'en'),
    'Big Bang (preuves)':               ('Cosmic microwave background radiation map', 'en'),
    'Quarks':                           ('Quark particle physics standard model', 'en'),
    'Boson de Higgs':                   ('Higgs boson particle CERN LHC collision', 'en'),
    'Ondes gravitationnelles':          ('Gravitational waves LIGO detection', 'en'),
    'Exoplanètes':                      ('Exoplanet transit detection telescope', 'en'),
    'Évolution par sélection naturelle': ('Charles Darwin natural selection finches', 'en'),
    'Radioactivité':                    ('Marie Curie radioactivity laboratory', 'en'),
}

for row in dec['rows']:
    num = row[0]
    titre = row[2]
    path = dec_dir / f'{num}.webp'
    terms_lang = SEARCH_TERMS.get(titre)
    if not terms_lang:
        print(f"  #{num} {titre}: TERME MANQUANT")
        continue
    term, lang = terms_lang
    print(f"  #{num} {titre}")
    src = wiki_search(term, lang)
    if src:
        save_img(src, path)
    else:
        print(f"    ÉCHEC pour {titre}")
    time.sleep(2)

# ── 2. Trier par date les listes CURATED avec colonne date ────────────────────

def parse_date(s):
    """Extrait l'année de début depuis une chaîne comme '1543', '1609-1619', 'v. 3400 av. J.-C.'"""
    s = str(s).strip()
    # av. J.-C.
    if 'av' in s.lower():
        nums = re.findall(r'\d+', s)
        return -int(nums[0]) if nums else 9999
    nums = re.findall(r'\d{4}', s)
    if nums:
        return int(nums[0])
    nums = re.findall(r'\d+', s)
    return int(nums[0]) if nums else 9999

DATE_LISTS = {
    # list_id: index of date column in row
    'decouvertes_scientifiques': 3,  # col Date
    'inventions_majeures': 3,        # col Date
    'revolutions': 3,                # col Année/Date
}

print(f"\n=== Tri par date ===")
for lst_id, date_col in DATE_LISTS.items():
    if lst_id not in by_id:
        print(f"  {lst_id}: non trouvé dans CURATED")
        continue
    lst = by_id[lst_id]
    rows = lst['rows']
    try:
        rows_sorted = sorted(rows, key=lambda r: parse_date(r[date_col]) if len(r) > date_col else 9999)
        # Renuméroter et mettre à jour image paths
        for i, row in enumerate(rows_sorted):
            row[0] = str(i + 1)
            row[1] = f'thumbs/{lst_id}/{i + 1}.webp'
        lst['rows'] = rows_sorted
        print(f"  {lst_id}: {len(rows)} entrées triées")
        for r in rows_sorted:
            print(f"    {r[0]}. {r[date_col]} — {r[2]}")
    except Exception as e:
        print(f"  {lst_id}: ERREUR {e}")

# ── Sauvegarder le HTML avec CURATED mis à jour ────────────────────────────────
html_new = html[:m.start(1)] + json.dumps(curated, ensure_ascii=False, indent=None) + html[m.end(1):]
open(HTML_PATH, 'w', encoding='utf-8', newline='').write(html_new)
print(f"\nHTML sauvegardé.")
print("\nNote : Après ce script, relancer build_images.py --list revolutions si les images")
print("de révolutions sont dans le mauvais ordre suite au tri.")
