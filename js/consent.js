/* WintWorks privacy preferences and Google Consent Mode v2 defaults.
   This first-party notice controls optional storage before advertising is enabled.
   IMPORTANT: AdSense publishers serving personalised ads in the EEA, UK or
   Switzerland must also activate a Google-certified TCF CMP (for example,
   AdSense > Privacy & messaging). This notice is not a certified IAB TCF CMP. */
(function () {
  "use strict";

  var STORAGE_KEY = "ww:consent:v1";
  var VERSION = 1;
  var state = null;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };

  // Privacy-safe defaults must be set before any Google advertising tag loads.
  window.gtag("consent", "default", {
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    analytics_storage: "denied",
    functionality_storage: "granted",
    security_storage: "granted",
    wait_for_update: 500
  });

  function read() {
    try {
      var value = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (value && value.version === VERSION) return value;
    } catch (_) {}
    return null;
  }

  function signal(value) {
    window.gtag("consent", "update", {
      ad_storage: value.advertising ? "granted" : "denied",
      ad_user_data: value.advertising ? "granted" : "denied",
      ad_personalization: value.advertising ? "granted" : "denied",
      analytics_storage: value.analytics ? "granted" : "denied",
      functionality_storage: value.preferences ? "granted" : "denied",
      security_storage: "granted"
    });
  }

  function save(next) {
    state = {
      version: VERSION,
      necessary: true,
      preferences: !!next.preferences,
      analytics: !!next.analytics,
      advertising: !!next.advertising,
      updatedAt: new Date().toISOString()
    };
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_) {}
    signal(state);
    closePanels();
    window.dispatchEvent(new CustomEvent("wintworks:consentchange", { detail: state }));
  }

  function allows(category) {
    if (category === "necessary") return true;
    return !!(state && state[category]);
  }

  function closePanels() {
    var banner = document.getElementById("cookieBanner");
    var modal = document.getElementById("cookieModal");
    if (banner) banner.hidden = true;
    if (modal) modal.hidden = true;
    document.documentElement.classList.remove("cookie-modal-open");
  }

  function openSettings() {
    var modal = document.getElementById("cookieModal");
    if (!modal) return;
    document.getElementById("consentPreferences").checked = state ? !!state.preferences : true;
    document.getElementById("consentAnalytics").checked = state ? !!state.analytics : false;
    document.getElementById("consentAdvertising").checked = state ? !!state.advertising : false;
    modal.hidden = false;
    document.documentElement.classList.add("cookie-modal-open");
    var heading = document.getElementById("cookieSettingsTitle");
    if (heading) heading.focus();
  }

  function markup() {
    var wrapper = document.createElement("div");
    wrapper.innerHTML = [
      '<section class="cookie-banner" id="cookieBanner" aria-label="Cookie notice" hidden>',
      '  <div class="cookie-banner-copy">',
      '    <h2>Privacy choices</h2>',
      '    <p>We use necessary storage for site features. With your permission, we may also use analytics and advertising cookies. You can accept, reject or manage your choices. See our <a href="privacy.html#cookies">Privacy &amp; Cookie Policy</a>.</p>',
      '  </div>',
      '  <div class="cookie-actions">',
      '    <button type="button" class="cookie-btn secondary" data-consent="reject">Reject non-essential</button>',
      '    <button type="button" class="cookie-btn secondary" data-consent="manage">Manage choices</button>',
      '    <button type="button" class="cookie-btn primary" data-consent="accept">Accept all</button>',
      '  </div>',
      '</section>',
      '<div class="cookie-modal" id="cookieModal" role="dialog" aria-modal="true" aria-labelledby="cookieSettingsTitle" hidden>',
      '  <div class="cookie-modal-card">',
      '    <div class="cookie-modal-head">',
      '      <div><h2 id="cookieSettingsTitle" tabindex="-1">Cookie settings</h2><p>Choose which optional technologies WintWorks may use.</p></div>',
      '      <button type="button" class="cookie-close" data-consent="close" aria-label="Close cookie settings">×</button>',
      '    </div>',
      '    <div class="cookie-choice"><div><b>Necessary</b><p>Security, consent records and features you request, such as theme or saved-job preferences.</p></div><span>Always on</span></div>',
      '    <label class="cookie-choice"><div><b>Preferences</b><p>Remember optional display and performance preferences.</p></div><input id="consentPreferences" type="checkbox"></label>',
      '    <label class="cookie-choice"><div><b>Analytics</b><p>Help us understand aggregate site usage if analytics is enabled.</p></div><input id="consentAnalytics" type="checkbox"></label>',
      '    <label class="cookie-choice"><div><b>Advertising</b><p>Allow advertising storage and personalised advertising where available.</p></div><input id="consentAdvertising" type="checkbox"></label>',
      '    <div class="cookie-modal-actions">',
      '      <button type="button" class="cookie-btn secondary" data-consent="reject">Reject non-essential</button>',
      '      <button type="button" class="cookie-btn primary" data-consent="save">Save choices</button>',
      '    </div>',
      '  </div>',
      '</div>'
    ].join("");
    while (wrapper.firstChild) document.body.appendChild(wrapper.firstChild);
  }

  function addSettingsLink() {
    var bottom = document.querySelector(".footer-bottom");
    if (!bottom || bottom.querySelector(".cookie-settings-link")) return;
    var button = document.createElement("button");
    button.type = "button";
    button.className = "cookie-settings-link";
    button.textContent = "Cookie settings";
    button.addEventListener("click", openSettings);
    bottom.appendChild(button);
  }

  function bind() {
    document.addEventListener("click", function (event) {
      var button = event.target.closest("[data-consent]");
      if (!button) return;
      var action = button.getAttribute("data-consent");
      if (action === "accept") save({ preferences: true, analytics: true, advertising: true });
      if (action === "reject") save({ preferences: false, analytics: false, advertising: false });
      if (action === "manage") openSettings();
      if (action === "close") closePanels();
      if (action === "save") save({
        preferences: document.getElementById("consentPreferences").checked,
        analytics: document.getElementById("consentAnalytics").checked,
        advertising: document.getElementById("consentAdvertising").checked
      });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closePanels();
    });
  }

  state = read();
  if (state) signal(state);

  window.WintConsent = {
    allows: allows,
    getState: function () { return state ? Object.assign({}, state) : null; },
    openSettings: openSettings
  };

  document.addEventListener("DOMContentLoaded", function () {
    markup();
    bind();
    addSettingsLink();
    if (!state) document.getElementById("cookieBanner").hidden = false;
  });
})();
