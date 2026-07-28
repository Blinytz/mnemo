const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { URL } = require('node:url');

const ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(ROOT, 'data', 'atelier');
const STATE = path.join(DATA_DIR, 'workspace.json');
const HISTORY = path.join(DATA_DIR, 'history');
const ASSETS = path.join(ROOT, 'assets', 'atelier');
const WIKI_ROOT = path.resolve(ROOT, '..', 'wikideck');
const HOST = process.env.MEMO_HOST || '127.0.0.1';
const PORT = Number(process.env.MEMO_PORT || 3434);
const TOKEN = process.env.MEMO_ATELIER_TOKEN || crypto.randomBytes(18).toString('base64url');
const MIME = { '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.mjs':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8', '.json':'application/json; charset=utf-8', '.webp':'image/webp', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.svg':'image/svg+xml' };

function json(res, status, body) {
  res.writeHead(status, { 'Content-Type': MIME['.json'], 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(body));
}
function readBody(req, limit = 20 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const chunks = []; let size = 0;
    req.on('data', c => { size += c.length; if (size > limit) reject(new Error('Fichier trop volumineux')); else chunks.push(c); });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}
function readState() { return JSON.parse(fs.readFileSync(STATE, 'utf8')); }
function validate(data) {
  const errors = [];
  if (data?.schemaVersion !== 1) errors.push('schemaVersion invalide');
  for (const k of ['categories','lists','entries','notes']) if (!Array.isArray(data?.[k])) errors.push(`${k} invalide`);
  const ids = new Set();
  for (const group of ['categories','lists','entries','notes']) for (const item of data?.[group] || []) {
    if (!item.id || ids.has(item.id)) errors.push(`identifiant absent ou dupliqué: ${item.id || '?'}`);
    ids.add(item.id);
  }
  for (const entry of data?.entries || []) if (entry.image?.thumbSource) errors.push(`source miniature interdite: ${entry.id}`);
  return errors;
}
function atomicSave(next, previous) {
  fs.mkdirSync(HISTORY, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  if (previous) fs.writeFileSync(path.join(HISTORY, `${stamp}.json`), JSON.stringify(previous, null, 2) + '\n');
  const tmp = `${STATE}.tmp-${process.pid}`;
  fs.writeFileSync(tmp, JSON.stringify(next, null, 2) + '\n');
  fs.renameSync(tmp, STATE);
}
function safeAsset(relative) {
  const resolved = path.resolve(ROOT, relative.replace(/^\/+/, ''));
  if (!resolved.startsWith(ROOT + path.sep)) throw new Error('Chemin interdit');
  return resolved;
}
function serveFile(res, file) {
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) return json(res, 404, { error: 'Introuvable' });
  res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}
function authorized(req, url) {
  return HOST === '127.0.0.1' || req.headers['x-memo-token'] === TOKEN || url.searchParams.get('token') === TOKEN;
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    if (url.pathname === '/api/workspace' && req.method === 'GET') return json(res, 200, readState());
    if (url.pathname === '/api/workspace' && req.method === 'PUT') {
      if (!authorized(req, url)) return json(res, 403, { error: 'Jeton requis' });
      const previous = readState();
      const next = JSON.parse((await readBody(req)).toString('utf8'));
      if (Number(req.headers['if-match']) !== previous.revision) return json(res, 409, { error: 'Les données ont changé. Rechargez avant d’enregistrer.', revision: previous.revision });
      const errors = validate(next); if (errors.length) return json(res, 422, { errors });
      next.revision = previous.revision + 1; next.updatedAt = new Date().toISOString();
      atomicSave(next, previous);
      return json(res, 200, { revision: next.revision, updatedAt: next.updatedAt });
    }
    if (url.pathname.startsWith('/api/image/') && req.method === 'PUT') {
      if (!authorized(req, url)) return json(res, 403, { error: 'Jeton requis' });
      const [, , entryId, kind] = url.pathname.split('/');
      if (!/^[a-z0-9_-]+$/i.test(entryId) || !['original','full','thumb'].includes(kind)) return json(res, 400, { error: 'Cible invalide' });
      const body = await readBody(req);
      const dir = path.join(ASSETS, entryId); fs.mkdirSync(dir, { recursive: true });
      const target = path.join(dir, `${kind}.webp`), tmp = `${target}.tmp-${process.pid}`;
      fs.writeFileSync(tmp, body); fs.renameSync(tmp, target);
      return json(res, 200, { path: `assets/atelier/${entryId}/${kind}.webp`, bytes: body.length });
    }
    if (url.pathname === '/api/wikideck/preview' && req.method === 'POST') {
      const body = JSON.parse((await readBody(req)).toString('utf8'));
      const state = readState(); const cards = body.cards || [];
      const norm = s => String(s || '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
      const canon = s => { try { const u = new URL(s); u.hash=''; u.search=''; return decodeURI(u.toString().replace(/\/$/,'')); } catch { return String(s || '').trim(); } };
      const matches = cards.map(card => {
        const wiki = state.entries.filter(e => card.wikipedia && canon(e.wikipedia) === canon(card.wikipedia));
        const id = state.entries.filter(e => e.externalIds?.wikideck === card.id);
        const names = state.entries.filter(e => norm(e.name) === norm(card.name));
        const found = wiki.length === 1 ? wiki : id.length === 1 ? id : names;
        return { card, status: found.length === 1 ? (wiki.length || id.length ? 'certain' : 'probable') : found.length ? 'ambiguous' : 'wikideck_only', candidates: found.map(e => ({ id:e.id, name:e.name, listId:e.listId, locked:!!e.image?.locked })) };
      });
      return json(res, 200, { dryRun: true, matches, memoOnly: state.entries.filter(e => !matches.some(m => m.candidates.some(c => c.id === e.id))).map(e => e.id) });
    }
    if (url.pathname === '/api/wikideck/apply' && req.method === 'POST') {
      if (!authorized(req, url)) return json(res, 403, { error: 'Jeton requis' });
      const body = JSON.parse((await readBody(req)).toString('utf8'));
      if (body.confirm !== true) return json(res, 400, { error: 'Confirmation explicite requise' });
      const state = readState(), results = [];
      for (const decision of body.decisions || []) {
        const entry = state.entries.find(e => e.id === decision.entryId);
        const card = (body.cards || []).find(c => c.id === decision.cardId);
        if (!entry || !card) { results.push({ cardId:decision.cardId, status:'ignore', reason:'cible absente' }); continue; }
        if (entry.image?.locked && decision.replaceLocked !== true) { results.push({ cardId:card.id, status:'conflict', reason:'image verrouillée' }); continue; }
        const base = path.basename(card.image || card.rendered || `${card.id}.webp`);
        const wikiSlug = body.collection?.slug || '';
        const candidates = {
          original: [path.join(WIKI_ROOT,'images','originaux',wikiSlug,base), path.join(WIKI_ROOT,card.image || '')],
          full: [path.join(WIKI_ROOT,card.rendered || ''), path.join(WIKI_ROOT,'images','full',wikiSlug,base)],
          thumb: [path.join(WIKI_ROOT,card.thumb || ''), path.join(WIKI_ROOT,'images','thumbs',wikiSlug,base)],
        };
        const dir = path.join(ASSETS, entry.id); fs.mkdirSync(dir,{recursive:true});
        for (const kind of ['original','full','thumb']) {
          const source = candidates[kind].find(p => p.startsWith(WIKI_ROOT + path.sep) && fs.existsSync(p));
          if (source) fs.copyFileSync(source,path.join(dir,`${kind}.webp`));
        }
        entry.image = { ...entry.image, source:`assets/atelier/${entry.id}/original.webp`, full:`assets/atelier/${entry.id}/full.webp`, thumb:`assets/atelier/${entry.id}/thumb.webp`, crop:card.crop || entry.image?.crop || {cx:.5,cy:.5,w:1}, status:card.crop?'importee':'a_verifier', provenance:{kind:'wikideck',cardId:card.id,sourceUrl:card.sourceUrl||null}, locked:false };
        entry.externalIds = { ...(entry.externalIds||{}), wikideck:card.id };
        if (!entry.wikipedia && card.wikipedia) entry.wikipedia=card.wikipedia;
        results.push({cardId:card.id,entryId:entry.id,status:'imported'});
      }
      const errors=validate(state); if(errors.length)return json(res,422,{errors});
      state.revision+=1; state.updatedAt=new Date().toISOString(); atomicSave(state,readState());
      return json(res,200,{revision:state.revision,results});
    }
    if (url.pathname === '/api/health') return json(res, 200, { ok:true, localFiles:true, imageFormat:[800,600], writeProtected:HOST !== '127.0.0.1' });
    let relative = decodeURIComponent(url.pathname);
    if (relative === '/' || relative === '/atelier' || relative === '/atelier/') relative = '/atelier/index.html';
    return serveFile(res, safeAsset(relative));
  } catch (error) {
    console.error(error); return json(res, 500, { error: error.message });
  }
});
server.listen(PORT, HOST, () => {
  console.log(`Atelier Mémo : http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}/atelier/`);
  if (HOST !== '127.0.0.1') console.log(`Jeton mobile : ${TOKEN}`);
});
