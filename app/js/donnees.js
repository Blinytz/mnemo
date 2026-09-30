// Chargement des données : le catalogue au démarrage, chaque liste à la demande.
// Les fichiers sont produits par build/exporter_donnees.mjs.

// Racine de Mémo vue depuis cette page (l'application vit dans app/ tant que
// l'ancienne version reste en place)
export const RACINE = new URL('../', document.baseURI).href;
export const chemin = p => p ? new URL(p, RACINE).href : '';

let catalogue = null;
const listes = new Map();

async function lireJson(p) {
  const r = await fetch(chemin(p), {cache: 'no-cache'});
  if (!r.ok) throw new Error(`${p} : ${r.status}`);
  return r.json();
}

export async function chargerCatalogue() {
  catalogue = await lireJson('data/catalogue.json');
  catalogue.parId = new Map(catalogue.listes.map(l => [l.id, l]));
  return catalogue;
}
export const leCatalogue = () => catalogue;

export async function chargerListe(id) {
  if (!listes.has(id)) listes.set(id, lireJson(`data/listes/${id}.json`).catch(e => { listes.delete(id); throw e; }));
  return listes.get(id);
}
export const chargerListes = ids => Promise.all([...new Set(ids)].map(chargerListe));
