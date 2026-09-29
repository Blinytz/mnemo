// Lecture et modification chirurgicale de memo.html.
//
// memo.html EST l'application. Deux choses y déterminent les images :
//   - la colonne 1 de chaque ligne de liste, qui porte le chemin de la
//     miniature « thumbs/<liste>/<clé>.<ext> » ;
//   - IMAGE_FILES_MAP, qui donne la grande image, indexée par <liste> puis par
//     la <clé> lue dans le nom de fichier de la miniature
//     (cf. localFullImageForThumb dans memo.html).
//
// Les listes arrivent par TROIS chemins qui se cumulent dans DEFAULT_LISTS :
// le littéral DEFAULT_LISTS et CURATED_LISTS_V3 sont du JSON, mais
// EXPANSION_LISTS est du JavaScript écrit à la main (clés nues, apostrophes,
// lignes construites par appel de fonction). Le ré-encoder serait risqué.
//
// D'où le choix retenu : l'Atelier n'écrit PAS dans les listes elles-mêmes. Il
// tient un bloc à part, ATELIER_IMAGES, appliqué à DEFAULT_LISTS au chargement.
// Un seul endroit à écrire, valable pour les trois provenances, et le travail
// de l'Atelier reste lisible d'un coup d'œil.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ici = path.dirname(fileURLToPath(import.meta.url));
export const RACINE = path.resolve(ici, '..');
export const MEMO_HTML = path.join(RACINE, 'memo.html');
const SAUVEGARDES = path.join(RACINE, 'backups');
const MAX_SAUVEGARDES = 20;

// Point d'insertion : juste après le dernier apport à DEFAULT_LISTS.
const ANCRE = 'DEFAULT_LISTS.push(...CURATED_LISTS_V3);';

const BLOC = (json) => `
/* ══════════ IMAGES DE L'ATELIER ══════════
   Bloc régénéré par l'Atelier (atelier/memo-html.mjs) : ne pas modifier à la
   main. Il porte les miniatures recadrées, par identifiant de liste puis par
   rang de ligne. Les grandes images correspondantes sont dans IMAGE_FILES_MAP. */
const ATELIER_IMAGES = ${json};
for (const [idListe, lignes] of Object.entries(ATELIER_IMAGES)) {
  const liste = DEFAULT_LISTS.find(l => l.id === idListe);
  if (!liste) continue;
  for (const [rang, chemin] of Object.entries(lignes)) {
    if (liste.rows[rang]) liste.rows[rang][1] = chemin;
  }
}`;

/* ---------- extraction ---------- */

// Bornes du littéral JSON qui suit « const <nom> = ».
function bornes(html, nom, obligatoire = true) {
  const prefixe = `const ${nom} = `;
  const ancre = html.indexOf(prefixe);
  if (ancre < 0) {
    if (obligatoire) throw new Error(`${nom} introuvable dans memo.html`);
    return null;
  }
  const debut = ancre + prefixe.length;
  const ouvrant = html[debut];
  if (ouvrant !== '[' && ouvrant !== '{') throw new Error(`${nom} n'est pas un littéral JSON`);
  const fermant = ouvrant === '[' ? ']' : '}';
  let profondeur = 0, dansTexte = false, echappe = false;
  for (let i = debut; i < html.length; i++) {
    const c = html[i];
    if (dansTexte) {
      if (echappe) echappe = false;
      else if (c === '\\') echappe = true;
      else if (c === '"') dansTexte = false;
      continue;
    }
    if (c === '"') dansTexte = true;
    else if (c === ouvrant) profondeur++;
    else if (c === fermant && --profondeur === 0) return { debut, fin: i + 1 };
  }
  throw new Error(`${nom} : littéral jamais refermé`);
}

// Identifiants de toutes les listes de l'application, quelle que soit leur
// provenance. Un simple relevé des « id » suffit : on n'a jamais besoin de
// réécrire ces blocs, seulement de savoir ce qu'ils contiennent.
function idsDeListes(html) {
  const ids = new Set();
  for (const nom of ['DEFAULT_LISTS', 'EXPANSION_LISTS', 'CURATED_LISTS_V3']) {
    const b = bornes(html, nom, false);
    if (!b) continue;
    const bloc = html.slice(b.debut, b.fin);
    for (const m of bloc.matchAll(/(?:^|[{,\s])"?id"?\s*:\s*['"]([a-z0-9_]+)['"]/gi)) ids.add(m[1]);
  }
  return ids;
}

// Colonne-sujet déclarée par memo.html pour chaque liste. C'est memo.html qui
// fait autorité : « f1_champions » pointe sur « Pilote », pas sur « Année ».
function lireColonnesSujet(html) {
  const b = bornes(html, 'IMAGE_REFERENCE_COLUMNS', false);
  if (!b) return {};
  const bloc = html.slice(b.debut, b.fin);
  const sortie = {};
  const motif = /(\w+)\s*:\s*\{\s*cols\s*:\s*\[([^\]]*)\](?:[^}]*?extraCols\s*:\s*\[([^\]]*)\])?/g;
  for (const m of bloc.matchAll(motif)) {
    const textes = t => [...String(t || '').matchAll(/'([^']*)'|"([^"]*)"/g)].map(x => x[1] ?? x[2]);
    sortie[m[1]] = { cols: textes(m[2]), extraCols: textes(m[3]) };
  }
  return sortie;
}

export function lireMemoHtml() {
  const html = fs.readFileSync(MEMO_HTML, 'utf8');
  const bImages = bornes(html, 'IMAGE_FILES_MAP');
  const bAtelier = bornes(html, 'ATELIER_IMAGES', false);
  return {
    html,
    bImages,
    bAtelier,
    imagesFull: JSON.parse(html.slice(bImages.debut, bImages.fin)),
    imagesAtelier: bAtelier ? JSON.parse(html.slice(bAtelier.debut, bAtelier.fin)) : {},
    idsListes: idsDeListes(html),
    colonnesSujet: lireColonnesSujet(html),
  };
}

/* ---------- écriture ---------- */

// IMAGE_FILES_MAP tient sur une seule ligne dans le fichier d'origine : on
// garde cette forme pour que le diff reste d'une ligne.
function serialiser(map) {
  return '{' + Object.entries(map)
    .map(([k, v]) => `${JSON.stringify(k)}:${JSON.stringify(v)}`).join(',') + '}';
}

function sauvegarder(html) {
  fs.mkdirSync(SAUVEGARDES, { recursive: true });
  const jour = new Date().toISOString().slice(0, 10);
  const cible = path.join(SAUVEGARDES, `memo-${jour}.html`);
  if (!fs.existsSync(cible)) fs.writeFileSync(cible, html);
  const anciennes = fs.readdirSync(SAUVEGARDES)
    .filter(f => /^memo-\d{4}-\d{2}-\d{2}\.html$/.test(f)).sort();
  for (const f of anciennes.slice(0, Math.max(0, anciennes.length - MAX_SAUVEGARDES))) {
    fs.rmSync(path.join(SAUVEGARDES, f), { force: true });
  }
}

export function ecrireMemoHtml(memo) {
  const { html, bImages, bAtelier } = lireMemoHtml();
  const jsonImages = serialiser(memo.imagesFull);
  const jsonAtelier = JSON.stringify(memo.imagesAtelier, null, 1);
  for (const bloc of [jsonImages, jsonAtelier]) {
    // une donnée ne doit jamais pouvoir refermer le <script>
    if (/<\/script/i.test(bloc)) throw new Error('Données contenant </script : écriture refusée');
  }

  let sortie;
  if (bAtelier) {
    // les deux littéraux existent : on remplace le plus loin d'abord, sinon
    // les bornes du premier glisseraient
    const [premier, second] = bImages.debut < bAtelier.debut
      ? [[bImages, jsonImages], [bAtelier, jsonAtelier]]
      : [[bAtelier, jsonAtelier], [bImages, jsonImages]];
    sortie = html.slice(0, second[0].debut) + second[1] + html.slice(second[0].fin);
    sortie = sortie.slice(0, premier[0].debut) + premier[1] + sortie.slice(premier[0].fin);
  } else {
    const ancre = html.indexOf(ANCRE);
    if (ancre < 0) throw new Error(`point d'insertion « ${ANCRE} » introuvable dans memo.html`);
    const apres = ancre + ANCRE.length;
    sortie = html.slice(0, apres) + BLOC(jsonAtelier) + html.slice(apres);
    // IMAGE_FILES_MAP se trouve après le point d'insertion : ses bornes ont
    // bougé, on les relit sur le texte produit
    const b = bornes(sortie, 'IMAGE_FILES_MAP');
    sortie = sortie.slice(0, b.debut) + jsonImages + sortie.slice(b.fin);
  }

  // relecture de contrôle avant de toucher au fichier réel
  for (const nom of ['IMAGE_FILES_MAP', 'ATELIER_IMAGES', 'DEFAULT_LISTS', 'CURATED_LISTS_V3']) {
    const b = bornes(sortie, nom, false);
    if (b) JSON.parse(sortie.slice(b.debut, b.fin));
  }

  sauvegarder(html);
  const tmp = `${MEMO_HTML}.tmp-${process.pid}`;
  fs.writeFileSync(tmp, sortie);
  fs.renameSync(tmp, MEMO_HTML);
  return { octets: Buffer.byteLength(sortie) };
}

/* ---------- correspondance entrée ↔ ligne de l'application ---------- */

// Clé de fichier d'une entrée : celle que porte déjà sa miniature, sinon son
// numéro. Deux entrées d'une même liste ne peuvent pas partager la même clé.
export function cleDeEntree(entree, prises) {
  const actuel = String(entree.image?.thumb || '');
  const m = actuel.match(/^thumbs\/[^/]+\/([^/.]+)\.[a-z0-9]+$/i);
  if (m) return m[1];
  const base = String(entree.number || entree.order + 1).replace(/[^a-z0-9_-]+/gi, '-') || String(entree.order + 1);
  if (!prises?.has(base)) return base;
  if (!prises.has(`${base}b`)) return `${base}b`;
  let n = 2;
  while (prises.has(`${base}-${n}`)) n++;
  return `${base}-${n}`;
}

export function clesPrises(entrees) {
  const prises = new Set();
  for (const e of entrees) {
    const m = String(e.image?.thumb || '').match(/^thumbs\/[^/]+\/([^/.]+)\.[a-z0-9]+$/i);
    if (m) prises.add(m[1]);
  }
  return prises;
}

/**
 * Inscrit une image dans l'application : la miniature via ATELIER_IMAGES (par
 * rang de ligne) et la grande image via IMAGE_FILES_MAP (par clé de fichier).
 * Les deux nomment le même fichier : ils ne peuvent pas diverger.
 */
export function poserImage(memo, idListe, rang, cle) {
  if (!memo.idsListes.has(idListe)) throw new Error(`liste ${idListe} absente de l'application`);
  const chemins = {
    original: `originaux/${idListe}/${cle}.webp`,
    full: `full/${idListe}/${cle}.webp`,
    thumb: `thumbs/${idListe}/${cle}.webp`,
  };
  (memo.imagesAtelier[idListe] ||= {})[String(rang)] = chemins.thumb;
  (memo.imagesFull[idListe] ||= {})[cle] = chemins.full;
  return chemins;
}
