import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { IMAGE_FORMAT, canonicalWikipedia, matchWikideckCard, previewBulk, stableId, validateWorkspace } from '../lib.mjs';

test('le format de grande image est exactement celui de WikiDeck', async () => {
  const source = fs.readFileSync(path.resolve('../wikideck/atelier/editeur.js'), 'utf8');
  const match = source.match(/EXPORT_FULL\s*=\s*\[(\d+),\s*(\d+)\]/);
  assert.deepEqual(IMAGE_FORMAT.full, match.slice(1).map(Number));
  assert.deepEqual(IMAGE_FORMAT.thumb, [213, 160]);
});

test('une miniature ne peut pas avoir de source indépendante', () => {
  const data = { schemaVersion:1, categories:[{id:'c'}], lists:[{id:'l',categoryId:'c'}], entries:[{id:'e',listId:'l',image:{thumbSource:'interdit'}}], notes:[] };
  assert.match(validateWorkspace(data).join(' '), /source miniature interdite/);
});

test('numéro et nom ne déterminent pas l’identifiant stable', () => {
  const id = stableId('entry','liste','position','nom');
  const entry = { id, number:'1', name:'Avant' };
  entry.number='51'; entry.name='Après';
  assert.equal(entry.id,id);
});

test('Wikipedia est canonisé pour le rapprochement', () => {
  assert.equal(canonicalWikipedia('http://fr.wikipedia.org/wiki/Jean Dupont?x=1#A'), 'https://fr.wikipedia.org/wiki/Jean_Dupont');
});

test('import WikiDeck distingue certain, probable et ambigu', () => {
  const card={id:'f1_x',nom:'X',lienWikipedia:'https://fr.wikipedia.org/wiki/X'};
  assert.equal(matchWikideckCard(card,[{id:'e',name:'X',wikipedia:card.lienWikipedia}]).kind,'certain');
  assert.equal(matchWikideckCard({...card,lienWikipedia:''},[{id:'e',name:'X'}]).kind,'certain');
  assert.equal(matchWikideckCard({...card,lienWikipedia:''},[{id:'e1',name:'X'},{id:'e2',name:'X'}]).kind,'ambiguous');
});

test('une opération collective produit un diff limité à la sélection', () => {
  const diff=previewBulk([{id:'a',number:'1'},{id:'b',number:'9'}],{type:'renumber',start:51});
  assert.deepEqual(diff.map(x=>x.after),['51','52']);
});
