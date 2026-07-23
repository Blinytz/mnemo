#!/usr/bin/env python3
"""
Corrige les images de mauvaise qualité et les doublons dans les listes enrichies.
1. Supprime les entrées en doublon dans decouvertes_scientifiques
2. Re-télécharge les images hors-sujet avec de meilleurs termes de recherche
"""
import sys, json, re, pathlib, requests, time
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

REPO = pathlib.Path(__file__).parent.parent
HTML = REPO / 'memo.html'
THUMBS = REPO / 'thumbs'
HEADERS = {'User-Agent': 'memo-app-build/1.0'}

# ── 1. Supprimer les doublons dans decouvertes_scientifiques ──────────────────

html = open(HTML, encoding='utf-8').read()
m = re.search(r'const CURATED_LISTS_V3 = (\[[\s\S]*?\]);\s*DEFAULT_LISTS\.push', html)
curated = json.loads(m.group(1))
by_id = {l['id']: l for l in curated}

dec = by_id['decouvertes_scientifiques']
print(f"decouvertes avant : {len(dec['rows'])} entrées")

# Titres à supprimer (doublons des 8 originales)
DOUBLONS = {
    'Loi de la gravitation universelle',   # doublon de "Gravitation universelle"
    'Oxygène et combustion',               # doublon de "Oxygène"
    'Évolution par sélection naturelle',   # doublon exact
    'Tableau périodique des éléments',     # doublon de "Tableau périodique"
    'Radioactivité',                       # doublon exact (col Découverte = row[2])
    'Structure de l\'ADN (double hélice)', # doublon de "Structure de l'ADN"
}

# Col Découverte = row[2] pour decouvertes
kept = []
removed = []
for row in dec['rows']:
    titre = row[2]
    if titre in DOUBLONS:
        removed.append(titre)
    else:
        kept.append(row)

# Renuméroter
for i, row in enumerate(kept):
    row[0] = str(i + 1)
    # Mettre à jour le chemin image aussi
    row[1] = f'thumbs/decouvertes_scientifiques/{i + 1}.webp'

dec['rows'] = kept
print(f"  Supprimés : {removed}")
print(f"decouvertes après : {len(dec['rows'])} entrées")

html = html[:m.start(1)] + json.dumps(curated, ensure_ascii=False) + html[m.end(1):]
open(HTML, 'w', encoding='utf-8', newline='').write(html)
print("HTML sauvegardé.\n")

# ── 2. Renommer les fichiers images pour correspondre aux nouveaux numéros ────

dec_dir = THUMBS / 'decouvertes_scientifiques'
# Construire la table de mapping ancien numéro → nouveau numéro
# Les titres gardés dans l'ordre originel avec leur ancien index
html_orig = open(HTML, encoding='utf-8').read()  # reload
m2 = re.search(r'const CURATED_LISTS_V3 = (\[[\s\S]*?\]);\s*DEFAULT_LISTS\.push', html_orig)
# On relit les titres originaux pour retrouver le mapping
# Méthode simple : les fichiers existants correspondent aux anciennes positions
# On relit le HTML AVANT la sauvegarde via une sauvegarde temporaire — trop complexe.
# À la place, on supprime les fichiers des doublons et on ré-indexe avec build_images.py
print("Note : les fichiers images seront réindexés au prochain build --list decouvertes_scientifiques")

# ── 3. Re-télécharger les images hors-sujet ──────────────────────────────────

def wiki_search_image(terms, lang='fr'):
    """Essaie plusieurs termes et retourne la première URL d'image trouvée."""
    url = f'https://{lang}.wikipedia.org/w/api.php'
    for term in terms:
        try:
            r = requests.get(url, params={
                'action': 'query', 'list': 'search', 'srsearch': term,
                'format': 'json', 'utf8': 1, 'srlimit': 3
            }, headers=HEADERS, timeout=10)
            results = r.json().get('query', {}).get('search', [])
            if not results:
                continue
            for result in results:
                title = result['title']
                r2 = requests.get(url, params={
                    'action': 'query', 'titles': title,
                    'prop': 'pageimages', 'pithumbsize': 400,
                    'format': 'json'
                }, headers=HEADERS, timeout=10)
                pages = r2.json().get('query', {}).get('pages', {})
                for p in pages.values():
                    src = p.get('thumbnail', {}).get('source')
                    if src:
                        print(f"  [{term}] → {title}")
                        return src
        except Exception as e:
            print(f"  Erreur: {e}")
        time.sleep(1)
    return None

def save_webp(url, path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200, 150), Image.LANCZOS)
        img.save(path, 'WEBP', quality=82)
        print(f"  → Sauvegardé : {path.name}")
        return True
    except Exception as e:
        print(f"  Erreur save: {e}")
        return False

# Table des corrections : (liste, numéro, [termes de recherche], langue)
CORRECTIONS = [
    # Révolutions
    ('revolutions', 17, ['Indian Rebellion 1857 Sepoy Mutiny', 'Révolte des cipayes 1857 bataille'], 'en'),
    ('revolutions', 27, ['Hugo Chavez Venezuela revolution', 'Révolution bolivarienne Venezuela'], 'en'),
    ('revolutions', 29, ['Segunda República española 1931', 'Spanish Civil War Second Republic'], 'en'),

    # Inventions
    ('inventions_majeures', 12, ['Poudre à canon histoire', 'Gunpowder black powder history'], 'en'),
    ('inventions_majeures', 20, ['Niépce daguerreotype first photograph', 'Daguerréotype premier', 'Joseph Nicéphore Niépce'], 'en'),
    ('inventions_majeures', 21, ['Crawford Long ether anesthesia 1842', 'Diethyl ether anesthesia history'], 'en'),
    ('inventions_majeures', 26, ['Guglielmo Marconi radio wireless', 'Marconi radio transmitter'], 'en'),
    ('inventions_majeures', 27, ['Cinématographe Lumière brothers 1895', 'Auguste Louis Lumière cinematograph'], 'en'),
    ('inventions_majeures', 28, ['Wright brothers Kitty Hawk Flyer 1903', 'Wright Flyer first flight'], 'en'),
    ('inventions_majeures', 29, ['Alexander Fleming penicillin mold', 'Pénicilline Fleming découverte'], 'en'),

    # Découvertes
    ('decouvertes_scientifiques', 3, ['Antoine Lavoisier oxygène chimie', 'Lavoisier oxygen experiment'], 'en'),
]

print("\n── Re-téléchargement des images hors-sujet ──")
for lst_id, num, terms, lang in CORRECTIONS:
    path = THUMBS / lst_id / f'{num}.webp'
    print(f"\n[{lst_id}] #{num} ({terms[0][:40]}...)")
    src = wiki_search_image(terms, lang)
    if src:
        save_webp(src, path)
    else:
        print(f"  ÉCHEC — aucune image trouvée")
    time.sleep(2)

print("\n\nTerminé. Relancer build_images.py --list <liste> pour patcher le HTML.")
