#!/usr/bin/env python3
"""MFA Picks: /picks/ (Hub, 2026-11-02).

Zain, 2026-11-02 23:28 ET: build a page of Amazon referral links that is linked ONLY from our videos and bios
(TikTok, YouTube Shorts, Instagram, Pinterest), not from the home page or the menu. So this page is noindex and is
not listed in tools/site_pages.json (the sitemap source). Amazon Associates tag: mfaadvisory-20 (Zain's account).

Links are Amazon search links with the tag (no guessed product IDs). Swap any line for a specific product link
once Zain names the exact item he uses. Rules: required Amazon disclosure at the top; rel="sponsored"; no prices;
never "free"; no CPA claim; no street address.
Run: python3 tools/build_picks.py
"""
from pathlib import Path
from urllib.parse import quote_plus
from html import escape as esc

import build_blog as B

ROOT = Path(__file__).resolve().parent.parent
URL = "https://mfa-advisory.com/picks/"
TAG = "mfaadvisory-20"
CHECKED = "November 2, 2026"


def amz(q):
    return f"https://www.amazon.com/s?k={quote_plus(q)}&tag={TAG}"


# (title, author, why it's worth reading, search query)
BOOKS = [
    ("Profit First", "Mike Michalowicz", "A simple bank-account system that makes a small business keep a profit and set money aside for taxes.", "Profit First Mike Michalowicz"),
    ("The Psychology of Money", "Morgan Housel", "Short stories about why people make the money choices they do. One of the most-shared money books of recent years.", "The Psychology of Money Morgan Housel"),
    ("Rich Dad Poor Dad", "Robert T. Kiyosaki", "The classic on assets vs. liabilities and thinking like an owner instead of an employee.", "Rich Dad Poor Dad Robert Kiyosaki"),
    ("I Will Teach You to Be Rich", "Ramit Sethi", "A practical system for automating saving, spending and paying off debt.", "I Will Teach You to Be Rich Ramit Sethi"),
    ("The Total Money Makeover", "Dave Ramsey", "A step-by-step plan for getting out of debt and building an emergency fund.", "The Total Money Makeover Dave Ramsey"),
    ("The Millionaire Next Door", "Thomas J. Stanley & William D. Danko", "Research on how everyday business owners actually build wealth: spend less than you earn, for a long time.", "The Millionaire Next Door Stanley Danko"),
    ("Accounting Made Simple", "Mike Piper", "Debits, credits and the three financial statements explained in about 100 pages.", "Accounting Made Simple Mike Piper"),
    ("Financial Intelligence for Entrepreneurs", "Karen Berman & Joe Knight", "How to read your own P&L, balance sheet and cash flow, written for owners, not accountants.", "Financial Intelligence for Entrepreneurs Berman Knight"),
]

# (tool, what to look for, tax note, search query)
TOOLS = [
    ("Portable receipt scanner", "Scans to PDF and syncs to your phone or cloud folder, so every receipt has a backup.", "Office equipment used for your business is usually deductible.", "portable receipt scanner"),
    ("Thermal shipping label printer", "Prints 4x6 labels for Etsy, eBay, Amazon and USPS without ink.", "A business shipping expense for online sellers.", "thermal shipping label printer 4x6"),
    ("Digital postage scale", "Weighs packages to the ounce so you don't overpay postage.", "Business supplies for sellers.", "digital postage scale shipping"),
    ("Label maker", "Labels your file boxes and binders by year and category.", "Office supplies.", "label maker"),
    ("Accordion receipt organizer", "13 or more pockets, one per month plus one for the year-end documents.", "Office supplies.", "accordion file organizer receipts"),
    ("Car phone mount", "Keeps your mileage app and maps visible for rideshare and delivery driving.", "How it's treated depends on how you deduct your car; ask your preparer.", "car phone mount dashboard"),
    ("Second monitor", "A 24- or 27-inch screen makes bookkeeping and spreadsheets much faster.", "Equipment for a home office used for business.", "24 inch computer monitor"),
    ("Ergonomic desk chair", "Adjustable seat height and lumbar support for long work days.", "Office furniture used for your business.", "ergonomic office chair lumbar support"),
]

CSS = """<style>
.pk-hero{background:var(--navy,#10233F);color:#fff;padding:72px 0 56px}
.pk-hero .eyebrow{color:var(--gold-b,#D8B769)}
.pk-hero h1{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:clamp(38px,6vw,60px);line-height:1.05;margin:10px 0 14px}
.pk-hero h1 em{font-style:italic;color:var(--gold-b,#D8B769)}
.pk-hero p{max-width:640px;color:rgba(255,255,255,.82);font-size:17px;line-height:1.6}
.pk-disc{margin-top:22px;display:inline-block;border:1px solid rgba(216,183,105,.45);border-radius:12px;padding:10px 14px;font-size:14px;color:#fff}
.pk-sec{padding:56px 0 8px}
.pk-sec h2{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:clamp(30px,4vw,40px);color:var(--navy,#10233F);margin:6px 0 6px}
.pk-sec .sub{color:rgba(21,21,21,.6);margin-bottom:22px}
.pk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.pk-card{background:#fff;border:1px solid rgba(21,21,21,.09);border-top:3px solid var(--gold,#B08D3F);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:8px}
.pk-card h3{font-size:18px;color:var(--navy,#10233F);margin:0}
.pk-card .by{font-size:13px;color:rgba(21,21,21,.55)}
.pk-card p{font-size:15px;line-height:1.5;margin:0}
.pk-card .tax{font-size:13px;color:rgba(21,21,21,.6)}
.pk-card a.btn{margin-top:auto;align-self:flex-start}
.pk-fine{padding:40px 0 64px;color:rgba(21,21,21,.6);font-size:13px;line-height:1.6}
@media (max-width:600px){.pk-hero{padding:52px 0 40px}}
</style>"""


def card(title, line2, body, url, cta, extra=""):
    return (f'<article class="pk-card"><h3>{esc(title)}</h3>{f"<span class=by>{esc(line2)}</span>" if line2 else ""}'
            f'<p>{esc(body)}</p>{f"<span class=tax>{esc(extra)}</span>" if extra else ""}'
            f'<a class="btn btn-gold" href="{esc(url)}" target="_blank" rel="sponsored noopener nofollow">{esc(cta)}</a></article>')


def build():
    title = "MFA Picks: Money Books and Tools We Mention | MFA"
    desc = "The finance books and small-business tools from our videos, with Amazon links."
    head = B.head(title, desc, URL, "https://mfa-advisory.com/apple-touch-icon.png",
                  CSS + '<meta name="robots" content="noindex,follow"/>')
    books = "".join(card(t, a, w, amz(q), "View on Amazon") for t, a, w, q in BOOKS)
    tools = "".join(card(t, "", w, amz(q), "See options on Amazon", n) for t, w, n, q in TOOLS)
    body = f"""<header class="pk-hero"><div class="wrap">
<span class="eyebrow">From our videos</span>
<h1>MFA <em>Picks</em></h1>
<p>The money books and small-business tools we talk about on TikTok, YouTube and Instagram, in one place.</p>
<p class="pk-disc"><b>Disclosure:</b> As an Amazon Associate, MFA earns from qualifying purchases. These are affiliate links; your price doesn't change.</p>
</div></header>
<main>
<section class="pk-sec" aria-labelledby="bk-h"><div class="wrap"><span class="eyebrow eb-dark">Read</span><h2 id="bk-h">Money books worth your time</h2>
<p class="sub">The finance books people keep sharing, plus two that explain your own numbers.</p><div class="pk-grid">{books}</div></div></section>
<section class="pk-sec" aria-labelledby="tl-h"><div class="wrap"><span class="eyebrow eb-dark">Set up</span><h2 id="tl-h">Tools for a tidier, tax-ready business</h2>
<p class="sub">What to look for in each, and how it's usually treated at tax time.</p><div class="pk-grid">{tools}</div></div></section>
<section class="pk-fine"><div class="wrap"><p>General information, not tax advice: whether an item is deductible depends on how you use it and how you deduct your
car and home office. Amazon prices and availability change; we don't control them. Links checked {CHECKED}.</p></div></section>
</main>"""
    html = f"""{head}
<body>{B.nav("")}
{body}
{B.FOOT}</body></html>"""
    out = ROOT / "site" / "picks" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build())
