import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root=path.resolve('.');
test('migration idempotente et données consommables',()=>{
  execFileSync(process.execPath,['atelier/migrate.mjs'],{cwd:root});
  const a=fs.readFileSync(path.join(root,'data/atelier/workspace.json'),'utf8');
  execFileSync(process.execPath,['atelier/migrate.mjs'],{cwd:root});
  const b=fs.readFileSync(path.join(root,'data/atelier/workspace.json'),'utf8');
  assert.equal(a,b);
  const data=JSON.parse(a);
  assert.ok(data.categories.length>0&&data.lists.length>20&&data.entries.length>500);
});

test('les images F1 choisies dans WikiDeck sont présentes',()=>{
  const wiki=JSON.parse(fs.readFileSync(path.resolve('../wikideck/data/pilotes-f1-champions-du-monde.json'),'utf8'));
  assert.ok(wiki.cartes.length>=35);
  for(const card of wiki.cartes){
    assert.ok(fs.existsSync(path.resolve('../wikideck',card.imageUrl)),card.nom);
    assert.ok(fs.existsSync(path.resolve('../wikideck',card.thumbUrl)),card.nom);
  }
});

test('aucun appel autonome n’est actif dans les deux déclencheurs',()=>{
  const html=fs.readFileSync(path.join(root,'memo.html'),'utf8');
  assert.match(html,/function autoResolveCurrentListImages\(\) \{\s*\/\/[^\n]*\n\s*\/\/[^\n]*\n\s*return;/);
  assert.match(html,/function maybeAutoUpdateImagesOnce\(\) \{\s*\/\/[^\n]*\n\s*return;/);
});
