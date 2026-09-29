// Serveur de l'Atelier Mémo.
//
// Différence essentielle avec la version précédente : enregistrer une image
// écrit maintenant dans l'application elle-même. Un seul appel dépose les trois
// fichiers (original, grande image, miniature) ET met à jour memo.html. Avant,
// les images partaient dans assets/atelier/, que memo.html ne lit jamais : on
// pouvait recadrer toute la journée sans que l'application change.

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { URL } from 'node:url';
import { validateWorkspace, slug } from './lib.mjs';
import {
  RACINE, lireMemoHtml, ecrireMemoHtml, poserImage, cleDeEntree, clesPrises,
} from './memo-html.mjs';
import * as wikideck from './wikideck-bridge.mjs';

const DOSSIER_DATA = path.join(RACINE, 'data', 'atelier');
const ETAT = path.join(DOSSIER_DATA, 'workspace.json');
const HISTORIQUE = path.join(DOSSIER_DATA, 'history');
const HOTE = process.env.MEMO_HOST || '127.0.0.1';
const PORT = Number(process.env.MEMO_PORT || 3434);
const JETON = process.env.MEMO_ATELIER_TOKEN || crypto.randomBytes(18).toString('base64url');

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.webp': 'image/webp',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.svg': 'image/svg+xml',
};

/* ---------- utilitaires ---------- */

function json(res, code, corps) {
  res.writeHead(code, { 'Content-Type': MIME['.json'], 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(corps));
}

function corps(req, limite = 64 * 1024 * 1024) {
  return new Promise((ok, non) => {
    const bouts = []; let taille = 0;
    req.on('data', c => {
      taille += c.length;
      if (taille > limite) non(new Error('Contenu trop volumineux'));
      else bouts.push(c);
    });
    req.on('end', () => ok(Buffer.concat(bouts)));
    req.on('error', non);
  });
}

const corpsJson = async req => JSON.parse((await corps(req)).toString('utf8'));

function lireEtat() { return JSON.parse(fs.readFileSync(ETAT, 'utf8')); }

function ecrireEtat(suivant, precedent) {
  fs.mkdirSync(HISTORIQUE, { recursive: true });
  const horodatage = new Date().toISOString().replace(/[:.]/g, '-');
  if (precedent) {
    fs.writeFileSync(path.join(HISTORIQUE, `${horodatage}.json`),
      JSON.stringify(precedent, null, 2) + '\n');
  }
  const tmp = `${ETAT}.tmp-${process.pid}`;
  fs.writeFileSync(tmp, JSON.stringify(suivant, null, 2) + '\n');
  fs.renameSync(tmp, ETAT);
}

function ecrireFichier(cible, donnees) {
  fs.mkdirSync(path.dirname(cible), { recursive: true });
  const tmp = `${cible}.tmp-${process.pid}`;
  fs.writeFileSync(tmp, donnees);
  fs.renameSync(tmp, cible);
}

function cheminSur(relatif) {
  const resolu = path.resolve(RACINE, String(relatif).replace(/^\/+/, ''));
  if (resolu !== RACINE && !resolu.startsWith(RACINE + path.sep)) throw new Error('Chemin interdit');
  return resolu;
}

function servir(res, fichier) {
  if (!fs.existsSync(fichier) || fs.statSync(fichier).isDirectory()) {
    return json(res, 404, { error: 'Introuvable' });
  }
  res.writeHead(200, {
    'Content-Type': MIME[path.extname(fichier).toLowerCase()] || 'application/octet-stream',
    'Cache-Control': 'no-store',
  });
  fs.createReadStream(fichier).pipe(res);
}

function autorise(req, url) {
  return HOTE === '127.0.0.1'
    || req.headers['x-memo-token'] === JETON
    || url.searchParams.get('token') === JETON;
}

// Les écritures qui touchent memo.html sont sérialisées : deux enregistrements
// simultanés ne peuvent pas se recouvrir.
let file = Promise.resolve();
function enFile(travail) {
  const suite = file.then(travail, travail);
  file = suite.then(() => {}, () => {});
  return suite;
}

/* ---------- listes : lien entre l'atelier et l'application ---------- */

// Une liste de l'atelier n'est utile à l'application que si celle-ci la
// connaît. Le cas échéant l'interface doit le dire, pas le taire.
function infosListes(memo = lireMemoHtml()) {
  const etat = lireEtat();
  return etat.lists.filter(l => !l.deletedAt).map(l => ({
    id: l.id,
    legacyId: l.legacyId,
    dansApplication: memo.idsListes.has(l.legacyId),
    colonneSujet: wikideck.colonneParDefaut(l, memo.colonnesSujet),
  }));
}

/* ---------- enregistrement d'une image ---------- */

async function enregistrerImage(entryId, charge) {
  return enFile(() => {
    const etat = lireEtat();
    const entree = etat.entries.find(e => e.id === entryId);
    if (!entree) throw Object.assign(new Error('Entrée inconnue'), { code: 404 });
    const liste = etat.lists.find(l => l.id === entree.listId);
    if (!liste) throw Object.assign(new Error('Liste inconnue'), { code: 404 });

    const memo = lireMemoHtml();
    const dansApplication = memo.idsListes.has(liste.legacyId);

    const blobs = {};
    for (const genre of ['original', 'full', 'thumb']) {
      if (!charge[genre]) throw Object.assign(new Error(`image « ${genre} » absente`), { code: 400 });
      blobs[genre] = Buffer.from(charge[genre], 'base64');
      if (!blobs[genre].length) throw Object.assign(new Error(`image « ${genre} » vide`), { code: 400 });
    }

    // La clé de fichier suit la convention de memo.html : « thumbs/<liste>/<clé> ».
    const voisines = etat.entries.filter(e => e.listId === entree.listId && !e.deletedAt && e.id !== entree.id);
    const cle = cleDeEntree(entree, clesPrises(voisines));
    let chemins;
    if (dansApplication) {
      chemins = poserImage(memo, liste.legacyId, entree.order, cle);
      ecrireMemoHtml(memo);
    } else {
      // liste absente de l'application : on dépose quand même les fichiers,
      // prêts à servir, mais on ne prétend pas avoir mis l'application à jour
      chemins = {
        original: `originaux/${liste.legacyId}/${cle}.webp`,
        full: `full/${liste.legacyId}/${cle}.webp`,
        thumb: `thumbs/${liste.legacyId}/${cle}.webp`,
      };
    }

    for (const genre of ['original', 'full', 'thumb']) {
      ecrireFichier(path.join(RACINE, chemins[genre]), blobs[genre]);
    }

    entree.image = {
      ...entree.image,
      source: chemins.original,
      full: chemins.full,
      thumb: chemins.thumb,
      crop: charge.cadrage || entree.image?.crop || { cx: 0.5, cy: 0.5, w: 1 },
      status: charge.statut || 'validee',
      locked: !!entree.image?.locked,
      provenance: charge.provenance || { kind: 'manuel', at: new Date().toISOString() },
    };
    if (charge.wikipedia && !entree.wikipedia) entree.wikipedia = charge.wikipedia;
    if (charge.cardId) entree.externalIds = { ...(entree.externalIds || {}), wikideck: charge.cardId };

    const erreurs = validateWorkspace(etat);
    if (erreurs.length) throw Object.assign(new Error(erreurs.join('\n')), { code: 422 });
    etat.revision += 1;
    etat.updatedAt = new Date().toISOString();
    ecrireEtat(etat, null);
    return { revision: etat.revision, image: entree.image, dansApplication };
  });
}

/* ---------- réparation des noms d'entrées ---------- */

// La migration a retenu la mauvaise colonne comme nom sur plusieurs listes :
// les 76 champions de Formule 1 s'appellent « 1950 », « 1951 »… au lieu de
// porter le nom du pilote. Sans nom juste, aucun rapprochement n'est possible.
function apercuNoms() {
  const memo = lireMemoHtml();
  const etat = lireEtat();
  const propositions = [];
  for (const liste of etat.lists.filter(l => !l.deletedAt)) {
    const colonne = memo.colonnesSujet?.[liste.legacyId]?.cols?.[0];
    if (!colonne || !liste.columns.includes(colonne)) continue;
    const changements = etat.entries
      .filter(e => e.listId === liste.id && !e.deletedAt)
      .map(e => ({ id: e.id, avant: e.name, apres: String(e.fields?.[colonne] ?? '').trim() }))
      .filter(c => c.apres && c.apres !== c.avant);
    if (changements.length) {
      propositions.push({ listId: liste.id, liste: liste.name, colonne, changements });
    }
  }
  return propositions;
}

function appliquerNoms(ids) {
  return enFile(() => {
    const etat = lireEtat();
    const voulus = ids?.length ? new Set(ids) : null;
    let modifiees = 0;
    for (const groupe of apercuNoms()) {
      for (const c of groupe.changements) {
        if (voulus && !voulus.has(c.id)) continue;
        const e = etat.entries.find(x => x.id === c.id);
        if (!e) continue;
        e.name = c.apres;
        e.slug = slug(c.apres);
        if (!e.title || e.title === c.avant) e.title = c.apres;
        modifiees++;
      }
    }
    const erreurs = validateWorkspace(etat);
    if (erreurs.length) throw Object.assign(new Error(erreurs.join('\n')), { code: 422 });
    etat.revision += 1;
    etat.updatedAt = new Date().toISOString();
    ecrireEtat(etat, null);
    return { modifiees, revision: etat.revision };
  });
}

/* ---------- routage ---------- */

const routes = {
  'GET /api/workspace': (req, res) => json(res, 200, lireEtat()),

  'GET /api/contexte': (req, res) => {
    const memo = lireMemoHtml();
    json(res, 200, {
      listes: infosListes(memo),
      listesApplication: [...memo.idsListes],
      colonnesSujet: memo.colonnesSujet,
      wikideck: wikideck.disponible() ? wikideck.collections() : [],
      formats: { full: [800, 600], thumb: [400, 300] },
    });
  },

  'PUT /api/workspace': async (req, res, url) => {
    if (!autorise(req, url)) return json(res, 403, { error: 'Jeton requis' });
    return enFile(() => {
      const precedent = lireEtat();
      return corpsJson(req).then(suivant => {
        if (Number(req.headers['if-match']) !== precedent.revision) {
          return json(res, 409, {
            error: 'Les données ont changé de leur côté. Rechargez avant d’enregistrer.',
            revision: precedent.revision,
          });
        }
        const erreurs = validateWorkspace(suivant);
        if (erreurs.length) return json(res, 422, { errors: erreurs });
        suivant.revision = precedent.revision + 1;
        suivant.updatedAt = new Date().toISOString();
        ecrireEtat(suivant, precedent);
        json(res, 200, { revision: suivant.revision, updatedAt: suivant.updatedAt });
      });
    });
  },

  'PUT /api/entree/image': async (req, res, url) => {
    if (!autorise(req, url)) return json(res, 403, { error: 'Jeton requis' });
    const entryId = url.searchParams.get('id');
    const resultat = await enregistrerImage(entryId, await corpsJson(req));
    json(res, 200, resultat);
  },

  'GET /api/wikideck/collections': (req, res) =>
    json(res, 200, { disponible: wikideck.disponible(), collections: wikideck.collections() }),

  'POST /api/wikideck/appariement': async (req, res) => {
    const { listId, collection, colonne } = await corpsJson(req);
    const etat = lireEtat();
    const liste = etat.lists.find(l => l.id === listId);
    if (!liste) return json(res, 404, { error: 'Liste inconnue' });
    const entrees = etat.entries.filter(e => e.listId === listId && !e.deletedAt)
      .sort((a, b) => a.order - b.order);
    const cartesCollection = wikideck.cartes(collection);
    const memo = lireMemoHtml();
    const retenue = colonne || wikideck.colonneParDefaut(liste, memo.colonnesSujet);
    json(res, 200, {
      ...wikideck.apparier({ entrees, cartes: cartesCollection, colonne: retenue }),
      colonnes: wikideck.colonnesCandidates(entrees, liste.columns, cartesCollection),
    });
  },

  'GET /api/noms/apercu': (req, res) => json(res, 200, { propositions: apercuNoms() }),

  'POST /api/noms/appliquer': async (req, res, url) => {
    if (!autorise(req, url)) return json(res, 403, { error: 'Jeton requis' });
    const { ids, confirm } = await corpsJson(req);
    if (confirm !== true) return json(res, 400, { error: 'Confirmation explicite requise' });
    json(res, 200, await appliquerNoms(ids));
  },

  'GET /api/health': (req, res) => json(res, 200, {
    ok: true,
    memoHtml: fs.existsSync(path.join(RACINE, 'memo.html')),
    wikideck: wikideck.disponible(),
    ecritureProtegee: HOTE !== '127.0.0.1',
  }),
};

const serveur = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const route = routes[`${req.method} ${url.pathname}`];
    if (route) return await route(req, res, url);

    // arbre WikiDeck, en lecture seule et limité aux images
    if (url.pathname.startsWith('/wikideck/')) {
      const relatif = decodeURIComponent(url.pathname.slice('/wikideck/'.length));
      if (!/^images\//.test(relatif)) return json(res, 403, { error: 'Chemin interdit' });
      const resolu = path.resolve(wikideck.WIKIDECK, relatif);
      if (!resolu.startsWith(wikideck.WIKIDECK + path.sep)) return json(res, 403, { error: 'Chemin interdit' });
      return servir(res, resolu);
    }

    let relatif = decodeURIComponent(url.pathname);
    if (relatif === '/' || relatif === '/atelier' || relatif === '/atelier/') relatif = '/atelier/index.html';
    return servir(res, cheminSur(relatif));
  } catch (erreur) {
    console.error(erreur);
    json(res, erreur.code && erreur.code < 600 ? erreur.code : 500, { error: erreur.message });
  }
});

serveur.listen(PORT, HOTE, () => {
  console.log(`Atelier Mémo : http://${HOTE === '0.0.0.0' ? 'localhost' : HOTE}:${PORT}/atelier/`);
  console.log(`Application mise à jour : ${path.join(RACINE, 'memo.html')}`);
  if (!wikideck.disponible()) console.log('WikiDeck introuvable : la reprise d’images sera désactivée.');
  if (HOTE !== '127.0.0.1') console.log(`Jeton mobile : ${JETON}`);
});
