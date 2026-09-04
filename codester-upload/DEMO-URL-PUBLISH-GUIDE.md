# Demo URL — How to get a live HTTPS link (NOT GitHub)

> Codester requires an HTTPS demo URL. This guide creates one without GitHub,
> without an account and without cost — in ~2 minutes.

---

## The link you will produce

```
https://<your-site-name>.netlify.app
```

Example (after renaming): `https://albayan-demo.netlify.app`

---

## Steps (from any browser)

1. Extract `netlify-drop.zip` → folder `al-bayan/` (contains `index.html`).
2. Open `https://app.netlify.com/drop` in your browser.
3. Drag the `al-bayan` **folder** onto the Netlify Drop area (not the ZIP).
4. Wait ~1 minute → Netlify creates the site and gives you an HTTPS link.
5. (Recommended) On the site page: **Site configuration → Change site name** → `albayan-demo`.
6. Copy `https://albayan-demo.netlify.app` and paste it into the Codester **Demo URL** field.

---

## Alternative (if you already have shared hosting)

- Upload the `al-bayan` folder contents to `public_html` via cPanel File Manager.
- Your own domain (e.g. `https://yourmosque.org`) becomes the demo URL.

---

## Alternative (if you host the demo on your own domain)

- Any static host works: Vercel, Cloudflare Pages, shared hosting, etc.
- Only requirement from Codester: the demo link must use **HTTPS**.

---

## Notes

- The demo is the full template as-is. It contains no personal data — only the template's demo content (prayer times, events, courses, donations, Quran).
- On Netlify the included `php/contact.php` runs as a demo only (no email sending). Real email needs PHP hosting or a form service — documented inside the package.
- To remove the demo later: Netlify → Site configuration → Danger zone → Delete site.
- The video file `al-bayan-promo-with-audio.mp4` (in this repo) is ready to upload to YouTube; after uploading, paste the YouTube link into the **Video URL** field.
