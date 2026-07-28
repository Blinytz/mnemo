import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const wikiRoot = path.resolve(here, '..', '..', 'wikideck');
const args = process.argv.slice(2);
const slug = args[0] || 'pilotes-f1-champions-du-monde';
const destination = path.resolve(args[1] || path.join(here, 'exports', slug));
const collection = JSON.parse(fs.readFileSync(path.join(wikiRoot, 'data', `${slug}.json`), 'utf8'));
const notes = JSON.parse(fs.readFileSync(path.join(wikiRoot, 'build', 'notes_atelier.json'), 'utf8'));
const sources = JSON.parse(fs.readFileSync(path.join(wikiRoot, 'build', 'images_sources.json'), 'utf8'));
fs.mkdirSync(path.join(destination, 'images'), { recursive: true });

const manifest = {
  schemaVersion: 1, source: 'wikideck', exportedAt: new Date().toISOString(),
  collection: { name: collection.collection, slug: collection.slug },
  cards: collection.cartes.map(card => {
    const candidates = [
      path.join(wikiRoot, 'images', 'originaux', slug, path.basename(card.imageUrl)),
      path.join(wikiRoot, card.imageUrl),
    ];
    const sourceFile = candidates.find(fs.existsSync);
    const relative = sourceFile ? `images/${path.basename(sourceFile)}` : null;
    if (sourceFile) fs.copyFileSync(sourceFile, path.join(destination, relative));
    return {
      id: card.id, name: card.nom, number: card.numero,
      wikipedia: card.lienWikipedia || '', fields: card,
      image: relative, rendered: card.imageUrl, thumb: card.thumbUrl,
      sourceUrl: sources[card.id]?.url || sources[card.id]?.source || null,
      crop: notes.cadrages?.[card.id] || null,
    };
  }),
};
fs.writeFileSync(path.join(destination, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(`Paquet exporté : ${destination} (${manifest.cards.length} cartes)`);
