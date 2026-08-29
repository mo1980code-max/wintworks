
/* ============================================================
   Scroll restoration — keep your place across a reload.
   The old code force-scrolled to the top on every load (twice),
   which — combined with the page's `scroll-behavior: smooth` —
   made refreshing mid-page visibly jump to the top. Instead we
   save the offset when the page is hidden and restore it
   instantly, after the scholarship list has rendered.
   ============================================================ */
if ('scrollRestoration' in history) {
  history.scrollRestoration = 'manual'; // we handle restoration ourselves
}

const WW_SCROLL_KEY = "ww:scroll:" + location.pathname + location.search;

function wwSaveScroll() {
  try {
    sessionStorage.setItem(WW_SCROLL_KEY, String(Math.round(window.scrollY)));
  } catch (e) { /* private mode etc. — ignore */ }
}

function wwScrollInstant(y) {
  const de = document.documentElement;
  const prev = de.style.scrollBehavior;
  de.style.scrollBehavior = "auto"; // bypass CSS `scroll-behavior: smooth`
  window.scrollTo(0, y);
  de.style.scrollBehavior = prev;
}

function wwRestoreScroll() {
  if (wwRestoreScroll.done) return;
  if (location.hash) return;        // hash routes (#/scholarship/…) manage their own scroll
  let y = 0;
  try { y = parseInt(sessionStorage.getItem(WW_SCROLL_KEY) || "0", 10) || 0; } catch (e) {}
  if (y > 0) {
    wwScrollInstant(y);
    wwRestoreScroll.done = true;
    try { sessionStorage.removeItem(WW_SCROLL_KEY); } catch (e) {}
  }
}

window.addEventListener("pagehide", wwSaveScroll);
window.addEventListener("beforeunload", wwSaveScroll);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") wwSaveScroll();
});

/* ============================================================
   WintWorks — dedicated scholarships page engine
   ============================================================ */
"use strict";

const CONFIG = {
  siteName: "WintWorks",
  siteUrl: "https://wintworks.com",
  adsenseClient: "ca-pub-7088247829787060",
  adSlots: { top: "", feed: "", detail: "" },
};

/* ============================ UTILS ============================ */
const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => String(s ?? "").replace(/[&<>\"']/g, (c) =>
  ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));


function isExpired(dateStr) {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  if (isNaN(d)) return false;
  return d.getTime() < Date.now();
}
function formatDeadline(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d)) return "";
  return "Deadline: " + d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function timeAgo(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const s = Math.max(1, Math.floor((Date.now() - d.getTime()) / 1000));
  if (s < 3600)  return `${Math.max(1, Math.floor(s / 60))}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  if (s < 86400 * 7) return `${Math.floor(s / 86400)}d ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function sanitizeHtml(html) {
  if (!html) return "";
  const div = document.createElement("div");
  div.innerHTML = String(html);
  div.querySelectorAll("script,style,iframe,object,embed,form,input,button,link,meta,img,svg,canvas,video,audio").forEach(n => n.remove());
  div.querySelectorAll("*").forEach(el => {
    [...el.attributes].forEach(a => {
      const name = a.name.toLowerCase();
      if (name.startsWith("on") || name === "style" || name === "id" || name === "class")
        el.removeAttribute(a.name);
      if (a.name === "href" && /^\s*javascript:/i.test(a.value))
        el.removeAttribute("href");
    });
  });
  return div.innerHTML;
}

function toast(msg, actionLabel, actionFn) {
  const t = $("#toast");
  if (!t) return;
  t.innerHTML = `<span>${esc(msg)}</span>`;
  if (actionLabel && actionFn) {
    const b = document.createElement("button");
    b.textContent = actionLabel;
    b.onclick = () => { actionFn(); hide(); };
    t.appendChild(b);
  }
  t.classList.add("show");
  let hide = () => t.classList.remove("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(hide, actionFn ? 9000 : 4000);
}

const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; }
    catch { return fallback; }
  },
  set(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch {}
  },
};

/* ============================ DATA STATE ============================ */
const state = {
  scholarships: [],
  filters: {
    q: "", funding: "All", level: "All", region: "All",
    country: "All", sort: "deadline",
  },
  visible: 24,
  bookmarks: new Set(store.get("ww:schBookmarks-page", [])),
};

const ARAB_COUNTRIES = [
  "Egypt","Morocco","Tunisia","Algeria","Jordan","Lebanon",
  "United Arab Emirates","Saudi Arabia","Oman","Bahrain","Qatar",
  "Palestine","Syria","Iraq","Sudan","Libya","Mauritania",
  "Djibouti","Yemen","Somalia","Comoros","Somaliland",
];
const ARAB_KEYS = ARAB_COUNTRIES.map(c => c.toLowerCase());

function isArabCountry(country) {
  return ARAB_KEYS.some(c => (country || "").toLowerCase().includes(c));
}
function isArabRegion(region, country) {
  return region === "AR" || isArabCountry(country);
}
function isWomenTag(scholarship) {
  return (scholarship.tags || []).some(t =>
    ["women","woman","female","girls","gender"].includes(t.toLowerCase()));
}
function isTechTag(scholarship) {
  return (scholarship.tags || []).some(t =>
    ["engineering","technology","computer science","data","ai","software",
      "tech","it"," Developer","programming","cyber","cloud","iot",
      "machine learning","artificial intelligence","web","frontend",
      "backend","full stack","developer","development","devops",
      "infrastructure","security","sysadmin","python","java","javascript",
      "react","node","golang","ruby","php","blockchain","game",
      "embedded","hardware","architect","electrical"," electronics",
      "mechanical","civil","chemical","industrial","biomedical",
      "nuclear","aerospace"," robotics","telecom","network",
      "data science","data analytics","big data","business intelligence",
      "deep learning"," nlp "," computer vision"].some(k =>
      t.toLowerCase().includes(k.toLowerCase())));
}

/* ============================ NORMALIZATION ============================ */
function normalize(s) {
  s.amountNum  = s.amount ? Number(s.amount) : 0;
  s.isSaved    = state.bookmarks.has(s.id);
  s.isArab     = isArabRegion(s.region, s.country);
  s.isWomen    = isWomenTag(s);
  s.isTech     = isTechTag(s);
  s.deadlineRemains = s.deadline ? formatDeadline(s.deadline) : "";
  return s;
}

function matches(s, f) {
  if (f.funding !== "All" && s.funding !== f.funding) return false;
  if (f.level   !== "All" && s.level   !== f.level)   return false;
  if (f.region  !== "All") {
    if (f.region === "AR") {
      if (!isArabRegion(s.region, s.country)) return false;
    } else if (s.region !== f.region) return false;
  }
  if (f.country !== "All") {
    if (f.country === "WW") { if (s.country) return false; }
    else if (f.country === "AR") {
      if (!isArabCountry(s.country)) return false;
    }
    else if (s.country !== f.country) return false;
  }
  if (f.q) {
    const hay = `${s.title} ${s.provider} ${s.location} ${s.country} ${
      s.funding} ${s.level} ${(s.tags||[]).join(" ")}`.toLowerCase();
    if (!hay.includes(f.q.toLowerCase())) return false;
  }
  return true;
}

function visibleScholarships() {
  const f = state.filters;
  let arr = state.scholarships.filter(s => matches(s, f));
  if (f.sort === "amount") {
    arr = [...arr].sort((a,b) => b.amountNum - a.amountNum);
  } else {
    arr = [...arr].sort((a,b) => {
      const da = a.deadline ? new Date(a.deadline).getTime() : Infinity;
      const db = b.deadline ? new Date(b.deadline).getTime() : Infinity;
      return da - db;
    });
  }
  return arr;
}

/* ============================ FUNDING COLORS ============================ */
const FUNDING_COLORS = {
  "Fully Funded":     { bg: "var(--green-bg)",  cls: "funding-fully"  },
  "Partially Funded": { bg: "var(--amber-bg)",  cls: "funding-partial" },
  "Government":       { bg: "#dbeafe",          cls: "funding-gov"     },
  "Fellowship":       { bg: "#ede9fe",          cls: "funding-fellow"  },
  "Annual":           { bg: "#d1fae5",          cls: "funding-annual"  },
  "Self Funded":      { bg: "#f3f4f6",          cls: "funding-self"    },
};
function fundingStyle(s) {
  return FUNDING_COLORS[s.funding] || FUNDING_COLORS["Annual"];
}

/* ============================ CARD HTML ============================ */
function scholarshipCardHtml(s) {
  const saved = state.bookmarks.has(s.id);
  const fc    = fundingStyle(s);

  return `
<article class="scholarship-card" data-id="${esc(s.id)}">
  <div class="scholarship-card-top">
    <span class="funding-badge ${fc.cls}" style="background:${fc.bg}">
      ${esc(s.funding)}
    </span>
    <div style="min-width:0;flex:1">
      <h3 class="scholarship-title">
        <a href="#/scholarship/${encodeURIComponent(s.id)}">${esc(s.title)}</a>
      </h3>
      <div class="scholarship-provider">${esc(s.provider || "")}</div>
    </div>
    <button class="bookmark-btn ${saved ? "saved" : ""}" data-sch-bookmark="${esc(s.id)}"
      aria-label="Save scholarship" title="Save scholarship">
      ${saved ? "★" : "☆"}</button>
  </div>
  <div class="scholarship-meta">
    <span class="badge">📍 ${esc(s.location || s.country || "—")}</span>
    ${s.remote ? '<span class="badge remote">🌐 Remote / Worldwide</span>' : ""}
    ${s.level ? `<span class="badge">${esc(s.level)}</span>` : ""}
    ${s.isArab ? '<span class="badge" style="background:#fef3c7;color:#92400e;border-color:#fde68a">🌙 Arab world</span>' : ""}
    ${s.isWomen ? '<span class="badge" style="background:#fce7f3;color:#9d174d;border-color:#fbcfe8">👩 Women</span>' : ""}
    ${s.isTech ? '<span class="badge" style="background:#dbeafe;color:#1e40af;border-color:#bfdbfe">💻 Tech / STEM</span>' : ""}
  </div>
  ${s.amount_str ? `<div class="scholarship-meta">
    <span class="badge salary">💰 ${esc(s.amount_str)}</span></div>` : ""}
  ${s.deadlineRemains ? `<div class="scholarship-meta">
    <span class="badge deadline">⏰ ${esc(s.deadlineRemains)}</span></div>` : ""}
  ${s.tags && s.tags.length ? `<div class="job-tags">${
    s.tags.slice(0,4).map(t => `<span class="job-tag">${esc(t)}</span>`).join("")}</div>` : ""}
  <div class="scholarship-foot">
    <span class="scholarship-source-line">
      <span class="posted-age">${timeAgo(s.deadline || s.date)}</span>
      <a class="source-credit" href="${esc(s.url || "#")}" target="_blank"
        rel="noopener noreferrer">Source: ${esc(s.source || "")}</a>
    </span>
    <a class="apply" href="${esc(s.url || "#")}" target="_blank" rel="noopener noreferrer">
      Details <span>→</span></a>
  </div>
</article>`;
}

/* ============================ RENDERING ============================ */
function renderScholarships() {
  const f    = state.filters;
  const list = visibleScholarships();
  const shown = list.slice(0, state.visible);

  $("#scholarshipResultCount").textContent =
    `${list.length} scholarship${list.length === 1 ? "" : "s"}${
      f.q || f.funding !== "All" || f.level !== "All" || f.region !== "All" ? " found" : " available"}`;
  $("#scholarshipGrid").innerHTML = shown.length
    ? shown.map(scholarshipCardHtml).join("")
    : `<div class="empty"><h3>No scholarships match your filters</h3>
      <p>Try clearing the search or filters.</p>
      <button class="btn ghost" id="scholarshipResetBtn">Reset filters</button></div>`;
  const lb = $("#scholarshipLoadMoreWrap");
  lb.classList.toggle("hidden", list.length <= shown.length);
  $("#scholarshipLoadMoreBtn").textContent =
    `Show more (${list.length - shown.length} left)`;

  // Funding chips
  const fcounts = {};
  state.scholarships.forEach(s => {
    fcounts[s.funding] = (fcounts[s.funding]||0) + 1;
  });
  $("#scholarshipCatChips").innerHTML =
    `<button class="cat-chip ${f.funding === "All" ? "active" : ""}" data-sch-funding="All">
      All (${state.scholarships.length})</button>` +
    Object.entries(fcounts).sort((a,b) => b[1]-a[1]).map(([ft,n]) =>
      `<button class="cat-chip ${f.funding === ft ? "active" : ""}"
        data-sch-funding="${esc(ft)}">${esc(ft)} (${n})</button>`).join("");

  // Stats
  $("#statTotal").textContent    = state.scholarships.length;
  $("#statFullyFunded").textContent = state.scholarships.filter(s => s.funding === "Fully Funded").length;
  $("#statArab").textContent     = state.scholarships.filter(s => s.isArab).length;
  $("#statWomen").textContent    = state.scholarships.filter(s => s.isWomen).length;
  $("#statTech").textContent     = state.scholarships.filter(s => s.isTech).length;

  // Country select
  const cc = {};
  state.scholarships.forEach(s => {
    const k = s.country || (s.region === "WW" ? "WW" :
      s.region === "AR" ? "AR" : "Other");
    cc[k] = (cc[k]||0) + 1;
  });
  const cNames = Object.keys(cc).filter(k => k !== "WW" && k !== "AR" && k !== "Other")
    .sort((a,b) => cc[b]-cc[a]);
  $("#scholarshipCountry").innerHTML =
    `<option value="All">All countries (${state.scholarships.length})</option>` +
    cNames.map(n => `<option value="${esc(n)}">${esc(n)} (${cc[n]})</option>`).join("") +
    (cc.WW ? `<option value="WW">🌍 Worldwide / Remote (${cc["WW"]})</option>` : "") +
    (cc.AR ? `<option value="AR">🌙 Arab world (${cc["AR"]})</option>` : "") +
    (cc.Other ? `<option value="Other">Other (${cc["Other"]})</option>` : "");
  $("#scholarshipCountry").value = f.country;
}

/* ============================ DETAIL VIEW ============================ */
function renderScholarshipDetail(s, scroll = true) {
  if (!s) { location.hash = ""; return; }
  document.title = `${s.title} | Scholarships | ${CONFIG.siteName}`;

  $("#detailTitle").innerHTML    = esc(s.title);
  $("#detailCompany").textContent = s.provider || "";
  $("#detailLogo").innerHTML     = schLogoHtml({ provider: s.provider || s.title, logo:"" }, 64);

  $("#detailMeta").innerHTML = `
    <span class="badge">📍 ${esc(s.location || s.country || "—")}</span>
    ${s.remote ? '<span class="badge remote">🌐 Remote / Worldwide</span>' : ""}
    ${s.level ? `<span class="badge">${esc(s.level)}</span>` : ""}
    ${s.funding ? `<span class="badge funding-badge" style="background:var(--green-bg)">${esc(s.funding)}</span>` : ""}
    ${s.isArab ? '<span class="badge" style="background:#fef3c7;color:#92400e">🌙 Arab world</span>' : ""}
    ${s.isWomen ? '<span class="badge" style="background:#fce7f3;color:#9d174d">👩 Women</span>' : ""}
    ${s.isTech ? '<span class="badge" style="background:#dbeafe;color:#1e40af">💻 Tech / STEM</span>' : ""}
    <span class="badge">${timeAgo(s.deadline || s.date)}</span>
    <a class="source-credit" href="${esc(s.url || "#")}" target="_blank"
      rel="noopener noreferrer">Source: ${esc(s.source || "")}</a>`;

  $("#detailBody").innerHTML = sanitizeHtml(s.description) ||
    "<p><em>Full details available on the provider's page.</em></p>";

  $("#applyNowBtn").href       = s.url || "#";
  $("#applyNowBtn").dataset.url = s.url || "#";
  $("#detailSaveBtn").innerHTML = state.bookmarks.has(s.id) ? "★ Saved" : "☆ Save";
  $("#detailSaveBtn").onclick   = () => {
    toggleBookmark(s.id);
    renderScholarshipDetail(s);
  };

  $("#detailAmount").textContent   = s.amount_str || "Not specified";
  $("#detailProvider").textContent = s.provider || "—";
  $("#detailLocation").textContent = s.location || s.country || "—";
  $("#detailFunding").textContent  = s.funding || "—";
  $("#detailLevel").textContent    = s.level || "—";
  $("#detailDeadline").textContent = s.deadline ? new Date(s.deadline).toLocaleDateString(
    "en-US", { month:"short", day:"numeric", year:"numeric" }) : "Not specified";
  $("#detailRegion").textContent   = s.region === "AR" ? "Arab world" :
    s.region === "EU" ? "Europe" :
    s.region === "US" ? "USA" :
    s.region === "WW" ? "Worldwide / Remote" : "—";
  $("#detailSource").textContent   = s.source || "—";

  const rel = state.scholarships
    .filter(x => x.funding === s.funding && x.id !== s.id)
    .slice(0, 4);
  $("#relatedTitle").classList.toggle("hidden", !rel.length);
  $("#relatedGrid").innerHTML = rel.map(scholarshipCardHtml).join("");

  const adBox = $("#detailAd");
  adBox.innerHTML = "";
  adBox.append(adEl(CONFIG.adSlots.detail));
  try { if (adsenseActive()) (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch {}

  $("#viewHome").classList.add("hidden");
  $("#viewDetail").classList.remove("hidden");
  if (scroll) window.scrollTo({ top: 0 });
}

function schLogoHtml(job, size = 46) {
  const letter = esc((job.provider || job.title || "W").charAt(0).toUpperCase());
  const fb = `<span class="job-logo-fallback" style="width:${size}px;height:${size}px">${letter}</span>`;
  if (job.logo && /^https?:\/\//i.test(job.logo)) {
    return `<span style="position:relative;display:inline-block;width:${size}px;height:${size}px;flex:none">
      ${fb}<img class="job-logo" style="position:absolute;inset:0;width:${size}px;height:${size}px"
      src="${esc(job.logo)}" alt="" loading="lazy" referrerpolicy="no-referrer"
      onerror="this.remove()"></span>`;
  }
  return fb;
}

/* ============================ BOOKMARKS ============================ */
function toggleBookmark(id) {
  if (state.bookmarks.has(id)) state.bookmarks.delete(id);
  else state.bookmarks.add(id);
  store.set("ww:schBookmarks-page", [...state.bookmarks]);
  renderScholarships();
  const s = state.scholarships.find(x => x.id === id);
  if (s) renderScholarshipDetail(s);
}

/* ============================ ADS ============================ */
let adsLoaded = false;
function adsenseConfigured() {
  return CONFIG.adsenseClient.startsWith("ca-pub-") &&
    !CONFIG.adsenseClient.includes("XXXX");
}
function adsenseActive() {
  return adsenseConfigured() &&
    !!(window.WintConsent && window.WintConsent.allows("advertising"));
}
function loadAdsense() {
  if (!adsenseActive() || adsLoaded ||
      document.querySelector('script[src*="pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"]'))
    return;
  adsLoaded = true;
  const s = document.createElement("script");
  s.async = true;
  s.crossOrigin = "anonymous";
  s.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${CONFIG.adsenseClient}`;
  document.head.appendChild(s);
}
function adEl(slot, label = "Advertisement") {
  const div = document.createElement("div");
  div.className = "ad-slot";
  if (!adsenseActive() || !slot) {
    div.classList.add("hidden");
    div.setAttribute("aria-hidden", "true");
    return div;
  }
  div.innerHTML = `<div class="ad-label">${esc(label)}</div>
    <ins class="adsbygoogle" style="display:block"
      data-ad-client="${esc(CONFIG.adsenseClient)}"
      data-ad-slot="${esc(slot)}"
      data-ad-format="auto"
      data-full-width-responsive="true"></ins>`;
  return div;
}

/* ============================ INTERACTIONS ============================ */
function applyFilters() { renderScholarships(); }

function bindEvents() {
  let debounce;
  $("#scholarshipSearch").addEventListener("input", e => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      state.filters.q = e.target.value.trim();
      state.visible = 24;
      applyFilters();
    }, 250);
  });
  $("#scholarshipFunding").addEventListener("change", e => {
    state.filters.funding = e.target.value;
    state.visible = 24;
    applyFilters();
  });
  $("#scholarshipLevel").addEventListener("change", e => {
    state.filters.level = e.target.value;
    state.visible = 24;
    applyFilters();
  });
  $("#scholarshipRegion").addEventListener("change", e => {
    state.filters.region = e.target.value;
    state.visible = 24;
    applyFilters();
  });
  $("#scholarshipCountry").addEventListener("change", e => {
    state.filters.country = e.target.value;
    state.visible = 24;
    applyFilters();
  });
  $("#scholarshipSort").addEventListener("change", e => {
    state.filters.sort = e.target.value;
    state.visible = 24;
    applyFilters();
  });
  $("#scholarshipReset").addEventListener("click", () => {
    state.filters = {
      q:"", funding:"All", level:"All", region:"All",
      country:"All", sort:"deadline",
    };
    $("#scholarshipSearch").value   = "";
    $("#scholarshipFunding").value   = "All";
    $("#scholarshipLevel").value     = "All";
    $("#scholarshipRegion").value    = "All";
    $("#scholarshipCountry").value   = "All";
    $("#scholarshipSort").value      = "deadline";
    state.visible = 24;
    applyFilters();
  });

  // Funding chips
  $("#scholarshipCatChips").addEventListener("click", e => {
    const btn = e.target.closest("[data-sch-funding]");
    if (!btn) return;
    state.filters.funding = btn.dataset.schFunding;
    $("#scholarshipFunding").value = state.filters.funding;
    state.visible = 24;
    applyFilters();
  });

  // Grid clicks
  $("#scholarshipGrid").addEventListener("click", e => {
    const b = e.target.closest("[data-sch-bookmark]");
    if (b) { e.preventDefault(); toggleBookmark(b.dataset.schBookmark); return; }
    const r = e.target.closest("#scholarshipResetBtn");
    if (r) {
      state.filters = {
        q:"", funding:"All", level:"All", region:"All",
        country:"All", sort:"deadline",
      };
      applyFilters();
    }
  });

  // Load more
  $("#scholarshipLoadMoreBtn").addEventListener("click", () => {
    state.visible += 24;
    renderScholarships();
  });

  // Quick chips in hero
  $$(".quick-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      const cat = btn.dataset.quick;
      if (cat === "Fully Funded")      { state.filters.funding = "Fully Funded";   $("#scholarshipFunding").value = "Fully Funded";   }
      else if (cat === "Partially Funded") { state.filters.funding = "Partially Funded"; $("#scholarshipFunding").value = "Partially Funded"; }
      else if (cat === "Government")   { state.filters.funding = "Government";       $("#scholarshipFunding").value = "Government";     }
      else if (cat === "Fellowship")   { state.filters.funding = "Fellowship";       $("#scholarshipFunding").value = "Fellowship";     }
      else if (cat === "Arab")         { state.filters.region = "AR";              $("#scholarshipRegion").value = "AR"; }
      else if (cat === "Women")        { state.filters.q = "women";               $("#scholarshipSearch").value = "women"; }
      else if (cat === "Engineering & IT") { state.filters.q = "Engineering & IT"; $("#scholarshipSearch").value = "Engineering & IT"; }
      else if (cat === "Data & AI")    { state.filters.q = "Data & AI";          $("#scholarshipSearch").value = "Data & AI"; }
      else { state.filters.country = "All"; $("#scholarshipCountry").value = "All"; }
      state.visible = 24;
      applyFilters();
      $("#scholarships").scrollIntoView({ behavior: "smooth" });
    });
  });

  // Bookmark button (header)
  $("#savedBtn").addEventListener("click", () => {
    // Toggle saved-only filter
    const savedOnly = !state.filters.savedOnly;
    state.filters.savedOnly = savedOnly;
    applyFilters();
    $("#scholarships").scrollIntoView({ behavior: "smooth" });
  });

  // Theme
  $("#themeBtn").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    store.set("ww:theme-page", next);
  });

  // Mobile nav
  $("#navToggle").addEventListener("click", () =>
    $("#mainNav").classList.toggle("open"));

  // Router
  window.addEventListener("hashchange", route);

  // Share
  $("#shareCopyBtn").addEventListener("click", () => {
    const url = $("#applyNowBtn") ? location.href : "";
    if (navigator.clipboard)
      navigator.clipboard.writeText(location.href).then(
        () => toast("Link copied to clipboard"));
    else toast("Copy the URL from the address bar");
  });
  $("#shareXBtn").addEventListener("click", () => {
    const t = encodeURIComponent(document.title);
    window.open(`https://twitter.com/intent/tweet?text=${t}&url=${encodeURIComponent(location.href)}`,
      "_blank", "noopener");
  });
  $("#shareFBBtn").addEventListener("click", () => {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(location.href)}`,
      "_blank", "noopener");
  });
}

/* ============================ ROUTER ============================ */
function route() {
  const m = location.hash.match(/^#\/scholarship\/(.+)$/);
  if (m) {
    const id = decodeURIComponent(m[1]);
    const s  = state.scholarships.find(x => x.id === id);
    if (s) { renderScholarshipDetail(s, false); return; }
  }
  showHomeView(false);
}

function showHomeView(scroll = true) {
  $("#viewDetail").classList.add("hidden");
  $("#viewHome").classList.remove("hidden");
  $("#viewHome").scrollIntoView({ behavior: scroll ? "smooth" : "auto" });
}

/* ============================ BOOT ============================ */
document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  $("#savedCount").textContent = state.bookmarks.size;
  $("#year").textContent = new Date().getFullYear();

  // Load scholarships, then restore the pre-reload scroll position
  const loadSch = (retry = true) =>
    fetch("data/scholarships.json")
      .then(r => r.json())
      .then(snap => {
        state.scholarships = snap.scholarships.map(normalize);
        renderScholarships();
      })
      .catch(() => {
        // fallback: try again
        if (retry) return loadSch(false);
      });
  loadSch().then(wwRestoreScroll);

  // Init theme
  const saved = store.get("ww:theme-page", null);
  document.documentElement.dataset.theme = saved === "dark" ? "dark" : "light";
});
