/**
 * extract_data.js — Extrait DEFAULT_LISTS et tables lookup depuis memo_v46_images.html
 * Usage: node extract_data.js <html_path>
 * Sortie: JSON sur stdout
 */
'use strict';
const fs = require('fs');
const htmlPath = process.argv[2];
if (!htmlPath) { process.stderr.write('Usage: node extract_data.js <html_path>\n'); process.exit(1); }
const html = fs.readFileSync(htmlPath, 'utf8');

function extractBracketedValue(str, name) {
  const marker = `const ${name} = `;
  const idx = str.indexOf(marker);
  if (idx === -1) return null;
  let i = idx + marker.length;
  while (i < str.length && str[i] !== '[' && str[i] !== '{') i++;
  if (i >= str.length) return null;
  return extractFrom(str, i);
}

function extractFrom(str, startIdx) {
  const open = str[startIdx];
  const close = open === '[' ? ']' : open === '{' ? '}' : null;
  if (!close) return null;
  let depth = 0, i = startIdx;
  while (i < str.length) {
    const c = str[i];
    if (c === '"') { i++; while (i < str.length && (str[i] !== '"' || str[i-1] === '\\')) i++; }
    else if (c === "'") { i++; while (i < str.length && (str[i] !== "'" || str[i-1] === '\\')) i++; }
    else if (c === '`') { i++; while (i < str.length && (str[i] !== '`' || str[i-1] === '\\')) i++; }
    else if (c === open) depth++;
    else if (c === close) { depth--; if (depth === 0) return str.substring(startIdx, i + 1); }
    i++;
  }
  return null;
}

function safeEval(code) {
  try { return new Function(`return ${code}`)(); }
  catch(e) { process.stderr.write(`safeEval error: ${e.message}\n${code.substring(0,200)}\n`); return null; }
}

const names = ['DEFAULT_LISTS', 'HADES_OFFICIAL_FILES', 'WIKI_IMAGE_ALIASES', 'PHILOSOPHER_COMMONS_FILES'];
const result = {};
for (const name of names) {
  const code = extractBracketedValue(html, name);
  if (code) {
    const val = safeEval(code);
    if (val !== null) result[name] = val;
    else process.stderr.write(`Warning: could not parse ${name}\n`);
  } else {
    process.stderr.write(`Warning: ${name} not found in HTML\n`);
  }
}

// Extract IMAGE_REFERENCE_COLUMNS as well
const ircCode = extractBracketedValue(html, 'IMAGE_REFERENCE_COLUMNS');
if (ircCode) result['IMAGE_REFERENCE_COLUMNS'] = safeEval(ircCode);

// ── Ajouter EXPANSION_LISTS et CURATED_LISTS_V3 à DEFAULT_LISTS ──────────

// Extraire les fonctions helper nécessaires à makeExpansionRows
function extractFunctionBody(str, name) {
  const m = str.match(new RegExp(`function\\s+${name}\\s*\\([^)]*\\)\\s*\\{`));
  if (!m) return null;
  const start = str.indexOf(m[0]);
  let depth = 0, i = start;
  while (i < str.length) {
    if (str[i] === '{') depth++;
    else if (str[i] === '}') { depth--; if (depth === 0) return str.substring(start, i + 1); }
    i++;
  }
  return null;
}

const helperFns = ['makeExpansionVisual', 'makeExpansionRows', 'makeTextRows']
  .map(fn => extractFunctionBody(html, fn))
  .filter(Boolean)
  .join('\n');

// EXPANSION_LISTS
const expansionCode = extractBracketedValue(html, 'EXPANSION_LISTS');
if (expansionCode && result['DEFAULT_LISTS']) {
  try {
    const expansionLists = new Function(
      'encodeURIComponent',
      helperFns + '\nreturn ' + expansionCode
    )(encodeURIComponent);
    // Normaliser les rows : remplacer les data-URI par '' pour alléger
    for (const lst of expansionLists) {
      if (lst.noImage) continue;
      for (const row of (lst.rows || [])) {
        if (row[1] && String(row[1]).startsWith('data:')) row[1] = '';
      }
    }
    result['DEFAULT_LISTS'].push(...expansionLists);
  } catch(e) {
    process.stderr.write(`Warning: could not parse EXPANSION_LISTS: ${e.message}\n`);
  }
}

// CURATED_LISTS_V3
const curatedCode = extractBracketedValue(html, 'CURATED_LISTS_V3');
if (curatedCode && result['DEFAULT_LISTS']) {
  try {
    const curatedLists = new Function('return ' + curatedCode)();
    result['DEFAULT_LISTS'].push(...curatedLists);
  } catch(e) {
    process.stderr.write(`Warning: could not parse CURATED_LISTS_V3: ${e.message}\n`);
  }
}

process.stdout.write(JSON.stringify(result));
