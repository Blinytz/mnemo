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
    expression: `new Promise(resolve => {
      if (typeof openTable === 'function') openTable('mythologie');
      setTimeout(() => {
        const list = typeof lists === 'undefined' ? null : lists.find(l => l.id === 'mythologie');
        const imgs = Array.from(document.querySelectorAll('#table-wrap img'));
        resolve(JSON.stringify({
          version: typeof APP_DATA_VERSION === 'undefined' ? null : APP_DATA_VERSION,
          db: typeof DB_PREFIX === 'undefined' ? null : DB_PREFIX,
          currentListId: typeof currentListId === 'undefined' ? null : currentListId,
          rowCount: list ? list.rows.length : null,
          columns: list ? list.columns : null,
          imgCount: imgs.length,
          complete: imgs.filter(img => img.complete && img.naturalWidth > 0).length,
          broken: imgs.filter(img => !img.complete || img.naturalWidth === 0).map(img => img.getAttribute('src')).slice(0, 20),
          firstImages: imgs.slice(0, 12).map(img => ({
            src: img.getAttribute('src'),
            complete: img.complete,
            width: img.naturalWidth,
            height: img.naturalHeight,
            alt: img.getAttribute('alt')
          }))
        }));
      }, 800);
    })`,
    awaitPromise: true,
    returnByValue: true,
  });
  ws.close();
  console.log(result.result.result.value);
}

main().catch(error => {
  console.error(error && error.stack || error);
  process.exit(1);
});
