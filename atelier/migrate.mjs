import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { canonicalWikipedia, stableId, slug, validateWorkspace } from './lib.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const sourcePath = path.join(root, 'build', 'extracted_data.json');
const curatedPath = path.join(root, 'data', 'curated_lists.json');
const imageMapPath = path.join(root, 'build', 'image_files_map.json');
const outputDir = path.join(root, 'data', 'atelier');
const outputPath = path.join(outputDir, 'workspace.json');
const reportPath = path.join(outputDir, 'migration-report.json');

const extracted = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
const curated = JSON.parse(fs.readFileSync(curatedPath, 'utf8'));
const imageMap = fs.existsSync(imageMapPath)
  ? JSON.parse(fs.readFileSync(imageMapPath, 'utf8'))
  : {};
const merged = new Map();
for (const list of [...(extracted.DEFAULT_LISTS || []), ...(curated.lists || [])]) merged.set(list.id, list);

const categoryNames = [...new Set([...merged.values()].map(l => l.category || 'Sans catégorie'))];
const categories = categoryNames.map((name, order) => ({
  id: stableId('cat', name), name, order, deletedAt: null,
}));
const categoryByName = new Map(categories.map(c => [c.name, c.id]));
const lists = [];
const entries = [];
const review = [];

function resolveLegacyFull(mappedPath, fallback) {
  if (!mappedPath) return fallback;
  if (fs.existsSync(path.join(root, mappedPath))) return mappedPath;
  const parsed = path.posix.parse(mappedPath);
  for (const extension of ['.jpg', '.jpeg', '.webp', '.png', '.svg']) {
    const candidate = path.posix.join(parsed.dir, `${parsed.name}${extension}`);
    if (fs.existsSync(path.join(root, candidate))) return candidate;
  }
  return fallback;
}

for (const [listKey, source] of merged) {
  const listId = stableId('list', listKey);
  lists.push({
    id: listId, legacyId: listKey, slug: slug(listKey), name: source.name,
    icon: source.icon || '📚', categoryId: categoryByName.get(source.category || 'Sans catégorie'),
    columns: source.columns || [], order: lists.length, metadata: {}, deletedAt: null,
  });
  (source.rows || []).forEach((row, order) => {
    const values = Object.fromEntries((source.columns || []).map((column, i) => [column, row[i] ?? '']));
    const nameIndex = (source.columns || []).findIndex((c, i) => i > 1 && !/image|photo|portrait|localisation/i.test(c));
    const name = String(row[nameIndex >= 0 ? nameIndex : 2] || `Entrée ${order + 1}`);
    const imageValue = String(row[1] || '');
    const imageMatch = imageValue.match(/^thumbs\/([^/]+)\/([^/.]+)\.[a-z0-9]+$/i);
    const mappedFull = imageMatch ? imageMap[imageMatch[1]]?.[imageMatch[2]] : null;
    const legacyFull = resolveLegacyFull(mappedFull, imageValue);
    const entry = {
      id: stableId('entry', listKey, order, name),
      listId, slug: slug(name), number: String(row[0] ?? order + 1), name,
      title: name, subtitle: '', description: '', extraText: '',
      wikipedia: canonicalWikipedia(source.wikipedia?.[order] || ''),
      fields: values, order, deletedAt: null, externalIds: {},
      image: {
        source: legacyFull || null,
        full: legacyFull || null,
        thumb: imageValue || null,
        crop: { cx: 0.5, cy: 0.5, w: 1 },
        status: imageValue ? 'a_verifier' : 'manquante',
        locked: false, provenance: { kind: 'legacy', value: imageValue || null },
      },
    };
    if (imageValue && !imageValue.startsWith('thumbs/')) review.push({ entryId: entry.id, issue: 'source_non_locale_ou_embarquee' });
    entries.push(entry);
  });
}

const workspace = {
  schemaVersion: 1, revision: 1, updatedAt: new Date().toISOString(),
  imageFormat: { ratio: 4 / 3, full: [800, 600], thumb: [213, 160], sourceOfTruth: '../atelier/lib.mjs' },
  categories, lists, entries, notes: [], history: [], trash: [],
};
const errors = validateWorkspace(workspace);
if (errors.length) throw new Error(errors.join('\n'));
fs.mkdirSync(outputDir, { recursive: true });
if (!fs.existsSync(outputPath)) fs.writeFileSync(outputPath, JSON.stringify(workspace, null, 2) + '\n');
const report = {
  generatedAt: new Date().toISOString(), sourceLists: merged.size,
  categories: categories.length, lists: lists.length, entries: entries.length,
  review, idempotent: fs.existsSync(outputPath),
};
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
