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

const STORE_KEY = "ww:cv:v3en";
let currentTpl = "executive";

/* -------------------- state -------------------- */
const defaults = {
  tpl: "executive",
  name: "John Smith",
  jobTitle: "Software Engineer",
  email: "john@example.com",
  phone: "+1 555 000 0000",
  location: "Berlin, Germany",
  link: "linkedin.com/in/username",
  summary: "Software engineer with 5+ years of experience building scalable web applications. Passionate about solving complex problems and improving system efficiency, with a proven track record of boosting performance and leading technical teams.",
  skills: "JavaScript, Python, React, Node.js, Project Management, Agile Methodology",
  langs: "English (Fluent), German (B2), Arabic (Native)",
  experiences: [
    { id: 1, title: "Senior Software Engineer", company: "Tech Solutions Inc.", date: "Jan 2021 - Present",
      desc: "- Led the development and maintenance of scalable web applications.\n- Collaborated with cross-functional teams to design new features.\n- Improved application performance by 30%." },
  ],
  educations: [
    { id: 2, degree: "B.Sc. in Computer Science", school: "Technical University of Berlin", date: "2016 - 2020",
      desc: "Graduated with honors, focusing on software engineering and algorithms." },
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
        <b>Experience</b>
        <button type="button" class="remove-btn" data-remove-exp="${exp.id}">✕ Remove</button>
      </div>
      <div class="fg">
        <label>Job Title</label>
        <input type="text" value="${esc(exp.title)}" data-exp="${exp.id}" data-field="title" placeholder="e.g. Project Manager">
      </div>
      <div class="fg">
        <label>Company / Employer</label>
        <input type="text" value="${esc(exp.company)}" data-exp="${exp.id}" data-field="company" placeholder="e.g. Advanced Tech Corp">
      </div>
      <div class="fg">
        <label>Time Period</label>
        <input type="text" value="${esc(exp.date)}" data-exp="${exp.id}" data-field="date" placeholder="e.g. Jan 2021 - Present">
      </div>
      <div class="fg">
        <label>Description &amp; Achievements</label>
        <textarea rows="3" data-exp="${exp.id}" data-field="desc" placeholder="Use bullet points starting with (-) and highlight a measurable achievement, e.g. reduced costs by 20%.">${esc(exp.desc)}</textarea>
      </div>
    </div>`).join("");
}

function renderEduForm() {
  const c = $("#eduContainer");
  c.innerHTML = educations.map((edu) => `
    <div class="repeater-item" data-id="${edu.id}">
      <div class="repeater-head">
        <b>Education</b>
        <button type="button" class="remove-btn" data-remove-edu="${edu.id}">✕ Remove</button>
      </div>
      <div class="fg">
        <label>Degree / Certificate</label>
        <input type="text" value="${esc(edu.degree)}" data-edu="${edu.id}" data-field="degree" placeholder="e.g. B.Sc. in Computer Science">
      </div>
      <div class="fg">
        <label>University / Institution</label>
        <input type="text" value="${esc(edu.school)}" data-edu="${edu.id}" data-field="school" placeholder="e.g. Technical University of Berlin">
      </div>
      <div class="fg">
        <label>Time Period</label>
        <input type="text" value="${esc(edu.date)}" data-edu="${edu.id}" data-field="date" placeholder="e.g. 2016 - 2020">
      </div>
      <div class="fg">
        <label>Additional Details (optional)</label>
        <textarea rows="2" data-edu="${edu.id}" data-field="desc" placeholder="e.g. Graduated with honors, high GPA.">${esc(edu.desc)}</textarea>
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
    h += `<div class="cv-section"><div class="cv-sec-title">Professional Summary</div>
      <div class="cv-item-desc">${nl2br(val("#cvSummary"))}</div></div>`;
  }
  if (experiences.length) {
    h += `<div class="cv-section"><div class="cv-sec-title">Work Experience</div>`;
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
    h += `<div class="cv-section"><div class="cv-sec-title">Education</div>`;
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
    h += `<div class="cv-section"><div class="cv-sec-title">Skills</div>
      <div class="cv-tags">${skillsArr().map((s) => `<span class="cv-tag">${esc(s)}</span>`).join("")}</div></div>`;
  }
  if (langsArr().length) {
    h += `<div class="cv-section"><div class="cv-sec-title">Languages</div>
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
    <div class="side-title">Contact</div>`;
  if (email) side += `<div class="contact-item"><span class="ic">✉</span><span dir="ltr">${esc(email)}</span></div>`;
  if (phone) side += `<div class="contact-item"><span class="ic">☎</span><span dir="ltr">${esc(phone)}</span></div>`;
  if (loc)   side += `<div class="contact-item"><span class="ic">📍</span><span>${esc(loc)}</span></div>`;
  if (link)  side += `<div class="contact-item"><span class="ic">🔗</span><span dir="ltr">${esc(link)}</span></div>`;

  const skills = skillsArr();
  if (skills.length) {
    side += `<div class="side-title">Skills</div><ul class="skills-list">`;
    skills.forEach((s, i) => {
      const pct = 70 + ((i * 7) % 26); // 70–95% varied, purely decorative
      side += `<li>${esc(s)}<div class="bar"><span style="width:${pct}%"></span></div></li>`;
    });
    side += `</ul>`;
  }
  const langs = langsArr();
  if (langs.length) {
    side += `<div class="side-title">Languages</div><ul class="lang-list">`;
    langs.forEach((l) => (side += `<li>${esc(l)}</li>`));
    side += `</ul>`;
  }

  // main
  let main = "";
  if (val("#cvSummary")) {
    main += `<div class="cv-section"><div class="main-title">Profile</div>
      <div class="profile-text">${nl2br(val("#cvSummary"))}</div></div>`;
  }
  if (experiences.length) {
    main += `<div class="cv-section"><div class="main-title">Work Experience</div>`;
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
    main += `<div class="cv-section"><div class="main-title">Education</div>`;
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
    h += `<div class="cv-section"><div class="cv-sec-title">Profile</div>
      <div class="cv-item-desc">${nl2br(val("#cvSummary"))}</div></div>`;
  }
  if (experiences.length) {
    h += `<div class="cv-section"><div class="cv-sec-title">Experience</div>`;
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
    h += `<div class="cv-section"><div class="cv-sec-title">Education</div>`;
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
    h += `<div class="cv-section"><div class="cv-sec-title">Skills</div>
      <div class="cv-tags">${skillsArr().map((s) => `<span class="cv-tag">${esc(s)}</span>`).join("")}</div></div>`;
  }
  if (langsArr().length) {
    h += `<div class="cv-section"><div class="cv-sec-title">Languages</div>
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
  label.textContent = "Preparing...";

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
