// Éclats de Mémo : seul le quiz du jour en rapporte, selon un barème.
//
// Le solde est tenu localement, derrière la même idée que le registre commun :
// chaque crédit porte une clé unique (une par jour pour le quiz), si bien qu'un
// même quiz ne peut pas être payé deux fois. Le branchement sur le registre
// (RPC eclats_reward, idempotente sur cette même clé) viendra remplacer le
// journal local sans toucher aux écrans.

export const QUESTIONS_QUIZ = 20;
// [à partir de n bonnes réponses, Éclats gagnés]
export const BAREME = [[0, 0], [10, 10], [13, 25], [16, 45], [18, 75], [20, 120]];

export const gainPour = n => BAREME.reduce((g, [seuil, e]) => n >= seuil ? e : g, 0);

/** Paliers prêts à afficher : {libelle, seuil, gain}. */
export function paliers() {
  return BAREME.map(([seuil, gain], i) => {
    const fin = (BAREME[i + 1]?.[0] ?? QUESTIONS_QUIZ + 1) - 1;
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
