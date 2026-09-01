/* ============================================================
   Ibadah — Main site JS (vanilla JS, no jQuery)
   Hero slider · Prayer strip · Countdowns · Reveal · Forms
   ============================================================ */

(function () {
  "use strict";

  var DATA = window.getSiteData ? window.getSiteData() : window.IBADAH_DEFAULTS;
  var state = {
    cityId: localStorage.getItem("ibadah-city") || DATA.prayerSettings.defaultCityId,
    method: localStorage.getItem("ibadah-method") || DATA.prayerSettings.method,
    madhab: localStorage.getItem("ibadah-madhab") || DATA.prayerSettings.asrMadhab,
    times: null,
    tickTimer: null
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
        if (value == null) break;
        value = value[path[i]];
      }
      if (value != null) {
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

    /* تفعيل رابط القسم الحالي */
    var links = $$(".navbar .nav-link[href^='#']");
    if (links.length) {
      var sections = links.map(function (l) { return $(l.getAttribute("href")); }).filter(Boolean);
      window.addEventListener("scroll", function () {
        var pos = window.scrollY + 140;
        var current = null;
        sections.forEach(function (s, i) {
          if (s.offsetTop <= pos) current = links[i];
        });
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
      b.setAttribute("aria-label", "شريحة " + (i + 1));
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
    return {
      method: state.method,
      asrMadhab: state.madhab,
      iqamaOffsets: DATA.prayerSettings.iqamaOffsets
    };
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

  function todayKey(date) {
    return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0");
  }

  function iqamaFor(key, time) {
    if (!time) return null;
    var off = DATA.prayerSettings.iqamaOffsets[key] || 0;
    if (key === "Maghrib") return time;
    var mins = time.hour * 60 + time.minute + off;
    return { hour: Math.floor((mins / 60) % 24), minute: mins % 60 };
  }

  /* شريط المواقيت في الرئيسية */
  function renderPrayerStrip() {
    var wrap = $("#prayerStrip");
    if (!wrap || !state.times) return;
    computeTimes();
    var names = [
      { key: "Fajr", ar: "الفجر", icon: "fa-cloud-moon" },
      { key: "Dhuhr", ar: "الظهر", icon: "fa-sun" },
      { key: "Asr", ar: "العصر", icon: "fa-cloud-sun" },
      { key: "Maghrib", ar: "المغرب", icon: "fa-umbrella-beach" },
      { key: "Isha", ar: "العشاء", icon: "fa-moon" },
      { key: "Jumuah", ar: "الجمعة", icon: "fa-mosque", custom: true }
    ];
    var html = '<div class="row g-3">';
    names.forEach(function (n, i) {
      var t = n.custom ? null : state.times[n.key.charAt(0).toLowerCase() + n.key.slice(1)];
      var iq = n.custom ? null : iqamaFor(n.key, t);
      var timeStr = n.custom ? "12:30 م" : PrayerCalc.format12(t || { hour: 0, minute: 0 });
      html += '<div class="col-6 col-md-4 col-lg-2">' +
        '<div class="prayer-card" id="prayerCard-' + n.key + '">' +
        '<div class="prayer-icon"><i class="fa-solid ' + n.icon + '"></i></div>' +
        '<div class="prayer-name">' + n.ar + '</div>' +
        '<div class="prayer-time">' + timeStr + '</div>' +
        '<div class="prayer-iqama">' + (n.custom ? "خطبة: 1:15 م" : "الإقامة: " + (iq ? PrayerCalc.format12(iq) : "--:--")) + '</div>' +
        '</div></div>';
    });
    html += '</div>';
    wrap.innerHTML = html;
    markCurrentPrayer();
  }

  function markCurrentPrayer() {
    if (!state.times || !state.now) return;
    var names = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];
    var cur = null, nextKey = null, nextTime = null;
    names.forEach(function (k) {
      var t = state.times[k.charAt(0).toLowerCase() + k.slice(1)];
      if (t) {
        var mins = t.hour * 60 + t.minute;
        var nowMins = state.now.getHours() * 60 + state.now.getMinutes();
        if (mins <= nowMins) cur = k;
        else if (!nextTime || mins < nextTime) { nextKey = k; nextTime = mins; }
      }
    });
    /* الصلاة التالية بعد منتصف الليل */
    if (!nextKey) nextKey = names[0];

    $$(".prayer-card").forEach(function (card) {
      var key = card.id.replace("prayerCard-", "");
      if (key === cur) card.classList.add("current");
      else card.classList.remove("current");
    });

    var note = $("#nextPrayerNote");
    if (note && nextKey) {
      var labels = { Fajr: "الفجر", Dhuhr: "الظهر", Asr: "العصر", Maghrib: "المغرب", Isha: "العشاء" };
      note.innerHTML = '<i class="fa-solid fa-clock"></i> الصلاة القادمة: <strong>' + labels[nextKey] + '</strong>';
    }
  }

  /* تحديث المواقيت كل دقيقة */
  function startTicker() {
    computeTimes();
    renderPrayerStrip();
    setInterval(function () { computeTimes(); renderPrayerStrip(); }, 60000);
  }

  /* ---------------- العد التنازلي للحدث ---------------- */
  function initCountdown() {
    var box = $("#countdown");
    if (!box) return;
    var target = new Date(box.getAttribute("data-target")).getTime();
    function pad(n) { return String(n).padStart(2, "0"); }
    function tick() {
      var diff = Math.max(0, target - Date.now());
      var d = Math.floor(diff / 86400000);
      var h = Math.floor((diff % 86400000) / 3600000);
      var m = Math.floor((diff % 3600000) / 60000);
      var s = Math.floor((diff % 60000) / 1000);
      box.innerHTML =
        '<div class="cd-box"><div class="cd-num">' + pad(d) + '</div><div class="cd-label">يوم</div></div>' +
        '<div class="cd-box"><div class="cd-num">' + pad(h) + '</div><div class="cd-label">ساعة</div></div>' +
        '<div class="cd-box"><div class="cd-num">' + pad(m) + '</div><div class="cd-label">دقيقة</div></div>' +
        '<div class="cd-box"><div class="cd-num">' + pad(s) + '</div><div class="cd-label">ثانية</div></div>';
      if (diff <= 0) clearInterval(timer);
    }
    tick();
    var timer = setInterval(tick, 1000);
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
        if (e.isIntersecting) {
          e.target.classList.add("revealed");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ---------------- عداد الأرقام ---------------- */
  function initCounters() {
    var nums = $$(".fact-num[data-count]");
    if (!nums.length) return;
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
          var val = Math.floor(target * (1 - Math.pow(1 - p, 3)));
          el.textContent = val.toLocaleString("ar-EG") + suffix;
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
        io.unobserve(el);
      });
    }, { threshold: 0.5 });
    nums.forEach(function (el) { io.observe(el); });
  }

  /* ---------------- Carousel بسيط للآيات ---------------- */
  function initAyat() {
    var wrap = $("#ayatSlider");
    if (!wrap) return;
    var current = 0;
    var html = "";
    DATA.ayat.forEach(function (a, i) {
      html += '<div class="carousel-item' + (i === 0 ? " active" : "") + '">' +
        '<i class="fa-solid fa-quote-right ayat-quote"></i>' +
        '<p class="ayat-text">' + a.text + '</p>' +
        '<p class="ayat-ref">' + a.ref + '</p></div>';
    });
    wrap.innerHTML = html;
    var carousel = new bootstrap.Carousel(wrap, { interval: 7000, ride: "carousel" });

    var prev = $("#ayatPrev"), next = $("#ayatNext");
    if (prev) prev.addEventListener("click", function () { carousel.prev(); });
    if (next) next.addEventListener("click", function () { carousel.next(); });
  }

  /* ---------------- بطاقات الدورات ---------------- */
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
        '<div class="course-price">$' + c.price + (c.priceFree ? ' <span class="small">(مجاني)</span>' : '') + '</div>' +
        '<h5 class="fw-bold text-green mt-4 mb-2"><a class="stretched-link text-green" href="courses.html?c=' + c.id + '">' + c.title + '</a></h5>' +
        '<p class="text-muted small mb-3">' + c.desc + '</p>' +
        '<div class="course-meta d-flex gap-3 flex-wrap small">' +
        '<span class="badge"><i class="fa-regular fa-calendar me-1"></i>' + c.weeks + ' أسبوعاً</span>' +
        '<span class="badge"><i class="fa-solid fa-users me-1"></i>' + c.enroll + ' منضم</span></div>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- بطاقات التبرعات ---------------- */
  function renderCauses() {
    var grid = $("#causeGrid");
    if (!grid) return;
    var html = "";
    DATA.causes.forEach(function (c) {
      var pct = Math.min(100, Math.round((c.raised / c.goal) * 100));
      var left = Math.max(0, c.goal - c.raised);
      html += '<div class="col-md-6 col-lg-4" data-reveal>' +
        '<div class="card-soft cause-card h-100 p-0 overflow-hidden">' +
        '<div class="cause-img">' +
        '<img src="' + c.img + '" alt="' + c.title + '" class="img-cover">' +
        '<span class="cause-cat">' + c.category + '</span></div>' +
        '<div class="p-4">' +
        '<h5 class="fw-bold text-green"><a class="stretched-link text-green" href="donate.html#cause-' + c.id + '">' + c.title + '</a></h5>' +
        '<p class="text-muted small">' + c.desc + '</p>' +
        '<div class="d-flex justify-content-between small fw-bold mb-1">' +
        '<span class="text-gold">' + pct + '%</span><span class="text-muted">' + (c.raised / c.goal * 100).toFixed(1) + '%</span></div>' +
        '<div class="cause-progress mb-3"><div class="bar" style="width:' + pct + '%"></div></div>' +
        '<div class="d-flex justify-content-between small">' +
        '<span><i class="fa-solid fa-hand-holding-heart text-gold me-1"></i>المتبقي: <strong class="text-green">$' + left.toLocaleString("ar-EG") + '</strong></span>' +
        '<a href="donate.html#cause-' + c.id + '" class="fw-bold text-green">تبرّع <i class="fa-solid fa-arrow-left"></i></a></div>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- بطاقات الفعاليات ---------------- */
  function renderEvents() {
    var grid = $("#eventGrid");
    if (!grid) return;
    var html = "";
    DATA.events.forEach(function (ev) {
      var d = new Date(ev.date);
      var monthNames = ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"];
      html += '<div class="col-md-6 col-lg-4" data-reveal>' +
        '<div class="card-soft event-card h-100 p-0 overflow-hidden">' +
        '<div class="event-img"><img src="' + ev.image + '" alt="' + ev.title + '" class="img-cover">' +
        '<div class="event-date-badge"><div class="d">' + d.getDate() + '</div><div class="m">' + monthNames[d.getMonth()] + '</div></div></div>' +
        '<div class="p-4">' +
        '<span class="badge text-bg-light border mb-2 fw-bold text-gold">' + ev.category + '</span>' +
        '<h5 class="fw-bold text-green"><a class="stretched-link text-green" href="event.html?id=' + ev.id + '">' + ev.title + '</a></h5>' +
        '<div class="event-meta my-3">' +
        '<span><i class="fa-regular fa-clock me-1"></i>' + d.toLocaleDateString("ar", { day: "numeric", month: "long", year: "numeric" }) + '</span>' +
        '<span><i class="fa-solid fa-location-dot me-1"></i>' + ev.location + '</span></div>' +
        '<p class="text-muted small mb-3">' + ev.desc + '</p>' +
        '<a href="event.html?id=' + ev.id + '" class="fw-bold text-green">التفاصيل <i class="fa-solid fa-arrow-left"></i></a>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- مشغل القرآن ---------------- */
  function initQuranAudio() {
    var player = $("#quranAudio");
    var list = $("#surahList");
    if (!player || !list) return;
    var surahs = [
      { n: 1, name: "الفاتحة", reciter: "مشاري العفاسي" },
      { n: 36, name: "يس", reciter: "مشاري العفاسي" },
      { n: 55, name: "الرحمن", reciter: "مشاري العفاسي" },
      { n: 67, name: "الملك", reciter: "مشاري العفاسي" },
      { n: 112, name: "الإخلاص", reciter: "مشاري العفاسي" },
      { n: 113, name: "الفلق", reciter: "مشاري العفاسي" },
      { n: 114, name: "الناس", reciter: "مشاري العفاسي" }
    ];
    var html = "";
    surahs.forEach(function (s, i) {
      html += '<button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center surah-item' +
        (i === 0 ? " active" : "") + '" data-n="' + s.n + '" data-name="' + s.name + '">' +
        '<span><i class="fa-solid fa-book-quran text-gold me-2"></i><strong>' + s.name + '</strong>' +
        '<span class="d-block small text-muted">' + s.reciter + '</span></span>' +
        '<i class="fa-solid fa-play-circle fs-4 text-gold"></i></button>';
    });
    list.innerHTML = html;

    var audio = player; /* #quranAudio هو عنصر <audio> نفسه */
    var title = $("#surahTitle");
    var items = $$(".surah-item", list);

    function load(n, name) {
      audio.src = "https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/" + n + ".mp3";
      audio.load();
      if (title) title.textContent = "سورة " + name;
      items.forEach(function (it) {
        it.classList.toggle("active", parseInt(it.getAttribute("data-n"), 10) === n);
      });
    }

    items.forEach(function (it) {
      it.addEventListener("click", function () {
        load(parseInt(it.getAttribute("data-n"), 10), it.getAttribute("data-name"));
        audio.play().catch(function () { toast("تعذر تشغيل الصوت، تحقق من اتصال الإنترنت", "error"); });
      });
    });

    audio.addEventListener("error", function () {
      toast("تعذر تحميل التلاوة، قد يكون الاتصال بالإنترنت ضعيفاً", "error");
    });

    load(1, "الفاتحة");
  }

  /* ---------------- نموذج التبرع ---------------- */
  function initDonateForm() {
    var form = $("#donateForm");
    if (!form) return;

    /* ملء قائمة الأسباب */
    var select = $("#donateCause");
    if (select) {
      DATA.causes.forEach(function (c) {
        var o = document.createElement("option");
        o.value = c.id;
        o.textContent = c.title;
        select.appendChild(o);
      });
      var hash = location.hash.replace("#cause-", "");
      if (hash) select.value = hash;
    }

    /* أزرار المبالغ */
    var customInput = $("#donateCustom");
    $$(".donate-amount-chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        $$(".donate-amount-chip").forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        if (customInput) customInput.value = "";
      });
    });
    if (customInput) {
      customInput.addEventListener("input", function () {
        if (customInput.value) {
          $$(".donate-amount-chip").forEach(function (c) { c.classList.remove("active"); });
        }
      });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var causeId = select ? select.value : "";
      var cause = null;
      DATA.causes.forEach(function (c) { if (c.id === causeId) cause = c; });

      var amount = parseFloat(($("#donateCustom") && $("#donateCustom").value) ||
        ($(".donate-amount-chip.active") ? $(".donate-amount-chip.active").getAttribute("data-amount") : 0));
      if (!amount || amount <= 0) {
        toast("فضلاً اختر مبلغ التبرع", "error");
        return;
      }

      var donor = ($("#donorName") && $("#donorName").value) || "متبرع كريم";
      var records = [];
      try { records = JSON.parse(localStorage.getItem("ibadah-donations") || "[]"); } catch (e) { records = []; }
      records.push({
        id: Date.now(),
        name: donor,
        cause: cause ? cause.title : "عام",
        amount: amount,
        date: new Date().toISOString()
      });
      localStorage.setItem("ibadah-donations", JSON.stringify(records));

      toast("جزاك الله خيراً " + donor + "! تم تسجيل تبرعك بقيمة $" + amount.toLocaleString("en-US") + ".");
      form.reset();
      $$(".donate-amount-chip").forEach(function (c) { c.classList.remove("active"); });

      /* تحديث نسبة الحملة محلياً (عرض تجريبي) */
      if (cause) {
        var newRaised = cause.raised + amount;
        try {
          var saved = window.getSiteData();
          saved.causes.forEach(function (c) { if (c.id === causeId) c.raised = newRaised; });
          window.saveSiteData(saved);
        } catch (err) { /* تجاهل */ }
      }
    });
  }

  /* ---------------- نموذج التواصل ---------------- */
  function initContactForm() {
    var form = $("#contactForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = $("#contactName").value.trim();
      var email = $("#contactEmail").value.trim();
      var msg = $("#contactMessage").value.trim();
      if (!name || !email || !msg) {
        toast("فضلاً أكمل جميع الحقول المطلوبة", "error");
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        toast("صيغة البريد الإلكتروني غير صحيحة", "error");
        return;
      }
      toast("تم إرسال رسالتك بنجاح، سيتواصل معك الفريق قريباً بإذن الله.");
      form.reset();
    });
  }

  /* ---------------- النشرة البريدية ---------------- */
  function initNewsletter() {
    var form = $("#newsletterForm");
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = form.querySelector("input[type=email]").value.trim();
      if (!email) { toast("أدخل بريدك الإلكتروني أولاً", "error"); return; }
      toast("تم اشتراكك في النشرة البريدية، تقبّل الله منك.");
      form.reset();
    });
  }

  /* ---------------- زر العودة للأعلى ---------------- */
  function initBackTop() {
    var btn = $(".back-to-top");
    if (!btn) return;
    window.addEventListener("scroll", function () {
      btn.classList.toggle("show", window.scrollY > 500);
    }, { passive: true });
    btn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
  }

  /* ---------------- شارة التاريخ الهجري ---------------- */
  function renderDates() {
    var now = new Date();
    var hijri = PrayerCalc.hijriDate(now);
    var els = $$("[data-hijri]");
    els.forEach(function (el) { el.textContent = hijri; });
    var g = $$("[data-gregorian]");
    g.forEach(function (el) { el.textContent = PrayerCalc.gregorianAr(now); });
  }

  /* ---------------- أخبار ---------------- */
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
        '<i class="fa-solid fa-user-pen text-gold"></i> بقلم: ' + n.author + '</div>' +
        '</div></div></div>';
    });
    grid.innerHTML = html;
    initReveal();
  }

  /* ---------------- أركان الإسلام ---------------- */
  function renderPillars() {
    var wrap = $("#pillarGrid");
    if (!wrap) return;
    var html = "";
    DATA.pillars.forEach(function (p) {
      html += '<div class="col-6 col-md-4 col-lg" data-reveal>' +
        '<div class="pillar-tile"><img src="' + p.img + '" alt="' + p.ar + '">' +
        '<div class="pillar-body"><div class="pillar-ar">' + p.ar + '</div>' +
        '<div class="pillar-en">' + p.en + '</div></div></div></div>';
    });
    wrap.innerHTML = html;
    initReveal();
  }

  /* ---------------- خطط الأسعار ---------------- */
  function renderPricing() {
    var wrap = $("#pricingGrid");
    if (!wrap) return;
    var html = "";
    DATA.pricing.forEach(function (p) {
      html += '<div class="col-md-4" data-reveal>' +
        '<div class="card-soft price-card h-100 p-4 text-center' + (p.featured ? " featured" : "") + '">' +
        (p.featured ? '<span class="featured-ribbon">الأكثر طلباً</span>' : '') +
        '<h5 class="fw-bold text-green">' + p.name + '</h5>' +
        '<p class="text-muted small">' + p.period + '</p>' +
        '<div class="price-tag my-3">$' + p.price + ' <small>/ ' + p.period + '</small></div>' +
        '<ul class="list-check text-start mx-auto" style="max-width:260px">';
      p.features.forEach(function (f) { html += '<li>' + f + '</li>'; });
      html += '</ul><a href="donate.html" class="btn btn-gold mt-4 w-100">انضم الآن</a></div></div>';
    });
    wrap.innerHTML = html;
    initReveal();
  }

  /* ---------------- صفحة تفاصيل حدث ---------------- */
  function renderEventDetail() {
    var wrap = $("#eventDetail");
    if (!wrap) return;
    var id = new URLSearchParams(location.search).get("id") || DATA.events[0].id;
    var ev = null;
    DATA.events.forEach(function (e) { if (e.id === id) ev = e; });
    if (!ev) ev = DATA.events[0];
    document.title = ev.title + " — " + DATA.general.siteName;
    var d = new Date(ev.date);
    wrap.innerHTML =
      '<div class="row g-5 align-items-center">' +
      '<div class="col-lg-6" data-reveal="left"><img src="' + ev.image + '" class="img-fluid rounded-4 shadow" alt="' + ev.title + '"></div>' +
      '<div class="col-lg-6" data-reveal="right">' +
      '<span class="badge text-bg-light border fw-bold text-gold mb-3">' + ev.category + '</span>' +
      '<h1 class="fw-bold text-green mb-3">' + ev.title + '</h1>' +
      '<div class="event-meta my-3 fs-6">' +
      '<span><i class="fa-regular fa-calendar me-1"></i>' + d.toLocaleDateString("ar", { weekday: "long", day: "numeric", month: "long", year: "numeric" }) + '</span><br>' +
      '<span><i class="fa-regular fa-clock me-1"></i>' + d.toLocaleTimeString("ar", { hour: "2-digit", minute: "2-digit" }) + '</span>' +
      '<span><i class="fa-solid fa-location-dot me-1"></i>' + ev.location + '</span></div>' +
      '<p class="text-muted">' + ev.desc + '</p>' +
      '<div class="row g-3 my-3">' +
      '<div class="col-sm-6"><div class="d-flex align-items-center gap-2"><i class="fa-solid fa-user-tie fs-4 text-gold"></i><div><div class="small text-muted">المتحدث</div><strong>' + ev.guests + '</strong></div></div></div>' +
      '<div class="col-sm-6"><div class="d-flex align-items-center gap-2"><i class="fa-solid fa-users fs-4 text-gold"></i><div><div class="small text-muted">المنظم</div><strong>' + ev.organizer + '</strong></div></div></div>' +
      '</div>' +
      '<div class="d-flex gap-3 flex-wrap mt-4">' +
      '<a href="donate.html" class="btn btn-gold"><i class="fa-solid fa-hand-holding-heart me-2"></i>ادعم الفعالية</a>' +
      '<a href="contact.html" class="btn btn-outline-green"><i class="fa-solid fa-ticket me-2"></i>احجز مكاناً</a>' +
      '</div></div></div>' +
      '<div class="row g-3 mt-4">' +
      '<div class="col-lg-8"><div class="card-soft p-4"><h5 class="fw-bold text-green mb-3"><i class="fa-regular fa-clock me-2 text-gold"></i>جدول اليوم</h5>' +
      '<ul class="schedule-list">' +
      '<li><span>الاستقبال والتسجيل</span><span class="time">4:00 م</span></li>' +
      '<li><span>الافتتاح والقرآن الكريم</span><span class="time">4:30 م</span></li>' +
      '<li><span>' + ev.title + '</span><span class="time">5:00 م</span></li>' +
      '<li><span>جلسة أسئلة وأجوبة</span><span class="time">6:30 م</span></li>' +
      '<li><span>الختام ودعاء</span><span class="time">7:15 م</span></li></ul></div></div>' +
      '<div class="col-lg-4"><div class="card-soft p-4 text-center"><h6 class="fw-bold text-green mb-3">يبدأ بعد</h6><div class="countdown justify-content-center" data-target="' + new Date(ev.date).getTime() + '" id="eventCountdown"></div></div></div>' +
      '</div>';
    initCountdown();
    initReveal();
  }

    /* ---------------- صفحة المواقيت ---------------- */
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
        '<td class="fw-bold">' + (isToday ? "اليوم — " : "") + PrayerCalc.weekdayAr(day) + '</td>';
      names.forEach(function (k) {
        html += '<td class="time-cell">' + (times[k] ? PrayerCalc.format12(times[k]) : "--:--") + '</td>';
      });
      html += '</tr>';
    }
    tbody.innerHTML = html;
  }

  /* ---------------- صفحة المواقيت ---------------- */
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
      [["Shafi", "الجمهور (الشافعي)"], ["Hanafi", "الحنفي"]].forEach(function (pair) {
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
      if (madhabLabel) madhabLabel.textContent = state.madhab === "Hanafi" ? "الحنفي" : "الجمهور (الشافعي)";

      var names = [
        { key: "fajr", ar: "الفجر" },
        { key: "sunrise", ar: "الشروق" },
        { key: "dhuhr", ar: "الظهر" },
        { key: "asr", ar: "العصر" },
        { key: "maghrib", ar: "المغرب" },
        { key: "isha", ar: "العشاء" }
      ];
      var html = "";
      var isFriday = now.getDay() === 5;
      names.forEach(function (n) {
        var t = times[n.key];
        var iq = n.key === "maghrib" ? t : iqamaFor(n.key.charAt(0).toUpperCase() + n.key.slice(1), t);
        html += '<tr class="' + (isFriday && n.key === "dhuhr" ? "today" : "") + '">' +
          '<td class="fw-bold">' + n.ar + '</td>' +
          '<td class="time-cell">' + (t ? PrayerCalc.format12(t) : "--:--") + '</td>' +
          '<td class="text-muted fw-semibold">' + (iq ? PrayerCalc.format12(iq) : "--:--") + '</td>' +
          '<td><span class="badge ' + (t ? "text-bg-success" : "text-bg-secondary") + '">' + (t ? "متاح" : "غير متاح") + '</span></td></tr>';
      });
      html += '<tr class="' + (isFriday ? "today" : "") + '"><td class="fw-bold">الجمعة</td>' +
        '<td class="time-cell" colspan="2">' + DATA.prayerSettings.jumuaTime + ' م</td>' +
        '<td><span class="badge text-bg-warning">خطبة</span></td></tr>';
      table.innerHTML = html;

      var pct = $("#prayerTodayPct");
      if (pct) pct.textContent = PrayerCalc.weekdayAr(now) + "، " + PrayerCalc.gregorianAr(now);
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
      localStorage.setItem("ibadah-city", state.cityId);
      fill();
      renderWeeklyTable();
    });
    if (methodSel) methodSel.addEventListener("change", function () {
      state.method = methodSel.value;
      localStorage.setItem("ibadah-method", state.method);
      fill();
      renderWeeklyTable();
    });
    if (madhabSel) madhabSel.addEventListener("change", function () {
      state.madhab = madhabSel.value;
      localStorage.setItem("ibadah-madhab", state.madhab);
      fill();
      renderWeeklyTable();
    });

    /* تحديث جدول الأسبوع أيضاً عند تغيير المدينة */
    if (citySel) citySel.addEventListener("change", renderWeeklyTable);
  }

  /* ---------------- تهيئة ---------------- */
  document.addEventListener("DOMContentLoaded", function () {
    applyTexts();
    renderDates();
    initNav();
    initHero();
    initReveal();
    initCounters();
    initAyat();
    initQuranAudio();
    initDonateForm();
    initContactForm();
    initNewsletter();
    initBackTop();
    renderCourses();
    renderCauses();
    renderEvents();
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
      renderCourses(); renderCauses(); renderEvents(); renderNews();
      renderPillars(); renderPricing(); renderEventDetail(); renderPrayerPage();
    },
    toast: toast
  };
})();
