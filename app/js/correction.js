// Correction d'une réponse tapée.
//
// Le propriétaire tape ses réponses (pas de propositions). La correction doit
// être tolérante sans devenir complaisante : accents, majuscules, articles et
// une ou deux fautes de frappe sont pardonnés ; le reste est faux. En cas de
// désaccord, l'écran propose de renverser le verdict : ce module ne tranche pas
// seul les cas limites, il donne un premier avis.

const ARTICLES = /^(le|la|les|l|un|une|des|du|de la|de l|d|the)\s+/;

export function norm(s) {
  return String(s || '').toLowerCase().replace(/œ/g, 'oe').replace(/æ/g, 'ae')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/['’`]/g, ' ').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim()
    .replace(ARTICLES, '').trim();
}

// Distance de Levenshtein : nombre de lettres à changer, ajouter ou retirer
export function distance(a, b) {
  const m = a.length, n = b.length;
  if (!m) return n;
  if (!n) return m;
  let prec = Array.from({length: n + 1}, (_, j) => j);
  for (let i = 1; i <= m; i++) {
    const cur = [i];
    for (let j = 1; j <= n; j++) cur[j] = Math.min(prec[j] + 1, cur[j - 1] + 1, prec[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    prec = cur;
  }
  return prec[n];
}

// Formes acceptées : chaque élément d'une liste « A · B », sans parenthèses,
// et, pour un nom de personne, le dernier mot s'il est assez long (« Monet »).
export function formes(attendu, estNom) {
  const out = new Set();
  for (const partie of String(attendu).split(/\s·\s|\s\/\s|,\s/)) {
    const sansPar = partie.replace(/\([^)]*\)/g, ' ');
    for (const v of [partie, sansPar]) {
      const n = norm(v);
      if (!n) continue;
      out.add(n);
      const mots = n.split(' ');
      if (estNom && mots.length > 1 && mots[mots.length - 1].length >= 4) out.add(mots[mots.length - 1]);
    }
  }
  return [...out];
}

function corrigerUn(t, attendu, estNom) {
  // une année se juge à l'exact : 1914 n'est pas 1915
  const annees = String(attendu).match(/\d{3,4}/g);
  if (annees && /^\d{3,4}$/.test(t)) return annees.includes(t) ? {verdict: 'juste'} : {verdict: 'faux'};
  let meilleure = Infinity;
  for (const f of formes(attendu, estNom)) {
    if (t === f) return {verdict: 'juste'};
    const tol = f.length <= 4 ? 0 : f.length <= 8 ? 1 : 2;
    const d = distance(t, f);
    if (d <= tol) meilleure = Math.min(meilleure, d);
  }
  return meilleure < Infinity ? {verdict: 'juste', presque: true} : {verdict: 'faux'};
}

/** Rend {verdict: 'juste'|'faux', presque?: true} */
export function corriger(tape, attendu, estNom = false) {
  if (!norm(tape)) return {verdict: 'faux', vide: true};
  if (norm(tape) === norm(attendu)) return {verdict: 'juste'};
  // plusieurs éléments tapés (« Monet, Renoir ») : un seul élément juste suffit
  const morceaux = String(tape).split(/\s*[,;·]\s*|\s+et\s+/).filter(m => norm(m));
  let presque = false;
  for (const m of morceaux) {
    const r = corrigerUn(norm(m), attendu, estNom);
    if (r.verdict === 'juste' && !r.presque) return r;
    if (r.verdict === 'juste') presque = true;
  }
  return presque ? {verdict: 'juste', presque: true} : {verdict: 'faux'};
}
