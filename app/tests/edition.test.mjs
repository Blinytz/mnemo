// Tests de l'édition sur l'appareil, de la collecte et du client du registre
import test from 'node:test';
import assert from 'node:assert/strict';
import * as ED from '../js/edition.js';
import * as E from '../js/eclats.js';
import * as P from '../js/progression.js';
import {createRegistre} from '../js/registre.js';

const officielle = () => ({id: 'fromages', nom: 'Fromages', icone: '🧀', categorie: 'gastronomie', colonnes: ['Fromage', 'Région'], cle: 0,
  fiches: [{id: 'comte', valeurs: ['Comté', 'Jura'], image: 'thumbs/fromages/comte.webp', grande: 'full/fromages/comte.webp'},
           {id: 'brie', valeurs: ['Brie', 'Île-de-France'], image: 'thumbs/fromages/brie.webp'}]});

test('couche de modifications sur une liste officielle', () => {
  const ed = ED.editionVide(), l = officielle();
  ED.modifierFiche(ed, l, 'comte', ['Comté', 'Franche-Comté']);
  let vue = ED.appliquer(l, ed);
  assert.equal(vue.fiches[0].valeurs[1], 'Franche-Comté');
  assert.equal(vue.fiches[0].modifiee, true);
  assert.equal(vue.fiches[0].grande, 'full/fromages/comte.webp');     // image inchangée : la grande reste
  assert.equal(l.fiches[0].valeurs[1], 'Jura', "la liste officielle n'est jamais réécrite");
  ED.modifierFiche(ed, l, 'comte', ['Comté', 'Franche-Comté'], 'perso:abc');
  vue = ED.appliquer(l, ed);
  assert.equal(vue.fiches[0].image, 'perso:abc');
  assert.equal(vue.fiches[0].grande, undefined);
  ED.retablirFiche(ed, 'fromages', 'comte');
  assert.deepEqual(ED.appliquer(l, ed).fiches[0], l.fiches[0]);
  assert.deepEqual(ed.modifs, {});
});

test('ajout, masquage et retour des fiches', () => {
  const ed = ED.editionVide(), l = officielle();
  const f = ED.ajouterFiche(ed, l, ['Salers', 'Auvergne']);
  ED.supprimerFiche(ed, 'fromages', 'brie');
  const vue = ED.appliquer(l, ed);
  assert.deepEqual(vue.fiches.map(x => x.id), ['comte', f.id]);
  assert.equal(vue.fiches[1].ajoutee, true);
  assert.deepEqual(ED.idsVisibles({id: 'fromages', ids: 'comte brie'}, ed), ['comte', f.id]);
  ED.modifierFiche(ed, l, f.id, ['Salers', 'Cantal']);
  assert.equal(ED.appliquer(l, ed).fiches[1].valeurs[1], 'Cantal');
  ED.supprimerFiche(ed, 'fromages', f.id);                           // une fiche ajoutée disparaît vraiment
  assert.deepEqual(ed.ajouts.fromages, []);
  assert.equal(ED.restaurerFichesRetirees(ed, 'fromages'), 1);
  assert.equal(ED.appliquer(l, ed).fiches.length, 2);
});

test('listes personnelles', () => {
  const ed = ED.editionVide();
  assert.throws(() => ED.creerListe(ed, {nom: ' ', colonnes: ['A']}));
  assert.throws(() => ED.creerListe(ed, {nom: 'X', colonnes: [' ']}));
  const t = ED.lireTableau('Pays\tCapitale\nFrance\tParis\n\nItalie\tRome\n');
  const l = ED.creerListe(ed, {nom: 'Capitales', icone: '', colonnes: t.colonnes, lignes: t.lignes});
  assert.equal(l.icone, '📋');
  assert.deepEqual(l.fiches.map(f => f.valeurs), [['France', 'Paris'], ['Italie', 'Rome']]);
  assert.ok(ED.estPerso(ed, l.id));
  assert.equal(ED.appliquer(l, ed), l);
  ED.ajouterFiche(ed, l, ['Espagne', 'Madrid'], 'perso:k1');
  ED.modifierListe(ed, l.id, {nom: "Capitales d'Europe", icone: '🏛️'});
  const r = ED.resumePerso(ED.listePerso(ed, l.id));
  assert.deepEqual([r.nom, r.fiches, r.categorie, r.perso, r.apercu], ["Capitales d'Europe", 3, 'mes-listes', true, ['perso:k1']]);
  assert.deepEqual([...ED.imagesUtilisees(ed)], ['k1']);
  ED.supprimerFiche(ed, l.id, l.fiches[0].id);
  assert.equal(ED.listePerso(ed, l.id).fiches.length, 2);
  ED.supprimerListe(ed, l.id);
  assert.equal(ed.perso.length, 0);
});

test('tableaux collés : tabulations, point-virgule, guillemets', () => {
  assert.deepEqual(ED.lireTableau('a;b\n"x;1";"dit ""oui"""\n'), {colonnes: ['a', 'b'], lignes: [['x;1', 'dit "oui"']]});
  assert.deepEqual(ED.lireTableau('a,b\n1,2'), {colonnes: ['a', 'b'], lignes: [['1', '2']]});
  assert.deepEqual(ED.lireLignes('x\ty\r\nz\tw'), [['x', 'y'], ['z', 'w']]);
  assert.deepEqual(ED.lireTableau(''), {colonnes: [], lignes: []});
});

test("reprise des listes personnelles de l'ancienne version", () => {
  const anciennes = [
    {id: 'custom_1', name: 'Rivières', icon: '🌊', _source: 'custom', columns: ['Numéro', 'Image', 'Rivière', 'Pays'],
     rows: [['1', 'https://ex.org/a.jpg', 'Loire', 'France'], ['2', '', 'Rhin', 'Allemagne'], ['3', '', '', '']]},
    {id: 'pays', name: 'Pays', _source: 'default', columns: [], rows: []},
  ];
  const m = new Map([['memo_v62_local_lists', JSON.stringify(anciennes)]]);
  const trouvees = ED.listesAnciennes({getItem: k => m.get(k) ?? null});
  assert.deepEqual(trouvees.map(l => l.id), ['custom_1']);
  const ed = ED.editionVide();
  const l = ED.reprendreAncienne(ed, trouvees[0]);
  assert.deepEqual(l.colonnes, ['Rivière', 'Pays']);
  assert.deepEqual(l.fiches.map(f => [f.valeurs[0], f.image]), [['Loire', 'https://ex.org/a.jpg'], ['Rhin', undefined]]);
  assert.equal(ED.reprendreAncienne(ed, trouvees[0]), null, "une liste n'est reprise qu'une fois");
});

/* ---------- collecte dans le registre ---------- */
function fauxRegistre({connecte = true, echoue = false} = {}) {
  const appels = [];
  return {appels, estConnecte: () => connecte,
    recompenser: async a => { appels.push(a); if (echoue) throw new Error('réseau'); return {movement_id: 'm' + appels.length, balance_after: 100}; }};
}

test("collecte : une seule fois par quiz, registre d'abord", async () => {
  const e = P.etatVide();
  E.crediter(e, 'memo-quiz-2026-10-01', 45, 'Quiz du jour', {jour: '2026-10-01', score: 16, bareme: E.BAREME_DEFAUT});
  E.crediter(e, 'memo-quiz-2026-10-02', 10, 'Quiz du jour', {jour: '2026-10-02', score: 11});
  assert.equal(E.montantACollecter(e), 55);
  await assert.rejects(E.collecter(e, fauxRegistre({connecte: false}), 'memo-quiz-2026-10-01'));
  await assert.rejects(E.collecter(e, fauxRegistre({echoue: true}), 'memo-quiz-2026-10-01'));
  assert.equal(E.montantACollecter(e), 55, 'un échec du registre ne marque rien comme versé');
  const r = fauxRegistre();
  await E.collecter(e, r, 'memo-quiz-2026-10-01');
  await E.collecter(e, r, 'memo-quiz-2026-10-01');
  assert.equal(r.appels.length, 1);
  assert.deepEqual([r.appels[0].montant, r.appels[0].idempotencyKey, r.appels[0].referenceId, r.appels[0].referenceType],
    [45, 'memo-quiz-2026-10-01', null, 'quiz_memo']);
  assert.match(r.appels[0].reason, /16 \/ 20/);
  const tout = await E.toutCollecter(e, r);
  assert.deepEqual([tout.verses, tout.montant, tout.erreur], [1, 10, null]);
  assert.equal(E.montantACollecter(e), 0);
  assert.equal(E.solde(e), 55, 'le total gagné dans Mémo ne change pas au versement');
});

test('client du registre : application « memo », session partagée', async () => {
  const stock = new Map([['eclats_session', JSON.stringify({access_token: 't', refresh_token: 'r', user: {email: 'x@y'}})]]);
  const requetes = [];
  const reg = createRegistre({
    storage: {getItem: k => stock.get(k) ?? null, setItem: (k, v) => stock.set(k, v), removeItem: k => stock.delete(k)},
    fetch: async (url, o) => { requetes.push([url, o]); return {ok: true, status: 200, text: async () => '{"movement_id":"m1","balance_after":3152}'}; },
  });
  assert.ok(reg.estConnecte());
  const rep = await reg.recompenser({montant: 45, reason: 'Quiz', referenceType: 'quiz_memo', idempotencyKey: 'memo-quiz-2026-10-01'});
  assert.equal(rep.balance_after, 3152);
  const [url, o] = requetes[0];
  assert.match(url, /\/rest\/v1\/rpc\/eclats_reward$/);
  const corps = JSON.parse(o.body);
  assert.deepEqual([corps.p_app_id, corps.p_amount, corps.p_idempotency_key, corps.p_reference_id], ['memo', 45, 'memo-quiz-2026-10-01', null]);
  assert.equal(o.headers.Authorization, 'Bearer t');
  assert.ok(!('depenser' in reg) && !('spend' in reg), 'Mémo ne sait pas dépenser');
});
