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
  const events = [];

  ws.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
      return;
    }
    if (message.method === 'Runtime.exceptionThrown') {
      events.push({ type: 'exception', details: message.params.exceptionDetails });
    }
    if (message.method === 'Runtime.consoleAPICalled') {
      events.push({
        type: 'console',
        level: message.params.type,
        text: message.params.args.map(a => a.value || a.description || '').join(' '),
      });
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
  await send('Page.enable');
  await send('Runtime.evaluate', {
    expression: "new Promise(resolve => { if (document.readyState === 'complete') resolve(true); else window.addEventListener('load', () => resolve(true), {once:true}); })",
    awaitPromise: true,
    returnByValue: true,
  });

  const result = await send('Runtime.evaluate', {
    expression: `JSON.stringify({
      ready: document.readyState,
      title: document.title,
      cards: document.querySelectorAll('#home-lists > *').length,
      homeText: (document.querySelector('#home-lists')?.innerText || '').slice(0, 600),
      bodyText: document.body.innerText.slice(0, 1000),
      listsType: typeof lists,
      listsLen: typeof lists === 'undefined' ? null : lists.length,
      defaultLen: typeof DEFAULT_LISTS === 'undefined' ? null : DEFAULT_LISTS.length,
      currentView: typeof currentView === 'undefined' ? null : currentView
    })`,
    returnByValue: true,
  });
  ws.close();

  console.log(result.result.result.value);
  if (events.length) {
    console.log('EVENTS');
    console.log(JSON.stringify(events, null, 2));
  }
}

main().catch(error => {
  console.error(error && error.stack || error);
  process.exit(1);
});
