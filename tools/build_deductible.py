#!/usr/bin/env python3
"""Builds the Is It Deductible? tool (/tools/is-it-deductible/). Site session owns this file.

Called from tools/build_resources.py (build()). Every rule, figure and source lives in data/deductions.json
(checked on irs.gov or in the Code/Regs; see meta.checked). The page renders the list server-side so it can be read
without JavaScript; site/resources/deductible.js adds search, category filters and the popup. Customer-facing dates
show the date only. Figures shared with other tools (mileage, home office) are cross-checked against
data/tax-figures-2026.json at build time.
"""
import hashlib
import json
from datetime import date
from pathlib import Path

import build_blog as B
import seo
import ui_kit
from build_resources import BASE, EXTRA_CSS, NOTE, OG, SITE, clean_ld, cta, esc, tool_ld, write

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "deductions.json").read_text(encoding="utf-8"))
FIG = json.loads((ROOT / "data" / "tax-figures-2026.json").read_text(encoding="utf-8"))
SLUG = "is-it-deductible"
URL = f"{BASE}/tools/{SLUG}/"
V = lambda f: hashlib.md5((SITE / "resources" / f).read_bytes()).hexdigest()[:10]

VERDICTS = {
    "deductible": {"label": "Deductible", "big": "Deductible", "line": "Generally deductible as a business expense, if it's ordinary and necessary for your business."},
    "partly": {"label": "Partly", "big": "Partly deductible", "line": "Only part of the cost counts: a percentage, the business share, or up to a limit."},
    "depends": {"label": "Depends", "big": "It depends", "line": "Whether and how you deduct it depends on how and why you use it. Read the rule below."},
    "not": {"label": "Not deductible", "big": "Not deductible", "line": "Generally not deductible as a business expense."},
}
SHORT_DISCLAIMER = ("Educational information only, not tax, legal or accounting advice. Rules change and depend on your facts: "
                    "check the IRS source and talk to a qualified tax professional before you file.")
TOOL_NAMES = {
    "/tools/home-office-deduction-calculator/": "Home office deduction calculator",
    "/tools/mileage-deduction-calculator/": "Mileage deduction calculator",
    "/tools/do-i-need-to-send-a-1099/": "Do I need to send a 1099?",
    "/tools/1099-contractor-tracker/": "1099 contractor tracker",
    "/tools/w-9-request-email-template/": "W-9 request email templates",
    "/tools/1099-tax-calculator/": "1099 tax calculator",
    "/tools/quarterly-estimated-tax-calculator/": "Quarterly estimated tax calculator",
    "/tools/paycheck-tax-calculator/": "Paycheck tax calculator",
    "/tools/s-corp-tax-savings-calculator/": "S corp tax savings calculator",
    "/llc-formation/": "LLC formation: NJ & NY fees",
}
POPULAR = [("Meals", "meals"), ("Home office", "home office"), ("Car", "car"), ("Phone", "phone"), ("Laptop", "laptop"), ("Travel", "travel")]

ICONS = {  # 24px line icons (stroke = currentColor)
    "home": '<path d="M3.5 11 12 4l8.5 7"/><path d="M5.5 9.5V20h13V9.5M10 20v-5h4v5"/>',
    "car": '<path d="M5 16.5h14M6.5 16.5V19M17.5 16.5V19M4 16.5l1.6-5.2A2 2 0 0 1 7.5 10h9a2 2 0 0 1 1.9 1.3l1.6 5.2"/><circle cx="8" cy="14" r=".6"/><circle cx="16" cy="14" r=".6"/>',
    "meal": '<path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M16 3c-1.7 0-3 2-3 5s1.3 4 3 4v9"/>',
    "laptop": '<rect x="4.5" y="5" width="15" height="10" rx="1.5"/><path d="M2.5 19h19"/>',
    "tool": '<path d="M14.5 6.5a4 4 0 0 0-5.3 5.3L4 17l3 3 5.2-5.2a4 4 0 0 0 5.3-5.3l-2.4 2.4-2.6-.4-.4-2.6z"/>',
    "people": '<circle cx="9" cy="8.5" r="3"/><path d="M3.5 19a5.5 5.5 0 0 1 11 0"/><circle cx="17" cy="9.5" r="2.4"/><path d="M15.5 14.4A4.5 4.5 0 0 1 21 19"/>',
    "shield": '<path d="M12 3 4.5 6v5.5c0 4.4 3.1 8.1 7.5 9.5 4.4-1.4 7.5-5.1 7.5-9.5V6z"/><path d="m9 12 2 2 4-4"/>',
    "piggy": '<path d="M5 11a6 5 0 0 1 11-2.8L19 7v4l1.5 1v3H18a6 5 0 0 1-2.5 2.2V20h-3v-2.1a7 6 0 0 1-2 0V20h-3v-3A5 5 0 0 1 5 11z"/><circle cx="15" cy="11" r=".6"/>',
    "scale": '<path d="M12 4v16M5 8h14M5 8l-2.5 6a3 3 0 0 0 5 0zM19 8l-2.5 6a3 3 0 0 0 5 0zM8 20h8"/>',
    "megaphone": '<path d="M4 10v4h3l7 4V6L7 10zM17 9.5a3.5 3.5 0 0 1 0 5M7 14l1.2 5h2.3l-.9-4.2"/>',
    "cap": '<path d="m2.5 9 9.5-4.5L21.5 9 12 13.5z"/><path d="M6.5 11v4.5c1.6 1.4 3.5 2 5.5 2s3.9-.6 5.5-2V11M21.5 9v5"/>',
    "bank": '<path d="M3 9.5 12 4l9 5.5M4.5 10v8M9 10v8M15 10v8M19.5 10v8M3 20h18"/>',
    "rocket": '<path d="M12 15c-1.5-1.5-2.5-3.5-2-6.5C10.5 6 12.5 4 16 3.5c.5 3.5-1.5 5.5-4 6.5M9.5 14.5 7 17M8 12.5H5l2.5-3h3M11.5 16v3l3-2.5v-3"/><circle cx="14.5" cy="8" r="1"/>',
    "box": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/>',
    "receipt": '<path d="M6 3h12v18l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4L6 21z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
    "ban": '<circle cx="12" cy="12" r="8.5"/><path d="m6 6 12 12"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    "warn": '<path d="M12 3.5 2.5 20h19z"/><path d="M12 10v4.5M12 17.2v.3"/>',
    "v-deductible": '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.8 2.8L16.5 9.5"/>',
    "v-partly": '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none"/>',
    "v-depends": '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 1 1 3.4 2.4c-.6.3-1 .8-1 1.5v.8M12 16.6v.3"/>',
    "v-not": '<circle cx="12" cy="12" r="9"/><path d="m8.8 8.8 6.4 6.4M15.2 8.8l-6.4 6.4"/>',
}
svg = lambda k, w=1.7: (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" '
                        f'stroke-linejoin="round" aria-hidden="true">{ICONS[k]}</svg>')


def nice(d):
    """Oct. 21, 2026 (AP-style month abbreviations)."""
    d = date.fromisoformat(d[:10])
    m = {3: "March", 4: "April", 5: "May", 6: "June", 7: "July"}.get(d.month) or d.strftime("%b") + "."
    return f"{'Sept.' if d.month == 9 else m} {d.day}, {d.year}"


def check_data():
    """Fail the build if the data drifts from the shared figures or breaks the project rules."""
    E = DATA["entries"]
    by = {e["slug"]: e for e in E}
    m = FIG["mileage"]
    for k in ("business_rate_2026_jan_jun", "business_rate_2026_jul_dec"):
        assert f'{m[k]["value"] * 100:g} cents' in by["mileage"]["limits"], f"mileage entry doesn't match tax-figures-2026.json {k}"
    h = FIG["home_office_simplified"]
    lim = by["home-office"]["limits"]
    assert f'${h["rate_per_sq_ft"]["value"]} per square foot' in lim and f'{h["max_sq_ft"]["value"]} square feet' in lim and f'${h["max_deduction"]["value"]:,}' in lim, \
        "home office entry doesn't match tax-figures-2026.json"
    txt = json.dumps(DATA).lower()
    assert " free " not in txt.replace('"', " ") and "cpa firm" not in txt, "banned wording in deductions.json"
    for e in E:
        for u in [e["source_url"]] + [a["url"] for a in e.get("also", [])]:
            assert u.startswith(("https://www.irs.gov/", "https://www.law.cornell.edu/")), f'{e["slug"]}: source must be irs.gov or the Code/Regs ({u})'
        for u in e.get("tools", []):
            assert u in TOOL_NAMES and (SITE / u.strip("/") / "index.html").exists(), f'{e["slug"]}: unknown tool link {u}'
    assert 50 <= len(E) <= 60, f"{len(E)} entries (expected 50-60)"


def item(e, cats):
    first = e["rule"].split(". ")[0].rstrip(".") + "."
    pct = f' · {e["percent"]}%' if e["percent"] is not None and e["verdict"] != "not" else ""
    return (f'<a class="dd-item v-{e["verdict"]}" href="#{e["slug"]}" data-slug="{e["slug"]}" aria-haspopup="dialog">'
            f'<span class="top"><span class="cat">{esc(cats[e["category"]]["name"])}</span>'
            f'<span class="dd-badge">{esc(VERDICTS[e["verdict"]]["label"])}{pct}</span></span>'
            f'<h3>{esc(e["name"])}</h3><p>{esc(first)}</p><span class="go">Rules, limits &amp; records <i>→</i></span></a>')


FAQ = [
    ("What makes a business expense deductible?",
     "The general test is that the cost is ordinary and necessary for carrying on your trade or business. Personal, living and family costs aren't "
     "deductible, and when something is used for both business and personal purposes, only the business share counts. Some expenses also have their "
     "own limits, such as the 50% limit on business meals and the $25 limit on gifts."),
    ("Can I deduct 100% of business meals in 2026?",
     "Usually not. Business meals with clients and meals while traveling are generally 50% deductible (80% for workers under Department of "
     "Transportation hours-of-service limits). Holiday parties and similar events mainly for employees are fully deductible. Starting in 2026, food "
     "and drinks an employer provides to employees at work, such as office snacks or on-site meals for the employer's convenience, are no longer deductible."),
    ("What records do I need to keep?",
     "Keep receipts, canceled checks and other documents that support each deduction. For travel, meals, gifts and car use, also record the amount, "
     "date, place, business purpose and business relationship, and keep receipts for lodging and anything $75 or more. Keep records at least until the "
     "period to assess tax runs out, generally 3 years after you file, and employment tax records for at least 4 years."),
    ("Should I deduct equipment all at once or depreciate it?",
     "You often have a choice. Items of $2,500 or less per invoice or item can be deducted under the de minimis safe harbor election. Larger purchases "
     "can be expensed under Section 179 (up to $2,560,000 for tax years beginning in 2026) or with 100% bonus depreciation for property acquired after "
     "Jan. 19, 2025, or depreciated over several years. The best choice depends on your income this year and in later years, so it's worth running the numbers."),
    ("Does this tool apply to my W-2 job?",
     "It's written for self-employed people and small businesses. W-2 employees generally can't deduct unreimbursed job costs such as car expenses "
     "or a home office."),
    ("How current is this information?",
     "Every entry was checked against IRS publications, instructions and the Internal Revenue Code on Oct. 21, 2026, and uses 2026 figures where the "
     "IRS has published them. Where a 2026 edition isn't out yet, the latest edition is cited with its year. IRS Publication 535 (Business Expenses) "
     "has been discontinued; its topics now live in Publication 334 and the Schedule C instructions."),
]


def sources_list():
    seen = {}
    for e in DATA["entries"]:
        for t, u in [(e["source_title"], e["source_url"])] + [(a["title"], a["url"]) for a in e.get("also", [])]:
            seen.setdefault(u, t)
    groups = [("IRS publications and instructions", lambda u: "/publications/" in u or "/instructions/" in u or "/pub/irs-pdf/" in u),
              ("Other IRS guidance", lambda u: u.startswith("https://www.irs.gov/")),
              ("Internal Revenue Code and Treasury Regulations", lambda u: True)]
    out, used = [], set()
    for name, test in groups:
        rows = sorted(((t, u) for u, t in seen.items() if u not in used and test(u)), key=lambda r: r[0])
        used |= {u for _, u in rows}
        if rows:
            out.append(f'<h3>{esc(name)}</h3><ul>' + "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in rows) + "</ul>")
    return "".join(out), len(seen)


def build():
    check_data()
    meta, E = DATA["meta"], DATA["entries"]
    cats = {c["id"]: c for c in meta["categories"]}
    checked = nice(meta["checked"])
    reviewed = nice(meta["last_reviewed"])
    title = "Is It Deductible? 2026 Business Expense Finder | MFA"
    desc = (f"Search {len(E)} common small business expenses to see if they're deductible in 2026, the limits and the records to keep, "
            "with the IRS source for each.")

    chips = "".join(f'<button class="chip dd-chip" type="button" data-q="{esc(q)}">{esc(t)}</button>' for t, q in POPULAR)
    hero = f"""<header class="bhero dd-hero"><div class="wrap">
  <div class="crumbs"><a href="/">Home</a> / <a href="/resources/">Resources</a> / Is it deductible?</div>
  <span class="eyebrow">Deduction finder · {meta["tax_year"]} tax year</span>
  <h1>Is it <em>deductible?</em></h1>
  <p>Search a business expense to see whether you can write it off, the limits that apply and the records to keep. Every answer links to its IRS source.</p>
  <div class="dd-search" role="search">{svg("search", 2)}<input type="search" id="dd-q" placeholder="Search an expense, e.g. meals, laptop, phone" aria-label="Search an expense" aria-controls="dd-list" autocomplete="off" spellcheck="false"/><button type="button" class="dd-x-q" id="dd-clear-q" aria-label="Clear search" hidden>×</button></div>
  <div class="chips dd-pop" role="group" aria-label="Popular searches"><span>Popular</span>{chips}</div>
  <p class="dd-rev">Reviewed by <a href="/authors/zain-merchant/">Zain Merchant, ACCA</a> · Last reviewed {reviewed}<br/>Facts checked {checked} · {len(E)} expenses · Sources: IRS and the Internal Revenue Code</p>
</div></header>"""

    warn = (f'<aside class="dd-warn" aria-label="Important: educational information only">{svg("warn", 1.9)}<div>'
            f'<strong>Educational information only, not tax, legal or accounting advice.</strong>'
            f'<p>Tax rules change and depend on your facts. Do your own research using the IRS sources linked, and talk to a qualified tax professional before you file.</p></div></aside>')
    cat_btns = "".join(
        f'<button type="button" class="dd-cat{" not" if c["id"] == "not" else ""}" data-cat="{c["id"]}" aria-pressed="false"><i>{svg(c["icon"])}</i>'
        f'<span><b>{esc(c["name"])}</b><small>{c["count"]} {"expense" if c["count"] == 1 else "expenses"}</small></span></button>'
        for c in meta["categories"] if c["count"])
    legend = "".join(f'<span><span class="dd-badge v-{k}">{esc(v["label"])}</span></span>' for k, v in VERDICTS.items())
    items = "".join(item(e, cats) for e in E)
    main = f"""<main class="dd-main" id="dd-main"><div class="wrap">
{warn}
<section aria-labelledby="dd-cats-h"><div class="dd-hd"><h2 id="dd-cats-h">Browse by category</h2><p>Tap a category to filter the list. Tap it again to show everything.</p></div>
<div class="dd-cats">{cat_btns}</div></section>
<section id="dd-results" aria-labelledby="dd-res-h" style="scroll-margin-top:96px"><div class="dd-hd"><h2 id="dd-res-h">All expenses</h2><p><span id="dd-count" aria-live="polite">{len(E)} expenses</span> <button type="button" class="dd-link" id="dd-all" hidden>Show all</button></p></div>
<div class="dd-legend" aria-label="What the labels mean">{legend}</div>
<div class="dd-list" id="dd-list">{items}</div>
<div class="dd-empty" id="dd-empty" hidden>Nothing matches “<span id="dd-empty-q"></span>” yet. Try a different word, browse the categories, or <a href="/#book" data-conv="book">ask us directly</a>.</div>
<noscript><p class="dd-empty">Search and the detail popups need JavaScript. The full list of expenses is shown above.</p></noscript>
</section></div></main>"""

    kinds = "".join(f'<li><span class="dd-badge v-{k}">{esc(v["label"])}</span><span>{esc(v["line"])}</span></li>' for k, v in VERDICTS.items())
    src_html, n_src = sources_list()
    faq = ui_kit.faq_accordion([(esc(q), esc(a)) for q, a in FAQ])
    info = f"""<div class="tinfo"><article class="article">
<h2>How to read the answers</h2>
<p>Each expense gets one of four labels. Open any card for the rule in plain English, the limits, the records to keep and the official source it comes from.</p>
<ul class="dd-kinds">{kinds}</ul>
<p>Answers are written for sole proprietors and single-member LLCs filing Schedule C, and most apply the same way to partnerships and corporations. Figures are for the {meta["tax_year"]} tax year where the IRS has published them. Pair this with the <a href="/tools/home-office-deduction-calculator/">home office calculator</a>, the <a href="/tools/mileage-deduction-calculator/">mileage calculator</a> and the <a href="/tools/1099-tax-calculator/">1099 tax calculator</a> to see what your deductions are worth.</p>
<section class="faqs" id="faqs"><h2>FAQs</h2>{faq}</section>
<section class="sources dd-src-g"><h2>Official sources</h2><p>All {n_src} sources used on this page. IRS Publication 535 (Business Expenses) has been discontinued, so it isn't cited.</p>{src_html}
<p class="disclaimer">Reviewed by <a href="/authors/zain-merchant/">Zain Merchant, ACCA</a>, {reviewed}. Facts checked against the sources above as of {checked}. {esc(NOTE)}</p></section>
</article></div>"""

    modal = """<div class="dd-modal" id="dd-modal" hidden aria-hidden="true"><div class="dd-back" id="dd-back"></div>
<div class="dd-sheet" id="dd-sheet" role="dialog" aria-modal="true" aria-labelledby="dd-mtitle" tabindex="-1">
<button type="button" class="dd-close" id="dd-close" aria-label="Close">×</button><div id="dd-mbody"></div></div></div>"""

    tools_used = sorted({u for e in E for u in e.get("tools", [])})
    payload = {
        "entries": [{k: e[k] for k in ("slug", "name", "category", "aliases", "verdict", "percent", "rule", "limits", "records", "applies_to",
                                       "source_url", "source_title", "also", "tools")} for e in E],
        "categories": [{"id": c["id"], "name": c["name"]} for c in meta["categories"]],
        "verdicts": VERDICTS, "tools": {u: TOOL_NAMES[u] for u in tools_used}, "checked_label": checked,
        "short_disclaimer": SHORT_DISCLAIMER, "icons": {k: svg("v-" + k, 1.8) for k in VERDICTS},
    }
    data_tag = '<script type="application/json" id="dd-data">' + json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/") + "</script>"

    ld = clean_ld(tool_ld("Is It Deductible? business expense finder", URL, desc))
    ld["@graph"].append({"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]})
    for g in ld["@graph"]:
        if g.get("@id") == URL + "#webpage":
            g["dateModified"] = meta["last_reviewed"]
            g["reviewedBy"] = {"@id": seo.PERSON_ID}
            g["lastReviewed"] = meta["last_reviewed"]
    extra = (EXTRA_CSS + f'<link rel="stylesheet" href="/resources/deductible.css?v={V("deductible.css")}"/>' + seo.script(ld))
    body = (hero + main + info + modal + data_tag +
            f'<script src="/resources/deductible.js?v={V("deductible.js")}" defer></script>' +
            cta("Not sure what you can write off?", "We review your expenses, set up your books so deductions are tracked all year and prepare your return. Book a 30-minute consultation."))
    html = f'{B.head(title, desc, URL, OG, extra)}\n<body class="dd-page">{B.nav("res")}\n{body}\n{B.FOOT}</body></html>'
    return write(f"tools/{SLUG}", html)


if __name__ == "__main__":
    print(build())
