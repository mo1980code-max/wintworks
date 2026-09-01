# 🕌 Ibadah — Islamic Center & Mosque Template (HTML / CSS / JS + Bootstrap 5)

A professional English (LTR) front-end template inspired by the **Ibadah** theme:
mosque + Islamic center, elegant green/gold design, built with **HTML5 + CSS3 +
vanilla JavaScript + Bootstrap 5** (no jQuery). Full **RTL support is preserved
inside the code** (see docs §6).

## Pages

| File | Description |
|---|---|
| `index.html` | Homepage: slider, live prayer times, causes, courses, pillars, ayat slider, Quran player, **latest projects**, **media embeds (YouTube/Vimeo/SoundCloud)**, countdown, news |
| `about.html` | About Us (story, values, team) |
| `prayers.html` | Prayer times + Hijri date + qibla + print |
| `events.html` / `event.html?id=..` | Events + **event schedule table** + details with **speaker bio** |
| `courses.html` | Courses + pricing plans |
| `donate.html` | Donation form + campaigns + FAQ |
| `contact.html` | Contact form + map |
| `admin.html` | **Admin panel** (edit texts, times, campaigns, courses, events — demo code: `ibadah01`) |
| `docs/index.html` | Full documentation & help |

## Features

- ⏰ **Astronomical prayer times** for 17 cities, 7 methods, Shafi/Hanafi Asr, iqamah offsets.
- 🌙 **Automatic Hijri date** (Umm al-Qura) via `Intl` + 🧭 **Qibla direction**.
- 💝 Donation campaigns with progress bars, donation form, local records.
- 🎓 Courses with teachers + membership pricing (Basic / Family / Patron).
- 📺 **Responsive media embeds**: YouTube, Vimeo and SoundCloud tabs.
- 🏗️ **Latest projects** section with status & progress.
- 🗓️ **Event schedule table** with Upcoming/Completed status.
- 👤 **Speaker/researcher bio** on every event page.
- ⏳ **Countdown timer** for upcoming events (home & details).
- 📱 Fully mobile-safe (responsive RTL/LTR) & 🖨️ print-friendly schedule.
- 🎨 Color/font variables for easy theming (Marcellus + DM Sans).
- ⚙️ Zero-server admin panel (localStorage) with reset option.
- 📄 Optional PHP examples in `php/`.

## Run

```bash
cd ibadah
python3 -m http.server 8080
# open http://localhost:8080
```

## File structure

```
ibadah/
├── index.html … contact.html     # pages
├── admin.html                    # admin panel
├── css/style.css                 # all design
├── js/main.js                    # site interactions
├── js/prayer-calc.js             # prayer engine + qibla
├── js/admin.js                   # admin logic
├── data/site-data.js             # central data (texts/campaigns/courses/events/projects)
├── assets/img/                   # images
├── docs/index.html               # documentation
└── php/                          # optional server examples
```

## Quick customization

1. **Texts & numbers**: via `admin.html` (instant save) or directly in `data/site-data.js`.
2. **Colors/fonts**: `:root` variables at the top of `css/style.css`.
3. **Images**: replace files in `assets/img/` with the same name.
