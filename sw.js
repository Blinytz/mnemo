// Service worker de Mémo : fonctionnement hors ligne.
//
// Réseau d'abord, cache en secours : en ligne, on voit toujours la dernière
// version ; hors ligne, on retrouve ce qui a déjà servi.
//   - à l'installation : l'application (app/), le catalogue et les 79 listes
//     (environ 1,5 Mo), pour que révisions et quiz marchent sans réseau ;
//   - au fil de l'usage : chaque image affichée (les séances chargent d'avance
//     toutes leurs grandes images).
// version.json ne passe jamais par le cache : c'est lui qui annonce une
// nouvelle version à l'application installée.

const CACHE = 'memo-v94';
const COQUILLE = [
  './app/', './app/index.html', './app/style.css', './app/manifest.json', './manifest.json', './icone.svg',
  './app/js/main.js', './app/js/ui.js', './app/js/icones.js', './app/js/donnees.js',
  './app/js/progression.js', './app/js/correction.js', './app/js/questions.js',
  './app/js/eclats.js', './app/js/registre.js', './app/js/edition.js',
  './app/js/images-perso.js', './app/js/ecrans-edition.js',
  './data/catalogue.json', './memo.html',
];

// GitHub Pages sert tout avec « Cache-Control: max-age=600 » : sans précaution,
// le navigateur garde dix minutes l'ancienne version, et cache.addAll remplit
// le cache neuf avec des fichiers périmés. On contourne donc le cache HTTP à
// l'installation (reload) et on revalide à chaque lecture (no-cache).
async function mettreEnCache(cache, chemins) {
  await Promise.all(chemins.map(async f => {
    try {
      const r = await fetch(new Request(f, {cache: 'reload'}));
      if (r.ok) await cache.put(f, r);
    } catch {}
  }));
}

async function remplirCache() {
  const cache = await caches.open(CACHE);
  await mettreEnCache(cache, COQUILLE);
  // les listes, d'après le catalogue tout juste lu
  try {
    const cat = await (await cache.match('./data/catalogue.json')).json();
    const listes = cat.listes.map(l => `./data/listes/${l.id}.json`);
    for (let i = 0; i < listes.length; i += 10) await mettreEnCache(cache, listes.slice(i, i + 10));
  } catch {}
}

self.addEventListener('install', e => {
  e.waitUntil(remplirCache().then(() => self.skipWaiting(), () => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      // Le domaine blinytz.github.io est partagé par toutes les applications :
      // ne supprimer que les anciens caches de Mémo.
      Promise.all(keys.filter(k => k.startsWith('memo-') && k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  const memeOrigine = url.origin === self.location.origin;
  if (memeOrigine && url.pathname.endsWith('/version.json')) return;   // toujours le réseau
  // ailleurs, seules les polices sont gardées ; le registre commun (Supabase)
  // et les sites externes passent sans détour
  if (!memeOrigine && !/^fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) return;

  // Une requête de navigation ne se clone pas avec un autre mode de cache :
  // on la reconstruit depuis son adresse.
  const requete = memeOrigine ? new Request(e.request.url, {cache: 'no-cache'}) : e.request;
  e.respondWith(
    fetch(requete)
      .then(resp => {
        if (resp.status === 200 && (memeOrigine || resp.type === 'cors')) {
          const copie = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, copie));
        }
        return resp;
      })
      // hors ligne : la version gardée, en ignorant les ?v=… ajoutés pour contourner les caches
      .catch(() => caches.match(e.request, {ignoreSearch: memeOrigine}))
  );
});
