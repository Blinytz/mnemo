// Écrans d'édition : fiche (modifier, ajouter, supprimer), liste personnelle
// (créer, renommer, compléter, supprimer).
//
// Les formulaires s'ouvrent dans la feuille du bas, comme le détail d'une
// fiche. Tout ce qui est enregistré ici reste sur l'appareil (voir edition.js).

import * as ED from './edition.js';
import {importerPhoto} from './images-perso.js';
import {$, esc, ic, img, toast} from './ui.js';

let ctx = null;
/**
 * ctx : {ed, sauverEd, liste(id), apresEdition(idListe, message), ouvrirListe(id),
 *        categories(), fermerFiche(), ouvrirFeuille(html)}
 */
export function initEdition(contexte) { ctx = contexte; }

const champTexte = (col, i, valeur, estCle) => {
  const long = String(valeur || '').length > 40;
  return `<label class="champ"><span>${esc(col)}${estCle ? ' <em>· nom de la fiche</em>' : ''}</span>
    <textarea rows="${long ? 3 : 1}" data-col="${i}" ${estCle ? 'required' : ''}>${esc(valeur || '')}</textarea></label>`;
};

/* ---------- fiche ---------- */
export async function formulaireFiche(idListe, idFiche = null) {
  const l = await ctx.liste(idListe);
  const f = idFiche ? l.fiches.find(x => x.id === idFiche) : null;
  if (idFiche && !f) return;
  let image;                                   // undefined : inchangée ; '' : retirée ; sinon la nouvelle
  const actuelle = () => image === undefined ? (f?.image || '') : image;
  const officielle = !ED.estPerso(ctx.ed, idListe) && f && !f.ajoutee;

  const dessiner = () => {
    const a = actuelle();
    $('#ed-apercu').innerHTML = a ? img(a, 'Image de la fiche') : `<span class="sous">Pas d'image</span>`;
    $('#ed-sans').hidden = !a;
  };

  ctx.ouvrirFeuille(`<div class="poignee"></div><form class="contenu formulaire" id="ed-fiche" novalidate>
    <div><span class="etiquette">${esc(l.nom)}</span><h1 style="margin-top:4px">${f ? 'Modifier la fiche' : 'Nouvelle fiche'}</h1></div>
    <div class="apercu-image" id="ed-apercu"></div>
    <div class="boutons-image">
      <label class="bouton fantome petit">${ic('image-square')} Photo<input type="file" accept="image/*" id="ed-fichier" hidden></label>
      <button type="button" class="bouton fantome petit" id="ed-lien">${ic('link')} Adresse web</button>
      <button type="button" class="bouton fantome petit" id="ed-sans">${ic('trash')} Sans image</button>
    </div>
    <label class="champ" id="ed-lien-champ" hidden><span>Adresse de l'image</span><input type="url" inputmode="url" placeholder="https://…" id="ed-lien-valeur"></label>
    ${l.colonnes.map((c, i) => champTexte(c, i, f?.valeurs[i], i === l.cle)).join('')}
    <p class="sous" style="margin:0">${officielle ? 'Ta modification reste sur cet appareil et passe avant la version officielle ; tu peux revenir à l\'original à tout moment.' : 'Enregistré sur cet appareil.'}</p>
    <div class="actions"><button class="bouton memo" type="submit">Enregistrer</button><button class="bouton fantome" type="button" id="ed-annuler">Annuler</button></div>
    ${f ? `<div class="actions-secondaires">
      ${f.modifiee ? `<button type="button" class="lien" id="ed-retablir">${ic('arrow-counter-clockwise')} Revenir à l'original</button>` : ''}
      <button type="button" class="lien danger" id="ed-supprimer">${ic('trash')} ${officielle ? 'Masquer cette fiche' : 'Supprimer cette fiche'}</button></div>` : ''}
  </form>`);
  dessiner();

  $('#ed-fichier').onchange = async e => {
    const fichier = e.target.files?.[0];
    if (!fichier) return;
    try { image = await importerPhoto(fichier); dessiner(); }
    catch { toast('Cette image ne peut pas être lue.'); }
  };
  $('#ed-lien').onclick = () => { $('#ed-lien-champ').hidden = false; $('#ed-lien-valeur').focus(); };
  $('#ed-lien-valeur').onchange = e => {
    const v = e.target.value.trim();
    if (v && !/^https?:\/\//i.test(v)) return toast('L\'adresse doit commencer par https://');
    image = v || undefined; dessiner();
  };
  $('#ed-sans').onclick = () => { image = ''; dessiner(); };
  $('#ed-annuler').onclick = ctx.fermerFiche;

  $('#ed-fiche').onsubmit = async e => {
    e.preventDefault();
    const valeurs = l.colonnes.map((c, i) => $(`[data-col="${i}"]`).value.trim());
    if (!valeurs[l.cle]) { toast(`« ${l.colonnes[l.cle]} » ne peut pas rester vide.`); return $(`[data-col="${l.cle}"]`).focus(); }
    if (f) ED.modifierFiche(ctx.ed, l, f.id, valeurs, image);
    else ED.ajouterFiche(ctx.ed, l, valeurs, image || undefined);
    if (ctx.sauverEd()) ctx.apresEdition(idListe, f ? 'Fiche enregistrée' : 'Fiche ajoutée');
  };
  $('#ed-retablir')?.addEventListener('click', () => {
    ED.retablirFiche(ctx.ed, idListe, f.id);
    if (ctx.sauverEd()) ctx.apresEdition(idListe, 'Fiche revenue à l\'original');
  });
  $('#ed-supprimer')?.addEventListener('click', () => {
    if (!confirm(officielle ? `Masquer « ${f.valeurs[l.cle]} » ? Tu pourras la faire revenir depuis la page de la liste.` : `Supprimer « ${f.valeurs[l.cle]} » ?`)) return;
    ED.supprimerFiche(ctx.ed, idListe, f.id);
    if (ctx.sauverEd()) ctx.apresEdition(idListe, officielle ? 'Fiche masquée' : 'Fiche supprimée');
  });
}

/* ---------- nouvelle liste ---------- */
const optionsCategories = choisie => ctx.categories().map(c =>
  `<option value="${esc(c.id)}" ${c.id === choisie ? 'selected' : ''}>${esc(c.icone)} ${esc(c.nom)}</option>`).join('');

export function vueNouvelleListe() {
  return `<button class="retour" id="retour">${ic('arrow-left')} Listes</button>
    <h1>Nouvelle liste</h1>
    <form class="carte pile formulaire" id="nouvelle-liste" style="margin-top:14px" novalidate>
      <label class="champ"><span>Nom</span><input id="nl-nom" maxlength="60" placeholder="Capitales d'Europe" required></label>
      <div class="deux">
        <label class="champ"><span>Icône</span><input id="nl-icone" maxlength="4" placeholder="📋"></label>
        <label class="champ"><span>Catégorie</span><select id="nl-categorie">${optionsCategories(ED.CATEGORIE_PERSO)}</select></label>
      </div>
      <label class="champ"><span>Colonnes</span><input id="nl-colonnes" placeholder="Pays, Capitale, Langue"></label>
      <p class="sous" style="margin:0">Sépare les colonnes par des virgules. La première nomme la fiche : c'est elle que le quiz demande sous l'image.</p>
      <details class="coller"><summary>Partir d'un tableau (facultatif)</summary>
        <p class="sous">Copie des cellules dans un tableur et colle-les ici, ou choisis un fichier CSV. La première ligne donne les colonnes.</p>
        <textarea id="nl-tableau" rows="5" placeholder="Pays&#9;Capitale&#10;France&#9;Paris"></textarea>
        <label class="bouton fantome petit" style="justify-self:start">${ic('upload-simple')} Fichier CSV<input type="file" accept=".csv,.tsv,.txt,text/csv" id="nl-csv" hidden></label>
      </details>
      <button class="bouton memo large" type="submit">${ic('plus')} Créer la liste</button>
    </form>`;
}

export function brancherNouvelleListe() {
  $('#nl-csv').onchange = async e => {
    const fichier = e.target.files?.[0];
    if (fichier) $('#nl-tableau').value = await fichier.text();
  };
  $('#nouvelle-liste').onsubmit = e => {
    e.preventDefault();
    const tableau = ED.lireTableau($('#nl-tableau').value);
    const colonnes = tableau.colonnes.length ? tableau.colonnes : $('#nl-colonnes').value.split(',');
    try {
      const l = ED.creerListe(ctx.ed, {nom: $('#nl-nom').value, icone: $('#nl-icone').value, categorie: $('#nl-categorie').value,
        colonnes, lignes: tableau.lignes});
      if (ctx.sauverEd()) { toast(`Liste créée${l.fiches.length ? ` avec ${l.fiches.length} fiches` : ''}`); ctx.apresEdition(l.id, null, true); }
    } catch (err) { toast(err.message); }
  };
}

/* ---------- liste personnelle ---------- */
export function formulaireListe(idListe) {
  const l = ED.listePerso(ctx.ed, idListe);
  if (!l) return;
  ctx.ouvrirFeuille(`<div class="poignee"></div><form class="contenu formulaire" id="ed-liste" novalidate>
    <div><span class="etiquette">Liste personnelle</span><h1 style="margin-top:4px">Modifier la liste</h1></div>
    <label class="champ"><span>Nom</span><input id="el-nom" maxlength="60" value="${esc(l.nom)}"></label>
    <div class="deux">
      <label class="champ"><span>Icône</span><input id="el-icone" maxlength="4" value="${esc(l.icone)}"></label>
      <label class="champ"><span>Catégorie</span><select id="el-categorie">${optionsCategories(l.categorie)}</select></label>
    </div>
    <details class="coller"><summary>Ajouter des fiches depuis un tableau</summary>
      <p class="sous">Une ligne par fiche, dans l'ordre des colonnes : ${esc(l.colonnes.join(' · '))}.</p>
      <textarea id="el-tableau" rows="5"></textarea>
    </details>
    <div class="actions"><button class="bouton memo" type="submit">Enregistrer</button><button class="bouton fantome" type="button" id="el-annuler">Annuler</button></div>
    <div class="actions-secondaires"><button type="button" class="lien danger" id="el-supprimer">${ic('trash')} Supprimer la liste</button></div>
  </form>`);
  $('#el-annuler').onclick = ctx.fermerFiche;
  $('#ed-liste').onsubmit = e => {
    e.preventDefault();
    ED.modifierListe(ctx.ed, idListe, {nom: $('#el-nom').value, icone: $('#el-icone').value, categorie: $('#el-categorie').value});
    // la première ligne collée peut répéter les noms de colonnes : on l'ignore alors
    const brut = $('#el-tableau').value.trim();
    let ajoutees = 0;
    if (brut) {
      for (const v of ED.lireLignes(brut)) {
        if (v.join('|').toLowerCase() === l.colonnes.join('|').toLowerCase() || !String(v[0] || '').trim()) continue;
        ED.ajouterFiche(ctx.ed, l, l.colonnes.map((c, i) => String(v[i] ?? '').trim()));
        ajoutees++;
      }
    }
    if (ctx.sauverEd()) ctx.apresEdition(idListe, ajoutees ? `${ajoutees} fiche${ajoutees > 1 ? 's' : ''} ajoutée${ajoutees > 1 ? 's' : ''}` : 'Liste enregistrée');
  };
  $('#el-supprimer').onclick = () => {
    if (!confirm(`Supprimer la liste « ${l.nom} » et ses ${l.fiches.length} fiches ? Cette action est définitive.`)) return;
    ED.supprimerListe(ctx.ed, idListe);
    if (ctx.sauverEd()) ctx.apresEdition(null, 'Liste supprimée');
  };
}

