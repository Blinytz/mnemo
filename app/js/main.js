// Mémo : écrans et séances.
//
// Quatre onglets (Aujourd'hui, Listes, Réviser, Progrès), une page par liste,
// une feuille de détail par fiche, et une séance plein écran qui sert à la fois
// aux révisions (sans Éclats) et au quiz du jour (20 questions, barème
// réglable). Le catalogue peut gagner ou perdre des listes d'une version à
// l'autre : les calculs ne retiennent que les fiches encore présentes.

import {ICONES, LOGO, ECLAT} from './icones.js';
import * as P from './progression.js';
import * as E from './eclats.js';
import {corriger} from './correction.js';
import {tirerQuestion, deplier, melanger, parAnciennete, tirerQuiz, noterRotation} from './questions.js';
import {chargerCatalogue, chargerListe, chemin} from './donnees.js';

/* ---------- outils ---------- */
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const ic = (n, v = 'regular') => `<svg class="i" viewBox="0 0 256 256" aria-hidden="true">${ICONES[`${n}-${v}`] || ''}</svg>`;
const logo = () => `<svg viewBox="0 0 256 256" aria-hidden="true"><path d="${LOGO}"/></svg>`;
const eclat = (cls = 'eclat-glyphe') => `<svg class="${cls}" viewBox="0 0 256 256" aria-hidden="true"><path d="${ECLAT}"/></svg>`;
const sansAccents = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
const pluriel = (n, mot, motPluriel = mot + 's') => `${n} ${n > 1 ? motPluriel : mot}`;
const img = (p, alt = '', attrs = '') => p ? `<img src="${esc(chemin(p))}" alt="${esc(alt)}" ${attrs}>` : `<span class="sans-image" aria-hidden="true"></span>`;

let etat = P.charger(localStorage);
const enregistrer = () => P.sauver(localStorage, etat);
const auj = () => P.jourDe();
let C = null;                                   // catalogue
let actives = new Set();                        // clés « liste/fiche » encore au catalogue
const garde = cle => actives.has(cle);
const chargees = new Map();                     // listes déjà lues, par identifiant
async function liste(id) {
  if (!chargees.has(id)) chargees.set(id, await chargerListe(id));
  return chargees.get(id);
}

/* ---------- calculs sur le catalogue ---------- */
const infoListe = id => C.parId.get(id);
const nomCategorie = id => C.categories.find(c => c.id === id) || {nom: '', icone: ''};
const maitriseListe = id => P.maitrise(etat, id, infoListe(id)?.fiches || 0, garde);
function duesParListe() {
  const m = new Map();
  for (const cle of P.fichesDues(etat, auj(), garde)) { const l = cle.split('/')[0]; m.set(l, (m.get(l) || 0) + 1); }
  return m;
}
function vuesParListe() {
  const m = new Map();
  for (const cle of Object.keys(etat.fiches)) if (garde(cle)) { const l = cle.split('/')[0]; m.set(l, (m.get(l) || 0) + 1); }
  return m;
}
const suivies = () => etat.suivies.filter(id => C.parId.has(id));
function nouvellesDisponibles() {
  const vues = vuesParListe();
  return suivies().reduce((s, id) => s + Math.max(0, infoListe(id).fiches - (vues.get(id) || 0)), 0);
}
const estNouvelle = id => P.estNouvelleListe(etat, id, auj());

// Lien pour approfondir : l'article exact quand WikiDeck le connaît, sinon une
// recherche (qui ouvre directement l'article si le titre existe)
function lienPour(l, f) {
  const nom = String(f.valeurs[l.cle] || '').replace(/\s*\([^)]*\)/g, '').trim();
  if (f.wiki) return {url: f.wiki, texte: 'Lire sur Wikipédia'};
  if (l.categorie === 'langues-vocabulaire') return {url: `https://fr.wiktionary.org/wiki/${encodeURIComponent(nom)}`, texte: 'Voir dans le Wiktionnaire'};
  return {url: `https://fr.wikipedia.org/w/index.php?search=${encodeURIComponent(nom)}&go=Go`, texte: 'Chercher sur Wikipédia'};
}
const lienWiki = (l, f) => { const x = lienPour(l, f); return `<a class="lien-wiki" href="${esc(x.url)}" target="_blank" rel="noopener">${ic('arrow-square-out')}${x.texte}</a>`; };

// ordre stable dans la journée, différent d'un jour à l'autre
function ordreDuJour(ids) {
  const h = s => { let x = auj(); for (const ch of s) x = (x * 31 + ch.charCodeAt(0)) % 1000003; return x; };
  return [...ids].sort((a, b) => h(a) - h(b));
}

/* ---------- navigation ---------- */
const vue = {page: 'aujourdhui', liste: null, affichage: 'fiches', filtre: 'tout', recherche: ''};
const ONGLETS = [['aujourdhui', "Aujourd'hui", 'house'], ['listes', 'Listes', 'books'], ['reviser', 'Réviser', 'lightning'], ['progres', 'Progrès', 'chart-line-up']];

function rendreOnglets() {
  $('#onglets nav').innerHTML = ONGLETS.map(([id, lib, n]) => id === 'reviser'
    ? `<button class="principal" data-onglet="${id}"><span class="rond">${ic(n, 'fill')}</span>${lib}</button>`
    : `<button data-onglet="${id}" ${vue.page === id || (id === 'listes' && vue.page === 'liste') ? 'aria-current="page"' : ''}>${ic(n, vue.page === id ? 'fill' : 'regular')}${lib}</button>`).join('');
  $$('[data-onglet]').forEach(b => b.onclick = () => {
    if (b.dataset.onglet === 'reviser') return lancerRevision().catch(erreur);
    aller(b.dataset.onglet);
  });
}
function aller(page) { vue.page = page; rendre(); window.scrollTo({top: 0}); }

function haut(titre) {
  const s = P.serie(etat, auj());
  return `<header class="haut"><div class="tuile">${logo()}</div><div class="marque">${titre}</div>
    <span class="pastille serie" title="Série : jours d'affilée à ${P.OBJECTIF_JOUR} réponses">${ic('fire', 'fill')}<span class="chiffre">${s}</span></span>
    <span class="pastille eclats" title="Éclats gagnés au quiz du jour">${eclat()}<span class="chiffre">${E.solde(etat).toLocaleString('fr-FR')}</span></span>
    <button class="pastille rond-reglages" id="reglages" aria-label="Réglages" title="Réglages">${ic('gear')}</button></header>`;
}

function blocBareme(score, bareme) {
  return `<div class="bareme">${E.paliers(bareme).map(p => {
    const atteint = score !== undefined && score >= p.seuil && score <= p.fin;
    return `<div class="palier ${atteint ? 'atteint' : ''}"><b>${p.gain ? `${p.gain} ${eclat()}` : '0'}</b><span>${p.libelle}</span></div>`;
  }).join('')}</div>`;
}

/* ---------- Aujourd'hui ---------- */
function vueAujourdhui() {
  const j = auj(), dues = P.fichesDues(etat, j, garde).length, neuves = Math.min(nouvellesDisponibles(), 5);
  const faits = P.reponsesDuJour(etat, j), objectif = Math.min(100, Math.round(100 * faits / P.OBJECTIF_JOUR));
  const qj = etat.quiz?.jour === j ? etat.quiz : null;
  const n = E.QUESTIONS_QUIZ, bareme = qj ? E.baremeDuQuiz(etat, qj) : E.baremeEnVigueur(etat);
  const quiz = qj?.fini
    ? `<h1><span class="chiffre">${qj.score} / ${n}</span> · +${qj.gain} ${eclat()}</h1><p class="sous" style="margin:0">Fait aujourd'hui. Reviens demain pour un nouveau tirage.</p>${blocBareme(qj.score, bareme)}`
    : qj
      ? `<h1>Quiz commencé : ${qj.reponses.length} / ${n}</h1><p class="sous" style="margin:0">Tes réponses sont gardées. Reprends où tu t'es arrêté.</p>${blocBareme(undefined, bareme)}
         <button class="bouton eclat large" id="quiz-jour">${ic('play', 'fill')} Reprendre le quiz</button>`
      : `<h1>N'importe quelle liste, ${n} questions</h1><p class="sous" style="margin:0">Une seule tentative par jour. Tu tapes tes réponses ; plus tu en trouves, plus tu gagnes d'Éclats.</p>${blocBareme(undefined, bareme)}
         <button class="bouton eclat large" id="quiz-jour">${ic('trophy', 'fill')} Tenter le quiz du jour</button>`;

  let heros;
  if (!suivies().length && !dues) {
    heros = `<h1>Choisis ta première liste</h1>
      <p>Chaque liste que tu révises entre dans ta mémoire : Mémo te repose ensuite ses fiches au bon moment, un peu chaque jour.</p>
      <button class="bouton plein large" data-onglet-lien="listes">${ic('books', 'fill')} Parcourir les listes</button>`;
  } else if (!dues && !neuves) {
    heros = `<h1>Tout est à jour</h1><p>Aucune fiche à revoir aujourd'hui. Ajoute une liste pour découvrir de nouvelles fiches.</p>
      <button class="bouton plein large" data-onglet-lien="listes">${ic('books', 'fill')} Ajouter une liste</button>`;
  } else {
    heros = `<h1>${pluriel(dues + neuves, "fiche t'attend", "fiches t'attendent")}</h1>
      <div class="ligne">
        <div><div class="val chiffre">${dues}</div><div class="lib">à revoir</div></div>
        <div><div class="val chiffre">${neuves}</div><div class="lib">${neuves > 1 ? 'nouvelles' : 'nouvelle'}</div></div>
        <div><div class="val chiffre">≈ ${Math.max(1, Math.round(Math.min(dues + neuves, 20) * 0.35))} min</div><div class="lib">durée</div></div>
      </div>
      <button class="bouton plein large" id="go">${ic('play', 'fill')} Réviser</button>`;
  }

  const derniere = etat.derniere && infoListe(etat.derniere);
  // « À découvrir » : 8 listes pas encore suivies ; les nouvelles d'abord, puis
  // un ordre qui change chaque jour
  const pasSuivies = C.listes.filter(l => !etat.suivies.includes(l.id)).map(l => l.id);
  const aDecouvrir = [...pasSuivies.filter(estNouvelle), ...ordreDuJour(pasSuivies.filter(id => !estNouvelle(id)))].slice(0, 8).map(infoListe);

  return haut('Mémo') + `
  <section class="quiz-jour monte">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
      <span class="etiquette" style="color:var(--eclat)">Quiz du jour</span>
      <span class="sous">${qj?.fini ? 'Nouveau quiz demain' : `${n} questions · toutes les listes`}</span></div>
    ${quiz}
  </section>

  <section class="heros section">
    <div class="anneau"></div>
    <span class="etiquette" style="color:#8FA0B6">Révision du jour</span>
    ${heros}
    <p style="font-size:13px">Les révisions ne rapportent pas d'Éclats : elles font monter tes fiches vers « Acquise ».</p>
  </section>

  <section class="section"><div class="carte objectif">
    <div class="jauge" style="--p:${objectif}"><span class="chiffre">${objectif}%</span></div>
    <div><h3>Objectif du jour</h3><div class="sous">${faits} / ${P.OBJECTIF_JOUR} réponses · ${faits >= P.OBJECTIF_JOUR ? 'journée validée' : `la série passe à ${P.serie(etat, j) + 1} ${P.serie(etat, j) ? 'jours' : 'jour'} à ${P.OBJECTIF_JOUR}`}</div></div>
  </div></section>

  ${derniere ? `<section class="section"><header><h2>Continuer</h2></header>
    <button class="carte continuer" data-liste="${derniere.id}">
      ${img(derniere.apercu[0])}
      <div style="text-align:left"><h3>${esc(derniere.nom)}</h3><div class="barre" style="margin:7px 0 4px"><i style="width:${maitriseListe(derniere.id)}%"></i></div><div class="sous">${maitriseListe(derniere.id)} % maîtrisé · ${derniere.fiches} fiches</div></div>
      ${ic('caret-right')}
    </button></section>` : ''}

  <section class="section"><header><h2>À découvrir</h2><button class="lien" data-onglet-lien="listes">Tout voir</button></header>
    <div class="defiler">${aDecouvrir.map(l => `<button class="decouverte" data-liste="${l.id}">${img(l.apercu[0])}<div>${estNouvelle(l.id) ? '<span class="badge eclat">Nouvelle</span>' : ''}${esc(l.nom)}<small>${l.fiches} fiches</small></div></button>`).join('')}</div>
  </section>`;
}

/* ---------- Listes ---------- */
function vueListes() {
  const dues = duesParListe();
  const cats = C.categories.filter(c => C.listes.some(l => l.categorie === c.id));
  const q = sansAccents(vue.recherche.trim());
  const garde = l => (vue.filtre === 'tout' || l.categorie === vue.filtre) && (!q || sansAccents(l.nom).includes(q));
  const blocs = cats.map(c => {
    const ls = C.listes.filter(l => l.categorie === c.id && garde(l)).sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
    if (!ls.length) return '';
    return `<div class="titre-cat"><span style="font-size:20px">${c.icone}</span><h2>${esc(c.nom)}</h2><span class="pct">${pluriel(ls.length, 'liste')}</span></div>
      <div class="carte" style="padding:4px 14px">${ls.map(l => {
        const m = maitriseListe(l.id), d = dues.get(l.id) || 0, suivie = etat.suivies.includes(l.id);
        return `<button class="ligne-liste" data-liste="${l.id}"><span class="ic-liste">${l.icone}</span>
          <span><span class="nom">${esc(l.nom)}</span><span class="meta">${suivie ? `<span class="barre"><i style="width:${m}%"></i></span><span class="sous chiffre">${m} %</span>` : `<span class="sous">${l.fiches} fiches</span>`}</span></span>
          ${d ? `<span class="badge">${d} à revoir</span>` : estNouvelle(l.id) ? '<span class="badge eclat">Nouvelle</span>' : ic('caret-right')}</button>`;
      }).join('')}</div>`;
  }).join('');
  return haut('Listes') + `
    <div class="pile"><label class="recherche">${ic('magnifying-glass')}<input id="rech" type="search" placeholder="Chercher parmi ${C.listes.length} listes" value="${esc(vue.recherche)}" aria-label="Chercher une liste"></label>
    <div class="puces" role="group" aria-label="Catégories">${[['tout', 'Tout']].concat(cats.map(c => [c.id, c.icone + ' ' + c.nom])).map(([id, lib]) => `<button class="puce" data-cat="${id}" aria-pressed="${vue.filtre === id}">${esc(lib)}</button>`).join('')}</div></div>
    ${blocs || '<p class="sous" style="margin-top:24px">Aucune liste ne correspond.</p>'}`;
}

/* ---------- Page d'une liste ---------- */
function niveaux(b) {
  return `<div class="niveaux" aria-label="${P.LIBELLES[b]}">${[1, 2, 3, 4, 5].map(n => `<i class="${b >= n ? 'on' : ''}"></i>`).join('')}</div>`;
}
function vueListe() {
  const info = infoListe(vue.liste), l = chargees.get(vue.liste);
  const retour = `<button class="retour" id="retour">${ic('arrow-left')} Listes</button>`;
  if (!l) return retour + `<p class="sous" style="margin-top:20px">Chargement de la liste…</p>`;
  const m = maitriseListe(l.id), dues = duesParListe().get(l.id) || 0;
  const vues = vuesParListe().get(l.id) || 0, neuves = l.fiches.length - vues;
  const cle = f => P.cleFiche(l.id, f.id);
  const autres = l.colonnes.map((c, i) => i).filter(i => i !== l.cle);
  return `${retour}
    <div class="entete-liste"><div><span class="etiquette">${esc(nomCategorie(l.categorie).nom)}</span><h1>${l.icone} ${esc(l.nom)}</h1>
      <div class="sous" style="margin-top:4px">${l.fiches.length} fiches · ${esc(l.colonnes.join(' · '))}</div></div>
      <div class="jauge" style="--p:${m}"><span class="chiffre">${m}%</span></div></div>
    <div class="actions">
      <button class="bouton memo" data-reviser="${l.id}">${ic('lightning', 'fill')} ${dues ? `Réviser (${dues})` : 'Réviser'}</button>
      <button class="bouton fantome" data-reviser="${l.id}" data-mode="decouvrir" ${neuves ? '' : 'disabled'}>${ic('sparkle')} ${neuves ? 'Découvrir' : 'Tout vu'}</button></div>
    <div class="segment" role="group" aria-label="Affichage"><button data-vue="fiches" aria-pressed="${vue.affichage === 'fiches'}">Fiches</button><button data-vue="tableau" aria-pressed="${vue.affichage === 'tableau'}">Tableau</button></div>
    ${vue.affichage === 'fiches'
      ? `<div class="grille">${l.fiches.map(f => `<button class="fiche" data-fiche="${esc(f.id)}">${f.image ? img(f.image, '', 'loading="lazy"') : ''}<div class="corps"><div class="nom">${esc(f.valeurs[l.cle])}</div><div class="sec">${esc(f.valeurs[autres[0]] || '')}</div>${niveaux(P.boite(etat, cle(f)))}</div></button>`).join('')}</div>`
      : `<div class="tableau"><table><thead><tr><th>${esc(l.colonnes[l.cle])}</th>${autres.map(i => `<th>${esc(l.colonnes[i])}</th>`).join('')}</tr></thead><tbody>${l.fiches.map(f => `<tr data-fiche="${esc(f.id)}"><td>${esc(f.valeurs[l.cle])}</td>${autres.map(i => `<td>${esc(f.valeurs[i])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}`;
}
async function ouvrirListe(id) {
  vue.page = 'liste'; vue.liste = id; vue.affichage = 'fiches';
  rendre(); window.scrollTo({top: 0});
  try { await liste(id); } catch { toast('Liste introuvable'); return aller('listes'); }
  if (vue.page === 'liste' && vue.liste === id) rendre();
}

function ouvrirFiche(idListe, idFiche) {
  const l = chargees.get(idListe), f = l?.fiches.find(x => x.id === idFiche);
  if (!f) return;
  const b = P.boite(etat, P.cleFiche(idListe, idFiche));
  const autres = l.colonnes.map((c, i) => i).filter(i => i !== l.cle && f.valeurs[i]);
  $('#feuille').innerHTML = `<div class="poignee"></div>${f.image ? img(f.grande || f.image, f.valeurs[l.cle]) : ''}<div class="contenu">
    <div><span class="etiquette">${esc(l.nom)}</span><h1 style="margin-top:4px">${esc(f.valeurs[l.cle])}</h1></div>
    ${f.carte ? `<div class="carte-loc">${img(f.carte, 'Localisation')}</div>` : ''}
    <dl>${autres.map(i => `<div><dt>${esc(l.colonnes[i])}</dt><dd>${esc(f.valeurs[i])}</dd></div>`).join('')}</dl>
    ${lienWiki(l, f)}
    <div class="carte" style="box-shadow:none;background:var(--surface-2);display:flex;gap:12px;align-items:center">${niveaux(b).replace('class="niveaux"', 'class="niveaux" style="flex:1;margin:0"')}<span class="sous">${b ? `${P.LIBELLES[b]} · niveau ${b} sur 5` : 'Jamais révisée'}</span></div>
    <button class="bouton fantome large" id="fermer">Fermer</button></div>`;
  $('#voile').classList.add('ouvert');
  $('#fermer').onclick = fermerFiche;
}
function fermerFiche() { $('#voile').classList.remove('ouvert'); }

/* ---------- Progrès ---------- */
function vueProgres() {
  const j = auj(), cmpt = P.repartition(etat, garde), maxB = Math.max(...cmpt.slice(1), 1);
  const deCote = P.misesDeCote(etat, garde);
  const taux = P.reussite(etat, j), mois = new Date(); mois.setDate(1); mois.setHours(0, 0, 0, 0);
  const jours = Array.from({length: 84}, (_, i) => {
    const n = P.reponsesDuJour(etat, j - 83 + i);
    return n >= P.OBJECTIF_JOUR ? 3 : n >= 10 ? 2 : n > 0 ? 1 : 0;
  });
  const cats = C.categories.map(c => {
    const ls = suivies().filter(id => infoListe(id).categorie === c.id);
    return ls.length ? [c.icone, c.nom, Math.round(ls.reduce((s, id) => s + maitriseListe(id), 0) / ls.length)] : null;
  }).filter(Boolean).sort((a, b) => b[2] - a[2]);
  return haut('Progrès') + `
    <div class="stats monte">
      <div class="stat"><b class="chiffre">${cmpt[5] + cmpt[4]}</b><span>fiches solides ou acquises</span></div>
      <div class="stat"><b class="chiffre">${P.serie(etat, j)} j</b><span>série en cours · record ${P.record(etat)} j</span></div>
      <div class="stat"><b class="chiffre">${taux === null ? '·' : taux + ' %'}</b><span>de réussite sur 7 jours</span></div>
      <div class="stat"><b class="chiffre" style="color:var(--eclat)">${eclat()} ${E.gagnesDepuis(etat, mois.toISOString())}</b><span>Éclats gagnés ce mois</span></div>
    </div>
    <section class="section"><header><h2>Mémoire</h2><span class="sous">${pluriel(cmpt.slice(1).reduce((a, b) => a + b, 0), 'fiche vue', 'fiches vues')}</span></header>
      <div class="carte"><div class="boites">${[1, 2, 3, 4, 5].map(b => `<div><b class="chiffre">${cmpt[b]}</b><span class="col b${b}" style="height:${Math.max(4, 100 * cmpt[b] / maxB)}%"></span><small>${P.LIBELLES[b]}</small></div>`).join('')}</div>
      <p class="sous" style="margin:12px 0 0">Une fiche réussie monte d'une case et revient de plus en plus tard (${P.INTERVALLES.join(', ').replace(/, (\d+)$/, ' puis $1')} jours). Une erreur la renvoie au début.</p>
      ${deCote ? `<p class="sous" style="margin:8px 0 0">${pluriel(deCote, 'fiche révisée appartient', 'fiches révisées appartiennent')} à des listes ou des fiches retirées du catalogue : leur progression est gardée de côté, hors de ces chiffres, et reviendra avec elles.</p>` : ''}</div></section>
    <section class="section"><header><h2>12 dernières semaines</h2></header><div class="carte"><div class="calendrier">${jours.map(n => `<i data-n="${n}"></i>`).join('')}</div></div></section>
    ${cats.length ? `<section class="section"><header><h2>Par catégorie</h2></header><div class="carte cat-maitrise">${cats.map(([i, n, p]) => `<div><span style="font-size:20px">${i}</span><span><b>${esc(n)}</b><span class="barre" style="display:block;margin-top:5px"><i style="width:${p}%"></i></span></span><span class="pct chiffre">${p}%</span></div>`).join('')}</div></section>` : ''}
    <p class="sous" style="margin-top:24px">Pour modifier une liste ou en créer une, l'<a href="../memo.html">ancienne version de Mémo</a> reste disponible pendant la refonte.</p>`;
}

/* ---------- Séances ---------- */
let seance = null;   // {mode, items: [question dépliée], reponses: [], n}

// Rend une question dépliée par question reçue, ou null si sa liste ou sa
// fiche a disparu du catalogue depuis
async function preparer(questions) {
  await Promise.allSettled([...new Set(questions.map(q => q.l))].filter(id => C.parId.has(id)).map(liste));
  return questions.map(q => chargees.has(q.l) ? deplier(q, chargees.get(q.l)) : null);
}

// Une question de secours, prise n'importe où sauf parmi les fiches déjà posées
async function questionDeSecours(prises) {
  for (const id of melanger(C.listes.map(l => l.id))) {
    const l = await liste(id).catch(() => null);
    if (!l) continue;
    for (const f of melanger(l.fiches)) {
      if (prises.has(`${id}/${f.id}`)) continue;
      const q = tirerQuestion(l, f);
      if (q) return q;
    }
  }
  return null;
}

async function lancerRevision(idListe, mode) {
  const j = auj();
  let cles;
  if (idListe) {
    const l = await liste(idListe);
    P.suivre(etat, idListe); etat.derniere = idListe;
    const toutes = l.fiches.map(f => P.cleFiche(idListe, f.id));
    const dues = toutes.filter(c => P.estDue(etat, c, j));
    const neuves = toutes.filter(c => !etat.fiches[c]);
    if (mode === 'decouvrir') cles = neuves.slice(0, 10);
    else {
      cles = [...dues.slice(0, 15), ...neuves.slice(0, Math.max(0, 10 - dues.length))];
      // rien de dû ni de neuf : révision libre des fiches déjà vues, les plus fragiles d'abord
      if (!cles.length) cles = toutes.sort((a, b) => P.boite(etat, a) - P.boite(etat, b)).slice(0, 10);
    }
  } else {
    const dues = P.fichesDues(etat, j, garde).slice(0, 20);
    const neuves = [];
    for (const id of suivies()) {
      if (neuves.length >= 5 || dues.length + neuves.length >= 20) break;
      const l = await liste(id);
      for (const f of l.fiches) {
        const c = P.cleFiche(id, f.id);
        if (!etat.fiches[c]) { neuves.push(c); if (neuves.length >= 5) break; }
      }
    }
    cles = [...dues, ...neuves];
    if (!cles.length) { toast(suivies().length ? "Rien à revoir aujourd'hui" : 'Choisis d\'abord une liste'); return aller('listes'); }
  }
  enregistrer();
  const questions = [];
  for (const c of melanger(cles)) {
    const [l, f] = c.split('/');
    const lst = await liste(l), fiche = lst.fiches.find(x => x.id === f);
    const q = fiche && tirerQuestion(lst, fiche);
    if (q) questions.push(q);
  }
  if (!questions.length) return toast('Aucune question possible pour cette liste');
  seance = {mode: 'revision', items: (await preparer(questions)).filter(Boolean), reponses: [], n: 0};
  ouvrirSeance();
}

async function lancerQuiz() {
  const j = auj();
  if (!(etat.quiz?.jour === j)) {
    // les listes les moins récemment posées d'abord (voir tirerQuiz)
    const ordre = parAnciennete(C.listes.filter(l => l.fiches).map(l => l.id), etat.rotation.listes);
    const lues = (await Promise.allSettled(ordre.slice(0, E.QUESTIONS_QUIZ + 5).map(liste)))
      .filter(r => r.status === 'fulfilled').map(r => r.value);
    const questions = tirerQuiz(lues, etat.rotation, E.QUESTIONS_QUIZ);
    // catalogue de moins de 20 listes : on complète ailleurs
    while (questions.length < E.QUESTIONS_QUIZ) {
      const q = await questionDeSecours(new Set(questions.map(x => `${x.l}/${x.f}`)));
      if (!q) break;
      questions.push(q);
    }
    noterRotation(etat.rotation, questions, j);
    // le barème est figé au lancement
    etat.quiz = {jour: j, questions, reponses: [], fini: false, bareme: E.baremeEnVigueur(etat)};
    enregistrer();
  }
  if (etat.quiz.fini) return;
  const items = await preparer(etat.quiz.questions);
  // une question restant à poser dont la liste a disparu est remplacée
  for (let i = etat.quiz.reponses.length; i < items.length; i++) {
    if (items[i]) continue;
    const q = await questionDeSecours(new Set(etat.quiz.questions.map(x => `${x.l}/${x.f}`)));
    if (!q) continue;
    etat.quiz.questions[i] = q;
    items[i] = (await preparer([q]))[0];
  }
  enregistrer();
  seance = {mode: 'quiz', items, reponses: etat.quiz.reponses, n: etat.quiz.reponses.length};
  if (seance.n >= seance.items.length) return terminer();
  ouvrirSeance();
}

function ouvrirSeance() {
  $('#seance').classList.add('ouverte'); document.body.style.overflow = 'hidden';
  rendreQuestion();
}
function fermerSeance() {
  $('#seance').classList.remove('ouverte'); document.body.style.overflow = ''; seance = null;
  if (vue.page === 'liste' && chargees.has(vue.liste)) rendre(); else rendre();
}
const bonnes = () => seance.reponses.filter(r => r.juste).length;

function rendreQuestion() {
  const it = seance.items[seance.n], r = seance.reponses[seance.n], fini = !!r, quiz = seance.mode === 'quiz';
  const total = seance.items.length, {liste: l, fiche: f} = it;
  const autres = l.colonnes.map((c, i) => i).filter(i => i !== l.cle && f.valeurs[i]);
  const visuel = it.q.t === 'image'
    ? `<div class="visuel">${img(f.image, 'Image à reconnaître')}</div>`
    : it.q.t === 'indice'
      ? `<div class="carte indice"><span class="etiquette">${esc(it.indice.titre)}</span><p>${esc(it.indice.texte)}</p></div>`
      : `<div class="contexte">${f.image ? img(f.image) : ''}<div><span class="etiquette">${esc(l.colonnes[l.cle])}</span><b>${esc(it.nom)}</b></div></div>`;
  $('#seance').innerHTML = `<div class="app"><div class="progres-seance"><button id="quitter" aria-label="Quitter">${ic('x')}</button>
    <div class="barre"><i style="width:${100 * (seance.n + (fini ? 1 : 0)) / total}%"></i></div>
    ${quiz ? `<span class="pastille eclats chiffre" title="Bonnes réponses">${bonnes()} / ${total}</span>` : `<span class="sous chiffre">${seance.n + 1} / ${total}</span>`}</div>
    <div class="question monte">
      <span class="etiquette" ${quiz ? 'style="color:var(--eclat)"' : ''}>${quiz ? 'Quiz du jour · ' : ''}${esc(l.nom)}</span>
      ${visuel}
      <div class="enonce">${esc(it.enonce)}</div>
      ${fini ? `<div class="saisie-faite ${r.juste ? 'ok' : 'ko'}"><span class="sous">Ta réponse</span><b>${r.tape ? esc(r.tape) : '<i>Je ne sais pas</i>'}</b></div>` : `
      <form class="saisie" id="saisie" autocomplete="off">
        <input id="rep" type="text" enterkeyhint="done" autocapitalize="off" autocomplete="off" spellcheck="false" placeholder="Tape ta réponse" aria-label="Ta réponse">
        <button class="bouton memo" type="submit">Valider</button>
      </form>
      <button class="lien" id="passe" style="justify-self:center">Je ne sais pas</button>`}
      ${fini ? `<div class="retour-fiche ${r.juste ? 'ok' : 'ko'} monte">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
            <span class="verdict">${r.juste ? (r.presque ? 'Juste, à une lettre près' : 'Juste !') : 'Faux'}</span>
            ${r.corrige ? '<span class="badge">corrigé par toi</span>' : ''}</div>
          <div>La réponse : <b style="color:var(--encre)">${esc(it.bonne)}</b></div>
          <dl><dt>${esc(l.colonnes[l.cle])}</dt><dd>${esc(it.nom)}</dd>${autres.map(i => `<dt>${esc(l.colonnes[i])}</dt><dd>${esc(f.valeurs[i])}</dd>`).join('')}</dl>
          <div class="pied-retour"><button class="corriger" id="corriger">${r.juste ? `${ic('x')} Compter comme faux` : `${ic('check')} En fait, j'avais juste`}</button>${lienWiki(l, f)}</div>
        </div>
        <button class="bouton ${quiz ? 'eclat' : 'memo'} large suite-fixe" id="suite">${seance.n + 1 < total ? 'Question suivante' : 'Voir le résultat'} ${ic('caret-right')}</button>` : ''}
    </div></div>`;
  $('#quitter').onclick = fermerSeance;
  if (!fini) {
    const champ = $('#rep');
    setTimeout(() => champ.focus(), 50);
    $('#saisie').onsubmit = e => { e.preventDefault(); repondre(champ.value); };
    $('#passe').onclick = () => repondre('');
  } else {
    $('#corriger').onclick = () => renverser(it, r);
    $('#suite').onclick = suivante;
    setTimeout(() => $('#suite')?.focus(), 50);
  }
}

function repondre(tape) {
  const it = seance.items[seance.n], j = auj();
  const c = corriger(tape, it.bonne, it.estNom);
  const r = {tape: tape.trim(), juste: c.verdict === 'juste', presque: !!c.presque, corrige: false};
  if (seance.mode === 'revision') r.avant = P.noter(etat, P.cleFiche(it.liste.id, it.fiche.id), r.juste, j);
  P.compterReponse(etat, j, r.juste);
  seance.reponses[seance.n] = r;
  enregistrer();
  if (navigator.vibrate) try { navigator.vibrate(r.juste ? 12 : [20, 40, 20]); } catch {}
  rendreQuestion();
}

function renverser(it, r) {
  const j = auj();
  r.juste = !r.juste; r.corrige = !r.corrige; r.presque = false;
  if (seance.mode === 'revision') P.renoter(etat, P.cleFiche(it.liste.id, it.fiche.id), r.avant, r.juste, j);
  P.recompterReponse(etat, j, r.juste);
  enregistrer();
  rendreQuestion();
}

function suivante() {
  seance.n++;
  if (seance.n < seance.items.length) rendreQuestion(); else terminer();
  $('#seance').scrollTo({top: 0});
}

function terminer() {
  const total = seance.items.length, n = bonnes(), quiz = seance.mode === 'quiz', j = auj();
  const corriges = seance.reponses.filter(r => r.corrige).length;
  let gain = 0;
  const bareme = quiz ? E.baremeDuQuiz(etat, etat.quiz) : null;
  if (quiz) {
    gain = E.gainPour(n, bareme);
    E.crediter(etat, `memo-quiz-${P.texteDuJour(j)}`, gain, 'Quiz du jour');
    Object.assign(etat.quiz, {fini: true, score: n, gain});
  }
  enregistrer();
  const s = P.serie(etat, j);
  $('#seance').classList.add('ouverte'); document.body.style.overflow = 'hidden';
  $('#seance').innerHTML = `<div class="app"><div class="fin">
    <span class="etiquette" ${quiz ? 'style="color:var(--eclat)"' : ''}>${quiz ? 'Quiz du jour terminé' : 'Révision terminée'}</span>
    <div class="score chiffre monte">${n}<span style="font-size:32px;color:var(--doux)"> / ${total}</span></div>
    <h2>${n === total ? 'Sans faute !' : n >= total * .7 ? 'Très bien joué' : 'On continue demain'}</h2>
    ${quiz ? `<div class="eclats-gagnes monte" style="animation-delay:.15s">+${gain} ${eclat()}</div>
      ${blocBareme(n, bareme)}
      <p class="sous" style="margin:0">${corriges ? `${pluriel(corriges, 'correction manuelle prise', 'corrections manuelles prises')} en compte.` : ''}</p>`
    : `<p class="sous" style="margin:0">Les révisions ne rapportent pas d'Éclats : c'est le quiz du jour qui en donne.</p>`}
    <div class="bilan monte" style="animation-delay:.25s"><div><b class="chiffre">${n}</b><span>${quiz ? (n > 1 ? 'bonnes réponses' : 'bonne réponse') : (n > 1 ? 'fiches en progrès' : 'fiche en progrès')}</span></div><div><b class="chiffre">${total - n}</b><span>${quiz ? (total - n > 1 ? 'manquées' : 'manquée') : 'à revoir demain'}</span></div><div><b class="chiffre">${s} j</b><span>de série</span></div></div>
    ${quiz ? '' : `<button class="bouton memo large" id="encore">${ic('lightning', 'fill')} Encore une révision</button>`}
    <button class="bouton fantome large" id="finir">Terminer</button></div></div>`;
  const e = $('#encore'); if (e) e.onclick = () => lancerRevision().catch(erreur);
  $('#finir').onclick = fermerSeance;
  $('#finir').focus();
}

/* ---------- Réglages ---------- */
let brouillon = null;            // barème en cours de modification, avant enregistrement
function vueReglages() {
  if (!brouillon) brouillon = E.baremeEnVigueur(etat).map(l => [...l]);
  const valide = E.normaliserBareme(brouillon);
  const qj = etat.quiz?.jour === auj() && !etat.quiz.fini;
  return `<button class="retour" id="retour-accueil">${ic('arrow-left')} Aujourd'hui</button>
    <h1>Réglages</h1>
    <section class="section"><header><h2>Barème du quiz du jour</h2></header>
    <div class="carte pile">
      <p class="sous" style="margin:0">Pour ${E.QUESTIONS_QUIZ} questions. Chaque palier dit combien d'Éclats rapporte le quiz à partir d'un nombre de bonnes réponses ; en dessous du premier palier, il ne rapporte rien.</p>
      <div class="paliers-edition">${brouillon.map(([s, g], i) => `<div class="ligne-palier">
        <label>Dès <input type="number" inputmode="numeric" min="1" max="${E.QUESTIONS_QUIZ}" value="${esc(s)}" data-p="${i}" data-k="0" aria-label="Bonnes réponses du palier ${i + 1}"> bonnes</label>
        <label><input type="number" inputmode="numeric" min="0" max="${E.GAIN_MAX}" value="${esc(g)}" data-p="${i}" data-k="1" aria-label="Éclats du palier ${i + 1}"> ${eclat()}</label>
        <button class="icone-bouton" data-suppr="${i}" aria-label="Retirer ce palier" ${brouillon.length <= 1 ? 'disabled' : ''}>${ic('trash')}</button></div>`).join('')}</div>
      <button class="lien" id="ajout-palier" style="justify-self:start">${ic('plus')} Ajouter un palier</button>
      <span class="etiquette">Aperçu</span>
      ${valide ? blocBareme(undefined, valide) : '<p class="sous" style="margin:0">Il faut au moins un palier entre 1 et 20 bonnes réponses.</p>'}
      ${qj ? `<p class="sous" style="margin:0">Le quiz commencé aujourd'hui garde le barème de son lancement ; le nouveau vaudra dès le prochain.</p>` : ''}
      <div class="actions" style="margin-top:4px"><button class="bouton memo" id="enregistrer-bareme" ${valide ? '' : 'disabled'}>Enregistrer</button><button class="bouton fantome" id="defaut-bareme">${ic('arrow-counter-clockwise')} D'origine</button></div>
    </div></section>`;
}
function brancherReglages() {
  $$('[data-p]').forEach(inp => inp.onchange = () => {
    brouillon[inp.dataset.p][inp.dataset.k] = inp.value;
    if (inp.dataset.k === '0') brouillon.sort((x, y) => Number(x[0]) - Number(y[0]));
    rendre();
  });
  $$('[data-suppr]').forEach(b => b.onclick = () => { brouillon.splice(Number(b.dataset.suppr), 1); rendre(); });
  $('#ajout-palier').onclick = () => {
    // le nouveau palier prend le plus haut seuil encore libre
    const pris = new Set(brouillon.map(l => Number(l[0])));
    let seuil = E.QUESTIONS_QUIZ;
    while (seuil > 0 && pris.has(seuil)) seuil--;
    if (!seuil) return toast('Tous les seuils sont déjà pris');
    const voisin = [...brouillon].filter(l => Number(l[0]) < seuil).pop();
    brouillon.push([seuil, voisin ? Number(voisin[1]) || 0 : 0]);
    brouillon.sort((x, y) => Number(x[0]) - Number(y[0]));
    rendre();
  };
  $('#defaut-bareme').onclick = () => { brouillon = E.BAREME_DEFAUT.map(l => [...l]); rendre(); };
  $('#enregistrer-bareme').onclick = () => {
    const valide = E.normaliserBareme(brouillon);
    if (!valide) return;
    etat.reglages.bareme = valide; enregistrer();
    brouillon = null; toast('Barème enregistré'); rendre();
  };
  $('#retour-accueil').onclick = () => { brouillon = null; aller('aujourdhui'); };
}

/* ---------- messages courts ---------- */
let minuteur;
function toast(texte) {
  const t = $('#toast'); t.textContent = texte; t.hidden = false;
  clearTimeout(minuteur); minuteur = setTimeout(() => { t.hidden = true; }, 2600);
}

/* ---------- rendu ---------- */
function rendre() {
  const vues = {aujourdhui: vueAujourdhui, listes: vueListes, liste: vueListe, progres: vueProgres, reglages: vueReglages};
  $('#racine').innerHTML = `<div class="app">${vues[vue.page]()}</div>`;
  rendreOnglets();
  if (vue.page === 'reglages') brancherReglages();
  $('#reglages')?.addEventListener('click', () => { brouillon = null; aller('reglages'); });
  $('#go')?.addEventListener('click', () => lancerRevision().catch(erreur));
  $('#quiz-jour')?.addEventListener('click', () => lancerQuiz().catch(erreur));
  $$('[data-liste]').forEach(b => b.onclick = () => ouvrirListe(b.dataset.liste));
  $$('[data-fiche]').forEach(b => b.onclick = () => ouvrirFiche(vue.liste, b.dataset.fiche));
  $$('[data-onglet-lien]').forEach(b => b.onclick = () => aller(b.dataset.ongletLien));
  $$('[data-cat]').forEach(b => b.onclick = () => { vue.filtre = b.dataset.cat; rendre(); });
  $$('[data-vue]').forEach(b => b.onclick = () => { vue.affichage = b.dataset.vue; rendre(); });
  $$('[data-reviser]').forEach(b => b.onclick = () => lancerRevision(b.dataset.reviser, b.dataset.mode).catch(erreur));
  $('#retour')?.addEventListener('click', () => aller('listes'));
  const rech = $('#rech');
  if (rech) rech.oninput = () => { vue.recherche = rech.value; const pos = rech.selectionStart; rendre(); const n = $('#rech'); n.focus(); n.setSelectionRange(pos, pos); };
}

function erreur(e) {
  console.error(e);
  toast('Chargement impossible. Vérifie la connexion et réessaie.');
}

$('#voile').onclick = e => { if (e.target.id === 'voile') fermerFiche(); };
document.addEventListener('keydown', e => { if (e.key === 'Escape') { if ($('#voile').classList.contains('ouvert')) fermerFiche(); } });

chargerCatalogue().then(c => {
  C = c;
  actives = new Set(C.listes.flatMap(l => (l.ids || '').split(' ').filter(Boolean).map(id => P.cleFiche(l.id, id))));
  P.noterCatalogue(etat, C.listes.map(l => l.id), auj());
  enregistrer();
  rendre();
}).catch(e => {
  console.error(e);
  $('#racine').innerHTML = `<div class="app"><p class="sous" style="padding-top:40px">Mémo n'a pas pu charger ses listes. Vérifie la connexion puis recharge la page.</p></div>`;
});
