#!/usr/bin/env python3
"""Page de relecture des listes WikiDeck avant leur entree dans Memo.

Pour chaque liste (cle de LISTES dans listes_wikideck.py), une fiche par
element avec l'image telle que Memo la montrera (meme cadrage), les colonnes
redigees et la note du redacteur ; les fiches « a_verifier » sont signalees.
La page est autonome (images incluses) et se publie en artifact : le
proprietaire y valide, corrige ou retire chaque fiche, decisions enregistrees
dans la base de l'artifact (collection « decisions », une fiche par carte).

Usage : python build/relecture_listes.py <sortie.html> <slug> [<slug>...]
"""
import io, sys, json, base64
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import listes_wikideck as L

MODELE = Path(__file__).resolve().parent / 'relecture' / 'modele.html'


def vignette(im):
    im = im.copy()
    im.thumbnail((256, 192))
    tampon = io.BytesIO()
    im.save(tampon, 'WEBP', quality=62)
    return 'data:image/webp;base64,' + base64.b64encode(tampon.getvalue()).decode()


def liste(slug, cadrages):
    cfg = L.LISTES[slug]
    textes = json.loads((L.TEXTES / f'{slug}.json').read_text(encoding='utf-8'))
    cartes = [c for c in json.loads((L.WIKIDECK / 'data' / f'{slug}.json').read_text(encoding='utf-8'))['cartes']
              if c['id'] in textes]
    manquantes = len(textes) - len(cartes)
    if isinstance(cfg['ordre'], tuple):
        cartes.sort(key=lambda c: (L.annee(textes[c['id']].get(cfg['ordre'][1], '')), c['nom']))
    else:
        cartes.sort(key=lambda c: (textes[c['id']].get(cfg['ordre'], ''), c['nom']))
    fiches = []
    for rang, c in enumerate(cartes, 1):
        t = textes[c['id']]
        fiches.append({
            'id': c['id'], 'rang': rang, 'nom': t.get('nom') or L.nom_affiche(c),
            'image': vignette(L.recadrer(c, cadrages)),
            'champs': [[lib, t.get(k, '')] for lib, k in cfg['colonnes'] if k],
            'doute': t.get('confiance') == 'a_verifier', 'note': t.get('note', ''),
        })
    print(f"  {cfg['nom']:<22} {len(fiches)} fiches, {sum(f['doute'] for f in fiches)} a verifier"
          + (f', {manquantes} fiches sans carte !' if manquantes else ''))
    return {'slug': slug, 'nom': cfg['nom'], 'colonnes': [lib for lib, _ in cfg['colonnes']], 'fiches': fiches}


def main():
    sortie, slugs = Path(sys.argv[1]), sys.argv[2:]
    cadrages = json.loads((L.WIKIDECK / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))['cadrages']
    donnees = {'listes': [liste(s, cadrages) for s in slugs]}
    brut = json.dumps(donnees, ensure_ascii=False).replace('</', '<\/')
    sortie.write_text(MODELE.read_text(encoding='utf-8').replace('__DONNEES__', brut), encoding='utf-8')
    print(sortie, round(sortie.stat().st_size / 1e6, 1), 'Mo')


if __name__ == '__main__':
    main()
