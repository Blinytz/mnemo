import crypto from 'node:crypto';

// La grande image reprend le format de WikiDeck ; la miniature garde celui de
// Mémo (400 × 300), sinon chaque enregistrement dégraderait l'application.
// Les deux sont toujours découpées dans le même cadrage.
export const IMAGE_FORMAT = Object.freeze({
  ratio: 4 / 3,
  full: Object.freeze([800, 600]),
  thumb: Object.freeze([400, 300]),
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

// L'ancien matchWikideckCard() a été retiré : il rapprochait les cartes par lien
// Wikipédia et par nom d'entrée, or aucune entrée de Mémo n'a de lien Wikipédia
// et plusieurs listes portaient le mauvais champ comme nom — il ne trouvait
// donc rien. L'appariement vit désormais dans wikideck-bridge.mjs, borné à un
// couple liste ↔ collection et fondé sur la colonne-sujet déclarée par memo.html.

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
