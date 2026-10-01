// Petits outils d'affichage partagés par les écrans.

import {ICONES, LOGO, ECLAT} from './icones.js';
import {chemin} from './donnees.js';

export const $ = s => document.querySelector(s);
export const $$ = s => document.querySelectorAll(s);
export const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
export const ic = (n, v = 'regular') => `<svg class="i" viewBox="0 0 256 256" aria-hidden="true">${ICONES[`${n}-${v}`] || ''}</svg>`;
export const logo = () => `<svg viewBox="0 0 256 256" aria-hidden="true"><path d="${LOGO}"/></svg>`;
export const eclat = (cls = 'eclat-glyphe') => `<svg class="${cls}" viewBox="0 0 256 256" aria-hidden="true"><path d="${ECLAT}"/></svg>`;
export const sansAccents = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
export const pluriel = (n, mot, motPluriel = mot + 's') => `${n} ${n > 1 ? motPluriel : mot}`;

/** Une image de Mémo, une adresse web, ou une photo importée (« perso:<clé> »). */
export function img(p, alt = '', attrs = '') {
  if (!p) return `<span class="sans-image" aria-hidden="true"></span>`;
  if (String(p).startsWith('perso:')) return `<img data-perso="${esc(p.slice(6))}" alt="${esc(alt)}" ${attrs}>`;
  return `<img src="${esc(chemin(p))}" alt="${esc(alt)}" ${attrs}>`;
}
// Miniature (400 px) ou grande image (800 px et plus) : le navigateur prend celle
// qui reste nette à la taille affichée, selon la densité de l'écran
export const imgNette = (f, alt, tailles, attrs = '') => f.grande && f.grande !== f.image
  ? img(f.image, alt, `srcset="${esc(chemin(f.image))} 400w, ${esc(chemin(f.grande))} 900w" sizes="${tailles}" ${attrs}`)
  : img(f.image, alt, attrs);

let minuteur;
export function toast(texte, duree = 2600) {
  const t = $('#toast'); t.textContent = texte; t.hidden = false;
  clearTimeout(minuteur); minuteur = setTimeout(() => { t.hidden = true; }, duree);
}
