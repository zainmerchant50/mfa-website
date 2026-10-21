#!/usr/bin/env python3
"""Builds /services/ (Site session). Moved off the home page at Zain's request (2026-10-20 20:54).

Only Zain-approved prices appear: LLC formation from $150 (+ state fee; raised from $99 by Zain 2026-10-20), Complete Launch $649,
monthly bookkeeping from $199/month (Zain, 2026-10-20). Everything else says "quoted up front".
Never "free", never "CPA", no street address. Customer-facing dates: date only.
"""
import json

import build_blog as B
import seo
from build_resources import page, write, esc, BASE, cta

ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'

SERVICES = [
    ("tax-preparation", "Tax Preparation &amp; Filing",
     "Federal and multi-state returns for individuals and businesses: accurate, on time, and positioned to minimize what you legitimately owe.",
     ["Individual returns (Form 1040) with Schedule C, E and multi-state filings",
      "Business returns: partnerships (1065), S corporations (1120-S), C corporations (1120)",
      "Federal and state estimated tax calculations, with a payment calendar",
      "1099 preparation and filing for the contractors you pay",
      "Extensions filed on time when the numbers aren't ready"],
     "Quoted up front by return type and complexity.",
     [("/tools/quarterly-estimated-tax-calculator/", "Quarterly estimated tax calculator"), ("/tools/tax-deadlines-2027/", "2027 tax deadlines")]),
    ("tax-planning", "Tax Planning &amp; Strategy",
     "Year-round planning tied to live numbers: entity elections, estimated payments, retirement vehicles and deductions.",
     ["Entity and S corporation analysis, including a reasonable-salary range",
      "Quarterly estimate reviews against year-to-date results",
      "Retirement plan options for owners (SEP IRA, solo 401(k))",
      "Year-end planning before December 31, while there's still time to act"],
     "Quoted up front; often bundled with monthly bookkeeping.",
     [("/tools/s-corp-tax-savings-calculator/", "Is an S corp worth it?"), ("/tools/1099-tax-calculator/", "1099 tax calculator")]),
    ("bookkeeping", "Bookkeeping &amp; Accounting",
     "Transactions, reconciliations, AP/AR and a disciplined monthly close, so your books stay decision-ready all year, not just at year-end.",
     ["Monthly categorization to a chart of accounts built for your business",
      "Bank, credit card and loan reconciliations to the statements",
      "Accounts payable and receivable tracking",
      "Monthly P&amp;L and balance sheet with a short note on what changed",
      "Catch-up and cleanup projects for books that are months behind (quoted after we look at a sample of your accounts)"],
     "Monthly bookkeeping <strong>from $199/month</strong> for one bank account, one card and up to 100 transactions a month. Larger books and cleanup projects are quoted up front.",
     [("/bookkeeping-cleanup/", "Request a bookkeeping cleanup quote"), ("/llc-formation/#monthly", "How monthly bookkeeping works"), ("/tools/1099-contractor-tracker/", "1099 contractor tracker")]),
    ("financial-reporting", "Financial Reporting",
     "P&amp;L, balance sheet and cash flow prepared for management use, plus the dashboards that turn them into decisions.",
     ["Monthly or quarterly financial statements for owners and managers",
      "Cash flow view and simple KPI dashboard",
      "Budget vs. actual and prior-period comparisons",
      "Statements prepared for your own use; we don't issue audit, review or compilation reports"],
     "Quoted up front; included in many monthly plans.",
     [("/tools/profit-margin-calculator/", "Profit margin calculator"), ("/tools/break-even-calculator/", "Break-even calculator")]),
    ("fractional-cfo", "Fractional CFO",
     "Forecasting, budgeting, margin analysis and board-ready reporting: financial leadership without an executive salary.",
     ["13-week cash flow and 12-month forecasts",
      "Annual budget and monthly review meetings",
      "Pricing and margin analysis by product, service or client",
      "Lender and investor reporting packages"],
     "Monthly retainer, quoted up front.",
     [("/tools/break-even-calculator/", "Break-even calculator")]),
    ("audit-support", "Audit Support &amp; Controls",
     "Help getting ready for your auditor: PBC lists, internal-controls assessment and remediation, drawn from Big Four audit experience.",
     ["Prepared-by-client (PBC) schedules and support",
      "Internal-controls walkthroughs and documentation",
      "Remediation plans for deficiencies your auditor raised",
      "We support your audit; we don't perform audits or issue audit opinions"],
     "Project fee, quoted up front.",
     []),
    ("technical-accounting", "Technical Accounting Advisory",
     "US GAAP and IFRS guidance on the hard parts: revenue recognition, leases, financial instruments and consolidations.",
     ["Accounting position memos (ASC 606, ASC 842 and others)",
      "IFRS to US GAAP differences for cross-border businesses",
      "Consolidation and intercompany setup"],
     "Hourly or project fee, quoted up front.",
     []),
    ("business-advisory", "Systems &amp; Business Advisory",
     "Entity formation, QuickBooks setup and cleanup, system selection, and financially grounded guidance for the decisions that matter.",
     ["LLC formation in all 50 states and DC, with EIN and operating agreement template",
      "QuickBooks Online setup, migration and cleanup",
      "Accounting system and app selection",
      "Business plans and financial models for banks"],
     "LLC formation <strong>from $150 plus the state fee</strong>, paid once. Other work quoted up front.",
     [("/llc-formation/", "LLC formation packages")]),
]

OFFERS = [
    ("LLC formation", "From $150", "+ state fee, paid once", "Formation $150, Business Setup $249, Complete Launch $649 with your first month of bookkeeping.", "/llc-formation/", "See packages"),
    ("Monthly bookkeeping", "From $199", "/ month", "One bank, one card, up to 100 transactions a month. Month to month; bigger books quoted up front.", "/llc-formation/#monthly", "How it works"),
    ("Tax preparation", "Quoted", "up front", "Individual and business returns, federal and state. You see the price before we start.", "/#book", "Get a quote"),
]


def build():
    url = BASE + "/services/"
    title = "Tax, Bookkeeping & CFO Services in NJ and NYC | MFA"
    desc = ("Tax preparation, bookkeeping from $199/month, fractional CFO, audit support and LLC formation from $150. "
            "Princeton, NJ; New York City; clients nationwide.")
    jump = "".join(f'<a href="#{sid}">{name}</a>' for sid, name, *_ in SERVICES)
    offers = "".join(f'''<div class="pkc card{" feat" if i == 1 else ""}"><span class="pk-tag">{esc(n)}</span>
<p class="pk-price"><b>{p}</b><span>{s}</span></p><p class="pk-lead">{t}</p>
<a class="btn {"btn-gold" if i == 1 else "btn-ink"}" href="{u}"{' data-conv="book"' if u == "/#book" else ""}>{b}</a></div>''' for i, (n, p, s, t, u, b) in enumerate(OFFERS))
    rows = []
    for i, (sid, name, lead, items, price, links) in enumerate(SERVICES, 1):
        lis = "".join(f"<li>{ICO}<span>{x}</span></li>" for x in items)
        lk = "".join(f'<a href="{u}">{esc(t)} →</a>' for u, t in links)
        rows.append(f'''<article class="sv card" id="{sid}"><div class="sv-hd"><span class="sv-n">{i:02d}</span><h2>{name}</h2></div>
<p class="sv-lead">{lead}</p><ul class="pk-list">{lis}</ul>
<p class="sv-price">{price}</p>{f'<p class="sv-links">{lk}</p>' if lk else ""}</article>''')
    body = f'''<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Accounting, tax &amp; business solutions</span>
<h1>Services built to <em>work together.</em></h1>
<p>Reporting, planning and compliance from one team, so each piece strengthens the others. Flat monthly fees or hourly, always quoted before we start.</p>
<div class="hero-btns"><a class="btn btn-gold" href="/#book" data-conv="book">Book a 30-minute consultation</a><a class="btn btn-line" href="#all">See all services</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="of-h"><div class="sec-hd"><span class="eyebrow eb-dark">Start here</span><h2 id="of-h">Three common starting points.</h2></div>
<div class="pk">{offers}</div></section>
<section class="wrap llc-sec" id="all" aria-labelledby="all-h"><div class="sec-hd"><span class="eyebrow eb-dark">All services</span><h2 id="all-h">Eight services, one finance function.</h2></div>
<nav class="sv-jump" aria-label="Jump to a service">{jump}</nav>
<div class="svs">{"".join(rows)}</div></section>
<section class="wrap llc-sec"><div class="diy card"><div><span class="eyebrow eb-dark">Prefer to do it yourself?</span><h3>Calculators, trackers and guides</h3>
<p>Quarterly estimates, 1099 tax, S corp savings, paycheck, home office and mileage calculators, a 1099 contractor tracker and the 2027 deadline calendar.</p></div>
<a class="btn btn-ink" href="/resources/">Browse resources</a></div></section>
<section class="wrap llc-sec" aria-labelledby="more-h"><div class="sec-hd"><span class="eyebrow eb-dark">Where we work, and more</span><h2 id="more-h">Local pages and related pages.</h2></div>
<nav class="sv-jump" aria-label="Local pages and related pages"><a href="/princeton-nj/">Princeton, NJ</a><a href="/union-city-nj/">Union City, NJ</a><a href="/new-york-ny/">New York City</a><a href="/llc-formation/">LLC formation in all 50 states</a><a href="/bookkeeping-cleanup/">Bookkeeping cleanup quote</a><a href="/shop/">Shop</a><a href="/resources/">Resources</a><a href="/blog/">MFA Insights</a><a href="/authors/zain-merchant/">About Zain Merchant, ACCA</a></nav></section>
{cta("Not sure where to start?", "Tell us what's going on in a 30-minute call and we'll suggest the smallest engagement that fixes it, with a price before any work begins.")}
<section class="wrap llc-sec"><p class="disclaimer">Merchant Financial Advisory provides accounting, bookkeeping, tax preparation and advisory services. We do not perform audits or issue audit, review or compilation reports, and we are not a law firm. Languages: English, Hindi and Urdu.</p></section>
</main>'''
    ld = seo.graph(url, "Services", desc, {"@type": "OfferCatalog", "@id": url + "#catalog", "name": "MFA services", "url": url,
                                            "itemListElement": [{"@id": f"{url}#{sid}"} for sid, *_ in SERVICES]},
                   *seo.service_nodes(), kind="CollectionPage", full_org=True,
                   crumb=[("Home", BASE + "/"), ("Services", url)])
    return write("services", page(title, desc, url, body, ld, active="s"))


if __name__ == "__main__":
    print(build())
