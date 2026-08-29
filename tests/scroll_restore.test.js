/* Mock-browser test for the scroll-restoration block in js/app.js.
   Simulates: save on pagehide -> reload -> restore after lists render.
   Run: node tests/scroll_restore.test.js */
const fs = require("fs");
const assert = require("assert");

// ---- extract the scroll-restoration block from js/app.js ----
const src = fs.readFileSync("js/app.js", "utf8");
const start = src.indexOf("const WW_SCROLL_KEY");
const end = src.indexOf('document.addEventListener("visibilitychange"');
assert(start > 0 && end > start, "block not found");
const block = src.slice(start, end) + `
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") wwSaveScroll();
});
`;

function makeEnv({ url, savedY, urlFiltered }) {
  const store = new Map();
  if (savedY != null) store.set("ww:scroll:" + url, String(savedY));
  const listeners = {};
  const g = {
    // browser globals
    location: { pathname: "/", search: "", hash: "", ...parseUrl(url) },
    sessionStorage: {
      getItem: k => (store.has(k) ? store.get(k) : null),
      setItem: (k, v) => store.set(k, String(v)),
      removeItem: k => store.delete(k),
    },
    scrollY: 4242,
    scrollTo: (x, y) => { g._scrolledTo = y; },
    addEventListener: (ev, fn) => { (listeners[ev] ||= []).push(fn); },
    document: {
      documentElement: { style: { scrollBehavior: "" } },
      addEventListener: (ev, fn) => { (listeners["doc:" + ev] ||= []).push(fn); },
      visibilityState: "visible",
    },
    // page state referenced by the block
    state: { urlFiltered: !!urlFiltered },
    _store: store, _listeners: listeners,
  };
  return g;
}
function parseUrl(url) {
  const u = new URL("https://wintworks.com" + url);
  return { search: u.search, hash: u.hash };
}

function run(env, withBlock) {
  const fn = new Function(
    "location", "sessionStorage", "window",
    "document", "state",
    withBlock + "\nreturn { wwRestoreScroll, wwSaveScroll, doc: document };"
  );
  const win = {
    addEventListener: env.addEventListener,
    scrollTo: (x, y) => env.scrollTo(x, y),
    get scrollY() { return env.scrollY; },
  };
  return fn(env.location, env.sessionStorage, win, env.document, env.state);
}

let pass = 0;
function t(name, cond) { assert(cond, "FAIL: " + name); console.log("ok -", name); pass++; }

// 1. Reload mid-page: saved 4242px, no hash -> restores exactly there, instantly, and clears the key
{
  const env = makeEnv({ url: "/", savedY: 4242 });
  run(env, block).wwRestoreScroll();
  t("restores saved offset after reload", env._scrolledTo === 4242);
  t("bypasses smooth scroll during restore", env.document.documentElement.style.scrollBehavior === "");
  t("clears key after restore", env.sessionStorage.getItem("ww:scroll:/") === null);
}

// 2. First visit (nothing saved) -> no scroll at all
{
  const env = makeEnv({ url: "/", savedY: null });
  run(env, block).wwRestoreScroll();
  t("no restore on first visit", env._scrolledTo === undefined);
}

// 3. Hash route open (#/job/x) -> never steals scroll
{
  const env = makeEnv({ url: "/#/job/abc", savedY: 999 });
  run(env, block).wwRestoreScroll();
  t("skips restore on hash routes", env._scrolledTo === undefined);
}

// 4. Filtered URL (?cat=tech) -> load() scrolls to #jobs itself, we stay out of the way
{
  const env = makeEnv({ url: "/?cat=tech", savedY: 999, urlFiltered: true });
  run(env, block).wwRestoreScroll();
  t("skips restore on url-filtered views", env._scrolledTo === undefined);
}

// 5. Restore is idempotent (safety-net calls must not re-scroll)
{
  const env = makeEnv({ url: "/", savedY: 100 });
  const api = run(env, block);
  api.wwRestoreScroll(); api.wwRestoreScroll();
  t("restore runs only once", env._scrolledTo === 100);
}

// 6. pagehide saves the live offset for the next reload
{
  const env = makeEnv({ url: "/", savedY: null });
  const api = run(env, block);
  env._listeners["pagehide"][0]();
  t("pagehide persists scroll offset", env._store.get("ww:scroll:/") === "4242");
}

// 7. Tab hidden (mobile) also persists
{
  const env = makeEnv({ url: "/", savedY: null });
  const api = run(env, block);
  env.document.visibilityState = "hidden";
  env._listeners["doc:visibilitychange"][0]();
  t("visibilitychange persists scroll offset", env._store.get("ww:scroll:/") === "4242");
}

console.log("\n" + pass + " scroll-restoration assertions passed");
