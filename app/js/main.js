// Mnémo : écrans et séances.
//
// Quatre onglets (Aujourd'hui, Listes, Réviser, Progrès), une page par liste,
// une feuille de détail par fiche, une séance plein écran qui sert à la fois
// aux révisions (sans Éclats) et au quiz du jour (20 questions, barème
// réglable), et les Réglages (registre commun, barème, données).
//
// Le catalogue peut gagner ou perdre des listes d'une version à l'autre, et
// l'utilisateur peut modifier les listes sur son appareil (edition.js) : les
// calculs ne retiennent que les fiches visibles.

import * as P from './progression.js';
import * as E from './eclats.js';
import * as ED from './edition.js';
import * as IMG from './images-perso.js';
import {createRegistre} from './registre.js';
import {corriger} from './correction.js';
import {tirerQuestion, deplier, melanger, parAnciennete, tirerQuiz, noterRotation} from './questions.js';
import {chargerCatalogue, chargerListe, chemin} from './donnees.js';
import {$, $$, esc, ic, logo, eclat, sansAccents, pluriel, img, imgNette, toast} from './ui.js';
import {initEdition, formulaireFiche, vueNouvelleListe, brancherNouvelleListe, formulaireListe} from './ecrans-edition.js';

/* ---------- état ---------- */
let etat = P.charger(localStorage);
const enregistrer = () => P.sauver(localStorage, etat);
let ed = ED.chargerEdition(localStorage);
function sauverEd() {
  try { ED.sauverEdition(localStorage, ed); return true; }
  catch { toast('Stockage plein : non enregistré', 4000); return false; }
}
const registre = createRegistre();
let soldeCommun = null;                         // dernier solde lu dans le registre
const auj = () => P.jourDe();

let catalogueOfficiel = null;                   // tel que publié
let C = null;                                   // catalogue vu par l'utilisateur (officiel + ses listes)
let actives = new Set();                        // clés « liste/fiche » visibles
const garde = cle => actives.has(cle);
const chargees = new Map();                     // listes prêtes à l'affichage, changements appliqués

async function liste(id) {
  if (!chargees.has(id)) {
    const perso = ED.listePerso(ed, id);
    chargees.set(id, perso || ED.appliquer(await chargerListe(id), ed));
  }
  return chargees.get(id);
}

/** Recalcule le catalogue vu par l'utilisateur après un changement de ses listes. */
function recomposer() {
  const listes = catalogueOfficiel.listes.map(l => {
    const ids = ED.idsVisibles(l, ed);
    return {...l, fiches: ids.length, idsVisibles: ids};
  });
  for (const l of ed.perso) listes.push({...ED.resumePerso(l), idsVisibles: l.fiches.map(f => f.id)});
  C = {...catalogueOfficiel, listes, parId: new Map(listes.map(l => [l.id, l]))};
  actives = new Set(listes.flatMap(l => l.idsVisibles.map(id => P.cleFiche(l.id, id))));
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
  const dans = id => vue.page === id || (id === 'listes' && ['liste', 'nouvelle'].includes(vue.page));
  $('#onglets nav').innerHTML = ONGLETS.map(([id, lib, n]) => id === 'reviser'
    ? `<button class="principal" data-onglet="${id}"><span class="rond">${ic(n, 'fill')}</span>${lib}</button>`
    : `<button data-onglet="${id}" ${dans(id) ? 'aria-current="page"' : ''}>${ic(n, dans(id) ? 'fill' : 'regular')}${lib}</button>`).join('');
  $$('[data-onglet]').forEach(b => b.onclick = () => {
    if (b.dataset.onglet === 'reviser') return lancerRevision().catch(erreur);
    aller(b.dataset.onglet);
  });
}
function aller(page) { vue.page = page; rendre(); window.scrollTo({top: 0}); }

function haut(titre) {
  const s = P.serie(etat, auj()), attente = E.montantACollecter(etat);
  return `<header class="haut"><div class="tuile">${logo()}</div><div class="marque">${titre}</div>
    <span class="pastille serie" title="Série : jours d'affilée à ${P.OBJECTIF_JOUR} réponses">${ic('fire', 'fill')}<span class="chiffre">${s}</span></span>
    <button class="pastille eclats ${attente ? 'a-verser' : ''}" data-aller="reglages" title="${attente ? `${attente} Éclats à verser dans le registre commun` : 'Éclats gagnés au quiz du jour'}">${eclat()}<span class="chiffre">${E.solde(etat).toLocaleString('fr-FR')}</span></button>
    <button class="pastille rond-reglages" data-aller="reglages" aria-label="Réglages" title="Réglages">${ic('gear')}</button></header>`;
}

function blocBareme(score, bareme) {
  return `<div class="bareme">${E.paliers(bareme).map(p => {
    const atteint = score !== undefined && score >= p.seuil && score <= p.fin;
    return `<div class="palier ${atteint ? 'atteint' : ''}"><b>${p.gain ? `${p.gain} ${eclat()}` : '0'}</b><span>${p.libelle}</span></div>`;
  }).join('')}</div>`;
}

// Le gain d'un quiz, versé ou non dans le registre
function blocVersement(cle) {
  const e = etat.eclats.journal.find(x => x.cle === cle);
  if (!e) return '';
  if (e.collecte) return `<p class="sous verse">${ic('check')} Versé</p>`;
  return registre.estConnecte()
    ? `<button class="bouton fantome large" data-verser="${esc(cle)}">${ic('cloud-arrow-up')} Verser ${e.montant} ${eclat()}</button>`
    : `<button class="bouton fantome large" data-aller="reglages">${ic('cloud-arrow-up')} Verser ${e.montant} ${eclat()}</button>`;
}
const cleQuiz = j => `memo-quiz-${P.texteDuJour(j)}`;

async function verser(cle) {
  try {
    await E.collecter(etat, registre, cle);
    enregistrer();
    toast('Versé');
    soldeCommun = null;
  } catch (e) {
    toast(e.status === 401 ? 'Session expirée' : `Échec : ${e.message}`, 4000);
  }
  if (seance?.fini) terminer(); else rendre();
}

/* ---------- Aujourd'hui ---------- */
function vueAujourdhui() {
  const j = auj(), dues = P.fichesDues(etat, j, garde).length, neuves = Math.min(nouvellesDisponibles(), 5);
  const faits = P.reponsesDuJour(etat, j), objectif = Math.min(100, Math.round(100 * faits / P.OBJECTIF_JOUR));
  const qj = etat.quiz?.jour === j ? etat.quiz : null;
  const n = E.QUESTIONS_QUIZ, bareme = qj ? E.baremeDuQuiz(etat, qj) : E.baremeEnVigueur(etat);
  const quiz = qj?.fini
    ? `<h1><span class="chiffre">${qj.score} / ${n}</span> · +${qj.gain} ${eclat()}</h1>${blocBareme(qj.score, bareme)}${blocVersement(cleQuiz(j))}`
    : qj
      ? `<h1><span class="chiffre">${qj.reponses.length} / ${n}</span></h1>${blocBareme(undefined, bareme)}
         <button class="bouton eclat large" id="quiz-jour">${ic('play', 'fill')} Reprendre</button>`
      : `<h1>${n} questions</h1>${blocBareme(undefined, bareme)}
         <button class="bouton eclat large" id="quiz-jour">${ic('trophy', 'fill')} Jouer</button>`;

  let heros;
  if (!suivies().length && !dues) {
    heros = `<h1>Choisis une liste</h1>
      <button class="bouton plein large" data-aller="listes">${ic('books', 'fill')} Listes</button>`;
  } else if (!dues && !neuves) {
    heros = `<h1>Tout est à jour</h1>
      <button class="bouton plein large" data-aller="listes">${ic('books', 'fill')} Listes</button>`;
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
  const pasSuivies = C.listes.filter(l => !etat.suivies.includes(l.id) && l.fiches).map(l => l.id);
  const aDecouvrir = [...pasSuivies.filter(estNouvelle), ...ordreDuJour(pasSuivies.filter(id => !estNouvelle(id)))].slice(0, 8).map(infoListe);

  const installable = window.__installation && !matchMedia('(display-mode: standalone)').matches;
  return haut('Mnémo') + `
  ${installable ? `<button class="bouton fantome large installer" id="installer">${ic('download-simple')} Installer l'application</button>` : ''}
  <section class="quiz-jour monte">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
      <span class="etiquette" style="color:var(--eclat)">Quiz du jour</span>
      ${qj?.fini ? '<span class="sous">Demain</span>' : ''}</div>
    ${quiz}
  </section>

  <section class="heros section">
    <div class="anneau"></div>
    <span class="etiquette" style="color:#8FA0B6">Révision du jour</span>
    ${heros}
  </section>

  <section class="section"><div class="carte objectif">
    <div class="jauge" style="--p:${objectif}"><span class="chiffre">${objectif}%</span></div>
    <div><h3>Objectif du jour</h3><div class="sous">${faits} / ${P.OBJECTIF_JOUR} réponses</div></div>
  </div></section>

  ${derniere ? `<section class="section"><header><h2>Continuer</h2></header>
    <button class="carte continuer" data-liste="${esc(derniere.id)}">
      ${img(derniere.apercu[0])}
      <div style="text-align:left"><h3>${esc(derniere.nom)}</h3><div class="barre" style="margin:7px 0 4px"><i style="width:${maitriseListe(derniere.id)}%"></i></div><div class="sous">${maitriseListe(derniere.id)} % maîtrisé · ${derniere.fiches} fiches</div></div>
      ${ic('caret-right')}
    </button></section>` : ''}

  ${aDecouvrir.length ? `<section class="section"><header><h2>À découvrir</h2><button class="lien" data-aller="listes">Tout voir</button></header>
    <div class="defiler">${aDecouvrir.map(l => `<button class="decouverte" data-liste="${esc(l.id)}">${img(l.apercu[0])}<div>${estNouvelle(l.id) ? '<span class="badge eclat">Nouvelle</span>' : ''}${esc(l.nom)}<small>${l.fiches} fiches</small></div></button>`).join('')}</div>
  </section>` : ''}`;
}

/* ---------- Listes ---------- */
function vueListes() {
  const dues = duesParListe();
  const cats = C.categories.filter(c => C.listes.some(l => l.categorie === c.id));
  const q = sansAccents(vue.recherche.trim());
  const retenue = l => (vue.filtre === 'tout' || l.categorie === vue.filtre) && (!q || sansAccents(l.nom).includes(q));
  const blocs = cats.map(c => {
    const ls = C.listes.filter(l => l.categorie === c.id && retenue(l)).sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
    if (!ls.length) return '';
    return `<div class="titre-cat"><span style="font-size:20px">${c.icone}</span><h2>${esc(c.nom)}</h2><span class="pct">${pluriel(ls.length, 'liste')}</span></div>
      <div class="carte" style="padding:4px 14px">${ls.map(l => {
        const m = maitriseListe(l.id), d = dues.get(l.id) || 0, suivie = etat.suivies.includes(l.id);
        return `<button class="ligne-liste" data-liste="${esc(l.id)}"><span class="ic-liste">${esc(l.icone)}</span>
          <span><span class="nom">${esc(l.nom)}</span><span class="meta">${suivie ? `<span class="barre"><i style="width:${m}%"></i></span><span class="sous chiffre">${m} %</span>` : `<span class="sous">${pluriel(l.fiches, 'fiche')}</span>`}</span></span>
          ${d ? `<span class="badge">${d} à revoir</span>` : estNouvelle(l.id) ? '<span class="badge eclat">Nouvelle</span>' : ic('caret-right')}</button>`;
      }).join('')}</div>`;
  }).join('');
  return haut('Listes') + `
    <div class="pile"><div class="barre-recherche"><label class="recherche">${ic('magnifying-glass')}<input id="rech" type="search" placeholder="Chercher parmi ${C.listes.length} listes" value="${esc(vue.recherche)}" aria-label="Chercher une liste"></label>
      <button class="bouton memo carre" data-aller="nouvelle" aria-label="Créer une liste" title="Créer une liste">${ic('plus')}</button></div>
    <div class="puces" role="group" aria-label="Catégories">${[['tout', 'Tout']].concat(cats.map(c => [c.id, c.icone + ' ' + c.nom])).map(([id, lib]) => `<button class="puce" data-cat="${id}" aria-pressed="${vue.filtre === id}">${esc(lib)}</button>`).join('')}</div></div>
    ${blocs || '<p class="sous" style="margin-top:24px">Aucune liste ne correspond.</p>'}`;
}

/* ---------- Page d'une liste ---------- */
function niveaux(b) {
  return `<div class="niveaux" aria-label="${P.LIBELLES[b]}">${[1, 2, 3, 4, 5].map(n => `<i class="${b >= n ? 'on' : ''}"></i>`).join('')}</div>`;
}
function vueListe() {
  const l = chargees.get(vue.liste);
  const retour = `<button class="retour" id="retour">${ic('arrow-left')} Listes</button>`;
  if (!l) return retour + `<p class="sous" style="margin-top:20px">Chargement de la liste…</p>`;
  const m = maitriseListe(l.id), dues = duesParListe().get(l.id) || 0;
  const vues = vuesParListe().get(l.id) || 0, neuves = l.fiches.length - vues;
  const cle = f => P.cleFiche(l.id, f.id);
  const autres = l.colonnes.map((c, i) => i).filter(i => i !== l.cle);
  const perso = ED.estPerso(ed, l.id), masquees = (ed.retraits[l.id] || []).length;
  return `${retour}
    <div class="entete-liste"><div><span class="etiquette">${perso ? 'Ma liste · ' : ''}${esc(nomCategorie(l.categorie).nom)}</span><h1>${esc(l.icone)} ${esc(l.nom)}</h1>
      <div class="sous" style="margin-top:4px">${pluriel(l.fiches.length, 'fiche')} · ${esc(l.colonnes.join(' · '))}</div></div>
      <div class="jauge" style="--p:${m}"><span class="chiffre">${m}%</span></div></div>
    <div class="actions">
      <button class="bouton memo" data-reviser="${esc(l.id)}" ${l.fiches.length ? '' : 'disabled'}>${ic('lightning', 'fill')} ${dues ? `Réviser (${dues})` : 'Réviser'}</button>
      <button class="bouton fantome" data-reviser="${esc(l.id)}" data-mode="decouvrir" ${neuves > 0 ? '' : 'disabled'}>${ic('sparkle')} ${neuves > 0 ? 'Découvrir' : 'Tout vu'}</button></div>
    <div class="outils-liste">
      <button class="lien" id="ajout-fiche">${ic('plus')} Fiche</button>
      ${perso ? `<button class="lien" id="modif-liste">${ic('pencil-simple')} Liste</button>` : ''}
      ${masquees ? `<button class="lien" id="restaurer">${ic('eye')} ${pluriel(masquees, 'masquée', 'masquées')}</button>` : ''}
    </div>
    ${l.fiches.length ? `<div class="segment" role="group" aria-label="Affichage"><button data-vue="fiches" aria-pressed="${vue.affichage === 'fiches'}">Fiches</button><button data-vue="tableau" aria-pressed="${vue.affichage === 'tableau'}">Tableau</button></div>` : ''}
    ${!l.fiches.length ? '' : vue.affichage === 'fiches'
      ? `<div class="grille">${l.fiches.map(f => `<button class="fiche" data-fiche="${esc(f.id)}">${f.image ? imgNette(f, '', '(max-width: 460px) 46vw, 210px', 'loading="lazy"') : (l.fiches.some(x => x.image) ? '<span class="sans-image"></span>' : '')}<div class="corps"><div class="nom">${esc(f.valeurs[l.cle])}${f.modifiee || f.ajoutee ? ` <span class="marque-perso" title="${f.ajoutee ? 'Ajoutée par toi' : 'Modifiée par toi'}">${ic('pencil-simple')}</span>` : ''}</div><div class="sec">${esc(f.valeurs[autres[0]] || '')}</div>${niveaux(P.boite(etat, cle(f)))}</div></button>`).join('')}</div>`
      : `<div class="tableau"><table><thead><tr><th>${esc(l.colonnes[l.cle])}</th>${autres.map(i => `<th>${esc(l.colonnes[i])}</th>`).join('')}</tr></thead><tbody>${l.fiches.map(f => `<tr data-fiche="${esc(f.id)}"><td>${esc(f.valeurs[l.cle])}</td>${autres.map(i => `<td>${esc(f.valeurs[i])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}`;
}
async function ouvrirListe(id) {
  vue.page = 'liste'; vue.liste = id; vue.affichage = 'fiches';
  rendre(); window.scrollTo({top: 0});
  try { await liste(id); } catch { toast('Liste introuvable'); return aller('listes'); }
  if (vue.page === 'liste' && vue.liste === id) rendre();
}

function ouvrirFeuille(html) {
  $('#feuille').innerHTML = html;
  $('#feuille').scrollTop = 0;
  $('#voile').classList.add('ouvert');
}
function fermerFiche() { $('#voile').classList.remove('ouvert'); }

function ouvrirFiche(idListe, idFiche) {
  const l = chargees.get(idListe), f = l?.fiches.find(x => x.id === idFiche);
  if (!f) return;
  const b = P.boite(etat, P.cleFiche(idListe, idFiche));
  const autres = l.colonnes.map((c, i) => i).filter(i => i !== l.cle && f.valeurs[i]);
  ouvrirFeuille(`<div class="poignee"></div>${f.image ? img(f.grande || f.image, f.valeurs[l.cle]) : ''}<div class="contenu">
    <div><span class="etiquette">${esc(l.nom)}</span><h1 style="margin-top:4px">${esc(f.valeurs[l.cle])}</h1></div>
    ${f.carte ? `<div class="carte-loc">${img(f.carteGrande || f.carte, 'Localisation')}</div>` : ''}
    <dl>${autres.map(i => `<div><dt>${esc(l.colonnes[i])}</dt><dd>${esc(f.valeurs[i])}</dd></div>`).join('')}</dl>
    <div class="pied-retour">${lienWiki(l, f)}<button class="lien" id="modifier-fiche">${ic('pencil-simple')} Modifier</button></div>
    <div class="carte" style="box-shadow:none;background:var(--surface-2);display:flex;gap:12px;align-items:center">${niveaux(b).replace('class="niveaux"', 'class="niveaux" style="flex:1;margin:0"')}<span class="sous">${b ? `${P.LIBELLES[b]} · niveau ${b} sur 5` : 'Jamais révisée'}</span></div>
    <button class="bouton fantome large" id="fermer">Fermer</button></div>`);
  $('#fermer').onclick = fermerFiche;
  $('#modifier-fiche').onclick = () => formulaireFiche(idListe, idFiche).catch(erreur);
}

/** Après une modification : catalogue recalculé, liste relue, écran à jour. */
async function apresEdition(idListe, message, ouvrir = false) {
  recomposer();
  if (idListe) chargees.delete(idListe);
  fermerFiche();
  if (message) toast(message);
  if (!idListe || !C.parId.has(idListe)) { if (vue.page === 'liste') aller('listes'); else rendre(); return; }
  if (ouvrir) return ouvrirListe(idListe);
  await liste(idListe);
  rendre();
}

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
      ${deCote ? `<p class="sous" style="margin:10px 0 0">+ ${pluriel(deCote, 'fiche retirée', 'fiches retirées')}</p>` : ''}</div></section>
    <section class="section"><header><h2>12 dernières semaines</h2></header><div class="carte"><div class="calendrier">${jours.map(n => `<i data-n="${n}"></i>`).join('')}</div></div></section>
    ${cats.length ? `<section class="section"><header><h2>Par catégorie</h2></header><div class="carte cat-maitrise">${cats.map(([i, n, p]) => `<div><span style="font-size:20px">${i}</span><span><b>${esc(n)}</b><span class="barre" style="display:block;margin-top:5px"><i style="width:${p}%"></i></span></span><span class="pct chiffre">${p}%</span></div>`).join('')}</div></section>` : ''}`;
}

/* ---------- Séances ---------- */
let seance = null;   // {mode, items: [question dépliée], reponses: [], n, fini}

// Rend une question dépliée par question reçue, ou null si sa liste ou sa
// fiche a disparu depuis
async function preparer(questions) {
  await Promise.allSettled([...new Set(questions.map(q => q.l))].filter(id => C.parId.has(id)).map(liste));
  return questions.map(q => chargees.has(q.l) ? deplier(q, chargees.get(q.l)) : null);
}

// Une question de secours pour le quiz, prise dans les listes officielles,
// sauf parmi les fiches déjà posées
async function questionDeSecours(prises) {
  for (const id of melanger(C.listes.filter(l => l.fiches && !l.perso).map(l => l.id))) {
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
      const l = await liste(id).catch(() => null);
      if (!l) continue;
      for (const f of l.fiches) {
        const c = P.cleFiche(id, f.id);
        if (!etat.fiches[c]) { neuves.push(c); if (neuves.length >= 5) break; }
      }
    }
    cles = [...dues, ...neuves];
    if (!cles.length) { toast(suivies().length ? 'Rien à revoir' : 'Choisis une liste'); return aller('listes'); }
  }
  enregistrer();
  const questions = [];
  for (const c of melanger(cles)) {
    const [l, f] = c.split('/');
    const lst = await liste(l).catch(() => null), fiche = lst?.fiches.find(x => x.id === f);
    const q = fiche && tirerQuestion(lst, fiche);
    if (q) questions.push(q);
  }
  if (!questions.length) return toast('Aucune question possible');
  seance = {mode: 'revision', items: (await preparer(questions)).filter(Boolean), reponses: [], n: 0};
  ouvrirSeance();
}

async function lancerQuiz() {
  const j = auj();
  if (!(etat.quiz?.jour === j)) {
    // les listes officielles les moins récemment posées d'abord (voir tirerQuiz) ;
    // les listes personnelles restent hors du quiz, qui doit valoir pour tous
    const ordre = parAnciennete(C.listes.filter(l => l.fiches && !l.perso).map(l => l.id), etat.rotation.listes);
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
  // toutes les grandes images de la séance se chargent d'avance : elles restent
  // ainsi disponibles si la connexion tombe en route
  for (const it of seance.items.slice(seance.n)) if (it?.fiche.grande) new Image().src = chemin(it.fiche.grande);
  rendreQuestion();
}
function fermerSeance() {
  $('#seance').classList.remove('ouverte'); document.body.style.overflow = ''; seance = null;
  rendre();
  verifierVersion();
}
const bonnes = () => seance.reponses.filter(r => r.juste).length;

function rendreQuestion() {
  const it = seance.items[seance.n], r = seance.reponses[seance.n], fini = !!r, quiz = seance.mode === 'quiz';
  const total = seance.items.length, {liste: l, fiche: f} = it;
  const autres = l.colonnes.map((c, i) => i).filter(i => i !== l.cle && f.valeurs[i]);
  const visuel = it.q.t === 'image'
    ? `<div class="visuel">${img(f.grande || f.image, 'Image à reconnaître')}</div>`
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
  let gain = 0;
  const bareme = quiz ? E.baremeDuQuiz(etat, etat.quiz) : null;
  if (quiz) {
    gain = etat.quiz.fini ? etat.quiz.gain : E.gainPour(n, bareme);
    if (!etat.quiz.fini) {
      E.crediter(etat, cleQuiz(j), gain, 'Quiz du jour', {jour: P.texteDuJour(j), score: n, bareme});
      Object.assign(etat.quiz, {fini: true, score: n, gain});
    }
  }
  seance.fini = true;
  enregistrer();
  const s = P.serie(etat, j);
  $('#seance').classList.add('ouverte'); document.body.style.overflow = 'hidden';
  $('#seance').innerHTML = `<div class="app"><div class="fin">
    <span class="etiquette" ${quiz ? 'style="color:var(--eclat)"' : ''}>${quiz ? 'Quiz du jour terminé' : 'Révision terminée'}</span>
    <div class="score chiffre monte">${n}<span style="font-size:32px;color:var(--doux)"> / ${total}</span></div>
    <h2>${n === total ? 'Sans faute !' : n >= total * .7 ? 'Très bien joué' : 'On continue demain'}</h2>
    ${quiz ? `<div class="eclats-gagnes monte" style="animation-delay:.15s">+${gain} ${eclat()}</div>
      ${blocBareme(n, bareme)}
      ${gain ? blocVersement(cleQuiz(j)) : ''}`
    : ''}
    <div class="bilan monte" style="animation-delay:.25s"><div><b class="chiffre">${n}</b><span>${quiz ? (n > 1 ? 'bonnes réponses' : 'bonne réponse') : (n > 1 ? 'fiches en progrès' : 'fiche en progrès')}</span></div><div><b class="chiffre">${total - n}</b><span>${quiz ? (total - n > 1 ? 'manquées' : 'manquée') : 'à revoir demain'}</span></div><div><b class="chiffre">${s} j</b><span>de série</span></div></div>
    ${quiz ? '' : `<button class="bouton memo large" id="encore">${ic('lightning', 'fill')} Encore</button>`}
    <button class="bouton fantome large" id="finir">Fermer</button></div></div>`;
  $('#encore')?.addEventListener('click', () => lancerRevision().catch(erreur));
  $('#seance [data-verser]')?.addEventListener('click', e => verser(e.currentTarget.dataset.verser));
  $('#seance [data-aller]')?.addEventListener('click', () => { fermerSeance(); aller('reglages'); });
  $('#finir').onclick = fermerSeance;
  $('#finir').focus();
}

/* ---------- Réglages ---------- */
let brouillon = null;            // barème en cours de modification, avant enregistrement
function vueReglages() {
  if (!brouillon) brouillon = E.baremeEnVigueur(etat).map(l => [...l]);
  const valide = E.normaliserBareme(brouillon);
  const montant = E.montantACollecter(etat);
  const connecte = registre.estConnecte();
  const anciennes = ED.listesAnciennes(localStorage).filter(a => !ed.perso.some(l => l.ancienneId === a.id));
  return `<button class="retour" id="retour-accueil">${ic('arrow-left')} Aujourd'hui</button>
    <h1>Réglages</h1>

    <section class="section"><header><h2>Registre des Éclats</h2></header>
    <div class="carte pile">
      ${connecte ? `
        <div class="ligne-info"><span class="sous">${esc(registre.utilisateur()?.email || '')}</span><b class="chiffre" id="solde-commun">${soldeCommun === null ? '…' : `${soldeCommun.toLocaleString('fr-FR')} ${eclat()}`}</b></div>
        ${montant ? `<button class="bouton memo large" id="tout-verser">${ic('cloud-arrow-up')} Verser ${montant} ${eclat()}</button>` : ''}
        <button class="lien" id="deconnexion" style="justify-self:start">${ic('sign-out')} Se déconnecter</button>`
      : `
        ${montant ? `<div class="ligne-info"><span class="sous">À verser</span><b class="chiffre">${montant} ${eclat()}</b></div>` : ''}
        <form class="pile formulaire" id="connexion" novalidate>
          <label class="champ"><span>Adresse e-mail</span><input type="email" id="cx-email" autocomplete="username" required></label>
          <label class="champ"><span>Mot de passe</span><input type="password" id="cx-mdp" autocomplete="current-password" required></label>
          <button class="bouton memo large" type="submit">${ic('sign-in')} Se connecter</button>
        </form>`}
    </div></section>

    <section class="section"><header><h2>Barème du quiz</h2></header>
    <div class="carte pile">
      <div class="paliers-edition">${brouillon.map(([s, g], i) => `<div class="ligne-palier">
        <label>Dès <input type="number" inputmode="numeric" min="1" max="${E.QUESTIONS_QUIZ}" value="${esc(s)}" data-p="${i}" data-k="0" aria-label="Bonnes réponses du palier ${i + 1}"> bonnes</label>
        <label><input type="number" inputmode="numeric" min="0" max="${E.GAIN_MAX}" value="${esc(g)}" data-p="${i}" data-k="1" aria-label="Éclats du palier ${i + 1}"> ${eclat()}</label>
        <button class="icone-bouton" data-suppr="${i}" aria-label="Retirer ce palier" ${brouillon.length <= 1 ? 'disabled' : ''}>${ic('trash')}</button></div>`).join('')}</div>
      <button class="lien" id="ajout-palier" style="justify-self:start">${ic('plus')} Ajouter un palier</button>
      ${valide ? blocBareme(undefined, valide) : ''}
      <div class="actions" style="margin-top:4px"><button class="bouton memo" id="enregistrer-bareme" ${valide ? '' : 'disabled'}>Enregistrer</button><button class="bouton fantome" id="defaut-bareme">${ic('arrow-counter-clockwise')} D'origine</button></div>
    </div></section>

    <section class="section"><header><h2>Mes données</h2></header>
    <div class="carte pile">
      ${anciennes.length ? `<button class="bouton fantome large" id="reprendre">${ic('download-simple')} Importer ${pluriel(anciennes.length, 'liste', 'listes')} de l'ancienne version</button>` : ''}
      <div class="actions"><button class="bouton fantome" id="exporter">${ic('download-simple')} Sauvegarder</button>
        <label class="bouton fantome">${ic('upload-simple')} Restaurer<input type="file" accept="application/json,.json" id="importer" hidden></label></div>
    </div></section>

    <section class="section"><header><h2>Liens</h2></header>
    <div class="carte pile">
      <a class="lien" href="../atelier.html">${ic('image-square')} Atelier des images</a>
      <a class="lien" href="../memo.html?ancienne">${ic('arrow-square-out')} Ancienne version</a>
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

  // registre commun
  $('#connexion')?.addEventListener('submit', async e => {
    e.preventDefault();
    const bouton = e.target.querySelector('button'); bouton.disabled = true;
    try {
      await registre.connexion($('#cx-email').value.trim(), $('#cx-mdp').value);
      soldeCommun = null; toast('Connecté'); rendre();
    } catch (err) { bouton.disabled = false; toast(err.message, 4000); }
  });
  $('#deconnexion')?.addEventListener('click', () => { registre.deconnexion(); soldeCommun = null; rendre(); });
  $('#tout-verser')?.addEventListener('click', async e => {
    e.currentTarget.disabled = true;
    const r = await E.toutCollecter(etat, registre);
    enregistrer(); soldeCommun = null;
    toast(r.erreur ? `Échec : ${r.erreur.message}` : `${r.montant} versés`, 4000);
    rendre();
  });
  if (registre.estConnecte() && soldeCommun === null) {
    registre.solde().then(v => {
      soldeCommun = v;
      const el = $('#solde-commun'); if (el) el.innerHTML = `${v.toLocaleString('fr-FR')} ${eclat()}`;
    }).catch(() => {
      // session refusée : le client l'a effacée, on revient au formulaire de connexion
      if (!registre.estConnecte()) { toast('Session expirée'); return rendre(); }
      const el = $('#solde-commun'); if (el) el.textContent = 'indisponible';
    });
  }

  // données
  $('#reprendre')?.addEventListener('click', reprendreAnciennes);
  $('#exporter').onclick = () => exporter().catch(erreur);
  $('#importer').onchange = e => { const f = e.target.files?.[0]; if (f) importer(f).catch(err => toast(`Échec : ${err.message}`, 4000)); };
}

async function reprendreAnciennes() {
  let n = 0;
  for (const a of ED.listesAnciennes(localStorage)) {
    const l = ED.reprendreAncienne(ed, a);
    if (!l) continue;
    n++;
    // les photos « data: » de l'ancienne version passent dans la base des photos
    for (const f of l.fiches) if (String(f.image).startsWith('data:')) {
      try { f.image = await IMG.importerDataUrl(f.image); } catch { delete f.image; }
    }
  }
  if (sauverEd()) { recomposer(); toast(n ? pluriel(n, 'liste importée', 'listes importées') : 'Rien à importer'); rendre(); }
}

async function exporter() {
  const images = {};
  for (const cle of ED.imagesUtilisees(ed)) {
    const blob = await IMG.lire(cle);
    if (blob) images[cle] = await new Promise(ok => { const r = new FileReader(); r.onload = () => ok(r.result); r.readAsDataURL(blob); });
  }
  const sauvegarde = {format: 'memo2-sauvegarde', v: 1, date: new Date().toISOString(), etat, edition: ed, images};
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(sauvegarde)], {type: 'application/json'}));
  a.download = `memo-sauvegarde-${P.texteDuJour(auj())}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  toast('Sauvegardé');
}

async function importer(fichier) {
  const s = JSON.parse(await fichier.text());
  if (s?.format !== 'memo2-sauvegarde' || !s.etat || !s.edition) throw new Error('fichier non reconnu');
  if (!confirm(`Restaurer la sauvegarde du ${new Date(s.date).toLocaleDateString('fr-FR')} ?`)) return;
  for (const [cle, url] of Object.entries(s.images || {})) {
    const blob = await (await fetch(url)).blob();
    await new Promise((ok, ko) => { const r = indexedDB.open('memo2-images', 1); r.onupgradeneeded = () => r.result.createObjectStore('images'); r.onsuccess = () => { const tx = r.result.transaction('images', 'readwrite'); tx.objectStore('images').put(blob, cle); tx.oncomplete = ok; tx.onerror = () => ko(tx.error); }; r.onerror = () => ko(r.error); });
  }
  localStorage.setItem(P.CLE_STOCKAGE, JSON.stringify(s.etat));
  localStorage.setItem(ED.CLE_EDITION, JSON.stringify(s.edition));
  location.reload();
}

/* ---------- rendu ---------- */
function rendre() {
  const vues = {aujourdhui: vueAujourdhui, listes: vueListes, liste: vueListe, progres: vueProgres, reglages: vueReglages, nouvelle: vueNouvelleListe};
  $('#racine').innerHTML = `<div class="app">${vues[vue.page]()}</div>`;
  rendreOnglets();
  if (vue.page === 'reglages') brancherReglages();
  if (vue.page === 'nouvelle') brancherNouvelleListe();
  $$('#racine [data-aller]').forEach(b => b.onclick = () => { if (b.dataset.aller === 'reglages') brouillon = null; aller(b.dataset.aller); });
  $$('#racine [data-verser]').forEach(b => b.onclick = () => verser(b.dataset.verser));
  $('#installer')?.addEventListener('click', async () => {
    const e = window.__installation;
    if (!e) return;
    e.prompt();
    const choix = await e.userChoice.catch(() => null);
    if (choix?.outcome === 'accepted') { window.__installation = null; rendre(); }
  });
  $('#go')?.addEventListener('click', () => lancerRevision().catch(erreur));
  $('#quiz-jour')?.addEventListener('click', () => lancerQuiz().catch(erreur));
  $$('[data-liste]').forEach(b => b.onclick = () => ouvrirListe(b.dataset.liste));
  $$('[data-fiche]').forEach(b => b.onclick = () => ouvrirFiche(vue.liste, b.dataset.fiche));
  $$('[data-cat]').forEach(b => b.onclick = () => { vue.filtre = b.dataset.cat; rendre(); });
  $$('[data-vue]').forEach(b => b.onclick = () => { vue.affichage = b.dataset.vue; rendre(); });
  $$('[data-reviser]').forEach(b => b.onclick = () => lancerRevision(b.dataset.reviser, b.dataset.mode).catch(erreur));
  $('#retour')?.addEventListener('click', () => aller('listes'));
  $('#ajout-fiche')?.addEventListener('click', () => formulaireFiche(vue.liste).catch(erreur));
  $('#modif-liste')?.addEventListener('click', () => formulaireListe(vue.liste));
  $('#restaurer')?.addEventListener('click', () => {
    const n = ED.restaurerFichesRetirees(ed, vue.liste);
    if (sauverEd()) apresEdition(vue.liste, null);
  });
  brancherDefilement();
  const rech = $('#rech');
  if (rech) rech.oninput = () => { vue.recherche = rech.value; const pos = rech.selectionStart; rendre(); const n = $('#rech'); n.focus(); n.setSelectionRange(pos, pos); };
}

// Bandeaux horizontaux : au doigt ils défilent seuls ; à la souris, la molette
// et le glisser les font défiler aussi
function brancherDefilement() {
  $$('.defiler').forEach(d => {
    d.addEventListener('wheel', e => {
      if (Math.abs(e.deltaY) <= Math.abs(e.deltaX) || d.scrollWidth <= d.clientWidth) return;
      e.preventDefault();
      d.scrollBy({left: e.deltaY});
    }, {passive: false});
    let depart = null, glisse = false;
    d.addEventListener('pointerdown', e => { if (e.pointerType === 'mouse') { depart = {x: e.clientX, s: d.scrollLeft}; glisse = false; } });
    d.addEventListener('pointermove', e => {
      if (!depart) return;
      const dx = e.clientX - depart.x;
      if (Math.abs(dx) > 5) { glisse = true; d.scrollLeft = depart.s - dx; }
    });
    const fin = () => { depart = null; };
    d.addEventListener('pointerup', fin); d.addEventListener('pointerleave', fin);
    // un glisser ne doit pas ouvrir la liste sous le pointeur
    d.addEventListener('click', e => { if (glisse) { e.stopPropagation(); e.preventDefault(); glisse = false; } }, true);
  });
}

function erreur(e) {
  console.error(e);
  toast(navigator.onLine === false ? 'Hors ligne' : 'Chargement impossible', 3000);
}

/* ---------- mises à jour et hors ligne ---------- */
// Une application installée n'est pas rechargée quand on la rouvre : elle
// relit version.json (écrit au déploiement) en revenant au premier plan, et se
// recharge d'elle-même si rien n'est en cours.
let versionVue = null;
async function verifierVersion() {
  let v = null;
  try { const r = await fetch(chemin('version.json'), {cache: 'no-store'}); if (r.ok) v = (await r.json()).version; } catch {}
  if (!v) return;
  if (!versionVue) { versionVue = v; return; }
  if (v === versionVue) return;
  const occupe = seance || $('#voile').classList.contains('ouvert') || ['nouvelle', 'reglages'].includes(vue.page);
  if (!occupe) return location.reload();
  const b = $('#mise-a-jour');
  b.hidden = false;
  b.onclick = () => location.reload();
}
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') verifierVersion(); });
window.addEventListener('focus', verifierVersion);

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register(new URL('../sw.js', document.baseURI).href, {scope: new URL('../', document.baseURI).href, updateViaCache: 'none'}).catch(() => {});
}

/* ---------- démarrage ---------- */
// une image pas encore gardée sur l'appareil, hors ligne : un fond neutre
// plutôt que l'icône d'image cassée
document.addEventListener('error', e => { if (e.target.tagName === 'IMG') e.target.classList.add('absente'); }, true);
document.addEventListener('load', e => { if (e.target.tagName === 'IMG') e.target.classList.remove('absente'); }, true);
window.addEventListener('offline', () => toast('Hors ligne'));
document.addEventListener('installable', () => { if (C && vue.page === 'aujourdhui') rendre(); });
window.addEventListener('appinstalled', () => { window.__installation = null; if (C) rendre(); });
$('#voile').onclick = e => { if (e.target.id === 'voile') fermerFiche(); };
document.addEventListener('keydown', e => { if (e.key === 'Escape' && $('#voile').classList.contains('ouvert')) fermerFiche(); });
IMG.surveiller();
initEdition({
  get ed() { return ed; }, sauverEd, liste, apresEdition, ouvrirListe, fermerFiche, ouvrirFeuille,
  categories: () => C.categories,
});

chargerCatalogue().then(c => {
  catalogueOfficiel = c;
  recomposer();
  P.noterCatalogue(etat, C.listes.map(l => l.id), auj());
  enregistrer();
  rendre();
  verifierVersion();
  // ménage discret : photos importées qui ne servent plus
  IMG.cles().then(ks => { const vives = ED.imagesUtilisees(ed); ks.filter(k => !vives.has(k)).forEach(k => IMG.effacer(k)); }).catch(() => {});
}).catch(e => {
  console.error(e);
  $('#racine').innerHTML = `<div class="app"><p class="sous" style="padding-top:40px">Chargement impossible.</p></div>`;
});
