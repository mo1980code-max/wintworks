"use strict";

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));

// Initial State
let experiences = [
  { id: Date.now(), title: "Senior Software Engineer", company: "Tech Solutions Inc.", date: "Jan 2021 - Present", desc: "- Developed and maintained scalable web applications.\n- Collaborated with cross-functional teams to define and design new features.\n- Improved application performance by 30%." }
];
let educations = [
  { id: Date.now() + 1, degree: "B.Sc. in Computer Science", school: "University of Technology", date: "2016 - 2020", desc: "Graduated with Honors. Focused on software engineering and algorithms." }
];

function bindInputs() {
  const inputs = $$('#cvEditor input, #cvEditor textarea');
  inputs.forEach(el => {
    el.addEventListener('input', renderPreview);
  });
  $('#templateSelect').addEventListener('change', (e) => {
    const paper = $('#cvPaper');
    paper.className = 'cv-paper temp-' + e.target.value;
    renderPreview();
  });
}

function renderExpForm() {
  const container = $('#expContainer');
  container.innerHTML = experiences.map((exp, i) => `
    <div class="repeater-item" data-id="${exp.id}">
      <button class="remove-btn" onclick="removeExp(${exp.id})">Remove</button>
      <div class="form-group">
        <label>Job Title</label>
        <input type="text" value="${esc(exp.title)}" oninput="updateExp(${exp.id}, 'title', this.value)">
      </div>
      <div class="form-group">
        <label>Company</label>
        <input type="text" value="${esc(exp.company)}" oninput="updateExp(${exp.id}, 'company', this.value)">
      </div>
      <div class="form-group">
        <label>Dates</label>
        <input type="text" value="${esc(exp.date)}" oninput="updateExp(${exp.id}, 'date', this.value)">
      </div>
      <div class="form-group">
        <label>Description / Responsibilities</label>
        <textarea rows="3" oninput="updateExp(${exp.id}, 'desc', this.value)">${esc(exp.desc)}</textarea>
      </div>
    </div>
  `).join('');
}

function renderEduForm() {
  const container = $('#eduContainer');
  container.innerHTML = educations.map((edu, i) => `
    <div class="repeater-item" data-id="${edu.id}">
      <button class="remove-btn" onclick="removeEdu(${edu.id})">Remove</button>
      <div class="form-group">
        <label>Degree / Certificate</label>
        <input type="text" value="${esc(edu.degree)}" oninput="updateEdu(${edu.id}, 'degree', this.value)">
      </div>
      <div class="form-group">
        <label>School / University</label>
        <input type="text" value="${esc(edu.school)}" oninput="updateEdu(${edu.id}, 'school', this.value)">
      </div>
      <div class="form-group">
        <label>Dates</label>
        <input type="text" value="${esc(edu.date)}" oninput="updateEdu(${edu.id}, 'date', this.value)">
      </div>
      <div class="form-group">
        <label>Details (Optional)</label>
        <textarea rows="2" oninput="updateEdu(${edu.id}, 'desc', this.value)">${esc(edu.desc)}</textarea>
      </div>
    </div>
  `).join('');
}

window.addExp = function() {
  experiences.push({ id: Date.now(), title: "", company: "", date: "", desc: "" });
  renderExpForm(); renderPreview();
};
window.removeExp = function(id) {
  experiences = experiences.filter(e => e.id !== id);
  renderExpForm(); renderPreview();
};
window.updateExp = function(id, field, val) {
  const e = experiences.find(e => e.id === id);
  if(e) e[field] = val;
  renderPreview();
};

window.addEdu = function() {
  educations.push({ id: Date.now(), degree: "", school: "", date: "", desc: "" });
  renderEduForm(); renderPreview();
};
window.removeEdu = function(id) {
  educations = educations.filter(e => e.id !== id);
  renderEduForm(); renderPreview();
};
window.updateEdu = function(id, field, val) {
  const e = educations.find(e => e.id === id);
  if(e) e[field] = val;
  renderPreview();
};

$('#addExpBtn').addEventListener('click', addExp);
$('#addEduBtn').addEventListener('click', addEdu);


/* ================= RENDERING TEMPLATES ================= */

function getContactLine(sep = " | ") {
  const items = [];
  const e = $('#cvEmail').value; if(e) items.push(e);
  const p = $('#cvPhone').value; if(p) items.push(p);
  const l = $('#cvLocation').value; if(l) items.push(l);
  const ln = $('#cvLink').value; if(ln) items.push(ln);
  return items.map(esc).join(sep);
}

function renderClassic() {
  const name = $('#cvName').value;
  const title = $('#cvJobTitle').value;
  const sum = $('#cvSummary').value;
  const skills = $('#cvSkills').value;
  const langs = $('#cvLangs').value;

  let html = `
    <div class="cv-header">
      <h1 class="cv-name">${esc(name)}</h1>
      <div class="cv-job-title">${esc(title)}</div>
      <div class="cv-contact">${getContactLine(" &bull; ")}</div>
    </div>
  `;

  if(sum) {
    html += `<div class="cv-section">
      <div class="cv-sec-title">Professional Summary</div>
      <div class="cv-item-desc">${esc(sum)}</div>
    </div>`;
  }

  if(experiences.length) {
    html += `<div class="cv-section"><div class="cv-sec-title">Experience</div>`;
    experiences.forEach(e => {
      html += `<div class="cv-item">
        <div class="cv-item-title"><span>${esc(e.title)}</span> <span>${esc(e.date)}</span></div>
        <div class="cv-item-sub">${esc(e.company)}</div>
        <div class="cv-item-desc">${esc(e.desc)}</div>
      </div>`;
    });
    html += `</div>`;
  }

  if(educations.length) {
    html += `<div class="cv-section"><div class="cv-sec-title">Education</div>`;
    educations.forEach(e => {
      html += `<div class="cv-item">
        <div class="cv-item-title"><span>${esc(e.degree)}</span> <span>${esc(e.date)}</span></div>
        <div class="cv-item-sub">${esc(e.school)}</div>
        ${e.desc ? `<div class="cv-item-desc">${esc(e.desc)}</div>` : ''}
      </div>`;
    });
    html += `</div>`;
  }

  let misc = [];
  if(skills) misc.push(`<b>Skills:</b> ${esc(skills)}`);
  if(langs) misc.push(`<b>Languages:</b> ${esc(langs)}`);
  if(misc.length) {
    html += `<div class="cv-section">
      <div class="cv-sec-title">Additional Information</div>
      <div class="cv-skills">${misc.join("<br><br>")}</div>
    </div>`;
  }

  return html;
}

function renderModern() {
  const name = $('#cvName').value;
  const title = $('#cvJobTitle').value;
  const sum = $('#cvSummary').value;
  const skills = $('#cvSkills').value;
  const langs = $('#cvLangs').value;

  const email = $('#cvEmail').value;
  const phone = $('#cvPhone').value;
  const loc = $('#cvLocation').value;
  const ln = $('#cvLink').value;

  const skillArr = skills.split(',').map(s=>s.trim()).filter(Boolean);
  const langArr = langs.split(',').map(s=>s.trim()).filter(Boolean);

  let leftHtml = `
    <h1 class="cv-name">${esc(name)}</h1>
    <div class="cv-job-title">${esc(title)}</div>
    
    <div class="cv-sec-title-left">Contact</div>
    ${email ? `<div class="cv-contact-item">✉ ${esc(email)}</div>` : ''}
    ${phone ? `<div class="cv-contact-item">☎ ${esc(phone)}</div>` : ''}
    ${loc ? `<div class="cv-contact-item">📍 ${esc(loc)}</div>` : ''}
    ${ln ? `<div class="cv-contact-item">🔗 ${esc(ln)}</div>` : ''}
  `;

  if(skillArr.length) {
    leftHtml += `<div class="cv-sec-title-left">Skills</div><ul class="cv-skills-list">`;
    skillArr.forEach(s => leftHtml += `<li>${esc(s)}</li>`);
    leftHtml += `</ul>`;
  }

  if(langArr.length) {
    leftHtml += `<div class="cv-sec-title-left">Languages</div><ul class="cv-skills-list">`;
    langArr.forEach(l => leftHtml += `<li>${esc(l)}</li>`);
    leftHtml += `</ul>`;
  }

  let rightHtml = ``;
  if(sum) {
    rightHtml += `<div class="cv-sec-title-right">Profile</div>
      <div class="cv-item-desc" style="margin-bottom:25px;">${esc(sum)}</div>`;
  }

  if(experiences.length) {
    rightHtml += `<div class="cv-sec-title-right">Experience</div>`;
    experiences.forEach(e => {
      rightHtml += `<div class="cv-item">
        <div class="cv-item-title"><span>${esc(e.title)}</span></div>
        <div class="cv-item-sub">${esc(e.company)} | ${esc(e.date)}</div>
        <div class="cv-item-desc">${esc(e.desc)}</div>
      </div>`;
    });
  }

  if(educations.length) {
    rightHtml += `<div class="cv-sec-title-right" style="margin-top:25px;">Education</div>`;
    educations.forEach(e => {
      rightHtml += `<div class="cv-item">
        <div class="cv-item-title"><span>${esc(e.degree)}</span></div>
        <div class="cv-item-sub">${esc(e.school)} | ${esc(e.date)}</div>
        ${e.desc ? `<div class="cv-item-desc">${esc(e.desc)}</div>` : ''}
      </div>`;
    });
  }

  return `<div class="modern-left">${leftHtml}</div><div class="modern-right">${rightHtml}</div>`;
}

function renderMinimal() {
  const name = $('#cvName').value;
  const title = $('#cvJobTitle').value;
  const sum = $('#cvSummary').value;
  const skills = $('#cvSkills').value;
  const langs = $('#cvLangs').value;

  let html = `
    <div class="cv-header">
      <div>
        <h1 class="cv-name">${esc(name)}</h1>
        <div class="cv-job-title">${esc(title)}</div>
      </div>
      <div class="cv-contact">
        ${esc($('#cvEmail').value)}<br>
        ${esc($('#cvPhone').value)}<br>
        ${esc($('#cvLocation').value)}<br>
        ${esc($('#cvLink').value)}
      </div>
    </div>
  `;

  if(sum) {
    html += `<div class="cv-section">
      <div class="cv-sec-left">Profile</div>
      <div class="cv-sec-right minimal-summary">${esc(sum)}</div>
    </div>`;
  }

  if(experiences.length) {
    html += `<div class="cv-section">
      <div class="cv-sec-left">Experience</div>
      <div class="cv-sec-right">`;
    experiences.forEach(e => {
      html += `<div class="cv-item">
        <div class="cv-item-title"><span>${esc(e.title)}</span> <span style="font-size:10pt; font-weight:normal; color:#666">${esc(e.date)}</span></div>
        <div class="cv-item-sub">${esc(e.company)}</div>
        <div class="cv-item-desc">${esc(e.desc)}</div>
      </div>`;
    });
    html += `</div></div>`;
  }

  if(educations.length) {
    html += `<div class="cv-section">
      <div class="cv-sec-left">Education</div>
      <div class="cv-sec-right">`;
    educations.forEach(e => {
      html += `<div class="cv-item">
        <div class="cv-item-title"><span>${esc(e.degree)}</span> <span style="font-size:10pt; font-weight:normal; color:#666">${esc(e.date)}</span></div>
        <div class="cv-item-sub">${esc(e.school)}</div>
        ${e.desc ? `<div class="cv-item-desc">${esc(e.desc)}</div>` : ''}
      </div>`;
    });
    html += `</div></div>`;
  }

  let misc = [];
  if(skills) misc.push(`<b>Skills:</b> ${esc(skills)}`);
  if(langs) misc.push(`<b>Languages:</b> ${esc(langs)}`);
  if(misc.length) {
    html += `<div class="cv-section">
      <div class="cv-sec-left">Details</div>
      <div class="cv-sec-right cv-item-desc">${misc.join("<br><br>")}</div>
    </div>`;
  }

  return html;
}

function renderPreview() {
  const tpl = $('#templateSelect').value;
  const paper = $('#cvPaper');
  if(tpl === 'classic') paper.innerHTML = renderClassic();
  else if(tpl === 'modern') paper.innerHTML = renderModern();
  else if(tpl === 'minimal') paper.innerHTML = renderMinimal();
}

document.addEventListener("DOMContentLoaded", () => {
  renderExpForm();
  renderEduForm();
  bindInputs();
  renderPreview();
});
