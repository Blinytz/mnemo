// Mémoire de chaque fiche : boîtes de Leitner à cinq niveaux.
//
// Une fiche réussie monte d'une boîte et revient de plus en plus tard ; une
// erreur la renvoie en boîte 1, à revoir le lendemain. Une fiche jamais vue est
// en boîte 0. Tout est rangé sous une seule clé du stockage local, préfixée
// « memo2- » : le domaine blinytz.github.io est partagé par toutes les applis.
//
// Des listes peuvent apparaître ou disparaître d'une version à l'autre. La
// progression d'une fiche retirée n'est jamais effacée (elle reviendrait avec
// sa liste) ; les calculs prennent un filtre « garde » qui ne laisse passer que
// les fiches encore présentes.

export const CLE_STOCKAGE = 'memo2-etat';
export const INTERVALLES = [1, 3, 7, 16, 35];     // jours d'attente après la boîte 1, 2, 3, 4, 5
export const OBJECTIF_JOUR = 20;                   // réponses pour valider une journée de série
export const LIBELLES = ['Jamais vue', 'À revoir', 'Fragile', 'En cours', 'Solide', 'Acquise'];

/* ---------- dates : un jour = un entier, en heure locale ---------- */
export function jourDe(date = new Date()) {
  return Math.round(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 864e5);
}
export function texteDuJour(j) {
  return new Date(j * 864e5).toISOString().slice(0, 10);
}

/* ---------- état ---------- */
export function etatVide() {
  return {v: 1, fiches: {}, suivies: [], derniere: null, jours: {}, quiz: null, eclats: {journal: []},
    reglages: {}, rotation: {listes: {}, fiches: {}}, catalogue: {connues: null, apparues: {}}};
}

export function charger(stockage) {
  try {
    const brut = JSON.parse(stockage.getItem(CLE_STOCKAGE) || 'null');
    if (brut && brut.v === 1) {
      const vide = etatVide();
      return {...vide, ...brut, rotation: {...vide.rotation, ...brut.rotation}, catalogue: {...vide.catalogue, ...brut.catalogue}};
    }
  } catch {}
  return etatVide();
}

export function sauver(stockage, etat) {
  try { stockage.setItem(CLE_STOCKAGE, JSON.stringify(etat)); return true; } catch { return false; }
}

/* ---------- lecture ---------- */
export const cleFiche = (idListe, idFiche) => `${idListe}/${idFiche}`;
export const boite = (etat, cle) => etat.fiches[cle]?.b || 0;
export const estDue = (etat, cle, aujourdhui) => {
  const f = etat.fiches[cle];
  return !!f && f.b >= 1 && f.d <= aujourdhui;
};

const tout = () => true;

export function maitrise(etat, idListe, nbFiches, garde = tout) {
  if (!nbFiches) return 0;
  let s = 0;
  const prefixe = idListe + '/';
  for (const [cle, f] of Object.entries(etat.fiches)) if (cle.startsWith(prefixe) && garde(cle)) s += f.b;
  return Math.round(100 * s / (5 * nbFiches));
}

/** Clés des fiches dues aujourd'hui, les plus en retard d'abord. */
export function fichesDues(etat, aujourdhui, garde = tout) {
  return Object.entries(etat.fiches)
    .filter(([cle, f]) => f.b >= 1 && f.d <= aujourdhui && garde(cle))
    .sort((a, b) => a[1].d - b[1].d || a[1].b - b[1].b)
    .map(([cle]) => cle);
}

export function repartition(etat, garde = tout) {
  const n = [0, 0, 0, 0, 0, 0];
  for (const [cle, f] of Object.entries(etat.fiches)) if (garde(cle)) n[f.b]++;
  return n;
}

/** Fiches dont la progression est gardée mais qui ne sont plus au catalogue. */
export const misesDeCote = (etat, garde) => Object.keys(etat.fiches).filter(cle => !garde(cle)).length;

/**
 * Note les listes apparues depuis la dernière visite. Au tout premier
 * lancement, rien n'est « nouveau ». Rend les identifiants des nouvelles.
 */
export function noterCatalogue(etat, ids, aujourdhui) {
  const c = etat.catalogue;
  if (!c.connues) { c.connues = [...ids]; return []; }
  const connues = new Set(c.connues), neuves = ids.filter(id => !connues.has(id));
  for (const id of neuves) c.apparues[id] = aujourdhui;
  c.connues = [...new Set([...c.connues, ...ids])];
  return neuves;
}
export const estNouvelleListe = (etat, id, aujourdhui, duree = 14) =>
  etat.catalogue.apparues[id] !== undefined && aujourdhui - etat.catalogue.apparues[id] < duree;

/* ---------- écriture ---------- */
/** Applique une réponse. Rend l'état d'avant, pour pouvoir annuler. */
export function noter(etat, cle, juste, aujourdhui) {
  const avant = etat.fiches[cle] ? {...etat.fiches[cle]} : null;
  const b0 = avant?.b || 0;
  // une fiche nouvelle trouvée du premier coup saute la boîte 1
  const b = juste ? (b0 === 0 ? 2 : Math.min(5, b0 + 1)) : 1;
  etat.fiches[cle] = {b, d: aujourdhui + INTERVALLES[b - 1], n: (avant?.n || 0) + 1};
  return avant;
}

/** Revient sur une réponse : repart de l'état d'avant et applique l'autre verdict. */
export function renoter(etat, cle, avant, juste, aujourdhui) {
  if (avant) etat.fiches[cle] = {...avant}; else delete etat.fiches[cle];
  noter(etat, cle, juste, aujourdhui);
  // la réponse a déjà été comptée une fois
  etat.fiches[cle].n = avant?.n ? avant.n + 1 : 1;
}

/** Compte une réponse dans la journée : {n: réponses, ok: réussites}. */
export function compterReponse(etat, aujourdhui, juste) {
  const t = texteDuJour(aujourdhui);
  const j = etat.jours[t] || (etat.jours[t] = {n: 0, ok: 0});
  j.n++;
  if (juste) j.ok++;
}
/** Un verdict renversé change le nombre de réussites, pas le nombre de réponses. */
export function recompterReponse(etat, aujourdhui, juste) {
  const j = etat.jours[texteDuJour(aujourdhui)];
  if (j) j.ok = Math.max(0, j.ok + (juste ? 1 : -1));
}
export const reponsesDuJour = (etat, j) => etat.jours[texteDuJour(j)]?.n || 0;

/** Taux de réussite sur les n derniers jours, ou null sans réponse. */
export function reussite(etat, aujourdhui, n = 7) {
  let tot = 0, ok = 0;
  for (let j = aujourdhui - n + 1; j <= aujourdhui; j++) {
    const x = etat.jours[texteDuJour(j)];
    if (x) { tot += x.n; ok += x.ok; }
  }
  return tot ? Math.round(100 * ok / tot) : null;
}

export function suivre(etat, idListe) {
  if (!etat.suivies.includes(idListe)) etat.suivies.push(idListe);
}

/* ---------- série ---------- */
export function serie(etat, aujourdhui) {
  const fait = j => reponsesDuJour(etat, j) >= OBJECTIF_JOUR;
  // la journée en cours ne casse pas la série tant qu'elle n'est pas finie
  let j = fait(aujourdhui) ? aujourdhui : aujourdhui - 1, n = 0;
  while (fait(j)) { n++; j--; }
  return n;
}

export function record(etat) {
  const jours = Object.entries(etat.jours).filter(([, x]) => x.n >= OBJECTIF_JOUR)
    .map(([t]) => jourDe(new Date(t + 'T12:00:00'))).sort((a, b) => a - b);
  let best = 0, cur = 0, prec = null;
  for (const j of jours) { cur = prec !== null && j === prec + 1 ? cur + 1 : 1; best = Math.max(best, cur); prec = j; }
  return best;
}
