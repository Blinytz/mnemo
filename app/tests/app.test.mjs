// Tests des modules sans écran : node --test app/tests/
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {corriger, norm} from '../js/correction.js';
import * as P from '../js/progression.js';
import * as E from '../js/eclats.js';
import {tirerQuestion, deplier, colonnesDemandables, tirerQuiz, noterRotation, parAnciennete} from '../js/questions.js';

const juste = (t, a, nom = false) => corriger(t, a, nom).verdict === 'juste';

test('correction : tolérance', () => {
  assert.ok(juste('monet', 'Claude Monet', true));
  assert.ok(juste('claude monet', 'Claude Monet', true));
  assert.ok(juste('Monnet', 'Claude Monet', true));            // une lettre de trop
  assert.ok(juste('heraclès', 'Héraclès'));
  assert.ok(juste('naissance de venus', 'La Naissance de Vénus · Le Printemps'));
  assert.ok(juste('le printemps et la cene', 'La Naissance de Vénus · Le Printemps'));
  assert.ok(juste('Vigne · Vin · Fête · Théâtre', 'Vigne · Vin · Fête · Théâtre'));
  assert.ok(juste('oeuf', 'Œuf'));
  assert.ok(juste('1914', '28 juillet 1914'));
});

test('correction : sévérité', () => {
  assert.ok(!juste('zeus', 'Héra'));
  assert.ok(!juste('1915', '1914'));
  assert.ok(!juste('', 'Paris'));
  assert.ok(!juste('rone', 'Rome'));                           // mot court : aucune faute tolérée
  assert.ok(!juste('claude', 'Claude Monet', true));            // le prénom seul ne suffit pas
  assert.equal(corriger('   ', 'Paris').vide, true);
  assert.equal(norm("L'Île-de-France"), 'ile de france');
});

test('mémoire : montée, chute, échéances', () => {
  const e = P.etatVide(), j = 20000;
  P.noter(e, 'a/x', true, j);
  assert.deepEqual([e.fiches['a/x'].b, e.fiches['a/x'].d], [2, j + 3]);   // nouvelle trouvée : boîte 2
  P.noter(e, 'a/x', true, j + 3);
  assert.equal(e.fiches['a/x'].b, 3);
  P.noter(e, 'a/x', false, j + 10);
  assert.deepEqual([e.fiches['a/x'].b, e.fiches['a/x'].d], [1, j + 11]);
  assert.ok(!P.estDue(e, 'a/x', j + 10));
  assert.ok(P.estDue(e, 'a/x', j + 11));
  for (let k = 0; k < 10; k++) P.noter(e, 'a/x', true, j);
  assert.equal(e.fiches['a/x'].b, 5);
});

test('mémoire : renverser un verdict', () => {
  const e = P.etatVide(), j = 20000;
  P.noter(e, 'a/x', true, j - 5);
  const avant = P.noter(e, 'a/x', false, j);
  assert.equal(e.fiches['a/x'].b, 1);
  P.renoter(e, 'a/x', avant, true, j);
  assert.equal(e.fiches['a/x'].b, 3);
  assert.equal(e.fiches['a/x'].n, 2);
  const avant2 = P.noter(e, 'b/y', false, j);
  P.renoter(e, 'b/y', avant2, true, j);
  assert.equal(e.fiches['b/y'].b, 2);
});

test('série, record et réussite', () => {
  const e = P.etatVide(), j = 20000;
  const jouer = (jour, n, ok = n) => { for (let i = 0; i < n; i++) P.compterReponse(e, jour, i < ok); };
  jouer(j - 3, 20); jouer(j - 2, 25); jouer(j - 1, 20, 10);
  assert.equal(P.serie(e, j), 3);            // aujourd'hui pas encore fait : la série tient
  jouer(j, 20);
  assert.equal(P.serie(e, j), 4);
  assert.equal(P.serie(e, j + 2), 0);        // un jour manqué casse la série
  assert.equal(P.record(e), 4);
  assert.equal(P.reussite(e, j), Math.round(100 * 75 / 85));
  P.recompterReponse(e, j, false);
  assert.equal(e.jours[P.texteDuJour(j)].ok, 19);
});

test('dates en heure locale', () => {
  const j = P.jourDe(new Date(2026, 9, 1, 23, 30));
  assert.equal(P.texteDuJour(j), '2026-10-01');
  assert.equal(P.jourDe(new Date(2026, 9, 2, 0, 5)), j + 1);
});

test('Éclats : barème et crédit unique', () => {
  assert.deepEqual([0, 9, 10, 12, 13, 16, 17, 18, 19, 20].map(n => E.gainPour(n)), [0, 0, 10, 10, 25, 45, 45, 75, 75, 120]);
  assert.deepEqual(E.paliers().map(p => p.libelle), ['0 à 9', '10 à 12', '13 à 15', '16 ou 17', '18 ou 19', '20']);
  const e = P.etatVide();
  assert.ok(E.crediter(e, 'memo-quiz-2026-10-01', 45, 'Quiz du jour'));
  assert.ok(!E.crediter(e, 'memo-quiz-2026-10-01', 45, 'Quiz du jour'));
  assert.ok(!E.crediter(e, 'memo-quiz-2026-10-02', 0, 'Quiz du jour'));
  assert.equal(E.solde(e), 45);
});

test('stockage : relecture et état abîmé', () => {
  const m = new Map(), s = {getItem: k => m.get(k) ?? null, setItem: (k, v) => m.set(k, v)};
  const e = P.etatVide(); P.noter(e, 'a/x', true, 1);
  P.sauver(s, e);
  assert.equal(P.charger(s).fiches['a/x'].b, 2);
  m.set(P.CLE_STOCKAGE, '{pas du json');
  assert.deepEqual(P.charger(s).fiches, {});
});

/* ---------- sur les vraies données, si elles ont été exportées ---------- */
const racine = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const dossier = path.join(racine, 'data', 'listes');
test('toutes les listes donnent des questions justes avec la bonne réponse', {skip: !fs.existsSync(dossier)}, () => {
  let n = 0, sansQuestion = [];
  for (const f of fs.readdirSync(dossier)) {
    const l = JSON.parse(fs.readFileSync(path.join(dossier, f), 'utf8'));
    let possibles = 0;
    for (const fiche of l.fiches) {
      for (const hasard of [() => 0, () => 0.99, () => 0.3]) {
        const q = tirerQuestion(l, fiche, hasard);
        if (!q) continue;
        possibles++;
        const d = deplier(q, l);
        assert.ok(d.bonne, `${l.id}/${fiche.id} : réponse vide`);
        assert.ok(juste(d.bonne, d.bonne, d.estNom), `${l.id}/${fiche.id} : « ${d.bonne} » refusée`);
        n++;
      }
      assert.ok(fiche.valeurs[l.cle], `${l.id}/${fiche.id} : fiche sans nom`);
    }
    if (!possibles) sansQuestion.push(l.id);
    colonnesDemandables(l, l.fiches[0]);
  }
  assert.deepEqual(sansQuestion, []);
  assert.ok(n > 10000);
});

test('barème réglable : remise en ordre et gains', () => {
  assert.deepEqual(E.normaliserBareme([[15, '30'], [5, 5], [5, 8], [0, 99], [25, 1], ['x', 3], [20, -4]]),
    [[5, 8], [15, 30], [20, 0]]);
  assert.equal(E.normaliserBareme([]), null);
  assert.equal(E.normaliserBareme('n importe quoi'), null);
  const b = [[5, 8], [15, 30], [20, 200]];
  assert.deepEqual([4, 5, 14, 15, 19, 20].map(n => E.gainPour(n, b)), [0, 8, 8, 30, 30, 200]);
  assert.deepEqual(E.paliers(b).map(p => `${p.libelle}:${p.gain}`), ['0 à 4:0', '5 à 14:8', '15 à 19:30', '20:200']);
  assert.deepEqual(E.paliers([[1, 2]]).map(p => p.libelle), ['0', '1 à 20']);
  const e = P.etatVide();
  assert.deepEqual(E.baremeEnVigueur(e), E.BAREME_DEFAUT);
  e.reglages.bareme = b;
  assert.deepEqual(E.baremeEnVigueur(e), b);
  // un quiz garde le barème de son lancement
  assert.deepEqual(E.baremeDuQuiz(e, {bareme: [[10, 10]]}), [[10, 10]]);
  assert.deepEqual(E.baremeDuQuiz(e, {}), b);
});

test('rotation du quiz : toutes les listes et toutes les fiches passent', () => {
  const listes = Array.from({length: 6}, (_, i) => ({
    id: 'l' + i, cle: 0, colonnes: ['Nom'],
    fiches: Array.from({length: 3}, (_, k) => ({id: 'f' + k, image: 'thumbs/x.webp', valeurs: [`Nom ${i}-${k}`]})),
  }));
  const rotation = {listes: {}, fiches: {}};
  const vues = new Set(), listesVues = [];
  for (let jour = 1; jour <= 9; jour++) {
    const ordre = parAnciennete(listes.map(l => l.id), rotation.listes).map(id => listes.find(l => l.id === id));
    const qs = tirerQuiz(ordre, rotation, 2);
    assert.equal(qs.length, 2);
    qs.forEach(q => { vues.add(`${q.l}/${q.f}`); listesVues.push(q.l); });
    noterRotation(rotation, qs, jour);
  }
  // 6 listes, 2 par jour : chaque liste revient tous les 3 jours
  assert.deepEqual(new Set(listesVues.slice(0, 6)).size, 6);
  // 18 fiches, 2 par jour sur 9 jours : aucune n'a été reposée avant que toutes passent
  assert.equal(vues.size, 18);
});

test('catalogue mouvant : fiches retirées mises de côté, listes nouvelles repérées', () => {
  const e = P.etatVide(), j = 30000;
  P.noter(e, 'a/x', false, j - 2);
  P.noter(e, 'a/y', true, j - 2);
  P.noter(e, 'retiree/z', false, j - 2);
  const garde = cle => cle.startsWith('a/');
  assert.deepEqual(P.fichesDues(e, j, garde), ['a/x']);
  assert.deepEqual(P.repartition(e, garde), [0, 1, 1, 0, 0, 0]);
  assert.equal(P.misesDeCote(e, garde), 1);
  assert.equal(P.maitrise(e, 'a', 2, garde), 30);
  assert.ok(e.fiches['retiree/z'], 'la progression d\'une fiche retirée est gardée');
  assert.deepEqual(P.noterCatalogue(e, ['a', 'b'], j), []);          // premier lancement : rien de nouveau
  assert.deepEqual(P.noterCatalogue(e, ['a', 'b', 'c'], j + 1), ['c']);
  assert.ok(P.estNouvelleListe(e, 'c', j + 5));
  assert.ok(!P.estNouvelleListe(e, 'c', j + 20));
  assert.ok(!P.estNouvelleListe(e, 'a', j + 5));
  assert.deepEqual(P.noterCatalogue(e, ['a'], j + 2), []);            // une liste retirée reste connue
  assert.deepEqual(P.noterCatalogue(e, ['a', 'b'], j + 3), []);       // et n'est pas « nouvelle » à son retour
});

test('ancien état sans réglages ni rotation : complété au chargement', () => {
  const m = new Map([[P.CLE_STOCKAGE, JSON.stringify({v: 1, fiches: {}, suivies: [], jours: {}, quiz: null, eclats: {journal: []}})]]);
  const e = P.charger({getItem: k => m.get(k) ?? null});
  assert.deepEqual(e.rotation, {listes: {}, fiches: {}});
  assert.deepEqual(e.reglages, {});
  assert.equal(e.catalogue.connues, null);
});

const catalogue = path.join(racine, 'data', 'catalogue.json');
test('catalogue : identifiants cohérents avec les listes, liens valides', {skip: !fs.existsSync(catalogue)}, () => {
  const c = JSON.parse(fs.readFileSync(catalogue, 'utf8'));
  for (const info of c.listes) {
    const l = JSON.parse(fs.readFileSync(path.join(dossier, `${info.id}.json`), 'utf8'));
    assert.equal(info.ids, l.fiches.map(f => f.id).join(' '), info.id);
    assert.equal(new Set(l.fiches.map(f => f.id)).size, l.fiches.length, `${info.id} : identifiants en double`);
    for (const f of l.fiches) if (f.wiki) assert.match(f.wiki, /^https:\/\/[a-z]+\.wikipedia\.org\/wiki\/./, `${info.id}/${f.id}`);
  }
});
