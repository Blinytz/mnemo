// Passerelle WikiDeck → Mémo.
//
// L'atelier WikiDeck a déjà cadré des centaines d'images. Plutôt que de
// rechercher les mêmes photos une deuxième fois, on apparie une liste de Mémo
// à une collection WikiDeck.
//
// L'appariement ne peut PAS se faire sur le lien Wikipédia : aucune des 2 131
// entrées de Mémo n'en possède. Il se fait sur la colonne qui porte le sujet,
// celle que memo.html déclare lui-même dans IMAGE_REFERENCE_COLUMNS
// (« f1_champions » → « Pilote », et non « Année »). Le lien Wikipédia voyage
// alors dans l'autre sens : c'est WikiDeck qui en fournit un à Mémo.
//
// La comparaison reste toujours bornée au couple liste ↔ collection choisi :
// un rapprochement à l'aveugle sur tout le corpus produirait des faux amis
// (le dieu Jupiter pour la planète Jupiter).

import fs from 'node:fs';
import path from 'node:path';
import { canonicalWikipedia } from './lib.mjs';
import { RACINE } from './memo-html.mjs';

export const WIKIDECK = path.resolve(RACINE, '..', 'wikideck');

function normaliser(valeur) {
  return String(valeur ?? '').normalize('NFD').replace(/\p{Diacritic}/gu, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

function lireJson(...morceaux) {
  const p = path.join(WIKIDECK, ...morceaux);
  return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : null;
}

export function disponible() {
  return fs.existsSync(path.join(WIKIDECK, 'data', 'collections.json'));
}

export function collections() {
  const index = lireJson('data', 'collections.json');
  if (!index) return [];
  const cadrages = lireJson('build', 'notes_atelier.json')?.cadrages || {};
  return index.collections.map(c => {
    const d = lireJson(...c.fichier.split('/'));
    if (!d) return null;
    const cartes = d.cartes || [];
    return {
      slug: d.slug,
      nom: d.collection,
      cartes: cartes.length,
      cadrees: cartes.filter(k => cadrages[k.id]).length,
    };
  }).filter(Boolean);
}

// Cartes d'une collection, enrichies du cadrage validé dans l'atelier WikiDeck
// et du chemin de l'image d'origine (la plus fidèle disponible).
export function cartes(slug) {
  const d = lireJson('data', `${slug}.json`);
  if (!d) throw new Error(`collection WikiDeck inconnue : ${slug}`);
  const cadrages = lireJson('build', 'notes_atelier.json')?.cadrages || {};
  const sources = lireJson('build', 'images_sources.json') || {};
  return (d.cartes || []).map(k => {
    const base = path.basename(k.imageUrl || `${k.id}.webp`);
    const candidats = [
      `images/originaux/${slug}/${base}`,
      k.imageUrl,
      k.thumbUrl,
    ].filter(r => r && fs.existsSync(path.join(WIKIDECK, r)));
    const cadrage = cadrages[k.id] || null;
    return {
      id: k.id,
      nom: k.nom,
      wikipedia: k.lienWikipedia || '',
      // le cadrage n'a de sens que s'il accompagne l'image d'origine
      cadrage: cadrage && candidats[0]?.startsWith('images/originaux/') ? cadrage : null,
      source: candidats[0] || null,
      apercu: fs.existsSync(path.join(WIKIDECK, k.thumbUrl || '')) ? k.thumbUrl : candidats[0],
      provenance: sources[k.id]?.source || null,
    };
  });
}

// Colonne-sujet par défaut : celle que memo.html déclare, sinon la première
// colonne qui ne soit ni un numéro, ni une image, ni une donnée annexe.
export function colonneParDefaut(liste, colonnesSujet) {
  const declaree = colonnesSujet?.[liste.legacyId]?.cols?.[0];
  if (declaree && liste.columns.includes(declaree)) return declaree;
  return liste.columns.find((c, i) =>
    i > 1 && !/^(num[ée]ro|image|photo|ann[ée]e|date)$/i.test(c)) || liste.columns[2] || '';
}

// Colonnes proposables pour l'appariement, les plus prometteuses d'abord :
// on mesure combien de valeurs de chaque colonne retombent sur un nom de carte.
export function colonnesCandidates(entrees, listeCols, cartesCollection) {
  const noms = new Set(cartesCollection.map(k => normaliser(k.nom)));
  return (listeCols || [])
    .filter(c => !/^(image)$/i.test(c))
    .map(col => ({
      col,
      touches: entrees.filter(e => noms.has(normaliser(e.fields?.[col]))).length,
    }))
    .sort((a, b) => b.touches - a.touches);
}

/**
 * Apparie les entrées d'une liste Mémo aux cartes d'une collection WikiDeck.
 *
 * Plusieurs entrées peuvent légitimement viser la même carte : les 76 saisons
 * de Formule 1 se partagent 35 pilotes. L'ambiguïté à signaler est l'inverse —
 * une entrée sur laquelle plusieurs cartes différentes correspondent.
 */
export function apparier({ entrees, cartes: cartesCollection, colonne }) {
  const parNom = new Map();
  for (const k of cartesCollection) {
    const n = normaliser(k.nom);
    if (!parNom.has(n)) parNom.set(n, []);
    parNom.get(n).push(k);
  }
  const parWiki = new Map();
  for (const k of cartesCollection) {
    const w = canonicalWikipedia(k.wikipedia);
    if (!w) continue;
    if (!parWiki.has(w)) parWiki.set(w, []);
    parWiki.get(w).push(k);
  }
  const parId = new Map(cartesCollection.map(k => [k.id, k]));

  const paires = entrees.map(e => {
    const valeur = String(e.fields?.[colonne] ?? '').trim();
    const deja = e.externalIds?.wikideck && parId.get(e.externalIds.wikideck);
    if (deja) return paire(e, valeur, [deja], 'certain', 'déjà appariée');
    const wiki = canonicalWikipedia(e.wikipedia);
    const parLien = wiki ? parWiki.get(wiki) || [] : [];
    if (parLien.length === 1) return paire(e, valeur, parLien, 'certain', 'lien Wikipédia');
    const parValeur = parNom.get(normaliser(valeur)) || [];
    if (parValeur.length === 1) return paire(e, valeur, parValeur, 'certain', `colonne « ${colonne} »`);
    if (parValeur.length > 1) return paire(e, valeur, parValeur, 'ambigu', `${parValeur.length} cartes de même nom`);
    return paire(e, valeur, [], 'sans', valeur ? 'aucune carte de ce nom' : `colonne « ${colonne} » vide`);
  });

  const utilisees = new Set(paires.flatMap(p => p.statut === 'certain' ? [p.candidats[0].id] : []));
  return {
    colonne,
    paires,
    resume: {
      certain: paires.filter(p => p.statut === 'certain').length,
      ambigu: paires.filter(p => p.statut === 'ambigu').length,
      sans: paires.filter(p => p.statut === 'sans').length,
      verrouillees: paires.filter(p => p.verrouillee).length,
      cartesInutilisees: cartesCollection.filter(k => !utilisees.has(k.id)).map(k => k.nom),
    },
  };
}

function paire(entree, valeur, candidats, statut, raison) {
  return {
    entryId: entree.id,
    libelle: entree.name,
    valeur,
    statut,
    raison,
    verrouillee: !!entree.image?.locked,
    aDejaUneImage: !!entree.image?.thumb,
    candidats: candidats.map(k => ({
      id: k.id, nom: k.nom, apercu: k.apercu, source: k.source,
      cadrage: k.cadrage, wikipedia: k.wikipedia, sansOriginal: !k.source,
    })),
  };
}
