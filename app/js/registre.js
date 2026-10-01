// Client du registre commun d'Éclats (partagé avec Pronos, Missions, Sport,
// Rédac, Cagnottes et Centrale). Copie du client de Sport, avec APP_ID = memo.
//
// Mémo ne fait que CRÉDITER : le gain du quiz du jour, collecté par
// l'utilisateur (`eclats_reward`). Aucune dépense n'est exposée ici.
//
// Aucune clé secrète : seule la clé publishable, comme les autres applications.
// La session vit sous `eclats_session`, partagée entre toutes les applications
// de blinytz.github.io : se connecter une fois suffit.
//
// Fabrique injectable (fetch, storage) pour rester testable hors navigateur.

export const REGISTRE_CONFIG = {
  url: 'https://psutbulpezfdftmaqkoo.supabase.co',
  anonKey: 'sb_publishable_KTE_3tQq6eGEo4z2f4QrUA_v7F4K4fT',
};

export const APP_ID = 'memo';

export function createRegistre({
  url = REGISTRE_CONFIG.url,
  anonKey = REGISTRE_CONFIG.anonKey,
  sessionKey = 'eclats_session',
  fetch: fetchImpl,
  storage,
} = {}) {
  const doFetch = fetchImpl
    || (typeof globalThis !== 'undefined' && globalThis.fetch
      ? (...a) => globalThis.fetch(...a) : null);
  const store = storage
    || (typeof globalThis !== 'undefined' && globalThis.localStorage) || memoryStorage();
  if (!doFetch) throw new Error('Aucune implémentation fetch disponible.');

  let session = null;
  try { session = JSON.parse(store.getItem(sessionKey) || 'null'); } catch { session = null; }

  function saveSession(s) {
    session = s;
    if (s) store.setItem(sessionKey, JSON.stringify(s));
    else store.removeItem(sessionKey);
  }

  function utilisateur() { return session ? session.user : null; }
  function estConnecte() { return !!session?.access_token; }

  async function connexion(email, motDePasse) {
    const r = await doFetch(`${url}/auth/v1/token?grant_type=password`, {
      method: 'POST',
      headers: { apikey: anonKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: motDePasse }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error_description || data.msg || 'Connexion refusée');
    saveSession(data);
    return data.user;
  }

  function deconnexion() { saveSession(null); }

  async function rafraichir() {
    if (!session?.refresh_token) return false;
    const r = await doFetch(`${url}/auth/v1/token?grant_type=refresh_token`, {
      method: 'POST',
      headers: { apikey: anonKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: session.refresh_token }),
    });
    if (!r.ok) { saveSession(null); return false; }
    saveSession(await r.json());
    return true;
  }

  async function appel(path, options = {}, dejaRetente = false) {
    const entetes = {
      apikey: anonKey,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (session?.access_token) entetes.Authorization = `Bearer ${session.access_token}`;
    const r = await doFetch(`${url}${path}`, { ...options, headers: entetes });
    if (r.status === 401 && !dejaRetente && await rafraichir()) {
      return appel(path, options, true);
    }
    const texte = await r.text();
    if (!r.ok) {
      let message = `Erreur ${r.status}`;
      try { message = JSON.parse(texte).message || message; } catch { /* corps non JSON */ }
      const err = new Error(message);
      err.status = r.status;
      throw err;
    }
    if (!texte) return null;
    try { return JSON.parse(texte); } catch { return null; }
  }

  function rpc(fonction, args = {}) {
    return appel(`/rest/v1/rpc/${fonction}`, { method: 'POST', body: JSON.stringify(args) });
  }

  async function solde() {
    const v = await rpc('eclats_balance');
    return Number(v) || 0;
  }

  /** Crédit idempotent : le gain d'un quiz du jour, à la collecte. */
  function recompenser({ montant, reason, referenceType, referenceId, idempotencyKey, metadata }) {
    return rpc('eclats_reward', {
      p_app_id: APP_ID,
      p_amount: montant,
      p_reason: reason,
      p_reference_type: referenceType,
      p_reference_id: referenceId ?? null,
      p_idempotency_key: idempotencyKey,
      p_metadata: metadata ?? null,
    });
  }

  function mouvements({ limit = 50, appId = APP_ID } = {}) {
    const params = new URLSearchParams({
      select: 'id,app_id,amount,kind,reason,reference_type,reference_id,occurred_at',
      order: 'occurred_at.desc',
      limit: String(limit),
    });
    if (appId) params.set('app_id', `eq.${appId}`);
    return appel(`/rest/v1/eclats_ledger?${params.toString()}`);
  }

  return {
    utilisateur,
    estConnecte,
    connexion,
    deconnexion,
    solde,
    recompenser,
    mouvements,
    _appel: appel,
    _rpc: rpc,
  };
}

function memoryStorage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
  };
}
