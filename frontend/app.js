/* Agent 6 — главное меню: Драфт / Топ / Новости / Настройки.
   Правила: цифры ТОЛЬКО из backend (DB через API), score в UI не считается. */
const $ = (id) => document.getElementById(id);
const MAX_PICKS = 5;
const state = { heroes: [], picks: { radiantPicks: [], direPicks: [], radiantBans: [], direBans: [] }, lastRecs: [], lastReq: null, lastError: null, topLoaded: false, newsLoaded: false };

// --- settings (persist) ---
const store = {
  get backend() { return localStorage.getItem("drafter.backend") || "http://localhost:8000"; },
  set backend(v) { localStorage.setItem("drafter.backend", v); },
  get limit() { return localStorage.getItem("drafter.limit") || "10"; },
  set limit(v) { localStorage.setItem("drafter.limit", v); },
};
const backend = () => (store.backend || "http://localhost:8000").replace(/\/$/, "");
const imgFor = (n) => "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/" + String(n || "").replace("npc_dota_hero_", "") + ".png";
const selectedAll = () => new Set([...state.picks.radiantPicks, ...state.picks.direPicks, ...state.picks.radiantBans, ...state.picks.direBans]);
const heroById = (id) => state.heroes.find(h => h.id === id);

async function api(path, opts) {
  let r;
  try { r = await fetch(backend() + path, opts); }
  catch (e) { throw new Error(`Нет связи с backend (${backend()}). Поднимите: docker compose up backend. Детали: ${e.message}`); }
  if (!r.ok) throw new Error(`API ${r.status}: ${(await r.text()).slice(0, 300)}`);
  return r.json();
}

// --- tabs ---
function initTabs() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll(".tab").forEach(b => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
      btn.classList.add("active"); btn.setAttribute("aria-selected", "true");
      document.querySelectorAll(".tabpanel").forEach(p => p.classList.add("hidden"));
      const panel = $("tab-" + btn.dataset.tab);
      panel.classList.remove("hidden");
      if (btn.dataset.tab === "top" && !state.topLoaded) loadTop();
      if (btn.dataset.tab === "news" && !state.newsLoaded) loadNews();
    };
  });
}

// --- draft (6.1–6.7, данные из DB через API) ---
async function loadHeroes() {
  $("status").textContent = "Загрузка героев из database…";
  $("retryBtn").classList.add("hidden");
  try {
    const data = await api("/heroes");
    state.heroes = data.heroes || [];
    $("dbMode").textContent = `БД: ${data.db_mode || "?"} · ${data.data_updated_at || "?"}`;
    $("dataUpdated").textContent = `data_updated_at: ${data.data_updated_at || "?"}`;
    const roles = new Set(); state.heroes.forEach(h => (h.roles || []).forEach(x => roles.add(x)));
    const cur = $("roleFilter").value;
    $("roleFilter").innerHTML = `<option value="">— любая —</option>` + [...roles].sort().map(x => `<option>${x}</option>`).join("");
    if ([...roles].includes(cur)) $("roleFilter").value = cur;
    renderAll();
    $("status").textContent = state.heroes.length
      ? `Героев из БД: ${state.heroes.length}. Вбей героя за каждую команду → «Рекомендовать пик».`
      : "Пусто: backend вернул 0 героев. Проверьте ETL (n8n / loader).";
  } catch (e) {
    state.lastError = e;
    $("status").textContent = `Ошибка загрузки: ${e.message}`;
    $("retryBtn").classList.remove("hidden");
  }
}

function avatar(h, big) {
  const w = document.createElement("span"); w.className = "avatar" + (big ? " big" : "");
  const img = document.createElement("img"); img.src = imgFor(h.name); img.alt = ""; img.loading = "lazy";
  img.onerror = () => img.remove();
  const fb = document.createElement("span"); fb.className = "fb";
  fb.textContent = h.localized_name.split(" ").map(s => s[0]).join("").slice(0, 2).toUpperCase();
  w.append(img, fb); return w;
}

function renderAll() { renderChips(); renderGrid(); }

function renderChips() {
  for (const key of Object.keys(state.picks)) {
    const el = $(key); el.innerHTML = "";
    state.picks[key].forEach(id => {
      const h = heroById(id);
      const d = document.createElement("span"); d.className = "chip";
      if (h) d.appendChild(avatar(h));
      const label = document.createElement("span"); label.textContent = h ? h.localized_name : `Hero ${id}`;
      const b = document.createElement("button"); b.type = "button"; b.textContent = "×";
      b.setAttribute("aria-label", `Убрать ${h ? h.localized_name : id}`);
      b.onclick = () => { state.picks[key] = state.picks[key].filter(x => x !== id); renderAll(); };
      d.append(label, b); el.appendChild(d);
    });
    if (!state.picks[key].length) el.innerHTML = `<span class="muted">— пусто —</span>`;
  }
  $("radiantCount").textContent = `${state.picks.radiantPicks.length}/${MAX_PICKS} пиков`;
  $("direCount").textContent = `${state.picks.direPicks.length}/${MAX_PICKS} пиков`;
}

function renderGrid() {
  const q = ($("search").value || "").toLowerCase(), role = $("roleFilter").value;
  const sel = selectedAll(), g = $("heroGrid"); g.innerHTML = "";
  const list = state.heroes.filter(h =>
    (!q || h.localized_name.toLowerCase().includes(q)) && (!role || (h.roles || []).includes(role)));
  $("heroCount").textContent = `· ${list.length}/${state.heroes.length}`;
  list.forEach(h => {
    const target = $("pickTarget").value;
    const full = target === "radiantPicks" ? state.picks.radiantPicks.length >= MAX_PICKS
      : target === "direPicks" ? state.picks.direPicks.length >= MAX_PICKS : false;
    const b = document.createElement("button");
    b.type = "button"; b.className = "hero-card" + ((sel.has(h.id) || full) ? " disabled" : "");
    b.setAttribute("role", "listitem"); b.disabled = sel.has(h.id) || full;
    b.appendChild(avatar(h, true));
    const tx = document.createElement("span"); tx.className = "tx";
    tx.innerHTML = `<b></b><span class="roles"></span>`;
    tx.querySelector("b").textContent = h.localized_name;
    tx.querySelector(".roles").textContent = (h.roles || []).join(", ") || "—";
    b.appendChild(tx);
    b.title = sel.has(h.id) ? "Уже в драфте" : full ? "Слоты команды заполнены (5/5)" : `В ${$("pickTarget").selectedOptions[0].text}`;
    b.setAttribute("aria-label", h.localized_name + (sel.has(h.id) ? " (в драфте)" : ""));
    b.onclick = () => {
      if (selectedAll().has(h.id)) return;
      const t = $("pickTarget").value;
      if ((t === "radiantPicks" || t === "direPicks") && state.picks[t].length >= MAX_PICKS) return;
      state.picks[t].push(h.id); renderAll();
    };
    g.appendChild(b);
  });
  if (!list.length) g.innerHTML = `<span class="muted">Ничего не найдено. Измените поиск или фильтр.</span>`;
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
  state.lastReq = req;
  $("loading").classList.remove("hidden"); $("recList").innerHTML = "";
  $("retryBtn").classList.add("hidden"); $("recommendBtn").disabled = true;
  $("status").textContent = "Считаем контрпики (SQL + scoring.py)…";
  try {
    const data = await api("/recommendations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(req) });
    state.lastRecs = data.recommendations || []; state.lastError = null;
    $("dataUpdated").textContent = `data_updated_at: ${data.data_updated_at}`;
    const stale = (data.data_updated_at || "").startsWith("2026-01-01");
    $("warnStale").classList.toggle("hidden", !stale);
    if (stale) $("warnStale").textContent = "⚠ Данные seed/demo без свежего sync. Прод-цифры — после n8n initial_load / loader.";
    const low = state.lastRecs.filter(r => r.confidence === "low").length;
    $("warnLow").classList.toggle("hidden", !(state.lastRecs.length && low === state.lastRecs.length));
    if (low === state.lastRecs.length && state.lastRecs.length) $("warnLow").textContent = "⚠ По всем кандидатам мало статистики — смотрите games перед пиком.";
    if (!state.lastRecs.length) { $("status").textContent = "Пусто: все герои в драфте. Освободите слот или сбросьте."; return; }
    const enemy = req.team_to_pick === "radiant" ? req.dire_picks : req.radiant_picks;
    const enames = enemy.map(id => (heroById(id) || {}).localized_name || ("#" + id)).join(", ");
    $("status").textContent = `Хорошо играют против (${enames || "—"}): топ-${state.lastRecs.length}. Низкая уверенность: ${low}.`;
    renderRecs(req);
  } catch (e) {
    state.lastError = e;
    $("status").textContent = `Ошибка API: ${e.message}`;
    $("retryBtn").classList.remove("hidden");
  } finally { $("loading").classList.add("hidden"); $("recommendBtn").disabled = false; }
}

function renderRecs(req) {
  const box = $("recList"); box.innerHTML = "";
  state.lastRecs.forEach((r, i) => {
    const h = heroById(r.hero_id) || { localized_name: "Hero " + r.hero_id, name: "" };
    const d = document.createElement("article"); d.className = "rec";
    const top = document.createElement("div"); top.className = "top";
    const left = document.createElement("span"); left.className = "rec-name";
    left.appendChild(avatar(h));
    const title = document.createElement("b"); title.textContent = `#${i + 1} ${h.localized_name}`;
    left.appendChild(title);
    const sc = document.createElement("span");
    sc.innerHTML = `score <b></b> <span class="conf ${r.confidence}"></span>`;
    sc.querySelector("b").textContent = Number(r.score).toFixed(2);
    sc.querySelector(".conf").textContent = r.confidence;
    top.append(left, sc); d.appendChild(top);
    const bar = document.createElement("div"); bar.className = "scorebar";
    const fill = document.createElement("div"); fill.style.width = `${Math.round(Number(r.score) * 100)}%`;
    bar.appendChild(fill); d.appendChild(bar);
    const rs = document.createElement("div"); rs.className = "reasons";
    rs.innerHTML = (r.reasons || []).map(x => {
      const opp = x.against_hero_id ? ` (vs #${x.against_hero_id}${(heroById(x.against_hero_id) || {}).localized_name ? " " + heroById(x.against_hero_id).localized_name : ""})` : "";
      return `• [${x.type}] ${x.summary}${opp} — ${x.games_played} игр`;
    }).join("<br>") || "—";
    d.appendChild(rs);
    (r.caveats || []).forEach(c => { const cv = document.createElement("div"); cv.className = "caveat"; cv.textContent = `⚠ ${c}`; d.appendChild(cv); });
    const acts = document.createElement("div"); acts.className = "rec-actions";
    const pick = document.createElement("button"); pick.type = "button"; pick.textContent = `Взять в ${req.team_to_pick}`;
    pick.onclick = () => {
      const slot = req.team_to_pick === "radiant" ? "radiantPicks" : "direPicks";
      if (selectedAll().has(r.hero_id) || state.picks[slot].length >= MAX_PICKS) return;
      state.picks[slot].push(r.hero_id); renderAll();
    };
    const expl = document.createElement("button"); expl.type = "button"; expl.textContent = "Объяснить";
    const out = document.createElement("div"); out.className = "expl hidden"; out.setAttribute("aria-live", "polite");
    expl.onclick = async () => {
      expl.disabled = true; out.classList.remove("hidden"); out.textContent = "Факты из scoring, без выдуманных цифр…";
      try {
        const ex = await api("/explain", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...req, hero_id: r.hero_id }) });
        out.textContent = ex.explanation + (ex.llm_generated ? " [LLM]" : " [template: цифры из scoring]");
      } catch (e) { out.textContent = "Ошибка объяснения: " + e.message; }
      expl.disabled = false;
    };
    acts.append(pick, expl); d.append(acts, out); box.appendChild(d);
  });
}

// --- top (БД, не хардкод) ---
async function loadTop() {
  $("topStatus").textContent = "Загружаем топ из database…";
  try {
    const d = await api("/meta/top?limit=10");
    state.topLoaded = true;
    $("topUpdated").textContent = `updated: ${d.data_updated_at} · ${d.db_mode}`;
    const box = $("topList"); box.innerHTML = "";
    (d.top || []).forEach((t, i) => {
      const row = document.createElement("div"); row.className = "top-row";
      const medals = ["🥇", "🥈", "🥉"];
      const m = document.createElement("span"); m.className = "medal"; m.textContent = medals[i] || `#${i + 1}`;
      const av = avatar({ localized_name: t.localized_name, name: (heroById(t.hero_id) || {}).name });
      const nm = document.createElement("span"); nm.className = "top-name"; nm.textContent = t.localized_name;
      const wr = document.createElement("b"); wr.textContent = `${(t.win_rate * 100).toFixed(1)}%`;
      const bar = document.createElement("div"); bar.className = "scorebar";
      const f = document.createElement("div"); f.style.width = `${Math.round(t.win_rate * 100)}%`;
      bar.appendChild(f);
      row.append(m, av, nm, wr); box.append(row, bar);
    });
    $("topStatus").textContent = "";
  } catch (e) { $("topStatus").textContent = "Ошибка: " + e.message; }
}

// --- news ---
async function loadNews() {
  $("newsStatus").textContent = "Загружаем новости…";
  try {
    const d = await api("/news?limit=10");
    state.newsLoaded = true;
    const box = $("newsList"); box.innerHTML = "";
    (d.news || []).forEach(n => {
      const a = document.createElement("a"); a.className = "news-card"; a.href = n.url; a.target = "_blank"; a.rel = "noopener";
      a.innerHTML = `<b></b><p></p><span class="muted"></span>`;
      a.querySelector("b").textContent = n.title;
      a.querySelector("p").textContent = n.summary;
      a.querySelector(".muted").textContent = `${n.source} · ${n.published_at}`;
      box.appendChild(a);
    });
    $("newsStatus").textContent = d.source_note || "";
  } catch (e) { $("newsStatus").textContent = "Ошибка: " + e.message; }
}

// --- settings ---
function initSettings() {
  $("backendUrl").value = store.backend;
  $("defLimit").value = store.limit;
  $("limit").value = store.limit;
  const op = localStorage.getItem("drafter.overlayOpacity") || "92";
  $("overlayOpacity").value = op; $("opVal").textContent = op + "%";
  $("overlayOpacity").oninput = (e) => { $("opVal").textContent = e.target.value + "%"; };
  $("saveSettings").onclick = () => {
    store.backend = $("backendUrl").value.trim() || "http://localhost:8000";
    store.limit = $("defLimit").value; $("limit").value = store.limit;
    localStorage.setItem("drafter.overlayOpacity", $("overlayOpacity").value);
    $("setStatus").textContent = "Сохранено. Перезагружаем героев с нового backend…";
    loadHeroes();
  };
}

$("recommendBtn").onclick = recommend;
$("retryBtn").onclick = () => { if (state.lastReq && state.lastError) recommend(); else loadHeroes(); };
$("clearBtn").onclick = () => { state.picks = { radiantPicks: [], direPicks: [], radiantBans: [], direBans: [] }; state.lastRecs = []; $("recList").innerHTML = ""; $("warnLow").classList.add("hidden"); renderAll(); };
$("refreshHeroes") && ($("refreshHeroes").onclick = loadHeroes);
$("reloadTop").onclick = () => { state.topLoaded = false; loadTop(); };
$("reloadNews").onclick = () => { state.newsLoaded = false; loadNews(); };
$("search").oninput = renderGrid; $("roleFilter").onchange = renderGrid; $("pickTarget").onchange = renderGrid;
window.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(location.search);
  if (params.get("backend")) store.backend = params.get("backend");
  initTabs(); initSettings(); loadHeroes();
});
