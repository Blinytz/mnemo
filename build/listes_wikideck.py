#!/usr/bin/env python3
"""Listes Memo construites a partir des collections WikiDeck.

WikiDeck fournit les elements et leurs images cadrees a la main ; les colonnes
d'apprentissage (dates, auteur, region...) sont redigees a part, relues, puis
rangees dans build/listes_wikideck/<slug>.json. Ce script en fait des listes
Memo :

  - images : recoupees dans l'original WikiDeck selon son cadrage, ecrites en
    thumbs/<liste>/<cle>.webp (400 x 300) et full/<liste>/<cle>.webp (au plus
    2000 x 1500), la cle etant le nom de la carte (jamais un rang : un rang
    change des qu'on ajoute un element) ;
  - memo.html : un bloc WIKIDECK_LISTS, pose juste apres l'ajout de
    CURATED_LISTS_V3, remplace les listes de meme identifiant ou s'ajoute ;
    les grandes images vont dans IMAGE_FILES_MAP ; la migration v47 (qui
    reimpose des images par rang) est ecartee pour ces listes.

Usage : python build/listes_wikideck.py            (toutes les listes decrites)
        python build/listes_wikideck.py --essai    (images et html en simulation)
"""
import io, re, sys, json, shutil, datetime, unicodedata
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
MEMO = Path(__file__).resolve().parent.parent
WIKIDECK = MEMO.parent / 'wikideck'
TEXTES = MEMO / 'build' / 'listes_wikideck'
HTML = MEMO / 'memo.html'

# Une liste Memo par collection WikiDeck : identifiant, nom, icone, colonnes
# (libelle, cle dans le fichier redige), et ordre des lignes.
LISTES = {
    'philosophes': dict(id='philosophes', nom='Philosophes', icone='🏛️', ordre=('chrono', 'dates'),
                        categorie='sciences-nature',
                        colonnes=[('Nom', None), ('Dates', 'dates'), ('Courant', 'courant'),
                                  ('Concepts clés', 'concepts'), ('Œuvres principales', 'oeuvres')]),
    'tableaux-celebres': dict(id='tableaux_celebres', nom='Tableaux célèbres', icone='🖼️', ordre=('chrono', 'date'),
                              categorie='arts-culture',
                              colonnes=[('Titre', None), ('Peintre', 'peintre'), ('Date', 'date'),
                                        ('Conservé à', 'lieu'), ('Mouvement', 'mouvement')]),
    'plats-francais': dict(id='plats_francais', nom='Plats français', icone='🍲', ordre='region',
                           categorie='gastronomie',
                           colonnes=[('Plat', None), ('Région', 'region'), ('Ingrédients', 'ingredients'),
                                     ('Type', 'type')]),
    # Lot 2 : en relecture tant que « relue » vaut False (le generateur les ignore)
    'grands-peintres': dict(id='peintres', nom='Grands peintres', icone='🎨', ordre=('chrono', 'dates'),
                            categorie='arts-culture',
                            colonnes=[('Nom', None), ('Dates', 'dates'), ('Nationalité', 'nationalite'),
                                      ('Mouvement', 'mouvement'), ('Œuvres majeures', 'oeuvres')]),
    'auteurs-classiques': dict(id='auteurs_classiques', nom='Auteurs classiques', icone='✒️', ordre=('chrono', 'dates'),
                               categorie='arts-culture',
                               colonnes=[('Nom', None), ('Dates', 'dates'), ('Nationalité', 'nationalite'),
                                         ('Mouvement', 'mouvement'), ('Œuvres majeures', 'oeuvres')]),
    'oeuvres-litteraires': dict(id='litterature', nom='Œuvres littéraires', icone='📚', ordre=('chrono', 'annee'),
                                categorie='arts-culture',
                                colonnes=[('Titre', None), ('Auteur', 'auteur'), ('Année', 'annee'),
                                          ('Pays', 'pays'), ('Genre', 'genre')]),
    'grandes-batailles-historiques': dict(id='batailles_decisives', nom='Grandes batailles', icone='⚔️',
                                          ordre=('chrono', 'date'), categorie='histoire',
                                          colonnes=[('Bataille', None), ('Date', 'date'), ('Lieu', 'lieu'),
                                                    ('Guerre', 'guerre'), ('Vainqueur', 'vainqueur')]),
    'iles': dict(id='iles', nom='Îles', icone='🏝️', ordre='mer', categorie='geographie',
                 colonnes=[('Île', None), ('Pays', 'pays'), ('Océan ou mer', 'mer'), ('Chef-lieu', 'cheflieu')]),
    'fromages': dict(id='fromages', nom='Fromages', icone='🧀', ordre='region', categorie='gastronomie',
                     colonnes=[('Fromage', None), ('Région', 'region'), ('Lait', 'lait'),
                               ('Appellation', 'appellation')]),
    # Lot 3
    'grands-compositeurs': dict(id='compositeurs', nom='Grands compositeurs', icone='🎼', ordre=('chrono', 'dates'),
                                categorie='arts-culture',
                                colonnes=[('Nom', None), ('Dates', 'dates'), ('Nationalité', 'nationalite'),
                                          ('Période', 'periode'), ('Œuvres majeures', 'oeuvres')]),
    'scientifiques-celebres': dict(id='grands_scientifiques', nom='Scientifiques célèbres', icone='🔭',
                                   ordre=('chrono', 'dates'), categorie='sciences-nature',
                                   colonnes=[('Nom', None), ('Dates', 'dates'), ('Nationalité', 'nationalite'),
                                             ('Domaine', 'domaine'), ('Découverte majeure', 'decouverte')]),
    'oeuvres-musicales': dict(id='oeuvres_musicales', nom='Œuvres musicales', icone='🎵', ordre=('chrono', 'annee'),
                              categorie='arts-culture',
                              colonnes=[('Œuvre', None), ('Compositeur', 'compositeur'), ('Année', 'annee'),
                                        ('Genre', 'genre')]),
    'sculptures-celebres': dict(id='sculptures_celebres', nom='Sculptures célèbres', icone='🗿', ordre=('chrono', 'date'),
                                categorie='arts-culture',
                                colonnes=[('Sculpture', None), ('Sculpteur', 'sculpteur'), ('Date', 'date'),
                                          ('Conservée à', 'lieu')]),
    'souverains-et-conquerants': dict(id='souverains', nom='Souverains et conquérants', icone='👑',
                                      ordre=('chrono', 'regne'), categorie='histoire',
                                      colonnes=[('Nom', None), ('Royaume ou empire', 'royaume'), ('Au pouvoir', 'regne'),
                                                ('Fait marquant', 'fait')]),
    'monuments-emblematiques': dict(id='monuments', nom='Monuments', icone='🗼', ordre='pays',
                                    categorie='geographie',
                                    colonnes=[('Monument', None), ('Ville', 'ville'), ('Pays', 'pays'),
                                              ('Date', 'date'), ('Architecte ou commanditaire', 'auteur')]),
    # Lot 4
    'grandes-guerres': dict(id='guerres', nom='Grandes guerres', icone='⚔️', ordre=('chrono', 'dates'),
                            categorie='histoire',
                            colonnes=[('Conflit', None), ('Dates', 'dates'), ('Belligérants', 'belligerants'),
                                      ('Issue', 'issue')]),
    'empires-et-civilisations': dict(id='civilisations', nom='Empires et civilisations', icone='🏺',
                                     ordre=('chrono', 'periode'), categorie='histoire',
                                     colonnes=[('Nom', None), ('Période', 'periode'), ('Capitale', 'capitale'),
                                               ('Aire géographique', 'aire')]),
    'grands-explorateurs': dict(id='grandes_explorations', nom='Grands explorateurs', icone='🧭',
                                ordre=('chrono', 'date'), categorie='histoire',
                                colonnes=[('Explorateur', None), ('Nationalité', 'nationalite'), ('Date', 'date'),
                                          ('Exploration', 'exploration')]),
    'inventions-importantes': dict(id='inventions_majeures', nom='Inventions importantes', icone='⚙️',
                                   ordre=('chrono', 'date'), categorie='sciences-nature',
                                   colonnes=[('Invention', None), ('Inventeur', 'inventeur'), ('Date', 'date'),
                                             ('Pays', 'pays')]),
    'villes-du-monde': dict(id='villes', nom='Villes du monde', icone='🏙️', ordre='pays',
                            categorie='geographie',
                            colonnes=[('Ville', None), ('Pays', 'pays'), ('Surnom ou monument', 'repere')]),
    'montagnes-et-volcans': dict(id='montagnes_monde', nom='Montagnes et volcans', icone='🏔️',
                                 ordre=('altitude', 'altitude'), categorie='geographie',
                                 colonnes=[('Sommet', None), ('Altitude', 'altitude'), ('Massif', 'massif'),
                                           ('Pays', 'pays'), ('Type', 'type')]),
    # Lot 5
    'langues-du-monde': dict(id='langues', nom='Langues du monde', icone='🗣️', ordre='famille',
                             categorie='langues-vocabulaire',
                             colonnes=[('Langue', None), ('Famille', 'famille'), ('Pays principaux', 'pays'),
                                       ('Écriture', 'ecriture')]),
    'monnaies-du-monde': dict(id='monnaies', nom='Monnaies du monde', icone='💱', ordre='pays',
                              categorie='geographie',
                              colonnes=[('Monnaie', None), ('Pays', 'pays'), ('Symbole', 'symbole'),
                                        ('Subdivision', 'sousunite')]),
    'cuisines-du-monde': dict(id='plats_monde', nom='Plats du monde', icone='🍜', ordre='pays',
                              categorie='gastronomie',
                              colonnes=[('Plat', None), ('Pays', 'pays'), ('Ingrédients', 'ingredients')]),
    'cepages': dict(id='cepages', nom='Cépages', icone='🍇', ordre='couleur', categorie='gastronomie',
                    colonnes=[('Cépage', None), ('Couleur', 'couleur'), ('Région viticole', 'region'),
                              ('Vin emblématique', 'vin')]),
    'figures-religieuses': dict(id='figures_religieuses', nom='Figures religieuses', icone='🕊️',
                                ordre=('chrono', 'epoque'), categorie='histoire',
                                colonnes=[('Nom', None), ('Religion', 'religion'), ('Époque', 'epoque'),
                                          ('Rôle', 'role')]),
    'conquete-spatiale': dict(id='conquete_spatiale', nom='Conquête spatiale', icone='🚀', ordre=('chrono', 'date'),
                              categorie='sciences-nature',
                              colonnes=[('Mission ou engin', None), ('Date', 'date'), ('Pays ou agence', 'pays'),
                                        ('Fait marquant', 'fait')]),
    # Lot 6 : mythologies (ordre '-' = alphabetique sur le nom)
    'dieux-et-figures-mythologiques-grecques': dict(id='mythologie', nom='Mythologie grecque', icone='⚡', ordre=('liste', 'type', ['Olympien', 'Titan', 'Divinité primordiale', 'Divinité', 'Héros', 'Mortel', 'Nymphe', 'Muse', 'Créature']),
        categorie='mythologies',
        colonnes=[('Nom', None), ('Type', 'type'), ('Domaine', 'domaine'), ('Symbole', 'attribut'),
                  ('Équivalent romain', 'romain')]),
    'mythologie-egyptienne': dict(id='mythologie_egyptienne', nom='Mythologie égyptienne', icone='☥', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologie-nordique': dict(id='mythologie_nordique', nom='Mythologie nordique', icone='🪓', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologie-hindoue': dict(id='mythologie_hindoue', nom='Mythologie hindoue', icone='🪷', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologie-celtique': dict(id='mythologie_celtique', nom='Mythologie celtique', icone='🍀', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologies-asie-est': dict(id='mythologies_asie_est', nom="Mythologies d'Asie de l'Est", icone='🐉', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    # Lot 7 : dernieres mythologies
    'mythologies-slaves': dict(id='mythologies_slaves', nom="Mythologies slaves et baltes", icone='🌲', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologies-africaines': dict(id='mythologies_africaines', nom="Mythologies africaines", icone='🥁', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologies-mesoamericaines': dict(id='mythologies_mesoamericaines', nom="Mythologies mésoaméricaines et andines", icone='🐍', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologies-proche-orient': dict(id='mythologies_proche_orient', nom="Mythologies du Proche-Orient ancien", icone='🏺', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologies-oceanie-ameriques': dict(id='mythologies_oceanie_ameriques', nom="Mythologies océaniennes et amérindiennes", icone='🌊', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    'mythologie-finnoise': dict(id='mythologie_finnoise', nom="Mythologie finnoise", icone='🦢', ordre='-', categorie='mythologies',
        colonnes=[('Nom', None), ('Rôle ou domaine', 'role'), ('Attribut ou symbole', 'attribut'), ('Parenté', 'parente')]),
    # Lot 8
    'creatures-et-legendes': dict(id='creatures_legendaires', nom="Créatures légendaires", icone='🦄', ordre='-', categorie='mythologies',
        colonnes=[('Créature', None), ('Origine', 'origine'), ('Description', 'description')]),
    'lieux-legendaires': dict(id='lieux_legendaires', nom="Lieux légendaires", icone='🏰', ordre='-', categorie='mythologies',
        colonnes=[('Lieu', None), ('Tradition ou œuvre', 'origine'), ('Description', 'description')]),
    'objets-mythiques': dict(id='objets_mythiques', nom="Objets mythiques", icone='🗡️', ordre='-', categorie='mythologies',
        colonnes=[('Objet', None), ('Tradition', 'origine'), ('Pouvoir ou rôle', 'role'), ('Possesseur', 'possesseur')]),
    'evenements-mythiques': dict(id='evenements_mythiques', nom="Événements mythiques", icone='🌋', ordre='-', categorie='mythologies',
        colonnes=[('Événement', None), ('Tradition', 'origine'), ('Description', 'description')]),
    'figures-emancipation': dict(id='figures_emancipation', nom="Figures de l'émancipation", icone='✊', ordre=('chrono', 'dates'), categorie='histoire',
        colonnes=[('Nom', None), ('Dates', 'dates'), ('Pays', 'pays'), ('Combat', 'combat')]),
    'figures-resistance': dict(id='figures_resistance', nom="Figures de la Résistance", icone='🕯️', ordre=('chrono', 'dates'), categorie='histoire',
        colonnes=[('Nom', None), ('Dates', 'dates'), ('Pays', 'pays'), ('Action', 'action')]),
    'dirigeants-contemporains': dict(id='dirigeants_contemporains', nom="Dirigeants contemporains", icone='🎖️', ordre=('chrono', 'mandat'), categorie='histoire',
        colonnes=[('Nom', None), ('Pays', 'pays'), ('Fonction', 'fonction'), ('Au pouvoir', 'mandat')]),
    # Lot 9
    'auteurs-modernes': dict(id='auteurs_modernes', nom="Auteurs modernes", icone='✍️', ordre=('chrono', 'dates'), categorie='arts-culture',
        colonnes=[('Nom', None), ('Dates', 'dates'), ('Nationalité', 'nationalite'), ('Œuvres majeures', 'oeuvres'), ('Prix', 'prix')]),
    'personnages-litterature': dict(id='personnages_litterature', nom="Personnages de littérature", icone='🎭', ordre='-', categorie='arts-culture',
        colonnes=[('Personnage', None), ('Œuvre', 'oeuvre'), ('Auteur', 'auteur')]),
    'traites-et-textes-fondateurs': dict(id='traites', nom="Traités et textes fondateurs", icone='📜', ordre=('chrono', 'date'), categorie='histoire',
        colonnes=[('Texte', None), ('Date', 'date'), ('Auteurs ou signataires', 'signataires'), ("Ce qu'il établit", 'objet')]),
    'sites-antiques': dict(id='sites_antiques', nom="Sites antiques", icone='🪨', ordre=('chrono', 'epoque'), categorie='histoire',
        colonnes=[('Site', None), ('Pays', 'pays'), ('Civilisation', 'civilisation'), ('Époque', 'epoque')]),
    'styles-architecturaux': dict(id='styles_architecturaux', nom="Styles architecturaux", icone='🏗️', ordre=('chrono', 'periode'), categorie='arts-culture',
        colonnes=[('Style', None), ('Période', 'periode'), ('Origine', 'origine'), ('Édifice type', 'edifice')]),
    'fleuves-mers-et-oceans': dict(id='fleuves_mers_oceans', nom="Fleuves, mers et océans", icone='🌊', ordre=('liste', 'type', ['Océan', 'Mer', 'Golfe', 'Détroit', 'Canal', 'Fleuve', 'Rivière', 'Chute', 'Lac', 'Cap', 'Autre']), categorie='geographie', remplace=['fleuves_monde', 'mers_oceans'],
        colonnes=[('Nom', None), ('Type', 'type'), ('Pays ou région', 'pays'), ('Repère', 'repere')]),
    # Lot 10 : listes Memo existantes refaites depuis WikiDeck
    'elements-chimiques': dict(id='elements', nom="Éléments chimiques", icone='⚗️', ordre=('chrono', 'z'), categorie='sciences-nature',
        colonnes=[('Élément', None), ('Symbole', 'symbole'), ('Numéro atomique', 'z'), ('Famille', 'famille')]),
    'constellations': dict(id='constellations', nom="Constellations", icone='✨', ordre='-', categorie='sciences-nature',
        colonnes=[('Constellation', None), ('Hémisphère', 'hemisphere'), ('Étoile principale', 'etoile'), ('Représente', 'represente')]),
    'pilotes-f1-champions-du-monde': dict(id='f1_champions', nom="Champions du monde de F1", icone='🏎️', ordre=('chrono', 'titres'), categorie='sports-loisirs',
        colonnes=[('Pilote', None), ('Nationalité', 'nationalite'), ('Titres', 'titres'), ('Écurie', 'ecurie')]),
    'coupes-du-monde-fifa': dict(id='coupes_monde', nom="Coupes du monde de football", icone='⚽', ordre=('chrono', 'annee'), categorie='sports-loisirs',
        colonnes=[('Édition', None), ('Année', 'annee'), ('Pays organisateur', 'organisateur'), ('Vainqueur', 'vainqueur'), ('Finale', 'finale')]),
    'jeux-olympiques': dict(id='jo_ete', nom="Jeux olympiques d'été", icone='🏅', ordre=('chrono', 'annee'), categorie='sports-loisirs',
        colonnes=[('Édition', None), ('Année', 'annee'), ('Ville', 'ville'), ('Pays', 'pays'), ('Fait marquant', 'fait')]),
    'jeux-olympiques-hiver': dict(id='jo_hiver', nom="Jeux olympiques d'hiver", icone='⛷️', ordre=('chrono', 'annee'), categorie='sports-loisirs',
        colonnes=[('Édition', None), ('Année', 'annee'), ('Ville', 'ville'), ('Pays', 'pays'), ('Fait marquant', 'fait')]),
}
VIDE = {'oeuvres': 'Aucun écrit conservé'}
ANCRE = 'DEFAULT_LISTS.push(...CURATED_LISTS_V3);'
DEBUT_BLOC = '/* ══════════ LISTES ISSUES DE WIKIDECK ══════════'
FIN_BLOC = '/* ══════════ FIN DES LISTES WIKIDECK ══════════ */'


MOIS = r'(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)'
ROMAINS = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}


def romain(s):
    n = 0
    for i, ch in enumerate(s):
        v = ROMAINS[ch]
        n += -v if i + 1 < len(s) and ROMAINS[s[i + 1]] > v else v
    return n


def annee(texte):
    """Annee de tri lue dans « vers 470-399 av. J.-C. », « 1503-1519 »,
    « 1er juillet-18 novembre 1916 », « VIIIe siècle av. J.-C. »..."""
    # « 28 000 » : les espaces entre groupes de chiffres ne coupent pas le nombre
    texte = re.sub(r'(\d)[ \u00a0\u202f](?=\d{3}\b)', r'\1', texte or '')
    avant = bool(re.search(r'av\.? ?J\.?-?C', texte))
    m = re.search(r'\b([IVXLC]+)(?:er|e) siècle', texte) or re.search(r'(\d{1,2})e siècle', texte)
    if m and not re.search(r'\d{3,4}', texte):
        s = romain(m.group(1)) if m.group(1)[0] in ROMAINS else int(m.group(1))
        a = (s - 1) * 100 + 50
        return -a if avant else a
    # les jours du mois (« 1er », « 18 novembre ») ne sont pas des annees
    sans_jours = re.sub(r'\b\d{1,2}(?:er)?\s+' + MOIS, ' ', texte)
    m = re.search(r'(\d{1,6})', sans_jours)
    if not m:
        return 99999
    a = int(m.group(1))
    a = -a if avant else a
    # le premier mois cite departage les evenements d'une meme annee
    mois = re.search(MOIS, texte)
    if mois:
        rang = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
                'septembre', 'octobre', 'novembre', 'décembre'].index(mois.group(0))
        a += (rang + 1) / 13
    return a


def nombre(texte):
    """Premier nombre lu dans « 8 849 m » (espaces de milliers compris), 0 sinon."""
    m = re.search(r'\d[\d \u00a0\u202f]*', texte or '')
    return int(re.sub(r'\D', '', m.group(0))) if m else 0


def sans_accents(texte):
    """Cle de tri alphabetique : « Île-de-France » avec les I, pas apres le Z."""
    texte = (texte or '').replace('Æ', 'Ae').replace('æ', 'ae').replace('Œ', 'Oe').replace('œ', 'oe')
    return ''.join(ch for ch in unicodedata.normalize('NFD', texte) if not unicodedata.combining(ch)).lower()


def nom_affiche(c):
    # une fiche peut imposer son nom (cle « nom ») quand la carte se trompe de sujet
    # « Ophélie (Millais) » garde sa precision ; « Ratatouille (plat) » la perd
    return re.sub(r' \((plat|gâteau|peinture|tableau|roman|peintre|philosophe|île|opéra|ballet|comédie musicale|suites|mythologie grecque|mythologie|arme|navigation|informatique|langue|monnaie|sonde|satellite|roi|apôtre|déesse|dieu|folklore|créature|légende)\)$', '', c['nom'])


def recadrer(c, cadrages):
    col, f = c['id'].split('_', 1)
    orig = WIKIDECK / 'images' / 'originaux' / col / f'{f}.webp'
    cad = cadrages.get(c['id'])
    if orig.exists() and cad and cad.get('w'):
        im = Image.open(orig).convert('RGB')
        iw, ih = im.size
        cw = cad['w'] * iw
        ch = cw * 3 / 4
        x0, y0 = cad['cx'] * iw - cw / 2, cad['cy'] * ih - ch / 2
        return im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch)))
    return Image.open(WIKIDECK / c['imageUrl']).convert('RGB')


CACHE_FICHIER = MEMO / 'build' / '.cache_images.json'
CACHE = json.loads(CACHE_FICHIER.read_text(encoding='utf-8')) if CACHE_FICHIER.exists() else {}


def signature(c, cadrages):
    """Empreinte de ce qui determine l'image : cadrage et fichier source (taille, date)."""
    col, f = c['id'].split('_', 1)
    orig = WIKIDECK / 'images' / 'originaux' / col / f'{f}.webp'
    src = orig if orig.exists() else WIKIDECK / c['imageUrl']
    st = src.stat() if src.exists() else None
    return json.dumps([cadrages.get(c['id']), str(src.name), st.st_size if st else 0,
                       int(st.st_mtime) if st else 0], sort_keys=True)


def ecrire_images(lid, cle, im, essai):
    w = min(2000, im.width)
    grand = im.resize((w, w * 3 // 4), Image.LANCZOS)
    petit = im.resize((400, 300), Image.LANCZOS)
    tf, ff = f'thumbs/{lid}/{cle}.webp', f'full/{lid}/{cle}.webp'
    if not essai:
        for rel, img, q in ((tf, petit, 82), (ff, grand, 86)):
            p = MEMO / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            img.save(p, 'WEBP', quality=q)
    return tf, ff


def construire(slug, cadrages, essai):
    cfg = LISTES[slug]
    textes = json.loads((TEXTES / f'{slug}.json').read_text(encoding='utf-8'))
    cartes = [c for c in json.loads((WIKIDECK / 'data' / f'{slug}.json').read_text(encoding='utf-8'))['cartes']
              if c['id'] in textes]
    # ordre : ('chrono', <cle de date>) ou <cle> pour un tri alphabetique sur cette colonne
    if isinstance(cfg['ordre'], tuple) and cfg['ordre'][0] == 'liste':
        rangs = cfg['ordre'][2]
        cartes.sort(key=lambda c: (rangs.index(textes[c['id']].get(cfg['ordre'][1]))
                                   if textes[c['id']].get(cfg['ordre'][1]) in rangs else len(rangs),
                                   sans_accents(c['nom'])))
    elif isinstance(cfg['ordre'], tuple) and cfg['ordre'][0] == 'altitude':
        cartes.sort(key=lambda c: (-nombre(textes[c['id']].get(cfg['ordre'][1], '')), c['nom']))
    elif isinstance(cfg['ordre'], tuple):
        cartes.sort(key=lambda c: (float(textes[c['id']]['tri']) if textes[c['id']].get('tri') else annee(textes[c['id']].get(cfg['ordre'][1], '')), c['nom']))
    else:
        cartes.sort(key=lambda c: (sans_accents(textes[c['id']].get(cfg['ordre'], '')), sans_accents(c['nom'])))
    lignes, grands = [], {}
    for i, c in enumerate(cartes, 1):
        t = textes[c['id']]
        cle = c['id'].split('_', 1)[1]
        empreinte = signature(c, cadrages)
        tf, ff = f"thumbs/{cfg['id']}/{cle}.webp", f"full/{cfg['id']}/{cle}.webp"
        deja = CACHE.get(f"{cfg['id']}/{cle}") == empreinte and (MEMO / tf).exists() and (MEMO / ff).exists()
        if not deja:
            tf, ff = ecrire_images(cfg['id'], cle, recadrer(c, cadrages), essai)
            if not essai:
                CACHE[f"{cfg['id']}/{cle}"] = empreinte
        grands[cle] = ff
        ligne = [str(i), tf]
        for lib, k in cfg['colonnes']:
            ligne.append((t.get('nom') or nom_affiche(c)) if k is None else (t.get(k) or VIDE.get(k, '')))
        lignes.append(ligne)
    liste = {'id': cfg['id'], 'name': cfg['nom'], 'icon': cfg['icone'],
             'columns': ['Numéro', 'Image'] + [lib for lib, _ in cfg['colonnes']],
             'rows': lignes, 'source': 'wikideck', 'categoryId': cfg['categorie']}
    return liste, grands


def litteral(html, nom):
    """Bornes du litteral JSON qui suit « const <nom> = »."""
    i = html.index(f'const {nom} = ') + len(f'const {nom} = ')
    obj, n = json.JSONDecoder().raw_decode(html[i:])
    return i, i + n, obj


def poser_dans_html(listes, grands, essai):
    html = HTML.read_text(encoding='utf-8')
    # 1. le bloc des listes, remplace s'il existe deja
    ids = [l['id'] for l in listes]
    bloc = (f"\n{DEBUT_BLOC}\n   Bloc régénéré par build/listes_wikideck.py : ne pas modifier à la main.\n"
            f"   Chaque liste remplace celle de même identifiant, ou s'ajoute. */\n"
            f"const WIKIDECK_LISTS = {json.dumps(listes, ensure_ascii=False)};\n"
            f"const WIKIDECK_LIST_IDS = new Set(WIKIDECK_LISTS.map(l => l.id));\n"
        f"const WIKIDECK_RETIRED = {json.dumps(sorted({r for c in LISTES.values() if c.get('relue', True) for r in c.get('remplace', [])}))};\n"
            f"for (const r of WIKIDECK_RETIRED) {{ const i = DEFAULT_LISTS.findIndex(x => x.id === r); if (i >= 0) DEFAULT_LISTS.splice(i, 1); }}\n"
            f"for (const l of WIKIDECK_LISTS) {{\n"
            f"  const i = DEFAULT_LISTS.findIndex(x => x.id === l.id);\n"
            f"  if (i >= 0) DEFAULT_LISTS[i] = l; else DEFAULT_LISTS.push(l);\n"
            f"}}\n{FIN_BLOC}")
    if DEBUT_BLOC in html:
        a = html.index('\n' + DEBUT_BLOC)
        b = html.index(FIN_BLOC) + len(FIN_BLOC)
        html = html[:a] + bloc + html[b:]
    else:
        k = html.index(ANCRE) + len(ANCRE)
        html = html[:k] + bloc + html[k:]
    # 2. les anciennes retouches par rang de l'Atelier ne valent plus pour ces listes
    a, b, atelier = litteral(html, 'ATELIER_IMAGES')
    retirees = [i for i in ids if i in atelier]
    for i in retirees:
        del atelier[i]
    html = html[:a] + json.dumps(atelier, ensure_ascii=False, indent=1) + html[b:]
    # 3. les grandes images
    a, b, carte = litteral(html, 'IMAGE_FILES_MAP')
    carte.update(grands)
    html = html[:a] + json.dumps(carte, ensure_ascii=False) + html[b:]
    # 4. la migration v47 reimpose des images par rang : pas sur ces listes
    html = html.replace('const map = V47_DATA[sl.id];',
                        'const map = (typeof WIKIDECK_LIST_IDS !== "undefined" && WIKIDECK_LIST_IDS.has(sl.id)) ? null : V47_DATA[sl.id];')
    if essai:
        print('  (simulation : memo.html non modifie)')
        return
    sauvegarde = MEMO / 'backups' / f'memo_{datetime.date.today():%Y-%m-%d}_avant_wikideck.html'
    sauvegarde.parent.mkdir(exist_ok=True)
    if not sauvegarde.exists():
        shutil.copy2(HTML, sauvegarde)
    HTML.write_text(html, encoding='utf-8')
    print(f'  memo.html mis a jour ; retouches par rang retirees : {retirees or "aucune"}')


def main():
    essai = '--essai' in sys.argv
    cadrages = json.loads((WIKIDECK / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))['cadrages']
    listes, grands = [], {}
    for slug in LISTES:
        if not LISTES[slug].get('relue', True) or not (TEXTES / f'{slug}.json').exists():
            continue
        liste, g = construire(slug, cadrages, essai)
        listes.append(liste)
        grands[liste['id']] = g
        print(f"  {liste['name']:<22} {len(liste['rows'])} lignes")
    poser_dans_html(listes, grands, essai)
    if not essai:
        CACHE_FICHIER.write_text(json.dumps(CACHE, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
