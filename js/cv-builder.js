"use strict";

/* ============================================================
   WintWorks — CV Builder logic
   - Split-screen live preview
   - 3 templates (Executive / Tech / Creative) with data-preserving switch
   - Dynamic experience/education repeaters
   - localStorage persistence
   - Fit-to-width scaling (no overlap, no dead space)
   - PDF export via html2pdf (fallback to window.print)
   ============================================================ */

const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nl2br = (s) => esc(s).replace(/\n/g, "<br>");

const STORE_KEY = "ww:cv:v2";
let currentTpl = "executive";

/* -------------------- state -------------------- */
const defaults = {
  tpl: "executive",
  name: "محمد أحمد",
  jobTitle: "مهندس برمجيات",
  email: "mohammed@example.com",
  phone: "+962 79 000 0000",
  location: "عمّان، الأردن",
  link: "linkedin.com/in/username",
  summary: "مهندس برمجيات بخبرة تزيد عن 5 سنوات في بناء تطبيقات ويب قابلة للتوسّع. شغوف بحلّ المشكلات المعقّدة ورفع كفاءة الأنظمة، مع سجلّ حافل في تحسين الأداء وقيادة الفرق التقنية.",
  skills: "JavaScript, Python, React, Node.js, إدارة المشاريع, العمل بمنهجية Agile",
  langs: "العربية (اللغة الأم), الإنجليزية (طليق), الألمانية (B2)",
  experiences: [
    { id: 1, title: "مهندس برمجيات أول", company: "شركة الحلول التقنية", date: "يناير 2021 - الآن",
      desc: "- قيادة تطوير وصيانة تطبيقات ويب قابلة للتوسّع.\n- التعاون مع فرق متعددة التخصصات لتصميم مزايا جديدة.\n- تحسين أداء التطبيق بنسبة 30%." },
  ],
  educations: [
    { id: 2, degree: "بكالوريوس علوم الحاسوب", school: "الجامعة الأردنية", date: "2016 - 2020",
      desc: "تخرّج بمرتبة الشرف مع تركيز على هندسة البرمجيات والخوارزميات." },
  ],
};

let experiences = [];
let educations = [];
let uid = Date.now();

/* -------------------- persistence -------------------- */
function saveState() {
  const data = {
    tpl: currentTpl,
    name: $("#cvName").value, jobTitle: $("#cvJobTitle").value,
    email: $("#cvEmail").value, phone: $("#cvPhone").value,
    location: $("#cvLocation").value, link: $("#cvLink").value,
    summary: $("#cvSummary").value, skills: $("#cvSkills").value, langs: $("#cvLangs").value,
    experiences, educations,
  };
  try { localStorage.setItem(STORE_KEY, JSON.stringify(data)); } catch (e) {}
}

function loadState() {
  let data = null;
  try { data = JSON.parse(localStorage.getItem(STORE_KEY)); } catch (e) {}
  const d = data && typeof data === "object" ? data : defaults;

  $("#cvName").value = d.name ?? defaults.name;
  $("#cvJobTitle").value = d.jobTitle ?? defaults.jobTitle;
  $("#cvEmail").value = d.email ?? defaults.email;
  $("#cvPhone").value = d.phone ?? defaults.phone;
  $("#cvLocation").value = d.location ?? defaults.location;
  $("#cvLink").value = d.link ?? defaults.link;
  $("#cvSummary").value = d.summary ?? defaults.summary;
  $("#cvSkills").value = d.skills ?? defaults.skills;
  $("#cvLangs").value = d.langs ?? defaults.langs;

  experiences = Array.isArray(d.experiences) && d.experiences.length
    ? d.experiences.map((e) => ({ ...e, id: e.id ?? ++uid }))
    : defaults.experiences.map((e) => ({ ...e }));
  educations = Array.isArray(d.educations) && d.educations.length
    ? d.educations.map((e) => ({ ...e, id: e.id ?? ++uid }))
    : defaults.educations.map((e) => ({ ...e }));

  currentTpl = d.tpl && ["executive", "tech", "creative"].includes(d.tpl) ? d.tpl : "executive";
}

/* -------------------- editor repeaters -------------------- */
function renderExpForm() {
  const c = $("#expContainer");
  c.innerHTML = experiences.map((exp) => `
    <div class="repeater-item" data-id="${exp.id}">
      <div class="repeater-head">
        <b>خبرة</b>
        <button type="button" class="remove-btn" data-remove-exp="${exp.id}">✕ حذف</button>
      </div>
      <div class="fg">
        <label>المسمى الوظيفي</label>
        <input type="text" value="${esc(exp.title)}" data-exp="${exp.id}" data-field="title" placeholder="مثال: مدير مشاريع">
      </div>
      <div class="fg">
        <label>الشركة / جهة العمل</label>
        <input type="text" value="${esc(exp.company)}" data-exp="${exp.id}" data-field="company" placeholder="مثال: شركة التقنية المتقدمة">
      </div>
      <div class="fg">
        <label>الفترة الزمنية</label>
        <input type="text" value="${esc(exp.date)}" data-exp="${exp.id}" data-field="date" placeholder="مثال: يناير 2021 - الآن">
      </div>
      <div class="fg">
        <label>الوصف والإنجازات</label>
        <textarea rows="3" data-exp="${exp.id}" data-field="desc" placeholder="استخدم نقاطاً تبدأ بـ (-) وأبرز إنجازاً قابلاً للقياس، مثل: خفّضت التكاليف 20%.">${esc(exp.desc)}</textarea>
      </div>
    </div>`).join("");
}

function renderEduForm() {
  const c = $("#eduContainer");
  c.innerHTML = educations.map((edu) => `
    <div class="repeater-item" data-id="${edu.id}">
      <div class="repeater-head">
        <b>مؤهل</b>
        <button type="button" class="remove-btn" data-remove-edu="${edu.id}">✕ حذف</button>
      </div>
      <div class="fg">
        <label>الشهادة / الدرجة</label>
        <input type="text" value="${esc(edu.degree)}" data-edu="${edu.id}" data-field="degree" placeholder="مثال: بكالوريوس علوم الحاسوب">
      </div>
      <div class="fg">
        <label>الجامعة / المؤسسة</label>
        <input type="text" value="${esc(edu.school)}" data-edu="${edu.id}" data-field="school" placeholder="مثال: الجامعة الأردنية">
      </div>
      <div class="fg">
        <label>الفترة الزمنية</label>
        <input type="text" value="${esc(edu.date)}" data-edu="${edu.id}" data-field="date" placeholder="مثال: 2016 - 2020">
      </div>
      <div class="fg">
        <label>تفاصيل إضافية (اختياري)</label>
        <textarea rows="2" data-edu="${edu.id}" data-field="desc" placeholder="مثال: تخرّج بمرتبة الشرف، معدّل تراكمي مرتفع.">${esc(edu.desc)}</textarea>
      </div>
    </div>`).join("");
}

/* delegated input for repeaters */
function onRepeaterInput(e) {
  const el = e.target;
  const expId = el.getAttribute("data-exp");
  const eduId = el.getAttribute("data-edu");
  const field = el.getAttribute("data-field");
  if (expId) {
    const item = experiences.find((x) => String(x.id) === expId);
    if (item) item[field] = el.value;
  } else if (eduId) {
    const item = educations.find((x) => String(x.id) === eduId);
    if (item) item[field] = el.value;
  } else return;
  renderPreview(); saveState();
}

function onRepeaterClick(e) {
  const rmExp = e.target.getAttribute("data-remove-exp");
  const rmEdu = e.target.getAttribute("data-remove-edu");
  if (rmExp) { experiences = experiences.filter((x) => String(x.id) !== rmExp); renderExpForm(); renderPreview(); saveState(); }
  if (rmEdu) { educations = educations.filter((x) => String(x.id) !== rmEdu); renderEduForm(); renderPreview(); saveState(); }
}

/* -------------------- helpers -------------------- */
function val(id) { return $(id).value.trim(); }
function contactParts() {
  return [
    { v: val("#cvEmail"), ic: "✉" },
    { v: val("#cvPhone"), ic: "☎" },
    { v: val("#cvLocation"), ic: "📍" },
    { v: val("#cvLink"), ic: "🔗" },
  ].filter((x) => x.v);
}
function skillsArr() { return val("#cvSkills").split(",").map((s) => s.trim()).filter(Boolean); }
function langsArr() { return val("#cvLangs").split(",").map((s) => s.trim()).filter(Boolean); }

/* -------------------- template renderers -------------------- */
function renderExecutive() {
  const contact = contactParts().map((c) => `<span>${c.ic} ${esc(c.v)}</span>`).join("");
  let h = `
    <div class="cv-header">
      <h1 class="cv-name">${esc(val("#cvName"))}</h1>
      <div class="cv-job-title">${esc(val("#cvJobTitle"))}</div>
      <div class="cv-contact">${contact}</div>
    </div>`;

  if (val("#cvSummary")) {
    h += `<div class="cv-section"><div class="cv-sec-title">الملخص المهني</div>
      <div class="cv-item-desc">${nl2br(val("#cvSummary"))}</div></div>`;
  }
  if (experiences.length) {
    h += `<div class="cv-section"><div class="cv-sec-title">الخبرات المهنية</div>`;
    experiences.forEach((e) => {
      h += `<div class="cv-item">
        <div class="cv-item-title"><span>${esc(e.title)}</span><span class="date">${esc(e.date)}</span></div>
        <div class="cv-item-sub">${esc(e.company)}</div>
        ${e.desc ? `<div class="cv-item-desc">${nl2br(e.desc)}</div>` : ""}
      </div>`;
    });
    h += `</div>`;
  }
  if (educations.length) {
    h += `<div class="cv-section"><div class="cv-sec-title">التعليم</div>`;
    educations.forEach((e) => {
      h += `<div class="cv-item">
        <div class="cv-item-title"><span>${esc(e.degree)}</span><span class="date">${esc(e.date)}</span></div>
        <div class="cv-item-sub">${esc(e.school)}</div>
        ${e.desc ? `<div class="cv-item-desc">${nl2br(e.desc)}</div>` : ""}
      </div>`;
    });
    h += `</div>`;
  }
  if (skillsArr().length) {
    h += `<div class="cv-section"><div class="cv-sec-title">المهارات</div>
      <div class="cv-tags">${skillsArr().map((s) => `<span class="cv-tag">${esc(s)}</span>`).join("")}</div></div>`;
  }
  if (langsArr().length) {
    h += `<div class="cv-section"><div class="cv-sec-title">اللغات</div>
      <div class="cv-langs">${langsArr().map((l) => esc(l)).join(" &nbsp;•&nbsp; ")}</div></div>`;
  }
  return h;
}

function renderTech() {
  const email = val("#cvEmail"), phone = val("#cvPhone"), loc = val("#cvLocation"), link = val("#cvLink");
  // sidebar
  let side = `
    <h1 class="cv-name">${esc(val("#cvName"))}</h1>
    <div class="cv-job-title">${esc(val("#cvJobTitle"))}</div>
    <div class="side-title">التواصل</div>`;
  if (email) side += `<div class="contact-item"><span class="ic">✉</span><span dir="ltr">${esc(email)}</span></div>`;
  if (phone) side += `<div class="contact-item"><span class="ic">☎</span><span dir="ltr">${esc(phone)}</span></div>`;
  if (loc)   side += `<div class="contact-item"><span class="ic">📍</span><span>${esc(loc)}</span></div>`;
  if (link)  side += `<div class="contact-item"><span class="ic">🔗</span><span dir="ltr">${esc(link)}</span></div>`;

  const skills = skillsArr();
  if (skills.length) {
    side += `<div class="side-title">المهارات</div><ul class="skills-list">`;
    skills.forEach((s, i) => {
      const pct = 70 + ((i * 7) % 26); // 70–95% varied, purely decorative
      side += `<li>${esc(s)}<div class="bar"><span style="width:${pct}%"></span></div></li>`;
    });
    side += `</ul>`;
  }
  const langs = langsArr();
  if (langs.length) {
    side += `<div class="side-title">اللغات</div><ul class="lang-list">`;
    langs.forEach((l) => (side += `<li>${esc(l)}</li>`));
    side += `</ul>`;
  }

  // main
  let main = "";
  if (val("#cvSummary")) {
    main += `<div class="cv-section"><div class="main-title">نبذة مهنية</div>
      <div class="profile-text">${nl2br(val("#cvSummary"))}</div></div>`;
  }
  if (experiences.length) {
    main += `<div class="cv-section"><div class="main-title">الخبرات المهنية</div>`;
    experiences.forEach((e) => {
      main += `<div class="cv-item">
        <div class="cv-item-title">${esc(e.title)}</div>
        <div class="cv-item-sub">${esc(e.company)} — ${esc(e.date)}</div>
        ${e.desc ? `<div class="cv-item-desc">${nl2br(e.desc)}</div>` : ""}
      </div>`;
    });
    main += `</div>`;
  }
  if (educations.length) {
    main += `<div class="cv-section"><div class="main-title">التعليم</div>`;
    educations.forEach((e) => {
      main += `<div class="cv-item">
        <div class="cv-item-title">${esc(e.degree)}</div>
        <div class="cv-item-sub">${esc(e.school)} — ${esc(e.date)}</div>
        ${e.desc ? `<div class="cv-item-desc">${nl2br(e.desc)}</div>` : ""}
      </div>`;
    });
    main += `</div>`;
  }
  return `<div class="tech-side">${side}</div><div class="tech-main">${main}</div>`;
}

function renderCreative() {
  const name = esc(val("#cvName"));
  const contact = contactParts().map((c) => `<span>${esc(c.v)}</span>`).join('<span class="dot">•</span>');
  let h = `
    <div class="cv-header">
      <h1 class="cv-name">${name}</h1>
      <div class="cv-job-title">${esc(val("#cvJobTitle"))}</div>
      <div class="cv-contact">${contact}</div>
    </div>`;
  if (val("#cvSummary")) {
    h += `<div class="cv-section"><div class="cv-sec-title">نبذة</div>
      <div class="cv-item-desc">${nl2br(val("#cvSummary"))}</div></div>`;
  }
  if (experiences.length) {
    h += `<div class="cv-section"><div class="cv-sec-title">الخبرات</div>`;
    experiences.forEach((e) => {
      h += `<div class="cv-item">
        <div class="cv-item-title">${esc(e.title)}</div>
        <div class="cv-item-sub">${esc(e.company)}<span class="dot">•</span>${esc(e.date)}</div>
        ${e.desc ? `<div class="cv-item-desc">${nl2br(e.desc)}</div>` : ""}
      </div>`;
    });
    h += `</div>`;
  }
  if (educations.length) {
    h += `<div class="cv-section"><div class="cv-sec-title">التعليم</div>`;
    educations.forEach((e) => {
      h += `<div class="cv-item">
        <div class="cv-item-title">${esc(e.degree)}</div>
        <div class="cv-item-sub">${esc(e.school)}<span class="dot">•</span>${esc(e.date)}</div>
        ${e.desc ? `<div class="cv-item-desc">${nl2br(e.desc)}</div>` : ""}
      </div>`;
    });
    h += `</div>`;
  }
  if (skillsArr().length) {
    h += `<div class="cv-section"><div class="cv-sec-title">المهارات</div>
      <div class="cv-tags">${skillsArr().map((s) => `<span class="cv-tag">${esc(s)}</span>`).join("")}</div></div>`;
  }
  if (langsArr().length) {
    h += `<div class="cv-section"><div class="cv-sec-title">اللغات</div>
      <div class="cv-langs">${langsArr().map((l) => esc(l)).join(" &nbsp;•&nbsp; ")}</div></div>`;
  }
  return h;
}

const RENDERERS = { executive: renderExecutive, tech: renderTech, creative: renderCreative };

function renderPreview() {
  const paper = $("#cvPaper");
  paper.className = "cv-paper temp-" + currentTpl;
  paper.innerHTML = (RENDERERS[currentTpl] || renderExecutive)();
  fitPaper();
}

/* -------------------- fit-to-width scaling -------------------- */
function fitPaper() {
  const scaler = $("#cvScaler");
  const paper = $("#cvPaper");
  if (!scaler || !paper) return;
  paper.style.setProperty("--cv-scale", "1");
  const available = scaler.clientWidth;
  const paperWidth = paper.offsetWidth;
  if (!paperWidth) return;
  const scale = Math.min(1, available / paperWidth);
  paper.style.setProperty("--cv-scale", String(scale));
  scaler.style.height = paper.offsetHeight * scale + "px";
}

/* -------------------- template switcher -------------------- */
function setTemplate(tpl) {
  if (!RENDERERS[tpl]) return;
  currentTpl = tpl;
  $$("#templateBtns .tpl-btn").forEach((b) =>
    b.classList.toggle("is-active", b.getAttribute("data-tpl") === tpl));
  renderPreview();      // data is preserved — only the layout changes
  saveState();
}

/* -------------------- PDF export -------------------- */
function exportPDF() {
  const paper = $("#cvPaper");
  const btn = $("#downloadBtn");
  const label = $("#downloadLabel");
  const filename = (val("#cvName") || "resume").replace(/\s+/g, "_") + "_CV.pdf";

  if (typeof window.html2pdf === "undefined") { window.print(); return; }

  btn.disabled = true;
  const prev = label.textContent;
  label.textContent = "جارٍ التحضير...";

  // Render at full scale in a detached clone so the PDF is crisp & 1:1.
  const clone = paper.cloneNode(true);
  clone.classList.add("pdf-rendering");
  clone.style.setProperty("--cv-scale", "1");
  clone.style.transform = "none";
  clone.style.boxShadow = "none";
  const holder = document.createElement("div");
  holder.style.cssText = "position:fixed;top:0;right:0;z-index:-1;opacity:0;pointer-events:none;";
  holder.appendChild(clone);
  document.body.appendChild(holder);

  const opt = {
    margin: 0,
    filename,
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff", windowWidth: clone.scrollWidth },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    pagebreak: { mode: ["css", "legacy"] },
  };

  window.html2pdf().set(opt).from(clone).save()
    .then(() => { cleanup(); })
    .catch(() => { cleanup(); window.print(); });

  function cleanup() {
    holder.remove();
    btn.disabled = false;
    label.textContent = prev;
  }
}

/* -------------------- init -------------------- */
function bindMainInputs() {
  ["#cvName","#cvJobTitle","#cvEmail","#cvPhone","#cvLocation","#cvLink","#cvSummary","#cvSkills","#cvLangs"]
    .forEach((id) => $(id).addEventListener("input", () => { renderPreview(); saveState(); }));
}

document.addEventListener("DOMContentLoaded", () => {
  loadState();
  renderExpForm();
  renderEduForm();
  bindMainInputs();

  $("#expContainer").addEventListener("input", onRepeaterInput);
  $("#eduContainer").addEventListener("input", onRepeaterInput);
  $("#expContainer").addEventListener("click", onRepeaterClick);
  $("#eduContainer").addEventListener("click", onRepeaterClick);

  $("#addExpBtn").addEventListener("click", () => {
    experiences.push({ id: ++uid, title: "", company: "", date: "", desc: "" });
    renderExpForm(); renderPreview(); saveState();
  });
  $("#addEduBtn").addEventListener("click", () => {
    educations.push({ id: ++uid, degree: "", school: "", date: "", desc: "" });
    renderEduForm(); renderPreview(); saveState();
  });

  $$("#templateBtns .tpl-btn").forEach((b) =>
    b.addEventListener("click", () => setTemplate(b.getAttribute("data-tpl"))));
  $("#downloadBtn").addEventListener("click", exportPDF);

  // apply persisted template selection to buttons
  $$("#templateBtns .tpl-btn").forEach((b) =>
    b.classList.toggle("is-active", b.getAttribute("data-tpl") === currentTpl));

  renderPreview();
});

window.addEventListener("resize", fitPaper);
window.addEventListener("load", fitPaper);
