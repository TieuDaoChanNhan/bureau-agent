// Additional controls for the browser-only customer demo.
function refreshSessionNotice() {
  const node = document.querySelector("#sessionNotice");
  if (!node) return;
  const info = demoStore.sessionInfo();
  node.textContent = info.persistent
    ? "Progress survives refreshes in this tab for 24 hours after your last interaction."
    : "Your browser cannot save progress here. Refreshing will start a fresh demo.";
}

function restoreSessionUI() {
  ui.drafts = demoStore.drafts();
  ui.sel = {};
  for (const event of demoStore.request("/api/events")) store(event);
  ui.outbox = ui.current ? demoStore.request(`/api/events/${ui.current}/outbox`) : [];
  if (ui.current) ui.sel[ui.current] = firstKey(summary());
}

function plannerControls(action, decided) {
  if (decided) return "";
  const hard = action.payload.constraints.hard;
  return `<details class="card"><summary>Try your own constraints</summary>
    <p class="note">Re-check the saved packages. Sample prices stay fixed when group size changes; this checks capacity, not a new quote.</p>
    <form id="scenarioForm" class="compose scenario-controls">
      <label>Budget per person (€)<input name="budget" type="number" min="1" max="1000" step="0.01" required value="${esc(hard.max_cost_per_person_cents / 100)}"></label>
      <label>People<input name="people" type="number" min="1" max="200" step="1" required value="${esc(hard.participants)}"></label>
      <label>Arrive before<input name="arrival" type="time" required value="${esc(hard.arrive_before)}"></label>
      <button type="submit" class="btn primary">Compare sample packages</button>
    </form></details>`;
}

document.querySelector("#detail").addEventListener("submit", event => {
  if (event.target.id !== "scenarioForm") return;
  event.preventDefault();
  if (ui.busy) return;
  const form = event.target;
  const overrides = {
    max_cost_per_person_cents: Math.round(Number(form.budget.value) * 100),
    participants: Number(form.people.value),
    arrive_before: form.arrival.value,
  };
  busy("Comparing sample packages with your constraints…", async () => {
    const data = await api(`/api/events/${encodeURIComponent(ui.current)}/plan`, {
      method: "POST", body: JSON.stringify({text: planRequestText(), overrides}),
    });
    store(data);
    const action = data.actions.find(a => a.id === data.action_id);
    setRun(`${action.payload.ranked_valid.length} sample package(s) meet your verified constraints. No live quotes or bookings.`);
  });
});
