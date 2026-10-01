// Fabrication des questions à partir d'une fiche.
//
// Trois formes, toutes à réponse tapée :
//   image  : l'image est montrée, on demande ce qui nomme la fiche ;
//   champ  : la fiche est nommée, on demande une de ses colonnes courtes ;
//   indice : (listes sans image) une colonne sert d'indice, on demande le nom.
// Une question est rangée sous une forme courte {l, f, t, c} pour survivre à un
// rechargement de la page ; tout le reste se recalcule depuis la liste.

// Une réponse qu'on peut raisonnablement taper : courte, peu de mots
// (« Aucune connue » ou un tiret ne sont pas des réponses)
const tapable = v => v && v.length <= 40 && v.split(/\s+/).length <= 5
  && !/^(aucun|inconnu|non |n\/a|[-–—?])/i.test(v) && !/\(aucun/i.test(v);

// Une colonne où la même réponse revient pour plus de 40 % des fiches (« AOP »,
// « Vache », « Nord ») se devine sans rien savoir : on ne la demande pas.
const triviales = new WeakMap();
function colonnesTriviales(liste) {
  if (!triviales.has(liste)) {
    const out = new Set();
    liste.colonnes.forEach((c, i) => {
      const compte = new Map();
      for (const f of liste.fiches) {
        const v = String(f.valeurs[i] || '').replace(/\([^)]*\)/g, '').trim().toLowerCase();
        if (v) compte.set(v, (compte.get(v) || 0) + 1);
      }
      if (Math.max(0, ...compte.values()) > 0.4 * liste.fiches.length) out.add(i);
    });
    triviales.set(liste, out);
  }
  return triviales.get(liste);
}

// Colonnes qui décrivent plus qu'elles ne nomment : bonnes à lire, impossibles
// à retrouver mot pour mot. Elles servent d'indice, jamais de réponse.
const DESCRIPTIVES = /rep[eè]re|fait marquant|description|caract[ée]ristiques|combat|action|r[oô]le|pouvoir|exemple|[ée]v[ée]nement|ce qu.il [ée]tablit|concepts|apport|surnom|d[ée]finition|repr[ée]sente|ingr[ée]dients|finale|construction/i;

export function colonnesDemandables(liste, fiche) {
  const nom = fiche.valeurs[liste.cle] || '', exclues = colonnesTriviales(liste);
  return liste.colonnes.map((c, i) => i)
    .filter(i => i !== liste.cle && !exclues.has(i) && !DESCRIPTIVES.test(liste.colonnes[i])
      && tapable(fiche.valeurs[i]) && !nom.includes(fiche.valeurs[i]));
}

/** Tire une question pour une fiche. hasard() rend un nombre entre 0 et 1. */
export function tirerQuestion(liste, fiche, hasard = Math.random) {
  const champs = colonnesDemandables(liste, fiche);
  const auHasard = a => a[Math.floor(hasard() * a.length)];
  if (fiche.image) {
    if (champs.length && hasard() < .45) return {l: liste.id, f: fiche.id, t: 'champ', c: auHasard(champs)};
    return {l: liste.id, f: fiche.id, t: 'image'};
  }
  // sans image : l'indice est la première colonne assez parlante
  const indice = liste.colonnes.findIndex((c, i) => i !== liste.cle && (fiche.valeurs[i] || '').length >= 12);
  if (indice >= 0 && (!champs.length || hasard() < .6)) return {l: liste.id, f: fiche.id, t: 'indice', c: indice};
  if (champs.length) return {l: liste.id, f: fiche.id, t: 'champ', c: auHasard(champs)};
  return null;
}

/** Tout ce qu'il faut pour afficher et corriger une question. */
export function deplier(q, liste) {
  const fiche = liste.fiches.find(f => f.id === q.f);
  if (!fiche) return null;
  const nom = fiche.valeurs[liste.cle];
  const base = {q, liste, fiche, nom};
  if (q.t === 'champ') return {...base, enonce: `${liste.colonnes[q.c]} ?`, bonne: fiche.valeurs[q.c], estNom: false};
  if (q.t === 'indice') return {...base, enonce: `${liste.colonnes[liste.cle]} ?`, indice: {titre: liste.colonnes[q.c], texte: fiche.valeurs[q.c]}, bonne: nom, estNom: true};
  return {...base, enonce: `${liste.colonnes[liste.cle]} ?`, bonne: nom, estNom: true};
}

export function melanger(a, hasard = Math.random) {
  const b = [...a];
  for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(hasard() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; }
  return b;
}

/* ---------- rotation du quiz du jour ---------- */
// Le quiz tient la date à laquelle chaque liste et chaque fiche ont été posées.
// Il prend d'abord les listes jamais posées ou posées il y a le plus longtemps,
// puis, dans chaque liste, la fiche la moins récemment posée : les 79 listes
// passent en quatre jours, et une fiche ne revient qu'une fois toutes les
// autres de sa liste posées. Le hasard ne départage que les ex aequo.
const anciennete = date => date ?? -Infinity;

export function parAnciennete(cles, dates, hasard = Math.random) {
  // (pas de soustraction : -Infinity moins -Infinity ne donne pas zéro)
  return melanger(cles, hasard).sort((a, b) => {
    const x = anciennete(dates[a]), y = anciennete(dates[b]);
    return x === y ? 0 : x < y ? -1 : 1;
  });
}

/**
 * Tire les questions du quiz. listes : listes chargées, déjà rangées par
 * ancienneté ; rotation : {listes, fiches} ; rend [{l, f, t, c}].
 */
export function tirerQuiz(listes, rotation, nombre, hasard = Math.random) {
  const questions = [];
  for (const l of listes) {
    if (questions.length >= nombre) break;
    const ids = parAnciennete(l.fiches.map(f => f.id), Object.fromEntries(l.fiches.map(f => [f.id, rotation.fiches[`${l.id}/${f.id}`]])), hasard);
    for (const id of ids) {
      const q = tirerQuestion(l, l.fiches.find(f => f.id === id), hasard);
      if (q) { questions.push(q); break; }
    }
  }
  return questions;
}

/** Note dans la rotation ce que le quiz vient de poser. */
export function noterRotation(rotation, questions, jour) {
  for (const q of questions) { rotation.listes[q.l] = jour; rotation.fiches[`${q.l}/${q.f}`] = jour; }
}
