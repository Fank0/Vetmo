/* Overlay: боковые меню + контрпики против введённых героев. Только backend-цифры. */
const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const BACKEND = (params.get("backend") || localStorage.getItem("drafter.backend") || "http://localhost:8000").replace(/\/$/, "");
const state = { heroes: [], radiant: [], dire: [], team: "radiant", timer: null };

const imgFor = (npcName) => "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/" + String(npcName || "").replace("npc_dota_hero_", "") + ".png";
const heroById = (id) => state.heroes.find(h => h.id === id);
const taken = () => new Set([...state.radiant, ...state.dire]);

async function api(path, opts) {
  const r = await fetch(BACKEND + path, opts);
  if (!r.ok) throw new Error("API " + r.status);
  return r.json();
}

function applyOpacity() {
  const op = parseInt(localStorage.getItem("drafter.overlayOpacity") || "92", 10);
  document.querySelector(".ov-shell").style.background = `rgba(10,14,22,${op / 100})`;
}

async function init() {
  applyOpacity();
  try {
    const d = await api("/heroes");
    state.heroes = d.heroes || [];
    $("ovDot").classList.add("ok");
    $("ovStatus").textContent = `${state.heroes.length} героев · ${d.db_mode || ""}`;
  } catch (e) { $("ovStatus").textContent = "Нет связи с backend"; $("ovDot").classList.add("bad"); return; }
  bindSide("R", "radiant"); bindSide("D", "dire");
  $("ovRadiant").onclick = () => setTeam("radiant");
  $("ovDire").onclick = () => setTeam("dire");
  renderSides(); schedule();
}

function setTeam(t) {
  state.team = t;
  $("ovRadiant").classList.toggle("on", t === "radiant");
  $("ovDire").classList.toggle("on", t === "dire");
  schedule();
}

function bindSide(suffix, key) {
  $("ovSearch" + suffix).oninput = (e) => renderGrid(suffix, e.target.value);
  renderGrid(suffix, "");
}

function avatar(h, cls) {
  const wrap = document.createElement("span");
  wrap.className = "avatar " + (cls || "");
  const img = document.createElement("img");
  img.src = imgFor(h.name); img.alt = ""; img.loading = "lazy";
  img.onerror = () => img.remove();
  const fb = document.createElement("span");
  fb.className = "fb"; fb.textContent = h.localized_name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
  const nm = document.createElement("span"); nm.className = "nm"; nm.textContent = h.localized_name;
  wrap.append(img, fb, nm);
  return wrap;
}

function renderSides() {
  for (const [suffix, key] of [["R", "radiant"], ["D", "dire"]]) {
    const box = $("ovList" + suffix); box.innerHTML = "";
    state[key].forEach(id => {
      const h = heroById(id); if (!h) return;
      const chip = document.createElement("span"); chip.className = "chip";
      chip.appendChild(avatar(h));
      const x = document.createElement("button"); x.type = "button"; x.textContent = "×";
      x.setAttribute("aria-label", "Убрать " + h.localized_name);
      x.onclick = () => { state[key] = state[key].filter(v => v !== id); renderSides(); schedule(); };
      chip.appendChild(x); box.appendChild(chip);
    });
    if (!state[key].length) box.innerHTML = '<span class="muted">— вбей героя ниже —</span>';
  }
}

function renderGrid(suffix, q) {
  const key = suffix === "R" ? "radiant" : "dire";
  const g = $("ovGrid" + suffix); g.innerHTML = "";
  const query = (q || "").toLowerCase(), tk = taken();
  state.heroes
    .filter(h => !query || h.localized_name.toLowerCase().includes(query))
    .slice(0, 8)
    .forEach(h => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "ov-hero" + (tk.has(h.id) ? " disabled" : "");
      b.disabled = tk.has(h.id);
      b.appendChild(avatar(h));
      b.title = tk.has(h.id) ? "Уже в драфте" : "В " + (suffix === "R" ? "Radiant" : "Dire");
      b.onclick = () => { if (taken().has(h.id)) return; state[key].push(h.id); $("ovSearch" + suffix).value = ""; renderSides(); renderGrid(suffix, ""); schedule(); };
      g.appendChild(b);
    });
}

function schedule() {
  clearTimeout(state.timer);
  state.timer = setTimeout(refresh, 350);
}

async function refresh() {
  const enemy = state.team === "radiant" ? state.dire : state.radiant;
  const box = $("ovRecs"); box.innerHTML = "";
  if (!enemy.length) {
    $("ovTitle").textContent = "Вбей героя соперника сбоку →";
    return;
  }
  const names = enemy.map(id => (heroById(id) || {}).localized_name || ("#" + id)).join(", ");
  $("ovTitle").textContent = `Против: ${names}`;
  $("ovLoading").classList.remove("hidden");
  try {
    const req = state.team === "radiant"
      ? { radiant_picks: state.radiant, dire_picks: state.dire, radiant_bans: [], dire_bans: [], team_to_pick: "radiant", requested_roles: [], limit: 6 }
      : { radiant_picks: state.radiant, dire_picks: state.dire, radiant_bans: [], dire_bans: [], team_to_pick: "dire", requested_roles: [], limit: 6 };
    const d = await api("/recommendations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(req) });
    (d.recommendations || []).forEach((r, i) => {
      const h = heroById(r.hero_id) || { localized_name: "Hero " + r.hero_id, name: "" };
      const row = document.createElement("div"); row.className = "ov-row";
      const pos = document.createElement("b"); pos.textContent = `#${i + 1}`;
      row.appendChild(pos); row.appendChild(avatar(h));
      const sc = document.createElement("span"); sc.className = "ov-score";
      sc.textContent = `${Number(r.score).toFixed(2)} · ${r.confidence}`;
      const g = (r.reasons || []).reduce((a, x) => a + (x.games_played || 0), 0);
      const n = document.createElement("span"); n.className = "muted"; n.textContent = `${g} игр`;
      row.append(sc, n); box.appendChild(row);
    });
    if (!(d.recommendations || []).length) box.innerHTML = '<span class="muted">Все герои уже в драфте</span>';
  } catch (e) { box.innerHTML = '<span class="muted">Ошибка API — проверь backend</span>'; }
  finally { $("ovLoading").classList.add("hidden"); }
}

window.addEventListener("DOMContentLoaded", init);
