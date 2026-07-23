#!/usr/bin/env node
const http = require('http');

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, response => {
      let body = '';
      response.on('data', chunk => { body += chunk; });
      response.on('end', () => resolve(JSON.parse(body)));
    }).on('error', reject);
  });
}

async function main() {
  const port = process.argv[2] || '9224';
  const tabs = await getJson(`http://127.0.0.1:${port}/json`);
  const tab = tabs.find(t => t.type === 'page');
  if (!tab) throw new Error('No page tab found');
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let nextId = 0;
  const pending = new Map();
  ws.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
    }
  };
  await new Promise(resolve => { ws.onopen = resolve; });
  function send(method, params = {}) {
    return new Promise(resolve => {
      const id = ++nextId;
      pending.set(id, resolve);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }
  await send('Runtime.enable');
  const result = await send('Runtime.evaluate', {
    expression: `JSON.stringify({
      ready: document.readyState,
      cards: document.querySelectorAll('#home-lists > *').length,
      v: typeof APP_DATA_VERSION === 'undefined' ? null : APP_DATA_VERSION,
      db: typeof DB_PREFIX === 'undefined' ? null : DB_PREFIX,
      f1: typeof lists === 'undefined' ? null : lists.find(l => l.id === 'f1_champions')?.columns,
      defaultF1: typeof DEFAULT_LISTS === 'undefined' ? null : DEFAULT_LISTS.find(l => l.id === 'f1_champions')?.columns,
      storageKeys: Object.keys(localStorage).filter(k => k.startsWith('memo_'))
    })`,
    returnByValue: true,
  });
  ws.close();
  console.log(result.result.result.value);
}

main().catch(error => {
  console.error(error && error.stack || error);
  process.exit(1);
});
