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
    expression: `new Promise(resolve => {
      const before = {
        cards: document.querySelectorAll('.list-card').length,
        groups: document.querySelectorAll('.list-group').length,
        reset: !!document.querySelector('#btn-reset-list'),
        categoryButton: !!document.querySelector('#btn-new-category')
      };
      document.querySelector('#btn-new-category').click();
      document.querySelector('#new-category-name').value = 'Essai catégorie';
      document.querySelector('#new-category-icon').value = '🧪';
      document.querySelector('#new-category-save').click();
      document.querySelector('#btn-new-list').click();
      const categoryOption = Array.from(document.querySelector('#new-list-category').options).find(option => option.textContent.includes('Essai catégorie'));
      document.querySelector('#new-list-name').value = 'Liste de contrôle';
      document.querySelector('#new-list-cols').value = 'Numéro, Nom';
      document.querySelector('#new-list-category').value = categoryOption?.value || '';
      document.querySelector('#new-list-save').click();
      const customList = lists.find(list => list.name === 'Liste de contrôle');
      openTable('pays');
      const continentIndex = lists.find(list => list.id === 'pays').columns.indexOf('Continent');
      document.querySelector('.sort-column[data-ci="' + continentIndex + '"]').click();
      setTimeout(() => {
        const rows = Array.from(document.querySelectorAll('#table-wrap tbody tr')).slice(0, 8).map(row => Array.from(row.cells).map(cell => cell.innerText.trim()));
        resolve(JSON.stringify({before, customList, customCategory:categories.find(category => category.name === 'Essai catégorie'), continentIndex, sort:tableSort.pays, rows}));
      }, 100);
    })`,
    awaitPromise: true,
    returnByValue: true,
  });
  socket.close();
  const check = JSON.parse(result.result.result.value);
  console.log(JSON.stringify(check, null, 2));
  if (check.before.cards < 30 || check.before.groups < 5 || check.before.reset || !check.before.categoryButton || check.sort.ci !== check.continentIndex || !check.customCategory || check.customList?.categoryId !== check.customCategory.id) process.exitCode = 1;
}

main().catch(error => { console.error(error.stack || error); process.exit(1); });
