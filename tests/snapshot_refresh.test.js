/* Mock-browser test for the snapshot refresh layer in js/app.js.
   Covers the "the site does not update jobs" fixes:
     • data/jobs.json is requested with a version query and an explicit cache mode
       (a cached CDN/browser copy was serving yesterday's snapshot)
     • the manual refresh bypasses every cache with no-store
     • snapshot metadata (snapshot_id, generated_at, per-source counts) reaches
       state and localStorage, with a trimmed fallback when the quota is exceeded
     • the freshness stamp and the stale warning render
     • index.html actually carries the DOM hooks the script expects
   Run: node tests/snapshot_refresh.test.js */
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const src = fs.readFileSync("js/app.js", "utf8");
const start = src.indexOf("/* ---- snapshot transport");
const end = src.indexOf("async function refreshLive(");
assert(start > 0 && end > start, "snapshot transport block not found in js/app.js");
const block = src.slice(start, end);

function makeElement() {
  return {
    textContent: "", innerHTML: "", disabled: false,
    dataset: {},
    classes: new Set(),
    classList: {
      add(c) { this._el.classes.add(c); },
      remove(c) { this._el.classes.delete(c); },
      toggle(c, on) { on ? this._el.classes.add(c) : this._el.classes.delete(c); },
      contains(c) { return this._el.classes.has(c); },
    },
  };
}
function el() { const e = makeElement(); e.classList._el = e; return e; }

function makeCtx({ snapshot, quotaFull = false, staleHours = 0 } = {}) {
  const calls = [];
  const store = new Map();
  const elements = { "#snapStamp": el(), "#refreshSnapshot": el(), "#jobs": el() };
  const ctx = {
    console,
    CONFIG: {
      snapshotUrl: "data/jobs.json", snapshotCheckMinutes: 15,
      snapshotStaleHours: staleHours || 12, browserLiveRefresh: false,
      maxJobsInMemory: 1800,
    },
    state: { jobs: [], snapshotMeta: null, urlFiltered: false, sourceStatus: {} },
    $: sel => elements[sel] || null,
    esc: s => String(s ?? ""),
    timeAgo: iso => {
      const s = (Date.now() - new Date(iso).getTime()) / 1000;
      return s < 60 ? "just now" : `${Math.floor(s / 60)}m ago`;
    },
    normalize: j => j,
    setJobs(list) { ctx.state.jobs = list; },
    renderAll() { calls.push("renderAll"); },
    applyFilters() { calls.push("applyFilters"); },
    route() { calls.push("route"); },
    refreshLive() { calls.push("refreshLive"); },
    toast(msg) { calls.push("toast:" + msg); },
    store: {
      get: (k, fallback) => (store.has(k) ? JSON.parse(store.get(k)) : fallback),
      set: (k, v) => {
        if (quotaFull) return false;
        store.set(k, JSON.stringify(v));
        return true;
      },
    },
    setTimeout: (fn) => { fn(); return 0; },
    clearTimeout: () => {},
    AbortController: class { constructor() { this.signal = {}; } abort() {} },
    Date,
    JSON,
    Math,
    Number,
    Object,
    Array,
    Set,
    isFinite,
    Error,
    Promise,
    fetch(url, opts) {
      calls.push(`fetch:${url}:${opts && opts.cache}`);
      if (snapshot instanceof Error) return Promise.reject(snapshot);
      return Promise.resolve({ ok: true, json: () => Promise.resolve(snapshot) });
    },
  };
  ctx.localStorage = store;
  vm.createContext(ctx);
  vm.runInContext(block, ctx);
  return { ctx, calls, store, elements };
}

const fresh = () => ({
  generated_at: new Date().toISOString(),
  count: 2,
  snapshot_id: "snap-aaa",
  per_source: { "The Muse": 96, Arbeitnow: 1401 },
  per_source_kept: { "The Muse": 96, Arbeitnow: 900 },
  source_errors: ["Remotive: 503"],
  jobs: [
    { id: "1", title: "A", company: "X", source: "The Muse", date: new Date().toISOString(), region: "US" },
    { id: "2", title: "B", company: "Y", source: "Arbeitnow", date: new Date().toISOString(), region: "EU" },
  ],
});

(async () => {
  // ---- automatic load: versioned URL, revalidating cache mode -----------------
  {
    const s = fresh();
    const { ctx, calls, store, elements } = makeCtx({ snapshot: s });
    await ctx.load();
    const fetched = calls.find(c => c.startsWith("fetch:"));
    assert.match(fetched, /^fetch:data\/jobs\.json\?v=t\d+:no-cache$/, "cache-busted URL: " + fetched);
    assert.strictEqual(ctx.state.jobs.length, 2, "jobs applied");
    assert.strictEqual(ctx.state.snapshotMeta.id, "snap-aaa", "snapshot id tracked");
    assert.strictEqual(ctx.state.snapshotMeta.perSource["The Muse"], 96, "fetched counts kept");
    assert.strictEqual(ctx.state.snapshotMeta.perSourceKept["The Muse"], 96, "kept counts kept");
    assert.deepStrictEqual(ctx.state.snapshotMeta.errors, ["Remotive: 503"]);
    const saved = JSON.parse(store.get("ww:snap"));
    assert.strictEqual(saved.meta.id, "snap-aaa", "snapshot id persisted for the next visit");
    assert.strictEqual(saved.jobs.length, 2);
    assert.match(elements["#snapStamp"].innerHTML, /Updated <b>just now<\/b>/,
      "freshness stamp: " + elements["#snapStamp"].innerHTML);
    assert.match(elements["#snapStamp"].innerHTML, /2 jobs from 2 sources/);
    assert.ok(!elements["#snapStamp"].classList.contains("is-stale"), "not stale");
    assert.ok(calls.includes("route"), "route() still runs after load");
    console.log("ok - load() busts the cache, keeps snapshot metadata and stamps freshness");
  }

  // ---- cached copy first, no flash of empty board ----------------------------
  {
    const { ctx, elements } = makeCtx({ snapshot: new Error("offline") });
    await ctx.load();
    assert.strictEqual(ctx.state.jobs.length, 0, "nothing to show when both fail");
    assert.strictEqual(elements["#snapStamp"].textContent,
      "updated automatically several times a day", "stamp keeps a sane default");
    console.log("ok - load() survives a failed snapshot fetch");
  }

  // ---- manual refresh: no-store, no quota errors, trimmed fallback -----------
  {
    const big = fresh();
    big.jobs = Array.from({ length: 1200 }, (_, i) => ({
      id: "j" + i, title: "T" + i, company: "C", source: "Arbeitnow",
      date: new Date().toISOString(), region: "EU",
    }));
    big.count = 1200;
    const { ctx, calls } = makeCtx({ snapshot: big, quotaFull: true });
    const changed = await ctx.refreshSnapshot(true);
    assert.ok(calls.some(c => /:no-store$/.test(c)), "manual refresh bypasses the cache");
    assert.ok(calls.some(c => /\?v=f\d+:no-store$/.test(c)), "force URL is unique per click");
    assert.strictEqual(changed, true, "new snapshot id reported as a change");
    assert.strictEqual(ctx.state.jobs.length, 1200, "quota failures never drop data on screen");
    assert.ok(calls.some(c => c.startsWith("toast:") && /newer snapshot/.test(c)),
      "user is told the board moved: " + calls.filter(c => c.startsWith("toast:")));
    console.log("ok - refreshSnapshot(true) forces a no-store fetch and tells the user");
  }

  // ---- unchanged snapshot is reported honestly --------------------------------
  {
    const s = fresh();
    const { ctx, calls } = makeCtx({ snapshot: s });
    await ctx.load();
    const again = await ctx.refreshSnapshot(true);
    assert.strictEqual(again, false, "same snapshot_id is not an update");
    assert.ok(calls.some(c => /Already current/.test(c)), "the 'already current' message shows");
    console.log("ok - an unchanged snapshot is not faked as an update");
  }

  // ---- stale data is flagged --------------------------------------------------
  {
    const s = fresh();
    s.generated_at = new Date(Date.now() - 40 * 3600 * 1000).toISOString();
    const { ctx, elements } = makeCtx({ snapshot: s });
    await ctx.load();
    const stamp = elements["#snapStamp"];
    assert.ok(stamp.classList.contains("is-stale"), "40h-old snapshot flagged");
    assert.match(stamp.innerHTML, /crawler is overdue/, "and explains what to do");
    console.log("ok - an overdue snapshot is visibly flagged instead of looking normal");
  }

  // ---- index.html wires the DOM the script needs ------------------------------
  {
    const html = fs.readFileSync("index.html", "utf8");
    for (const id of ["snapStamp", "refreshSnapshot", "syncStatus", "grid", "searchInput"]) {
      assert.ok(html.includes(`id="${id}"`), `index.html is missing #${id}`);
    }
    assert.match(html, /<script src="js\/app\.min\.js\?v=/, "bundle is version-stamped");
    console.log("ok - index.html carries the freshness hooks and a versioned bundle");
  }
})();
