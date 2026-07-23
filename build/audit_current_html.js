#!/usr/bin/env node
const fs = require('fs');
const cp = require('child_process');

const out = cp.execFileSync('node', ['build/extract_data.js', 'memo.html'], { encoding: 'utf8' });
const lists = JSON.parse(out).DEFAULT_LISTS;

const missing = [];
for (const l of lists) {
  for (const r of l.rows) {
    for (const [i, c] of l.columns.entries()) {
      if (/image|localisation/i.test(c)) {
        const p = r[i];
        if (p && !String(p).startsWith('data:') && !fs.existsSync(p)) missing.push([l.id, r[0], c, p]);
      }
    }
  }
}

const osTargets = [8,11,15,18,63,64,65,66,67,68,69,70,97,98,99,100,101,102,103,109,110,111,112,113,114,115,116,117,118,119,120,121,122];
const os = osTargets.map(n => ({
  n,
  thumb: fs.existsSync(`thumbs/os/${n}.webp`),
  fullPng: fs.existsSync(`full/os/${n}.png`),
}));

const films = lists.find(l => l.id === 'films');
const ti = films.columns.indexOf('Titre');
const yi = films.columns.indexOf('Année');
const seen = new Map();
const dups = [];
for (const r of films.rows) {
  const key = String(r[ti]).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/\s*\((prod\.|production)\)\s*/g, '').trim();
  if (seen.has(key)) dups.push([key, seen.get(key), [r[0], r[yi], r[ti]]]);
  else seen.set(key, [r[0], r[yi], r[ti]]);
}

console.log(JSON.stringify({
  listCount: lists.length,
  missingPaths: missing.length,
  osFixedTargets: os.filter(x => x.thumb && x.fullPng).length,
  osNotFixed: os.filter(x => !x.thumb || !x.fullPng),
  filmDuplicates: dups,
}, null, 2));
