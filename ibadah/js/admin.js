/* ============================================================
   Ibadah — Admin panel (demo) — vanilla JS
   يقرأ البيانات من site-data.js ويحفظ التعديلات في localStorage
   ============================================================ */

(function () {
  "use strict";

  function $(s) { return document.querySelector(s); }
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }

  var data = window.getSiteData();
  var sessionKey = "ibadah-admin-ok";

  /* ---------------- الدخول ---------------- */
  $("#loginForm").addEventListener("submit", function (e) {
    e.preventDefault();
    var pin = $("#adminPin").value.trim();
    if (pin === "ibadah01") {
      sessionStorage.setItem(sessionKey, "1");
      showPanel();
      loadAll();
      toast("مرحباً بك في لوحة الإدارة");
    } else {
      toast("رمز الدخول غير صحيح (تجريبي: ibadah01)", "error");
    }
  });

  $("#logoutBtn").addEventListener("click", function () {
    sessionStorage.removeItem(sessionKey);
    $("#adminLogin").classList.remove("d-none");
    $("#adminPanel").classList.add("d-none");
  });

  function showPanel() {
    $("#adminLogin").classList.add("d-none");
    $("#adminPanel").classList.remove("d-none");
  }

  if (sessionStorage.getItem(sessionKey) === "1") {
    showPanel();
    loadAll();
  }

  function toast(msg, type) {
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
    el.innerHTML = '<div class="d-flex"><div class="toast-body fw-semibold">' + msg +
      '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    zone.appendChild(el);
    var t = new bootstrap.Toast(el, { delay: 3500 });
    t.show();
    el.addEventListener("hidden.bs.toast", function () { el.remove(); });
  }

  /* ---------------- تبويبات ---------------- */
  $$(".admin-sidebar [data-tab]").forEach(function (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      activate(link.getAttribute("data-tab"));
    });
  });
  $("#mobileTab").addEventListener("change", function () { activate(this.value); });

  function activate(name) {
    $$(".admin-tab").forEach(function (t) { t.classList.add("d-none"); });
    $("#tab-" + name).classList.remove("d-none");
    $$(".admin-sidebar [data-tab]").forEach(function (l) {
      l.classList.toggle("active", l.getAttribute("data-tab") === name);
    });
    $("#mobileTab").value = name;
    if (name === "donations") renderDonations();
  }

  /* ---------------- تعبئة النماذج ---------------- */
  function fillGeneral() {
    var g = data.general;
    $("#g-siteName").value = g.siteName;
    $("#g-siteNameEn").value = g.siteNameEn;
    $("#g-phone").value = g.phone;
    $("#g-email").value = g.email;
    $("#g-address").value = g.address;
    $("#g-workingHours").value = g.workingHours;
    $("#g-heroTitle").value = g.heroTitle;
    $("#g-heroSubtitle").value = g.heroSubtitle;
    $("#g-heroCta1").value = g.heroCta1;
    $("#g-heroCta2").value = g.heroCta2;
    $("#g-aboutText").value = g.aboutText;
    $("#g-aboutText2").value = g.aboutText2;
  }

  function fillPrayer() {
    var ps = data.prayerSettings;
    var citySel = $("#p-defaultCity");
    citySel.innerHTML = "";
    data.cities.forEach(function (c) {
      var o = document.createElement("option");
      o.value = c.id; o.textContent = c.name;
      if (c.id === ps.defaultCityId) o.selected = true;
      citySel.appendChild(o);
    });
    var meth = $("#p-method");
    meth.innerHTML = "";
    Object.keys(PrayerCalc.METHODS).forEach(function (k) {
      var o = document.createElement("option");
      o.value = k; o.textContent = PrayerCalc.METHODS[k].name;
      if (k === ps.method) o.selected = true;
      meth.appendChild(o);
    });
    $("#p-madhab").value = ps.asrMadhab;
    $("#p-jumua").value = ps.jumuaTime;
    ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"].forEach(function (k) {
      $("#p-iq-" + k).value = ps.iqamaOffsets[k] || 0;
    });
  }

  /* ---------------- حملات ---------------- */
  function renderCauses() {
    var tbody = $("#c-list");
    tbody.innerHTML = "";
    data.causes.forEach(function (c, i) {
      var pct = Math.round((c.raised / c.goal) * 100);
      var tr = document.createElement("tr");
      tr.innerHTML = '<td class="fw-semibold">' + c.title + '</td>' +
        '<td>$' + c.goal.toLocaleString("en-US") + '</td>' +
        '<td>$' + c.raised.toLocaleString("en-US") + '</td>' +
        '<td><div class="cause-progress" style="width:110px"><div class="bar" style="width:' + pct + '%"></div></div></td>' +
        '<td class="text-nowrap">' +
        '<button class="btn-icon btn btn-warning btn-sm me-1" data-edit="' + i + '" title="تعديل"><i class="fa-solid fa-pen"></i></button>' +
        '<button class="btn-icon btn btn-danger btn-sm" data-del="' + i + '" title="حذف"><i class="fa-solid fa-trash"></i></button></td>';
      tbody.appendChild(tr);
    });
    $$("#c-list [data-del]").forEach(function (b) {
      b.addEventListener("click", function () {
        data.causes.splice(parseInt(b.getAttribute("data-del"), 10), 1);
        renderCauses(); save();
        toast("تم حذف الحملة");
      });
    });
    $$("#c-list [data-edit]").forEach(function (b) {
      b.addEventListener("click", function () {
        var c = data.causes[parseInt(b.getAttribute("data-edit"), 10)];
        var newGoal = prompt("الهدف الجديد ($)", c.goal);
        var newRaised = prompt("المبلغ المجموع ($)", c.raised);
        if (newGoal) c.goal = parseFloat(newGoal) || c.goal;
        if (newRaised) c.raised = parseFloat(newRaised) || c.raised;
        renderCauses(); save();
        toast("تم تحديث الحملة");
      });
    });
  }

  /* ---------------- دورات ---------------- */
  function renderCourses() {
    var tbody = $("#co-list");
    tbody.innerHTML = "";
    data.courses.forEach(function (c, i) {
      var tr = document.createElement("tr");
      tr.innerHTML = '<td><strong>' + c.title + '</strong><div class="small text-muted">' + c.category + '</div></td>' +
        '<td>' + c.teacher + '</td>' +
        '<td>$' + c.price + (c.priceFree ? ' <span class="badge text-bg-success">مجاني</span>' : '') + '</td>' +
        '<td>' + c.weeks + '</td>' +
        '<td><button class="btn-icon btn btn-danger btn-sm" data-del="' + i + '"><i class="fa-solid fa-trash"></i></button></td>';
      tbody.appendChild(tr);
    });
    $$("#co-list [data-del]").forEach(function (b) {
      b.addEventListener("click", function () {
        data.courses.splice(parseInt(b.getAttribute("data-del"), 10), 1);
        renderCourses(); save();
        toast("تم حذف الدورة");
      });
    });
  }

  /* ---------------- فعاليات ---------------- */
  function renderEvents() {
    var tbody = $("#e-list");
    tbody.innerHTML = "";
    data.events.forEach(function (ev, i) {
      var d = new Date(ev.date);
      var tr = document.createElement("tr");
      tr.innerHTML = '<td><strong>' + ev.title + '</strong><div class="small text-muted">' + ev.category + '</div></td>' +
        '<td>' + d.toLocaleDateString("ar") + '</td>' +
        '<td>' + ev.location + '</td>' +
        '<td><button class="btn-icon btn btn-danger btn-sm" data-del="' + i + '"><i class="fa-solid fa-trash"></i></button></td>';
      tbody.appendChild(tr);
    });
    $$("#e-list [data-del]").forEach(function (b) {
      b.addEventListener("click", function () {
        data.events.splice(parseInt(b.getAttribute("data-del"), 10), 1);
        renderEvents(); save();
        toast("تم حذف الفعالية");
      });
    });
  }

  /* ---------------- تبرعات ---------------- */
  function renderDonations() {
    var tbody = $("#d-list");
    tbody.innerHTML = "";
    var records = [];
    try { records = JSON.parse(localStorage.getItem("ibadah-donations") || "[]"); } catch (e) { records = []; }
    if (!records.length) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">لا توجد تبرعات مسجلة بعد — جرّب نموذج التبرع في الموقع.</td></tr>';
      return;
    }
    records.slice().reverse().forEach(function (r) {
      var tr = document.createElement("tr");
      tr.innerHTML = '<td>' + r.name + '</td><td>' + r.cause + '</td>' +
        '<td class="fw-bold text-gold">$' + r.amount.toLocaleString("en-US") + '</td>' +
        '<td>' + new Date(r.date).toLocaleString("ar") + '</td>';
      tbody.appendChild(tr);
    });
  }

  /* ---------------- حفظ وقراءة ---------------- */
  function collect() {
    data.general.siteName = $("#g-siteName").value;
    data.general.siteNameEn = $("#g-siteNameEn").value;
    data.general.phone = $("#g-phone").value;
    data.general.email = $("#g-email").value;
    data.general.address = $("#g-address").value;
    data.general.workingHours = $("#g-workingHours").value;
    data.general.heroTitle = $("#g-heroTitle").value;
    data.general.heroSubtitle = $("#g-heroSubtitle").value;
    data.general.heroCta1 = $("#g-heroCta1").value;
    data.general.heroCta2 = $("#g-heroCta2").value;
    data.general.aboutText = $("#g-aboutText").value;
    data.general.aboutText2 = $("#g-aboutText2").value;

    data.prayerSettings.defaultCityId = $("#p-defaultCity").value;
    data.prayerSettings.method = $("#p-method").value;
    data.prayerSettings.asrMadhab = $("#p-madhab").value;
    data.prayerSettings.jumuaTime = $("#p-jumua").value;
    ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"].forEach(function (k) {
      data.prayerSettings.iqamaOffsets[k] = parseInt($("#p-iq-" + k).value, 10) || 0;
    });
  }

  function save() {
    window.saveSiteData(data);
    if (window.IBADAH_UI && window.IBADAH_UI.refresh) window.IBADAH_UI.refresh();
  }

  $("#saveAllBtn").addEventListener("click", function () {
    collect();
    save();
    toast("تم حفظ التعديلات بنجاح — أعد تحميل الموقع لرؤيتها");
  });

  $("#resetAllBtn").addEventListener("click", function () {
    if (!confirm("سيتم استعادة جميع الإعدادات الافتراضية. هل أنت متأكد؟")) return;
    window.resetSiteData();
    data = window.getSiteData();
    loadAll();
    toast("تمت الاستعادة للوضع الافتراضي");
  });

  function loadAll() {
    fillGeneral();
    fillPrayer();
    renderCauses();
    renderCourses();
    renderEvents();
    renderDonations();
  }

  /* ---------------- إضافة عناصر ---------------- */
  $("#c-addBtn").addEventListener("click", function () {
    var title = $("#c-newTitle").value.trim();
    if (!title) { toast("أدخل عنوان الحملة", "error"); return; }
    data.causes.push({
      id: "cause-" + Date.now(),
      title: title,
      category: $("#c-newCat").value.trim() || "خير",
      goal: parseFloat($("#c-newGoal").value) || 1000,
      raised: parseFloat($("#c-newRaised").value) || 0,
      img: $("#c-newImg").value.trim() || "assets/img/cause-food.jpg",
      desc: $("#c-newDesc").value.trim() || title
    });
    renderCauses(); save();
    toast("تمت إضافة الحملة بنجاح");
    ["c-newTitle","c-newCat","c-newGoal","c-newRaised","c-newImg","c-newDesc"].forEach(function (id) { $("#" + id).value = ""; });
  });

  $("#co-addBtn").addEventListener("click", function () {
    var title = $("#co-newTitle").value.trim();
    if (!title) { toast("أدخل عنوان الدورة", "error"); return; }
    data.courses.push({
      id: "course-" + Date.now(),
      title: title,
      category: $("#co-newCat").value.trim() || "دورة",
      price: parseFloat($("#co-newPrice").value) || 0,
      priceFree: false,
      weeks: parseInt($("#co-newWeeks").value, 10) || 8,
      enroll: 0,
      img: $("#co-newImg").value.trim() || "assets/img/course-quran.jpg",
      teacher: $("#co-newTeacher").value.trim() || "مدرّس المركز",
      teacherRole: "مدرّس",
      teacherImg: $("#co-newTImg").value.trim() || "assets/img/about-manuscript.jpg",
      desc: $("#co-newDesc").value.trim() || title
    });
    renderCourses(); save();
    toast("تمت إضافة الدورة بنجاح");
    ["co-newTitle","co-newCat","co-newPrice","co-newWeeks","co-newImg","co-newTeacher","co-newTImg","co-newDesc"].forEach(function (id) { $("#" + id).value = ""; });
  });

  $("#e-addBtn").addEventListener("click", function () {
    var title = $("#e-newTitle").value.trim();
    if (!title) { toast("أدخل عنوان الفعالية", "error"); return; }
    var dateVal = $("#e-newDate").value;
    data.events.push({
      id: "event-" + Date.now(),
      title: title,
      category: $("#e-newCat").value.trim() || "فعالية",
      date: dateVal ? new Date(dateVal).toISOString() : new Date(Date.now() + 86400000).toISOString(),
      location: $("#e-newLoc").value.trim() || "المقر الرئيسي للمركز",
      guests: $("#e-newGuest").value.trim() || "ضيف المركز",
      organizer: $("#e-newOrg").value.trim() || "لجنة الفعاليات",
      img: $("#e-newImg").value.trim() || "assets/img/hero-2.jpg",
      desc: $("#e-newDesc").value.trim() || title
    });
    renderEvents(); save();
    toast("تمت إضافة الفعالية بنجاح");
    ["e-newTitle","e-newCat","e-newDate","e-newLoc","e-newGuest","e-newOrg","e-newImg","e-newDesc"].forEach(function (id) { $("#" + id).value = ""; });
  });
})();
