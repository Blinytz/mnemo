const CACHE = 'memo-v92';
const PRECACHE = ['./memo.html', './manifest.json'];

// GitHub Pages sert tout avec « Cache-Control: max-age=600 » : sans précaution,
// le navigateur garde dix minutes l'ancienne version, et cache.addAll remplit
// le cache neuf avec des fichiers périmés qui y restent. On contourne donc le
// cache HTTP à l'installation (reload) et on revalide à chaque lecture (no-cache).
async function remplirCache() {
  const cache = await caches.open(CACHE);
  await Promise.all(PRECACHE.map(async f => {
    try {
      const r = await fetch(new Request(f, { cache: 'reload' }));
      if (r.ok) await cache.put(f, r);
    } catch {}
  }));
}

self.addEventListener('install', e => {
  e.waitUntil(remplirCache().then(() => self.skipWaiting(), () => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const memeOrigine = new URL(e.request.url).origin === self.location.origin;

  // Network-first partout : les images locales changent souvent pendant les audits.
  // Le cache ne sert que de secours hors ligne, jamais de source prioritaire.
  // Une requête de navigation ne se clone pas avec un autre mode de cache :
  // on la reconstruit depuis son adresse.
  const requete = memeOrigine ? new Request(e.request.url, { cache: 'no-cache' }) : e.request;
  e.respondWith(
    fetch(requete)
      .then(resp => {
        const copy = resp.clone();
        if (resp.status === 200) {
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return resp;
      })
      .catch(() => caches.match(e.request))
  );
});
