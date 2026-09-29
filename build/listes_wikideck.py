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
import io, re, sys, json, shutil, datetime
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
    'philosophes': dict(id='philosophes', nom='Philosophes', icone='🏛️', ordre='chrono',
                        colonnes=[('Nom', None), ('Dates', 'dates'), ('Courant', 'courant'),
                                  ('Concepts clés', 'concepts'), ('Œuvres principales', 'oeuvres')]),
    'tableaux-celebres': dict(id='tableaux_celebres', nom='Tableaux célèbres', icone='🖼️', ordre='chrono',
                              colonnes=[('Titre', None), ('Peintre', 'peintre'), ('Date', 'date'),
                                        ('Conservé à', 'lieu'), ('Mouvement', 'mouvement')]),
    'plats-francais': dict(id='plats_francais', nom='Plats français', icone='🍲', ordre='region',
                           colonnes=[('Plat', None), ('Région', 'region'), ('Ingrédients', 'ingredients'),
                                     ('Type', 'type')]),
}
VIDE = {'oeuvres': 'Aucun écrit conservé'}
ANCRE = 'DEFAULT_LISTS.push(...CURATED_LISTS_V3);'
DEBUT_BLOC = '/* ══════════ LISTES ISSUES DE WIKIDECK ══════════'
FIN_BLOC = '/* ══════════ FIN DES LISTES WIKIDECK ══════════ */'


def annee(texte):
    """Premiere annee lue dans « vers 470-399 av. J.-C. », « 1503-1519 »..."""
    m = re.search(r'(\d{1,4})', texte or '')
    if not m:
        return 99999
    a = int(m.group(1))
    if re.search(r'av\.? ?J\.?-?C', texte or ''):
        a = -a
    if re.search(r'(\d{1,2})e siècle', texte or '') and not re.search(r'\d{3,4}', texte or ''):
        s = int(re.search(r'(\d{1,2})e siècle', texte).group(1))
        a = (s - 1) * 100 + 50 if a > 0 else -(s - 1) * 100 - 50
    return a


def nom_affiche(c):
    # « Ophélie (Millais) » garde sa precision ; « Ratatouille (plat) » la perd
    return re.sub(r' \((plat|gâteau|peinture|tableau)\)$', '', c['nom'])


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
    if cfg['ordre'] == 'chrono':
        cle_date = cfg['colonnes'][1][1] if cfg['colonnes'][1][1] in ('dates', 'date') else 'date'
        cartes.sort(key=lambda c: (annee(textes[c['id']].get(cle_date, '')), c['nom']))
    else:
        cartes.sort(key=lambda c: (textes[c['id']].get('region', ''), c['nom']))
    lignes, grands = [], {}
    for i, c in enumerate(cartes, 1):
        t = textes[c['id']]
        cle = c['id'].split('_', 1)[1]
        tf, ff = ecrire_images(cfg['id'], cle, recadrer(c, cadrages), essai)
        grands[cle] = ff
        ligne = [str(i), tf]
        for lib, k in cfg['colonnes']:
            ligne.append(nom_affiche(c) if k is None else (t.get(k) or VIDE.get(k, '')))
        lignes.append(ligne)
    liste = {'id': cfg['id'], 'name': cfg['nom'], 'icon': cfg['icone'],
             'columns': ['Numéro', 'Image'] + [lib for lib, _ in cfg['colonnes']],
             'rows': lignes, 'source': 'wikideck'}
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
        if not (TEXTES / f'{slug}.json').exists():
            continue
        liste, g = construire(slug, cadrages, essai)
        listes.append(liste)
        grands[liste['id']] = g
        print(f"  {liste['name']:<22} {len(liste['rows'])} lignes")
    poser_dans_html(listes, grands, essai)


if __name__ == '__main__':
    main()
