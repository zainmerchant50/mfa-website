#!/usr/bin/env python3
"""'Products that go with this tool' block for every /tools/<slug>/ page (Zain 2026-10-26).

Products, prices and links come from catalog/products.json (live products only, existing public prices; nothing is
priced here). Buy goes to the Etsy listing in a new tab, with UTM tags and a data-shop attribute (same click-tracking
hook as /shop/ and the blog). Products without an Etsy listing fall back to seo.buy_link (Gumroad). Hooked in by
build_resources.write(), so every builder that writes a tools/ page keeps the block when pages are regenerated.
"""
import html as _html
import re

import seo

# tool slug -> product slugs (order = display order)
MAP = {
    "quarterly-estimated-tax-calculator": ["1099-self-employed-tax-calculator-2026", "small-business-year-end-tax-checklist", "1099-income-tracker-freelancers-2026"],
    "1099-tax-calculator": ["1099-self-employed-tax-calculator-2026", "self-employed-tax-deduction-tracker-2026", "1099-income-tracker-freelancers-2026"],
    "s-corp-tax-savings-calculator": ["s-corp-vs-llc-savings-calculator", "new-business-setup-checklist", "small-business-bookkeeping-spreadsheet"],
    "paycheck-tax-calculator": ["salary-paycheck-tax-calculator-2026", "2026-tax-organizer"],
    "home-office-deduction-calculator": ["self-employed-tax-deduction-tracker-2026", "expense-categorization-guide-tracker"],
    "mileage-deduction-calculator": ["irs-mileage-log-2026", "rideshare-delivery-driver-tax-tracker", "self-employed-tax-deduction-tracker-2026"],
    "1099-contractor-tracker": ["1099-contractor-payment-tracker-2026", "1099-kit"],
    "tax-deadlines-2027": ["small-business-year-end-tax-checklist", "tax-season-bundle-2026", "2026-tax-organizer"],
    "break-even-calculator": ["small-business-budget-13-week-cash-flow", "small-business-bookkeeping-spreadsheet"],
    "profit-margin-calculator": ["small-business-bookkeeping-spreadsheet", "small-business-budget-13-week-cash-flow", "expense-categorization-guide-tracker"],
    "do-i-need-to-send-a-1099": ["1099-kit", "1099-contractor-payment-tracker-2026"],
    "is-it-deductible": ["self-employed-tax-deduction-tracker-2026", "expense-categorization-guide-tracker", "small-business-year-end-tax-checklist"],
    "w-9-request-email-template": ["1099-kit", "1099-contractor-payment-tracker-2026"],
}
# /resources/ index: a short shop strip
HUB = ["1099-kit", "1099-self-employed-tax-calculator-2026", "self-employed-tax-deduction-tracker-2026"]

CSS = """<style>
.tp-sec{padding-top:8px}
.tp-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin-top:6px}
.tp-grid .card{display:flex;flex-direction:column;padding:20px 22px;background:#fff;border:1px solid var(--hair);border-radius:16px}
.tp-fmt{font-size:9.5px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--gold)}
.tp-grid h3{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:1.22rem;color:var(--navy);margin:6px 0;line-height:1.2}
.tp-grid p{margin:0 0 14px;font-size:.88rem;line-height:1.55;color:var(--muted);flex:1}
.tp-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.tp-price{font-size:1.1rem;font-weight:700;color:var(--navy)}
.tp-btns{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.tp-grid .btn{padding:10px 18px}
.tp-shop{font-size:.85rem;border-bottom:1px solid var(--gold)}
.tp-all{margin:16px 0 0;font-size:.92rem}.tp-all a{border-bottom:1px solid var(--gold);font-weight:600}
@media (prefers-color-scheme:dark){.tp-grid .card{background:transparent}.tp-price,.tp-grid h3{color:inherit}}
</style>"""


def _live():
    return {p["slug"]: p for p in seo.live_products()}


def _buy(p, campaign):
    if p["via"] == "etsy":
        sep = "&" if "?" in p["url"] else "?"
        href = f'{p["url"]}{sep}utm_source=mfa_site&utm_medium=tool_page&utm_campaign={campaign}'
        return f'<a class="btn btn-gold" href="{_html.escape(href)}" target="_blank" rel="noopener" data-shop="{_html.escape(p["slug"])}">Buy on Etsy</a>'
    return f'<a class="btn btn-gold" href="{_html.escape(p["url"])}" data-shop="{_html.escape(p["slug"])}">Buy now</a>'


def render(slug, slugs=None, heading="Products that go with this tool", eyebrow="From the MFA shop", campaign=None):
    live = _live()
    prods = [live[s] for s in (slugs if slugs is not None else MAP.get(slug, [])) if s in live]
    if not prods:
        return ""
    campaign = campaign or slug
    cards = "".join(
        f'<div class="card"><span class="tp-fmt">{_html.escape(p["format"])}</span><h3>{_html.escape(p["name"])}</h3>'
        f'<p>{_html.escape(p["blurb"])}</p><div class="tp-foot"><span class="tp-price">${_html.escape(str(p["price"]))}</span>'
        f'<span class="tp-btns">{_buy(p, campaign)}<a class="tp-shop" href="/shop/">View in shop</a></span></div></div>' for p in prods)
    return (f'{CSS}<section class="wrap llc-sec tp-sec" id="shop-products" aria-labelledby="tp-h"><div class="sec-hd">'
            f'<span class="eyebrow eb-dark">{_html.escape(eyebrow)}</span><h2 id="tp-h">{_html.escape(heading)}</h2>'
            f'<p>Spreadsheets and checklists built by accountants, for when you want to keep your own records. Instant download.</p></div>'
            f'<div class="tp-grid">{cards}</div><p class="tp-all"><a href="/shop/">Browse the full shop</a></p></section>')


def inject(slug, html):
    """Insert the block into a built tools/<slug> page (idempotent)."""
    if slug not in MAP or 'id="shop-products"' in html:
        return html
    block = render(slug)
    if not block:
        return html
    if slug == "is-it-deductible":
        anchors = ['<section class="dd-all']   # right after the tap-an-expense tiles and results
    else:
        anchors = ['<div class="tinfo"', "</main>"]
    for a in anchors:
        i = html.find(a)
        if i != -1:
            return html[:i] + block + html[i:]
    raise RuntimeError(f"no place to put the product block on {slug}")
