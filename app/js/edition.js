// Édition des listes, sur l'appareil.
//
// Les listes officielles (data/, produites depuis WikiDeck et l'Atelier) ne
// sont jamais réécrites : les changements de l'utilisateur forment une couche
// posée par-dessus au chargement. Une fiche modifiée peut toujours revenir à
// l'original ; une mise à jour officielle d'une fiche non modifiée passe
// telle quelle.
//
// Rangement, sous la clé « memo2-listes » :
//   modifs   {idListe: {idFiche: {valeurs, image?}}}   fiches officielles changées
//   ajouts   {idListe: [fiche]}                        fiches ajoutées à une liste officielle
//   retraits {idListe: [idFiche]}                      fiches officielles masquées
//   perso    [liste]                                   listes créées par l'utilisateur
// Les photos importées vivent à part (images-perso.js) ; une fiche n'en garde
// que la référence « perso:<clé> ».

export const CLE_EDITION = 'memo2-listes';
export const CATEGORIE_PERSO = 'mes-listes';

export function editionVide() {
  return {v: 1, modifs: {}, ajouts: {}, retraits: {}, perso: []};
}

export function chargerEdition(stockage) {
  try {
    const e = JSON.parse(stockage.getItem(CLE_EDITION) || 'null');
    if (e && e.v === 1) return {...editionVide(), ...e};
  } catch {}
  return editionVide();
}

export function sauverEdition(stockage, ed) {
  stockage.setItem(CLE_EDITION, JSON.stringify(ed));   // l'appelant traite le stockage plein
}

/* ---------- identifiants ---------- */
export function nouvelId(prefixe = 'p') {
  const alea = Math.random().toString(36).slice(2, 8);
  return `${prefixe}-${Date.now().toString(36)}${alea}`;
}
const slug = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'liste';

/* ---------- lecture ---------- */
export const estPerso = (ed, idListe) => ed.perso.some(l => l.id === idListe);
export const listePerso = (ed, idListe) => ed.perso.find(l => l.id === idListe);

/** La liste telle que l'utilisateur la voit : officielle + ses changements. */
export function appliquer(liste, ed) {
  if (estPerso(ed, liste.id)) return liste;
  const modifs = ed.modifs[liste.id] || {}, retraits = new Set(ed.retraits[liste.id] || []);
  const fiches = liste.fiches.filter(f => !retraits.has(f.id)).map(f => {
    const m = modifs[f.id];
    if (!m) return f;
    const g = {...f, valeurs: liste.colonnes.map((c, i) => m.valeurs?.[i] ?? f.valeurs[i]), modifiee: true};
    if (m.image !== undefined) { g.image = m.image; delete g.grande; }
    return g;
  });
  for (const f of ed.ajouts[liste.id] || []) fiches.push({...f, ajoutee: true});
  return {...liste, fiches};
}

/** Résumé d'une liste personnelle, au format du catalogue. */
export function resumePerso(l) {
  return {id: l.id, nom: l.nom, icone: l.icone, categorie: l.categorie || CATEGORIE_PERSO, colonnes: l.colonnes, cle: 0,
    fiches: l.fiches.length, images: l.fiches.some(f => f.image), perso: true,
    apercu: l.fiches.filter(f => f.image).slice(0, 3).map(f => f.image), ids: l.fiches.map(f => f.id).join(' ')};
}

/** Identifiants « liste/fiche » visibles après changements, pour une liste du catalogue. */
export function idsVisibles(infoCatalogue, ed) {
  const retraits = new Set(ed.retraits[infoCatalogue.id] || []);
  const ids = (infoCatalogue.ids || '').split(' ').filter(id => id && !retraits.has(id));
  for (const f of ed.ajouts[infoCatalogue.id] || []) ids.push(f.id);
  return ids;
}

/* ---------- fiches ---------- */
export function modifierFiche(ed, liste, idFiche, valeurs, image) {
  const perso = listePerso(ed, liste.id);
  if (perso) {
    const f = perso.fiches.find(x => x.id === idFiche);
    if (!f) return;
    f.valeurs = valeurs;
    if (image !== undefined) f.image = image;
    return;
  }
  const ajout = (ed.ajouts[liste.id] || []).find(x => x.id === idFiche);
  if (ajout) { ajout.valeurs = valeurs; if (image !== undefined) ajout.image = image; return; }
  const m = (ed.modifs[liste.id] ||= {});
  m[idFiche] = {...m[idFiche], valeurs};
  if (image !== undefined) m[idFiche].image = image;
}

export function retablirFiche(ed, idListe, idFiche) {
  if (ed.modifs[idListe]) {
    delete ed.modifs[idListe][idFiche];
    if (!Object.keys(ed.modifs[idListe]).length) delete ed.modifs[idListe];
  }
}

export function ajouterFiche(ed, liste, valeurs, image) {
  const f = {id: nouvelId('f'), valeurs};
  if (image) f.image = image;
  const perso = listePerso(ed, liste.id);
  if (perso) perso.fiches.push(f);
  else (ed.ajouts[liste.id] ||= []).push(f);
  return f;
}

export function supprimerFiche(ed, idListe, idFiche) {
  const perso = listePerso(ed, idListe);
  if (perso) { perso.fiches = perso.fiches.filter(f => f.id !== idFiche); return; }
  const ajouts = ed.ajouts[idListe] || [];
  if (ajouts.some(f => f.id === idFiche)) { ed.ajouts[idListe] = ajouts.filter(f => f.id !== idFiche); return; }
  retablirFiche(ed, idListe, idFiche);
  const r = (ed.retraits[idListe] ||= []);
  if (!r.includes(idFiche)) r.push(idFiche);
}

export function restaurerFichesRetirees(ed, idListe) {
  const n = (ed.retraits[idListe] || []).length;
  delete ed.retraits[idListe];
  return n;
}

/** Les photos importées encore utilisées, pour faire le ménage. */
export function imagesUtilisees(ed) {
  const out = new Set();
  const voir = f => { if (String(f.image || '').startsWith('perso:')) out.add(f.image.slice(6)); };
  ed.perso.forEach(l => l.fiches.forEach(voir));
  Object.values(ed.ajouts).forEach(fs => fs.forEach(voir));
  Object.values(ed.modifs).forEach(m => Object.values(m).forEach(voir));
  return out;
}

/* ---------- listes personnelles ---------- */
export function creerListe(ed, {nom, icone, categorie, colonnes, lignes = []}) {
  const cols = colonnes.map(c => String(c).trim()).filter(Boolean);
  if (!String(nom || '').trim()) throw new Error('Donne un nom à la liste.');
  if (!cols.length) throw new Error('Il faut au moins une colonne.');
  const l = {id: `perso-${slug(nom)}-${Date.now().toString(36)}`, nom: String(nom).trim(), icone: String(icone || '📋').trim() || '📋',
    categorie: categorie || CATEGORIE_PERSO, colonnes: cols, cle: 0, fiches: [], cree: new Date().toISOString()};
  for (const v of lignes) if (String(v[0] || '').trim()) l.fiches.push({id: nouvelId('f'), valeurs: cols.map((c, i) => String(v[i] ?? '').trim())});
  ed.perso.push(l);
  return l;
}

export function modifierListe(ed, idListe, {nom, icone, categorie}) {
  const l = listePerso(ed, idListe);
  if (!l) return;
  if (String(nom || '').trim()) l.nom = String(nom).trim();
  if (String(icone || '').trim()) l.icone = String(icone).trim();
  if (categorie) l.categorie = categorie;
}

export function supprimerListe(ed, idListe) {
  ed.perso = ed.perso.filter(l => l.id !== idListe);
}

/* ---------- tableau collé ou fichier CSV ---------- */
/**
 * Lit un tableau collé depuis un tableur (tabulations) ou un CSV (point-virgule
 * ou virgule). Rend {colonnes, lignes} : la première ligne donne les colonnes.
 */
export function lireTableau(texte) {
  const [colonnes, ...lignes] = lireLignes(texte);
  return {colonnes: colonnes || [], lignes};
}

/** Toutes les lignes non vides d'un tableau collé, sans traiter la première à part. */
export function lireLignes(texte) {
  const brut = String(texte || '').replace(/\r\n?/g, '\n').trim();
  if (!brut) return [];
  const premiere = brut.split('\n')[0];
  const sep = premiere.includes('\t') ? '\t' : (premiere.split(';').length >= premiere.split(',').length ? ';' : ',');
  const lignes = [];
  let ligne = [], champ = '', guillemets = false;
  for (let i = 0; i < brut.length; i++) {
    const c = brut[i];
    if (guillemets) {
      if (c === '"' && brut[i + 1] === '"') { champ += '"'; i++; }
      else if (c === '"') guillemets = false;
      else champ += c;
    } else if (c === '"' && champ === '') guillemets = true;
    else if (c === sep) { ligne.push(champ.trim()); champ = ''; }
    else if (c === '\n') { ligne.push(champ.trim()); lignes.push(ligne); ligne = []; champ = ''; }
    else champ += c;
  }
  ligne.push(champ.trim()); lignes.push(ligne);
  return lignes.filter(l => l.some(Boolean));
}

/* ---------- reprise des listes de l'ancienne version ---------- */
// L'ancienne version range ses listes sous « memo_v62_local_lists » (même
// domaine) : colonne 0 = numéro, colonne 1 = image, puis le texte.
export function listesAnciennes(stockage) {
  try {
    const ls = JSON.parse(stockage.getItem('memo_v62_local_lists') || '[]');
    return Array.isArray(ls) ? ls.filter(l => l && l._source === 'custom' && Array.isArray(l.columns) && Array.isArray(l.rows)) : [];
  } catch { return []; }
}

export function reprendreAncienne(ed, ancienne) {
  if (ed.perso.some(l => l.ancienneId === ancienne.id)) return null;
  const sansImage = !!ancienne.noImage;
  const debut = sansImage ? 1 : 2;
  const colonnes = ancienne.columns.slice(debut).map(c => String(c || '').trim() || 'Colonne');
  const l = creerListe(ed, {nom: ancienne.name || 'Liste reprise', icone: ancienne.icon || '📋', colonnes: colonnes.length ? colonnes : ['Nom']});
  l.ancienneId = ancienne.id;
  for (const r of ancienne.rows) {
    const valeurs = colonnes.map((c, i) => String(r[debut + i] ?? '').trim());
    if (!valeurs.some(Boolean)) continue;
    const f = {id: nouvelId('f'), valeurs};
    const img = String(r[1] || '').trim();
    // une photo web, une image de Mnémo ou une photo importée (rangée ensuite à part)
    if (!sansImage && /^(https?:|thumbs\/|full\/|data:image\/(?!svg))/.test(img)) f.image = img;
    l.fiches.push(f);
  }
  return l;
}
