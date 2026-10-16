/* Frontend MVP (Agent 6). Рекомендации всегда из backend, не генерируются в UI. */
const $ = (id) => document.getElementById(id);
const state = { heroes: [], picks: { radiantPicks: [], direPicks: [], radiantBans: [], direBans: [] }, lastRecs: [] };
const backend = () => ($("backendUrl").value || "http://localhost:8000").replace(/\/$/, "");
const selectedAll = () => new Set([...state.picks.radiantPicks, ...state.picks.direPicks, ...state.picks.radiantBans, ...state.picks.direBans]);

async function api(path, opts) {
  const r = await fetch(backend() + path, opts);
  if (!r.ok) throw new Error(`API ${r.status}: ${(await r.text()).slice(0, 300)}`);
  return r.json();
}

async function loadHeroes() {
  $("status").textContent = "Загрузка героев…";
  try {
    const data = await api("/heroes");
    state.heroes = data.heroes || [];
    $("dbMode").textContent = `mode=${data.db_mode || "?"} · updated=${data.data_updated_at || "?"}`;
    $("dataUpdated").textContent = `data_updated_at: ${data.data_updated_at || "?"}`;
    const roles = new Set(); state.heroes.forEach(h => (h.roles || []).forEach(r => roles.add(r)));
    $("roleFilter").innerHTML = `<option value="">— любая —</option>` + [...roles].sort().map(r => `<option>${r}</option>`).join("");
    renderAll();
    $("status").textContent = `Героев: ${state.heroes.length}. Готово к рекомендации.`;
  } catch (e) {
    $("status").textContent = `Ошибка загрузки героев: ${e.message}. Проверьте backend (docker compose up backend).`;
  }
}

function heroById(id) { return state.heroes.find(h => h.id === id); }

function renderAll() { renderChips(); renderGrid(); }

function renderChips() {
  for (const key of Object.keys(state.picks)) {
    const el = $(key); el.innerHTML = "";
    state.picks[key].forEach(id => {
      const h = heroById(id); const d = document.createElement("span"); d.className = "chip";
      d.innerHTML = `${h ? h.localized_name : id} <button aria-label="убрать">×</button>`;
      d.querySelector("button").onclick = () => { state.picks[key] = state.picks[key].filter(x => x !== id); renderAll(); };
      el.appendChild(d);
    });
    if (!state.picks[key].length) el.innerHTML = `<span class="muted">— пусто —</span>`;
  }
}

function renderGrid() {
  const q = ($("search").value || "").toLowerCase(), role = $("roleFilter").value;
  const sel = selectedAll(), g = $("heroGrid"); g.innerHTML = "";
  const list = state.heroes.filter(h =>
    (!q || h.localized_name.toLowerCase().includes(q)) && (!role || (h.roles || []).includes(role)));
  $("heroCount").textContent = `· ${list.length}/${state.heroes.length}`;
  list.forEach(h => {
    const d = document.createElement("div"); d.className = "hero" + (sel.has(h.id) ? " disabled" : "");
    d.innerHTML = `<b>${h.localized_name}</b><div class="roles">${(h.roles || []).join(", ") || "—"}</div><div class="muted">#${h.id}</div>`;
    d.title = sel.has(h.id) ? "Уже выбран/забанен" : `Добавить в ${$("pickTarget").selectedOptions[0].text}`;
    d.onclick = () => {
      if (sel.has(h.id)) return;
      state.picks[$("pickTarget").value].push(h.id); renderAll();
    };
    g.appendChild(d);
  });
  if (!list.length) g.innerHTML = `<span class="muted">Ничего не найдено.</span>`;
}

function draftRequest() {
  return {
    radiant_picks: state.picks.radiantPicks, dire_picks: state.picks.direPicks,
    radiant_bans: state.picks.radiantBans, dire_bans: state.picks.direBans,
    team_to_pick: $("teamToPick").value,
    requested_roles: $("roleFilter").value ? [$("roleFilter").value] : [],
    limit: parseInt($("limit").value, 10) || 10,
  };
}

async function recommend() {
  const req = draftRequest();
  $("loading").classList.remove("hidden"); $("recList").innerHTML = "";
  $("status").textContent = "Считаем рекомендации (SQL + scoring.py)…";
  try {
    const data = await api("/recommendations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(req) });
    state.lastRecs = data.recommendations || [];
    $("dataUpdated").textContent = `data_updated_at: ${data.data_updated_at}`;
    const stale = (data.data_updated_at || "").startsWith("2026-01-01");
    $("warnStale").classList.toggle("hidden", !stale);
    if (stale) $("warnStale").textContent = "Данные seed/demo (БД без свежих sync). Запустите n8n initial_load или loader для свежих данных OpenDota.";
    if (!state.lastRecs.length) { $("status").textContent = "Пусто: все герои выбраны/забанены."; return; }
    const low = state.lastRecs.filter(r => r.confidence === "low").length;
    $("status").textContent = `Топ-${state.lastRecs.length} (кандидатов: ${data.meta?.total_candidates}, исключено: ${data.meta?.excluded}, engine: ${data.meta?.engine}). Низкая уверенность: ${low}.`;
    if (data.rag_context?.length) $("status").textContent += ` RAG-контекст: ${data.rag_context.length} сценариев.`;
    renderRecs(req);
  } catch (e) {
    $("status").textContent = `Ошибка API: ${e.message}`;
  } finally { $("loading").classList.add("hidden"); }
}

function renderRecs(req) {
  const box = $("recList"); box.innerHTML = "";
  state.lastRecs.forEach((r, i) => {
    const h = heroById(r.hero_id);
    const d = document.createElement("div"); d.className = "rec";
    d.innerHTML = `
      <div class="top"><b>#${i + 1} ${h ? h.localized_name : "Hero " + r.hero_id}</b>
      <span>score <b>${r.score.toFixed(2)}</b> <span class="conf ${r.confidence}">${r.confidence}</span></span></div>
      <div class="scorebar"><div style="width:${Math.round(r.score * 100)}%"></div></div>
      <div class="reasons">${r.reasons.map(x => `• [${x.type}] ${x.summary}${x.against_hero_id ? ` (vs #${x.against_hero_id}${heroById(x.against_hero_id) ? " " + heroById(x.against_hero_id).localized_name : ""})` : ""} — ${x.games_played} игр`).join("<br>") || "—"}</div>
      ${r.caveats.map(c => `<div class="caveat">⚠ ${c}</div>`).join("")}
      <button>Объяснить</button><div class="expl hidden"></div>`;
    const [btn, expl] = [d.querySelector("button"), d.querySelector(".expl")];
    btn.onclick = async () => {
      btn.disabled = true; expl.classList.remove("hidden"); expl.textContent = "Объясняем (факты из scoring, без выдуманных цифр)…";
      try {
        const ex = await api("/explain", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...req, hero_id: r.hero_id }) });
        expl.textContent = ex.explanation + (ex.llm_generated ? " [LLM]" : " [template: цифры из scoring]");
      } catch (e) { expl.textContent = "Ошибка объяснения: " + e.message; }
      btn.disabled = false;
    };
    box.appendChild(d);
  });
}

$("recommendBtn").onclick = recommend;
$("refreshHeroes").onclick = loadHeroes;
$("clearBtn").onclick = () => { state.picks = { radiantPicks: [], direPicks: [], radiantBans: [], direBans: [] }; $("recList").innerHTML = ""; renderAll(); };
$("search").oninput = renderGrid; $("roleFilter").onchange = renderGrid; $("pickTarget").onchange = renderGrid;
window.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(location.search);
  if (params.get("backend")) $("backendUrl").value = params.get("backend");
  loadHeroes();
});
