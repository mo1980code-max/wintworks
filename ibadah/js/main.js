/* ============================================================
   Ibadah — Main site JS (vanilla JS, no jQuery)
   Hero slider · Prayer strip · Countdowns · Projects
   Event schedule · Speaker bio · Reveal · Forms
   ============================================================ */

(function () {
  "use strict";

  var DATA = window.getSiteData ? window.getSiteData() : window.IBADAH_DEFAULTS;
  var state = {
    cityId: (window.IBADAH_STORE ? window.IBADAH_STORE.get("ibadah-city") : localStorage.getItem("ibadah-city")) || DATA.prayerSettings.defaultCityId,
    method: (window.IBADAH_STORE ? window.IBADAH_STORE.get("ibadah-method") : localStorage.getItem("ibadah-method")) || DATA.prayerSettings.method,
    madhab: (window.IBADAH_STORE ? window.IBADAH_STORE.get("ibadah-madhab") : localStorage.getItem("ibadah-madhab")) || DATA.prayerSettings.asrMadhab,
    times: null
  };

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  /* ---------------- Toast ---------------- */
  function toast(message, type) {
    var zone = $("#toastZone");
    if (!zone) {
      zone = document.createElement("div");
      zone.id = "toastZone";
      zone.className = "toast-zone";
      document.body.appendChild(zone);
    }
    var el = document.createElement("div");
    el.className = "toast align-items-center text-bg-" + (type === "error" ? "danger" : "success") + " border-0";
    el.setAttribute("role", "alert");
    el.innerHTML = '<div class="d-flex"><div class="toast-body fw-semibold">' + message +
      '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    zone.appendChild(el);
    var t = new bootstrap.Toast(el, { delay: 4200 });
    t.show();
    el.addEventListener("hidden.bs.toast", function () { el.remove(); });
  }

  /* ---------------- Bind texts from data ---------------- */
  function applyTexts() {
    $$("[data-bind]").forEach(function (el) {
      var path = el.getAttribute("data-bind").split(".");
      var value = DATA;
      for (var i = 0; i < path.length; i++) {
        if (value === null || value === undefined) break;
        value = value[path[i]];
      }
      if (value !== null && value !== undefined) {
        if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") el.value = value;
        else el.textContent = value;
      }
    });
  }

  /* ---------------- Navbar ---------------- */
  function initNav() {
    var nav = $(".main-navbar");
    if (!nav) return;
    window.addEventListener("scroll", function () {
      nav.classList.toggle("scrolled", window.scrollY > 60);
    }, { passive: true });

    var links = $$(".navbar .nav-link[href^='#']");
    if (links.length) {
      var sections = links.map(function (l) { return $(l.getAttribute("href")); }).filter(Boolean);
      window.addEventListener("scroll", function () {
        var pos = window.scrollY + 140;
        var current = null;
        sections.forEach(function (s, i) { if (s.offsetTop <= pos) current = links[i]; });
        links.forEach(function (l) { l.classList.remove("active"); });
        if (current) current.classList.add("active");
      }, { passive: true });
    }
  }

  /* ---------------- Hero slider ---------------- */
  function initHero() {
    var hero = $("#heroSlider");
    if (!hero) return;
    var slides = $$(".hero-slide", hero);
    var dotsWrap = $(".hero-dots", hero);
    var idx = 0, timer = null;

    slides.forEach(function (s, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", "Slide " + (i + 1));
      if (i === 0) b.classList.add("active");
      b.addEventListener("click", function () { go(i); restart(); });
      dotsWrap.appendChild(b);
    });
    var dots = $$("button", dotsWrap);

    function go(i) {
      slides[idx].classList.remove("active");
      dots[idx].classList.remove("active");
      idx = (i + slides.length) % slides.length;
      slides[idx].classList.add("active");
      dots[idx].classList.add("active");
    }
    function restart() { clearInterval(timer); timer = setInterval(function () { go(idx + 1); }, 6500); }

    var prevBtn = $(".hero-arrows .prev", hero);
    var nextBtn = $(".hero-arrows .next", hero);
    if (prevBtn) prevBtn.addEventListener("click", function () { go(idx - 1); restart(); });
    if (nextBtn) nextBtn.addEventListener("click", function () { go(idx + 1); restart(); });
    restart();
  }

  /* ---------------- Prayer helpers ---------------- */
  function getSettings() {
    return { method: state.method, asrMadhab: state.madhab, iqamaOffsets: DATA.prayerSettings.iqamaOffsets };
  }
  function getCity() {
    var city = null;
    DATA.cities.forEach(function (c) { if (c.id === state.cityId) city = c; });
    return city || DATA.cities[0];
  }
  function computeTimes() {
    var now = new Date();
    var city = getCity();
    state.times = PrayerCalc.getTimes(now, city, getSettings());
    state.city = city;
    state.now = now;
  }
  function iqamaFor(key, time) {
    if (!time) return null;
    var off = DATA.prayerSettings.iqamaOffsets[key] || 0;
    if (key === "Maghrib") return time;
    var mins = time.hour * 60 + time.minute + off;
    return { hour: Math.floor((mins / 60) % 24), minute: mins % 60 };
  }

  /* Home prayer strip */
  function renderPrayerStrip() {
    var wrap = $("#prayerStrip");
    if (!wrap) return;
    computeTimes();
    var names = [
      { key: "Fajr", label: "Fajr", icon: "fa-cloud-moon" },
      { key: "Dhuhr", label: "Dhuhr", icon: "fa-sun" },
      { key: "Asr", label: "Asr", icon: "fa-cloud-sun" },
      { key: "Maghrib", label: "Maghrib", icon: "fa-umbrella-beach" },
      { key: "Isha", label: "Isha", icon: "fa-moon" },
      { key: "Jumuah", label: "Jumu'ah", icon: "fa-mosque", custom: true }
    ];
    var html = '<div class="row g-3">';
    names.forEach(function (n) {
      var t = n.custom ? null : state.times[n.key.charAt(0).toLowerCase() + n.key.slice(1)];
      var iq = n.custom ? null : iqamaFor(n.key, t);
      var timeStr = n.custom ? "12:30 PM" : PrayerCalc.format12(t || { hour: 0, minute: 0 });
      html += '<div class="col-6 col-md-4 col-lg-2">' +
        '<div class="prayer-card" id="prayerCard-' + n.key + '">' +
        '<div class="prayer-icon"><i class="fa-solid ' + n.icon + '"></i></div>' +
        '<div class="prayer-name">' + n.label + '</div>' +
        '<div class="prayer-time">' + timeStr + '</div>' +
        '<div class="prayer-iqama">' + (n.custom ? "Khutbah: 1:15 PM" : "Iqamah: " + (iq ? PrayerCalc.format12(iq) : "--:--")) + '</div>' +
        '</div></div>';
    });
    html += '</div>';
    wrap.innerHTML = html;

    /* Highlight current prayer */
    var names2 = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];
    var cur = null, nextKey = null, nextTime = null;
    names2.forEach(function (k) {
      var t = state.times[k.charAt(0).toLowerCase() + k.slice(1)];
      if (t) {
        var mins = t.hour * 60 + t.minute;
        var nowMins = state.now.getHours() * 60 + state.now.getMinutes();
        if (mins <= nowMins) cur = k;
        else if (!nextTime || mins < nextTime) { nextKey = k; nextTime = mins; }
      }
    });
    if (!nextKey) nextKey = names2[0];
    $$(".prayer-card").forEach(function (card) {
      card.classList.toggle("current", card.id.replace("prayerCard-", "") === cur);
    });
    var note = $("#nextPrayerNote");
    if (note && nextKey) note.innerHTML = '<i class="fa-solid fa-clock"></i> Next prayer: <strong>' + nextKey + '</strong>';
  }

  function startTicker() {
    computeTimes();
    renderPrayerStrip();
    setInterval(function () { computeTimes(); renderPrayerStrip(); }, 60000);
  }

  /* ---------------- Countdown ---------------- */
  function initCountdown() {
    var box = $("#countdown") || $("#eventCountdown");
    if (!box) return;
    var target = new Date(box.getAttribute("data-target")).getTime();
    var timer;
    function pad(n) { return String(n).padStart(2, "0"); }
    function tick() {
      var diff = Math.max(0, target - Date.now());
      var d = Math.floor(diff / 86400000);
      var h = Math.floor((diff % 86400000) / 3600000);
      var m = Math.floor((diff % 3600000) / 60000);
      var s = Math.floor((diff % 60000) / 1000);
      box.innerHTML =
        '<div class="cd-box"><div class="cd-num">' + pad(d) + '</div><div class="cd-label">Days</div></div>' +
        '<div class="cd-box"><div class="cd-num">' + pad(h) + '</div><div class="cd-label">Hours</div></div>' +
        '<div class="cd-box"><div class="cd-num">' + pad(m) + '</div><div class="cd-label">Min</div></div>' +
        '<div class="cd-box"><div class="cd-num">' + pad(s) + '</div><div class="cd-label">Sec</div></div>';
      if (diff <= 0) clearInterval(timer);
    }
    tick();
    timer = setInterval(tick, 1000);
  }

  /* ---------------- Reveal on scroll ---------------- */
  function initReveal() {
    var items = $$("[data-reveal]");
    if (!("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("revealed"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("revealed"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ---------------- Counters ---------------- */
  function initCounters() {
    var nums = $$(".fact-num[data-count]");
    if (!nums.length) return;
    if (!("IntersectionObserver" in window)) {
      nums.forEach(function (el) {
        var target = parseInt(el.getAttribute("data-count"), 10);
        var suffix = el.getAttribute("data-suffix") || "";
        el.textContent = target.toLocaleString("en-US") + suffix;
      });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        var target = parseInt(el.getAttribute("data-count"), 10);
        var suffix = el.getAttribute("data-suffix") || "";
        var start = null, dur = 1800;
        function step(ts) {
          if (!start) start = ts;
          var p = Math.min(1, (ts - start) / dur);
          el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3))).toLocaleString("en-US") + suffix;
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
        io.unobserve(el);
      });
    }, { threshold: 0.5 });
    nums.forEach(function (el) { io.observe(el); });
  }

  /* ---------------- Ayat slider (Arabic + English) ---------------- */
  function initAyat() {
    var wrap = $("#ayatSlider");
    if (!wrap) return;
    var html = "";
    DATA.ayat.forEach(function (a, i) {
      html += '<div class="carousel-item' + (i === 0 ? " active" : "") + '">' +
        '<i class="fa-solid fa-quote-right ayat-quote"></i>' +
        '<p class="ayat-text">' + a.text + '</p>' +
        '<p class="ayat-ref fst-italic">“' + a.translation + '”</p>' +
        '<p class="ayat-ref"><span class="text-gold fw-bold">' + a.ref + '</span></p></div>';
    });
    wrap.innerHTML = html;
    var carousel = new bootstrap.Carousel(wrap, { interval: 7000, ride: "carousel" });
    var prev = $("#ayatPrev"), next = $("#ayatNext");
    if (prev) prev.addEventListener("click", function () { carousel.prev(); });
    if (next) next.addEventListener("click", function () { carousel.next(); });
  }

  /* ---------------- Courses ---------------- */
  function renderCourses() {
    var grid = $("#courseGrid");
    if (!grid) return;
    var html = "";
    DATA.courses.forEach(function (c) {
      html += '<div class="col-md-6 col-lg-3" data-reveal>' +
        '<div class="card-soft course-card h-100 p-0 overflow-hidden">' +
        '<div class="course-img"><img src="' + c.img + '" alt="' + c.title + '" class="img-cover"></div>' +
        '<div class="p-4" style="padding-top:26px !important">' +
        '<div class="scholar-chip mb-3">' +
        '<span class="icon-chip" style="width:44px;height:44px;border-radius:50%;font-size:1rem;flex:none"><i class="fa-solid fa-user-tie"></i></span>' +
        '<div><div class="fw-bold text-green">' + c.teacher + '</div>' +
        '<div class="small text-muted">' + c.teacherRole + '</div></div></div>' +
        '<div class="course-price">$' + c.price + (c.priceFree ? ' <span class="small">(Free)</span>' : '') + '</div>' +
        '<h5 class="fw-bold text-green mt-4 mb-2"><a class="stretched-link text-green" href="courses.html?c=' + c.id + '">' + c.title + '</a></h5>' +
        '<p class="text-muted small mb-3">' + c.desc + '</p>' +
        '<div class="course-meta d-flex gap-3 flex-wrap small">' +
        '<span class="badge"><i class="fa-regular fa-calendar me-1"></i>' + c.weeks + ' weeks</span>' +
        '<span class="badge"><i class="fa-solid fa-users me-1"></i>' + c.enroll + ' enrolled</span></div>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- Causes ---------------- */
  function renderCauses() {
    var grid = $("#causeGrid");
    if (!grid) return;
    var html = "";
    DATA.causes.forEach(function (c) {
      var pct = Math.min(100, Math.round((c.raised / c.goal) * 100));
      var left = Math.max(0, c.goal - c.raised);
      html += '<div class="col-md-6 col-lg-4" data-reveal>' +
        '<div class="card-soft cause-card h-100 p-0 overflow-hidden">' +
        '<div class="cause-img"><img src="' + c.img + '" alt="' + c.title + '" class="img-cover">' +
        '<span class="cause-cat">' + c.category + '</span></div>' +
        '<div class="p-4">' +
        '<h5 class="fw-bold text-green"><a class="stretched-link text-green" href="donate.html#cause-' + c.id + '">' + c.title + '</a></h5>' +
        '<p class="text-muted small">' + c.desc + '</p>' +
        '<div class="d-flex justify-content-between small fw-bold mb-1">' +
        '<span class="text-gold">' + pct + '%</span><span class="text-muted">' + (c.raised / c.goal * 100).toFixed(1) + '%</span></div>' +
        '<div class="cause-progress mb-3"><div class="bar" style="width:' + pct + '%"></div></div>' +
        '<div class="d-flex justify-content-between small">' +
        '<span><i class="fa-solid fa-hand-holding-heart text-gold me-1"></i>Left: <strong class="text-green">$' + left.toLocaleString("en-US") + '</strong></span>' +
        '<a href="donate.html#cause-' + c.id + '" class="fw-bold text-green">Donate <i class="fa-solid fa-arrow-right"></i></a></div>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- Events cards ---------------- */
  function renderEvents() {
    var grid = $("#eventGrid");
    if (!grid) return;
    var html = "";
    DATA.events.forEach(function (ev) {
      var d = new Date(ev.date);
      var mon = d.toLocaleDateString("en-US", { month: "short" });
      html += '<div class="col-md-6 col-lg-4" data-reveal>' +
        '<div class="card-soft event-card h-100 p-0 overflow-hidden">' +
        '<div class="event-img"><img src="' + ev.image + '" alt="' + ev.title + '" class="img-cover">' +
        '<div class="event-date-badge"><div class="d">' + d.getDate() + '</div><div class="m">' + mon + '</div></div></div>' +
        '<div class="p-4">' +
        '<span class="badge text-bg-light border mb-2 fw-bold text-gold">' + ev.category + '</span>' +
        '<h5 class="fw-bold text-green"><a class="stretched-link text-green" href="event.html?id=' + ev.id + '">' + ev.title + '</a></h5>' +
        '<div class="event-meta my-3">' +
        '<span><i class="fa-regular fa-clock me-1"></i>' + d.toLocaleDateString("en-US", { day: "numeric", month: "long", year: "numeric" }) + '</span>' +
        '<span><i class="fa-solid fa-location-dot me-1"></i>' + ev.location + '</span></div>' +
        '<p class="text-muted small mb-3">' + ev.desc + '</p>' +
        '<a href="event.html?id=' + ev.id + '" class="fw-bold text-green">Details <i class="fa-solid fa-arrow-right"></i></a>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- Event schedule table ---------------- */
  function renderEventSchedule() {
    var tbody = $("#scheduleTableBody");
    if (!tbody) return;
    var rows = DATA.events.slice().sort(function (a, b) { return new Date(a.date) - new Date(b.date); });
    var html = "";
    rows.forEach(function (ev) {
      var d = new Date(ev.date);
      var past = d.getTime() < Date.now();
      html += '<tr>' +
        '<td class="date-cell">' + d.toLocaleDateString("en-US", { weekday: "short", day: "numeric", month: "short", year: "numeric" }) + '</td>' +
        '<td class="fw-semibold">' + d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" }) + '</td>' +
        '<td><strong class="text-green">' + ev.title + '</strong><div class="small text-muted">' + ev.category + '</div></td>' +
        '<td class="small text-muted">' + ev.location + '</td>' +
        '<td><span class="badge ' + (past ? "text-bg-secondary" : "text-bg-success") + '">' + (past ? "Completed" : "Upcoming") + '</span></td>' +
        '<td><a href="event.html?id=' + ev.id + '" class="btn btn-sm btn-outline-green">View</a></td></tr>';
    });
    tbody.innerHTML = html;
  }

  /* ---------------- Latest projects ---------------- */
  function renderProjects() {
    var grid = $("#projectGrid");
    if (!grid) return;
    var html = "";
    DATA.projects.forEach(function (p) {
      var statusLabel = p.status === "completed" ? "Completed" : p.status === "in-progress" ? "In Progress" : "Planned";
      html += '<div class="col-md-6 col-lg-3" data-reveal>' +
        '<div class="card-soft project-card h-100 p-0 overflow-hidden">' +
        '<div class="project-img"><img src="' + p.img + '" alt="' + p.title + '" class="img-cover">' +
        '<span class="project-status ' + p.status + '">' + statusLabel + '</span></div>' +
        '<div class="p-4">' +
        '<div class="project-meta mb-2"><i class="fa-regular fa-calendar me-1"></i>' + p.year + ' · ' + p.category + '</div>' +
        '<h5 class="fw-bold text-green">' + p.title + '</h5>' +
        '<p class="text-muted small mb-3">' + p.desc + '</p>' +
        '<div class="d-flex justify-content-between small fw-bold mb-1"><span class="text-gold">' + p.progress + '%</span><span class="text-muted">Progress</span></div>' +
        '<div class="cause-progress"><div class="bar" style="width:' + p.progress + '%"></div></div>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- Quran player (all 114 surahs + reciter switch) ---------------- */
  function initQuranAudio() {
    var player = $("#quranAudio");
    var list = $("#surahList");
    var select = $("#quranReciter");
    var title = $("#surahTitle");
    if (!player || !list) return;

    var Q = window.IBADAH_QURAN || [];
    var reciters = (DATA.reciters && DATA.reciters.length) ? DATA.reciters : [{ id: "ar.alafasy", name: "Mishary Rashid Alafasy" }];
    var reciterId = reciters[0].id;
    if (select && !select.options.length) {
      reciters.forEach(function (r) {
        var o = document.createElement("option");
        o.value = r.id; o.textContent = r.name;
        select.appendChild(o);
      });
    }
    if (select) select.addEventListener("change", function () {
      reciterId = select.value;
      var cur = parseInt(player.getAttribute("data-surah") || "1", 10);
      if (cur) load(cur);
    });

    function surahName(n) {
      var s = Q[n - 1];
      return s ? (s.t || "Surah " + n) : ("Surah " + n);
    }

    /* Full 114 list (scrollable) */
    var html = "";
    (Q.length ? Q : []).slice(0, 114).forEach(function (s, i) {
      var n = s.id || (i + 1);
      html += '<button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center surah-item' +
        (n === 1 ? " active" : "") + '" data-n="' + n + '" data-name="' + surahName(n) + '">' +
        '<span><i class="fa-solid fa-book-quran text-gold me-2"></i><strong>' + surahName(n) + '</strong>' +
        '<span class="d-block small text-muted">' + s.v.length + ' verses</span></span>' +
        '<i class="fa-solid fa-play-circle fs-4 text-gold"></i></button>';
    });
    list.innerHTML = html;

    var audio = player;
    var items = $$(".surah-item", list);

    function load(n) {
      audio.src = "https://cdn.islamic.network/quran/audio-surah/128/" + reciterId + "/" + n + ".mp3";
      audio.load();
      audio.setAttribute("data-surah", n);
      if (title) title.textContent = "Surah " + surahName(n);
      items.forEach(function (it) {
        it.classList.toggle("active", parseInt(it.getAttribute("data-n"), 10) === n);
      });
    }

    items.forEach(function (it) {
      it.addEventListener("click", function () {
        load(parseInt(it.getAttribute("data-n"), 10));
        audio.play().catch(function () { toast("Audio could not start — check your connection", "error"); });
      });
    });

    audio.addEventListener("error", function () {
      if (audio.src) toast("Could not load recitation — check your internet connection", "error");
    });

    load(1);
  }

  /* ---------------- Media embeds (YouTube / Vimeo / SoundCloud) ---------------- */
  function mediaUrl(m) {
    var u = (m.url || m.embedUrl || "").trim();
    if (!u) return "";
    if (m.type === "youtube") {
      var m1 = u.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{6,})/);
      if (m1) return "https://www.youtube-nocookie.com/embed/" + m1[1];
      if (u.indexOf("youtube") !== -1 || u.indexOf("youtu.be") !== -1) return u;
      return "";
    }
    if (m.type === "vimeo") {
      var m2 = u.match(/vimeo\.com\/(?:video\/)?(\d+)/);
      if (m2) return "https://player.vimeo.com/video/" + m2[1];
      return "";
    }
    if (m.type === "soundcloud") {
      if (u.indexOf("w.soundcloud.com/player") !== -1) return u;
      if (u.indexOf("soundcloud.com") !== -1) return "https://w.soundcloud.com/player/?url=" + encodeURIComponent(u) + "&color=%23c9a227&auto_play=false&hide_related=true&show_comments=false";
      return "";
    }
    return u;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function renderMedia() {
    var items = (DATA.media && DATA.media.length) ? DATA.media : [];
    var buckets = { youtube: [], vimeo: [], soundcloud: [] };
    items.forEach(function (m) {
      var src = mediaUrl(m);
      if (!src) return;
      (buckets[m.type] || buckets.youtube).push({ m: m, src: src });
    });
    var targets = { youtube: $("#mediaEmbeds-youtube"), vimeo: $("#mediaEmbeds-vimeo"), soundcloud: $("#mediaEmbeds-soundcloud"), all: $("#mediaEmbeds") };
    Object.keys(buckets).forEach(function (type) {
      var wrap = targets[type] || targets.all;
      if (!wrap) return;
      var html = "";
      buckets[type].forEach(function (item) {
        var m = item.m, src = item.src;
        var title = m.title || m.type + " embed";
        var cls = m.type === "soundcloud" ? "media-embed soundcloud" : "media-embed";
        var allow = m.type === "youtube"
          ? "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          : "autoplay; fullscreen; picture-in-picture";
        html += '<div class="col-md-6 media-card" data-reveal>' +
          '<div class="card-soft p-2 h-100">' +
            '<h3 class="h5 fw-bold text-green px-2 pt-2">' + escapeHtml(title) + '</h3>' +
            '<div class="' + cls + '"><iframe title="' + escapeHtml(title) + '" src="' + src + '" loading="lazy" allow="' + allow + '" allowfullscreen></iframe></div>' +
          '</div></div>';
      });
      wrap.innerHTML = html ? '<div class="row g-4 mt-1">' + html + '</div>'
        : '<div class="text-center text-muted py-5"><i class="fa-regular fa-circle-play me-2"></i>No ' + type + ' items yet — add them from the admin panel (Media tab).</div>';
    });
  }

  /* ---------------- Quran page (quran.html) ---------------- */
  function initQuranPage() {
    var Q = window.IBADAH_QURAN;
    if (!Q || !$(".quran-page")) return;
    var list = $("#surahCards");
    var reader = $("#quranReader");
    var textBox = $("#quranText");
    var search = $("#quranSearch");
    var nextBtn = $("#quranNext"), prevBtn = $("#quranPrev");
    var verseStats = $("#verseCount");
    var nameBox = $("#quranSurahName");
    var metaBox = $("#quranSurahMeta");
    var pageAudio = $("#quranAudioPage");
    var pageReciter = $("#quranReciterPage");
    var current = 1;

    var pageReciters = (DATA.reciters && DATA.reciters.length) ? DATA.reciters : [{ id: "ar.alafasy", name: "Mishary Rashid Alafasy" }];
    var pageReciterId = pageReciters[0].id;
    if (pageReciter && !pageReciter.options.length) {
      pageReciters.forEach(function (r) {
        var o = document.createElement("option");
        o.value = r.id; o.textContent = r.name;
        pageReciter.appendChild(o);
      });
      pageReciter.addEventListener("change", function () {
        pageReciterId = pageReciter.value;
        loadPageAudio(current);
      });
    }

    function loadPageAudio(n) {
      if (!pageAudio) return;
      pageAudio.src = "https://cdn.islamic.network/quran/audio-surah/128/" + pageReciterId + "/" + n + ".mp3";
      pageAudio.load();
    }

    function open(n) {
      var s = Q[n - 1];
      if (!s) return;
      current = n;
      window.IBADAH_STORE.set("ibadah-last-surah", String(n));
      textBox.innerHTML = "";
      s.v.forEach(function (v, i) {
        var span = document.createElement("span");
        span.className = "ayah-wrap";
        span.textContent = v + " ";
        var num = document.createElement("span");
        num.className = "ayah-num";
        num.innerHTML = "\u06DD" + (i + 1) + "\u06DE";
        span.appendChild(num);
        textBox.appendChild(span);
      });
      if (reader && reader.scrollIntoView) reader.scrollIntoView({ behavior: "smooth", block: "start" });
      renderList(search ? search.value : "");
      if (verseStats) verseStats.textContent = s.v.length;
      if (nameBox) nameBox.textContent = "Surah " + (s.t || n);
      if (metaBox) metaBox.textContent = n + ":" + s.v.length + " — " + (s.type === "D" ? "Medinan" : "Meccan");
      var head = $("#quranBismillah");
      if (head) head.textContent = s.name;
      loadPageAudio(n);
    }

    function renderList(filter) {
      var f = (filter || "").trim().toLowerCase();
      var html = "";
      Q.forEach(function (s) {
        var n = s.id;
        var match = !f || String(n) === f ||
          (s.t || "").toLowerCase().indexOf(f) !== -1 ||
          (s.name || "").indexOf(filter || "") !== -1;
        if (!match) return;
        html +=
          '<div class="col-6 col-md-4 col-lg-3 col-xl-2">' +
            '<button type="button" class="surah-card w-100' + (n === current ? " active" : "") + '" data-n="' + n + '">' +
              '<span class="surah-num">' + n + '</span>' +
              '<span class="flex-grow-1"><span class="fw-bold d-block small">' + (s.t || "Surah " + n) + '</span>' +
              '<span class="surah-name-ar d-none d-md-block">' + s.name + '</span></span>' +
            '</button>' +
          '</div>';
      });
      list.innerHTML = html || '<div class="col-12 text-center text-muted py-4">No surahs match your search.</div>';
      $$(".surah-card", list).forEach(function (btn) {
        btn.addEventListener("click", function () { open(parseInt(btn.getAttribute("data-n"), 10)); });
      });
    }

    if (search) search.addEventListener("input", function () { renderList(search.value); });
    if (prevBtn) prevBtn.addEventListener("click", function () { if (current > 1) open(current - 1); else open(114); });
    if (nextBtn) nextBtn.addEventListener("click", function () { if (current < 114) open(current + 1); else open(1); });

    var lastSaved = parseInt(window.IBADAH_STORE.get("ibadah-last-surah") || "1", 10);
    if (!(lastSaved >= 1 && lastSaved <= 114)) lastSaved = 1;
    open(lastSaved);
  }

  /* ---------------- Dark mode (Quran page) ---------------- */
  function initQuranDarkMode() {
    var btn = $("#quranDarkToggle");
    if (!btn) return;
    function apply(on) {
      document.body.classList.toggle("quran-dark", on);
      var icon = btn.querySelector("i");
      if (icon) icon.className = on ? "fa-solid fa-sun" : "fa-solid fa-moon";
    }
    apply(window.IBADAH_STORE.get("ibadah-quran-dark") === "1");
    btn.addEventListener("click", function () {
      var on = !document.body.classList.contains("quran-dark");
      window.IBADAH_STORE.set("ibadah-quran-dark", on ? "1" : "0");
      apply(on);
    });
  }


  /* ---------------- Donate form ---------------- */
  function initDonateForm() {
    var form = $("#donateForm");
    if (!form) return;
    var select = $("#donateCause");
    if (select) {
      DATA.causes.forEach(function (c) {
        var o = document.createElement("option");
        o.value = c.id; o.textContent = c.title;
        select.appendChild(o);
      });
      var hash = location.hash.replace("#cause-", "");
      if (hash) select.value = hash;
    }
    var customInput = $("#donateCustom");
    $$(".donate-amount-chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        $$(".donate-amount-chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        if (customInput) customInput.value = "";
      });
    });
    if (customInput) customInput.addEventListener("input", function () {
      if (customInput.value) $$(".donate-amount-chip").forEach(function (c) { c.classList.remove("active"); });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var causeId = select ? select.value : "";
      var cause = null;
      DATA.causes.forEach(function (c) { if (c.id === causeId) cause = c; });
      var amount = parseFloat(($("#donateCustom") && $("#donateCustom").value) ||
        ($(".donate-amount-chip.active") ? $(".donate-amount-chip.active").getAttribute("data-amount") : 0));
      if (!amount || amount <= 0) { toast("Please choose a donation amount", "error"); return; }
      var donor = ($("#donorName") && $("#donorName").value) || "Anonymous Donor";
      var records = [];
      try { records = JSON.parse(window.IBADAH_STORE.get("ibadah-donations") || "[]"); } catch (err) { records = []; }
      records.push({ id: Date.now(), name: donor, cause: cause ? cause.title : "General", amount: amount, date: new Date().toISOString() });
      window.IBADAH_STORE.set("ibadah-donations", JSON.stringify(records));

      toast("Jazakum Allahu khayran, " + donor + "! Your $" + amount.toLocaleString("en-US") + " donation was recorded.");
      form.reset();
      $$(".donate-amount-chip").forEach(function (c) { c.classList.remove("active"); });
      if (cause) {
        var newRaised = cause.raised + amount;
        try {
          var saved = window.getSiteData();
          saved.causes.forEach(function (c) { if (c.id === causeId) c.raised = newRaised; });
          window.saveSiteData(saved);
        } catch (err) { /* ignore */ }
      }
    });
  }

  /* ---------------- Contact & newsletter ---------------- */
  function initContactForm() {
    var form = $("#contactForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = $("#contactName").value.trim();
      var email = $("#contactEmail").value.trim();
      var msg = $("#contactMessage").value.trim();
      if (!name || !email || !msg) { toast("Please complete all required fields", "error"); return; }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { toast("Please enter a valid email address", "error"); return; }
      toast("Your message was sent — our team will reply soon, in shaa Allah.");
      form.reset();
    });
  }
  function initNewsletter() {
    var form = $("#newsletterForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = form.querySelector("input[type=email]").value.trim();
      if (!email) { toast("Please enter your email first", "error"); return; }
      toast("Subscribed successfully — thank you!");
      form.reset();
    });
  }

  /* ---------------- Back to top ---------------- */
  function initBackTop() {
    var btn = $(".back-to-top");
    if (!btn) return;
    window.addEventListener("scroll", function () {
      btn.classList.toggle("show", window.scrollY > 500);
    }, { passive: true });
    btn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
  }

  /* ---------------- Dates ---------------- */
  function renderDates() {
    var now = new Date();
    var hijri = PrayerCalc.hijriDate(now);
    $$("[data-hijri]").forEach(function (el) { el.textContent = hijri; });
    $$("[data-gregorian]").forEach(function (el) { el.textContent = PrayerCalc.gregorianEn(now); });
  }

  /* ---------------- News ---------------- */
  function renderNews() {
    var grid = $("#newsGrid");
    if (!grid) return;
    var html = "";
    DATA.news.forEach(function (n) {
      html += '<div class="col-md-6 col-lg-4" data-reveal>' +
        '<div class="card-soft news-card h-100 p-0 overflow-hidden">' +
        '<div class="news-img"><img src="' + n.img + '" alt="' + n.title + '" class="img-cover"></div>' +
        '<div class="p-4">' +
        '<div class="news-date mb-2"><i class="fa-regular fa-calendar-days me-1"></i>' + n.date + '</div>' +
        '<h5 class="news-title mb-3">' + n.title + '</h5>' +
        '<p class="text-muted small">' + n.excerpt + '</p>' +
        '<div class="d-flex align-items-center gap-2 mt-3 small text-muted">' +
        '<i class="fa-solid fa-user-pen text-gold"></i> By: ' + n.author + '</div>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- Pillars (Arabic name + English) ---------------- */
  function renderPillars() {
    var wrap = $("#pillarGrid");
    if (!wrap) return;
    var html = "";
    DATA.pillars.forEach(function (p) {
      html += '<div class="col-6 col-md-4 col-lg" data-reveal>' +
        '<div class="pillar-tile"><img src="' + p.img + '" alt="' + p.en + '">' +
        '<div class="pillar-body"><div class="pillar-ar">' + p.ar + '</div>' +
        '<div class="pillar-en">' + p.en + '</div></div></div></div>';
    });
    wrap.innerHTML = html;
    initReveal();
  }

  /* ---------------- Pricing ---------------- */
  function renderPricing() {
    var wrap = $("#pricingGrid");
    if (!wrap) return;
    var html = "";
    DATA.pricing.forEach(function (p) {
      html += '<div class="col-md-4" data-reveal>' +
        '<div class="card-soft price-card h-100 p-4 text-center' + (p.featured ? " featured" : "") + '">' +
        (p.featured ? '<span class="featured-ribbon">Most Popular</span>' : '') +
        '<h5 class="fw-bold text-green">' + p.name + '</h5>' +
        '<p class="text-muted small">' + p.period + '</p>' +
        '<div class="price-tag my-3">$' + p.price + ' <small>/ ' + p.period + '</small></div>' +
        '<ul class="list-check text-start mx-auto" style="max-width:260px">';
      p.features.forEach(function (f) { html += '<li>' + f + '</li>'; });
      html += '</ul><a href="donate.html" class="btn btn-gold mt-4 w-100">Join Now</a></div></div>';
    });
    wrap.innerHTML = html;
    initReveal();
  }

  /* ---------------- Event detail (with speaker bio) ---------------- */
  function renderEventDetail() {
    var wrap = $("#eventDetail");
    if (!wrap) return;
    var id = new URLSearchParams(location.search).get("id") || DATA.events[0].id;
    var ev = null;
    DATA.events.forEach(function (e) { if (e.id === id) ev = e; });
    if (!ev) ev = DATA.events[0];
    document.title = ev.title + " — " + DATA.general.siteName;
    var d = new Date(ev.date);
    var tags = (ev.tags || []).map(function (t) { return '<span class="badge">' + t + '</span>'; }).join("");

    wrap.innerHTML =
      '<div class="row g-5 align-items-center">' +
      '<div class="col-lg-6" data-reveal="left"><img src="' + ev.image + '" class="img-fluid rounded-4 shadow" alt="' + ev.title + '"></div>' +
      '<div class="col-lg-6" data-reveal="right">' +
      '<span class="badge text-bg-light border fw-bold text-gold mb-3">' + ev.category + '</span>' +
      '<h1 class="fw-bold text-green mb-3">' + ev.title + '</h1>' +
      '<div class="event-meta my-3 fs-6">' +
      '<span><i class="fa-regular fa-calendar me-1"></i>' + d.toLocaleDateString("en-US", { weekday: "long", day: "numeric", month: "long", year: "numeric" }) + '</span><br>' +
      '<span><i class="fa-regular fa-clock me-1"></i>' + d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" }) + '</span>' +
      '<span><i class="fa-solid fa-location-dot me-1"></i>' + ev.location + '</span></div>' +
      '<p class="text-muted">' + ev.desc + '</p>' +
      '<div class="row g-3 my-3">' +
      '<div class="col-sm-6"><div class="d-flex align-items-center gap-2"><i class="fa-solid fa-user-tie fs-4 text-gold"></i><div><div class="small text-muted">Speaker</div><strong>' + ev.guests + '</strong></div></div></div>' +
      '<div class="col-sm-6"><div class="d-flex align-items-center gap-2"><i class="fa-solid fa-users fs-4 text-gold"></i><div><div class="small text-muted">Organizer</div><strong>' + ev.organizer + '</strong></div></div></div>' +
      '</div>' +
      '<div class="d-flex gap-3 flex-wrap mt-4">' +
      '<a href="donate.html" class="btn btn-gold"><i class="fa-solid fa-hand-holding-heart me-2"></i>Support This Event</a>' +
      '<a href="contact.html" class="btn btn-outline-green"><i class="fa-solid fa-ticket me-2"></i>Reserve a Seat</a>' +
      '</div></div></div>' +

      /* Speaker / researcher bio */
      '<div class="card-soft p-4 mt-5" data-reveal>' +
      '<div class="speaker-bio">' +
      '<span class="speaker-avatar"><i class="fa-solid fa-user-tie"></i></span>' +
      '<div class="w-100">' +
      '<div class="small text-muted mb-1">About the speaker</div>' +
      '<div class="speaker-name">' + ev.guests + '</div>' +
      '<div class="speaker-role">' + (ev.guestRole || "Guest speaker") + '</div>' +
      '<p class="text-muted mt-2 mb-0">' + (ev.guestBio || "") + '</p>' +
      '<div class="speaker-tags">' + tags + '</div>' +
      '</div></div></div>' +

      '<div class="row g-3 mt-4">' +
      '<div class="col-lg-8"><div class="card-soft p-4"><h5 class="fw-bold text-green mb-3"><i class="fa-regular fa-clock me-2 text-gold"></i>Day Schedule</h5>' +
      '<ul class="schedule-list">' +
      '<li><span>Registration & welcome</span><span class="time">4:00 PM</span></li>' +
      '<li><span>Opening & Quran recitation</span><span class="time">4:30 PM</span></li>' +
      '<li><span>' + ev.title + '</span><span class="time">5:00 PM</span></li>' +
      '<li><span>Open Q&A session</span><span class="time">6:30 PM</span></li>' +
      '<li><span>Closing & du\'a</span><span class="time">7:15 PM</span></li></ul></div></div>' +
      '<div class="col-lg-4"><div class="card-soft p-4 text-center"><h6 class="fw-bold text-green mb-3">Starts in</h6><div class="countdown justify-content-center" data-target="' + new Date(ev.date).getTime() + '" id="eventCountdown"></div></div></div>' +
      '</div>';
    initCountdown();
    initReveal();
  }

  /* ---------------- Prayer page ---------------- */
  function renderWeeklyTable() {
    var tbody = $("#weeklyTableBody");
    if (!tbody) return;
    var city = getCity();
    var names = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"];
    var html = "";
    for (var i = 0; i < 7; i++) {
      var day = PrayerCalc.addDays(new Date(), i);
      var times = PrayerCalc.getTimes(day, city, getSettings());
      var isToday = i === 0;
      html += '<tr class="' + (isToday ? "today" : "") + '">' +
        '<td class="fw-bold">' + (isToday ? "Today — " : "") + PrayerCalc.weekdayEn(day) + '</td>';
      names.forEach(function (k) {
        html += '<td class="time-cell">' + (times[k] ? PrayerCalc.format12(times[k]) : "--:--") + '</td>';
      });
      html += '</tr>';
    }
    tbody.innerHTML = html;
  }

  function renderPrayerPage() {
    var table = $("#prayerTableBody");
    if (!table) return;

    var citySel = $("#prayerCity");
    if (citySel && citySel.options.length === 0) {
      DATA.cities.forEach(function (c) {
        var o = document.createElement("option");
        o.value = c.id; o.textContent = c.name;
        if (c.id === state.cityId) o.selected = true;
        citySel.appendChild(o);
      });
    }
    var methodSel = $("#prayerMethod");
    if (methodSel && methodSel.options.length === 0) {
      Object.keys(PrayerCalc.METHODS).forEach(function (k) {
        var o = document.createElement("option");
        o.value = k; o.textContent = PrayerCalc.METHODS[k].name;
        if (k === state.method) o.selected = true;
        methodSel.appendChild(o);
      });
    }
    var madhabSel = $("#prayerMadhab");
    if (madhabSel && madhabSel.options.length === 0) {
      [["Shafi", "Standard (Shafi)"], ["Hanafi", "Hanafi"]].forEach(function (pair) {
        var o = document.createElement("option");
        o.value = pair[0]; o.textContent = pair[1];
        if (pair[0] === state.madhab) o.selected = true;
        madhabSel.appendChild(o);
      });
    }

    function fill() {
      var now = new Date();
      var city = getCity();
      var times = PrayerCalc.getTimes(now, city, getSettings());
      var iqOffsets = DATA.prayerSettings.iqamaOffsets;

      var heroTime = $("#prayerHeroTime");
      if (heroTime) heroTime.textContent = PrayerCalc.format12(times.dhuhr);
      var heroCity = $("#prayerHeroCity");
      if (heroCity) heroCity.textContent = city.name;
      var methodLabel = $("#prayerMethodLabel");
      if (methodLabel) methodLabel.textContent = PrayerCalc.METHODS[state.method].name;
      var madhabLabel = $("#prayerMadhabLabel");
      if (madhabLabel) madhabLabel.textContent = state.madhab === "Hanafi" ? "Hanafi" : "Standard (Shafi)";

      var names = [
        { key: "fajr", label: "Fajr" }, { key: "sunrise", label: "Sunrise" },
        { key: "dhuhr", label: "Dhuhr" }, { key: "asr", label: "Asr" },
        { key: "maghrib", label: "Maghrib" }, { key: "isha", label: "Isha" }
      ];
      var html = "";
      var isFriday = now.getDay() === 5;
      names.forEach(function (n) {
        var t = times[n.key];
        var iq = n.key === "maghrib" ? t : iqamaFor(n.key.charAt(0).toUpperCase() + n.key.slice(1), t);
        html += '<tr class="' + (isFriday && n.key === "dhuhr" ? "today" : "") + '">' +
          '<td class="fw-bold">' + n.label + '</td>' +
          '<td class="time-cell">' + (t ? PrayerCalc.format12(t) : "--:--") + '</td>' +
          '<td class="text-muted fw-semibold">' + (iq ? PrayerCalc.format12(iq) : "--:--") + '</td>' +
          '<td><span class="badge ' + (t ? "text-bg-success" : "text-bg-secondary") + '">' + (t ? "Available" : "N/A") + '</span></td></tr>';
      });
      html += '<tr class="' + (isFriday ? "today" : "") + '"><td class="fw-bold">Jumu\'ah</td>' +
        '<td class="time-cell" colspan="2">' + DATA.prayerSettings.jumuaTime + ' PM</td>' +
        '<td><span class="badge text-bg-warning">Khutbah</span></td></tr>';
      table.innerHTML = html;

      var pct = $("#prayerTodayPct");
      if (pct) pct.textContent = PrayerCalc.weekdayEn(now) + ", " + PrayerCalc.gregorianEn(now);
      var hij = $("#prayerHijri");
      if (hij) hij.textContent = PrayerCalc.hijriDate(now);
      var qc = $("#qiblaCity");
      if (qc) qc.textContent = city.name;
      var qd = $("#qiblaDeg");
      if (qd) qd.textContent = (PrayerCalc.qiblaBearing(city.lat, city.lng) || 0).toFixed(1) + "°";
    }

    fill();
    renderWeeklyTable();
    if (citySel) citySel.addEventListener("change", function () {
      state.cityId = citySel.value;
      window.IBADAH_STORE.set("ibadah-city", state.cityId);
      fill(); renderWeeklyTable();
    });
    if (methodSel) methodSel.addEventListener("change", function () {
      state.method = methodSel.value;
      window.IBADAH_STORE.set("ibadah-method", state.method);
      fill(); renderWeeklyTable();
    });
    if (madhabSel) madhabSel.addEventListener("change", function () {
      state.madhab = madhabSel.value;
      window.IBADAH_STORE.set("ibadah-madhab", state.madhab);
      fill(); renderWeeklyTable();
    });
  }

  /* ---------------- Init ---------------- */
  document.addEventListener("DOMContentLoaded", function () {
    applyTexts();
    renderDates();
    initNav();
    initHero();
    initReveal();
    initCounters();
    initAyat();
    initQuranAudio();
    initQuranPage();
    initQuranDarkMode();
    initDonateForm();
    initContactForm();
    initNewsletter();
    initBackTop();
    renderMedia();
    renderCourses();
    renderCauses();
    renderEvents();
    renderEventSchedule();
    renderProjects();
    renderNews();
    renderPillars();
    renderPricing();
    renderEventDetail();
    renderPrayerPage();
    initCountdown();
    startTicker();
  });

  window.IBADAH_UI = {
    refresh: function () {
      DATA = window.getSiteData();
      computeTimes();
      renderPrayerStrip();
      renderCourses(); renderCauses(); renderEvents(); renderEventSchedule();
      renderProjects(); renderNews(); renderPillars(); renderPricing();
      renderEventDetail(); renderPrayerPage(); renderMedia();
    },
    toast: toast
  };
})();
