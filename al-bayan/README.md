# Al-Bayan — Islamic Center &amp; Mosque Website Template

A complete, professional **English (LTR)** front-end template for mosques, Islamic
centers, schools and charities. Built with **HTML5 + CSS3 + vanilla JavaScript +
Bootstrap 5.3.3** (no jQuery, no frameworks).

Full **RTL support is preserved inside the code** — switch any page to Arabic with
`<html lang="ar" dir="rtl">`; logical CSS properties handle the layout flip.

---

## Pages

| File | Description |
|---|---|
| `index.html` | Homepage: hero slider, live prayer times, causes, courses, pillars, ayat slider, **full-Quran player**, latest projects, media embeds, countdown, news |
| `quran.html` | **The Holy Quran — complete text (114 surahs, 6,236 verses, Uthmani script)**, search, dark reading mode, verse numbering, per-surah audio with 7 reciters, "continue where you left off" |
| `about.html` | About Us (story, values, team) |
| `prayers.html` | Prayer times + Hijri date + qibla + print view |
| `events.html` / `event.html?id=…` | Events + event schedule table + details with speaker/researcher bio |
| `courses.html` | Courses + pricing plans |
| `donate.html` | Donation form + campaigns + FAQ |
| `contact.html` | Contact form + map |
| `admin.html` | **Admin panel** — edit texts, prayer settings, campaigns, courses, events and **media embeds** (demo code: `albayan01`) |
| `al-bayan-offline.html` | Single-file build: all CSS, JS, images and the full Quran text inlined. Opens from disk with no server and no internet |

## Features

- ⏰ **Astronomical prayer times** — 17 cities, 7 calculation methods, Shafi/Hanafi Asr, iqamah offsets
- 🌙 **Automatic Hijri date** (Umm al-Qura) + 🧭 **qibla direction**
- 📖 **Complete Holy Quran** — full text, search, audio (7 reciters), bookmark, dark mode
- 📺 **Media embeds** — YouTube / Vimeo / SoundCloud, fully manageable from the admin panel
- 💝 Donation campaigns with progress bars, donation form, local records
- 🎓 Courses with teachers + membership pricing
- 🏗️ Latest projects section with status &amp; progress
- 🗓️ Event schedule table with Upcoming/Completed status
- 👤 Speaker/researcher bio on every event page
- ⏳ Countdown timer for upcoming events
- 📱 Fully responsive (mobile / tablet / desktop) &amp; 🖨️ print-friendly
- 🎨 Theme via CSS variables (green/gold palette)
- ⚙️ Zero-server admin panel (safe storage with memory fallback)
- 📄 Optional PHP contact endpoint (`php/contact.php`)

## Run locally

```bash
cd al-bayan
python3 -m http.server 8080
# open http://localhost:8080
```

Or simply double-click `al-bayan-offline.html` — works offline, no server needed.

## File structure

```
al-bayan/
├── index.html … contact.html, quran.html, admin.html
├── al-bayan-offline.html            # single-file offline build
├── css/style.css                  # all design (CSS variables at top)
├── js/main.js                     # site logic (rendering, Quran, media, countdown)
├── js/prayer-calc.js              # prayer engine + Hijri + qibla
├── js/admin.js                    # admin panel logic
├── data/site-data.js              # central data (texts, campaigns, courses, events, media, reciters)
├── data/quran-data.js             # complete Quran text (Uthmani)
├── assets/img/                    # original images
├── docs/Al-Bayan-Template-Guide.pdf # full buyer guide (setup, customization, hosting)
├── docs/CREDITS.md                # third-party licences & attribution
├── LICENSE.txt                    # item licence
└── php/contact.php                # optional PHP contact endpoint
```

## Quick customization

1. **Texts, media, reciters** — via `admin.html` (instant save in the browser)
   or directly in `data/site-data.js` (permanent for all visitors).
2. **Colors / fonts** — `:root` variables at the top of `css/style.css`.
3. **Images** — replace files in `assets/img/` keeping the same file names.
4. **YouTube embeds** — admin panel → **Media Embed** tab; paste any
   `youtube.com/watch?v=…`, `youtu.be/…` or `youtube.com/shorts/…` URL.
