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
POSTS_DIR = ROOT / "content" / "posts"
PAGES_DIR = ROOT / "content" / "pages"
BASE = "https://mfa-advisory.com"
BOOK_URL = BASE + "/#book"
EMAIL = "info@mfa-advisory.com"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"/>'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400'
         '&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>')
MAIL_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2"/>'
             '<path d="m22 7-10 6L2 7"/></svg>')
TOPICS = ["Tax Filing & Deadlines", "Tax Planning", "Accrual Accounting", "QuickBooks Tips & Updates",
          "Bookkeeping Best Practices", "Small & Mid-Sized Business Finance"]
BLOG_DESC = ("Practical tax, accounting, and QuickBooks guidance for individuals and small and mid-sized businesses: "
             "filing deadlines and IRS updates, tax planning, accrual accounting, bookkeeping best practices, and QuickBooks tips.")
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
    posts.sort(key=lambda p: p["dt"], reverse=True)
    return posts


def nav(active):
    def a(href, label, key):
        return f'<a href="{href}"{" class=on" if key == active else ""}>{label}</a>'
    return f'''<header class="bnav"><div class="wrap bnav-in">
  <a href="/" class="brand" aria-label="Merchant Financial Advisory — home"><img src="/apple-touch-icon.png" alt="" width="44" height="44"/><span class="brand-txt"><b>Merchant</b><i>Financial Advisory</i></span></a>
  <nav class="bnav-links" aria-label="Main navigation">{a("/#services","Services","s")}{a("/blog/","Insights","blog")}{a("/#book","Book","b")}<a href="/#contact" class="cta">{MAIL_ICON}Contact Us</a></nav>
</div></header>'''


FOOT = f'''<footer class="bfoot"><div class="wrap">
  <span>© {datetime.now().year} Merchant Financial Advisory LLC · Union City, NJ · Serving clients nationwide</span>
  <nav><a href="/">Home</a><a href="/blog/">Insights</a><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a><a href="/disclaimer.html">Disclaimer</a><a href="/blog/feed.xml">RSS</a><a href="mailto:{EMAIL}">{EMAIL}</a></nav>
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
{FONTS}<link rel="stylesheet" href="/blog/blog.css"/>
{extra}</head>'''


def cta(p):
    topic = p.get("ctaTopic", "your situation")
    return f'''<section class="cta-block" aria-label="Book a consultation"><div class="cta-card">
  <span class="eyebrow">Talk to MFA</span>
  <h2>{esc(p.get("ctaHeadline", "Want a second set of eyes before you act?"))}</h2>
  <p>Book a free 30-minute consultation to talk through {esc(topic)}, or email us at <a href="mailto:{EMAIL}" style="color:#D8B769;border-bottom:1px solid rgba(216,183,105,.5)">{EMAIL}</a>. We provide tax and accounting solutions for individuals and small and mid-sized businesses in New Jersey and nationwide.</p>
  <div class="cta-btns"><a class="btn btn-gold" href="{BOOK_URL}">Book a consultation</a><a class="btn btn-line" href="mailto:{EMAIL}?subject={esc(p['title'])}">Email info@mfa-advisory.com</a></div>
</div></section>'''


def build_post(p):
    url = f"{BASE}/blog/{p['slug']}/"
    img = url + p["og"]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": p["title"], "description": p["description"],
         "datePublished": p["date"], "dateModified": p.get("updated", p["date"]),
         "image": img, "mainEntityOfPage": url, "keywords": ", ".join(p.get("keywords", [])),
         "author": {"@type": "Organization", "name": "Merchant Financial Advisory LLC", "url": BASE},
         "publisher": {"@type": "Organization", "name": "Merchant Financial Advisory LLC",
                       "logo": {"@type": "ImageObject", "url": BASE + "/apple-touch-icon.png"}}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Insights", "item": BASE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": url}]}]}
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
  <div class="ameta"><span><b>Merchant Financial Advisory</b></span><span>{nice}</span><span>{p["minutes"]} min read</span></div>
</div></header>
<main><article class="article">
{p["body"]}
<section class="sources"><h2>Sources</h2><ul>{sources}</ul>
<p class="disclaimer">Facts checked against the sources above as of {asof}. {DISCLAIMER}</p></section>
</article>
{cta(p)}</main>
{FOOT}</body></html>'''
    out = SITE / "blog" / p["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


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
{cta({"title": "Question from the MFA blog", "ctaHeadline": "Have a question about your taxes, books, or QuickBooks?", "ctaTopic": "your taxes, accounting, or QuickBooks setup"})}
{FOOT}</body></html>'''
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


def build_sitemap(posts, pages=()):
    today = datetime.now(timezone.utc).date().isoformat()
    urls = [(BASE + "/", today), (BASE + "/blog/", posts[0]["date"] if posts else today)]
    urls += [(f'{BASE}/blog/{p["slug"]}/', p.get("updated", p["date"])) for p in posts]
    urls += [(f"{BASE}/{pg['slug']}.html", pg["updated"]) for pg in pages]
    body = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    (SITE / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>',
        encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")


if __name__ == "__main__":
    posts = load_posts()
    for p in posts:
        build_post(p)
    build_index(posts)
    build_feed(posts)
    build_latest(posts)
    pages = build_pages()
    build_sitemap(posts, pages)
    print(f"Built {len(posts)} post(s): " + ", ".join(p["slug"] for p in posts))
