"""
fix2 — Corrige les doublons inventions + télécharge toutes les images
dans le bon ordre (APRÈS le tri) pour decouvertes, inventions, revolutions.
"""
import sys, json, re, pathlib, requests, time, shutil
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

REPO = pathlib.Path(__file__).parent.parent
HTML_PATH = REPO / 'memo.html'
THUMBS = REPO / 'thumbs'
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
LANG_EN = 'https://en.wikipedia.org/w/api.php'
LANG_FR = 'https://fr.wikipedia.org/w/api.php'

html = open(HTML_PATH, encoding='utf-8').read()
m = re.search(r'const CURATED_LISTS_V3 = (\[[\s\S]*?\]);\s*DEFAULT_LISTS\.push', html)
curated = json.loads(m.group(1))
by_id = {l['id']: l for l in curated}

# ── Wikipedia helpers ──────────────────────────────────────────────────────────

def wiki_img(term, base_url=LANG_EN, skip_svg=True):
    try:
        time.sleep(2.5)
        r = requests.get(base_url, params={
            'action': 'query', 'list': 'search', 'srsearch': term,
            'format': 'json', 'utf8': 1, 'srlimit': 5
        }, headers=HEADERS, timeout=20)
        if not r.content:
            return None
        results = r.json().get('query', {}).get('search', [])
        for result in results:
            time.sleep(1.2)
            r2 = requests.get(base_url, params={
                'action': 'query', 'titles': result['title'],
                'prop': 'pageimages', 'pithumbsize': 400,
                'format': 'json'
            }, headers=HEADERS, timeout=20)
            if not r2.content:
                continue
            for p in r2.json().get('query', {}).get('pages', {}).values():
                src = p.get('thumbnail', {}).get('source', '')
                if src and (not skip_svg or not src.lower().endswith('.svg')):
                    print(f"      → {result['title']}")
                    return src
    except Exception as e:
        print(f"      Erreur: {e}")
    return None

def save_webp(url, path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img = img.resize((200, 150), Image.LANCZOS)
        img.save(path, 'WEBP', quality=82)
        print(f"      Sauvé: {path.name} ({path.stat().st_size}B)")
        return True
    except Exception as e:
        print(f"      Erreur save: {e}")
        return False

# ── 1. Nettoyer les doublons dans inventions_majeures ─────────────────────────

print("=== 1. Nettoyage doublons inventions_majeures ===")
inv = by_id['inventions_majeures']
seen = {}
kept = []
removed = []
for row in inv['rows']:
    titre = row[2] if len(row) > 2 else ''
    if titre not in seen:
        seen[titre] = True
        kept.append(row)
    else:
        removed.append(titre)
        print(f"  Supprimé doublon: {titre}")

# Trier par date
def parse_date(s):
    s = str(s).strip()
    if 'av' in s.lower():
        nums = re.findall(r'\d+', s)
        return (-int(nums[0]) if nums else 9999, s)
    nums = re.findall(r'\d{4}', s)
    if nums:
        return (int(nums[0]), s)
    nums = re.findall(r'\d+', s)
    return (int(nums[0]) if nums else 9998, s)

# Repérer les entrées "siècle" mal datées (les fusionner avec celles à date précise)
# Garder la version avec date précise si double titre
kept_sorted = sorted(kept, key=lambda r: parse_date(r[3] if len(r) > 3 else ''))
for i, row in enumerate(kept_sorted):
    row[0] = str(i + 1)
    row[1] = f'thumbs/inventions_majeures/{i + 1}.webp'
inv['rows'] = kept_sorted
print(f"  → {len(kept_sorted)} entrées après nettoyage")

# ── 2. Définir les termes de recherche par liste ──────────────────────────────

DEC_TERMS = [
    (1,  'Héliocentrisme',                    'Copernican heliocentrism Copernicus',           LANG_EN),
    (2,  'Lois de Kepler',                    'Johannes Kepler laws planetary motion',          LANG_EN),
    (3,  'Circulation sanguine',              'William Harvey blood circulation heart',          LANG_EN),
    (4,  'Calcul différentiel et intégral',   'Leibniz Newton calculus mathematics history',     LANG_EN),
    (5,  'Gravitation universelle',           'Isaac Newton gravity apple Principia',            LANG_EN),
    (6,  'Électricité statique et paratonnerre','Benjamin Franklin lightning kite electricity',  LANG_EN),
    (7,  'Oxygène',                           'Antoine Lavoisier oxygen discovery chemistry',    LANG_EN),
    (8,  'Thermodynamique',                   'Thermodynamics Carnot Kelvin heat engine',        LANG_EN),
    (9,  'Évolution par sélection naturelle', 'Charles Darwin natural selection origin species', LANG_EN),
    (10, 'Ondes électromagnétiques',          'James Clerk Maxwell electromagnetic spectrum',    LANG_EN),
    (11, 'Tableau périodique',                'Mendeleev periodic table elements chemistry',     LANG_EN),
    (12, 'Rayons X',                          'Wilhelm Röntgen X-ray radiograph hand 1895',     LANG_EN),
    (13, 'Radioactivité',                     'Marie Curie radioactivity polonium radium',       LANG_EN),
    (14, 'Relativité restreinte',             'Albert Einstein special relativity 1905',         LANG_EN),
    (15, 'Tectonique des plaques',            'Plate tectonics continental drift Wegener',       LANG_EN),
    (16, 'Mécanique quantique',               'Solvay conference 1927 quantum mechanics',        LANG_EN),
    (17, 'Pénicilline',                       'Alexander Fleming penicillin mold culture',       LANG_EN),
    (18, 'Fission nucléaire',                 'Nuclear fission chain reaction Hahn Meitner',     LANG_EN),
    (19, 'Structure de l\'ADN',              'DNA double helix Watson Crick Franklin 1953',     LANG_EN),
    (20, 'Big Bang (preuves)',                'Cosmic microwave background radiation CMB',        LANG_EN),
    (21, 'Quarks',                            'Quark particle physics Gell-Mann standard model', LANG_EN),
    (22, 'Exoplanètes',                       'Exoplanet discovery transit method telescope',    LANG_EN),
    (23, 'Boson de Higgs',                    'Higgs boson CERN LHC particle detection 2012',   LANG_EN),
    (24, 'Ondes gravitationnelles',           'Gravitational waves LIGO detection 2015',         LANG_EN),
]

INV_TERMS = {
    'Roue':                              'Wheel invention ancient Mesopotamia',
    'Écriture cunéiforme':              'Cuneiform writing Mesopotamia clay tablet',
    'Lunettes':                         'Eyeglasses glasses invention medieval',
    'Imprimerie à caractères mobiles':  'Gutenberg movable type printing press Bible',
    'Presse à imprimer':                'Gutenberg printing press movable type 1450',
    'Thermomètre':                      'Galileo thermometer temperature measurement',
    'Télescope':                        'Galileo telescope astronomy invention',
    'Machine à calculer':               'Blaise Pascal calculator Pascaline machine',
    'Machine à vapeur':                 'James Watt steam engine industrial revolution',
    'Vaccin':                           'Edward Jenner smallpox vaccine cowpox',
    'Locomotive à vapeur':              'Steam locomotive railway George Stephenson',
    'Photographie':                     'Nicéphore Niépce first photograph View Window Gras',
    'Dynamo électrique':                'Electric dynamo generator Faraday electromagnetic',
    'Télégraphe':                       'Samuel Morse telegraph electric communication',
    'Anesthésie':                       'Ether anesthesia surgery Crawford Long Morton',
    'Téléphone':                        'Alexander Graham Bell telephone invention 1876',
    'Moteur à combustion interne':      'Internal combustion engine Otto Benz automobile',
    'Ampoule électrique':               'Thomas Edison light bulb electric lamp filament',
    'Radio':                            'Guglielmo Marconi wireless radio telegraphy',
    'Cinéma':                           'Lumière brothers cinematograph film 1895',
    'Avion motorisé':                   'Wright brothers Kitty Hawk first flight Flyer 1903',
    'Antibiotiques':                    'Alexander Fleming penicillin antibiotic discovery',
    'Radar':                            'Radar invention WWII radio detection ranging',
    'Ordinateur programmable':          'Konrad Zuse Z3 programmable computer Turing',
    'Transistor':                       'Transistor invention Bell Labs Shockley 1947',
    'Satellite artificiel':             'Sputnik Soviet satellite space 1957',
    'Laser':                            'Laser invention Theodore Maiman ruby 1960',
    'Internet':                         'ARPANET internet history packet switching',
    'Web':                              'Tim Berners-Lee World Wide Web HTML hypertext',
    'Boussole':                         'Magnetic compass navigation China ancient invention',
    'Poudre à canon':                   'Gunpowder black powder China medieval invention',
}

REV_TERMS = {
    'Révolution de Cromwell':               'English Civil War Cromwell Roundheads Cavaliers',
    'Révolution anglaise (Glorieuse)':      'Glorious Revolution 1688 William Orange England',
    'Révolution américaine':                'American Revolution independence 1776 Continental',
    'Révolution française':                 'French Revolution 1789 Bastille Paris storming',
    'Révolution haïtienne':                 'Haitian Revolution Toussaint Louverture slavery',
    'Révolution française thermidorienne':  'Thermidorian Reaction 1794 Robespierre guillotine',
    'Indépendances hispano-américaines':    'Latin American independence Simon Bolivar wars',
    'Indépendance du Cône Sud':             'San Martin independence Argentina Chile liberation',
    'Indépendance du Brésil':              'Brazilian independence 1822 Pedro I Empire',
    'Révolution de 1830':                   'Revolution 1830 July Monarchy France Barricades',
    'Révolutions de 1848':                  'Revolutions 1848 Spring of Nations Europe uprising',
    'Révolte des Cipayes':                  'Indian Rebellion 1857 Sepoy Mutiny British',
    'Commune de Paris':                     'Paris Commune 1871 barricades communards',
    'Révolution mexicaine':                 'Mexican Revolution 1910 Zapata Villa Diaz',
    'Révolution chinoise de 1911':          'Chinese Revolution 1911 Sun Yat-sen Qing dynasty',
    'Révolution russe':                     'Russian Revolution 1917 Bolshevik Lenin October',
    'Révolution turque kémaliste':          'Atatürk Turkish revolution Kemal republic Ankara',
    'Révolution espagnole (IIe République)':'Spanish Republic Civil War 1931 Franco war',
    'Indépendance de l\'Inde':             'Indian independence 1947 Gandhi Nehru partition',
    'Révolution cubaine':                   'Cuban Revolution Fidel Castro Guevara 1959',
    'Révolution algérienne':               'Algerian War independence FLN France 1962',
    'Décolonisation africaine':            'African decolonization independence flags nations',
    'Révolution des œillets':              'Carnation Revolution Portugal 1974 military coup',
    'Révolution iranienne':                'Iranian Revolution 1979 Khomeini Shah overthrow',
    'Révolution sandiniste':               'Nicaraguan Revolution Sandinistas Somoza 1979',
    'Révolution de Velours':               'Velvet Revolution Czechoslovakia 1989 peaceful',
    'Chute du Mur de Berlin':             'Fall Berlin Wall 1989 crowd celebrating',
    'Révolution bolivarienne':             'Venezuelan Revolution Hugo Chavez Bolivarian',
    'Révolutions arabes':                  'Arab Spring protests Tunisia Egypt 2011',
    'Révolution ukrainienne (Maïdan)':    'Euromaidan Ukraine revolution 2014 Kyiv protests',
}

# ── 3. Télécharger les images dans le BON ordre ────────────────────────────────

def download_list_images(lst_id, terms_by_num_or_title, num_key='num'):
    print(f"\n=== Images: {lst_id} ===")
    d = THUMBS / lst_id
    # Clear folder
    for f in d.glob('*.webp'):
        f.unlink()
    print(f"  Dossier vidé.")

    lst = by_id[lst_id]
    for row in lst['rows']:
        num = int(row[0])
        titre = row[2] if len(row) > 2 else ''
        path = d / f'{num}.webp'

        if isinstance(terms_by_num_or_title, list):
            # decouvertes: list of (num, titre, term, url)
            entry = next((e for e in terms_by_num_or_title if e[0] == num), None)
            if not entry:
                print(f"  #{num} {titre}: TERME MANQUANT")
                continue
            _, _, term, base = entry
        else:
            # dict by title
            term = terms_by_num_or_title.get(titre)
            if not term:
                print(f"  #{num} {titre}: TERME MANQUANT")
                continue
            base = LANG_EN

        print(f"  #{num} {titre[:40]}")
        src = wiki_img(term, base)
        if src:
            save_webp(src, path)
        else:
            print(f"      ÉCHEC")

# Décide l'ordre de téléchargement : décalage de 60s par liste pour éviter rate-limit
download_list_images('decouvertes_scientifiques', DEC_TERMS)
time.sleep(30)
download_list_images('inventions_majeures', INV_TERMS)
time.sleep(30)

# Revolutions: après tri, les images doivent correspondre au nouvel ordre
rev = by_id['revolutions']
download_list_images('revolutions', REV_TERMS)

# ── 4. Sauvegarder HTML ────────────────────────────────────────────────────────

html_new = html[:m.start(1)] + json.dumps(curated, ensure_ascii=False) + html[m.end(1):]
open(HTML_PATH, 'w', encoding='utf-8', newline='').write(html_new)
print("\nHTML sauvegardé avec données triées et purgées de doublons.")
print(f"  inventions: {len(by_id['inventions_majeures']['rows'])} entrées")
print(f"  decouvertes: {len(by_id['decouvertes_scientifiques']['rows'])} entrées")
print(f"  revolutions: {len(by_id['revolutions']['rows'])} entrées")
