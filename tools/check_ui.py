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
Added 2026-10-24 after Zain's /book/ review ("you need to catch these things"):
  5. "below"/"above" references to the booking calendar, a form, the sources list or add-to-calendar
     links must match the page order (the target really is after/before the sentence);
  6. a stand-alone disclaimer section must use the .fineprint component (ui_kit.fineprint), and the
     kit CSS must keep the minimum spacing for footnotes (.disclaimer margin-top, .fineprint padding,
     last <main> section padding-bottom) so fine print never sits on the footer line;
  7. same-page anchors (href="#x") must exist; internal links (href="/...") must resolve to a built
     file or a _redirects rule, and their #fragment must exist on the target page;
  8. no leftover placeholder text in visible copy (lorem ipsum, TODO, TBD, FIXME, [insert...], {VAR});
  9. one phone number and one email: (347) 205-4468 / +13472054468 and info@mfa-advisory.com;
 10. no sentence repeated back-to-back, and no firm-voice "I/me" ("contact me", "I'll review"):
     the firm is "we"/"our team", the person is "Zain".
Optional: `python3 tools/check_ui.py --render` (needs Playwright + Chromium) also opens every page at 390 and
1300 px and fails when the last line of text in <main>, or any .disclaimer/.fine/.note, sits less than 40px above
the footer, or less than 12px under the element above it.
See docs/design-system.md for the components to use. Exit code 1 on any problem.
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

SITE = Path(__file__).resolve().parent.parent / "site"
SKIP = ("newsletter/issues/", "ready/", "404.html")


# ---------- helpers for rules 5-10 ----------
def visible(h):
    """Same-length copy of the HTML with only visible text kept (offsets line up with the raw HTML)."""
    blank = lambda m: " " * len(m.group())
    v = re.sub(r"<head\b.*?</head>|<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->|<noscript\b.*?</noscript>",
               blank, h, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", blank, v)


# (name, reference regex on visible text with group "dir", target regex on raw HTML)
DIR_RULES = [
    ("booking calendar",
     r"\b(?:pick|choose|select|book|schedule)\b[^.?!]{0,60}?\b(?:time|slot|call|consultation|meeting)\b[^.?!]{0,40}?\b(?P<dir>below|above)\b"
     r"|\bcalendar\s+(?P<dir2>below|above)\b",
     r'<iframe[^>]+calendar\.google\.com|\bid="(?:calendar|book)"|class="(?:cta-block|final)\b|class="helpbox\b|class="hero-btns"'),
    ("form", r"\b(?:form|fields?|your email|box)\b[^.?!]{0,30}?\b(?P<dir>below|above)\b", r"<form\b"),
    ("sources", r"\bsources?\b[^.?!]{0,15}?\b(?P<dir>below|above)\b", r'class="sources\b|>(?:Official )?[Ss]ources</h2>'),
    ("add-to-calendar links", r"\bcalendar\b[^.?!]{0,40}?\b(?:links?|buttons?)\s+(?P<dir>below|above)\b",
     r'class="kd-add|\.ics"|add-to-calendar|class="cal-add'),
]
PLACEHOLDER = re.compile(r"lorem ipsum|\bTODO\b|\bTBD\b|\bFIXME\b|\[insert|\{\{|\}\}|\{[A-Z_]{3,}\}")
PHONE_RE = re.compile(r"\(?\b\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b")
FIRM_I = re.compile(r"\b(?:contact|email|call|text|book with|meet with|hire) me\b|\bI(?:'ll| will) (?:review|prepare|file|handle|send|reply|get back|call)\b")


def check_directions(rel, h, v, errs):
    for name, ref, tgt in DIR_RULES:
        targets = [m.start() for m in re.finditer(tgt, h, re.I)]
        for m in re.finditer(ref, v, re.I | re.S):
            d = (m.groupdict().get("dir") or m.groupdict().get("dir2") or "").lower()
            ok = any(t > m.end() for t in targets) if d == "below" else any(t < m.start() for t in targets)
            if not ok:
                snip = " ".join(v[max(0, m.start() - 40):m.end() + 20].split())
                errs.append(f'{rel}: says the {name} is "{d}" but it is not {d} this sentence: "...{snip}..." '
                            f"(say where it really is, or link to it)")


def check_kit_css(errs):
    """Rule 6 (CSS): footnote spacing lives in the kit and blog.css; fail if someone weakens it."""
    def px(css, sel, prop):
        m = re.search(re.escape(sel) + r"\{[^}]*?\b" + prop + r":(\d+)px", css)
        return int(m.group(1)) if m else None
    import ui_kit
    blog = (SITE / "blog" / "blog.css").read_text(encoding="utf-8")
    for css, sel, prop, need in [(blog, ".disclaimer", "margin-top", 16),
                                 (ui_kit.UI_CSS, ".fineprint", "padding-top", 40),
                                 (ui_kit.UI_CSS, ".fineprint", "padding-bottom", 48),
                                 (ui_kit.UI_CSS, "main>.llc-sec:last-child", "padding-bottom", 48),
                                 (ui_kit.UI_CSS, "main>.tinfo:last-child", "padding-bottom", 32)]:
        got = px(css, sel, prop)
        if got is None or got < need:
            errs.append(f"CSS: {sel} needs {prop} >= {need}px (found {got}); fine print must not touch the footer")


def page_ids(path, cache={}):
    if path not in cache:
        cache[path] = set(re.findall(r'\b(?:id|name)="([^"]+)"', path.read_text(encoding="utf-8", errors="ignore")))
    return cache[path]


def resolve(url):
    """Internal URL path -> built file, or None."""
    p = url.split("?")[0]
    cands = [SITE / p.lstrip("/")]
    if p.endswith("/"):
        cands = [SITE / p.lstrip("/") / "index.html"]
    else:
        cands += [SITE / (p.lstrip("/") + ".html"), SITE / p.lstrip("/") / "index.html"]
    return next((c for c in cands if c.is_file()), None)


def redirect_sources():
    f = SITE / "_redirects"
    srcs = []
    if f.exists():
        for line in f.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                srcs.append(line.split()[0])
    return srcs


def check_links(rel, h, errs, redirects):
    ids = page_ids(SITE / rel)
    body = re.sub(r"<script\b.*?</script>", "", h, flags=re.S | re.I)
    for frag in set(re.findall(r'href="#([^"]+)"', body)):
        if frag not in ids:
            errs.append(f"{rel}: link to #{frag} but no element has that id")
    for url in set(re.findall(r'href="(/[^"#]*)(?:#([^"]*))?"', body)):
        path, frag = url
        if path.startswith("//") or path.startswith("/cdn-cgi/") or path.startswith("/api/") or path.startswith("/u/"):
            continue
        target = resolve(path)
        if target is None:
            if not any(path == r or (r.endswith("*") and path.startswith(r[:-1])) or path.rstrip("/") == r.rstrip("/") for r in redirects):
                errs.append(f"{rel}: broken internal link {path}")
            continue
        if frag and target.suffix == ".html" and frag not in page_ids(target):
            errs.append(f"{rel}: link {path}#{frag} but that page has no id=\"{frag}\"")


def check_copy(rel, h, v, errs):
    text = " ".join(v.split())
    for m in PLACEHOLDER.finditer(text):
        errs.append(f'{rel}: placeholder text "{m.group()}" near "...{text[max(0, m.start() - 40):m.end() + 30]}..."')
    for m in PHONE_RE.finditer(text):
        if re.sub(r"\D", "", m.group()) != "3472054468":
            errs.append(f"{rel}: unexpected phone number {m.group()} (use (347) 205-4468)")
    for t in re.findall(r'href="tel:([^"]+)"', h):
        if re.sub(r"\D", "", t)[-10:] != "3472054468":
            errs.append(f"{rel}: tel: link {t} is not +13472054468")
    for e in re.findall(r'href="mailto:([^"?]+)', h):
        if e.lower() != "info@mfa-advisory.com":
            errs.append(f"{rel}: mailto {e} (use info@mfa-advisory.com)")
    for m in re.finditer(r"([A-Z][^.!?]{24,}[.!?])\s+\1", text):
        errs.append(f'{rel}: sentence repeated back-to-back: "{m.group(1)[:80]}"')
    for m in FIRM_I.finditer(text):
        errs.append(f'{rel}: firm-voice "{m.group()}"; write "we"/"our team" for MFA, or "Zain" for the person')
    for m in re.finditer(r'<section\b([^>]*)>\s*<p class="disclaimer">.*?</p>\s*</section>', h, re.S):
        if "fineprint" not in m.group(1):
            errs.append(f'{rel}: stand-alone disclaimer section without .fineprint (use ui_kit.fineprint())')


RENDER_JS = r"""() => {
 document.querySelectorAll('.rv').forEach(e=>e.classList.add('in'));
 const st=document.createElement('style'); st.textContent='*{transition:none!important;animation:none!important}'; document.head.appendChild(st);
 const foots=[...document.querySelectorAll('footer, .bfoot')]; const foot=foots[foots.length-1]; if(!foot) return [];
 const ft=foot.getBoundingClientRect().top+scrollY, out=[]; let maxb=0, last='';
 for(const e of document.body.querySelectorAll('*')){
   if(foot.contains(e)||e.closest('.relnav,.final,.cta-block,dialog,[hidden],[aria-hidden="true"]')) continue;
   const cs=getComputedStyle(e); if(cs.position==='fixed'||cs.position==='sticky'||cs.display==='none'||cs.visibility==='hidden') continue;
   if(![...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())) continue;
   const r=e.getBoundingClientRect(); if(!r.height) continue; const b=r.bottom+scrollY;
   if(b<=ft+1&&b>maxb){maxb=b; last=(e.textContent||'').trim().slice(0,50);}
 }
 if(maxb && ft-maxb<40 && !document.querySelector('main>.relnav:last-child')) out.push(`last text "${last}" is ${Math.round(ft-maxb)}px above the footer (need 40)`);
 for(const d of document.querySelectorAll('.disclaimer,.fine,.note')){
   if(foot.contains(d)) continue; const r=d.getBoundingClientRect(); if(!r.height) continue;
   let p=d.previousElementSibling; while(p&&!p.getBoundingClientRect().height) p=p.previousElementSibling;
   if(p){const g=r.top-p.getBoundingClientRect().bottom; if(g<12) out.push(`.${d.className.split(' ')[0]} "${d.textContent.trim().slice(0,40)}" is ${Math.round(g)}px under the element above (need 12)`);}
 }
 return out;}"""


def render_check(pages, errs):
    """Rule 6 in a real browser: fine print and the last line of <main> keep their distance from the footer."""
    import functools, http.server, threading
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("UI: --render skipped (Playwright not installed)")
        return
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    block = ("googletagmanager", "google-analytics", "gumroad.com", "calendar.google", "stripe", "fonts.g")
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w in (390, 1300):
            pg = b.new_page(viewport={"width": w, "height": 900})
            pg.route("**/*", lambda r: r.abort() if any(x in r.request.url for x in block) else r.continue_())
            for rel in pages:
                pg.goto(base + rel.replace("index.html", ""), wait_until="load")
                for msg in pg.evaluate(RENDER_JS):
                    errs.append(f"{rel} @{w}px: {msg}")
        b.close()
    srv.shutdown()


def main():
    errs = []
    check_kit_css(errs)
    redirects = redirect_sources()
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
        v = visible(h)
        check_directions(rel, h, v, errs)
        check_links(rel, h, errs, redirects)
        check_copy(rel, h, v, errs)
    if "--render" in sys.argv:
        render_check([p.relative_to(SITE).as_posix() for p in pages
                      if "http-equiv=\"refresh\"" not in p.read_text(encoding="utf-8", errors="ignore")], errs)
    for e in errs:
        print("UI:", e)
    print(f"ui {'OK' if not errs else 'FAIL'}: {len(pages)} pages checked, {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
