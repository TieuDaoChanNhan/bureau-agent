// Web UI skeleton (TASK T06). Talks only to the JSON API in api/main.py.
// Implemented: load events and list issues of the selected event.
// To do: issue detail (decision trace, checks), approve / edit / dismiss,
// travel option table, "run agent" button. See web/reference/mockup.html.

const state = { events: [], current: null, issues: [] };

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

function renderEvents() {
  const el = document.getElementById("events");
  el.innerHTML = state.events.map(e => `
    <button class="card" data-id="${e.id}" aria-pressed="${state.current === e.id}">
      <strong>${e.name}</strong>
      <span>${e.counts.blocking} blocking · ${e.counts.non_blocking} non-blocking · ${e.counts.resolved} resolved</span>
    </button>`).join("");
}

function renderIssues() {
  const el = document.getElementById("issues");
  const row = i => `<li class="${i.blocking ? "blocking" : ""}"><code>${i.kind}</code> ${i.title}
      <span class="muted">(${i.status})</span></li>`;
  el.innerHTML = `<h2>Issues</h2><ul>${state.issues.map(row).join("")}</ul>`;
  // TODO(T06): click an issue -> render its proposed action in #detail
}

async function selectEvent(id) {
  state.current = id;
  const data = await api(`/api/events/${id}`);
  state.issues = data.issues;
  renderEvents();
  renderIssues();
}

document.getElementById("events").addEventListener("click", e => {
  const card = e.target.closest(".card");
  if (card) selectEvent(card.dataset.id);
});

(async () => {
  try {
    state.events = await api("/api/events");
    renderEvents();
    if (state.events.length) selectEvent(state.events[0].id);
  } catch (err) {
    document.getElementById("events").textContent = `API not reachable: ${err.message}`;
  }
})();
