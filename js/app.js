/* ============================================================
   WintWorks — job board engine
   Fetches US jobs automatically from free public sources,
   no API keys, no backend, no maintenance.
   ============================================================ */
"use strict";

/* ============================ CONFIG ============================ */
const CONFIG = {
  siteName: "WintWorks",
  siteUrl: "https://wintworks.com",
  contactEmail: "hello@wintworks.com",
  /* ─── Google AdSense ─────────────────────────────────────────
     After AdSense approves your site, replace the XXXX below with
     your publisher ID (starts with ca-pub-). Then create ad units
     and paste their slot IDs. That's the ONLY manual step. */
  adsenseClient: "ca-pub-XXXXXXXXXXXXXXXX",
  adSlots: { top: "0000000001", feed: "0000000002", detail: "0000000003" },
  /* ── refresh cadence (minutes) ── */
  refreshMinutes: 20,
  maxJobsInMemory: 1800,
};

/* ============================ UTILS ============================ */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function timeAgo(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const s = Math.max(1, Math.floor((Date.now() - d.getTime()) / 1000));
  if (s < 3600) return `${Math.max(1, Math.floor(s / 60))}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  if (s < 86400 * 7) return `${Math.floor(s / 86400)}d ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function sanitizeHtml(html) {
  if (!html) return "";
  const div = document.createElement("div");
  div.innerHTML = String(html);
  div.querySelectorAll("script,style,iframe,object,embed,form,input,button,link,meta,img,svg,canvas,video,audio").forEach((n) => n.remove());
  div.querySelectorAll("*").forEach((el) => {
    [...el.attributes].forEach((a) => {
      const name = a.name.toLowerCase();
      if (name.startsWith("on") || name === "style" || name === "id" || name === "class") el.removeAttribute(a.name);
      if (a.name === "href" && /^\s*javascript:/i.test(a.value)) el.removeAttribute("href");
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

/* =============== US + ALL-EUROPE REGION & COUNTRY DETECTION =============== */
const US_STATES = new Set(["alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida","georgia","hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine","maryland","massachusetts","michigan","minnesota","mississippi","missouri","montana","nebraska","nevada","new hampshire","new jersey","new mexico","new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island","south carolina","south dakota","tennessee","texas","utah","vermont","virginia","washington","west virginia","wisconsin","wyoming","district of columbia"]);
const US_ABBR = new Set(["al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia","ks","ky","la","me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa","wv","wi","wy","dc"]);
const US_CITIES = new Set(["atlanta","austin","baltimore","boston","charlotte","chicago","cincinnati","cleveland","columbus","dallas","denver","detroit","houston","indianapolis","jacksonville","las vegas","los angeles","miami","milwaukee","minneapolis","nashville","new orleans","new york","newark","oakland","oklahoma city","omaha","orlando","philadelphia","phoenix","pittsburgh","portland","raleigh","sacramento","san antonio","san diego","san francisco","san jose","seattle","st. louis","st louis","tampa","washington","arlington","boulder","brooklyn","burlington","chandler","charleston","colorado springs","fort worth","frisco","fremont","grand rapids","irvine","jersey city","kansas city","long beach","madison","menlo park","mountain view","new haven","palo alto","plano","redmond","richmond","rochester","salt lake city","santa clara","santa fe","santa monica","sunnyvale","tempe","tucson","tulsa","urbana","waltham","walnut creek","princeton","albany","ann arbor","asheville","boise","corvallis","davis","durham","evanston","fort collins","gainesville","hershey","knoxville","lexington","lincoln","little rock","louisville","mclean","memphis","mesa","norfolk","pasadena","provo","reston","round rock","san mateo","scottsdale","sioux falls","spokane","springfield","stamford","syracuse","tallahassee","wichita","wilmington","worcester","birmingham","manchester","bristol","oxford","plymouth","brighton","madison"]);

const EU_WORDS = ["europe","european","uk","united kingdom","britain","british","england","scotland","wales","northern ireland","ireland","france","germany","deutschland","allemagne","spain","españa","italy","italia","portugal","netherlands","nederland","holland","belgium","belgique","belgie","luxembourg","switzerland","schweiz","suisse","austria","österreich","sweden","sverige","norway","norge","denmark","danmark","finland","suomi","iceland","poland","polska","polen","czech","czechia","slovakia","hungary","romania","bulgaria","greece","croatia","slovenia","serbia","bosnia","montenegro","north macedonia","albania","kosovo","estonia","latvia","lithuania","ukraine","moldova","belarus","russia","malta","cyprus","turkey","türkiye","georgien","armenia","arménie","azerbaijan","monaco","andorra","liechtenstein","gibraltar","isle of man","bavaria","bayern"];
const EU_ABBR = new Set(["uk","gb","ie","fr","es","it","pt","nl","be","lu","ch","at","se","no","dk","fi","is","pl","cz","sk","hu","ro","bg","gr","hr","si","rs","ba","mk","xk","ee","lv","lt","ua","by","ru","cy","tr"]);
const EU_CITIES = new Set(["london","leeds","liverpool","edinburgh","glasgow","belfast","cardiff","dublin","cork","paris","lyon","marseille","toulouse","bordeaux","nice","lille","strasbourg","nantes","berlin","munich","munchen","münchen","hamburg","frankfurt","cologne","köln","stuttgart","dusseldorf","düsseldorf","leipzig","dortmund","essen","bremen","dresden","hanover","nuremberg","nürnberg","trier","zurich","zürich","geneva","genève","basel","bern","lausanne","amsterdam","rotterdam","utrecht","eindhoven","brussels","brussel","antwerp","ghent","vienna","wien","graz","linz","salzburg","madrid","barcelona","valencia","seville","bilbao","malaga","lisbon","lisboa","porto","milan","milano","rome","roma","turin","torino","naples","napoli","florence","firenze","warsaw","warszawa","krakow","kraków","wroclaw","gdansk","poznan","lodz","lublin","katowice","szczecin","prague","praha","brno","bratislava","budapest","debrecen","szeged","bucharest","bucuresti","cluj","timisoara","iasi","brasov","sofia","plovdiv","varna","athens","athina","thessaloniki","zagreb","split","dubrovnik","ljubljana","belgrade","beograd","sarajevo","skopje","tirana","podgorica","tallinn","tartu","riga","vilnius","kaunas","klaipeda","kyiv","kiev","lviv","odesa","chisinau","minsk","valletta","nicosia","limassol","istanbul","ankara","tbilisi","yerevan","baku","reykjavik","monaco","gibraltar","stockholm","gothenburg","malmo","uppsala","lund","oslo","bergen","stavanger","trondheim","copenhagen","københavn","helsinki","tampere","turku","oulu"]);

const WW_WORDS = ["worldwide","anywhere","any country","global","all countries","international","emea","remote","homeoffice","fully remote","remote job","work from home","wfh"];
function hasWorldwide(s) {
  const low = s.toLowerCase();
  return WW_WORDS.some((w) => low.includes(w));
}

/* country markers: [countryName, [markers…]] — checked with word boundaries */
const COUNTRY_MARKERS = [
  ["United Kingdom", ["united kingdom","britain","british","england","scotland","wales","northern ireland","uk","london","manchester","leeds","liverpool","edinburgh","glasgow","belfast","cardiff","grossbritannien","großbritannien","royaume-uni"]],
  ["Germany", ["germany","deutschland","allemagne","bavaria","bayern","berlin","munich","munchen","münchen","hamburg","frankfurt","cologne","köln","stuttgart","dusseldorf","düsseldorf","leipzig","dortmund","essen","bremen","dresden","hanover","nuremberg","nürnberg","trier","de-"]],
  ["France", ["france","paris","lyon","marseille","toulouse","bordeaux","nice","lille","strasbourg","nantes"]],
  ["Netherlands", ["netherlands","nederland","holland","amsterdam","rotterdam","utrecht","eindhoven"]],
  ["Belgium", ["belgium","belgique","belgie","brussels","brussel","antwerp","ghent"]],
  ["Switzerland", ["switzerland","schweiz","suisse","zurich","zürich","geneva","genève","basel","bern","lausanne","luzern"]],
  ["Austria", ["austria","österreich","oesterreich","vienna","wien","graz","linz","salzburg"]],
  ["Spain", ["spain","españa","espana","espagne","madrid","barcelona","valencia","seville","bilbao","malaga"]],
  ["Portugal", ["portugal","lisbon","lisboa","porto"]],
  ["Italy", ["italy","italia","italie","milan","milano","rome","roma","turin","torino","naples","napoli","florence","firenze"]],
  ["Ireland", ["ireland","irland","irlande","dublin","cork"]],
  ["Sweden", ["sweden","sverige","schweden","suède","stockholm","gothenburg","malmo","uppsala","lund"]],
  ["Norway", ["norway","norge","norwegen","oslo","bergen","stavanger","trondheim"]],
  ["Denmark", ["denmark","danmark","dänemark","copenhagen","københavn","aarhus","odense"]],
  ["Finland", ["finland","finlande","finnland","suomi","helsinki","tampere","turku","oulu"]],
  ["Iceland", ["iceland","island","ísland","reykjavik"]],
  ["Poland", ["poland","polska","polen","pologne","warsaw","warszawa","krakow","kraków","wroclaw","gdansk","poznan","lodz","lublin","katowice","szczecin"]],
  ["Czechia", ["czech","czechia","tschechien","tchéquie","prague","praha","brno"]],
  ["Slovakia", ["slovakia","slovensko","slowakei","bratislava"]],
  ["Hungary", ["hungary","ungarn","hongrie","budapest","debrecen","szeged"]],
  ["Romania", ["romania","românia","rumänien","bucharest","bucuresti","cluj","timisoara","iasi","brasov"]],
  ["Bulgaria", ["bulgaria","bulgarien","sofia","plovdiv","varna"]],
  ["Greece", ["greece","griechenland","grèce","athens","athina","thessaloniki"]],
  ["Croatia", ["croatia","kroatien","hrvatska","zagreb","split","dubrovnik"]],
  ["Slovenia", ["slovenia","slowenien","slovenija","ljubljana"]],
  ["Serbia", ["serbia","serbien","srbija","belgrade","beograd"]],
  ["Bosnia & Herzegovina", ["bosnia","bosnien","bosnie","sarajevo"]],
  ["Montenegro", ["montenegro","monténégro","podgorica"]],
  ["North Macedonia", ["macedonia","nordmazedonien","skopje"]],
  ["Albania", ["albania","albanien","tirana"]],
  ["Kosovo", ["kosovo"]],
  ["Estonia", ["estonia","estland","eesti","tallinn","tartu"]],
  ["Latvia", ["latvia","lettland","latvija","riga"]],
  ["Lithuania", ["lithuania","litauen","lietuva","vilnius","kaunas","klaipeda"]],
  ["Ukraine", ["ukraine","ukraina","kyiv","kiev","lviv","odesa"]],
  ["Moldova", ["moldova","moldawien","chisinau"]],
  ["Belarus", ["belarus","weissrussland","minsk"]],
  ["Malta", ["malta","valletta"]],
  ["Cyprus", ["cyprus","zypern","chypre","nicosia","limassol"]],
  ["Turkey", ["turkey","türkiye","turquie","türkei","istanbul","ankara"]],
  ["Georgia", ["tbilisi","georgien","géorgie"]],
  ["Armenia", ["armenia","armenien","yerevan"]],
  ["Azerbaijan", ["azerbaijan","aserbaidschan","baku"]],
  ["Monaco", ["monaco"]],
  ["Luxembourg", ["luxembourg","luxemburg"]],
  ["Andorra", ["andorra"]],
  ["Liechtenstein", ["liechtenstein"]],
  ["Gibraltar", ["gibraltar"]],
];

/* strong evidence = explicit country / state name / postal abbr pattern
   weak evidence = city name only — strong always beats weak */
const ABBR_RE = (set, s) => {
  const m1 = s.match(/,\s*([a-z]{2})\b/);
  if (m1 && set.has(m1[1])) return true;
  const m2 = s.match(/(?:^|[\s\-])([a-z]{2})(?:\s|$)/);
  if (m2 && set.has(m2[1]) && s.length <= 12) return true;
  const m3 = s.match(/\b([a-z]{2})\s*[,.]?$/);
  if (m3 && set.has(m3[1])) return true;
  return false;
};
const hasWord = (words, s) => words.some((w) => new RegExp(`\\b${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`).test(s));

const US_STRONG = ["united states","usa","u.s.a","us only", ...US_STATES];
const EU_STRONG = ["europe","european","united kingdom","britain","british","england","scotland","wales","northern ireland","ireland","france","germany","deutschland","allemagne","spain","españa","italy","italia","portugal","netherlands","nederland","holland","belgium","belgique","belgie","luxembourg","switzerland","schweiz","suisse","austria","österreich","sweden","sverige","norway","norge","denmark","danmark","finland","suomi","iceland","poland","polska","polen","czech","czechia","czech republic","slovakia","hungary","romania","bulgaria","greece","croatia","slovenia","serbia","bosnia","montenegro","macedonia","albania","kosovo","estonia","latvia","lithuania","ukraine","moldova","belarus","russia","malta","cyprus","turkey","türkiye","georgien","armenia","azerbaijan","monaco","andorra","liechtenstein","gibraltar","isle of man","bavaria","bayern"];

function regionOf(loc) {
  if (!loc) return null;
  const s = String(loc).toLowerCase().trim();
  if (!s) return null;
  const usStrong = hasWord(US_STRONG, s) || ABBR_RE(US_ABBR, s);
  const euStrong = hasWord(EU_STRONG, s) || ABBR_RE(EU_ABBR, s);
  const usCity = hasWord([...US_CITIES], s);
  const euCity = hasWord([...EU_CITIES], s);
  if (usStrong && euStrong) return "WW";
  if (euStrong && !usStrong) return "EU";
  if (usStrong && !euStrong) return "US";
  if (euCity && !usCity) return "EU";
  if (usCity && !euCity) return "US";
  if (hasWorldwide(s)) return "WW";
  return null;
}
function countryOf(loc) {
  if (!loc) return "";
  const s = String(loc).toLowerCase().trim();
  if (!s) return "";
  const r = regionOf(loc);
  if (r === "US") return "USA";
  if (r !== "EU") return "";
  for (const [name, markers] of COUNTRY_MARKERS) {
    if (hasWord(markers, s)) return name;
  }
  return "";
}
function regionEmoji(j) {
  if (j.region === "US") return "🇺🇸 US";
  if (j.region === "EU") return "🇪🇺 EU";
  if (j.region === "WW") return "🌍 WW";
  return "";
}

/* ======================== CATEGORY TAXONOMY ======================== */
const TAXONOMY = [
  ["Engineering & IT", ["engineering","software","developer","development","devops","frontend","backend","full stack","mobile","ios","android","qa","testing","engineer","tech","it ","information technology","cloud","security","sysadmin","infrastructure","web","python","java","javascript","react","node","golang","ruby","php","blockchain","game","embedded","hardware","architect"]],
  ["Data & AI", ["data","analytics","analyst","machine learning"," ml "," ai ","artificial intelligence","bi ","database","scientist","statistician","deep learning","nlp","computer vision"]],
  ["Design & Creative", ["design","ux","ui","graphic","creative","illustrator","animation","art ","visual","brand","figma","product design"]],
  ["Marketing & Growth", ["marketing","seo","growth","digital marketing","social media","content marketing","brand","affiliate","ppc","advertising","go-to-market","gtm","communications","community","email marketing"]],
  ["Sales & Business Dev", ["sales","account executive","business development","bdr","sdr","account manager","partnership","sales development"]],
  ["Product & Project", ["product","pm","product manager","product owner","project manager","program manager","scrum","agile"]],
  ["Customer Support", ["customer support","customer service","support","success","customer success","csm","help desk","technical support","service desk"]],
  ["Finance & Accounting", ["finance","accounting","bookkeeper","financial","tax","audit","payroll","controller","treasury","cpa","actuary"]],
  ["HR & Recruiting", ["hr","human resources","recruiter","recruiting","talent","people operations","people","onboarding"]],
  ["Writing & Content", ["writing","writer","content","copywriter","editor","journalism","translation","editorial","blog","author","proofreader"]],
  ["Operations & Admin", ["operations","administration","office manager","logistics","supply chain","facilities","executive assistant","admin","procurement","warehouse","receptionist"]],
  ["Education & Training", ["education","teacher","tutor","training","instructional","elearning","learning","professor","curriculum","edtech"]],
  ["Healthcare & Wellness", ["healthcare","nurse","medical","clinical","health","therapy","pharma","physician"," care ","dentist","psycholog","wellness"]],
  ["Legal & Compliance", ["legal","lawyer","attorney","compliance","counsel","paralegal","law ","regulatory"]],
];
const OTHER = "Other";
const EXTRA_KEYS = {
  "Engineering & IT": ["informatik","informatica","informática","informatyka","ingenieur","ingeniero","ingénieur","inżynier","entwickler","desarrollador","programador","programmeur","programista","softwareentwickler","sistemas","système","elektronik","netzwerk","technik","ingeniería","ingenierie"],
  "Data & AI": ["daten","datos","données","dane","künstliche intelligenz","inteligencia artificial","intelligence artificielle","sztuczna inteligencja","analityk"],
  "Design & Creative": ["gestaltung","diseño","conception","projektowanie","grafika","ilustración","illustration"],
  "Marketing & Growth": ["werbung","publicidad","pubblicità","reklama","kommunikation","comunicación","communication","communicatie","komunikacja","mercadeo"],
  "Sales & Business Dev": ["verkauf","vertrieb","ventas","vendite","sprzedaż","verkoop","handel","commercial"],
  "Product & Project": ["produktmanager","projektleitung","projektmanager","chef de projet","projectleider","kierownik projektu","productmanager"],
  "Customer Support": ["kundendienst","service client","servicio al cliente","klantenservice","obsługa klienta"],
  "Finance & Accounting": ["finanzen","finanzas","finances","financieel","księgowość","buchhaltung","comptabilité","contabilidad","contabilità","rechnungswesen","buchhalter","accountant","finanz"],
  "HR & Recruiting": ["personalwesen","recursos humanos","ressources humaines","personeelszaken","zasoby ludzkie"],
  "Writing & Content": ["redaktion","redacción","rédaction","übersetzer","traductor","traducteur","tłumacz"],
  "Operations & Admin": ["logistik","logística","logistique","logistiek","logistyka","verwaltung","administración","administration","administratie","administracja","einkauf","compras","achats","inkoop","zakupy","lager","sachbearbeiter"],
  "Education & Training": ["bildung","enseñanza","enseignement","onderwijs","nauczanie","lehrer","profesor","enseignant","docent","nauczyciel","ausbildung"],
  "Healthcare & Wellness": ["gesundheit","gesundheitswesen","pflege","soins","santé","sanidad","salud","salute","zdrowie","gezondheidszorg","verpleging","verpleegkundige","cuidados","medizin","médecine","medicina","medycyna","krankenpflege","infirmier"],
  "Legal & Compliance": ["recht","droit","derecho","diritto","prawo","juridique","juridisch","jurídico","giuridico","prawny","anwalt","advocaat"],
};
for (const [cat, kws] of Object.entries(EXTRA_KEYS)) {
  const row = TAXONOMY.find((r) => r[0] === cat);
  if (row) row[1].push(...kws);
}
function mapCategory() {
  const blob = [...arguments].filter(Boolean).join(" ").toLowerCase();
  for (const [name, keys] of TAXONOMY) {
    for (const k of keys) if (blob.includes(k)) return name;
  }
  return OTHER;
}
function fmtMoney(lo, hi, symbol = "$") {
  const f = (v) => (v ? symbol + Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 }) : "");
  if (lo && hi) return `${f(lo)} – ${f(hi)} / yr`;
  if (lo) return `${f(lo)} / yr`;
  if (hi) return `up to ${f(hi)} / yr`;
  return "";
}
function salaryNumber(salaryStr) {
  const m = String(salaryStr || "").match(/\$([\d,]+)/);
  return m ? parseFloat(m[1].replace(/,/g, "")) : 0;
}

/* ============================ SOURCES ============================ */
const SOURCES = [
  {
    name: "The Muse", icon: "M",
    urls: [1, 2].map((p) => `https://www.themuse.com/api/public/jobs?page=${p}&limit=20`),
    parse(json) {
      const out = [];
      for (const r of json.results || []) {
        const locs = (r.locations || []).map((l) => l.name).filter(Boolean);
        if (locs.length && !regionOf(locs.join("; "))) continue;
        const cats = (r.categories || []).map((c) => c.name);
        const tags = (r.tags || []).map((t) => t.name || t);
        out.push({
          id: `muse-${r.id}`,
          title: r.name || "",
          company: (r.company || {}).name || "",
          logo: "",
          location: locs.join("; ") || "United States",
          remote: false,
          type: "",
          salary: "",
          date: r.publication_date || "",
          category: mapCategory(...cats, ...tags, r.name),
          tags: tags.slice(0, 6),
          description: r.contents || "",
          url: (r.refs || {}).landing_page || "",
          source: "The Muse",
        });
      }
      return out;
    },
  },
  {
    name: "Jobicy", icon: "J",
    urls: ["https://jobicy.com/api/v2/remote-jobs"],
    parse(json) {
      const out = [];
      for (const r of json.jobs || []) {
        if (!regionOf(r.jobGeo || "")) continue;
        const jt = r.jobType || [];
        const ind = r.jobIndustry || [];
        out.push({
          id: `jobicy-${r.id}`,
          title: r.jobTitle || "",
          company: r.companyName || "",
          logo: r.companyLogo || "",
          location: r.jobGeo || "",
          remote: true,
          type: jt[0] || "Remote",
          salary: [r.salaryMin, r.salaryMax].some((x) => x)
            ? fmtMoney(r.salaryMin, r.salaryMax) : "",
          date: r.pubDate || "",
          category: mapCategory(...ind, r.jobTitle),
          tags: ind.slice(0, 4),
          description: r.jobDescription || r.jobExcerpt || "",
          url: r.url || "",
          source: "Jobicy",
        });
      }
      return out;
    },
  },
  {
    name: "RemoteOK", icon: "R",
    urls: ["https://remoteok.com/api"],
    parse(json) {
      const out = [];
      for (const r of json || []) {
        if (!r || !r.position) continue;
        const loc = (r.location || "").replace(/,+/g, " ").trim();
        if (!regionOf(loc)) continue;
        out.push({
          id: `remoteok-${r.slug || r.id}`,
          title: r.position || "",
          company: r.company || "",
          logo: r.company_logo || r.logo || "",
          location: loc,
          remote: true,
          type: "Remote",
          salary: fmtMoney(r.salary_min, r.salary_max),
          date: r.date || "",
          category: mapCategory(...(r.tags || []), r.position),
          tags: (r.tags || []).slice(0, 6),
          description: r.description || "",
          url: r.apply_url || r.url || "",
          source: "RemoteOK",
        });
      }
      return out;
    },
  },
  {
    name: "Remotive", icon: "RE",
    urls: ["https://remotive.com/api/remote-jobs"],
    parse(json) {
      const out = [];
      for (const r of json.jobs || []) {
        if (!regionOf(r.candidate_required_location || "")) continue;
        out.push({
          id: `remotive-${r.id}`,
          title: r.title || "",
          company: r.company_name || "",
          logo: r.company_logo_url || r.company_logo || "",
          location: r.candidate_required_location || "",
          remote: true,
          type: (r.job_type || "").replace(/_/g, " "),
          salary: r.salary || "",
          date: r.publication_date || "",
          region: regionOf(r.candidate_required_location || "") || "",
          category: mapCategory(r.category, ...(r.tags || []), r.title),
          tags: (r.tags || []).slice(0, 6),
          description: r.description || "",
          url: r.url || "",
          source: "Remotive",
        });
      }
      return out;
    },
  },
  {
    name: "Arbeitnow", icon: "A",
    urls: Array.from({length: 2}, (_, i) => `https://www.arbeitnow.com/api/job-board-api?page=${i + 1}`),
    parse(json) {
      const out = [];
      for (const r of json.data || []) {
        const loc = r.location || "";
        const reg = regionOf(loc);
        if (!reg) continue;
        const jt = r.job_types || [];
        out.push({
          id: `arbeitnow-${r.slug || Math.random().toString(36).slice(2, 9)}`,
          title: r.title || "",
          company: r.company_name || "",
          logo: "",
          location: loc,
          region: reg,
          remote: !!r.remote,
          type: jt[0] || "",
          salary: "",
          date: r.created_at ? new Date(r.created_at * 1000).toISOString() : "",
          category: mapCategory(...(r.tags || []), r.title),
          tags: (r.tags || []).slice(0, 6),
          description: r.description || "",
          url: r.url || "",
          source: "Arbeitnow",
        });
      }
      return out;
    },
  },
];

async function fetchSource(src) {
  const results = [];
  let anySuccess = false;
  for (const item of src.urls) {
    const url = typeof item === "string" ? item : item.url;
    const meta = typeof item === "object" ? item : null;
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 20000);
    try {
      const res = await fetch(url, { signal: ctrl.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      results.push(...src.parse(await res.json(), meta));
      anySuccess = true;
    } catch (_) { /* skip failed page, keep others */ }
    finally { clearTimeout(timer); }
  }
  if (!anySuccess) throw new Error("source unreachable");
  return results;
}

/* ============================ DATA LAYER ============================ */
const state = {
  jobs: [],
  filters: { q: "", cat: "All", region: "All", country: "All", loc: "", remoteOnly: false, savedOnly: false, sort: "new" },
  visible: 24,
  bookmarks: new Set(store.get("ww:bookmarks", [])),
  lastLive: null,
  sourceStatus: {},   // name -> {ok, count}
};

function normalize(job) {
  job.salaryNum = salaryNumber(job.salary);
  job.isBookmarked = state.bookmarks.has(job.id);
  // prefer values from the source/snapshot (e.g. Adzuna market), fall back to
  // location-string detection for live-fetched jobs.
  job.region = job.region || regionOf(job.location) || null;
  job.country = job.country || countryOf(job.location) || "";
  return job;
}

function mergeJobs(list) {
  const byId = new Map(state.jobs.map((j) => [j.id, j]));
  for (const raw of list) {
    const j = normalize(raw);
    if (!j.title || !j.url || !j.region) continue;
    const exId = byId.get(j.id);
    if (exId) {
      if ((j.description || "").length > (exId.description || "").length) byId.set(j.id, j);
      continue;
    }
    // cross-source duplicate (same title+company)
    const key = (j.title + "|" + j.company).toLowerCase();
    let dup = null;
    for (const [id, e] of byId) {
      if ((e.title + "|" + e.company).toLowerCase() === key) { dup = e; break; }
    }
    byId.set(j.id, dup && (j.description || "").length > (dup.description || "").length ? j : dup || j);
  }
  const arr = [...byId.values()].sort((a, b) => new Date(b.date) - new Date(a.date));
  return arr.slice(0, CONFIG.maxJobsInMemory);
}

function setJobs(list) {
  state.jobs = list.map(normalize);
  renderAll();
}

const SNAP_TTL = 30 * 60 * 1000; // نعاود استخدام السناپشوت المخزن 30 دقيقة

async function load() {
  // 1) عرض فوري من localStorage (صفر تحميل للزائر العائد)
  const cached = store.get("ww:snap", null);
  if (cached && cached.jobs && Date.now() - cached.t < SNAP_TTL) {
    setJobs(cached.jobs.map(normalize));
  }
  // 2) تحديث من ملف السناپشوت (يستفيد من كاش HTTP؛ بدون cache-buster)
  try {
    const res = await fetch("data/jobs.json");
    if (res.ok) {
      const snap = await res.json();
      store.set("ww:snap", { t: Date.now(), jobs: snap.jobs }); // نسخة خفيفة للكاش فقط
      setJobs(snap.jobs.map(normalize));
    } else throw new Error("no snapshot");
  } catch {
    if (!cached) {
      const old = store.get("ww:jobs", null);
      if (old && Array.isArray(old)) setJobs(old);
    }
  }
  // 3) live refresh from all sources
  refreshLive(true);
  if (state.urlFiltered) {
    const j = $("#jobs");
    if (j && typeof j.scrollIntoView === "function")
      setTimeout(() => j.scrollIntoView({ behavior: "smooth" }), 350);
  }
}

async function refreshLive(initial = false) {
  const prevIds = new Set(state.jobs.map((j) => j.id));
  const active = SOURCES;
  const settled = await Promise.allSettled(active.map((s) => fetchSource(s)));
  const fresh = [];
  settled.forEach((r, i) => {
    const name = active[i].name;
    if (r.status === "fulfilled") {
      state.sourceStatus[name] = { ok: true, count: r.value.length };
      fresh.push(...r.value);
    } else {
      state.sourceStatus[name] = { ok: false, count: 0 };
    }
  });
  state.lastLive = new Date();
  setJobs(mergeJobs(fresh));
  const gained = state.jobs.filter((j) => !prevIds.has(j.id)).length;
  if (!initial && gained > 0) {
    toast(`${gained} new job${gained > 1 ? "s" : ""} found automatically`, "Show", showToastRefresh);
  }
  updateSyncPills();
}

function showToastRefresh() { applyFilters(); }

/* ============================ FILTERS ============================ */
function countMatches() {
  const f = state.filters;
  return state.jobs.filter((j) => matches(j, f)).length;
}

function matches(j, f) {
  if (f.savedOnly && !state.bookmarks.has(j.id)) return false;
  if (f.region && f.region !== "All" && j.region !== f.region) return false;
  if (f.country && f.country !== "All") {
    if (f.country === "WW") { if (j.country) return false; }
    else if (j.country !== f.country) return false;
  }
  if (f.remoteOnly && !j.remote) return false;
  if (f.cat !== "All" && j.category !== f.cat) return false;
  if (f.loc && !String(j.location).toLowerCase().includes(f.loc.toLowerCase())) return false;
  if (f.q) {
    const hay = `${j.title} ${j.company} ${j.location} ${j.category} ${(j.tags || []).join(" ")}`.toLowerCase();
    if (!hay.includes(f.q.toLowerCase())) return false;
  }
  return true;
}

function visibleJobs() {
  const f = state.filters;
  let arr = state.jobs.filter((j) => matches(j, f));
  if (f.sort === "salary") arr = [...arr].sort((a, b) => (b.salaryNum || 0) - (a.salaryNum || 0));
  return arr;
}

/* ============================ RENDERING ============================ */
function logoHtml(job, size = 46) {
  const letter = esc((job.company || job.title || "W").charAt(0).toUpperCase());
  const fb = `<span class="job-logo-fallback" style="width:${size}px;height:${size}px">${letter}</span>`;
  if (job.logo && /^https?:\/\//i.test(job.logo)) {
    return `<span style="position:relative;display:inline-block;width:${size}px;height:${size}px;flex:none">${fb}<img class="job-logo" style="position:absolute;inset:0;width:${size}px;height:${size}px" src="${esc(job.logo)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()"></span>`;
  }
  return fb;
}

function sourceName(source) {
  return source === "RemoteOK" ? "Remote OK" : source || "Original source";
}

function sourceAttribution(job) {
  const url = esc(job.url || "#");
  const rel = "noopener noreferrer"; // Deliberately no nofollow: Remote OK requires a followed source link.
  if (job.source === "Adzuna") {
    return `<a class="source-credit adzuna-credit" href="${url}" target="_blank" rel="${rel}" aria-label="Jobs by Adzuna">
      <span>Jobs by</span><img src="assets/adzuna-logo.png" alt="Adzuna" width="63" height="23">
    </a>`;
  }
  return `<a class="source-credit" href="${url}" target="_blank" rel="${rel}">Source: ${esc(sourceName(job.source))}</a>`;
}

function cardHtml(job) {
  const saved = state.bookmarks.has(job.id);
  return `
  <article class="job-card" data-id="${esc(job.id)}">
    <div class="job-card-top">
      ${logoHtml(job)}
      <div style="min-width:0">
        <h3 class="job-title"><a href="#/job/${encodeURIComponent(job.id)}">${esc(job.title)}</a></h3>
        <div class="job-company">${esc(job.company)}</div>
      </div>
      <button class="bookmark-btn ${saved ? "saved" : ""}" data-bookmark="${esc(job.id)}" aria-label="Save job" title="Save job">${saved ? "★" : "☆"}</button>
    </div>
    <div class="job-meta">
      ${job.region ? `<span class="badge region">${regionEmoji(job)}</span>` : ""}
      <span class="badge">📍 ${esc(job.location || "USA")}</span>
      ${job.remote ? '<span class="badge remote">🌐 Remote</span>' : ""}
      ${job.type ? `<span class="badge">${esc(job.type)}</span>` : ""}
    </div>
    ${job.salary ? `<div class="job-meta"><span class="badge salary">💰 ${esc(job.salary)}</span></div>` : ""}
    ${job.tags && job.tags.length ? `<div class="job-tags">${job.tags.slice(0, 3).map((t) => `<span class="job-tag">${esc(t)}</span>`).join("")}</div>` : ""}
    <div class="job-foot">
      <span class="job-source-line"><span class="posted-age">${timeAgo(job.date)}</span>${sourceAttribution(job)}</span>
      <a class="apply" href="${esc(job.url)}" target="_blank" rel="noopener noreferrer">Apply <span>→</span></a>
    </div>
  </article>`;
}

function renderSkeletons(n = 6) {
  const grid = $("#grid");
  if (grid) grid.innerHTML = Array.from({ length: n }, () =>
    `<div class="skel"><div class="l w60"></div><div class="l w80"></div><div class="l w40"></div></div>`).join("");
}

function renderHome() {
  const f = state.filters;
  const list = visibleJobs();
  const shown = list.slice(0, state.visible);

  $("#resultCount").textContent = `${list.length} job${list.length === 1 ? "" : "s"}${f.q || f.cat !== "All" || f.loc ? " found" : " available"}`;
  $("#grid").innerHTML = shown.length
    ? shown.map(cardHtml).join("")
    : `<div class="empty"><h3>No jobs match your filters</h3><p>Try clearing the search or filters.</p><button class="btn ghost" id="resetBtn">Reset filters</button></div>`;
  const lb = $("#loadMoreWrap");
  lb.classList.toggle("hidden", list.length <= shown.length);
  $("#loadMoreBtn").textContent = `Show more (${list.length - shown.length} left)`;

  // category chips with counts
  const counts = {};
  state.jobs.forEach((j) => { counts[j.category] = (counts[j.category] || 0) + 1; });
  const cats = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  $("#catChips").innerHTML =
    `<button class="cat-chip ${f.cat === "All" ? "active" : ""}" data-cat="All">All (${state.jobs.length})</button>` +
    cats.map(([c, n]) => `<button class="cat-chip ${f.cat === c ? "active" : ""}" data-cat="${esc(c)}">${esc(c)} (${n})</button>`).join("");

  // country select
  const cc = {};
  state.jobs.forEach((j) => { const k = j.country || "WW"; cc[k] = (cc[k] || 0) + 1; });
  const cNames = Object.keys(cc).filter((k) => k !== "WW").sort((a, b) => cc[b] - cc[a]);
  $("#filterCountry").innerHTML =
    `<option value="All">All countries (${state.jobs.length})</option>` +
    cNames.map((n) => `<option value="${esc(n)}">${esc(n)} (${cc[n]})</option>`).join("") +
    (cc.WW ? `<option value="WW">🌍 Worldwide / Remote (${cc.WW})</option>` : "");
  $("#filterCountry").value = f.country;

  // stats
  $("#statTotal").textContent = state.jobs.length.toLocaleString();
  $("#statNew").textContent = "24h"; // placeholder, updated below
  const dayAgo = Date.now() - 86400000;
  $("#statNew").textContent = state.jobs.filter((j) => new Date(j.date) > dayAgo).length;
  $("#statSources").textContent = new Set(state.jobs.map((j) => j.source).filter(Boolean)).size || SOURCES.length;
  $("#statSalary").textContent = state.jobs.filter((j) => j.salary).length;

  injectFeedAds();
}

function updateSyncPills() {
  const wrap = $("#syncStatus");
  if (!wrap) return;
  // مصدر Adzuna يأتي في السناپشوت اليومي (وليس من المتصفح) — نعرضه من بيانات الحالة
  const snapCounts = {};
  state.jobs.forEach((j) => { snapCounts[j.source] = (snapCounts[j.source] || 0) + 1; });
  const names = SOURCES.map((s) => s.name);
  Object.keys(snapCounts).forEach((n) => { if (!names.includes(n)) names.push(n); });
  wrap.innerHTML = names.map((name) => {
    const st = state.sourceStatus[name];
    const count = st ? st.count : snapCounts[name] || 0;
    const cls = st ? (st.ok ? "ok" : "err") : "ok";
    return `<span class="src-pill ${cls}"><span class="dot"></span>${esc(name)} <b>${count}</b></span>`;
  }).join("");
}

let adsLoaded = false;
function adsenseConfigured() {
  return CONFIG.adsenseClient.startsWith("ca-pub-") && !CONFIG.adsenseClient.includes("XXXX");
}
function adsenseActive() {
  return adsenseConfigured() && !!(window.WintConsent && window.WintConsent.allows("advertising"));
}
function loadAdsense() {
  if (!adsenseActive() || adsLoaded || window.adsbygoogle) return;
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
  if (!adsenseActive()) {
    // Keep unconfigured ad placements completely invisible to visitors and reviewers.
    div.classList.add("hidden");
    div.setAttribute("aria-hidden", "true");
    return div;
  }
  div.innerHTML = `<div class="ad-label">${esc(label)}</div><ins class="adsbygoogle" style="display:block" data-ad-client="${esc(CONFIG.adsenseClient)}" data-ad-slot="${esc(slot)}" data-ad-format="auto" data-full-width-responsive="true"></ins>`;
  return div;
}
function injectFeedAds() {
  loadAdsense();
  const grid = $("#grid");
  if (!grid) return;
  $$(".ad-slot", grid).forEach((el) => el.remove());
  const cards = $$(".job-card", grid);
  if (cards.length >= 6) {
    const slot = CONFIG.adSlots.feed;
    const anchor = cards[Math.min(6, cards.length - 1)];
    anchor.after(adEl(slot));
    if (adsenseActive()) try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch {}
  }
  const top = $("#adTop");
  if (top) {
    top.innerHTML = "";
    top.append(adEl(CONFIG.adSlots.top));
  }
}

/* ---------------- detail view ---------------- */
function relatedJobs(job, n = 4) {
  return state.jobs.filter((j) => j.category === job.category && j.id !== job.id).slice(0, n);
}

function renderDetail(job, scroll = true) {
  if (!job) { location.hash = ""; return; }
  document.title = `${job.title} at ${job.company} | ${CONFIG.siteName}`;
  $("#detailTitle").innerHTML = esc(job.title);
  $("#detailCompany").textContent = job.company;
  $("#detailLogo").innerHTML = logoHtml(job, 64);
  $("#detailMeta").innerHTML = `
    <span class="badge">📍 ${esc(job.location || "USA")}</span>
    ${job.remote ? '<span class="badge remote">🌐 Remote</span>' : ""}
    ${job.type ? `<span class="badge">${esc(job.type)}</span>` : ""}
    <span class="badge">${timeAgo(job.date)}</span>
    ${sourceAttribution(job)}`;
  $("#detailSalary").textContent = job.salary || "Not specified";
  $("#detailBody").innerHTML = sanitizeHtml(job.description) || "<p><em>Full description available on the employer's page.</em></p>";
  $("#applyNowBtn").href = job.url;
  $("#applyNowBtn").dataset.url = job.url;
  $("#detailSaveBtn").innerHTML = (state.bookmarks.has(job.id) ? "★ Saved" : "☆ Save job");
  $("#detailSaveBtn").onclick = () => { toggleBookmark(job.id); renderDetail(job); };

  // facts
  $("#factCompany").textContent = job.company;
  $("#factLocation").textContent = job.location || "USA";
  $("#factType").textContent = job.type || (job.remote ? "Remote" : "—");
  $("#factDate").textContent = new Date(job.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  $("#factCategory").textContent = job.category;
  const fc = $("#factCountry");
  if (fc) fc.textContent = job.country || (job.region === "WW" ? "Worldwide / Remote" : "—");

  const rel = relatedJobs(job);
  $("#relatedTitle").classList.toggle("hidden", !rel.length);
  $("#relatedGrid").innerHTML = rel.map(cardHtml).join("");

  // ads in detail
  const adBox = $("#detailAd");
  adBox.innerHTML = "";
  adBox.append(adEl(CONFIG.adSlots.detail));
  try { if (adsenseActive()) (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch {}

  $("#viewHome").classList.add("hidden");
  $("#viewDetail").classList.remove("hidden");
  if (scroll) window.scrollTo({ top: 0 });
}

function showHomeView(scroll = true) {
  $("#viewDetail").classList.add("hidden");
  $("#viewHome").classList.remove("hidden");
  document.title = `${CONFIG.siteName} — Jobs in the USA & Europe | Auto-Updated Job Board`;
  if (scroll) window.scrollTo({ top: 0 });
}

function renderAll() {
  updateSyncPills();
  renderHome();
  const m = location.hash.match(/^#\/job\/(.+)$/);
  if (m) {
    const job = state.jobs.find((j) => j.id === decodeURIComponent(m[1]));
    if (job) renderDetail(job, false);
  }
}

/* ============================ ROUTER ============================ */
function route() {
  const m = location.hash.match(/^#\/job\/(.+)$/);
  if (m) {
    const id = decodeURIComponent(m[1]);
    const job = state.jobs.find((j) => j.id === id);
    if (job) renderDetail(job, false);
    else showHomeView(false);
  } else {
    showHomeView(false);
  }
}

/* ============================ INTERACTIONS ============================ */
function toggleBookmark(id) {
  if (state.bookmarks.has(id)) state.bookmarks.delete(id);
  else state.bookmarks.add(id);
  store.set("ww:bookmarks", [...state.bookmarks]);
  const card = $(`[data-id="${CSS.escape(id)}"] .bookmark-btn`);
  if (card) { card.classList.toggle("saved", state.bookmarks.has(id)); card.textContent = state.bookmarks.has(id) ? "★" : "☆"; }
  $("#savedCount").textContent = state.bookmarks.size;
}

function applyFilters() {
  renderHome();
}

function bindEvents() {
  // search
  let debounce;
  $("#searchInput").addEventListener("input", (e) => {
    clearTimeout(debounce);
    debounce = setTimeout(() => { state.filters.q = e.target.value.trim(); state.visible = 24; applyFilters(); }, 250);
  });
  $("#filterRegion").addEventListener("change", (e) => {
    state.filters.region = e.target.value; state.visible = 24; applyFilters();
  });
  $("#filterCountry").addEventListener("change", (e) => {
    state.filters.country = e.target.value; state.visible = 24; applyFilters();
  });
  $("#filterLoc").addEventListener("input", (e) => {
    state.filters.loc = e.target.value.trim(); state.visible = 24; applyFilters();
  });
  $("#filterCat").addEventListener("change", (e) => {
    state.filters.cat = e.target.value; state.visible = 24; applyFilters();
  });
  $("#filterSort").addEventListener("change", (e) => {
    state.filters.sort = e.target.value; state.visible = 24; applyFilters();
  });
  $("#filterRemote").addEventListener("change", (e) => {
    state.filters.remoteOnly = e.target.checked; state.visible = 24; applyFilters();
  });
  $("#filterSaved").addEventListener("change", (e) => {
    state.filters.savedOnly = e.target.checked; applyFilters();
  });
  $("#resetFilters").addEventListener("click", () => {
    state.filters = { q: "", cat: "All", region: "All", country: "All", loc: "", remoteOnly: false, savedOnly: false, sort: "new" };
    $("#searchInput").value = ""; $("#filterLoc").value = ""; $("#filterCat").value = "All";
    $("#filterRegion").value = "All"; $("#filterCountry").value = "All";
    $("#filterSort").value = "new"; $("#filterRemote").checked = false; $("#filterSaved").checked = false;
    state.visible = 24;
    applyFilters();
  });

  // category chips (delegated)
  $("#catChips").addEventListener("click", (e) => {
    const btn = e.target.closest(".cat-chip");
    if (!btn) return;
    state.filters.cat = btn.dataset.cat;
    $("#filterCat").value = state.filters.cat;
    state.visible = 24;
    applyFilters();
  });

  // quick chips in hero
  $$(".quick-chip").forEach((btn) => btn.addEventListener("click", () => {
    const cat = btn.dataset.quick;
    const isCountry = btn.dataset.quickType === "country";
    state.filters.remoteOnly = false; $("#filterRemote").checked = false;
    if (cat === "Remote") {
      state.filters.remoteOnly = true; $("#filterRemote").checked = true;
    } else if (isCountry) {
      state.filters.region = "All"; $("#filterRegion").value = "All";
      state.filters.country = cat; $("#filterCountry").value = cat;
    } else if (cat === "US" || cat === "EU" || cat === "WW") {
      state.filters.country = "All"; $("#filterCountry").value = "All";
      state.filters.region = cat; $("#filterRegion").value = cat;
    } else {
      state.filters.country = "All"; $("#filterCountry").value = "All";
      state.filters.region = "All"; $("#filterRegion").value = "All";
      state.filters.cat = cat; $("#filterCat").value = cat;
    }
    state.visible = 24;
    applyFilters();
    $("#jobs").scrollIntoView({ behavior: "smooth" });
  }));

  // load more
  $("#loadMoreBtn").addEventListener("click", () => {
    state.visible += 24;
    renderHome();
  });

  // grid clicks (delegated): bookmark + reset empty state
  $("#grid").addEventListener("click", (e) => {
    const b = e.target.closest("[data-bookmark]");
    if (b) { e.preventDefault(); toggleBookmark(b.dataset.bookmark); return; }
    if (e.target.id === "resetBtn") {
      state.filters = { q: "", cat: "All", region: "All", country: "All", loc: "", remoteOnly: false, savedOnly: false, sort: "new" };
      applyFilters();
    }
  });

  // detail: share + copy
  $("#shareCopyBtn").addEventListener("click", () => {
    const url = $("#applyNowBtn") ? location.href : "";
    if (navigator.clipboard) navigator.clipboard.writeText(location.href).then(() => toast("Link copied to clipboard"));
    else toast("Copy the URL from the address bar");
  });
  $("#shareXBtn").addEventListener("click", () => {
    const t = encodeURIComponent(document.title);
    window.open(`https://twitter.com/intent/tweet?text=${t}&url=${encodeURIComponent(location.href)}`, "_blank", "noopener");
  });
  $("#shareFBBtn").addEventListener("click", () => {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(location.href)}`, "_blank", "noopener");
  });

  // saved button → toggles saved filter & scrolls to jobs
  $("#savedBtn").addEventListener("click", () => {
    state.filters.savedOnly = !state.filters.savedOnly;
    $("#filterSaved").checked = state.filters.savedOnly;
    applyFilters();
    $("#jobs").scrollIntoView({ behavior: "smooth" });
  });

  // theme toggle
  $("#themeBtn").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    store.set("ww:theme", next);
  });

  // mobile nav
  $("#navToggle").addEventListener("click", () => $("#mainNav").classList.toggle("open"));

  // router
  window.addEventListener("hashchange", route);

  // Load advertising only after an explicit advertising-storage choice.
  window.addEventListener("wintworks:consentchange", (event) => {
    if (event.detail && event.detail.advertising) renderAll();
  });

  // auto refresh (set & forget)
  setInterval(() => { if (!document.hidden) refreshLive(); }, CONFIG.refreshMinutes * 60000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && state.lastLive && Date.now() - state.lastLive > 10 * 60000) refreshLive();
  });
}

function initTheme() {
  // الوضع الافتراضي = فاتح. الداكن فقط إذا اختاره المستخدم بنفسه.
  const saved = store.get("ww:theme", null);
  if (saved === "dark") document.documentElement.dataset.theme = "dark";
  else document.documentElement.dataset.theme = "light";
}

/* ===================== URL FILTER PARAMS (SEO landing) ===================== */
function applyUrlParams() {
  const p = new URLSearchParams(location.search);
  let applied = false;
  if (p.has("q")) { state.filters.q = p.get("q").trim(); $("#searchInput").value = state.filters.q; applied = true; }
  if (p.has("cat")) { state.filters.cat = p.get("cat"); $("#filterCat").value = state.filters.cat; applied = true; }
  if (p.has("region")) { state.filters.region = p.get("region"); $("#filterRegion").value = state.filters.region; applied = true; }
  if (p.has("country")) { state.filters.country = p.get("country"); applied = true; }
  if (p.get("remote") === "1") { state.filters.remoteOnly = true; $("#filterRemote").checked = true; applied = true; }
  if (p.get("saved") === "1") { state.filters.savedOnly = true; $("#filterSaved").checked = true; applied = true; }
  if (applied) state.urlFiltered = true;
  return applied;
}

/* ============================ BOOT ============================ */
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  bindEvents();
  applyUrlParams();
  $("#savedCount").textContent = state.bookmarks.size;
  $("#year").textContent = new Date().getFullYear();
  updateSyncPills();
  renderSkeletons();
  load();
});
