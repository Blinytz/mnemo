// Sort les listes de Mémo de memo.html vers des fichiers de données propres.
//
//   node build/exporter_donnees.mjs
//
// memo.html reste pour l'instant la source : l'Atelier et le générateur des
// listes WikiDeck y écrivent. Ce script évalue la partie « données » du fichier,
// exactement comme l'application au chargement, puis écrit :
//   data/catalogue.json        catégories et résumé de chaque liste
//   data/listes/<id>.json      les fiches d'une liste
// À relancer après chaque modification des listes ou des images.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const racine = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = fs.readFileSync(path.join(racine, 'memo.html'), 'utf8');
const L = html.split('\n');
const ligne = motif => {
  const i = L.findIndex(l => l.includes(motif));
  if (i < 0) throw new Error(`repère introuvable dans memo.html : ${motif}`);
  return i;
};

/* ---------- 1. Évaluer les données comme le fait l'application ---------- */
const code = [
  ...L.slice(ligne('/* ══════════ STORAGE ══════════ */'), ligne('let lists        = normalizeStoredLists')),
  ...L.slice(ligne('const DEFAULT_CATEGORIES = ['), ligne('function normalizeCategories')),
  L[ligne('const IMAGE_FILES_MAP = ')],
  `globalThis.__sortie = { listes: cloneDefaultLists(), categories: DEFAULT_CATEGORIES,
     parListe: DEFAULT_CATEGORY_BY_LIST, grandes: IMAGE_FILES_MAP,
     wikideck: typeof WIKIDECK_LIST_IDS !== 'undefined' ? [...WIKIDECK_LIST_IDS] : [] };`,
].join('\n');
const magasin = new Map();
const ctx = { console, localStorage: { getItem: k => magasin.get(k) ?? null, setItem: (k, v) => magasin.set(k, String(v)), removeItem: k => magasin.delete(k) } };
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(code, ctx, { filename: 'memo.html (données)' });
const S = ctx.__sortie;

/* ---------- liens Wikipédia des cartes WikiDeck ---------- */
// La table LISTES du générateur relie chaque collection WikiDeck à sa liste Mémo ;
// les cartes de la collection portent le lien exact vers leur article.
const liens = new Map();                         // idListe -> Map(clé d'image -> lien)
const wikideck = path.join(racine, '..', 'wikideck', 'data');
const generateur = fs.readFileSync(path.join(racine, 'build', 'listes_wikideck.py'), 'utf8');
for (const [, collection, idListe] of generateur.matchAll(/'([a-z0-9-]+)':\s*dict\(id='([a-z0-9_]+)'/g)) {
  const fichier = path.join(wikideck, `${collection}.json`);
  if (!fs.existsSync(fichier)) continue;
  const m = new Map();
  for (const c of JSON.parse(fs.readFileSync(fichier, 'utf8')).cartes || [])
    if (c.lienWikipedia) m.set(c.id.split('_').slice(1).join('_'), c.lienWikipedia);
  liens.set(idListe, m);
}
// Sans le dossier WikiDeck (au déploiement, sur GitHub), on reprend les liens
// déjà présents dans les données précédentes, fiche par fiche
const liensPrecedents = new Map();             // « liste/fiche » -> lien
if (!liens.size) {
  const avant = path.join(racine, 'data', 'listes');
  if (fs.existsSync(avant)) for (const f of fs.readdirSync(avant)) {
    const l = JSON.parse(fs.readFileSync(path.join(avant, f), 'utf8'));
    for (const x of l.fiches) if (x.wiki) liensPrecedents.set(`${l.id}/${x.id}`, x.wiki);
  }
  console.log(`Dossier wikideck/data absent : ${liensPrecedents.size} liens Wikipédia repris des données précédentes.`);
}

/* ---------- 2. Mettre en forme ---------- */
// Colonne qui nomme la fiche, quand ce n'est pas la première colonne de texte
const CLE = { films: 'Titre', consoles: 'Console', periodes_geologiques: 'Période', coupes_monde: 'Édition', jo_ete: 'Édition', jo_hiver: 'Édition' };
// Listes dont les images sont des cartons de texte générés : aucune valeur de quiz
const SANS_IMAGE = new Set(['phrasal_verbs']);
const DRAPEAU = /^[\u{1F1E6}-\u{1F1FF}]{2}\s*/u;

const slug = s => String(s).toLowerCase().replace(/œ/g, 'oe').replace(/æ/g, 'ae')
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'x';
const estImage = v => /^(thumbs\/|full\/|data:image|https?:)/.test(String(v || ''));

const catalogue = { note: 'Fichier produit par build/exporter_donnees.mjs à partir de memo.html : ne pas modifier à la main.',
  categories: S.categories.map(c => ({ id: c.id, nom: c.name, icone: c.icon })), listes: [] };
const dossier = path.join(racine, 'data', 'listes');
fs.rmSync(dossier, { recursive: true, force: true });
fs.mkdirSync(dossier, { recursive: true });

const problemes = [];
for (const l of S.listes) {
  const avecImage = !l.noImage && !SANS_IMAGE.has(l.id);
  const debut = l.noImage ? 1 : 2;                 // 0 = numéro, 1 = image
  // colonnes d'images secondaires (cartes de localisation)
  const secondaires = l.columns.map((c, i) => i >= debut && l.rows.some(r => estImage(r[i])) ? i : -1).filter(i => i >= 0);
  const texte = l.columns.map((c, i) => i).filter(i => i >= debut && !secondaires.includes(i));
  const colonnes = texte.map(i => l.columns[i]);
  let cle = CLE[l.id] ? colonnes.indexOf(CLE[l.id]) : 0;
  if (cle < 0) { problemes.push(`${l.id} : colonne ${CLE[l.id]} absente`); cle = 0; }

  const pris = new Map();
  const fiches = l.rows.map((r, ri) => {
    const valeurs = texte.map(i => String(r[i] ?? '').trim());
    if (l.id === 'pays') valeurs[cle] = valeurs[cle].replace(DRAPEAU, '');
    // identifiant stable, qui porte la progression : la clé de l'image quand il y
    // en a une (elle ne bouge ni quand la liste est retriée, ni quand un nom est
    // corrigé), sinon le nom
    const cleImage = String(r[1] || '').match(/^thumbs\/[^/]+\/([^/.]+)\.[a-z0-9]+$/i)?.[1];
    let id = avecImage && cleImage ? slug(cleImage) : slug(valeurs[cle] || r[0] || ri + 1);
    const n = (pris.get(id) || 0) + 1; pris.set(id, n);
    if (n > 1) id += '-' + n;
    const fiche = { id, valeurs };
    if (avecImage && r[1]) {
      fiche.image = r[1];
      const m = String(r[1]).match(/^thumbs\/[^/]+\/([^/.]+)\.[a-z0-9]+$/i);
      const grande = m && S.grandes[l.id]?.[m[1]];
      if (grande) fiche.grande = grande;
      if (!fs.existsSync(path.join(racine, r[1]))) problemes.push(`${l.id} : miniature absente ${r[1]}`);
    }
    if (secondaires.length) {
      fiche.carte = r[secondaires[0]];
      const k = String(fiche.carte).match(/^thumbs\/[^/]+\/([^/.]+)\.[a-z0-9]+$/i)?.[1];
      if (k && S.grandes[l.id]?.[k]) fiche.carteGrande = S.grandes[l.id][k];
    }
    const lien = (cleImage && liens.get(l.id)?.get(cleImage)) || liensPrecedents.get(`${l.id}/${id}`);
    if (lien) fiche.wiki = lien;
    if (!valeurs[cle]) problemes.push(`${l.id} : fiche ${ri + 1} sans nom`);
    return fiche;
  });

  const categorie = l.categoryId || S.parListe[l.id] || 'mes-listes';
  const donnee = { id: l.id, nom: l.name, icone: l.icon, categorie, colonnes, cle, fiches };
  if (l.source) donnee.source = l.source;
  fs.writeFileSync(path.join(dossier, `${l.id}.json`), JSON.stringify(donnee));
  catalogue.listes.push({ id: l.id, nom: l.name, icone: l.icon, categorie, colonnes, cle,
    fiches: fiches.length, images: avecImage, wikideck: S.wikideck.includes(l.id),
    apercu: fiches.filter(f => f.image).slice(0, 3).map(f => f.image),
    // identifiants des fiches : l'application y reconnaît les fiches retirées
    ids: fiches.map(f => f.id).join(' ') });
}
fs.writeFileSync(path.join(racine, 'data', 'catalogue.json'), JSON.stringify(catalogue, null, 1));

const total = catalogue.listes.reduce((n, l) => n + l.fiches, 0);
let avecLien = 0;
for (const l of catalogue.listes) avecLien += JSON.parse(fs.readFileSync(path.join(dossier, `${l.id}.json`), 'utf8')).fiches.filter(f => f.wiki).length;
console.log(`${catalogue.listes.length} listes, ${total} fiches écrites dans data/ (${avecLien} avec leur lien Wikipédia)`);
if (problemes.length) { console.log(`${problemes.length} point(s) à regarder :`); for (const p of problemes.slice(0, 40)) console.log(' - ' + p); }
