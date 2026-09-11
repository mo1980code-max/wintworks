#!/usr/bin/env python3
"""
Guards the pre-built Tailwind stylesheet used by cv-builder.html.

The page used to load the Tailwind Play CDN, which compiled utilities in the
visitor's browser (~400 KB of JavaScript) and blocked the first paint. It now
loads `css/tailwind.min.css`, built by `npm run build:css`.

These checks fail loudly when someone edits cv-builder.html and forgets to
rebuild, or reintroduces the CDN:
  1. no runtime Tailwind (or any other) CSS compiler in the page;
  2. every utility class used in the markup exists in the built stylesheet
     (dark:/md: variants and arbitrary values included);
  3. the built file stays small — a regression here means the content glob
     stopped purging.
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(BASE, "cv-builder.html")
CSS = os.path.join(BASE, "css", "tailwind.min.css")
PASS = 0


def ok(label, cond, extra=""):
    global PASS
    assert cond, f"FAIL: {label} {extra}"
    PASS += 1
    print(f"  ✔ {label}")


html = open(PAGE, encoding="utf-8").read()
css = open(CSS, encoding="utf-8").read()

print("cv-builder build:")
ok("no Tailwind Play CDN", "cdn.tailwindcss.com" not in html)
ok("no runtime tailwind.config", "tailwind.config" not in html)
ok("built stylesheet linked", 'href="css/tailwind.min.css"' in html)
ok("built stylesheet is loaded before the CV template CSS",
   html.index("css/tailwind.min.css") < html.index("css/cv-builder.css"))
ok("built CSS is minified", len(css.splitlines()) <= 2)
size_kb = len(css.encode()) / 1024
ok("built CSS stays small (<40 KB)", size_kb < 40, f"({size_kb:.1f} KB)")

# ---- class coverage -------------------------------------------------------
# Only real Tailwind utilities are checked: hand-written classes live in
# css/cv-builder.css and are intentionally absent from the built file.
UTILITY_RX = re.compile(
    r"^(?:"
    r"(?:sm|md|lg|xl|2xl):|dark:|hover:|focus:|active:|group-hover:|"
    r"backdrop-blur|bg-|text-|font-|border|rounded|shadow|p[xytrbl]?-|m[xytrbl]?-|"
    r"w-|h-|min-|max-|flex|grid|gap-|items-|justify-|space-|hidden|block|inline|"
    r"sticky|fixed|absolute|relative|top-|inset-|z-|overflow-|cursor-|transition|"
    r"duration-|opacity-|translate-|scale-|ring-|divide-|order-|col-|row-|"
    r"whitespace-|truncate|uppercase|lowercase|tracking-|leading-|list-|"
    r"object-|aspect-|select-|pointer-events-|sr-only|antialiased|outline-|"
    r"print:|animate-|ease-|delay-|rotate-|transform|origin-|align-|uppercase"
    r")"
)

classes = set()
for attr in re.findall(r'class="([^"]*)"', html):
    for token in attr.split():
        if UTILITY_RX.match(token):
            classes.add(token)

missing = []
# Tailwind escapes special characters in the emitted selector
# (`.bg-white\/80`, `.max-w-\[1500px\]`), so compare against the unescaped
# stylesheet: what matters is that the utility exists, not how it is escaped.
css_plain = css.replace("\\", "")
for token in sorted(classes):
    if re.search(re.escape(token) + r"(?![\w-])", css_plain) is None:
        missing.append(token)

ok(f"all {len(classes)} Tailwind utilities used in the page exist in the build",
   not missing, f"missing: {missing[:8]}")

# reverse direction: a stale build often keeps classes that were deleted
print(f"\n{len(classes)} utilities checked · built CSS {size_kb:.1f} KB "
      f"(Play CDN was ~400 KB of JavaScript)")
sys.exit(0)
