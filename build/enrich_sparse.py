#!/usr/bin/env python3
"""Enrichit les 4 listes CURATED sparse + ajoute EXTRA_VOCAB pour vocabulaire_precis."""
import sys, json, re, pathlib
sys.stdout.reconfigure(encoding='utf-8')

REPO = pathlib.Path(__file__).parent.parent
HTML = REPO / 'memo.html'

# ── Nouvelles entrées CURATED ────────────────────────────────────────────────

NEW_REVOLUTIONS = [
    ['Révolution anglaise (Glorieuse)', '1688', 'Angleterre', 'Monarchie constitutionnelle'],
    ['Indépendances hispano-américaines', '1810-1826', 'Amérique latine', 'Bolivar, San Martín'],
    ['Indépendance du Brésil', '1822', 'Brésil', 'Empire sous Dom Pedro Ier'],
    ['Révolution de 1830', '1830', 'France / Europe', 'Monarchie de Juillet'],
    ['Commune de Paris', '1871', 'France', 'Première insurrection ouvrière parisienne'],
    ['Révolution de Cromwell', '1642-1651', 'Angleterre', 'Guerre civile et République'],
    ['Révolution chinoise de 1911', '1911', 'Chine', 'Fin de la dynastie Qing'],
    ['Révolution turque kémaliste', '1919-1923', 'Turquie', 'Fondation de la République'],
    ['Révolte des Cipayes', '1857', 'Inde', 'Rébellion contre la Compagnie des Indes'],
    ['Révolution des œillets', '1974', 'Portugal', 'Fin du salazarisme'],
    ['Indépendance de l\'Inde', '1947', 'Inde', 'Gandhi et la non-violence'],
    ['Révolution algérienne', '1954-1962', 'Algérie', 'Indépendance vis-à-vis de la France'],
    ['Décolonisation africaine', '1956-1975', 'Afrique subsaharienne', 'Vague d\'indépendances'],
    ['Révolution iranienne', '1979', 'Iran', 'République islamique de Khomeini'],
    ['Révolution sandiniste', '1979', 'Nicaragua', 'Renversement de Somoza'],
    ['Chute du Mur de Berlin', '1989', 'Allemagne', 'Réunification allemande'],
    ['Révolutions arabes', '2010-2012', 'Monde arabe', 'Printemps arabe'],
    ['Révolution ukrainienne (Maïdan)', '2013-2014', 'Ukraine', 'Renversement de Ianoukovitch'],
    ['Révolution bolivarienne', '1999-', 'Venezuela', 'Hugo Chávez'],
    ['Révolution française thermidorienne', '1794', 'France', 'Chute de Robespierre'],
    ['Révolution espagnole (IIe République)', '1931-1939', 'Espagne', 'Guerre civile et franquisme'],
    ['Indépendance du Cône Sud', '1816-1818', 'Argentine / Chili', 'San Martín et O\'Higgins'],
]

NEW_MERS_OCEANS = [
    ['Océan Austral', '20,3 millions km²', 'Austral', 'Autour de l\'Antarctique'],
    ['Mer de Chine méridionale', '3,5 millions km²', 'Pacifique', 'Zone de conflits territoriaux'],
    ['Mer de Corail', '4,8 millions km²', 'Pacifique', 'Grande Barrière de corail'],
    ['Mer de Tasman', '2,3 millions km²', 'Pacifique', 'Entre Australie et Nouvelle-Zélande'],
    ['Mer d\'Arabie', '3,8 millions km²', 'Indien', 'Entre Péninsule arabique et Inde'],
    ['Mer d\'Oman', '2,0 millions km²', 'Indien', 'Entre Oman, Pakistan et Iran'],
    ['Golfe du Mexique', '1,5 million km²', 'Atlantique', 'Pétrole et cyclones'],
    ['Golfe Persique', '251 000 km²', 'Indien', 'Réserves pétrolières majeures'],
    ['Mer du Nord', '575 000 km²', 'Atlantique', 'Entre Royaume-Uni et Europe continentale'],
    ['Mer Noire', '436 000 km²', 'Méditerranée', 'Turquie, Ukraine, Russie'],
    ['Mer Caspienne', '371 000 km²', 'Lac endoréique', 'Plus grand lac du monde'],
    ['Mer Égée', '214 000 km²', 'Méditerranée', 'Grèce et Turquie'],
]

NEW_INVENTIONS = [
    ['Roue', 'v. 3500 av. J.-C.', 'Transport', 'Mésopotamie'],
    ['Écriture cunéiforme', 'v. 3400 av. J.-C.', 'Communication', 'Sumer'],
    ['Boussole', 'IXe siècle', 'Navigation', 'Chine'],
    ['Poudre à canon', 'IXe siècle', 'Militaire', 'Chine'],
    ['Lunettes', 'v. 1286', 'Optique', 'Italie du Nord'],
    ['Presse à imprimer', '1450', 'Communication', 'Gutenberg'],
    ['Thermomètre', '1592', 'Mesure', 'Galilée / Sanctorius'],
    ['Machine à calculer', '1642', 'Calcul', 'Pascal (Pascaline)'],
    ['Machine à vapeur', '1769', 'Énergie', 'James Watt'],
    ['Vaccin', '1796', 'Médecine', 'Jenner (variole)'],
    ['Locomotive à vapeur', '1804', 'Transport', 'Trevithick'],
    ['Photographie', '1826', 'Image', 'Niépce / Daguerre'],
    ['Anesthésie', '1846', 'Médecine', 'Morton (éther)'],
    ['Dynamo électrique', '1831', 'Énergie', 'Faraday'],
    ['Moteur à combustion interne', '1876', 'Transport', 'Otto'],
    ['Ampoule électrique', '1879', 'Éclairage', 'Edison'],
    ['Téléphone', '1876', 'Communication', 'Bell'],
    ['Radio', '1895', 'Communication', 'Marconi / Popov'],
    ['Cinéma', '1895', 'Audiovisuel', 'Frères Lumière'],
    ['Avion motorisé', '1903', 'Transport', 'Frères Wright'],
    ['Antibiotiques', '1928', 'Médecine', 'Fleming (pénicilline)'],
    ['Ordinateur programmable', '1936', 'Informatique', 'Turing / Zuse'],
    ['Radar', '1935', 'Détection', 'Watson-Watt'],
    ['Transistor', '1947', 'Électronique', 'Bell Labs'],
    ['Satellite artificiel', '1957', 'Espace', 'Spoutnik (URSS)'],
    ['Internet', '1969', 'Communication', 'ARPANET / Berners-Lee'],
    ['Laser', '1960', 'Optique', 'Maiman'],
]

NEW_DECOUVERTES = [
    ['Lois de Kepler', '1609-1619', 'Astronomie', 'Mouvement des planètes'],
    ['Circulation sanguine', '1628', 'Médecine', 'Harvey'],
    ['Calcul différentiel et intégral', '1665-1684', 'Mathématiques', 'Newton / Leibniz'],
    ['Loi de la gravitation universelle', '1687', 'Physique', 'Newton'],
    ['Électricité statique et paratonnerre', '1752', 'Physique', 'Franklin'],
    ['Oxygène et combustion', '1774', 'Chimie', 'Lavoisier'],
    ['Thermodynamique', '1842-1865', 'Physique', 'Joule, Clausius'],
    ['Ondes électromagnétiques', '1864', 'Physique', 'Maxwell'],
    ['Évolution par sélection naturelle', '1859', 'Biologie', 'Darwin'],
    ['Tableau périodique des éléments', '1869', 'Chimie', 'Mendéleïev'],
    ['Rayons X', '1895', 'Médecine / Physique', 'Röntgen'],
    ['Radioactivité', '1896', 'Physique', 'Becquerel / Marie Curie'],
    ['Relativité restreinte', '1905', 'Physique', 'Einstein'],
    ['Mécanique quantique', '1925-1927', 'Physique', 'Heisenberg, Schrödinger'],
    ['Fission nucléaire', '1938', 'Physique nucléaire', 'Hahn, Strassmann, Meitner'],
    ['Structure de l\'ADN (double hélice)', '1953', 'Biologie', 'Watson, Crick, Franklin'],
    ['Tectonique des plaques', '1912-1960', 'Géologie', 'Wegener, Hess'],
    ['Big Bang (preuves)', '1964', 'Cosmologie', 'Penzias & Wilson (rayonnement fossile)'],
    ['Quarks', '1964', 'Physique des particules', 'Gell-Mann'],
    ['Boson de Higgs', '2012', 'Physique des particules', 'CERN'],
    ['Ondes gravitationnelles', '2015', 'Astronomie', 'LIGO'],
    ['Exoplanètes', '1992-1995', 'Astronomie', 'Wolszczan / Mayor & Queloz'],
]

EXTRA_VOCAB = [
    ('Épistémique', 'Relatif à la connaissance et à ses fondements.', 'Philosophie', 'La question épistémique porte sur la validité du savoir.'),
    ('Heuristique', 'Méthode de résolution par approximation et essais.', 'Sciences / Pédagogie', 'Une approche heuristique favorise la découverte autonome.'),
    ('Tautologie', 'Répétition d\'une idée sous une forme différente sans apport nouveau.', 'Logique', '« Il est mort car il a cessé de vivre » est une tautologie.'),
    ('Paralogisme', 'Raisonnement faux commis de bonne foi.', 'Logique', 'Confondre corrélation et causalité est un paralogisme courant.'),
    ('Sophisme', 'Argument délibérément trompeur mais apparemment correct.', 'Rhétorique', 'L\'argument ad hominem est un sophisme classique.'),
    ('Catharsis', 'Purification émotionnelle provoquée par l\'art ou le théâtre.', 'Littérature / Psychologie', 'Aristote décrit la catharsis dans sa Poétique.'),
    ('Axiome', 'Proposition admise sans démonstration comme point de départ.', 'Mathématiques / Philosophie', 'Les axiomes d\'Euclide fondent la géométrie classique.'),
    ('Corollaire', 'Conséquence directe d\'une proposition déjà démontrée.', 'Mathématiques', 'Ce corollaire découle immédiatement du théorème.'),
    ('Ostracisme', 'Exclusion d\'un individu d\'un groupe ou d\'une société.', 'Histoire / Usage courant', 'L\'ostracisme athénien bannissait les personnalités gênantes.'),
    ('Parangon', 'Modèle exemplaire d\'une qualité.', 'Littérature', 'Ce diplomate est un parangon de sagesse.'),
    ('Acrimonie', 'Aigreur ou amertume dans les paroles.', 'Psychologie', 'Il répondit avec une acrimonie inattendue.'),
    ('Péjoratif', 'Qui déprécie ou donne un sens défavorable.', 'Linguistique', 'Le mot « politicien » peut avoir une connotation péjorative.'),
    ('Équivoque', 'Qui peut être interprété de plusieurs façons ambiguës.', 'Communication', 'Sa réponse était volontairement équivoque.'),
    ('Contingent', 'Qui peut être ou ne pas être, non nécessaire.', 'Philosophie', 'La mort est certaine, mais sa date est contingente.'),
    ('Résilience', 'Capacité à se reconstruire après une épreuve.', 'Psychologie / Usage courant', 'La résilience permet de surmonter les traumatismes.'),
    ('Pléonasme', 'Emploi de mots redondants.', 'Grammaire', '« Monter en haut » est un pléonasme.'),
    ('Paradigme', 'Modèle de référence qui structure une discipline.', 'Sciences / Philosophie', 'Kuhn décrit les révolutions de paradigme scientifique.'),
    ('Aporie', 'Difficulté logique sans solution apparente.', 'Philosophie', 'Le paradoxe de Zénon est une célèbre aporie.'),
    ('Litote', 'Atténuation d\'une idée par la négation de son contraire.', 'Rhétorique', '« Ce n\'est pas mal » pour dire « c\'est très bien » est une litote.'),
    ('Métonymie', 'Figure de style désignant une chose par une autre liée.', 'Rhétorique', '« Boire un verre » (le contenu pour le contenant) est une métonymie.'),
    ('Oxymore', 'Alliance de deux termes contradictoires.', 'Rhétorique', '« Un silence assourdissant » est un oxymore.'),
    ('Allitération', 'Répétition de consonnes identiques pour un effet sonore.', 'Poésie', '« Pour qui sont ces serpents qui sifflent sur vos têtes ? »'),
    ('Assonance', 'Répétition de voyelles pour un effet musical.', 'Poésie', 'L\'assonance en « i » crée une impression aiguë.'),
    ('Prolepse', 'Figure rhétorique qui anticipe une objection pour la réfuter.', 'Rhétorique', 'La prolepse renforce l\'argument en répondant d\'avance.'),
]

# ── Patch ────────────────────────────────────────────────────────────────────

html = open(HTML, encoding='utf-8').read()

# 1. Enrichir CURATED_LISTS_V3
m = re.search(r'const CURATED_LISTS_V3 = (\[[\s\S]*?\]);\s*DEFAULT_LISTS\.push', html)
curated = json.loads(m.group(1))
by_id = {l['id']: l for l in curated}

def extend(lst_id, new_rows_data):
    lst = by_id[lst_id]
    n = len(lst['rows'])
    for i, row_data in enumerate(new_rows_data):
        num = str(n + i + 1)
        lst['rows'].append([num, f'thumbs/{lst_id}/{num}.webp'] + list(row_data))
    print(f'  {lst_id}: {n} -> {len(lst["rows"])} entrées')

extend('revolutions', NEW_REVOLUTIONS)
extend('mers_oceans', NEW_MERS_OCEANS)
extend('inventions_majeures', NEW_INVENTIONS)
extend('decouvertes_scientifiques', NEW_DECOUVERTES)

html = html[:m.start(1)] + json.dumps(curated, ensure_ascii=False) + html[m.end(1):]

# 2. Insérer EXTRA_VOCAB avant vocabulaireList.rows.sort
anchor = 'vocabulaireList.rows.sort'
assert anchor in html, f'anchor introuvable: {anchor}'

def esc(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")

rows_js = ',\n  '.join(
    f"['{esc(mot)}','{esc(defn)}','{esc(dom)}','{esc(ex)}']"
    for mot, defn, dom, ex in EXTRA_VOCAB
)
extra_block = (
    "const EXTRA_VOCAB = [\n  " + rows_js + "\n];\n"
    "const vocabulaireList2 = DEFAULT_LISTS.find(list => list.id === 'vocabulaire_precis');\n"
    "const existingVocab = new Set(vocabulaireList2.rows.map(row => row[1]));\n"
    "EXTRA_VOCAB.forEach(item => {\n"
    "  if (!existingVocab.has(item[0])) {\n"
    "    vocabulaireList2.rows.push([String(vocabulaireList2.rows.length + 1), ...item]);\n"
    "  }\n"
    "});\n\n"
)
html = html.replace(anchor, extra_block + anchor, 1)
print(f'  vocabulaire_precis: 16 + {len(EXTRA_VOCAB)} extras = {16 + len(EXTRA_VOCAB)} entrées')

open(HTML, 'w', encoding='utf-8', newline='').write(html)
print(f'\nSaved {HTML.name}')
