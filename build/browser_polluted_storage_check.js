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
  const port = process.argv[2] || '9225';
  const tabs = await getJson(`http://127.0.0.1:${port}/json`);
  const tab = tabs.find(t => t.type === 'page');
  if (!tab) throw new Error('No page tab found');
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let nextId = 0;
  const pending = new Map();
  const events = [];
  ws.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
      return;
    }
    if (message.method === 'Runtime.exceptionThrown') events.push(message.params.exceptionDetails);
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
  await send('Page.enable');
  await send('Runtime.evaluate', {
    expression: "new Promise(resolve => { if (document.readyState === 'complete') resolve(true); else window.addEventListener('load', () => resolve(true), {once:true}); })",
    awaitPromise: true,
    returnByValue: true,
  });
  await send('Runtime.evaluate', {
    expression: `(() => {
      const big = 'x'.repeat(350000);
      for (let i = 1; i <= 20; i++) {
        try { localStorage.setItem('memo_v' + i + '_local_junk', big); } catch {}
      }
      return localStorage.length;
    })()`,
    returnByValue: true,
  });
  await send('Page.reload', { ignoreCache: true });
  await new Promise(resolve => setTimeout(resolve, 1800));
  const result = await send('Runtime.evaluate', {
    expression: `JSON.stringify({
      ready: document.readyState,
      cards: document.querySelectorAll('#home-lists > *').length,
      text: document.body.innerText.slice(0, 500),
      storageKeys: Object.keys(localStorage).filter(k => k.startsWith('memo_')).length
    })`,
    returnByValue: true,
  });
  ws.close();
  console.log(result.result.result.value);
  if (events.length) console.log(JSON.stringify(events, null, 2));
}

main().catch(error => {
  console.error(error && error.stack || error);
  process.exit(1);
});
