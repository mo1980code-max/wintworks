# Design proposals — WintWorks visual refresh

Two complete redesigns of the site, kept **out of the live site**: nothing in this
folder is referenced by any page, so `wintworks.com` is unaffected.

Both proposals are **drop-in replacements for `css/app.css`**. They reuse every
existing class name, ID and markup structure, so applying one means changing a
single file — no HTML edits, no JS edits, no link changes, and the auto-update
bot (`scripts/generate_static_jobs.py`) keeps working because its
`<div class="jobs-grid" id="grid">` … `load-more-wrap` hooks are untouched.

| File | What it is |
|---|---|
| `palettes.html` | **Same design, 10 colour schemes** — live switcher (also toggles design A/B and dark mode). |
| `comparison.html` | Side-by-side comparison, fully self-contained (CSS inlined). Open it directly in a browser. |
| `preview-a.html` | Proposal A full-page mockup (static sample content). |
| `preview-b.html` | Proposal B full-page mockup (static sample content). |
| `proposal-a.css` | Proposal A stylesheet — copy over `css/app.css` to apply. |
| `proposal-b.css` | Proposal B stylesheet — copy over `css/app.css` to apply. |

## The two directions

**A · "Clean List"** — Google-Jobs style. White surfaces, a single blue accent
(`#1a73e8`), hairline borders, no gradients and no shadows. The job list becomes
one clean column instead of a card grid.

**B · "Paper / Editorial"** — warm paper background, serif display headings,
hairline rules, directory-style job list, ink-dark footer. Deep green accent
(`#16604a`) with amber for scholarships.

Both keep the existing dark mode (`[data-theme="dark"]`) and every CSS custom
property used inline in the markup (`--muted`, `--amber-grad`, `--green-bg`,
`--amber-bg`, `--amber`).

## Applying one

```bash
cp design-proposals/proposal-a.css css/app.css   # or proposal-b.css
```

Then verify: `npm test` and a link check over all 286 HTML pages.
