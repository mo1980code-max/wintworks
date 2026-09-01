/* ============================================================
   Ibadah — Admin panel (demo, English) — vanilla JS
   Reads defaults from site-data.js, saves edits to localStorage
   ============================================================ */

(function () {
  "use strict";

  function $(s) { return document.querySelector(s); }
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }

  var data = window.getSiteData();
  var sessionKey = "ibadah-admin-ok";

  /* ---------------- Login ---------------- */
  $("#loginForm").addEventListener("submit", function (e) {
    e.preventDefault();
    var pin = $("#adminPin").value.trim();
    if (pin === "ibadah01") {
      sessionStorage.setItem(sessionKey, "1");
      showPanel();
      loadAll();
      toast("Welcome back to the admin panel");
    } else {
      toast("Incorrect access code (demo: ibadah01)", "error");
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
  if (sessionStorage.getItem(sessionKey) === "1") { showPanel(); loadAll(); }

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

  /* ---------------- Tabs ---------------- */
  $$(".admin-sidebar [data-tab]").forEach(function (link) {
    link.addEventListener("click", function (e) { e.preventDefault(); activate(link.getAttribute("data-tab")); });
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

  /* ---------------- Fill forms ---------------- */
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

  /* ---------------- Campaigns ---------------- */
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
        '<button class="btn-icon btn btn-warning btn-sm me-1" data-edit="' + i + '" title="Edit"><i class="fa-solid fa-pen"></i></button>' +
        '<button class="btn-icon btn btn-danger btn-sm" data-del="' + i + '" title="Delete"><i class="fa-solid fa-trash"></i></button></td>';
      tbody.appendChild(tr);
    });
    $$("#c-list [data-del]").forEach(function (b) {
      b.addEventListener("click", function () {
        data.causes.splice(parseInt(b.getAttribute("data-del"), 10), 1);
        renderCauses(); save();
        toast("Campaign deleted");
      });
    });
    $$("#c-list [data-edit]").forEach(function (b) {
      b.addEventListener("click", function () {
        var c = data.causes[parseInt(b.getAttribute("data-edit"), 10)];
        var newGoal = prompt("New goal ($)", c.goal);
        var newRaised = prompt("Amount raised ($)", c.raised);
        if (newGoal) c.goal = parseFloat(newGoal) || c.goal;
        if (newRaised) c.raised = parseFloat(newRaised) || c.raised;
        renderCauses(); save();
        toast("Campaign updated");
      });
    });
  }

  /* ---------------- Courses ---------------- */
  function renderCourses() {
    var tbody = $("#co-list");
    tbody.innerHTML = "";
    data.courses.forEach(function (c, i) {
      var tr = document.createElement("tr");
      tr.innerHTML = '<td><strong>' + c.title + '</strong><div class="small text-muted">' + c.category + '</div></td>' +
        '<td>' + c.teacher + '</td>' +
        '<td>$' + c.price + (c.priceFree ? ' <span class="badge text-bg-success">Free</span>' : '') + '</td>' +
        '<td>' + c.weeks + '</td>' +
        '<td><button class="btn-icon btn btn-danger btn-sm" data-del="' + i + '"><i class="fa-solid fa-trash"></i></button></td>';
      tbody.appendChild(tr);
    });
    $$("#co-list [data-del]").forEach(function (b) {
      b.addEventListener("click", function () {
        data.courses.splice(parseInt(b.getAttribute("data-del"), 10), 1);
        renderCourses(); save();
        toast("Course deleted");
      });
    });
  }

  /* ---------------- Events ---------------- */
  function renderEvents() {
    var tbody = $("#e-list");
    tbody.innerHTML = "";
    data.events.forEach(function (ev, i) {
      var d = new Date(ev.date);
      var tr = document.createElement("tr");
      tr.innerHTML = '<td><strong>' + ev.title + '</strong><div class="small text-muted">' + ev.category + '</div></td>' +
        '<td>' + d.toLocaleDateString("en-US") + '</td>' +
        '<td>' + ev.location + '</td>' +
        '<td><button class="btn-icon btn btn-danger btn-sm" data-del="' + i + '"><i class="fa-solid fa-trash"></i></button></td>';
      tbody.appendChild(tr);
    });
    $$("#e-list [data-del]").forEach(function (b) {
      b.addEventListener("click", function () {
        data.events.splice(parseInt(b.getAttribute("data-del"), 10), 1);
        renderEvents(); save();
        toast("Event deleted");
      });
    });
  }

  /* ---------------- Donation records ---------------- */
  function renderDonations() {
    var tbody = $("#d-list");
    tbody.innerHTML = "";
    var records = [];
    try { records = JSON.parse(localStorage.getItem("ibadah-donations") || "[]"); } catch (e) { records = []; }
    if (!records.length) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">No donations recorded yet — try the site donation form.</td></tr>';
      return;
    }
    records.slice().reverse().forEach(function (r) {
      var tr = document.createElement("tr");
      tr.innerHTML = '<td>' + r.name + '</td><td>' + r.cause + '</td>' +
        '<td class="fw-bold text-gold">$' + r.amount.toLocaleString("en-US") + '</td>' +
        '<td>' + new Date(r.date).toLocaleString("en-US") + '</td>';
      tbody.appendChild(tr);
    });
  }

  /* ---------------- Save & load ---------------- */
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
    toast("Changes saved — reload the site to see them");
  });

  $("#resetAllBtn").addEventListener("click", function () {
    if (!confirm("This will restore all default settings. Are you sure?")) return;
    window.resetSiteData();
    data = window.getSiteData();
    loadAll();
    toast("Defaults restored");
  });

  function loadAll() {
    fillGeneral();
    fillPrayer();
    renderCauses();
    renderCourses();
    renderEvents();
    renderDonations();
  }

  /* ---------------- Add items ---------------- */
  $("#c-addBtn").addEventListener("click", function () {
    var title = $("#c-newTitle").value.trim();
    if (!title) { toast("Please enter a campaign title", "error"); return; }
    data.causes.push({
      id: "cause-" + Date.now(),
      title: title,
      category: $("#c-newCat").value.trim() || "Charity",
      goal: parseFloat($("#c-newGoal").value) || 1000,
      raised: parseFloat($("#c-newRaised").value) || 0,
      img: $("#c-newImg").value.trim() || "assets/img/cause-food.jpg",
      desc: $("#c-newDesc").value.trim() || title
    });
    renderCauses(); save();
    toast("Campaign added successfully");
    ["c-newTitle","c-newCat","c-newGoal","c-newRaised","c-newImg","c-newDesc"].forEach(function (id) { $("#" + id).value = ""; });
  });

  $("#co-addBtn").addEventListener("click", function () {
    var title = $("#co-newTitle").value.trim();
    if (!title) { toast("Please enter a course title", "error"); return; }
    data.courses.push({
      id: "course-" + Date.now(),
      title: title,
      category: $("#co-newCat").value.trim() || "Course",
      price: parseFloat($("#co-newPrice").value) || 0,
      priceFree: false,
      weeks: parseInt($("#co-newWeeks").value, 10) || 8,
      enroll: 0,
      img: $("#co-newImg").value.trim() || "assets/img/course-quran.jpg",
      teacher: $("#co-newTeacher").value.trim() || "Center Instructor",
      teacherRole: "Instructor",
      teacherImg: $("#co-newTImg").value.trim() || "assets/img/about-manuscript.jpg",
      desc: $("#co-newDesc").value.trim() || title
    });
    renderCourses(); save();
    toast("Course added successfully");
    ["co-newTitle","co-newCat","co-newPrice","co-newWeeks","co-newImg","co-newTeacher","co-newTImg","co-newDesc"].forEach(function (id) { $("#" + id).value = ""; });
  });

  $("#e-addBtn").addEventListener("click", function () {
    var title = $("#e-newTitle").value.trim();
    if (!title) { toast("Please enter an event title", "error"); return; }
    var dateVal = $("#e-newDate").value;
    var speaker = $("#e-newGuest").value.trim() || "Guest Speaker";
    data.events.push({
      id: "event-" + Date.now(),
      title: title,
      category: $("#e-newCat").value.trim() || "Event",
      date: dateVal ? new Date(dateVal).toISOString() : new Date(Date.now() + 86400000).toISOString(),
      location: $("#e-newLoc").value.trim() || "Main Center Building",
      guests: speaker,
      guestRole: $("#e-newOrg").value.trim() || "Guest",
      guestBio: "Speaker at Ibadah Islamic Center.",
      organizer: $("#e-newOrg").value.trim() || "Events Committee",
      img: $("#e-newImg").value.trim() || "assets/img/hero-2.jpg",
      desc: $("#e-newDesc").value.trim() || title
    });
    renderEvents(); save();
    toast("Event added successfully");
    ["e-newTitle","e-newCat","e-newDate","e-newLoc","e-newGuest","e-newOrg","e-newImg","e-newDesc"].forEach(function (id) { $("#" + id).value = ""; });
  });
})();
