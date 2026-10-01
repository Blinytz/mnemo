// Éclats de Mémo : seul le quiz du jour en rapporte, selon un barème.
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

/** Crédite une seule fois par clé. Rend true si le crédit est nouveau. */
export function crediter(etat, cle, montant, motif) {
  if (!montant || etat.eclats.journal.some(e => e.cle === cle)) return false;
  etat.eclats.journal.push({cle, montant, motif, quand: new Date().toISOString()});
  return true;
}

export function gagnesDepuis(etat, depuis) {
  return etat.eclats.journal.filter(e => e.quand >= depuis).reduce((s, e) => s + e.montant, 0);
}
