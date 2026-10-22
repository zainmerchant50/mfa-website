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
import re
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
JSON_URL = URL + "deductions.json"   # the dataset, published next to the page (data/deductions.json + license note)
PAGE_MODIFIED = "2026-10-22"         # page/markup last changed (facts: meta.checked; review: meta.last_reviewed)
LICENSE_NOTE = ("© Merchant Financial Advisory LLC. You may quote or reuse this data if you cite it with a link to "
                + URL + ". Educational information only, not tax, legal or accounting advice.")
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
POPULAR = [("Meals", "meals"), ("Home office", "home office"), ("Car", "car"), ("Phone", "phone"), ("Laptop", "laptop"), ("Travel", "travel"),
           ("Software", "software"), ("Health insurance", "health insurance"), ("Client gifts", "gifts"), ("Parking tickets", "parking ticket"),
           ("Coworking", "coworking"), ("Contractors", "contractors")]
LEGEND = {"deductible": "Generally deductible", "partly": "A share, a percentage or up to a limit",
          "depends": "Turns on how and why you use it", "not": "Generally not deductible"}
TYPE_EXAMPLES = ["client lunch", "new laptop", "home office", "parking ticket", "cell phone", "health insurance", "coworking desk"]
# The hero receipt: each line matches an entry's verdict (slug in the comment). Decorative; the real answers are in the list.
RECEIPT = [("Client lunch", "$86.40", "half", "50%"),        # meals
           ("Office chair", "$340.00", "yes", ""),          # tools-equipment / de minimis
           ("Design software", "$29.00", "yes", ""),        # software-subscriptions
           ("Cell phone bill", "$78.00", "part", ""),       # cell-phone (business share)
           ("Golf with a client", "$120.00", "no", ""),     # entertainment
           ("Parking ticket", "$45.00", "no", "")]          # fines-penalties
MARKS = {"yes": '<path pathLength="1" d="m4 12.5 5 5L20 6.5"/>', "no": '<path pathLength="1" d="M6 6l12 12"/><path pathLength="1" d="M18 6 6 18"/>',
         "half": '<circle pathLength="1" cx="12" cy="12" r="8.5"/>', "part": '<path pathLength="1" d="M12 3.5a8.5 8.5 0 1 1-8.5 8.5"/>'}

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
    "tick": '<path pathLength="1" d="m5 12.5 4.2 4.2L19 7"/>',
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


def first_sentence(t):
    return t.split(". ")[0].rstrip(".") + "."


def verdict_big(e):
    """'50% deductible', 'Partly deductible', 'Not deductible' ..."""
    if e["verdict"] == "not":
        return VERDICTS["not"]["big"]
    return f'{e["percent"]}% deductible' if e["percent"] is not None else VERDICTS[e["verdict"]]["big"]


def checklist(t):
    """Records text -> checklist items: one per sentence, and 'X, plus Y' becomes two items."""
    out = []
    for sent in re.split(r"(?<=[a-z0-9)])\.\s+(?=[A-Z])", t.strip()):
        for part in re.split(r",\s+plus\s+", sent.rstrip(".")):
            part = part.strip()
            if part:
                out.append(part[0].upper() + part[1:])
    return out


def stamp(e, cls="dd-stamp"):
    pct = f'<i>{e["percent"]}%</i>' if e["percent"] is not None and e["verdict"] != "not" else ""
    return f'<span class="{cls}"><b>{esc(VERDICTS[e["verdict"]]["label"])}</b>{pct}</span>'


def full(e):
    """The complete answer for one expense, server-rendered (crawlable, readable without JS). The popup reuses this markup."""
    v = VERDICTS[e["verdict"]]
    src = (f'<li><a href="{esc(e["source_url"])}" target="_blank" rel="noopener">{esc(e["source_title"])}</a></li>' +
           "".join(f'<li><a href="{esc(a["url"])}" target="_blank" rel="noopener">{esc(a["title"])}</a></li>' for a in e.get("also", [])))
    tools = "".join(f'<a href="{u}">{esc(TOOL_NAMES[u])}</a>' for u in e.get("tools", []))
    recs = "".join(f'<li style="--i:{i}">{svg("tick", 2.4)}<span>{esc(r)}</span></li>' for i, r in enumerate(checklist(e["records"])))
    return (f'<div class="dd-full">'
            f'<p class="dd-vl"><strong>{esc(verdict_big(e))}.</strong> {esc(v["line"])}</p>'
            f'<div class="dd-sec dd-rule"><h4>The rule</h4><blockquote><p>{esc(e["rule"])}</p></blockquote></div>'
            f'<div class="dd-sec"><h4>Limits</h4><p>{esc(e["limits"])}</p></div>'
            f'<div class="dd-sec"><h4>Records to keep</h4><ul class="dd-check">{recs}</ul></div>'
            f'<div class="dd-sec"><h4>Who it applies to</h4><p>{esc(e["applies_to"])}</p></div>'
            f'<div class="dd-sec dd-srcs"><h4>Official sources</h4><ul>{src}</ul></div>'
            + (f'<div class="dd-sec"><h4>Related MFA tools</h4><div class="dd-tools">{tools}</div></div>' if tools else "") +
            '</div>')


def item(e, cats):
    return (f'<article class="dd-item v-{e["verdict"]}" id="{e["slug"]}" data-slug="{e["slug"]}" data-cat="{e["category"]}">'
            f'<div class="top"><span class="cat">{esc(cats[e["category"]]["name"])}</span>{stamp(e)}</div>'
            f'<h3><a class="dd-open" href="#{e["slug"]}" aria-haspopup="dialog">{esc(e["name"])}</a></h3>'
            f'<p class="dd-tease">{esc(first_sentence(e["rule"]))}</p>{full(e)}'
            f'<span class="go" aria-hidden="true">Rules, limits &amp; records</span></article>')


FAQ = [
    ("What makes a business expense deductible?",
     "The general test is that the cost is ordinary and necessary for carrying on your trade or business. Personal, living and family costs aren't "
     "deductible, and when something is used for both business and personal purposes, only the business share counts. Some expenses also have their "
     "own limits, such as the 50% limit on business meals and the $25 limit on gifts."),
    ("What can I write off if I'm self-employed?",
     "Ordinary and necessary costs of running your business, reported on Schedule C. Common write-offs include software and supplies, "
     "advertising, payments to contractors, business insurance, business travel, a qualifying home office and the business share of your "
     "phone, internet and car. Self-employed people can also deduct half of their self-employment tax, self-employed health insurance "
     "premiums if they qualify, and contributions to a SEP IRA or solo 401(k); those are claimed on Form 1040 rather than Schedule C."),
    ("Can I deduct 100% of business meals in 2026?",
     "Usually not. Business meals with clients and meals while traveling are generally 50% deductible (80% for workers under Department of "
     "Transportation hours-of-service limits). Holiday parties and similar events mainly for employees are fully deductible. Starting in 2026, food "
     "and drinks an employer provides to employees at work, such as office snacks or on-site meals for the employer's convenience, are no longer deductible."),
    ("What expenses are never deductible as business expenses?",
     "Commuting between home and your regular workplace, fines and penalties paid to a government (including parking tickets and tax "
     "penalties), political contributions and most lobbying, dues for social, athletic and similar clubs, entertainment such as game "
     "tickets and golf, and personal, living and family expenses. A sole proprietor's charitable donations aren't a business expense "
     "either, though they may be deductible on Schedule A if you itemize."),
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


def all_sources():
    seen = {}
    for e in DATA["entries"]:
        for t, u in [(e["source_title"], e["source_url"])] + [(a["title"], a["url"]) for a in e.get("also", [])]:
            seen.setdefault(u, t)
    return seen


def structured_data(title, desc, n):
    """WebPage (reviewedBy, citations) + WebApplication + Dataset + FAQPage + ItemList + BreadcrumbList, one @graph."""
    meta, E = DATA["meta"], DATA["entries"]
    pubs = [{"@type": "CreativeWork", "@id": u, "name": t, "url": u,
             "publisher": {"@type": "GovernmentOrganization", "name": "Internal Revenue Service", "url": "https://www.irs.gov/"}}
            for u, t in sorted(all_sources().items(), key=lambda r: r[1])
            if u.startswith("https://www.irs.gov/") and ("/publications/" in u or "/instructions/" in u or "/pub/irs-pdf/" in u)]
    app = {"@type": "WebApplication", "@id": URL + "#app", "name": "Is It Deductible? business expense finder", "url": URL,
           "description": desc, "applicationCategory": "FinanceApplication", "applicationSubCategory": "Tax deduction lookup",
           "operatingSystem": "Any", "browserRequirements": "Works in any modern browser; search and filters use JavaScript",
           "inLanguage": "en-US", "publisher": {"@id": seo.ORG_ID}, "creator": {"@id": seo.ORG_ID},
           "featureList": [f"Search {n} common business expenses by name or everyday wording",
                           "Filter by category", "Verdict, rule, limits, records to keep and the IRS source for each expense"],
           "isBasedOn": {"@id": URL + "#dataset"}}
    dataset = {"@type": "Dataset", "@id": URL + "#dataset", "name": f"Is It Deductible? {meta['tax_year']} business expense deductions",
               "description": (f"{n} common small business expenses with a verdict (deductible, partly, depends, not deductible), the percentage "
                               f"where one applies, the rule, limits, records to keep and who it applies to, each sourced to IRS publications, "
                               f"instructions or the Internal Revenue Code. Facts checked {nice(meta['checked'])}."),
               "url": URL, "sameAs": JSON_URL, "inLanguage": "en-US",
               "keywords": ["tax deductions", "business expenses", "self-employed", "Schedule C", "write-offs", str(meta["tax_year"])],
               "temporalCoverage": str(meta["tax_year"]), "spatialCoverage": {"@type": "Country", "name": "United States"},
               "dateModified": PAGE_MODIFIED, "creator": {"@id": seo.ORG_ID}, "publisher": {"@id": seo.ORG_ID},
               "copyrightHolder": {"@id": seo.ORG_ID}, "copyrightNotice": LICENSE_NOTE,
               "license": {"@type": "CreativeWork", "name": "Copyright Merchant Financial Advisory LLC; reuse with attribution (cite with a link)", "url": URL},
               "contributor": {"@id": seo.PERSON_ID}, "citation": [{"@id": c["@id"]} for c in pubs],
               "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": JSON_URL}}
    faq = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    items = {"@type": "ItemList", "@id": URL + "#expenses", "name": f"{n} business expenses and whether they're deductible in {meta['tax_year']}",
             "numberOfItems": n, "itemListOrder": "https://schema.org/ItemListUnordered", "itemListElement": [
                 {"@type": "ListItem", "position": i, "url": f"{URL}#{e['slug']}", "name": f"{e['name']}: {verdict_big(e)}",
                  "description": first_sentence(e["rule"])} for i, e in enumerate(E, 1)]}
    ld = seo.graph(URL, title.replace(" | MFA", ""), desc, app, dataset, faq, items,
                   crumb=[("Home", BASE + "/"), ("Resources", BASE + "/resources/"), ("Is it tax deductible?", URL)],
                   modified=PAGE_MODIFIED,
                   extra={"mainEntity": {"@id": URL + "#app"}, "hasPart": [{"@id": URL + "#expenses"}, {"@id": URL + "#faq"}],
                          "reviewedBy": {"@id": seo.PERSON_ID}, "lastReviewed": meta["last_reviewed"], "citation": pubs,
                          "keywords": "is it tax deductible, can I write off, business expense deductions 2026, what can I write off self-employed"})
    return clean_ld(ld)


def write_json():
    """Publishes the dataset at /tools/is-it-deductible/deductions.json (same content as data/deductions.json, plus where it lives and the license)."""
    out = {"meta": {**{k: v for k, v in DATA["meta"].items() if k != "owner"}, "url": JSON_URL, "page": URL, "page_modified": PAGE_MODIFIED, "license": LICENSE_NOTE,
                    "publisher": seo.NAME}, "entries": DATA["entries"]}
    path = SITE / "tools" / SLUG / "deductions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def llms_lines(full_text=False):
    """Plain-text summary of every entry for llms.txt (one line each) and llms-full.txt (rule, limits, records, source). Used by tools/seo.py."""
    E, meta = DATA["entries"], DATA["meta"]
    if not full_text:
        return [f"- [{e['name']}]({URL}#{e['slug']}): {verdict_big(e)}. {first_sentence(e['rule'])}" for e in E]
    o = []
    for e in E:
        o += [f"### {e['name']}: {verdict_big(e)}", f"Rule: {e['rule']}", f"Limits: {e['limits']}", f"Records to keep: {e['records']}",
              f"Applies to: {e['applies_to']}", f"Source: {e['source_title']} {e['source_url']}"]
        o += [f"Also: {a['title']} {a['url']}" for a in e.get("also", [])]
        o += [f"Page: {URL}#{e['slug']}", ""]
    return o


def build():
    check_data()
    meta, E = DATA["meta"], DATA["entries"]
    cats = {c["id"]: c for c in meta["categories"]}
    checked = nice(meta["checked"])
    reviewed = nice(meta["last_reviewed"])
    n = len(E)
    title = "Is It Tax Deductible? 2026 Business Write-Off Finder | MFA"
    desc = (f"Can I write it off? Search {n} business expense deductions for 2026: what self-employed people can deduct, "
            "the limits, records and IRS source.")
    assert len(title) <= 60 and len(desc) <= 155, (len(title), len(desc))

    chips = "".join(f'<button class="dd-chip" type="button" data-q="{esc(q)}">{esc(t)}</button>' for t, q in POPULAR)
    chips_dup = "".join(f'<button class="dd-chip" type="button" data-q="{esc(q)}" tabindex="-1">{esc(t)}</button>' for t, q in POPULAR)
    rows = "".join(f'<li style="--i:{i}"><span class="n">{esc(nm)}</span><span class="ld"></span><span class="a">{amt}</span>'
                   f'<span class="mk m-{k}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" '
                   f'stroke-linejoin="round">{MARKS[k]}</svg>{f"<em>{esc(t)}</em>" if t else ""}</span></li>'
                   for i, (nm, amt, k, t) in enumerate(RECEIPT))
    receipt = f"""<div class="dd-rcpt" aria-hidden="true"><div class="paper">
    <div class="rh"><b>MFA</b><span>Expense review</span><span>Tax year {meta["tax_year"]}</span></div>
    <ol>{rows}</ol>
    <div class="tot"><span>Write-offs</span><span class="ld"></span><span>?</span></div>
    <div class="bar"></div></div>
    <div class="dd-bigstamp"><span>Deductible?</span></div></div>"""
    hero = f"""<header class="bhero dd-hero"><div class="wrap">
  <div class="crumbs"><a href="/">Home</a> / <a href="/resources/">Resources</a> / Is it tax deductible?</div>
  <div class="dd-hgrid"><div class="dd-htext">
  <h1>Is it tax <em>deductible?</em></h1>
  <p class="dd-dek">Can I write this off? Search {n} common business expenses to see what's deductible for {meta["tax_year"]}, the limits that apply and the records to keep. Every answer links to its IRS source.</p>
  <div class="dd-search" role="search">{svg("search", 2)}<input type="search" id="dd-q" placeholder="Search an expense, e.g. meals, laptop, phone" aria-label="Search an expense" aria-controls="dd-list" autocomplete="off" spellcheck="false" data-examples="{esc(json.dumps(TYPE_EXAMPLES))}"/><button type="button" class="dd-x-q" id="dd-clear-q" aria-label="Clear search" hidden>×</button></div>
  <noscript><p class="dd-nojs">Search and filters need JavaScript. All {n} answers are listed in full below.</p></noscript>
  <p class="dd-rev">Reviewed by <a href="/authors/zain-merchant/">Zain Merchant, ACCA</a> · Last reviewed {reviewed}<br/>Facts checked {checked} · {n} expenses · Sources: IRS and the Internal Revenue Code</p>
  </div>{receipt}</div>
</div>
<div class="dd-marq" role="group" aria-label="Most searched expenses"><span class="lbl">Most searched</span><div class="track"><div class="belt"><span class="set">{chips}</span><span class="set dup" aria-hidden="true">{chips_dup}</span></div></div></div>
</header>"""

    warn = (f'<aside class="dd-warn" aria-label="Important: educational information only">{svg("warn", 1.9)}<div>'
            f'<strong>Educational information only, not tax, legal or accounting advice.</strong>'
            f'<p>Tax rules change and depend on your facts. Do your own research using the IRS sources linked, and talk to a qualified tax professional before you file.</p></div></aside>')
    cat_btns = "".join(
        f'<button type="button" class="dd-cat{" not" if c["id"] == "not" else ""}" data-cat="{c["id"]}" aria-pressed="false" style="--i:{i}"><i>{svg(c["icon"])}</i>'
        f'<span><b>{esc(c["name"])}</b><small>{c["count"]} {"expense" if c["count"] == 1 else "expenses"}</small></span></button>'
        for i, c in enumerate(c for c in meta["categories"] if c["count"]))
    legend = "".join(f'<li class="v-{k}"><span class="dd-stamp"><b>{esc(v["label"])}</b></span><span>{esc(LEGEND[k])}</span></li>' for k, v in VERDICTS.items())
    items = "".join(item(e, cats) for e in E)
    main = f"""<main class="dd-main" id="dd-main"><div class="wrap">
{warn}
<section class="dd-catsec" aria-labelledby="dd-cats-h"><div class="dd-hd"><h2 id="dd-cats-h">Browse by category</h2><p>Tap a category to filter the list. Tap it again to show everything.</p></div>
<div class="dd-cats">{cat_btns}</div></section>
<section id="dd-results" aria-labelledby="dd-res-h" style="scroll-margin-top:96px"><div class="dd-hd"><h2 id="dd-res-h">All {n} business expenses</h2><p><span id="dd-count" aria-live="polite">{n} expenses</span> <button type="button" class="dd-link" id="dd-all" hidden>Show all</button></p></div>
<ul class="dd-legend" aria-label="What the labels mean">{legend}</ul>
<div class="dd-list" id="dd-list">{items}</div>
<div class="dd-empty" id="dd-empty" hidden>Nothing matches “<span id="dd-empty-q"></span>” yet. Try a different word, browse the categories, or <a href="/#book" data-conv="book">ask us directly</a>.</div>
</section></div></main>"""

    kinds = "".join(f'<li class="v-{k}"><span class="dd-stamp"><b>{esc(v["label"])}</b></span><span>{esc(v["line"])}</span></li>' for k, v in VERDICTS.items())
    src_html, n_src = sources_list()
    faq = ui_kit.faq_accordion([(esc(q), esc(a)) for q, a in FAQ])
    info = f"""<div class="tinfo"><article class="article">
<h2>How to read the answers</h2>
<p>Each expense gets one of four labels. Open any card for the rule in plain English, the limits, the records to keep and the official source it comes from.</p>
<ul class="dd-kinds">{kinds}</ul>
<p>Answers are written for sole proprietors and single-member LLCs filing Schedule C, and most apply the same way to partnerships and corporations. Figures are for the {meta["tax_year"]} tax year where the IRS has published them. Pair this with the <a href="/tools/home-office-deduction-calculator/">home office calculator</a>, the <a href="/tools/mileage-deduction-calculator/">mileage calculator</a> and the <a href="/tools/1099-tax-calculator/">1099 tax calculator</a> to see what your deductions are worth.</p>
<p>Building something with this? The full list is published as a dataset at <a href="/tools/{SLUG}/deductions.json">deductions.json</a>. Cite it with a link to this page.</p>
<section class="faqs" id="faqs"><h2>FAQs</h2>{faq}</section>
<section class="sources dd-src-g"><h2>Official sources</h2><p>All {n_src} sources used on this page. IRS Publication 535 (Business Expenses) has been discontinued, so it isn't cited.</p>{src_html}
<p class="disclaimer">Reviewed by <a href="/authors/zain-merchant/">Zain Merchant, ACCA</a>, {reviewed}. Facts checked against the sources above as of {checked}. {esc(NOTE)}</p></section>
</article></div>"""

    modal = """<div class="dd-modal" id="dd-modal" hidden aria-hidden="true"><div class="dd-back" id="dd-back"></div>
<div class="dd-sheet" id="dd-sheet" role="dialog" aria-modal="true" aria-labelledby="dd-mtitle" tabindex="-1">
<button type="button" class="dd-close" id="dd-close" aria-label="Close">×</button><div id="dd-mbody"></div></div></div>"""

    # Search index only: everything a reader sees is in the HTML above.
    payload = {
        "entries": [{"slug": e["slug"], "name": e["name"], "aliases": e["aliases"], "category": e["category"], "verdict": e["verdict"],
                     "percent": e["percent"]} for e in E],
        "categories": [{"id": c["id"], "name": c["name"]} for c in meta["categories"]],
        "verdicts": {k: {"label": v["label"], "big": v["big"]} for k, v in VERDICTS.items()}, "checked_label": checked,
        "short_disclaimer": SHORT_DISCLAIMER, "icons": {k: svg("v-" + k, 1.8) for k in VERDICTS},
    }
    data_tag = '<script type="application/json" id="dd-data">' + json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/") + "</script>"

    ld = structured_data(title, desc, n)
    extra = ('<script>document.documentElement.classList.add("dd-js")</script>' + EXTRA_CSS +
             f'<link rel="stylesheet" href="/resources/deductible.css?v={V("deductible.css")}"/>' +
             f'<link rel="alternate" type="application/json" href="/tools/{SLUG}/deductions.json" title="Is It Deductible? dataset"/>' + seo.script(ld))
    body = (hero + main + info + modal + data_tag +
            f'<script src="/resources/deductible.js?v={V("deductible.js")}" defer></script>' +
            cta("Not sure what you can write off?", "We review your expenses, set up your books so deductions are tracked all year and prepare your return. Book a 30-minute consultation."))
    html = f'{B.head(title, desc, URL, OG, extra)}\n<body class="dd-page">{B.nav("res")}\n{body}\n{B.FOOT}</body></html>'
    ids = re.findall(r'\sid="([^"]+)"', html)
    dup = {x for x in ids if ids.count(x) > 1}
    assert not dup, f"duplicate ids on the page: {sorted(dup)}"
    write_json()
    return write(f"tools/{SLUG}", html)


if __name__ == "__main__":
    print(build())
