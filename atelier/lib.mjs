import crypto from 'node:crypto';

export const IMAGE_FORMAT = Object.freeze({
  ratio: 4 / 3,
  full: Object.freeze([800, 600]),
  thumb: Object.freeze([213, 160]),
});

export const IMAGE_STATUSES = Object.freeze([
  'manquante', 'importee', 'a_cadrer', 'a_verifier', 'validee',
  'verrouillee', 'source_cassee', 'conflit',
]);

export function slug(value = '') {
  return String(value).normalize('NFD').replace(/\p{Diacritic}/gu, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

export function stableId(namespace, ...parts) {
  return `${namespace}_${crypto.createHash('sha256')
    .update(parts.map(String).join('\u241f')).digest('hex').slice(0, 16)}`;
}

export function canonicalWikipedia(value = '') {
  if (!value) return '';
  try {
    const url = new URL(value);
    if (!/\.wikipedia\.org$/i.test(url.hostname)) return value.trim();
    url.protocol = 'https:';
    url.hash = '';
    url.search = '';
    const pathname = decodeURIComponent(url.pathname).replace(/\/+$/, '').replace(/ /g, '_');
    return `${url.origin}${pathname}`;
  } catch {
    return value.trim();
  }
}

export function normalizeName(value = '') {
  return slug(value).replace(/-/g, ' ');
}

export function validateWorkspace(data) {
  const errors = [];
  if (!data || data.schemaVersion !== 1) errors.push('schemaVersion doit valoir 1');
  for (const key of ['categories', 'lists', 'entries', 'notes']) {
    if (!Array.isArray(data?.[key])) errors.push(`${key} doit être un tableau`);
  }
  const unique = (items, label) => {
    const seen = new Set();
    for (const item of items || []) {
      if (!item.id) errors.push(`${label} sans identifiant`);
      else if (seen.has(item.id)) errors.push(`${label} dupliqué : ${item.id}`);
      seen.add(item.id);
    }
    return seen;
  };
  const categories = unique(data?.categories, 'catégorie');
  const lists = unique(data?.lists, 'liste');
  unique(data?.entries, 'entrée');
  unique(data?.notes, 'note');
  for (const list of data?.lists || []) {
    if (!categories.has(list.categoryId)) errors.push(`catégorie absente pour ${list.id}`);
  }
  for (const entry of data?.entries || []) {
    if (!lists.has(entry.listId)) errors.push(`liste absente pour ${entry.id}`);
    if (entry.image?.thumbSource) errors.push(`source miniature interdite pour ${entry.id}`);
  }
  return errors;
}

export function matchWikideckCard(card, entries) {
  const wiki = canonicalWikipedia(card.lienWikipedia);
  const byWiki = wiki ? entries.filter(e => canonicalWikipedia(e.wikipedia) === wiki) : [];
  if (byWiki.length === 1) return { kind: 'certain', reason: 'wikipedia', entry: byWiki[0] };
  const byId = entries.filter(e => e.externalIds?.wikideck === card.id);
  if (byId.length === 1) return { kind: 'certain', reason: 'identifiant', entry: byId[0] };
  const cardSlug = slug(card.id?.split('_').slice(1).join('_') || card.nom);
  const bySlug = entries.filter(e => slug(e.slug || e.name) === cardSlug);
  if (bySlug.length === 1) return { kind: 'certain', reason: 'slug', entry: bySlug[0] };
  const byName = entries.filter(e => normalizeName(e.name) === normalizeName(card.nom));
  if (byName.length === 1) return { kind: 'probable', reason: 'nom', entry: byName[0] };
  if (byName.length > 1) return { kind: 'ambiguous', reason: 'nom', entries: byName };
  return { kind: 'wikideck_only', reason: 'aucune correspondance' };
}

export function previewBulk(entries, operation) {
  const changes = [];
  for (const entry of entries) {
    if (operation.type === 'renumber') {
      const after = String(Number(operation.start) + changes.length);
      if (String(entry.number) !== after) changes.push({ id: entry.id, field: 'number', before: entry.number, after });
    } else if (operation.type === 'replacePrefix') {
      const before = String(entry.title || entry.name || '');
      const after = before.replace(new RegExp(`^${escapeRegex(operation.from || '')}`), operation.to || '');
      if (before !== after) changes.push({ id: entry.id, field: 'title', before, after });
    }
  }
  return changes;
}

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
