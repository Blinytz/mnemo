// Éclats de Mnémo : seul le quiz du jour en rapporte, selon un barème.
//
// Le barème est réglable par l'utilisateur (écran Réglages). Un quiz fige le
// barème en vigueur à son lancement : le changer en cours de route ne modifie
// pas ce que rapporte le quiz commencé.
//
// Le solde est tenu localement, derrière la même idée que le registre commun :
// chaque crédit porte une clé unique (une par jour pour le quiz), si bien qu'un
// même quiz ne peut pas être payé deux fois. Le branchement sur le registre
// (RPC eclats_reward, idempotente sur cette même clé) viendra remplacer le
// journal local sans toucher aux écrans.

export const QUESTIONS_QUIZ = 20;
export const GAIN_MAX = 10000;
// [à partir de n bonnes réponses, Éclats gagnés] ; en dessous du premier palier, rien
export const BAREME_DEFAUT = [[10, 10], [13, 25], [16, 45], [18, 75], [20, 120]];

/**
 * Remet un barème saisi en ordre : seuils entiers de 1 à 20, sans doublon,
 * triés ; gains entiers de 0 à GAIN_MAX. Rend null si rien n'est utilisable.
 */
export function normaliserBareme(lignes) {
  if (!Array.isArray(lignes)) return null;
  const parSeuil = new Map();
  for (const l of lignes) {
    const seuil = Math.round(Number(l?.[0])), gain = Math.round(Number(l?.[1]));
    if (!Number.isFinite(seuil) || !Number.isFinite(gain)) continue;
    if (seuil < 1 || seuil > QUESTIONS_QUIZ) continue;
    parSeuil.set(seuil, Math.min(GAIN_MAX, Math.max(0, gain)));
  }
  const out = [...parSeuil].sort((a, b) => a[0] - b[0]);
  return out.length ? out : null;
}

export const baremeEnVigueur = etat => normaliserBareme(etat.reglages?.bareme) || BAREME_DEFAUT;
export const baremeDuQuiz = (etat, quiz) => normaliserBareme(quiz?.bareme) || baremeEnVigueur(etat);

export const gainPour = (n, bareme = BAREME_DEFAUT) => bareme.reduce((g, [seuil, e]) => n >= seuil ? e : g, 0);

/** Paliers prêts à afficher, palier « rien » compris : {libelle, seuil, fin, gain}. */
export function paliers(bareme = BAREME_DEFAUT) {
  const complet = bareme[0][0] > 0 ? [[0, 0], ...bareme] : bareme;
  return complet.map(([seuil, gain], i) => {
    const fin = (complet[i + 1]?.[0] ?? QUESTIONS_QUIZ + 1) - 1;
    const libelle = seuil === fin ? String(seuil) : fin === seuil + 1 ? `${seuil} ou ${fin}` : `${seuil} à ${fin}`;
    return {libelle, seuil, fin, gain};
  });
}

export const solde = etat => etat.eclats.journal.reduce((s, e) => s + e.montant, 0);

/** Inscrit un gain une seule fois par clé. Rend true si le gain est nouveau. */
export function crediter(etat, cle, montant, motif, details = {}) {
  if (!montant || etat.eclats.journal.some(e => e.cle === cle)) return false;
  etat.eclats.journal.push({cle, montant, motif, quand: new Date().toISOString(), ...details, collecte: null});
  return true;
}

/* ---------- collecte dans le registre commun ---------- */
// Comme dans Sport et Missions, rien ne part tout seul : un gain reste « à
// collecter » tant que l'utilisateur ne l'a pas versé. Le registre d'abord,
// l'état local ensuite : la clé d'idempotence (une par jour de quiz) fait
// qu'un double clic ou une coupure réseau rejoue la même écriture sans
// créer un second mouvement.

export const aCollecter = etat => etat.eclats.journal.filter(e => !e.collecte);
export const montantACollecter = etat => aCollecter(etat).reduce((s, e) => s + e.montant, 0);

export async function collecter(etat, registre, cle, maintenant = () => new Date()) {
  const e = etat.eclats.journal.find(x => x.cle === cle);
  if (!e || e.collecte) return e;
  if (!registre.estConnecte()) throw new Error('Connecte-toi au registre commun pour verser tes Éclats.');
  const reponse = await registre.recompenser({
    montant: e.montant,
    reason: e.jour ? `Quiz du jour du ${e.jour} : ${e.score} / ${QUESTIONS_QUIZ}` : e.motif,
    referenceType: 'quiz_memo',
    referenceId: null,                    // le registre attend un uuid : le jour part en metadata
    idempotencyKey: e.cle,
    metadata: {jour: e.jour ?? null, score: e.score ?? null, bareme: e.bareme ?? null},
  });
  e.collecte = {quand: maintenant().toISOString(), mouvementId: reponse?.movement_id || null, soldeApres: reponse?.balance_after ?? null};
  return e;
}

/** Verse tous les gains en attente ; rend {verses, montant, erreur}. */
export async function toutCollecter(etat, registre) {
  let verses = 0, montant = 0;
  for (const e of aCollecter(etat)) {
    try { await collecter(etat, registre, e.cle); verses++; montant += e.montant; }
    catch (erreur) { return {verses, montant, erreur}; }
  }
  return {verses, montant, erreur: null};
}

export function gagnesDepuis(etat, depuis) {
  return etat.eclats.journal.filter(e => e.quand >= depuis).reduce((s, e) => s + e.montant, 0);
}
