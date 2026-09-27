/* sessionStorage is scoped to the current tab, unlike localStorage.
 * A blocked or full storage area must never stop the demo from working.
 */
function createDemoSession(fixtures, options = {}) {
  const key = "bureau-demo-session-v2";
  const ttl = 24 * 60 * 60 * 1000;
  const clock = options.clock || Date.now;
  const clone = value => JSON.parse(JSON.stringify(value));
  let storage = null;
  let persistent = false;
  try {
    storage = options.storage === undefined ? window.sessionStorage : options.storage;
    if (storage) {
      storage.setItem(key + "-probe", "1");
      storage.removeItem(key + "-probe");
      persistent = true;
    }
  } catch { storage = null; }
  const fresh = () => ({schema: 2, revision: fixtures.revision,
    id: crypto.randomUUID(), expiresAt: clock() + ttl, sequence: 0,
    events: clone(fixtures.events), drafts: {}});
  let state = fresh();
  let restored = false;
  if (storage) {
    try {
      const saved = JSON.parse(storage.getItem(key));
      if (saved && saved.schema === 2 && saved.revision === fixtures.revision &&
          typeof saved.id === "string" && /^[\da-f-]{36}$/i.test(saved.id) &&
          saved.expiresAt > clock() && saved.expiresAt <= clock() + ttl &&
          Number.isSafeInteger(saved.sequence) && saved.sequence >= 0 &&
          saved.drafts && typeof saved.drafts === "object" && !Array.isArray(saved.drafts) &&
          Object.entries(fixtures.events).every(([id]) => {
            const s = saved.events?.[id];
            return s?.id === id && [s.issues, s.actions, s.audit, s.outbox].every(Array.isArray) &&
              s.issues.every(i => i && typeof i.id === "string" && Array.isArray(i.depends_on) && Array.isArray(i.subject_ids) && i.details) &&
              s.actions.every(a => a && typeof a.id === "string" && a.payload && Array.isArray(a.evidence) && Array.isArray(a.checks)) &&
              s.records?.participants && s.records.groups && s.records.payments;
          })) {
        state = saved;
        restored = true;
      } else storage.removeItem(key);
    } catch { try { storage.removeItem(key); } catch { /* in-memory fallback */ } }
  }
  function save() {
    state.expiresAt = clock() + ttl;
    if (storage) {
      try { storage.setItem(key, JSON.stringify(state)); }
      catch { persistent = false; try { storage.removeItem(key); } catch { /* blocked */ } storage = null; }
    }
  }
  function expireIfNeeded() {
    if (state.expiresAt > clock()) return false;
    const next = fresh();
    // Preserve the events object held by the adapter, but replace its contents.
    for (const id of Object.keys(state.events)) delete state.events[id];
    Object.assign(state.events, next.events);
    Object.assign(state, {...next, events: state.events});
    restored = false;
    save();
    return true;
  }
  save();
  return {state, save, expireIfNeeded, info: () => ({id: state.id, expiresAt: state.expiresAt, persistent, restored})};
}
