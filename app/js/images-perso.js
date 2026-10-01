// Photos importées par l'utilisateur, rangées dans IndexedDB.
//
// Le stockage local (5 Mo environ) est partagé par toutes les applis de
// blinytz.github.io : des photos l'auraient vite rempli. IndexedDB offre bien
// plus de place. Une fiche ne garde que « perso:<clé> » ; à l'affichage, une
// balise <img data-perso="<clé>"> reçoit son adresse dès que la photo est lue.

const BASE = 'memo2-images', MAGASIN = 'images';
let ouverture = null;
const adresses = new Map();          // clé -> URL objet déjà fabriquée

function base() {
  if (!ouverture) ouverture = new Promise((ok, ko) => {
    const r = indexedDB.open(BASE, 1);
    r.onupgradeneeded = () => r.result.createObjectStore(MAGASIN);
    r.onsuccess = () => ok(r.result);
    r.onerror = () => ko(r.error);
  });
  return ouverture;
}
async function operation(mode, faire) {
  const db = await base();
  return new Promise((ok, ko) => {
    const tx = db.transaction(MAGASIN, mode), req = faire(tx.objectStore(MAGASIN));
    tx.oncomplete = () => ok(req?.result);
    tx.onerror = () => ko(tx.error);
  });
}

export async function ranger(blob) {
  const cle = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;
  await operation('readwrite', s => s.put(blob, cle));
  return cle;
}
export const lire = cle => operation('readonly', s => s.get(cle));
export const effacer = cle => operation('readwrite', s => s.delete(cle));
export const cles = () => operation('readonly', s => s.getAllKeys());

export function adresse(cle) {
  // la promesse est gardée, pas son résultat : deux demandes simultanées
  // reçoivent la même adresse
  if (!adresses.has(cle)) adresses.set(cle, lire(cle).then(blob => blob ? URL.createObjectURL(blob) : ''));
  return adresses.get(cle);
}

/** Donne leur adresse aux images perso apparues dans la page. */
export function hydrater(racine = document) {
  racine.querySelectorAll('img[data-perso]:not([src])').forEach(async img => {
    const url = await adresse(img.dataset.perso).catch(() => '');
    if (url) img.src = url; else img.replaceWith(Object.assign(document.createElement('span'), {className: 'sans-image'}));
  });
}

/** Surveille la page : toute image perso ajoutée est hydratée sans y penser. */
export function surveiller() {
  new MutationObserver(() => hydrater()).observe(document.body, {childList: true, subtree: true});
}

/**
 * Réduit une photo choisie sur l'appareil (au plus 1000 × 750) et la range.
 * Rend la référence « perso:<clé> » à mettre dans la fiche.
 */
export async function importerPhoto(fichier, cote = 1000) {
  const bitmap = await createImageBitmap(fichier);
  const k = Math.min(1, cote / Math.max(bitmap.width, bitmap.height));
  const toile = document.createElement('canvas');
  toile.width = Math.round(bitmap.width * k); toile.height = Math.round(bitmap.height * k);
  toile.getContext('2d').drawImage(bitmap, 0, 0, toile.width, toile.height);
  const blob = await new Promise(ok => toile.toBlob(ok, 'image/jpeg', 0.85));
  return 'perso:' + await ranger(blob);
}

/** Range une image « data: » (reprise de l'ancienne version). */
export async function importerDataUrl(dataUrl) {
  const blob = await (await fetch(dataUrl)).blob();
  return 'perso:' + await ranger(blob);
}
