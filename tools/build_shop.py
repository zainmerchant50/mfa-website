#!/usr/bin/env python3
"""Builds /shop/ (Site/Hub). Zain approved the page 2026-10-21 01:25 ET ("go ahead with shop").

Lists only products that are LIVE on Gumroad, at their live Gumroad prices.
Buy buttons are plain links to mfaadvisory.gumroad.com/l/<slug>; Gumroad's overlay script
(https://gumroad.com/js/gumroad.js, loaded once) opens checkout on top of this page.
Gumroad is the merchant of record (payment + sales tax). Never "free", never "CPA", no street address.
Products, prices and links come from catalog/products.json. Change them there (in the same commit as the Gumroad change) and rebuild.
"""
import json
from pathlib import Path

from build_resources import page, write, esc, BASE, cta

CATALOG = Path(__file__).resolve().parent.parent / "catalog" / "products.json"


def load():
    """Live products from catalog/products.json (the single source of truth), as tuples for the page."""
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    items = []
    for p in cat["products"]:
        if p["status"] != "live" or not p["gumroad"].get("url"):
            continue
        s = p["shop"]
        rel = (s["related"]["url"], s["related"]["label"]) if s.get("related") else None
        items.append((s["group"], p["slug"], p["name"], p["gumroad"]["price"], s["blurb"], s["format"], rel, p["gumroad"]["url"]))
    groups = [(g["id"], g["name"], g["lead"]) for g in cat["groups"]]
    return items, groups


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
.shop-svc{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px 24px;padding:22px 24px}
.shop-svc h3{font-size:1.2rem;margin:0 0 6px}.shop-svc p{margin:0;font-size:.92rem;line-height:1.55;max-width:640px}
.shop-svc .btn{flex-shrink:0}
.shop-note{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:6px}
.shop-note div{font-size:.9rem;line-height:1.5}
@media (prefers-color-scheme:dark){.shp-price{color:inherit}}
</style>"""


def price_txt(p):
    return f"${p}"


def build():
    PRODUCTS, GROUPS = load()
    url = BASE + "/shop/"
    title = "Shop: Tax Calculators, Bookkeeping Checklists & Kits | Merchant Financial Advisory"
    desc = ("Spreadsheets, checklists and kits from MFA: 1099 and paycheck tax calculators, S corp savings, month-end close, "
            "bookkeeping cleanup, new business setup and AI prompt packs. Instant download.")
    secs = []
    for gid, gname, glead in GROUPS:
        cards = []
        for g, slug, name, price, blurb, fmt, rel, gurl in PRODUCTS:
            if g != gid:
                continue
            rl = f'<p class="shp-rel"><a href="{rel[0]}">{esc(rel[1])} →</a></p>' if rel else ""
            cards.append(f'''<article class="shp card"><img src="/shop/img/{slug}.webp" alt="" width="400" height="400" loading="lazy"/>
<div class="shp-bd"><h3>{esc(name)}</h3><p>{esc(blurb)}</p>{rl}
<div class="shp-meta"><span class="shp-price">{price_txt(price)}</span><span class="shp-fmt">{esc(fmt)}</span></div>
<a class="btn btn-gold" href="{gurl}" data-shop="{slug}">Buy now</a></div></article>''')
        secs.append(f'''<section class="wrap llc-sec" id="{gid}" aria-labelledby="{gid}-h"><div class="sec-hd"><span class="eyebrow eb-dark">{esc(gname)}</span>
<h2 id="{gid}-h">{esc(glead)}</h2></div><div class="shop-grid">{"".join(cards)}</div></section>''')
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">MFA shop</span>
<h1>Do-it-yourself tools, <em>built by accountants.</em></h1>
<p>The same calculators, checklists and trackers we use with clients, ready to download. Prefer to hand it off? We'll do the work for a price quoted up front.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#calc">Browse the shop</a><a class="btn btn-line" href="/services/">See our services</a></div></div></header>
<main>
{"".join(secs)}
<section class="wrap llc-sec" id="services" aria-labelledby="svc-h"><div class="sec-hd"><span class="eyebrow eb-dark">Services</span>
<h2 id="svc-h">Need it done for you?</h2></div>
<div class="shop-svc card"><div><h3>Bookkeeping cleanup</h3><p>Months behind on your books? We catch up the categorization, reconcile your bank and card accounts, tidy payables and receivables, and send a written summary. We review a sample of your accounts and give you a fixed quote before any work starts.</p></div>
<a class="btn btn-ink" href="/bookkeeping-cleanup/">Request a quote</a></div></section>
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
                        "url": gurl}}}
            for i, (g, slug, name, price, blurb, fmt, rel, gurl) in enumerate(PRODUCTS, 1)]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Shop", "item": url}]}]}
    return write("shop", page(title, desc, url, body, ld, active="shop"))


if __name__ == "__main__":
    print(build())
