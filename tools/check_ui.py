#!/usr/bin/env python3
"""UI consistency check for the built site (run after build_resources.py + build_blog.py, before every push).

Zain (2026-10-23): every new page and every update must match the site's design from the first version,
with animations where they fit. This catches the mistakes that slipped through on /book/:
  1. every page loads the shared UI kit (blog/ui.css, or the kit inlined on home/landing pages),
     which gives the FAQ accordion, scroll reveal, hero entrance and hover lift;
  2. no bare <details> blocks: FAQs must use ui_kit.faq_accordion() (gold plus/minus rows);
     a styled widget may use <details class="...">;
  3. exactly one <h1> per page;
  4. no section heading block without the site's eyebrow + heading pattern on resource pages
     (a <h2> directly inside <section class="wrap ..."> must sit in <div class="sec-hd">; FAQ sections
     (class "faqs") may use a plain <h2>FAQs</h2> like the blog).
See docs/design-system.md for the components to use. Exit code 1 on any problem.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
SKIP = ("newsletter/issues/", "ready/", "404.html")


def main():
    errs = []
    pages = [p for p in SITE.rglob("*.html") if not any(s in p.as_posix() for s in SKIP)]
    for p in pages:
        rel = p.relative_to(SITE).as_posix()
        h = p.read_text(encoding="utf-8", errors="ignore")
        if "<meta http-equiv=\"refresh\"" in h:
            continue
        kit = "ui.css" in h or "MFA UI kit" in h or ("faq-q" in h and "IntersectionObserver" in h)  # home page inlines its own copy
        if not kit:
            errs.append(f"{rel}: does not load the UI kit (ui.css)")
        if re.search(r"<details>", h):
            errs.append(f"{rel}: bare <details> found; use ui_kit.faq_accordion() for FAQs")
        n = len(re.findall(r"<h1[\s>]", h))
        if n != 1:
            errs.append(f"{rel}: {n} <h1> tags (need exactly 1)")
        for m in re.finditer(r'<section class="wrap(?![^"]*\bfaqs\b)[^"]*"[^>]*>\s*<h2', h):
            errs.append(f"{rel}: section heading without the eyebrow + .sec-hd pattern near offset {m.start()}")
    for e in errs:
        print("UI:", e)
    print(f"ui {'OK' if not errs else 'FAIL'}: {len(pages)} pages checked, {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
