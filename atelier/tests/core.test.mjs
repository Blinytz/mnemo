import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { IMAGE_FORMAT, canonicalWikipedia, previewBulk, stableId, validateWorkspace } from '../lib.mjs';
import { apparier } from '../wikideck-bridge.mjs';
import { lireMemoHtml, poserImage, cleDeEntree, clesPrises } from '../memo-html.mjs';
import { calerAxe } from '../image-editor.js';

test('la grande image suit WikiDeck, la miniature garde le format de Mémo', async () => {
  const source = fs.readFileSync(path.resolve('../wikideck/atelier/editeur.js'), 'utf8');
  const match = source.match(/EXPORT_FULL\s*=\s*\[(\d+),\s*(\d+)\]/);
  assert.deepEqual(IMAGE_FORMAT.full, match.slice(1).map(Number));
  // 400 × 300 est le format des miniatures de Mémo : reprendre le 213 × 160 des
  // cartes WikiDeck reviendrait à dégrader l'application à chaque enregistrement
  assert.deepEqual(IMAGE_FORMAT.thumb, [400, 300]);
  assert.equal(IMAGE_FORMAT.full[0] / IMAGE_FORMAT.full[1], IMAGE_FORMAT.thumb[0] / IMAGE_FORMAT.thumb[1]);
});

test('une miniature ne peut pas avoir de source indépendante', () => {
  const data = { schemaVersion:1, categories:[{id:'c'}], lists:[{id:'l',categoryId:'c'}], entries:[{id:'e',listId:'l',image:{thumbSource:'interdit'}}], notes:[] };
  assert.match(validateWorkspace(data).join(' '), /source miniature interdite/);
});

test('numéro et nom ne déterminent pas l’identifiant stable', () => {
  const id = stableId('entry','liste','position','nom');
  const entry = { id, number:'1', name:'Avant' };
  entry.number='51'; entry.name='Après';
  assert.equal(entry.id,id);
});

test('Wikipedia est canonisé pour le rapprochement', () => {
  assert.equal(canonicalWikipedia('http://fr.wikipedia.org/wiki/Jean Dupont?x=1#A'), 'https://fr.wikipedia.org/wiki/Jean_Dupont');
});

test('l’appariement se fait sur la colonne-sujet, pas sur le nom d’entrée', () => {
  // reproduit le cas Formule 1 : les entrées s'appellent « 1950 », « 1951 »…
  // et c'est la colonne « Pilote » qui porte le sujet
  const cartes = [
    { id: 'c1', nom: 'Giuseppe Farina', wikipedia: 'https://fr.wikipedia.org/wiki/Giuseppe_Farina', source: 'images/originaux/f1/farina.webp', cadrage: { cx: .5, cy: .5, w: .9 } },
    { id: 'c2', nom: 'Juan Manuel Fangio', wikipedia: '', source: 'images/originaux/f1/fangio.webp', cadrage: null },
  ];
  const entrees = [
    { id: 'e1', name: '1950', fields: { 'Année': '1950', 'Pilote': 'Giuseppe Farina' } },
    { id: 'e2', name: '1951', fields: { 'Année': '1951', 'Pilote': 'Juan Manuel Fangio' } },
    { id: 'e3', name: '1952', fields: { 'Année': '1952', 'Pilote': 'Juan Manuel Fangio' } },
    { id: 'e4', name: '1953', fields: { 'Année': '1953', 'Pilote': 'Inconnu' } },
  ];
  const surAnnee = apparier({ entrees, cartes, colonne: 'Année' });
  assert.equal(surAnnee.resume.certain, 0, 'la mauvaise colonne ne doit rien apparier');

  const surPilote = apparier({ entrees, cartes, colonne: 'Pilote' });
  assert.equal(surPilote.resume.certain, 3);
  assert.equal(surPilote.resume.sans, 1);
  // deux saisons peuvent légitimement partager le même pilote
  assert.equal(surPilote.paires[1].candidats[0].id, surPilote.paires[2].candidats[0].id);
});

test('deux cartes de même nom rendent l’entrée ambiguë au lieu d’être devinée', () => {
  const cartes = [{ id: 'a', nom: 'Jupiter', source: 's' }, { id: 'b', nom: 'Jupiter', source: 's' }];
  const r = apparier({ entrees: [{ id: 'e', name: 'x', fields: { Sujet: 'Jupiter' } }], cartes, colonne: 'Sujet' });
  assert.equal(r.paires[0].statut, 'ambigu');
});

test('une entrée verrouillée est signalée pour ne jamais être écrasée en lot', () => {
  const r = apparier({
    entrees: [{ id: 'e', name: 'x', fields: { Sujet: 'A' }, image: { locked: true } }],
    cartes: [{ id: 'a', nom: 'A', source: 's' }],
    colonne: 'Sujet',
  });
  assert.equal(r.paires[0].verrouillee, true);
  assert.equal(r.resume.verrouillees, 1);
});

test('une opération collective produit un diff limité à la sélection', () => {
  const diff=previewBulk([{id:'a',number:'1'},{id:'b',number:'9'}],{type:'renumber',start:51});
  assert.deepEqual(diff.map(x=>x.after),['51','52']);
});

/* ---------- bornage du cadrage ---------- */

test('une image qui déborde ne peut pas laisser de vide au bord', () => {
  // marge négative : l'image est plus grande que le cadre
  const marge = -200;
  assert.equal(calerAxe(50, marge), 0, 'décalage positif interdit');
  assert.equal(calerAxe(-500, marge), marge, 'on ne peut pas dépasser le bord opposé');
  assert.equal(calerAxe(-120, marge), -120, 'une position valide est conservée');
});

test('une image plus petite que le cadre reste à l’intérieur', () => {
  // marge positive : cadrage libre assumé, l'image ne remplit pas le cadre
  const marge = 300;
  assert.equal(calerAxe(-40, marge), 0, 'elle ne peut pas sortir par la gauche');
  assert.equal(calerAxe(999, marge), marge, 'ni par la droite');
  assert.equal(calerAxe(150, marge), 150, 'elle se place librement entre les deux');
});

/* ---------- memo.html : la sortie réelle de l'Atelier ---------- */

test('les listes sont relevées quelle que soit la façon dont memo.html les déclare', () => {
  const memo = lireMemoHtml();
  // DEFAULT_LISTS (JSON), CURATED_LISTS_V3 (JSON) et EXPANSION_LISTS (écrit à
  // la main) alimentent tous les trois DEFAULT_LISTS au chargement
  assert.ok(memo.idsListes.size >= 40, `seulement ${memo.idsListes.size} listes relevées`);
  for (const id of ['chefs_etat', 'f1_champions', 'batailles_decisives', 'civilisations']) {
    assert.ok(memo.idsListes.has(id), `${id} devrait être reconnue`);
  }
  assert.ok(Object.keys(memo.imagesFull).length > 0);
  // memo.html sait que le sujet de la Formule 1 est le pilote, pas l'année
  assert.deepEqual(memo.colonnesSujet.f1_champions.cols, ['Pilote']);
});

test('poser une image inscrit la miniature ET la grande image de l’application', () => {
  const memo = lireMemoHtml();
  const chemins = poserImage(memo, 'civilisations', 3, '4');
  // la miniature passe par le bloc de l'Atelier, indexé par rang de ligne :
  // c'est ce qui permet de servir aussi les listes écrites à la main
  assert.equal(memo.imagesAtelier.civilisations['3'], chemins.thumb);
  assert.equal(memo.imagesFull.civilisations['4'], chemins.full);
  // le nom de fichier est le même partout : c'est ce que memo.html attend
  // (cf. localFullImageForThumb) — les deux ne peuvent pas diverger
  assert.equal(chemins.thumb, 'thumbs/civilisations/4.webp');
  assert.equal(chemins.full, 'full/civilisations/4.webp');
});

test('une liste inconnue de l’application est refusée plutôt qu’écrite au hasard', () => {
  const memo = lireMemoHtml();
  assert.throws(() => poserImage(memo, 'liste_inexistante', 0, '1'), /absente de l'application/);
});

test('une clé de fichier existante est réutilisée, jamais réinventée', () => {
  const entrees = [
    { id: 'a', number: '7', order: 0, image: { thumb: 'thumbs/demo/7b.webp' } },
    { id: 'b', number: '7', order: 1, image: {} },
  ];
  assert.equal(cleDeEntree(entrees[0], clesPrises(entrees)), '7b');
  // une entrée sans miniature ne doit pas voler la clé d'une autre
  assert.notEqual(cleDeEntree(entrees[1], clesPrises(entrees)), '7b');
});
