const port = process.argv[2] || "9224";

async function json(url) {
  const r = await fetch(url);
  return r.json();
}

async function main() {
  const tabs = await json(`http://127.0.0.1:${port}/json`);
  const tab = tabs.find(t => t.type === "page");
  if (!tab) throw new Error("No page tab");
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  };
  await new Promise(resolve => ws.onopen = resolve);
  const send = (method, params = {}) => new Promise(resolve => {
    const msgId = ++id;
    pending.set(msgId, resolve);
    ws.send(JSON.stringify({ id: msgId, method, params }));
  });
  await send("Runtime.enable");
  const expr = `({
    cards: document.querySelectorAll('#home-lists > *').length,
    v: typeof APP_DATA_VERSION !== 'undefined' ? APP_DATA_VERSION : null,
    db: typeof DB_PREFIX !== 'undefined' ? DB_PREFIX : null,
    lune2: localFullImageForThumb('thumbs/lunes/2.webp', 'lunes', 1, 1),
    lune10: localFullImageForThumb('thumbs/lunes/10.webp', 'lunes', 1, 9),
    lune15: localFullImageForThumb('thumbs/lunes/15.webp', 'lunes', 1, 14)
  })`;
  const out = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
  console.log(JSON.stringify(out.result.result.value));
  ws.close();
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
