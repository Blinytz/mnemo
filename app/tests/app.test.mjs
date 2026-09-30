// Tests des modules sans écran : node --test app/tests/
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {corriger, norm} from '../js/correction.js';
import * as P from '../js/progression.js';
import * as E from '../js/eclats.js';
import {tirerQuestion, deplier, colonnesDemandables} from '../js/questions.js';

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
  assert.deepEqual([0, 9, 10, 12, 13, 16, 17, 18, 19, 20].map(E.gainPour), [0, 0, 10, 10, 25, 45, 45, 75, 75, 120]);
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
