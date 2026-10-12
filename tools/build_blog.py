#!/usr/bin/env python3
"""Build the MFA Insights blog (static) from content/posts/*.html.

Each post source file starts with a JSON metadata block inside an HTML comment:

    <!--meta
    { "title": "...", "slug": "...", "date": "2026-10-09", ... }
    -->
    <p>Article body HTML ...</p>

Outputs (all under site/):
    blog/index.html            listing page
    blog/<slug>/index.html     article pages (CTA, sources, disclaimer added automatically)
    blog/feed.xml              RSS 2.0 feed (used later for the weekly newsletter)
    sitemap.xml, robots.txt

Run from the repo root:  python3 tools/build_blog.py
Standard library only, so it runs anywhere (Netlify needs no build step; output is committed).
"""
import html, json, re, sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
import hashlib
CSS_VER = hashlib.sha1((SITE / "blog" / "blog.css").read_bytes()).hexdigest()[:10]  # cache-buster: new CSS = new URL
POSTS_DIR = ROOT / "content" / "posts"
PAGES_DIR = ROOT / "content" / "pages"
BASE = "https://mfa-advisory.com"
BOOK_URL = BASE + "/#book"
FORM_ENDPOINT = "https://formsubmit.co/ajax/info@mfa-advisory.com"   # same inbox as the site contact forms
EMAIL = "info@mfa-advisory.com"
# Newsletter signups go straight into MailerLite (account 2707043, embedded form "MFA Insights – website signup",
# group "MFA Insights Newsletter", double opt-in ON). Unsubscribes from emails are handled by MailerLite's own
# {$unsubscribe} link; the site's /newsletter/unsubscribe/ page is a backup that emails info@ via FormSubmit.
NEWSLETTER_ENDPOINT = "https://assets.mailerlite.com/jsonp/2707043/forms/201153544226604130/subscribe"
UNSUB_ENDPOINT = FORM_ENDPOINT
NEWSLETTER_NAME = "MFA Insights"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"/>'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400'
         '&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>')
MAIL_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2"/>'
             '<path d="m22 7-10 6L2 7"/></svg>')
TOPICS = ["IRS & Federal Tax", "New Jersey Tax", "New York Tax", "Tax Filing & Deadlines", "Tax Planning", "Accrual Accounting", "QuickBooks Tips & Updates",
          "Bookkeeping Best Practices", "Small & Mid-Sized Business Finance"]
BLOG_DESC = ("Practical tax, accounting, and QuickBooks guidance for individuals and small and mid-sized businesses: "
             "IRS, New Jersey and New York filing deadlines and tax updates, tax planning, accrual accounting, bookkeeping best practices, and QuickBooks tips.")
# Default author for every post (override per post with "author" in the meta).
AUTHOR_LINKEDIN = "https://www.linkedin.com/in/zainmerchant50"
AUTHOR_PATH = "/authors/zain-merchant/"
AUTHOR = {
    "name": "Zain Merchant",
    "credential": "ACCA",
    "title": "Founder & Principal, Merchant Financial Advisory",
    "url": BASE + AUTHOR_PATH,
    "linkedin": AUTHOR_LINKEDIN,
    "sameAs": [AUTHOR_LINKEDIN, "https://www.upwork.com/freelancers/zainmerchant50", "https://www.fiverr.com/zainmerchant50"],
    "bio": ("Zain Merchant, ACCA, is the founder and principal of Merchant Financial Advisory. A QuickBooks ProAdvisor "
            "with eight years of Big Four audit and tax experience, he helps individuals and small and mid-sized businesses with "
            "accrual accounting, clean books, and tax filing and preparation."),
}


def person_ld(a):
    return {"@type": "Person", "@id": a["url"] + "#person", "name": a["name"], "url": a["url"], "jobTitle": a["title"],
            "honorificSuffix": a["credential"], "sameAs": a["sameAs"],
            "worksFor": {"@type": "Organization", "name": "Merchant Financial Advisory LLC", "url": BASE}}


LI_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.23 0z"/></svg>')


def author_box(a):
    initials = "".join(w[0] for w in a["name"].split()[:2])
    return (f'<aside class="author" aria-label="About the author"><div class="av" aria-hidden="true">{initials}</div>'
            f'<div><span class="author-k">About the author</span>'
            f'<a class="author-n" href="{a["url"]}" rel="author">{esc(a["name"])}, {esc(a["credential"])}</a>'
            f'<span class="author-t">{esc(a["title"])}</span><p>{esc(a["bio"])}</p>'
            f'<a class="author-li" href="{a["linkedin"]}" target="_blank" rel="noopener">{LI_ICON}Connect on LinkedIn</a>'
            f'<a class="author-more" href="{a["url"]}">More articles by {esc(a["name"].split()[0])} →</a></div></aside>')


DISCLAIMER = ("This article is general information, not tax, legal, or financial advice, and reading it does not "
              "create a client relationship. Tax rules change and every situation is different; confirm the details "
              "for your situation with a qualified professional before acting.")

esc = lambda s: html.escape(str(s), quote=True)


def load_posts():
    posts = []
    for f in sorted(POSTS_DIR.glob("*.html")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)\Z", raw, re.S)
        if not m:
            sys.exit(f"{f.name}: missing <!--meta {{...}} --> header")
        meta, body = json.loads(m.group(1)), m.group(2).strip()
        for k in ("title", "slug", "date", "description", "dek", "category", "cover", "coverAlt", "og", "sources"):
            if k not in meta:
                sys.exit(f"{f.name}: meta missing '{k}'")
        if meta.get("status", "published") != "published":
            continue
        words = len(re.sub(r"<[^>]+>", " ", body).split())
        meta["minutes"] = max(1, round(words / 225))
        meta["body"] = body
        meta["dt"] = datetime.fromisoformat(meta["date"]).replace(tzinfo=timezone.utc)
        posts.append(meta)
    posts.sort(key=lambda p: (p["dt"], p.get("time", "00:00")), reverse=True)  # optional "time" (HH:MM) breaks same-day ties
    return posts


def nav(active):
    def a(href, label, key):
        return f'<a href="{href}"{" class=on" if key == active else ""}>{label}</a>'
    return f'''<header class="bnav"><div class="wrap bnav-in">
  <a href="/" class="brand" aria-label="Merchant Financial Advisory — home"><img src="/apple-touch-icon.png" alt="" width="44" height="44"/><span class="brand-txt"><b>Merchant</b><i>Financial Advisory</i></span></a>
  <nav class="bnav-links" aria-label="Main navigation">{a("/#services","Services","s")}{a("/blog/","Insights","blog")}{a("/#book","Book","b")}<a href="/#contact" class="cta">{MAIL_ICON}Contact Us</a></nav>
</div></header>'''


FOOT = f'''<footer class="bfoot"><div class="wrap">
  <span>© {datetime.now().year} Merchant Financial Advisory LLC · Princeton, NJ · <a href="tel:+13472054468">(347) 205-4468</a> · Serving New Jersey, New York and clients nationwide</span>
  <nav><a href="/">Home</a><a href="/blog/">Insights</a><a href="/newsletter/">Newsletter</a><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a><a href="/disclaimer.html">Disclaimer</a><a href="/blog/feed.xml">RSS</a><a href="mailto:{EMAIL}">{EMAIL}</a></nav>
  <p class="legal">Content on this site is general information only and is not tax, accounting, legal, or financial advice. Reading it or contacting us does not create a client relationship. See our <a href="/disclaimer.html">Disclaimer</a>.</p>
</div></footer>'''


def head(title, desc, url, image, extra="", keywords=None, og_type="website"):
    kw = f'<meta name="keywords" content="{esc(", ".join(keywords))}"/>' if keywords else ""
    return f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}"/>{kw}
<link rel="canonical" href="{url}"/>
<meta property="og:type" content="{og_type}"/><meta property="og:site_name" content="Merchant Financial Advisory"/>
<meta property="og:title" content="{esc(title)}"/><meta property="og:description" content="{esc(desc)}"/>
<meta property="og:url" content="{url}"/><meta property="og:image" content="{image}"/>
<meta name="twitter:card" content="summary_large_image"/><meta name="twitter:image" content="{image}"/>
<link rel="icon" href="/favicon.png"/><link rel="apple-touch-icon" href="/apple-touch-icon.png"/>
<link rel="alternate" type="application/rss+xml" title="MFA Insights" href="/blog/feed.xml"/>
{FONTS}<link rel="stylesheet" href="/blog/blog.css?v={CSS_VER}"/>
{extra}</head>'''


def cta(p):
    topic = p.get("ctaTopic", "your situation")
    return f'''<section class="cta-block" aria-label="Book a consultation"><div class="cta-card">
  <span class="eyebrow">Talk to MFA</span>
  <h2>{esc(p.get("ctaHeadline", "Want a second set of eyes before you act?"))}</h2>
  <p>Book a 30-minute consultation to talk through {esc(topic)}, or email us at <a href="mailto:{EMAIL}" style="color:#D8B769;border-bottom:1px solid rgba(216,183,105,.5)">{EMAIL}</a>. We provide tax and accounting solutions for individuals and small and mid-sized businesses in New Jersey, New York and nationwide.</p>
  <div class="cta-btns"><a class="btn btn-gold" href="{BOOK_URL}">Book a consultation</a><a class="btn btn-line" href="mailto:{EMAIL}?subject={esc(p['title'])}">Email info@mfa-advisory.com</a></div>
</div></section>'''


def ask_box(p):
    """Private 'Have a question about this?' form on every post. Sent by FormSubmit to EMAIL (not published)."""
    return f'''<section class="ask" aria-label="Ask a question about this article">
  <h2>Have a question about this?</h2>
  <p>Ask us privately. Your question goes straight to our inbox, not onto the page, and we reply by email within one to three business days. Please don't include Social Security or account numbers.</p>
  <form class="ask-f" data-post="{esc(p["title"])}" novalidate>
    <div class="ask-row"><label>Name<input name="name" autocomplete="name" required/></label><label>Email<input name="email" type="email" autocomplete="email" required/></label></div>
    <label>Your question<textarea name="question" rows="4" required placeholder="Type your question about this article"></textarea></label>
    <input class="ask-hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
    <button class="btn btn-ink" type="submit">Send my question</button>
    <p class="ask-st" role="status" aria-live="polite"></p>
  </form>
  <p class="ask-done" hidden>Thanks, your question is in. We'll reply by email within one to three business days.</p>
</section>
<script>
(function(){{var s=document.currentScript.previousElementSibling,f=s.querySelector('.ask-f'),st=s.querySelector('.ask-st');
f.addEventListener('submit',function(e){{e.preventDefault();if(f._honey.value)return;if(!f.checkValidity()){{f.reportValidity();return;}}
var b=f.querySelector('button'),l=b.textContent;b.disabled=true;b.textContent='Sending\u2026';var d=new FormData(f);
d.append('article',f.dataset.post);d.append('page',location.href);d.append('_subject','Blog question: '+f.dataset.post);d.append('_captcha','false');d.append('_template','table');
fetch('{FORM_ENDPOINT}',{{method:'POST',headers:{{'Accept':'application/json'}},body:d}}).then(function(r){{if(!r.ok)throw 0;return r.json();}})
.then(function(j){{if(j.success===false||j.success==='false')throw 0;f.hidden=true;s.querySelector('.ask-done').hidden=false;}})
.catch(function(){{st.textContent='Couldn’t send. Please email {EMAIL} directly.';b.disabled=false;b.textContent=l;}});}});}})();
</script>'''


SHARE_ICONS = {
    "linkedin": '<path fill="currentColor" d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.23 0z"/>',
    "x": '<path fill="currentColor" d="M18.24 2.25h3.31l-7.23 8.26 8.5 11.24h-6.66l-5.21-6.82-5.97 6.82H1.67l7.73-8.84L1.25 2.25h6.83l4.71 6.23 5.45-6.23zm-1.16 17.52h1.83L7.08 4.13H5.12z"/>',
    "facebook": '<path fill="currentColor" d="M24 12.07C24 5.41 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.04V9.41c0-3.02 1.8-4.7 4.54-4.7 1.31 0 2.68.24 2.68.24v2.97h-1.5c-1.5 0-1.96.93-1.96 1.89v2.26h3.32l-.53 3.5h-2.8V24C19.62 23.1 24 18.1 24 12.07"/>',
    "email": '<g fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/></g>',
    "link": '<g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></g>',
    "share": '<g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="m16 6-4-4-4 4M12 2v13"/></g>',
}


def share_bar(p, url, variant=""):
    from urllib.parse import quote
    u, t = quote(url, safe=""), quote(p["title"], safe="")
    ic = lambda k: f'<svg viewBox="0 0 24 24" aria-hidden="true">{SHARE_ICONS[k]}</svg>'
    links = [
        ("linkedin", "Share on LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={u}"),
        ("x", "Share on X", f"https://twitter.com/intent/tweet?url={u}&text={t}"),
        ("facebook", "Share on Facebook", f"https://www.facebook.com/sharer/sharer.php?u={u}"),
        ("email", "Share by email", f"mailto:?subject={t}&body={quote(p['description'] + ' ', safe='')}{u}"),
    ]
    a = "".join(f'<a class="sh sh-{k}" href="{h}" target="_blank" rel="noopener" aria-label="{lbl}" title="{lbl}">{ic(k)}</a>'
                for k, lbl, h in links)
    return (f'<div class="share {variant}" data-url="{esc(url)}" data-title="{esc(p["title"])}">'
            f'<span class="share-lbl">Share</span>'
            f'<a class="sh sh-li-wide" href="{links[0][2]}" target="_blank" rel="noopener">{ic("linkedin")}<span>Post on LinkedIn</span></a>'
            f'{a}<button type="button" class="sh sh-copy" aria-label="Copy link">{ic("link")}<span>Copy link</span></button>'
            f'<button type="button" class="sh sh-native" aria-label="Share" hidden>{ic("share")}</button></div>')


SHARE_JS = """<script>
(function(){document.querySelectorAll('.share').forEach(function(b){
 var url=b.getAttribute('data-url'),title=b.getAttribute('data-title');
 var c=b.querySelector('.sh-copy'),lbl=c.querySelector('span');
 c.addEventListener('click',function(){
  var done=function(){lbl.textContent='Link copied';c.classList.add('ok');setTimeout(function(){lbl.textContent='Copy link';c.classList.remove('ok')},2200)};
  if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(url).then(done,fallback)}else{fallback()}
  function fallback(){var t=document.createElement('textarea');t.value=url;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();try{document.execCommand('copy');done()}catch(e){prompt('Copy this link:',url)}document.body.removeChild(t)}
 });
 var n=b.querySelector('.sh-native');
 if(navigator.share&&matchMedia('(pointer:coarse)').matches){n.hidden=false;n.addEventListener('click',function(){navigator.share({title:title,url:url}).catch(function(){})})}
});})();
</script>"""


def faq_schema(body):
    m = re.search(r"<h2>Quick answers</h2>(.*)", body, re.S)
    if not m:
        return None
    pairs = re.findall(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", m.group(1), re.S)
    strip = lambda h: html.unescape(re.sub(r"<[^>]+>", "", h)).strip()
    if not pairs:
        return None
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in pairs]}



def seo_lint(p):
    """Warn when target keywords aren't actually used on the page (meta keywords alone don't rank)."""
    norm = lambda t: re.sub(r"[^a-z0-9$%]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)).lower()).strip()
    body, title = norm(p["body"]), norm(p.get("seoTitle", "") + " " + p["title"])
    heads = norm(" ".join(re.findall(r"<h[23]>(.*?)</h[23]>", p["body"])))
    intro = " ".join(body.split()[:160])
    warn = []
    kws = p.get("keywords", [])
    if kws:
        prim = norm(kws[0]).split()
        if not all(w in title.split() for w in prim):
            warn.append(f"primary keyword '{kws[0]}' not fully in title/seoTitle")
        if norm(kws[0]) not in intro and norm(kws[0]) not in heads:
            warn.append(f"primary keyword '{kws[0]}' not in first 160 words or a heading")
    for k in kws:
        if norm(k) not in body and norm(k) not in title:
            warn.append(f"keyword '{k}' never appears in the article text")
    if not 120 <= len(p["description"]) <= 165:
        warn.append(f"description is {len(p['description'])} chars (aim 140-160)")
    for w in warn:
        print(f"  SEO [{p['slug']}]: {w}")
    return warn


def tags_block(p):
    kws = p.get("keywords", [])
    if not kws:
        return ""
    return ('<div class="tags"><span class="tags-k">Topics covered</span><ul>'
            + "".join(f"<li>{esc(k)}</li>" for k in kws) + "</ul></div>")


# ---------- Key dates (savable calendar) ----------
def _ics_text(t):
    return (t.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n"))


def _ics_fold(line):
    if len(line.encode("utf-8")) <= 74:
        return line
    out, cur = [], b""
    for ch in line:
        e = ch.encode("utf-8")
        if len(cur) + len(e) > 73:
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += e
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def ics_calendar(events, name):
    """events: [{date, title, note, url, uid}] -> RFC 5545 all-day events with a 7-day reminder."""
    from datetime import timedelta
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Merchant Financial Advisory//MFA Insights//EN",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{_ics_text(name)}", "X-WR-TIMEZONE:America/New_York",
         "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D"]
    for e in events:
        d = datetime.fromisoformat(e["date"]).date()
        desc = (e.get("note", "") + ("\n\n" if e.get("note") else "") + "Details: " + e["url"]
                + "\nGeneral information, not tax advice. Merchant Financial Advisory, mfa-advisory.com")
        L += ["BEGIN:VEVENT", f"UID:{e['uid']}", f"DTSTAMP:{stamp}",
              f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
              f"SUMMARY:{_ics_text(e['title'])}", f"DESCRIPTION:{_ics_text(desc)}", f"URL:{e['url']}",
              "TRANSP:TRANSPARENT", "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_ics_text(e['title'])}",
              "TRIGGER:-P7D", "END:VALARM", "END:VEVENT"]
    L.append("END:VCALENDAR")
    return "\r\n".join(_ics_fold(x) for x in L) + "\r\n"


def post_events(p):
    url = f"{BASE}/blog/{p['slug']}/"
    return [{"date": k["date"], "title": k["title"], "note": k.get("note", ""), "url": url,
             "uid": k.get("uid") or f"{p['slug']}-{i}@mfa-advisory.com"} for i, k in enumerate(p.get("keyDates", []))]


def gcal_link(e):
    from datetime import timedelta
    from urllib.parse import urlencode
    d = datetime.fromisoformat(e["date"]).date()
    return "https://calendar.google.com/calendar/render?" + urlencode({
        "action": "TEMPLATE", "text": e["title"], "dates": f"{d:%Y%m%d}/{d + timedelta(days=1):%Y%m%d}",
        "details": (e.get("note", "") + "\n\nDetails: " + e["url"]).strip()})


def keydates_block(p):
    ev = post_events(p)
    if not ev:
        return ""
    rows = "".join(
        f'<li><span class="kd-d">{datetime.fromisoformat(e["date"]):%a, %b %-d, %Y}</span>'
        f'<span class="kd-t"><b>{esc(e["title"])}</b>{(" " + esc(e["note"])) if e["note"] else ""}</span>'
        f'<a class="kd-g" href="{esc(gcal_link(e))}" target="_blank" rel="noopener">+ Google Calendar</a></li>' for e in ev)
    return f"""<section class="keydates" aria-label="Key dates">
  <h2>Save the key dates</h2>
  <ul class="kd-list">{rows}</ul>
  <div class="kd-btns"><a class="btn btn-ink" href="key-dates.ics" download>Add to my calendar (.ics)</a>
  <a class="btn btn-line-ink" href="webcal://mfa-advisory.com/newsletter/mfa-key-dates.ics">Subscribe to every MFA key date</a></div>
  <p class="kd-note">The .ics file works with Apple Calendar, Outlook and Google Calendar. The subscription updates itself whenever we publish a new deadline.</p>
</section>"""


# ---------- Newsletter signup / unsubscribe ----------
NL_JS = """<script>
(function(){document.querySelectorAll('form.nl-f').forEach(function(f){var st=f.querySelector('.nl-st');
function done(){f.hidden=true;var ok=f.parentNode.querySelector('.nl-done');if(ok)ok.hidden=false;}
f.addEventListener('submit',function(e){e.preventDefault();if(f._honey&&f._honey.value)return;if(!f.checkValidity()){f.reportValidity();return;}
var b=f.querySelector('button'),l=b.textContent;b.disabled=true;b.textContent='Sending\\u2026';
var unsub=f.dataset.kind==='unsubscribe';
function fail(){st.textContent='Couldn\\u2019t send. Please email %(email)s with the word '+(unsub?'UNSUBSCRIBE':'SUBSCRIBE')+'.';b.disabled=false;b.textContent=l;}
if(unsub){var d=new FormData(f);d.append('page',location.href);d.append('_captcha','false');d.append('_template','table');
 d.append('_subject','Newsletter UNSUBSCRIBE: '+(f.email.value||''));d.append('list','MFA Insights');
 fetch('%(unsub)s',{method:'POST',headers:{'Accept':'application/json'},body:d}).then(function(r){if(!r.ok)throw 0;return r.json();})
 .then(function(j){if(j.success===false||j.success==='false')throw 0;done();}).catch(fail);return;}
var m=new URLSearchParams();m.append('fields[email]',f.email.value.trim());if(f.name&&f.name.value)m.append('fields[name]',f.name.value.trim());
m.append('ml-submit','1');m.append('anticsrf','true');
fetch('%(ml)s',{method:'POST',headers:{'Accept':'application/json'},body:m}).then(function(r){return r.json();})
.then(function(j){if(j&&j.success===false)throw 0;done();})
.catch(function(){fetch('%(ml)s',{method:'POST',mode:'no-cors',body:m}).then(done).catch(fail);});});});})();
</script>""" % {"ml": NEWSLETTER_ENDPOINT, "unsub": UNSUB_ENDPOINT, "email": EMAIL}


def nl_form(kind="subscribe", variant=""):
    if kind == "unsubscribe":
        return f"""<form class="nl-f {variant}" data-kind="unsubscribe" novalidate>
  <label>Email address<input name="email" type="email" autocomplete="email" required/></label>
  <label>Anything we could do better? (optional)<input name="reason"/></label>
  <input class="ask-hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
  <button class="btn btn-ink" type="submit">Unsubscribe me</button>
  <p class="nl-st" role="status" aria-live="polite"></p>
</form>
<p class="nl-done" hidden>You're unsubscribed and won't get any more {NEWSLETTER_NAME} emails. If you change your mind, you can sign up again any time.</p>"""
    return f"""<form class="nl-f {variant}" data-kind="subscribe" novalidate>
  <div class="nl-row"><label>First name<input name="name" autocomplete="given-name"/></label><label>Email<input name="email" type="email" autocomplete="email" required/></label></div>
  <input class="ask-hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
  <button class="btn btn-gold" type="submit">Subscribe</button>
  <p class="nl-fine">Up to 3 short emails a week. Unsubscribe from any email in one click. We never sell or share your address. <a href="/privacy.html">Privacy Policy</a>.</p>
  <p class="nl-st" role="status" aria-live="polite"></p>
</form>
<p class="nl-done" hidden>Almost done: check your inbox and click the confirmation link to join {NEWSLETTER_NAME}. (If you don't see it in a minute, check Promotions or Spam.)</p>"""


def nl_box():
    return f"""<section class="nl-box" aria-label="Subscribe to {NEWSLETTER_NAME}">
  <span class="eyebrow">MFA Insights newsletter</span>
  <h2>Get key tax dates and new articles by email</h2>
  <p>Every new MFA Insights article, the IRS, New Jersey and New York deadlines that matter, and a calendar you can save. For individuals and small and mid-sized businesses.</p>
  {nl_form("subscribe", "nl-dark")}
</section>"""


def build_newsletter_pages(posts):
    nl = SITE / "newsletter"
    (nl / "unsubscribe").mkdir(parents=True, exist_ok=True)
    events = sorted((e for p in posts for e in post_events(p)), key=lambda e: e["date"])
    with open(nl / "mfa-key-dates.ics", "w", encoding="utf-8", newline="") as fh:
        fh.write(ics_calendar(events, "MFA Key Tax & Accounting Dates"))
    today = datetime.now(timezone.utc).date().isoformat()
    upcoming = [e for e in events if e["date"] >= today][:8]
    up = "".join(f'<li><span class="kd-d">{datetime.fromisoformat(e["date"]):%a, %b %-d, %Y}</span><span class="kd-t"><b>{esc(e["title"])}</b></span>'
                 f'<a class="kd-g" href="{esc(e["url"])}">Read more</a></li>' for e in upcoming)
    recent = "".join(f'<li><a href="/blog/{p["slug"]}/"><b>{esc(p["title"])}</b></a> <span class="m">{p["dt"]:%b %-d, %Y}</span></li>' for p in posts[:5])
    desc = ("Subscribe to MFA Insights: emails with new tax, accounting and QuickBooks articles, key IRS and New Jersey "
            "deadlines, and a savable calendar for small businesses.")
    page = f"""{head("Subscribe to MFA Insights: Tax Dates, Accounting & QuickBooks Tips by Email", desc, BASE + "/newsletter/", BASE + "/apple-touch-icon.png")}
<body>{nav("blog")}
<header class="ahead"><div class="wrap"><div class="crumbs"><a href="/">Home</a> / <a href="/blog/">Insights</a> / Newsletter</div>
<span class="eyebrow">Newsletter</span><h1>MFA Insights, in your inbox</h1>
<p class="dek">New articles, the tax and accounting dates that matter, and a calendar you can save. Plain English, no hype, for individuals and small and mid-sized businesses.</p></div></header>
<main><article class="article nl-page">
{nl_box()}
<h2>What you'll get</h2>
<ul><li><strong>Each new article</strong> on IRS and federal tax, New Jersey and New York tax, tax planning, accrual accounting, bookkeeping and QuickBooks, delivered in full.</li>
<li><strong>Key dates</strong> with one-click "add to calendar" links.</li>
<li><strong>A live MFA key-dates calendar</strong> you can subscribe to in Apple Calendar, Outlook or Google Calendar. It updates itself: new deadlines appear and changed dates move automatically.</li></ul>
<h2 id="calendar">Upcoming key dates</h2>
{f'<ul class="kd-list">{up}</ul>' if up else '<p>New dates are added with each article.</p>'}
<div class="kd-btns"><a class="btn btn-ink" href="webcal://mfa-advisory.com/newsletter/mfa-key-dates.ics">Subscribe to the key-dates calendar</a><a class="btn btn-line-ink" href="/newsletter/mfa-key-dates.ics" download>Download .ics</a></div>
<h2>Latest articles</h2><ul class="nl-recent">{recent}</ul>
<p class="disclaimer">Newsletter content is general information, not tax, accounting, legal or financial advice. Unsubscribe any time from the link in any email or at <a href="/newsletter/unsubscribe/">mfa-advisory.com/newsletter/unsubscribe</a>.</p>
</article></main>
{FOOT}{NL_JS}</body></html>"""
    (nl / "index.html").write_text(page, encoding="utf-8")
    un = f"""{head("Unsubscribe | MFA Insights", "Unsubscribe from the MFA Insights newsletter.", BASE + "/newsletter/unsubscribe/", BASE + "/apple-touch-icon.png", '<meta name="robots" content="noindex"/>')}
<body>{nav("blog")}
<header class="ahead"><div class="wrap"><span class="eyebrow">Newsletter</span><h1>Unsubscribe from MFA Insights</h1>
<p class="dek">Sorry to see you go. Confirm your email below and we'll take you off the list.</p></div></header>
<main><article class="article"><section class="ask">{nl_form("unsubscribe")}</section>
<p>Prefer email? Write to <a href="mailto:{EMAIL}?subject=Unsubscribe">{EMAIL}</a> with the subject "Unsubscribe".</p></article></main>
{FOOT}{NL_JS}
<script>(function(){{var q=new URLSearchParams(location.search).get('e');if(q){{var i=document.querySelector('form.nl-f input[name=email]');if(i)i.value=q;}}}})();</script>
</body></html>"""
    (nl / "unsubscribe" / "index.html").write_text(un, encoding="utf-8")


def build_post(p):
    A = {**AUTHOR, **p.get("author", {})}
    url = f"{BASE}/blog/{p['slug']}/"
    img = url + p["og"]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": p["title"], "description": p["description"],
         "datePublished": p["date"], "dateModified": p.get("updated", p["date"]),
         "image": img, "mainEntityOfPage": url, "keywords": ", ".join(p.get("keywords", [])),
         "author": person_ld(A),
         "publisher": {"@type": "Organization", "name": "Merchant Financial Advisory LLC",
                       "logo": {"@type": "ImageObject", "url": BASE + "/apple-touch-icon.png"}}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Insights", "item": BASE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": url}]}]}
    faq = faq_schema(p["body"])
    if faq:
        ld["@graph"].append(faq)
    extra = (f'<meta property="article:published_time" content="{p["date"]}"/>'
             f'<script type="application/ld+json">{json.dumps(ld)}</script>')
    sources = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a></li>'
                      for s in p["sources"])
    nice = p["dt"].strftime("%B %-d, %Y")
    asof = datetime.fromisoformat(p.get("factsAsOf", p["date"])).strftime("%B %-d, %Y")
    page = f'''{head(p.get("seoTitle", p["title"]) + " | MFA Insights", p["description"], url, img, extra, p.get("keywords"), "article")}
<body>{nav("blog")}
<header class="ahead"><div class="wrap">
  <div class="crumbs"><a href="/">Home</a> / <a href="/blog/">Insights</a> / {esc(p["category"])}</div>
  <span class="eyebrow">{esc(p["category"])}</span>
  <h1>{esc(p["title"])}</h1>
  <p class="dek">{esc(p["dek"])}</p>
  <div class="ameta"><span>By <a class="byline" href="{A["url"]}" rel="author"><b>{esc(A["name"])}, {esc(A["credential"])}</b></a></span><span>{nice}</span><span>{p["minutes"]} min read</span></div>
  {share_bar(p, url, "share-dark")}
</div></header>
<main><article class="article">
{p["body"]}
{keydates_block(p)}
{tags_block(p)}
<div class="share-end"><p>Found this useful? Share it with someone who's dealing with the same thing.</p>{share_bar(p, url)}</div>
{nl_box()}
{ask_box(p)}
{author_box(A)}
<section class="sources"><h2>Sources</h2><ul>{sources}</ul>
<p class="disclaimer">Facts checked against the sources above as of {asof}. {DISCLAIMER}</p></section>
</article>
{cta(p)}</main>
{FOOT}{SHARE_JS}{NL_JS}</body></html>'''
    out = SITE / "blog" / p["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    if p.get("keyDates"):
        with open(out.parent / "key-dates.ics", "w", encoding="utf-8", newline="") as fh:
            fh.write(ics_calendar(post_events(p), p["title"]))


def build_index(posts):
    cards = "".join(f'''<a class="pcard" href="/blog/{p["slug"]}/">
  <div class="thumb"><img src="/blog/{p["slug"]}/{p["og"]}" alt="{esc(p["coverAlt"])}" loading="lazy" width="1200" height="630"/></div>
  <div class="body"><span class="meta">{esc(p["category"])} · {p["dt"].strftime("%b %-d, %Y")}</span>
  <h2>{esc(p["title"])}</h2><p>{esc(p["description"])}</p><span class="more">Read the article →</span></div></a>''' for p in posts)
    desc = BLOG_DESC
    og = f'{BASE}/blog/{posts[0]["slug"]}/{posts[0]["og"]}' if posts else BASE + "/apple-touch-icon.png"
    page = f'''{head("MFA Insights: Tax, Accounting & QuickBooks Tips for Individuals and Small Businesses", desc, BASE + "/blog/", og)}
<body>{nav("blog")}
<header class="bhero"><div class="wrap"><span class="eyebrow">MFA Insights</span>
<h1>Tax, accounting &amp; QuickBooks, <em>made usable.</em></h1>
<p>Practical guidance for individuals and small and mid-sized businesses, from filing deadlines and tax planning to accrual accounting, clean books and getting more out of QuickBooks.</p>
<ul class="topics" aria-label="Topics we cover">{"".join(f"<li>{esc(t)}</li>" for t in TOPICS)}</ul></div></header>
<main class="wrap plist">{cards}</main>
<div class="wrap nl-wrap">{nl_box()}</div>
{cta({"title": "Question from the MFA blog", "ctaHeadline": "Have a question about your taxes, books, or QuickBooks?", "ctaTopic": "your taxes, accounting, or QuickBooks setup"})}
{FOOT}{NL_JS}</body></html>'''
    (SITE / "blog" / "index.html").write_text(page, encoding="utf-8")


def build_feed(posts):
    items = "".join(f'''<item><title>{esc(p["title"])}</title><link>{BASE}/blog/{p["slug"]}/</link>
<guid isPermaLink="true">{BASE}/blog/{p["slug"]}/</guid><pubDate>{format_datetime(p["dt"])}</pubDate>
<category>{esc(p["category"])}</category><description>{esc(p["description"])}</description>
<enclosure url="{BASE}/blog/{p["slug"]}/{p["og"]}" type="image/png" length="0"/></item>''' for p in posts)
    feed = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>MFA Insights</title><link>{BASE}/blog/</link>
<atom:link href="{BASE}/blog/feed.xml" rel="self" type="application/rss+xml"/>
<description>{esc(BLOG_DESC)}</description>
<language>en-us</language>{items}</channel></rss>'''
    (SITE / "blog" / "feed.xml").write_text(feed, encoding="utf-8")


def build_pages():
    out = []
    for f in sorted(PAGES_DIR.glob("*.html")):
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)\Z", f.read_text(encoding="utf-8"), re.S)
        meta, body = json.loads(m.group(1)), m.group(2).strip()
        url = f"{BASE}/{meta['slug']}.html"
        upd = datetime.fromisoformat(meta["updated"]).strftime("%B %-d, %Y")
        page = f'''{head(meta["title"] + " | Merchant Financial Advisory", meta["description"], url, BASE + "/apple-touch-icon.png")}
<body>{nav("")}
<header class="ahead"><div class="wrap"><div class="crumbs"><a href="/">Home</a> / {esc(meta["title"])}</div>
<span class="eyebrow">Legal</span><h1>{esc(meta["title"])}</h1><div class="ameta"><span>Last updated {upd}</span></div></div></header>
<main><article class="article legalpage">{body}</article></main>
{FOOT}</body></html>'''
        (SITE / f"{meta['slug']}.html").write_text(page, encoding="utf-8")
        out.append(meta)
    return out


def build_latest(posts, n=5):
    data = [{"title": p["title"], "url": f"/blog/{p['slug']}/", "date": p["date"], "category": p["category"],
             "thumb": f"/blog/{p['slug']}/{p['og']}", "description": p["description"]} for p in posts[:n]]
    (SITE / "blog" / "latest.json").write_text(json.dumps({"posts": data}, indent=1), encoding="utf-8")


def build_author(posts):
    a = AUTHOR
    url = a["url"]
    mine = [p for p in posts if {**AUTHOR, **p.get("author", {})}["name"] == a["name"]]
    items = "".join(f'<li><a href="/blog/{p["slug"]}/"><span class="m">{esc(p["category"])} · {p["dt"].strftime("%b %-d, %Y")}</span>'
                    f'<b>{esc(p["title"])}</b><span class="d">{esc(p["description"])}</span></a></li>' for p in mine)
    person = person_ld(a)
    person.update({"description": a["bio"], "image": BASE + "/apple-touch-icon.png",
                   "address": {"@type": "PostalAddress", "addressLocality": "Princeton", "addressRegion": "NJ", "addressCountry": "US"},
                   "knowsAbout": ["Tax preparation", "Tax planning", "Accrual accounting", "Bookkeeping", "QuickBooks Online",
                                  "Form 1099 reporting", "Financial reporting", "Internal controls", "SOX compliance", "Audit"]})
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "ProfilePage", "@id": url, "url": url, "name": f'{a["name"]}, {a["credential"]}', "mainEntity": {"@id": url + "#person"},
         "hasPart": [{"@type": "BlogPosting", "headline": p["title"], "url": f'{BASE}/blog/{p["slug"]}/'} for p in mine]},
        person]}
    desc = (f'{a["name"]}, ACCA, is a Princeton, NJ accountant and founder of Merchant Financial Advisory, writing on tax deadlines, '
            f'1099s, accrual accounting and QuickBooks for individuals and small businesses.')
    li_btn = f'<a class="btn btn-gold" href="{a["linkedin"]}" target="_blank" rel="noopener me">{LI_ICON}Connect on LinkedIn</a>'
    page = f"""{head(f'{a["name"]}, ACCA | Accountant & Tax Advisor, Princeton NJ | Merchant Financial Advisory', desc, url,
                 BASE + "/apple-touch-icon.png", f'<script type="application/ld+json">{json.dumps(ld)}</script>', None, "profile")}
<body>{nav("blog")}
<header class="ahead aprofile"><div class="wrap">
  <div class="crumbs"><a href="/">Home</a> / <a href="/blog/">Insights</a> / Authors</div>
  <div class="ap-row"><div class="ap-av" aria-hidden="true">ZM</div><div>
  <span class="eyebrow">Author</span>
  <h1>{esc(a["name"])}, {esc(a["credential"])}</h1>
  <p class="dek">Founder &amp; Principal of Merchant Financial Advisory, an accounting and tax solutions provider in Princeton, New Jersey, serving individuals and small and mid-sized businesses nationwide.</p>
  <div class="cta-btns">{li_btn}<a class="btn btn-line" href="/#book">Book a consultation</a></div></div></div>
</div></header>
<main><article class="article">
<h2>About Zain</h2>
<p>Zain Merchant is an ACCA-qualified accountant and the founder of Merchant Financial Advisory (MFA). Before starting MFA, he spent eight years at Big Four accounting firms, including PwC in New York, working on audits, SOX and internal-controls engagements for Fortune 500 financial services clients, with a rotation through tax.</p>
<p>Today he helps individuals, freelancers and small and mid-sized businesses keep accurate, accrual-basis books, stay on top of IRS and New Jersey filing deadlines, and get more out of QuickBooks. He is a certified QuickBooks ProAdvisor.</p>
<h2>What Zain writes about</h2>
<ul><li>Tax filing deadlines, IRS updates and New Jersey tax rules</li><li>Form 1099s, W-9s and year-end compliance</li><li>Accrual accounting, month-end close and clean books</li><li>QuickBooks Online tips, setup and cleanups</li><li>Tax planning for business owners and the self-employed</li></ul>
<h2>Articles by {esc(a["name"])}</h2>
<ul class="alist">{items}</ul>
<h2>Connect</h2>
<p><a href="{a["linkedin"]}" target="_blank" rel="noopener me">LinkedIn</a> · <a href="https://www.upwork.com/freelancers/zainmerchant50" target="_blank" rel="noopener me">Upwork</a> · <a href="https://www.fiverr.com/zainmerchant50" target="_blank" rel="noopener me">Fiverr</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
</article></main>
{FOOT}</body></html>"""
    out = SITE / AUTHOR_PATH.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


def build_sitemap(posts, pages=()):
    today = datetime.now(timezone.utc).date().isoformat()
    urls = [(BASE + "/", today), (BASE + "/blog/", posts[0]["date"] if posts else today)]
    urls += [(f'{BASE}/blog/{p["slug"]}/', p.get("updated", p["date"])) for p in posts]
    urls += [(AUTHOR["url"], posts[0]["date"] if posts else today), (BASE + "/newsletter/", posts[0]["date"] if posts else today)]
    for lp in ("union-city-nj", "princeton-nj"):   # Google Ads landing pages (tools/build_landing.py)
        if (SITE / lp / "index.html").exists():
            urls += [(f"{BASE}/{lp}/", today)]
    urls += [(f"{BASE}/{pg['slug']}.html", pg["updated"]) for pg in pages]
    body = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    (SITE / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>',
        encoding="utf-8")
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot"]
    robots = "User-agent: *\nAllow: /\n\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"Sitemap: {BASE}/sitemap.xml\n"
    (SITE / "robots.txt").write_text(robots, encoding="utf-8")


def build_llms(posts):
    lines = [
        "# Merchant Financial Advisory LLC (MFA)",
        "",
        "> Accounting and tax solutions provider based in Princeton, New Jersey, serving individuals and small and mid-sized businesses in New Jersey, New York and nationwide. MFA Insights covers IRS/federal, New Jersey and New York tax rules and deadlines, accounting, bookkeeping and QuickBooks.",
        "",
        "MFA provides tax preparation and filing, tax planning, bookkeeping, accrual-basis accounting and financial reporting, QuickBooks setup, cleanup and support, fractional CFO and business advisory, and audit support.",
        "Contact: info@mfa-advisory.com, (347) 205-4468. Languages: English, Hindi, Urdu. Book a 30-minute consultation: https://mfa-advisory.com/#book",
        "",
        "## Key pages",
        f"- [Home and services]({BASE}/): services, approach, client reviews, booking and contact",
        f"- [Union City, NJ bookkeeping, accounting and tax preparation]({BASE}/union-city-nj/): local services page for Union City and Hudson County, NJ",
        f"- [Princeton, NJ bookkeeping, accounting and tax preparation]({BASE}/princeton-nj/): local services page for Princeton and Mercer County, NJ",
        f"- [MFA Insights blog]({BASE}/blog/): tax deadlines, IRS updates, accounting best practices and QuickBooks tips",
        f"- [MFA Insights newsletter]({BASE}/newsletter/): email with new articles, key tax dates and a subscribable key-dates calendar",
        f"- [Zain Merchant, ACCA]({AUTHOR['url']}): founder and principal of MFA, author of MFA Insights",
        f"- [Disclaimer]({BASE}/disclaimer.html): site content is general information, not tax, accounting, legal or financial advice",
        "",
        "## Latest articles",
    ] + [f"- [{p['title']}]({BASE}/blog/{p['slug']}/): {p['description']}" for p in posts[:30]]
    (SITE / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    posts = load_posts()
    for p in posts:
        seo_lint(p)
        build_post(p)
    build_index(posts)
    build_feed(posts)
    build_latest(posts)
    pages = build_pages()
    build_sitemap(posts, pages)
    build_author(posts)
    build_llms(posts)
    build_newsletter_pages(posts)
    print(f"Built {len(posts)} post(s): " + ", ".join(p["slug"] for p in posts))
