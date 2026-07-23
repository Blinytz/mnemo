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
  const tab = tabs.find(item => item.type === 'page');
  if (!tab) throw new Error('No page tab found');
  const socket = new WebSocket(tab.webSocketDebuggerUrl);
  let nextId = 0;
  const pending = new Map();
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
    }
  };
  await new Promise(resolve => { socket.onopen = resolve; });
  const send = (method, params = {}) => new Promise(resolve => {
    const id = ++nextId;
    pending.set(id, resolve);
    socket.send(JSON.stringify({ id, method, params }));
  });
  await send('Runtime.enable');
  const result = await send('Runtime.evaluate', {
    expression: `new Promise(async resolve => {
      const report = [];
      for (const list of lists) {
        openTable(list.id);
        const scrollTargets = [
          document.querySelector('#table-wrap'),
          document.querySelector('.table-scroll'),
          document.scrollingElement,
        ].filter(Boolean);
        for (let step = 0; step <= 8; step += 1) {
          for (const target of scrollTargets) target.scrollTop = target.scrollHeight * step / 8;
          window.scrollTo(0, document.documentElement.scrollHeight * step / 8);
          await new Promise(done => setTimeout(done, 90));
        }
        const deadline = Date.now() + 5000;
        let images = [];
        do {
          await new Promise(done => setTimeout(done, 150));
          images = Array.from(document.querySelectorAll('#table-wrap img'));
        } while (Date.now() < deadline && images.some(image => !image.complete || image.naturalWidth === 0));
        report.push({
          id: list.id,
          expected: list.rows.length * list.columns.filter(column => /(image|localisation)/i.test(column)).length,
          rendered: images.length,
          loaded: images.filter(image => image.complete && image.naturalWidth > 0).length,
          broken: images.filter(image => !image.complete || image.naturalWidth === 0).map(image => image.getAttribute('src')).slice(0, 3)
        });
      }
      resolve(JSON.stringify(report));
    })`,
    awaitPromise: true,
    returnByValue: true,
  });
  socket.close();
  const report = JSON.parse(result.result.result.value);
  console.log(JSON.stringify(report, null, 2));
  const failed = report.filter(item => item.rendered !== item.expected || item.loaded !== item.rendered || item.broken.length);
  if (failed.length) process.exitCode = 1;
}

main().catch(error => { console.error(error.stack || error); process.exit(1); });
