// Atelier Mémo — orchestrateur : grille d'images, éditeur de cadrage, reprise
// du travail déjà fait dans WikiDeck, tableau de données, notes, entretien.

import { Editeur, rendreDepuisCadrage, FORMAT } from './image-editor.js';

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const STATUTS = ['manquante', 'importee', 'a_cadrer', 'a_verifier', 'validee',
                 'verrouillee', 'source_cassee', 'conflit'];
const PASTILLE = { validee: '✓', a_verifier: '⚠', manquante: '🚫', importee: '⬇' };

const etat = {
  data: null,
  contexte: null,
  listeCourante: null,
  entreeCourante: null,
  modifie: false,
  undo: [],
  redo: [],
};
// aperçus locaux des images enregistrées pendant la session : la grille les
// affiche tout de suite, sans dépendre du cache du navigateur
const apercus = {};
let editeur = null;
let remplacementEnCours = false;

/* ================= chargement ================= */

async function demarrer() {
  brancherOnglets();
  brancherFiltres();
  brancherEditeur();
  brancherTableau();
  await recharger();
  rendreTout();
  message('enregistré');
  setInterval(() => { if (etat.modifie) enregistrer(); }, 30000);
  window.addEventListener('beforeunload', ev => {
    if (etat.modifie) { ev.preventDefault(); ev.returnValue = ''; }
  });
}

async function recharger() {
  const [data, contexte] = await Promise.all([
    fetch('/api/workspace').then(r => r.json()),
    fetch('/api/contexte').then(r => r.json()),
  ]);
  etat.data = data;
  etat.contexte = contexte;
  etat.listeCourante ||= listesVivantes()[0]?.id || null;
}

function message(texte) { $('#etat').textContent = texte; }
function listesVivantes() { return etat.data.lists.filter(l => !l.deletedAt); }
function listeParId(id) { return etat.data.lists.find(l => l.id === id); }
function infoListe(id) { return etat.contexte.listes.find(l => l.id === id) || {}; }
function entreesDe(listId) {
  return etat.data.entries.filter(e => e.listId === listId && !e.deletedAt)
    .sort((a, b) => a.order - b.order);
}

function instantane() {
  etat.undo.push(JSON.stringify({ categories: etat.data.categories, lists: etat.data.lists, entries: etat.data.entries, notes: etat.data.notes }));
  if (etat.undo.length > 30) etat.undo.shift();
  etat.redo = [];
}

function modifier(fn) {
  instantane();
  fn();
  etat.modifie = true;
  message('modifications en cours');
}

async function enregistrer() {
  const r = await fetch('/api/workspace', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'If-Match': etat.data.revision },
    body: JSON.stringify(etat.data),
  });
  const j = await r.json();
  if (!r.ok) { message('erreur'); alert(j.error || (j.errors || []).join('\n')); return false; }
  etat.data.revision = j.revision;
  etat.data.updatedAt = j.updatedAt;
  etat.modifie = false;
  message('enregistré');
  return true;
}

function rendreTout() {
  remplirFiltres();
  rendreGrille();
  rendreTableau();
  rendreNotes();
}

/* ================= onglets ================= */

function afficherVue(nom) {
  for (const b of document.querySelectorAll('#onglets button')) {
    b.classList.toggle('actif', b.dataset.vue === nom);
  }
  for (const v of document.querySelectorAll('.vue')) {
    v.classList.toggle('visible', v.id === `vue-${nom}`);
  }
  $('#barre-filtres').hidden = !['grille'].includes(nom);
}

function brancherOnglets() {
  for (const b of document.querySelectorAll('#onglets button')) {
    b.addEventListener('click', () => {
      afficherVue(b.dataset.vue);
      if (b.dataset.vue === 'reprise') rendreReprise();
      if (b.dataset.vue === 'entretien') rendreEntretien();
      if (b.dataset.vue === 'tableau') rendreTableau();
    });
  }
  $('#btn-enregistrer').addEventListener('click', enregistrer);
  $('#btn-annuler').addEventListener('click', () => permuterHistorique(etat.undo, etat.redo));
  $('#btn-refaire').addEventListener('click', () => permuterHistorique(etat.redo, etat.undo));
}

function permuterHistorique(source, cible) {
  if (!source.length) return;
  cible.push(JSON.stringify({ categories: etat.data.categories, lists: etat.data.lists, entries: etat.data.entries, notes: etat.data.notes }));
  Object.assign(etat.data, JSON.parse(source.pop()));
  etat.modifie = true;
  message('modifications en cours');
  rendreTout();
}

/* ================= filtres et grille ================= */

function remplirFiltres() {
  const select = $('#f-liste');
  const garde = select.value;
  select.innerHTML = '<option value="">Toutes les listes</option>' +
    listesVivantes().map(l => {
      const hors = infoListe(l.id).dansApplication === false ? ' — hors application' : '';
      return `<option value="${esc(l.id)}">${esc(l.icon || '📚')} ${esc(l.name)}${hors}</option>`;
    }).join('');
  select.value = garde;
}

function brancherFiltres() {
  for (const id of ['#f-liste', '#f-statut', '#f-texte', '#f-hors-app']) {
    $(id).addEventListener('input', rendreGrille);
  }
}

function statutDe(entree) { return entree.image?.status || 'manquante'; }
function aUneImage(entree) { return !!entree.image?.thumb; }

function sourceVignette(entree) {
  if (apercus[entree.id]) return apercus[entree.id];
  return entree.image?.thumb ? '/' + entree.image.thumb : null;
}

function entreeVisible(entree) {
  const st = $('#f-statut').value;
  const q = $('#f-texte').value.trim().toLowerCase();
  if (st === 'sans' && aUneImage(entree)) return false;
  if (st && st !== 'sans' && statutDe(entree) !== st) return false;
  if (q && !`${entree.name} ${entree.number}`.toLowerCase().includes(q)) return false;
  return true;
}

function rendreGrille() {
  const filtreListe = $('#f-liste').value;
  const masquerHors = $('#f-hors-app').checked;
  const morceaux = [];
  const sommaire = [];
  let total = 0;

  for (const liste of listesVivantes()) {
    if (filtreListe && liste.id !== filtreListe) continue;
    const info = infoListe(liste.id);
    if (masquerHors && info.dansApplication === false) continue;
    const visibles = entreesDe(liste.id).filter(entreeVisible);
    if (!visibles.length) continue;
    total += visibles.length;
    sommaire.push(`<a href="#liste-${esc(liste.id)}">${esc(liste.name)} (${visibles.length})</a>`);
    const badge = info.dansApplication === false
      ? '<span class="etiquette-hors-app" title="memo.html ne contient pas cette liste : les images enregistrées ne s’afficheront pas dans l’application">hors application</span>'
      : '';
    morceaux.push(`<h2 id="liste-${esc(liste.id)}">${esc(liste.icon || '📚')} ${esc(liste.name)}
      <small>${visibles.length}</small>${badge}</h2>
      <div class="grille">` + visibles.map(vignette).join('') + '</div>');
  }

  $('#vue-grille').innerHTML = morceaux.length
    ? `<nav class="sommaire">${sommaire.join('')}</nav><p class="doux">${total} entrée(s) affichée(s)</p>` + morceaux.join('')
    : '<p class="doux">Aucune entrée ne correspond à ces filtres.</p>';

  $('#vue-grille').onclick = ev => {
    const pastille = ev.target.closest('[data-statut]');
    if (pastille) {
      const entree = etat.data.entries.find(e => e.id === pastille.dataset.statut);
      const suite = { validee: 'a_verifier', a_verifier: 'validee' };
      modifier(() => { entree.image.status = suite[statutDe(entree)] || 'a_verifier'; });
      rendreGrille();
      return;
    }
    const v = ev.target.closest('.vignette');
    if (v) ouvrirEditeur(v.dataset.id);
  };
}

function vignette(entree) {
  const src = sourceVignette(entree);
  const st = statutDe(entree);
  const liste = listeParId(entree.listId);
  return `<div class="vignette" data-id="${esc(entree.id)}">
    ${src ? `<img loading="lazy" src="${esc(src)}" alt="">`
          : '<div class="sans-image">🚫</div>'}
    <button class="v-statut ${esc(st)}" data-statut="${esc(entree.id)}"
            title="${esc(st.replaceAll('_', ' '))}">${PASTILLE[st] || '·'}</button>
    ${entree.image?.locked ? '<span class="v-verrou" title="verrouillée">🔒</span>' : ''}
    <div class="v-nom" title="${esc(entree.name)}">${esc(entree.name)}</div>
    <div class="v-liste">n° ${esc(entree.number)} · ${esc(liste?.name || '')}</div>
  </div>`;
}

/* ================= éditeur ================= */

function brancherEditeur() {
  editeur = new Editeur($('#ed-conteneur'), $('#ed-image'), $('#ed-canvas-apercu'), majMesures);
  $('#ed-f-statut').innerHTML = STATUTS.map(s =>
    `<option value="${s}">${s.replaceAll('_', ' ')}</option>`).join('');

  $('#ed-fermer').addEventListener('click', fermerEditeur);
  $('#ed-plus').addEventListener('click', () => editeur.zoomer(1.2));
  $('#ed-moins').addEventListener('click', () => editeur.zoomer(1 / 1.2));
  $('#ed-reset').addEventListener('click', () => editeur.recadrerAuto());
  $('#ed-contenir').addEventListener('click', () => editeur.contenir());
  $('#ed-annuler').addEventListener('click', () => editeur.annuler());
  // Le garde-fou se règle par liste : les logos de départements se dézooment,
  // les portraits non. Le choix est retenu pour toute la liste.
  $('#ed-f-borne').addEventListener('change', ev => {
    const e = entreeCourante();
    if (!e) return;
    const liste = listeParId(e.listId);
    modifier(() => { (liste.metadata ||= {}).cadrageLibre = !ev.target.checked; });
    editeur.setBorne(ev.target.checked);
    majOutilsCadrage();
  });
  $('#ed-enregistrer').addEventListener('click', enregistrerImage);
  $('#ed-remplacer').addEventListener('click', modaleRemplacement);
  $('#ed-note').addEventListener('click', () => etat.entreeCourante && modaleNote([etat.entreeCourante]));
  $('#ed-fichier').addEventListener('change', async ev => {
    const f = ev.target.files[0];
    if (f) { await chargerRemplacement(f); ev.target.value = ''; }
  });

  // fiche : liaison directe des champs simples
  const champs = [['#ed-f-numero', 'number'], ['#ed-f-nom', 'name'], ['#ed-f-titre', 'title'],
                  ['#ed-f-soustitre', 'subtitle'], ['#ed-f-wiki', 'wikipedia'],
                  ['#ed-f-description', 'description']];
  for (const [sel, cle] of champs) {
    $(sel).addEventListener('input', ev => {
      const e = entreeCourante();
      if (!e) return;
      e[cle] = ev.target.value;
      etat.modifie = true;
      message('modifications en cours');
      if (cle === 'wikipedia') $('#ed-f-wiki-ouvrir').href = ev.target.value || '#';
      if (cle === 'name') $('#ed-nom').textContent = ev.target.value;
    });
  }
  $('#ed-f-statut').addEventListener('change', ev => {
    const e = entreeCourante(); if (!e) return;
    modifier(() => { e.image.status = ev.target.value; });
  });
  $('#ed-f-verrou').addEventListener('change', ev => {
    const e = entreeCourante(); if (!e) return;
    modifier(() => { e.image.locked = ev.target.checked; });
  });
  $('#ed-champs-liste').addEventListener('input', ev => {
    const e = entreeCourante(); if (!e || !ev.target.dataset.champ) return;
    e.fields[ev.target.dataset.champ] = ev.target.value;
    etat.modifie = true;
    message('modifications en cours');
  });

  // coller une image ou une URL n'importe où dans l'éditeur
  document.addEventListener('paste', async ev => {
    if ($('#editeur').hidden) return;
    if (ev.target.closest('input, textarea, select, [contenteditable]')) return;
    const item = [...(ev.clipboardData?.items || [])].find(i => i.type.startsWith('image/'));
    if (item) { ev.preventDefault(); await chargerRemplacement(item.getAsFile()); return; }
    const texte = ev.clipboardData?.getData('text');
    if (texte && /^https?:\/\//.test(texte.trim())) {
      ev.preventDefault();
      await chargerRemplacementURL(texte.trim());
    }
  });
  const ed = $('#editeur');
  ed.addEventListener('dragover', ev => ev.preventDefault());
  ed.addEventListener('drop', async ev => {
    ev.preventDefault();
    const f = ev.dataTransfer?.files?.[0];
    if (f && f.type.startsWith('image/')) await chargerRemplacement(f);
  });
  document.addEventListener('keydown', ev => {
    if (ev.key === 'Escape' && !$('#editeur').hidden && $('#modale').hidden) fermerEditeur();
  });
}

function entreeCourante() {
  return etat.data.entries.find(e => e.id === etat.entreeCourante);
}

function majMesures() {
  const out = $('#ed-mesures');
  if (!editeur?.source) { out.textContent = ''; return; }
  // 100 % = l'image remplit exactement le cadre ; en dessous, du fond apparaît
  const couverture = Math.round(editeur.s / editeur.sCouvre * 100);
  out.textContent = `source ${editeur.iw} × ${editeur.ih} px · cadre rempli à ${couverture} %`
    + (editeur.aDuFond ? ' · fond comblé autour' : '');
}

function majOutilsCadrage() {
  $('#ed-contenir').hidden = editeur.borne;
}

function cadrageLibrePour(liste) {
  return !!liste?.metadata?.cadrageLibre;
}

async function ouvrirEditeur(entryId) {
  etat.entreeCourante = entryId;
  const e = entreeCourante();
  if (!e) return;
  const liste = listeParId(e.listId);
  const info = infoListe(e.listId);
  remplacementEnCours = false;

  $('#ed-nom').textContent = e.name;
  $('#ed-infos').textContent = `${liste?.name || ''} · n° ${e.number}` +
    (info.dansApplication === false ? ' · liste absente de l’application' : '');
  $('#ed-f-numero').value = e.number || '';
  $('#ed-f-nom').value = e.name || '';
  $('#ed-f-titre').value = e.title || '';
  $('#ed-f-soustitre').value = e.subtitle || '';
  $('#ed-f-wiki').value = e.wikipedia || '';
  $('#ed-f-wiki-ouvrir').href = e.wikipedia || '#';
  $('#ed-f-description').value = e.description || '';
  $('#ed-f-statut').value = statutDe(e);
  $('#ed-f-verrou').checked = !!e.image?.locked;
  $('#ed-champs-liste').innerHTML = Object.entries(e.fields || {})
    .filter(([k]) => !/^image$/i.test(k))
    .map(([k, v]) => `<label>${esc(k)}<input data-champ="${esc(k)}" value="${esc(v)}"></label>`).join('');

  $('#editeur').hidden = false;   // le cadre doit avoir sa taille avant tout calcul
  const borne = !cadrageLibrePour(liste);
  $('#ed-f-borne').checked = borne;
  editeur.borne = borne;
  majOutilsCadrage();
  editeur.vider();
  $('#ed-vide').hidden = false;

  const bust = `?v=${Date.now()}`;
  const sources = [e.image?.source, e.image?.full, e.image?.thumb]
    .filter(Boolean).map(p => '/' + p + bust);
  if (!sources.length) { majMesures(); return; }
  try {
    await editeur.chargerPremiereDisponible(sources);
    $('#ed-vide').hidden = true;
    // un cadrage déjà décidé dans l'Atelier prime ; sinon, en cadrage libre, on
    // montre l'image entière plutôt qu'un cadrage qui l'ampute d'emblée
    const dejaCadree = ['manuel', 'recadrage', 'wikideck'].includes(e.image?.provenance?.kind);
    if (dejaCadree) editeur.setCadrage(e.image?.crop);
    else if (!borne) editeur.contenir();
    else editeur.setCadrage(e.image?.crop);
  } catch {
    $('#ed-vide').hidden = false;
    $('#ed-vide').textContent = 'Image d’origine illisible — remplace-la pour continuer.';
  }
  majMesures();
}

function fermerEditeur() {
  $('#editeur').hidden = true;
  etat.entreeCourante = null;
  rendreGrille();
}

function modaleRemplacement() {
  ouvrirModale(`
    <h3>Remplacer l'image</h3>
    <p class="doux">Trois moyens :</p>
    <input type="url" id="m-url" placeholder="Coller l'URL d'une image puis Entrée…">
    <p class="doux">— ou colle l'image elle-même (Ctrl+V) n'importe où dans l'éditeur —</p>
    <div class="m-boutons">
      <button class="btn" id="m-fichier">📁 Choisir un fichier…</button>
      <button class="btn btn-discret" id="m-annuler">Annuler</button>
    </div>`);
  $('#m-url').addEventListener('keydown', async ev => {
    if (ev.key === 'Enter' && ev.target.value.trim()) {
      const url = ev.target.value.trim();
      fermerModale();
      await chargerRemplacementURL(url);
    }
  });
  $('#m-fichier').onclick = () => { fermerModale(); $('#ed-fichier').click(); };
  $('#m-annuler').onclick = fermerModale;
}

async function chargerRemplacementURL(url) {
  // essai direct, puis via un relais si le serveur d'origine refuse le partage
  const candidats = [url,
    'https://images.weserv.nl/?url=' + encodeURIComponent(url.replace(/^https?:\/\//, '')) + '&w=2000'];
  for (const u of candidats) {
    try {
      await editeur.chargerURL(u);
      remplacementEnCours = true;
      $('#ed-vide').hidden = true;
      majMesures();
      return;
    } catch { /* candidat suivant */ }
  }
  alert('Impossible de charger cette URL. Essaie de copier l’image elle-même puis Ctrl+V.');
}

async function chargerRemplacement(blob) {
  await editeur.chargerBlob(blob);
  remplacementEnCours = true;
  $('#ed-vide').hidden = true;
  majMesures();
}

function blobEnBase64(blob) {
  return new Promise((ok, non) => {
    const fr = new FileReader();
    fr.onload = () => ok(String(fr.result).split(',')[1]);
    fr.onerror = non;
    fr.readAsDataURL(blob);
  });
}

async function envoyerImage(entryId, sorties, extra = {}) {
  const charge = {
    original: await blobEnBase64(sorties.original),
    full: await blobEnBase64(sorties.full),
    thumb: await blobEnBase64(sorties.thumb),
    cadrage: sorties.cadrage,
    ...extra,
  };
  const r = await fetch(`/api/entree/image?id=${encodeURIComponent(entryId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(charge),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || 'échec de l’enregistrement');
  // le serveur fait autorité sur l'image et la révision
  const e = etat.data.entries.find(x => x.id === entryId);
  if (e) e.image = j.image;
  etat.data.revision = j.revision;
  apercus[entryId] = URL.createObjectURL(sorties.thumb);
  return j;
}

async function enregistrerImage() {
  const e = entreeCourante();
  if (!e) return;
  if (!editeur.source) return alert('Charge d’abord une image (🔄 Remplacer).');
  if (e.image?.locked && !confirm('Cette image est verrouillée. La remplacer quand même ?')) return;
  const bouton = $('#ed-enregistrer');
  bouton.disabled = true;
  message('enregistrement de l’image…');
  try {
    const sorties = await editeur.exporter();
    sorties.cadrage = editeur.getCadrage();
    const j = await envoyerImage(e.id, sorties, {
      statut: 'validee',
      provenance: { kind: remplacementEnCours ? 'manuel' : 'recadrage', at: new Date().toISOString() },
    });
    message(j.dansApplication ? 'image enregistrée dans Mémo' : 'image enregistrée (liste hors application)');
    if (!j.dansApplication) {
      alert('Les fichiers sont écrits, mais memo.html ne contient pas cette liste :\n' +
            'l’application n’affichera pas encore cette image.');
    }
    fermerEditeur();
  } catch (err) {
    message('erreur');
    alert('Échec : ' + err.message);
  } finally {
    bouton.disabled = false;
  }
}

/* ================= tableau ================= */

function brancherTableau() {
  $('#btn-ligne').addEventListener('click', ajouterLigne);
  $('#btn-dupliquer').addEventListener('click', dupliquerLigne);
  $('#btn-corbeille').addEventListener('click', mettreALaCorbeille);
  $('#btn-renumeroter').addEventListener('click', renumeroter);
  $('#tbody').addEventListener('click', ev => {
    const tr = ev.target.closest('tr');
    if (tr && ev.target.closest('[data-ouvrir]')) ouvrirEditeur(tr.dataset.id);
  });
  $('#tbody').addEventListener('input', ev => {
    const tr = ev.target.closest('tr');
    const e = etat.data.entries.find(x => x.id === tr?.dataset.id);
    if (!e) return;
    if (ev.target.dataset.champ === 'number') e.number = ev.target.textContent.trim();
    else if (ev.target.dataset.champ === 'name') e.name = ev.target.textContent.trim();
    else if (ev.target.dataset.extra) e.fields[ev.target.dataset.extra] = ev.target.textContent.trim();
    etat.modifie = true;
    message('modifications en cours');
  });
}

function listeTableau() {
  return listeParId($('#f-liste').value) || listeParId(etat.listeCourante) || listesVivantes()[0];
}

function rendreTableau() {
  const liste = listeTableau();
  if (!liste) return;
  etat.listeCourante = liste.id;
  const entrees = entreesDe(liste.id);
  const sans = entrees.filter(e => !aUneImage(e)).length;
  $('#tableau-titre').textContent = `${liste.icon || '📚'} ${liste.name}`;
  $('#tableau-metriques').textContent =
    `${entrees.length} entrées · ${sans} sans image` +
    (infoListe(liste.id).dansApplication === false ? ' · hors application' : '');
  const extra = (liste.columns || []).filter(c => !/^(num[ée]ro|image|nom)$/i.test(c));
  $('#thead').innerHTML = `<tr><th>N°</th><th>Image</th><th>Nom</th>${
    extra.map(c => `<th>${esc(c)}</th>`).join('')}</tr>`;
  $('#tbody').innerHTML = entrees.map(e => {
    const src = sourceVignette(e);
    return `<tr data-id="${esc(e.id)}">
      <td contenteditable data-champ="number">${esc(e.number)}</td>
      <td data-ouvrir>${src ? `<img loading="lazy" src="${esc(src)}" alt="">` : '—'}</td>
      <td contenteditable data-champ="name">${esc(e.name)}</td>
      ${extra.map(c => `<td contenteditable data-extra="${esc(c)}">${esc(e.fields?.[c] || '')}</td>`).join('')}
    </tr>`;
  }).join('');
}

function ajouterLigne() {
  const liste = listeTableau();
  if (!liste) return;
  modifier(() => {
    const rang = entreesDe(liste.id).length;
    etat.data.entries.push({
      id: crypto.randomUUID(), listId: liste.id, slug: '', number: String(rang + 1),
      name: 'Nouvelle entrée', title: 'Nouvelle entrée', subtitle: '', description: '',
      extraText: '', wikipedia: '', fields: {}, order: rang, deletedAt: null, externalIds: {},
      image: { source: null, full: null, thumb: null, crop: { cx: .5, cy: .5, w: 1 },
               status: 'manquante', locked: false, provenance: {} },
    });
  });
  rendreTableau();
}

function dupliquerLigne() {
  const e = entreeCourante() || entreesDe(listeTableau()?.id)[0];
  if (!e) return;
  modifier(() => {
    const rang = entreesDe(e.listId).length;
    etat.data.entries.push({
      ...structuredClone(e), id: crypto.randomUUID(), order: rang,
      number: String(Number(e.number || 0) + 1),
      image: { ...structuredClone(e.image), locked: false },
    });
  });
  rendreTableau();
}

function mettreALaCorbeille() {
  const e = entreeCourante();
  if (!e) return alert('Ouvre d’abord une entrée.');
  if (!confirm(`Placer « ${e.name} » dans la corbeille ?`)) return;
  modifier(() => {
    e.deletedAt = new Date().toISOString();
    etat.data.trash.push({ type: 'entry', id: e.id, at: e.deletedAt });
  });
  etat.entreeCourante = null;
  rendreTout();
}

function renumeroter() {
  const liste = listeTableau();
  if (!liste) return;
  const depart = Number(prompt('Premier numéro', '1'));
  if (!Number.isFinite(depart)) return;
  const entrees = entreesDe(liste.id);
  ouvrirModale(`
    <h3>Renuméroter ${entrees.length} entrée(s)</h3>
    <div style="max-height:40vh;overflow:auto">${entrees.map((e, i) =>
      `<div class="diff"><s>${esc(e.number)}</s><span>→</span><b>${depart + i}</b></div>`).join('')}</div>
    <div class="m-boutons">
      <button class="btn btn-primaire" id="m-ok">Confirmer</button>
      <button class="btn btn-discret" id="m-annuler">Annuler</button>
    </div>`);
  $('#m-ok').onclick = () => {
    modifier(() => entrees.forEach((e, i) => { e.number = String(depart + i); }));
    fermerModale();
    rendreTableau();
  };
  $('#m-annuler').onclick = fermerModale;
}

/* ================= reprise WikiDeck ================= */

let appariementCourant = null;

function rendreReprise() {
  const collections = etat.contexte.wikideck || [];
  if (!collections.length) {
    $('#vue-reprise').innerHTML = `<div class="panneau"><h3>Reprise WikiDeck</h3>
      <p class="doux">L'atelier WikiDeck est introuvable à côté de Mémo. Rien à reprendre.</p></div>`;
    return;
  }
  const listes = listesVivantes();
  $('#vue-reprise').innerHTML = `
    <div class="panneau">
      <h3>Reprendre le travail déjà fait dans WikiDeck</h3>
      <p class="doux">Choisis une liste de Mémo et la collection WikiDeck correspondante.
      L'appariement se fait sur la colonne qui porte le sujet — pour la Formule 1
      c'est « Pilote », pas « Année ». Rien n'est écrit avant que tu ne confirmes.</p>
      <div class="reglages-reprise">
        <label>Liste de Mémo
          <select id="r-liste">${listes.map(l =>
            `<option value="${esc(l.id)}">${esc(l.name)} (${entreesDe(l.id).length})</option>`).join('')}</select></label>
        <label>Collection WikiDeck
          <select id="r-collection">${collections.map(c =>
            `<option value="${esc(c.slug)}">${esc(c.nom)} (${c.cartes} cartes, ${c.cadrees} cadrées)</option>`).join('')}</select></label>
        <label>Colonne servant de sujet
          <select id="r-colonne"><option>—</option></select></label>
      </div>
      <div class="m-boutons">
        <button class="btn btn-primaire" id="r-analyser">Analyser</button>
      </div>
      <div id="r-resultat"></div>
    </div>`;
  $('#r-analyser').onclick = analyserReprise;
  $('#r-liste').onchange = () => { $('#r-resultat').innerHTML = ''; };
  $('#r-colonne').onchange = () => { if (appariementCourant) analyserReprise($('#r-colonne').value); };
  proposerCollection();
  $('#r-liste').addEventListener('change', proposerCollection);
}

// Pré-sélectionne la collection dont le nom ressemble le plus à celui de la liste.
function proposerCollection() {
  const liste = listeParId($('#r-liste').value);
  if (!liste) return;
  const mots = s => new Set(String(s).toLowerCase().normalize('NFD')
    .replace(/\p{Diacritic}/gu, '').split(/[^a-z0-9]+/).filter(m => m.length > 3));
  const cible = mots(liste.name);
  let meilleur = null, score = 0;
  for (const c of etat.contexte.wikideck) {
    const n = [...mots(c.nom)].filter(m => cible.has(m)).length;
    if (n > score) { score = n; meilleur = c.slug; }
  }
  if (meilleur) $('#r-collection').value = meilleur;
}

async function analyserReprise(colonneVoulue) {
  const listId = $('#r-liste').value;
  const collection = $('#r-collection').value;
  $('#r-resultat').innerHTML = '<p class="doux">Analyse en cours…</p>';
  const r = await fetch('/api/wikideck/appariement', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ listId, collection, colonne: typeof colonneVoulue === 'string' ? colonneVoulue : undefined }),
  });
  const j = await r.json();
  if (!r.ok) { $('#r-resultat').innerHTML = `<p class="doux">Erreur : ${esc(j.error)}</p>`; return; }
  appariementCourant = { ...j, listId, collection };
  $('#r-colonne').innerHTML = j.colonnes.map(c =>
    `<option value="${esc(c.col)}" ${c.col === j.colonne ? 'selected' : ''}>${esc(c.col)} — ${c.touches} correspondance(s)</option>`).join('');
  rendreResultatReprise();
}

function rendreResultatReprise() {
  const { paires, resume, colonne } = appariementCourant;
  const retenables = paires.filter(p => p.statut === 'certain' && p.candidats[0] && !p.candidats[0].sansOriginal);
  $('#r-resultat').innerHTML = `
    <hr>
    <p><span class="pastille certain">${resume.certain} certaines</span>
       <span class="pastille ambigu">${resume.ambigu} ambiguës</span>
       <span class="pastille sans">${resume.sans} sans correspondance</span></p>
    <p class="doux">Appariement sur la colonne « ${esc(colonne)} ».
      ${resume.verrouillees ? resume.verrouillees + ' entrée(s) verrouillée(s) seront ignorées. ' : ''}
      Les images de WikiDeck remplaceront celles de Mémo, avec leur cadrage déjà validé,
      redécoupées aux formats de Mémo (${FORMAT.full.join(' × ')} et ${FORMAT.thumb.join(' × ')}).</p>
    <div class="m-boutons">
      <button class="btn btn-primaire" id="r-importer" ${retenables.length ? '' : 'disabled'}>
        Importer ${retenables.length} image(s)</button>
      <button class="btn btn-discret" id="r-tout-cocher">Tout cocher</button>
      <button class="btn btn-discret" id="r-rien-cocher">Tout décocher</button>
    </div>
    <div class="progression" id="r-progression" hidden><i></i></div>
    <div class="paires">${paires.map(ligneAppariement).join('')}</div>`;
  $('#r-importer').onclick = importerReprise;
  $('#r-tout-cocher').onclick = () => basculerCases(true);
  $('#r-rien-cocher').onclick = () => basculerCases(false);
}

function basculerCases(valeur) {
  for (const c of document.querySelectorAll('#r-resultat input[type=checkbox]:not(:disabled)')) c.checked = valeur;
}

function ligneAppariement(p) {
  const carte = p.candidats[0];
  const entree = etat.data.entries.find(e => e.id === p.entryId);
  const actuelle = entree && sourceVignette(entree);
  const importable = p.statut === 'certain' && carte && !carte.sansOriginal && !p.verrouillee;
  return `<div class="paire ${esc(p.statut)}">
    <input type="checkbox" data-paire="${esc(p.entryId)}" ${importable ? 'checked' : 'disabled'}>
    ${actuelle ? `<img loading="lazy" src="${esc(actuelle)}" alt="">` : '<div class="vide">🚫</div>'}
    <div class="infos">
      <b>${esc(p.libelle)}</b>
      <div>${esc(p.valeur || '—')} · <span class="pastille ${esc(p.statut)}">${esc(p.raison)}</span>
      ${p.verrouillee ? ' 🔒 verrouillée' : ''}
      ${carte?.sansOriginal ? ' · image d’origine absente côté WikiDeck' : ''}</div>
    </div>
    <div class="fleche">→</div>
    ${carte ? `<img class="apercu-carte" loading="lazy" src="/wikideck/${esc(carte.apercu || '')}" alt="" title="${esc(carte.nom)}">`
            : '<div class="vide apercu-carte">—</div>'}
  </div>`;
}

async function importerReprise() {
  const choisies = [...document.querySelectorAll('#r-resultat input[type=checkbox]:checked')]
    .map(c => c.dataset.paire);
  const paires = appariementCourant.paires.filter(p => choisies.includes(p.entryId) && p.candidats[0]);
  if (!paires.length) return;
  if (!confirm(`Importer ${paires.length} image(s) depuis WikiDeck ?\n` +
               'Les images actuelles de Mémo seront remplacées et memo.html mis à jour.')) return;

  const barre = $('#r-progression');
  barre.hidden = false;
  const bouton = $('#r-importer');
  bouton.disabled = true;
  let faites = 0;
  const echecs = [];

  for (const p of paires) {
    const carte = p.candidats[0];
    try {
      const sorties = await rendreDepuisCadrage(`/wikideck/${carte.source}`, carte.cadrage);
      await envoyerImage(p.entryId, sorties, {
        statut: 'importee',
        cardId: carte.id,
        wikipedia: carte.wikipedia || undefined,
        provenance: { kind: 'wikideck', cardId: carte.id, at: new Date().toISOString() },
      });
    } catch (err) {
      echecs.push(`${p.libelle} : ${err.message}`);
    }
    faites++;
    barre.querySelector('i').style.width = `${Math.round(faites / paires.length * 100)}%`;
    message(`reprise ${faites}/${paires.length}`);
  }

  bouton.disabled = false;
  message('enregistré');
  await recharger();
  rendreTout();
  alert(`${paires.length - echecs.length} image(s) reprises et écrites dans Mémo.` +
        (echecs.length ? `\n\n${echecs.length} échec(s) :\n` + echecs.slice(0, 10).join('\n') : ''));
  analyserReprise($('#r-colonne').value);
}

/* ================= notes ================= */

function rendreNotes() {
  const notes = etat.data.notes || [];
  $('#nb-notes').textContent = notes.length ? `(${notes.length})` : '';
  $('#vue-notes').innerHTML = `
    <div class="panneau">
      <h3>Nouvelle note</h3>
      <textarea id="n-texte" placeholder="Remarque à traiter plus tard…"></textarea>
      <div class="m-boutons">
        <select id="n-priorite"><option>normale</option><option>haute</option><option>basse</option></select>
        <button class="btn btn-primaire" id="n-ajouter">Ajouter sur la liste affichée</button>
      </div>
    </div>` +
    (notes.length ? notes.map(n => `<div class="note">
      <b>${esc(n.status || 'todo')} · ${esc(n.priority || 'normale')}</b>
      <p>${esc(n.text)}</p>
      <small class="doux">${(n.targets?.entryIds || []).length} entrée(s), ${(n.targets?.listIds || []).length} liste(s)</small>
      <div class="m-boutons"><button class="btn btn-discret" data-note-suppr="${esc(n.id)}">Supprimer</button></div>
    </div>`).join('') : '<p class="doux">Aucune note.</p>');

  $('#n-ajouter').onclick = () => {
    const texte = $('#n-texte').value.trim();
    if (!texte) return;
    modifier(() => etat.data.notes.push({
      id: crypto.randomUUID(), text: texte,
      targets: { entryIds: [], listIds: [etat.listeCourante].filter(Boolean) },
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
      status: 'todo', priority: $('#n-priorite').value,
    }));
    rendreNotes();
  };
  $('#vue-notes').onclick = ev => {
    const id = ev.target.dataset?.noteSuppr;
    if (id && confirm('Supprimer cette note ?')) {
      modifier(() => { etat.data.notes = etat.data.notes.filter(n => n.id !== id); });
      rendreNotes();
    }
  };
}

function modaleNote(entryIds) {
  ouvrirModale(`
    <h3>Note sur cette entrée</h3>
    <textarea id="m-texte" rows="4" placeholder="Remarque…"></textarea>
    <div class="m-boutons">
      <button class="btn btn-primaire" id="m-ok">Enregistrer</button>
      <button class="btn btn-discret" id="m-annuler">Annuler</button>
    </div>`);
  $('#m-ok').onclick = () => {
    const texte = $('#m-texte').value.trim();
    if (!texte) return fermerModale();
    modifier(() => etat.data.notes.push({
      id: crypto.randomUUID(), text: texte,
      targets: { entryIds, listIds: [] },
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
      status: 'todo', priority: 'normale',
    }));
    fermerModale();
    rendreNotes();
  };
  $('#m-annuler').onclick = fermerModale;
}

/* ================= entretien ================= */

async function rendreEntretien() {
  $('#vue-entretien').innerHTML = '<p class="doux">Analyse en cours…</p>';
  const [sante, noms] = await Promise.all([
    fetch('/api/health').then(r => r.json()),
    fetch('/api/noms/apercu').then(r => r.json()),
  ]);
  const hors = etat.contexte.listes.filter(l => !l.dansApplication);
  const total = noms.propositions.reduce((a, p) => a + p.changements.length, 0);

  $('#vue-entretien').innerHTML = `
    <div class="panneau">
      <h3>État</h3>
      <p class="doux">
        Application : ${sante.memoHtml ? '🟢 memo.html trouvé et mis à jour à chaque enregistrement' : '🔴 memo.html introuvable'}<br>
        WikiDeck : ${sante.wikideck ? '🟢 disponible pour la reprise d’images' : '🔴 introuvable'}<br>
        Formats écrits : grande image ${FORMAT.full.join(' × ')}, miniature ${FORMAT.thumb.join(' × ')}, découpées dans le même cadrage.
      </p>
    </div>

    ${hors.length ? `<div class="panneau">
      <h3>${hors.length} liste(s) absente(s) de l'application</h3>
      <p class="doux">memo.html n'embarque que ${etat.contexte.listesApplication.length} listes.
      Pour celles-ci, l'Atelier écrit bien les fichiers images, mais l'application
      ne les affichera pas tant que les listes n'y auront pas été ajoutées :</p>
      <p class="doux">${hors.map(l => esc(listeParId(l.id)?.name || l.legacyId)).join(' · ')}</p>
    </div>` : ''}

    <div class="panneau">
      <h3>Noms d'entrées</h3>
      ${total ? `<p class="doux">La migration a retenu la mauvaise colonne comme nom sur
      ${noms.propositions.length} liste(s) : ${total} entrée(s) portent par exemple une année
      au lieu du nom du sujet. Sans nom juste, aucun rapprochement avec WikiDeck n'est possible.
      memo.html déclare lui-même la bonne colonne pour chaque liste.</p>
      <div class="m-boutons">
        <button class="btn btn-primaire" id="e-noms">Corriger les ${total} noms</button>
      </div>
      ${noms.propositions.map(p => `<h4>${esc(p.liste)} <small class="doux">colonne « ${esc(p.colonne)} » — ${p.changements.length}</small></h4>
        ${p.changements.slice(0, 8).map(c =>
          `<div class="diff"><s>${esc(c.avant)}</s><span>→</span><b>${esc(c.apres)}</b></div>`).join('')}
        ${p.changements.length > 8 ? `<p class="doux">… et ${p.changements.length - 8} autres</p>` : ''}`).join('')}`
      : '<p class="doux">Rien à corriger : chaque entrée porte déjà le nom de sa colonne-sujet.</p>'}
    </div>`;

  const bouton = $('#e-noms');
  if (bouton) {
    bouton.onclick = async () => {
      if (!confirm(`Corriger ${total} nom(s) d'entrées ?`)) return;
      if (etat.modifie && !await enregistrer()) return;
      const r = await fetch('/api/noms/appliquer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true }),
      });
      const j = await r.json();
      if (!r.ok) return alert(j.error || 'échec');
      await recharger();
      rendreTout();
      rendreEntretien();
      alert(`${j.modifiees} nom(s) corrigé(s).`);
    };
  }
}

/* ================= modale ================= */

function ouvrirModale(html) { $('#modale-boite').innerHTML = html; $('#modale').hidden = false; }
function fermerModale() { $('#modale').hidden = true; }
$('#modale').addEventListener('click', ev => { if (ev.target.id === 'modale') fermerModale(); });

demarrer();
