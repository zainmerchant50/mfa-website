#!/usr/bin/env python3
"""MFA Picks: /picks/ (Hub, 2026-11-02; covers + tool illustrations 2026-11-03).

Zain, 2026-11-02 23:28 ET: build a page of Amazon referral links that is linked ONLY from our videos and bios
(TikTok, YouTube Shorts, Instagram, Pinterest), not from the home page or the menu. So this page is noindex and is
not listed in tools/site_pages.json (the sitemap source). Amazon Associates tag: mfaadvisory-20 (Zain's account).
Zain, 2026-11-03 00:09: show the book covers and make the tools section interesting enough that people read on the
page and then click through to buy.

Book covers come from the Open Library Covers API (covers.openlibrary.org, cover ids looked up Nov 3, 2026), not from
Amazon: Amazon's Operating Agreement only allows Amazon product images through its own tools (PA-API, which unlocks
after 3 qualifying sales). Tool cards use original inline SVG illustrations in MFA colors, no Amazon images.
Links are Amazon search links with the tag (no guessed product IDs). Swap a line for a specific product link once
Zain names the exact item he uses. Rules: Amazon disclosure at the top; rel="sponsored"; no prices; never "free";
no CPA claim; no street address.
Run: python3 tools/build_picks.py
"""
from pathlib import Path
from urllib.parse import quote_plus
from html import escape as esc

import build_blog as B

ROOT = Path(__file__).resolve().parent.parent
URL = "https://mfa-advisory.com/picks/"
TAG = "mfaadvisory-20"
CHECKED = "November 3, 2026"


def amz(q):
    return f"https://www.amazon.com/s?k={quote_plus(q)}&tag={TAG}"


# (title, author, open library cover id, the hook, who it's for, search query)
BOOKS = [
    ("Profit First", "Mike Michalowicz", 14624477,
     "Take your profit first, then run the business on what's left. A few bank accounts and a simple percentage split make it happen.",
     "Owners whose sales grow but whose bank balance doesn't", "Profit First Mike Michalowicz"),
    ("The Psychology of Money", "Morgan Housel", 10389354,
     "19 short stories about why smart people make odd money choices, and the habits that quietly build wealth.",
     "Anyone who wants a calmer relationship with money", "The Psychology of Money Morgan Housel"),
    ("Rich Dad Poor Dad", "Robert T. Kiyosaki", 8315603,
     "The classic that made millions of people ask: is this an asset that pays me, or a liability that costs me?",
     "First-time founders and side-hustlers", "Rich Dad Poor Dad Robert Kiyosaki"),
    ("I Will Teach You to Be Rich", "Ramit Sethi", 6305971,
     "A six-week system to automate saving, spending and paying off debt, so good habits run on their own.",
     "Freelancers with uneven income", "I Will Teach You to Be Rich Ramit Sethi"),
    ("The Total Money Makeover", "Dave Ramsey", 6873839,
     "A step-by-step plan for clearing debt and building an emergency fund, one baby step at a time.",
     "Anyone carrying card debt into the new year", "The Total Money Makeover Dave Ramsey"),
    ("The Millionaire Next Door", "Thomas J. Stanley & William D. Danko", 797467,
     "Decades of research on how ordinary business owners build wealth: spend less than you earn, for a long time.",
     "Owners deciding how to pay themselves", "The Millionaire Next Door Stanley Danko"),
    ("Accounting Made Simple", "Mike Piper", 9270154,
     "Debits, credits and the three financial statements explained in about 100 pages. The fastest way to read your own books.",
     "Owners who do their own bookkeeping", "Accounting Made Simple Mike Piper"),
    ("Financial Intelligence for Entrepreneurs", "Karen Berman & Joe Knight", 12179921,
     "How to read a P&L, balance sheet and cash flow statement, and what the numbers say about your business.",
     "Owners who want to understand their monthly reports", "Financial Intelligence for Entrepreneurs Berman Knight"),
]

# Original line illustrations (navy strokes, gold accents) on a 120x90 canvas.
N, G = "#10233F", "#B08D3F"
ART = {
    "scanner": f'<rect x="20" y="34" width="80" height="26" rx="8" fill="none" stroke="{N}" stroke-width="3"/><path d="M38 34V20h44v14" fill="none" stroke="{N}" stroke-width="3"/><path d="M40 60v14h40V60" fill="#fff" stroke="{N}" stroke-width="3"/><path d="M46 66h28M46 71h18" stroke="{G}" stroke-width="3" stroke-linecap="round"/><circle cx="88" cy="47" r="3" fill="{G}"/>',
    "label": f'<rect x="18" y="30" width="62" height="40" rx="9" fill="none" stroke="{N}" stroke-width="3"/><path d="M80 44h22v26H80" fill="none" stroke="{N}" stroke-width="3"/><path d="M84 52h14M84 60h10" stroke="{G}" stroke-width="3" stroke-linecap="round"/><rect x="30" y="18" width="38" height="12" rx="3" fill="#fff" stroke="{N}" stroke-width="3"/>',
    "scale": f'<rect x="22" y="56" width="76" height="16" rx="5" fill="none" stroke="{N}" stroke-width="3"/><rect x="34" y="30" width="52" height="26" rx="4" fill="#fff" stroke="{N}" stroke-width="3"/><path d="M44 40h20M44 47h30" stroke="{G}" stroke-width="3" stroke-linecap="round"/><rect x="46" y="61" width="28" height="6" rx="2" fill="{G}"/>',
    "maker": f'<rect x="34" y="16" width="42" height="60" rx="10" fill="none" stroke="{N}" stroke-width="3"/><rect x="41" y="24" width="28" height="12" rx="3" fill="{G}"/><circle cx="48" cy="48" r="3" fill="{N}"/><circle cx="62" cy="48" r="3" fill="{N}"/><circle cx="48" cy="60" r="3" fill="{N}"/><circle cx="62" cy="60" r="3" fill="{N}"/><path d="M76 30h22" stroke="{G}" stroke-width="4" stroke-linecap="round"/>',
    "folder": f'<path d="M20 34h80v38H20z" fill="none" stroke="{N}" stroke-width="3" stroke-linejoin="round"/><path d="M26 34l6-12h56l6 12" fill="none" stroke="{N}" stroke-width="3" stroke-linejoin="round"/><path d="M36 22v12M50 22v12M64 22v12M78 22v12" stroke="{G}" stroke-width="3"/>',
    "mount": f'<rect x="44" y="12" width="32" height="54" rx="6" fill="#fff" stroke="{N}" stroke-width="3"/><path d="M52 28l8 8 10-14" fill="none" stroke="{G}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M38 40h6M76 40h6M60 66v10M46 78h28" stroke="{N}" stroke-width="3" stroke-linecap="round"/>',
    "monitor": f'<rect x="16" y="16" width="88" height="50" rx="5" fill="none" stroke="{N}" stroke-width="3"/><path d="M28 54l14-14 10 8 16-18 16 12" fill="none" stroke="{G}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M60 66v10M44 78h32" stroke="{N}" stroke-width="3" stroke-linecap="round"/>',
    "chair": f'<path d="M42 14h36a4 4 0 0 1 4 4v30H38V18a4 4 0 0 1 4-4z" fill="none" stroke="{N}" stroke-width="3"/><path d="M32 48h56v8H32z" fill="{G}"/><path d="M60 56v14M42 78l18-8 18 8M30 40v12M90 40v12" stroke="{N}" stroke-width="3" stroke-linecap="round"/>',
}

# (tool, art, why it helps, what to look for [3], tax note, search query)
TOOLS = [
    ("Portable receipt scanner", "scanner", "Paper receipts fade. A scan is a backup the IRS accepts as a record.",
     ["Scans to PDF on your phone or computer", "Saves to a cloud folder automatically", "Handles small, long receipts"],
     "Office equipment used for your business is usually deductible.", "portable receipt scanner"),
    ("Thermal shipping label printer", "label", "Print a 4x6 label in seconds for Etsy, eBay, Amazon or USPS orders.",
     ["Prints 4x6 thermal labels (no ink to buy)", "Works with your selling platform", "USB or Bluetooth"],
     "A business shipping expense for online sellers.", "thermal shipping label printer 4x6"),
    ("Digital postage scale", "scale", "Weigh each package to the ounce so you stop overpaying postage.",
     ["Reads ounces and pounds", "Big enough for your largest box", "Tare button for the box weight"],
     "Business supplies for sellers.", "digital postage scale shipping"),
    ("Label maker", "maker", "Label every file box by year and category, so you can find any receipt in a minute.",
     ["Prints from your phone", "Tape widths for files and boxes", "Rechargeable battery"],
     "Office supplies.", "label maker"),
    ("Accordion receipt organizer", "folder", "One pocket per month plus one for tax forms. Year-end takes an hour, not a weekend.",
     ["13 or more pockets", "Elastic or snap closure", "Labeled tabs"],
     "Office supplies.", "accordion file organizer receipts"),
    ("Car phone mount", "mount", "Keeps your mileage app and maps in view on every rideshare or delivery trip.",
     ["Dash, vent or cup-holder mount", "One-hand release", "Fits your phone with its case"],
     "How it's treated depends on how you deduct your car; ask your preparer.", "car phone mount dashboard"),
    ("Second monitor", "monitor", "Spreadsheet on one screen, bank statement on the other. Bookkeeping goes much faster.",
     ["24 or 27 inches", "HDMI or USB-C to match your laptop", "Adjustable stand"],
     "Equipment for a home office used for business.", "24 inch computer monitor"),
    ("Ergonomic desk chair", "chair", "Long bookkeeping days are easier on your back with the right chair.",
     ["Adjustable seat height and arms", "Lumbar support", "Breathable mesh back"],
     "Office furniture used for your business.", "ergonomic office chair lumbar support"),
]

CSS = """<style>
.pk-hero{background:var(--navy,#10233F);color:#fff;padding:72px 0 56px}
.pk-hero .eyebrow{color:var(--gold-b,#D8B769)}
.pk-hero h1{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:clamp(38px,6vw,60px);line-height:1.05;margin:10px 0 14px}
.pk-hero h1 em{font-style:italic;color:var(--gold-b,#D8B769)}
.pk-hero p{max-width:640px;color:rgba(255,255,255,.82);font-size:17px;line-height:1.6}
.pk-jump{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
.pk-jump a{color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:8px 14px;font-size:14px;text-decoration:none}
.pk-disc{margin-top:22px;display:inline-block;border:1px solid rgba(216,183,105,.45);border-radius:12px;padding:10px 14px;font-size:14px;color:#fff}
.pk-sec{padding:56px 0 8px}
.pk-sec h2{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:clamp(30px,4vw,40px);color:var(--navy,#10233F);margin:6px 0 6px}
.pk-sec .sub{color:rgba(21,21,21,.6);margin-bottom:22px}
.pk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px}
.pk-card{background:#fff;border:1px solid rgba(21,21,21,.09);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;transition:transform .2s,box-shadow .2s}
.pk-card:hover{transform:translateY(-3px);box-shadow:0 14px 30px rgba(16,35,63,.10)}
.pk-media{background:linear-gradient(160deg,#F5F4EF,#ECE7DA);height:210px;display:flex;align-items:center;justify-content:center;border-bottom:3px solid var(--gold,#B08D3F)}
.pk-media img{height:178px;width:auto;max-width:80%;border-radius:4px;box-shadow:0 10px 22px rgba(16,35,63,.25)}
.pk-media svg{width:150px;height:auto}
.pk-body{padding:18px 20px 20px;display:flex;flex-direction:column;gap:8px;flex:1}
.pk-card h3{font-size:18px;color:var(--navy,#10233F);margin:0}
.pk-card .by{font-size:13px;color:rgba(21,21,21,.55)}
.pk-card p{font-size:15px;line-height:1.5;margin:0}
.pk-card .for{font-size:13px;color:var(--navy,#10233F);background:#F5F4EF;border-radius:8px;padding:6px 10px}
.pk-card ul{margin:0;padding-left:18px;font-size:14px;line-height:1.5;color:rgba(21,21,21,.8)}
.pk-card .tax{font-size:12.5px;color:rgba(21,21,21,.58)}
.pk-card a.btn{margin-top:auto;align-self:flex-start}
.pk-fine{padding:40px 0 64px;color:rgba(21,21,21,.6);font-size:13px;line-height:1.6}
@media (max-width:600px){.pk-hero{padding:52px 0 40px}.pk-media{height:190px}.pk-media img{height:160px}}
</style>"""


def btn(url, label):
    return f'<a class="btn btn-gold" href="{esc(url)}" target="_blank" rel="sponsored noopener nofollow">{esc(label)}</a>'


def book_card(t, a, cover, hook, who, q):
    img = (f'<img src="https://covers.openlibrary.org/b/id/{cover}-M.jpg" alt="Cover of {esc(t)} by {esc(a)}" '
           f'loading="lazy" width="120" height="178"/>')
    return (f'<article class="pk-card"><a class="pk-media" href="{esc(amz(q))}" target="_blank" rel="sponsored noopener nofollow" '
            f'aria-label="{esc(t)} on Amazon">{img}</a><div class="pk-body"><h3>{esc(t)}</h3><span class="by">{esc(a)}</span>'
            f'<p>{esc(hook)}</p><span class="for"><b>Best for:</b> {esc(who)}</span>{btn(amz(q), "View on Amazon")}</div></article>')


def tool_card(t, art, why, look, tax, q):
    svg = f'<svg viewBox="0 0 120 90" role="img" aria-label="{esc(t)} illustration">{ART[art]}</svg>'
    lis = "".join(f"<li>{esc(x)}</li>" for x in look)
    return (f'<article class="pk-card"><div class="pk-media">{svg}</div><div class="pk-body"><h3>{esc(t)}</h3>'
            f'<p>{esc(why)}</p><span class="by">What to look for</span><ul>{lis}</ul><span class="tax">{esc(tax)}</span>'
            f'{btn(amz(q), "See options on Amazon")}</div></article>')


def build():
    title = "MFA Picks: Money Books and Tools We Mention | MFA"
    desc = "The finance books and small-business tools from our videos, with Amazon links."
    head = B.head(title, desc, URL, "https://mfa-advisory.com/apple-touch-icon.png",
                  CSS + '<meta name="robots" content="noindex,follow"/>')
    books = "".join(book_card(*b) for b in BOOKS)
    tools = "".join(tool_card(*t) for t in TOOLS)
    body = f"""<header class="pk-hero"><div class="wrap">
<span class="eyebrow">From our videos</span>
<h1>MFA <em>Picks</em></h1>
<p>The money books and small-business tools we talk about on TikTok, YouTube and Instagram, in one place.</p>
<nav class="pk-jump" aria-label="Jump to"><a href="#books">Money books</a><a href="#tools">Tools for your business</a></nav>
<p class="pk-disc"><b>Disclosure:</b> As an Amazon Associate, MFA earns from qualifying purchases. These are affiliate links; your price doesn't change.</p>
</div></header>
<main>
<section class="pk-sec" id="books" aria-labelledby="bk-h"><div class="wrap"><span class="eyebrow eb-dark">Read</span><h2 id="bk-h">Money books worth your time</h2>
<p class="sub">The finance books people keep sharing, plus two that explain your own numbers.</p><div class="pk-grid">{books}</div></div></section>
<section class="pk-sec" id="tools" aria-labelledby="tl-h"><div class="wrap"><span class="eyebrow eb-dark">Set up</span><h2 id="tl-h">Tools for a tidier, tax-ready business</h2>
<p class="sub">Why each one helps, what to look for, and how it's usually treated at tax time.</p><div class="pk-grid">{tools}</div></div></section>
<section class="pk-fine"><div class="wrap"><p>General information, not tax advice: whether an item is deductible depends on how you use it and how you deduct your
car and home office. Amazon prices and availability change; we don't control them. Book covers via Open Library. Links checked {CHECKED}.</p></div></section>
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
