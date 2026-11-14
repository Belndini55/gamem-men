/* ===== GameMen frontend ===== */
"use strict";

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const state = {
  games: [],
  mode: "live",
  filter: "all",        // all | favorites | platform:<id>
  search: "",
  sort: "name",
  view: "grid",
  current: null,        // game opened in modal
};

const PLATFORM_ORDER = ["steam", "epic", "gog", "xbox", "battlenet", "ea", "ubisoft", "riot", "minecraft", "other"];

/* ================= API ================= */

async function api(path, body) {
  const opts = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const res = await fetch(path, opts);
  return res.json();
}

async function loadGames(showOverlay) {
  if (showOverlay) $("#scan-overlay").hidden = false;
  try {
    const data = await api("/api/games");
    state.games = data.games || [];
    state.mode = data.mode || "live";
    renderAll();
  } catch (e) {
    toast("Nie udało się połączyć z serwerem GameMen.", "err");
  } finally {
    $("#scan-overlay").hidden = true;
  }
}

async function rescan() {
  const btn = $("#btn-scan");
  btn.classList.add("busy");
  btn.disabled = true;
  $("#scan-overlay").hidden = false;
  try {
    const data = await api("/api/scan", {});
    state.games = data.games || [];
    state.mode = data.mode || "live";
    renderAll();
    toast(`Przeskanowano bibliotekę — ${state.games.length} gier.`, "ok");
  } catch (e) {
    toast("Skanowanie nie powiodło się.", "err");
  } finally {
    btn.classList.remove("busy");
    btn.disabled = false;
    $("#scan-overlay").hidden = true;
  }
}

/* ================= Rendering ================= */

function fmtSize(bytes) {
  if (!bytes || bytes <= 0) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0, v = bytes;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v >= 100 || i < 2 ? 0 : 1)} ${units[i]}`;
}

function fmtDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("pl-PL", { year: "numeric", month: "short", day: "numeric" });
  } catch (e) { return iso; }
}

function placeholderHTML(game) {
  const [c1, c2] = (game.color_hint || "hsl(250,45%,32%)|hsl(290,55%,55%)").split("|");
  return `<div class="cover-placeholder" style="background:linear-gradient(150deg, ${c1}, ${c2})">${game.monogram || "?"}</div>`;
}

function coverHTML(game, lazy) {
  if (game.cover) {
    return `<img src="${game.cover}" alt="${escapeHtml(game.name)}" ${lazy ? 'loading="lazy"' : ""} onerror="this.outerHTML=window.__ph(this.closest('[data-game]')?.dataset.game || '')">`;
  }
  return placeholderHTML(game);
}

// fallback used from inline onerror: look the game up by element id
window.__ph = (gameId) => {
  const g = state.games.find((x) => x.id === gameId) || { monogram: "?", color_hint: "hsl(250,45%,32%)|hsl(290,55%,55%)" };
  return placeholderHTML(g);
};

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function visibleGames() {
  let list = state.games.slice();
  if (state.filter === "favorites") list = list.filter((g) => g.favorite);
  else if (state.filter.startsWith("platform:")) {
    const p = state.filter.split(":")[1];
    list = list.filter((g) => g.platform === p);
  }
  const q = state.search.trim().toLowerCase();
  if (q) list = list.filter((g) => g.name.toLowerCase().includes(q));

  const by = {
    name: (a, b) => a.name.localeCompare(b.name, "pl"),
    "name-desc": (a, b) => b.name.localeCompare(a.name, "pl"),
    size: (a, b) => (b.size_bytes || 0) - (a.size_bytes || 0),
    date: (a, b) => (b.install_date || "").localeCompare(a.install_date || ""),
    platform: (a, b) => a.platform_name.localeCompare(b.platform_name, "pl") || a.name.localeCompare(b.name, "pl"),
  };
  list.sort(by[state.sort] || by.name);
  return list;
}

function renderAll() {
  renderSidebar();
  renderStats();
  renderGrid();
  renderMode();
}

function renderMode() {
  const badge = $("#mode-badge");
  const banner = $("#demo-banner");
  if (state.mode === "demo") {
    badge.textContent = "tryb demo";
    badge.className = "mode-badge demo";
    banner.hidden = false;
  } else {
    badge.textContent = "skaner aktywny";
    badge.className = "mode-badge live";
    banner.hidden = true;
  }
}

function renderSidebar() {
  const counts = {};
  for (const g of state.games) counts[g.platform] = (counts[g.platform] || 0) + 1;
  $("#count-all").textContent = state.games.length;
  $("#count-fav").textContent = state.games.filter((g) => g.favorite).length;

  const nav = $("#platform-nav");
  const present = PLATFORM_ORDER.filter((p) => counts[p]);
  nav.innerHTML = present.map((p) => {
    const sample = state.games.find((g) => g.platform === p);
    const name = sample ? sample.platform_name : p;
    const color = sample ? sample.platform_color : "#9aa4b2";
    const active = state.filter === `platform:${p}` ? " active" : "";
    return `
      <button class="nav-item${active}" data-filter="platform:${p}">
        <span class="nav-dot" style="background:${color}"></span>
        <span>${escapeHtml(name)}</span>
        <span class="nav-count">${counts[p]}</span>
      </button>`;
  }).join("");

  $$(".nav-item").forEach((el) => {
    el.addEventListener("click", () => {
      state.filter = el.dataset.filter;
      $$(".nav-item").forEach((n) => n.classList.remove("active"));
      el.classList.add("active");
      renderGrid();
    });
  });
}

function renderStats() {
  const games = state.games;
  const totalSize = games.reduce((s, g) => s + (g.size_bytes || 0), 0);
  const platforms = new Set(games.map((g) => g.platform)).size;
  const biggest = games.reduce((best, g) => ((g.size_bytes || 0) > (best?.size_bytes || 0) ? g : best), null);
  $("#stat-games").textContent = games.length;
  $("#stat-size").textContent = fmtSize(totalSize);
  $("#stat-platforms").textContent = platforms;
  $("#stat-biggest").textContent = biggest ? biggest.name : "—";
  $("#stat-biggest").style.fontSize = "15px";
}

function renderGrid() {
  const list = visibleGames();
  const grid = $("#grid");
  const titles = { all: "Wszystkie gry", favorites: "Ulubione" };
  let title = titles[state.filter];
  if (!title && state.filter.startsWith("platform:")) {
    const p = state.filter.split(":")[1];
    const sample = state.games.find((g) => g.platform === p);
    title = sample ? sample.platform_name : p;
  }
  $("#section-title").textContent = title || "Gry";
  $("#content-meta").textContent = `${list.length} ${list.length === 1 ? "gra" : list.length < 5 ? "gry" : "gier"}`;

  grid.className = "grid" + (state.view === "list" ? " list-view" : "");
  grid.innerHTML = list.map((g, i) => `
    <div class="card" data-game="${g.id}" style="animation-delay:${Math.min(i * 28, 400)}ms">
      <div class="card-cover" data-game="${g.id}">
        ${coverHTML(g, true)}
        <div class="card-badge" style="box-shadow:inset 0 -2px 0 ${g.platform_color}">${escapeHtml(g.platform_name.split(" ")[0])}</div>
        ${g.favorite ? '<div class="card-fav on">★</div>' : '<div class="card-fav">★</div>'}
        <div class="card-play" data-play="${g.id}">▶ GRAJ</div>
      </div>
      <div class="card-info">
        <div class="card-name">${escapeHtml(g.name)}</div>
        <div class="card-sub">${fmtSize(g.size_bytes)} · ${fmtDate(g.install_date)}</div>
      </div>
    </div>`).join("");

  $("#empty").hidden = list.length > 0;

  $$(".card").forEach((el) => {
    el.addEventListener("click", (e) => {
      const playId = e.target.closest("[data-play]")?.dataset.play;
      if (playId) {
        e.stopPropagation();
        playGame(playId);
        return;
      }
      openModal(el.dataset.game);
    });
  });
}

/* ================= Modal ================= */

function openModal(gameId) {
  const g = state.games.find((x) => x.id === gameId);
  if (!g) return;
  state.current = g;

  $("#modal-cover").innerHTML = coverHTML(g, false);
  $("#modal-platform").innerHTML = `<span class="nav-dot" style="background:${g.platform_color}"></span>${escapeHtml(g.platform_name)}`;
  $("#modal-title").textContent = g.name;
  $("#modal-meta").innerHTML = `
    <div>Rozmiar: <b>${fmtSize(g.size_bytes)}</b></div>
    <div>Zainstalowano: <b>${fmtDate(g.install_date)}</b></div>`;
  $("#modal-path").textContent = g.install_path || "Nieznana ścieżka instalacji";
  $("#modal-fav").classList.toggle("on", !!g.favorite);
  $("#modal-fav").textContent = g.favorite ? "★" : "☆";
  $("#modal").hidden = false;
}

function closeModal() {
  $("#modal").hidden = true;
  state.current = null;
}

/* ================= Actions ================= */

async function playGame(id) {
  const g = state.games.find((x) => x.id === id);
  if (state.mode === "demo") {
    toast(`Tryb demo — „${g ? g.name : ""}” zostanie uruchomione po zainstalowaniu GameMen na Windows.`, "warn");
    return;
  }
  const res = await api("/api/launch", { id });
  toast(res.message || (res.ok ? "Uruchamianie…" : "Nie udało się."), res.ok ? "ok" : "err");
}

async function openFolder() {
  if (!state.current) return;
  if (state.mode === "demo") { toast("Tryb demo — brak prawdziwych folderów.", "warn"); return; }
  const res = await api("/api/folder", { id: state.current.id });
  toast(res.message || "…", res.ok ? "ok" : "err");
}

async function toggleFav() {
  const g = state.current;
  if (!g) return;
  const res = await api("/api/favorite", { id: g.id });
  if (res.ok) {
    g.favorite = res.favorite;
    $("#modal-fav").classList.toggle("on", res.favorite);
    $("#modal-fav").textContent = res.favorite ? "★" : "☆";
    renderSidebar();
    renderGrid();
  }
}

async function uninstallGame() {
  const g = state.current;
  if (!g) return;
  if (state.mode === "demo") { toast("Tryb demo — nic nie zostanie odinstalowane.", "warn"); return; }
  if (!confirm(`Na pewno odinstalować „${g.name}”?`)) return;
  const res = await api("/api/uninstall", { id: g.id });
  toast(res.message || "…", res.ok ? "ok" : "err");
}

/* ================= Toasts ================= */

function toast(message, kind = "") {
  const wrap = $("#toasts");
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = message;
  wrap.appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .4s"; }, 3600);
  setTimeout(() => el.remove(), 4100);
}

/* ================= Events ================= */

function bind() {
  $("#search").addEventListener("input", (e) => {
    state.search = e.target.value;
    renderGrid();
  });

  $("#sort").addEventListener("change", (e) => {
    state.sort = e.target.value;
    renderGrid();
  });

  $$(".view-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.view = btn.dataset.view;
      $$(".view-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      renderGrid();
    });
  });

  $("#btn-scan").addEventListener("click", rescan);

  $("#modal-close").addEventListener("click", closeModal);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });
  $("#modal-play").addEventListener("click", () => state.current && playGame(state.current.id));
  $("#modal-folder").addEventListener("click", openFolder);
  $("#modal-fav").addEventListener("click", toggleFav);
  $("#modal-uninstall").addEventListener("click", uninstallGame);

  $("#btn-settings").addEventListener("click", async () => {
    const cfg = await api("/api/config");
    $("#settings-folders").value = (cfg.extra_folders || []).join("\n");
    $("#settings-modal").hidden = false;
  });
  $("#settings-close").addEventListener("click", () => ($("#settings-modal").hidden = true));
  $("#settings-modal").addEventListener("click", (e) => {
    if (e.target.id === "settings-modal") $("#settings-modal").hidden = true;
  });
  $("#settings-save").addEventListener("click", async () => {
    const folders = $("#settings-folders").value.split("\n").map((s) => s.trim()).filter(Boolean);
    await api("/api/settings", { extra_folders: folders });
    $("#settings-modal").hidden = true;
    toast("Zapisano ustawienia skanowania.", "ok");
    rescan();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeModal();
      $("#settings-modal").hidden = true;
    }
    if (e.key === "/" && document.activeElement !== $("#search")) {
      e.preventDefault();
      $("#search").focus();
    }
  });
}

/* ================= Init ================= */

bind();
loadGames(false);
