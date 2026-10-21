#!/usr/bin/env python3
"""Builds /shop/ (Site/Hub). Zain approved the page 2026-10-21 01:25 ET ("go ahead with shop").

Lists only products that are LIVE on Gumroad, at their live Gumroad prices.
Buy buttons are plain links to mfaadvisory.gumroad.com/l/<slug>; Gumroad's overlay script
(https://gumroad.com/js/gumroad.js, loaded once) opens checkout on top of this page.
Gumroad is the merchant of record (payment + sales tax). Never "free", never "CPA", no street address.
When a price changes on Gumroad, change it here too and rebuild.
"""
import json

from build_resources import page, write, esc, BASE, cta

GUM = "https://mfaadvisory.gumroad.com/l/"

# (group, slug, name, price, blurb, format, related link or None)
PRODUCTS = [
    ("calc", "1099-self-employed-tax-calculator-2026", "1099 Self-Employed Tax Calculator & Quarterly Planner (2026)", "11.99",
     "From Schedule C to self-employment tax to a 1040-ES schedule: set-aside %, safe-harbor sizing, 2026 and 2027 due dates and a payment log.",
     "Excel / Google Sheets", ("/tools/1099-tax-calculator/", "Try the quick online version")),
    ("calc", "salary-paycheck-tax-calculator-2026", "2026 Salary & Paycheck Tax Calculator (W-2)", "11.99",
     "See where a 2026 paycheck goes: federal, FICA, NJ / NY / NYC tax and net pay per year and per paycheck, with a bracket-by-bracket table.",
     "Excel / Google Sheets", ("/tools/paycheck-tax-calculator/", "Try the quick online version")),
    ("calc", "s-corp-vs-llc-savings-calculator", "S Corp vs LLC Savings Calculator", "11.99",
     "Compare self-employment tax with S corp payroll taxes after the extra costs, see net annual savings and the break-even profit, and read the warnings before you elect.",
     "Excel / Google Sheets", ("/tools/s-corp-tax-savings-calculator/", "Try the quick online version")),
    ("kit", "1099-kit", "The 1099 Kit (2026 payments, filed in 2027)", "15",
     "Decide who needs a 1099, collect W-9s and file on time. Updated for the new $2,000 threshold, with a contractor tracker.",
     "PDF + Excel", ("/tools/do-i-need-to-send-a-1099/", "Do I need to send a 1099?")),
    ("kit", "month-end-close-checklist", "Month-End Close Checklist + Close Workbook", "12.99",
     "A 38-step close checklist plus an 8-tab workbook: 12-month close tracker, month view, reconciliation log, flux review, sign-off sheet and dashboard.",
     "PDF + Excel", None),
    ("kit", "bookkeeping-cleanup-checklist", "Bookkeeping Cleanup Checklist + Catch-Up Tracker", "12",
     "The step-by-step method to catch up months-behind books, plus a tracker that shows what's done.",
     "PDF + Excel", None),
    ("kit", "new-business-setup-checklist", "New Business Setup Checklist", "9",
     "Every step from idea to set up right: entity, EIN, registrations, bank, books and the compliance calendar.",
     "PDF", ("/llc-formation/", "Or have MFA form your LLC")),
    ("kit", "small-business-year-end-tax-checklist", "Small Business Year-End Tax Checklist", "4.99",
     "A check-the-box year-end guide for sole props, partnerships, S corps and C corps: documents, reconciliations, 1099s, payroll, assets, owner pay and 2027 deadlines.",
     "PDF", ("/tools/tax-deadlines-2027/", "2027 tax deadlines")),
    ("ai", "ai-prompts-small-business-bookkeeping-taxes", "AI Prompts for Small Business Bookkeeping & Taxes", "6.99",
     "130 copy-paste AI prompts for bookkeeping, month-end close, reconciliations, Schedule C prep, quarterly estimates and 1099s, each with an expected output and a \"check this\" note.",
     "PDF", None),
    ("ai", "ai-prompts-tax-preparers-bookkeepers", "AI Prompts for Tax Preparers & Bookkeepers", "6.99",
     "104 copy-paste AI prompts for client intake, document requests, notices in plain English, cleanup scoping, review notes, newsletters, social posts and SOPs.",
     "PDF", None),
]

GROUPS = [
    ("calc", "Tax calculators", "Spreadsheets that do the math with 2026 federal and NJ / NY figures."),
    ("kit", "Checklists & kits", "The routines a bookkeeper runs, written so you can run them yourself."),
    ("ai", "AI prompt packs", "Copy-paste prompts with a \"check this\" note, so AI speeds you up without guessing."),
]

CSS = """<style>
.shop-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px;margin-top:18px}
.shp{display:flex;flex-direction:column;padding:0;overflow:hidden}
.shp img{display:block;width:100%;height:auto;aspect-ratio:1/1;object-fit:cover;background:#F5F4EF}
.shp-bd{display:flex;flex-direction:column;gap:8px;padding:18px 18px 20px;flex:1}
.shp h3{font-size:1.15rem;line-height:1.25;margin:0}
.shp p{margin:0;font-size:.92rem;line-height:1.5}
.shp-meta{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-top:auto;padding-top:8px}
.shp-price{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.6rem;font-weight:600;color:#10233F}
.shp-fmt{font-size:.78rem;color:#6b6b6b}
.shp .btn{width:100%;justify-content:center;text-align:center}
.shp-rel{font-size:.85rem}
.shop-note{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:6px}
.shop-note div{font-size:.9rem;line-height:1.5}
@media (prefers-color-scheme:dark){.shp-price{color:inherit}}
</style>"""


def price_txt(p):
    return f"${p}"


def build():
    url = BASE + "/shop/"
    title = "Shop: Tax Calculators, Bookkeeping Checklists & Kits | Merchant Financial Advisory"
    desc = ("Spreadsheets, checklists and kits from MFA: 1099 and paycheck tax calculators, S corp savings, month-end close, "
            "bookkeeping cleanup, new business setup and AI prompt packs. Instant download.")
    secs = []
    for gid, gname, glead in GROUPS:
        cards = []
        for g, slug, name, price, blurb, fmt, rel in PRODUCTS:
            if g != gid:
                continue
            rl = f'<p class="shp-rel"><a href="{rel[0]}">{esc(rel[1])} →</a></p>' if rel else ""
            cards.append(f'''<article class="shp card"><img src="/shop/img/{slug}.webp" alt="" width="400" height="400" loading="lazy"/>
<div class="shp-bd"><h3>{esc(name)}</h3><p>{esc(blurb)}</p>{rl}
<div class="shp-meta"><span class="shp-price">{price_txt(price)}</span><span class="shp-fmt">{esc(fmt)}</span></div>
<a class="btn btn-gold" href="{GUM}{slug}" data-shop="{slug}">Buy now</a></div></article>''')
        secs.append(f'''<section class="wrap llc-sec" id="{gid}" aria-labelledby="{gid}-h"><div class="sec-hd"><span class="eyebrow eb-dark">{esc(gname)}</span>
<h2 id="{gid}-h">{esc(glead)}</h2></div><div class="shop-grid">{"".join(cards)}</div></section>''')
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">MFA shop</span>
<h1>Do-it-yourself tools, <em>built by accountants.</em></h1>
<p>The same calculators, checklists and trackers we use with clients, ready to download. Prefer to hand it off? We'll do the work for a price quoted up front.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#calc">Browse the shop</a><a class="btn btn-line" href="/services/">See our services</a></div></div></header>
<main>
{"".join(secs)}
<section class="wrap llc-sec" aria-label="How buying works"><div class="card" style="padding:22px 24px">
<h2 style="margin-top:0;font-size:1.4rem">How buying works</h2>
<div class="shop-note">
<div><strong>Secure checkout by Gumroad.</strong> Checkout opens on this page. Gumroad processes the payment and handles sales tax.</div>
<div><strong>Instant download.</strong> Files arrive right after checkout and by email. Spreadsheets work in Excel and Google Sheets, with no macros.</div>
<div><strong>All sales final.</strong> Because files are delivered instantly, purchases aren't refundable. Questions before you buy? Email info@mfa-advisory.com.</div>
</div></div></section>
{cta("Rather have it done for you?", "Book a 30-minute call. We'll handle the bookkeeping, filings or tax work, with the price agreed before we start.")}
<section class="wrap llc-sec"><p class="disclaimer">Products are general information, not tax, legal or accounting advice, and don't create a client relationship. MFA is not affiliated with the IRS, Intuit, QuickBooks or Xero.</p></section>
</main>
<script src="https://gumroad.com/js/gumroad.js"></script>'''
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "ItemList", "name": "MFA shop", "url": url, "itemListElement": [
            {"@type": "ListItem", "position": i, "item": {"@type": "Product", "name": name, "description": blurb,
             "image": f"{BASE}/shop/img/{slug}.webp", "brand": {"@type": "Brand", "name": "Merchant Financial Advisory"},
             "offers": {"@type": "Offer", "price": price, "priceCurrency": "USD", "availability": "https://schema.org/InStock",
                        "url": GUM + slug}}}
            for i, (g, slug, name, price, blurb, fmt, rel) in enumerate(PRODUCTS, 1)]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Shop", "item": url}]}]}
    return write("shop", page(title, desc, url, body, ld, active="shop"))


if __name__ == "__main__":
    print(build())
