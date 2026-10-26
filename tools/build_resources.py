#!/usr/bin/env python3
"""Builds the MFA Resources hub (/resources/) and the interactive tools (/tools/<slug>/).

Site session owns this file (see claude/site-session-brief.md). Run from the repo root:
    python3 tools/build_resources.py
It reuses the blog's head/nav/footer (tools/build_blog.py) and ui_kit animations so every page matches.
Every tool shows: an "educational information, not tax or legal advice" note, a "facts checked" date
and its official sources. Tax figures live in the FACTS dict below, each with its source URL.
Writes tools/site_pages.json so build_blog.py can list these URLs in sitemap.xml.
"""
import hashlib, json, re, sys
from urllib.parse import quote
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_blog as B  # noqa: E402
import seo  # noqa: E402  JSON-LD building blocks and root files (tools/seo.py)

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BASE, esc = B.BASE, B.esc
OG = BASE + "/apple-touch-icon.png"
CSS = SITE / "resources" / "resources.css"
CSS_V = hashlib.md5(CSS.read_bytes()).hexdigest()[:10]
EXTRA_CSS = f'<link rel="stylesheet" href="/resources/resources.css?v={CSS_V}"/>'
NOTE = ("Educational information, not tax or legal advice. Results are estimates based on the information you enter; "
        "your situation may differ. Using this tool doesn't create a client relationship.")

# Verified figures (re-check each season). Every number used by a tool lives here with its source.
FACTS = {
    "1099": {
        "checked": "2026-10-20",
        "nec_threshold": 2000, "misc_threshold": 2000, "royalties": 10, "attorney_proceeds": 600,
        "sources": [
            ("IRS: Instructions for Forms 1099-MISC and 1099-NEC (12/2026)", "https://www.irs.gov/instructions/i1099mec"),
            ("IRS IR-2025-107: Form 1099-K threshold reverts to $20,000 and 200 transactions",
             "https://www.irs.gov/newsroom/irs-issues-faqs-on-form-1099-k-threshold-under-the-one-big-beautiful-bill-dollar-limit-reverts-to-20000"),
            ("IRS: Backup withholding", "https://www.irs.gov/businesses/small-businesses-self-employed/backup-withholding"),
            ("IRS: About Form W-9", "https://www.irs.gov/forms-pubs/about-form-w-9"),
        ],
    },
    "w9": {"checked": "2026-10-20", "sources": [("IRS: About Form W-9 (Rev. March 2024)", "https://www.irs.gov/forms-pubs/about-form-w-9")]},
    "breakeven": {"checked": "2026-10-20", "sources": [("U.S. Small Business Administration: Break-even point", "https://www.sba.gov/breakevenpointcalculator")]},
}

I = {  # simple line icons (stroke = currentColor)
    "calc": '<rect x="5" y="2.5" width="14" height="19" rx="2.5"/><path d="M8.5 6.5h7M8.5 11h1M12 11h1M15.5 11h0M8.5 14.5h1M12 14.5h1M15.5 14.5v3M8.5 18h1M12 18h1"/>',
    "check": '<path d="M9 11.5l2.2 2.2L15.5 9.5"/><rect x="3.5" y="3.5" width="17" height="17" rx="4"/>',
    "cal": '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m21 7-9 6-9-6"/>',
    "book": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20"/>',
    "map": '<path d="M9 4 3.5 6v14L9 18l6 2 5.5-2V4L15 6z"/><path d="M9 4v14M15 6v14"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "pct": '<circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/><path d="M19 5 5 19"/>',
    "home": '<path d="M3.5 11 12 4l8.5 7"/><path d="M5.5 9.5V20h13V9.5"/>',
    "car": '<path d="M5 16.5h14M6.5 16.5V19M17.5 16.5V19M4 16.5l1.6-5.2A2 2 0 0 1 7.5 10h9a2 2 0 0 1 1.9 1.3l1.6 5.2"/>',
    "scale": '<path d="M12 4v16M5 8h14M5 8l-2.5 6a3 3 0 0 0 5 0zM19 8l-2.5 6a3 3 0 0 0 5 0zM8 20h8"/>',
    "list": '<path d="M9 6h11M9 12h11M9 18h11"/><path d="m3.5 6 1 1 2-2M3.5 12l1 1 2-2M3.5 18l1 1 2-2"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "user": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>',
    "box": '<path d="M3.5 7.5 12 3l8.5 4.5v9L12 21l-8.5-4.5z"/><path d="M3.5 7.5 12 12l8.5-4.5M12 12v9"/>',
}
svg = lambda k: f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{I[k]}</svg>'

# The hub: (group, title, description, url or None for "coming soon", icon, keywords, badge)
GROUPS = [
    ("checkers", "Checkers", "Answer a few questions, get a plain-English answer and what to do next."),
    ("calculators", "Calculators", "Quick numbers for pricing, planning and taxes."),
    ("calendars", "Calendars", "Never miss a filing or payment date."),
    ("templates", "Templates & checklists", "Ready-to-use emails, logs and checklists."),
    ("soon", "Coming soon", "Tools and templates on the way. Want one sooner? Tell us."),
    ("guides", "Guides", "In-depth MFA Insights articles, checked against IRS and state sources."),
    ("states", "State directory", "Formation fees, annual reports and filing offices by state."),
]
TOOLS = [
    ("checkers", "Do I need to send a 1099?", "Four questions to see whether a payment needs a 1099-NEC or 1099-MISC for 2026, and what to do next.",
     "/tools/do-i-need-to-send-a-1099/", "check", "1099 nec misc contractor w-9 threshold 2000", "New"),
    ("checkers", "Is It Deductible?", "Search an expense and see whether it's deductible, the limits and the records to keep.",
     "/tools/is-it-deductible/", "list", "deduction deductible write off expense business expenses schedule c", "New"),
    ("calculators", "Break-even calculator", "How many sales you need each month to cover your costs, and to hit a profit goal.",
     "/tools/break-even-calculator/", "chart", "break even pricing fixed costs contribution margin", "New"),
    ("calculators", "Profit margin & markup calculator", "Turn cost and price into margin and markup, or find the price for the margin you want.",
     "/tools/profit-margin-calculator/", "pct", "margin markup pricing gross profit", "New"),
    ("calculators", "Self-employment (1099) tax calculator", "Estimate self-employment tax, federal income tax and NJ/NY tax on freelance income.", None, "calc", "self employment tax 1099 freelancer", ""),
    ("calculators", "Quarterly estimated tax calculator", "Your four estimated payments and their due dates, federal and NJ/NY.", None, "calc", "estimated tax quarterly 1040-es", ""),
    ("calculators", "S corp vs LLC savings estimator", "See whether an S corp election could save tax once payroll costs are counted.", None, "scale", "s corp llc election salary", ""),
    ("calculators", "Home office deduction calculator", "Compare the simplified and regular home office methods.", None, "home", "home office deduction", ""),
    ("calculators", "Mileage deduction calculator", "Business miles times the IRS standard rate, with a log you can keep.", None, "car", "mileage standard rate", ""),
    ("calendars", "2027 tax calendar", "Every key federal and NJ/NY filing date for the 2027 season, with add-to-calendar links.",
     "/blog/2027-tax-calendar/", "cal", "tax deadlines 2027 calendar", ""),
    ("calendars", "Business tax deadlines by entity", "Sole proprietor, partnership, S corp, C corp, employer and nonprofit calendars.", None, "cal", "deadline entity s corp partnership", ""),
    ("templates", "W-9 request email templates", "Copy-ready emails to collect W-9s from new vendors, at year-end, and as a reminder.",
     "/tools/w-9-request-email-template/", "mail", "w-9 request email vendor template", "New"),
    ("states", "LLC formation: NJ & NY fees and first-year cost", "State filing fees, annual reports, tax registration and your first-year total, from the official state sources.",
     "/llc-formation/", "map", "llc formation state fee annual report new jersey new york", "New"),
]


# "Coming soon" (Zain, 2026-10-24: "add more coming soon resources where we might have new tools come in").
# Ordered by expected demand (search interest from MFA's audience), most-asked-for first. No dates, prices or outcomes.
# (title, kind, description, icon, keywords)
SOON = [
    ("Tax refund estimator", "Calculator", "Estimate your federal refund or amount due from your W-2s, 1099s and withholding.", "calc",
     "tax refund estimator federal refund amount due withholding w-2 1040"),
    ("NJ & NY sales tax calculator", "Calculator", "Add sales tax to a price, or back it out of a total, at New Jersey and New York rates.", "pct",
     "sales tax calculator new jersey new york rate reverse"),
    ("Contractor or employee?", "Checker", "Questions based on the IRS common-law factors to help you decide between a 1099 and a W-2.", "check",
     "worker classification contractor employee 1099 w-2 misclassification ss-8"),
    ("Freelance hourly rate calculator", "Calculator", "Work back from the income you want to the rate you need, after taxes, costs and time off.", "clock",
     "hourly rate freelancer pricing day rate self employed"),
    ("Mileage log & receipt log", "Template", "Simple logs that hold up if the IRS asks.", "doc", "mileage log receipt log"),
    ("Cost of hiring an employee calculator", "Calculator", "Wages plus employer payroll taxes and common extras, so you can budget a first hire.", "user",
     "cost of employee employer payroll taxes futa suta fica hiring budget"),
    ("Section 179 & depreciation calculator", "Calculator", "Compare Section 179, bonus and regular depreciation for an equipment or vehicle purchase.", "chart",
     "section 179 bonus depreciation macrs equipment vehicle"),
    ("Where do I owe sales tax?", "Checker", "Compare your sales in each state with the sales level at which that state makes out-of-state sellers collect its tax.", "map",
     "sales tax nexus economic nexus online sellers wayfair registration"),
    ("Month-end close checklist", "Template", "The steps to close your books cleanly every month.", "list", "month end close checklist"),
    ("Cash flow runway calculator", "Calculator", "How many months your cash covers your costs, and what changes when sales or spending move.", "chart",
     "cash flow runway burn rate small business forecast"),
    ("Chart of accounts samples", "Template", "Starter charts of accounts for service, retail and construction businesses.", "doc", "chart of accounts quickbooks"),
    ("Record retention checklist", "Template", "How long to keep receipts, returns, payroll and bank records, by document type.", "box",
     "how long to keep records receipts tax returns record retention"),
]
TOOLS += [("soon", t, d, None, icon, kw + " coming soon " + kind.lower(), kind) for t, kind, d, icon, kw in SOON]


def page(title, desc, url, body, ld=None, active="res", image=None, keywords=None):
    extra = EXTRA_CSS + (seo.script(ld) if ld else "")
    return f"""{B.head(title, desc, url, image or OG, extra, keywords)}
<body>{B.nav(active)}
{body}
{B.FOOT}</body></html>"""


def cta(headline, text):
    return f"""<section class="cta-block" aria-label="Book a consultation"><div class="cta-card">
  <span class="eyebrow">Talk to MFA</span><h2>{esc(headline)}</h2><p>{text}</p>
  <div class="cta-btns"><a class="btn btn-gold" href="/book/" data-conv="book">Book a 30-minute consultation</a><a class="btn btn-line" href="mailto:{B.EMAIL}">Email {B.EMAIL}</a></div>
</div></section>"""


def sources_block(key, extra_note=""):
    f = FACTS[key]
    checked = date.fromisoformat(f["checked"]).strftime("%B %-d, %Y")
    lis = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in f["sources"])
    return (f'<section class="sources"><h2>Sources</h2><ul>{lis}</ul>'
            f'<p class="disclaimer">Facts checked against the sources above as of {checked}. {extra_note}{NOTE}</p></section>')


def tool_header(eyebrow, h1, dek):
    return f"""<header class="ahead"><div class="wrap">
  <div class="crumbs"><a href="/">Home</a> / <a href="/resources/">Resources</a> / {esc(eyebrow)}</div>
  <span class="eyebrow">{esc(eyebrow)}</span><h1>{esc(h1)}</h1><p class="dek">{esc(dek)}</p>
</div></header>"""


def tool_ld(name, url, desc, cat="BusinessApplication"):
    app = {"@type": "WebApplication", "@id": url + "#app", "name": name, "url": url, "description": desc, "applicationCategory": cat,
           "operatingSystem": "Any", "browserRequirements": "Requires JavaScript", "inLanguage": "en-US",
           "publisher": {"@id": seo.ORG_ID}}
    return seo.graph(url, name, desc, app, crumb=[("Home", BASE + "/"), ("Resources", BASE + "/resources/"), (name, url)],
                     extra={"mainEntity": {"@id": url + "#app"}})


def clean_ld(ld):
    for g in ld["@graph"]:
        g.pop("isAccessibleForFreeYes", None)
    return ld


def write(rel, html):
    if rel.startswith("tools/"):   # internal links: tool -> service, shop product, guide (placed just above the site footer)
        rel_html = seo.related_html(rel.split("/", 1)[1])
        html = re.sub(r"<footer\b", lambda m: rel_html + m.group(0), html, count=1) if rel_html else html
        import tool_products
        html = tool_products.inject(rel.split("/", 1)[1], html)
    out = SITE / rel / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return BASE + "/" + rel + "/"


# ------------------------------------------------------------------ hub
def build_hub(posts):
    cards = {g[0]: [] for g in GROUPS}
    for grp, title, desc, url, icon, kw, badge in TOOLS:
        b = f'<span class="badge{" new" if badge == "New" else ""}">{esc(badge)}</span>' if badge and url else ""
        if url:
            cards[grp].append(f'<a class="rcard card" href="{url}" data-k="{esc((title + " " + desc + " " + kw).lower())}">{b}'
                              f'<span class="ri">{svg(icon)}</span><h3>{esc(title)}</h3><p>{esc(desc)}</p>'
                              f'<span class="go">{"Read the guide" if url.startswith("/blog/") else "Use the tool"} <i>→</i></span></a>')
        else:
            ask = f"mailto:{B.EMAIL}?subject=" + quote(f"Resource request: {title}")
            kind = f'<span class="kind">{esc(badge)}</span>' if badge else ""
            cards[grp].append(f'<div class="rcard card soon" data-k="{esc((title + " " + desc + " " + kw).lower())}"><span class="badge">Coming soon</span>'
                              f'<span class="ri">{svg(icon)}</span>{kind}<h3>{esc(title)}</h3><p>{esc(desc)}</p>'
                              f'<a class="rask" href="{esc(ask)}">Want this first? Tell us <i>→</i></a></div>')
    for p in posts:
        k = (p["title"] + " " + p["description"] + " " + p["category"] + " " + " ".join(p.get("keywords", []))).lower()
        cards["guides"].append(f'<a class="rcard card" href="/blog/{p["slug"]}/" data-k="{esc(k)}"><span class="ri">{svg("book")}</span>'
                               f'<span class="meta" style="font-size:9.5px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--gold)">{esc(p["category"])}</span>'
                               f'<h3>{esc(p["title"])}</h3><span class="go">Read the guide <i>→</i></span></a>')
    sections = "".join(
        f'<section class="rgroup" id="{gid}" data-g="{gid}"><div class="rgroup-hd"><h2>{esc(name)}</h2><p>{esc(sub)}</p></div>'
        f'<div class="rgrid">{"".join(cards[gid])}</div></section>' for gid, name, sub in GROUPS if cards[gid])
    chips = '<button class="chip" type="button" data-f="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" type="button" data-f="{gid}" aria-pressed="false">{esc(name)}</button>' for gid, name, _ in GROUPS if cards[gid])
    desc = ("Calculators, checkers, tax calendars, templates and guides for small businesses and individuals, "
            "from Merchant Financial Advisory in Princeton, NJ.")
    url = BASE + "/resources/"
    body = f"""<header class="bhero rhero"><div class="wrap"><span class="eyebrow">MFA Resources</span>
<h1>Tools for your taxes, books <em>and business.</em></h1>
<p>Calculators, checkers, calendars, templates and guides for individuals and small and mid-sized businesses. Plain English, checked against IRS and state sources.</p>
<div class="rsearch"><input type="search" id="rq" placeholder="Search tools and guides, e.g. 1099, break-even, deadline" aria-label="Search resources"/></div>
<div class="chips" role="group" aria-label="Filter by type">{chips}</div></div></header>
<main class="wrap rgroups" id="rmain">{sections}<p class="rempty" id="rempty">Nothing matches that search yet. Try another word, or <a href="/book/" style="border-bottom:1px solid var(--gold)">ask us directly</a>.</p></main>
<p class="rnote">{esc(NOTE)} Each tool lists its official sources and the date its facts were last checked.</p>
{__import__("tool_products").render("resources", slugs=__import__("tool_products").HUB, heading="Spreadsheets and checklists from the shop", campaign="resources-index")}
{cta("Rather have it handled for you?", "Book a 30-minute consultation about your books, taxes or business setup, or email us at <a href='mailto:" + B.EMAIL + "' style='color:#D8B769;border-bottom:1px solid rgba(216,183,105,.5)'>" + B.EMAIL + "</a>.")}
<script>
(function(){{var q=document.getElementById('rq'),chips=[].slice.call(document.querySelectorAll('.chip')),f='all';
var groups=[].slice.call(document.querySelectorAll('.rgroup')),empty=document.getElementById('rempty');
function run(){{var t=(q.value||'').toLowerCase().trim(),any=false;groups.forEach(function(g){{var on=f==='all'||g.getAttribute('data-g')===f,n=0;
[].slice.call(g.querySelectorAll('.rcard')).forEach(function(c){{var m=on&&(!t||c.getAttribute('data-k').indexOf(t)>-1);c.style.display=m?'':'none';if(m)n++;}});
g.style.display=n?'':'none';if(n)any=true;}});empty.style.display=any?'none':'block';}}
q.addEventListener('input',run);chips.forEach(function(c){{c.addEventListener('click',function(){{f=c.getAttribute('data-f');chips.forEach(function(x){{x.setAttribute('aria-pressed',x===c?'true':'false');}});run();}});}});
function hash(){{var h=location.hash.replace('#',''),c=h&&document.querySelector('.chip[data-f="'+h+'"]');if(c){{q.value='';c.click();var g=document.getElementById(h);if(g)g.scrollIntoView();}}}}
hash();window.addEventListener('hashchange',hash);}})();
</script>"""
    items = list(dict.fromkeys([t[3] for t in TOOLS if t[3]] + [f"/blog/{p['slug']}/" for p in posts]))
    ld = seo.graph(url, "MFA Resources", desc, {"@type": "ItemList", "@id": url + "#list", "name": "MFA tools, templates and guides",
                                                "itemListElement": [{"@type": "ListItem", "position": n, "url": BASE + u} for n, u in enumerate(items, 1)]},
                   kind="CollectionPage", crumb=[("Home", BASE + "/"), ("Resources", url)], extra={"mainEntity": {"@id": url + "#list"}})
    return write("resources", page("Tax Calculators, 1099 Checker & Templates | MFA Resources", desc, url, body, ld))


# ------------------------------------------------------------------ tool: 1099 checker
def build_1099():
    F = FACTS["1099"]
    url = BASE + "/tools/do-i-need-to-send-a-1099/"
    title = "Do I Need to Send a 1099? 2026 Payments Checker"
    desc = "Four questions show whether a 2026 payment needs a Form 1099-NEC or 1099-MISC: the $2,000 threshold, card and corporation exceptions, and deadlines."
    def radios(name, opts):
        return '<div class="opts">' + "".join(
            f'<label class="opt"><input type="radio" name="{name}" value="{v}"/><span>{t}{f"<small>{s}</small>" if s else ""}</span></label>' for v, t, s in opts) + "</div>"
    form = f"""<div class="tcard"><h2>Your payment</h2><p class="sub">Answer for one payee at a time. Totals are for everything you paid them from Jan. 1 to Dec. 31, 2026.</p>
<div class="prog" aria-hidden="true"><i id="pg"></i></div>
<div class="fld"><span class="lbl">1. Was it a business payment?</span>{radios("purpose", [("business", "Yes, paid by my business", ""), ("personal", "No, it was personal", "e.g., a contractor for your own home")])}</div>
<div class="fld"><span class="lbl">2. How did you pay?</span>{radios("method", [("bank", "Check, ACH, wire, cash, Zelle or a personal app transfer", "Includes PayPal Friends &amp; Family and personal Venmo / Cash App"), ("card", "Credit or debit card, or a business payment app", "PayPal Goods &amp; Services, Stripe, Square, business Venmo or Cash App")])}</div>
<div class="fld"><span class="lbl">3. Who did you pay?</span>{radios("payee", [("indiv", "Individual or sole proprietor", ""), ("llc", "LLC taxed as a sole proprietor or partnership, or a partnership", "Check box 3 on their Form W-9"), ("corp", "C corporation or S corporation", "Including an LLC that elected corporate tax status"), ("exempt", "Tax-exempt organization or government agency", ""), ("employee", "My employee", ""), ("foreign", "Foreign person or business (gave you a W-8)", "")])}</div>
<div class="fld"><span class="lbl">4. What was it for?</span>{radios("type", [("services", "Services or contract labor", "Freelancers, consultants, repairs, cleaning, bookkeeping"), ("attorney_fees", "Legal services (attorney fees)", ""), ("attorney_proceeds", "Gross proceeds paid to an attorney", "e.g., settlement funds paid to a lawyer"), ("rent", "Rent paid to the property owner", "Office, warehouse, equipment"), ("rent_agent", "Rent paid to a real estate agent or property manager", ""), ("medical", "Medical or health care services", ""), ("royalties", "Royalties", ""), ("prizes", "Prizes, awards or other income", ""), ("goods", "Merchandise, freight, storage or telephone", "")])}</div>
<div class="fld"><label for="amt">5. Total paid in 2026</label><div class="money"><input type="number" id="amt" min="0" step="0.01" inputmode="decimal" placeholder="0.00"/></div>
<label class="opt" style="margin-top:10px"><input type="checkbox" id="bw"/><span>I withheld federal income tax (backup withholding)<small>Usually because the payee didn't give you a tax ID number</small></span></label></div>
</div>"""
    result = """<div class="tcard tres" aria-live="polite"><h2>Your answer</h2><p class="sub">Updates as you answer.</p><div id="out"><div class="verdict"><span class="vk">Start with question 1</span><h3>Let's find out.</h3><p>Most 1099 questions come down to four things: business or personal, how you paid, who you paid, and how much.</p></div></div>
<div class="acts"><a class="btn btn-gold" href="/book/" data-conv="book">Have MFA file your 1099s</a><a class="btn btn-line" href="/blog/form-1099-preparation-guide-2026/">Read the full 1099 guide</a></div>
<p class="muted">Educational information, not tax or legal advice.</p></div>"""
    js = """<script>
(function(){var T={nec:%NEC%,misc:%MISC%,roy:%ROY%,att:%ATT%};
var M={services:['1099-NEC','Nonemployee compensation',T.nec,'nec'],attorney_fees:['1099-NEC','Attorney fees for legal services',T.nec,'nec'],
attorney_proceeds:['1099-MISC','Box 10: gross proceeds paid to an attorney',T.att,'misc10'],rent:['1099-MISC','Box 1: rents',T.misc,'misc'],
medical:['1099-MISC','Box 6: medical and health care payments',T.misc,'misc'],royalties:['1099-MISC','Box 2: royalties',T.roy,'misc'],prizes:['1099-MISC','Box 3: other income',T.misc,'misc']};
var $=function(n){var e=document.querySelector('input[name='+n+']:checked');return e?e.value:'';};
var out=document.getElementById('out'),amt=document.getElementById('amt'),bw=document.getElementById('bw'),pg=document.getElementById('pg');
var fmt=function(n){return '$'+Number(n).toLocaleString('en-US',{maximumFractionDigits:2});};
function v(cls,k,h,p,steps){out.innerHTML='<div class="verdict '+cls+'"><span class="vk">'+k+'</span><h3>'+h+'</h3><p>'+p+'</p></div>'+(steps?'<ol class="steps-out">'+steps.map(function(s){return '<li>'+s+'</li>';}).join('')+'</ol>':'');}
function due(code){if(code==='nec')return 'Send it to the payee <b>and</b> file it with the IRS by <b>Monday, Feb. 1, 2027</b> (no automatic extension).';
if(code==='misc10')return 'Send the payee copy by <b>Tuesday, Feb. 16, 2027</b>; file with the IRS by <b>March 1, 2027</b> on paper or <b>March 31, 2027</b> electronically.';
return 'Send the payee copy by <b>Monday, Feb. 1, 2027</b>; file with the IRS by <b>March 1, 2027</b> on paper or <b>March 31, 2027</b> electronically.';}
function run(){var p=$('purpose'),m=$('method'),w=$('payee'),t=$('type'),a=parseFloat(amt.value);
pg.style.width=([p,m,w,t].filter(Boolean).length+(amt.value?1:0))*20+'%';
if(!p)return;
if(p==='personal')return v('','Answer','No 1099 needed','1099s are only for payments made in the course of your trade or business. Personal payments, like a contractor who worked on your own home, aren\\'t reportable.');
if(!m)return v('','Next','Business payment: keep going','Now tell us how you paid. Payment method decides who reports it.');
if(m==='card')return v('','Answer','No 1099 from you','Payments by credit or debit card, and through payment processors like PayPal Goods &amp; Services, Stripe or Square, are reported by the processor on Form 1099-K. Don\\'t also send a 1099-NEC or 1099-MISC for those amounts.',['Keep the receipt and record the payee in your books.','If you paid the same vendor by check, ACH or Zelle too, run those payments through this checker separately.']);
if(!w)return v('','Next','Now: who did you pay?','The payee\\'s tax classification on their Form W-9 decides whether they get a 1099.');
if(w==='employee')return v('','Answer','Use Form W-2, not a 1099','Wages paid to employees go on Form W-2 through payroll, not on a 1099.');
if(w==='foreign')return v('','Answer','Usually no 1099, but check Form 1042-S','Foreign persons who give you a Form W-8 generally don\\'t receive a 1099. Some U.S.-source payments to foreign persons need withholding and Form 1042-S instead. This one is worth a quick conversation.',['Keep the signed Form W-8 on file.','Book a call if the work was performed in the U.S. or you\\'re unsure.']);
if(w==='exempt')return v('','Answer','Generally no 1099','Payments to tax-exempt organizations and government agencies generally aren\\'t reported on Form 1099-NEC or 1099-MISC.');
if(!t)return v('','Next','Now: what was it for?','Different payments go on different forms, with different thresholds.');
if(t==='goods')return v('','Answer','No 1099 for goods','Payments for merchandise, freight, storage, telephone and similar items aren\\'t reportable. If a bill mixes services and parts, only the services portion counts.');
if(t==='rent_agent')return v('','Answer','No 1099 from you','Rent paid to a real estate agent or property manager isn\\'t reported by you. The agent or manager reports the rent paid over to the property owner.');
if(w==='corp'&&['attorney_fees','attorney_proceeds','medical'].indexOf(t)<0)return v('','Answer','Generally no 1099 for corporations','Payments to C and S corporations (including LLCs taxed as corporations) are generally exempt. The big exceptions are attorneys and medical providers, who get a 1099 even if incorporated.',['Keep their Form W-9 on file showing the corporate classification.']);
var r=M[t],form=r[0],line=r[1],th=r[2],code=r[3];
if(bw.checked)return v('yes','Answer','Yes: file Form '+form,'Because federal income tax was withheld, you file regardless of the amount. Report it as: '+line+', with the tax withheld in box 4.',[due(code),'Deposit the withheld tax with the IRS and keep the payee\\'s records.','E-file through the IRS IRIS system or a provider such as QuickBooks; e-filing is required if you file 10 or more information returns in total.']);
if(!amt.value)return v('','Almost there','Form '+form+' if you paid '+fmt(th)+' or more','Enter the total you paid this payee in 2026 to see the answer. Threshold for this payment type: '+fmt(th)+'.');
if(a>=th)return v('yes','Answer','Yes: send Form '+form,'You paid '+fmt(a)+', which meets the '+fmt(th)+' threshold for 2026 payments. Report it as: '+line+(w==='corp'?'. The corporation exemption doesn\\'t apply to this payment type.':'.'),
['Get a signed Form W-9 now (legal name, tax ID, classification), before January.',due(code),'E-file through the IRS IRIS system or a provider such as QuickBooks; e-filing is required if you file 10 or more information returns in total.','Check whether your state needs its own copy.']);
return v('','Answer','Not required at this amount','You paid '+fmt(a)+', below the '+fmt(th)+' threshold for 2026 payments. Keep their W-9 on file anyway. If you pay them more before Dec. 31, run this again.');}
document.addEventListener('change',run);amt.addEventListener('input',run);run();})();
</script>""".replace("%NEC%", str(F["nec_threshold"])).replace("%MISC%", str(F["misc_threshold"])).replace("%ROY%", str(F["royalties"])).replace("%ATT%", str(F["attorney_proceeds"]))
    info = f"""<div class="tinfo"><article class="article">
<h2>How this checker decides</h2>
<p>For payments made in 2026, a Form 1099 depends on four things: whether the payment was for your business, how you paid, who you paid, and the total for the year.</p>
<ul><li><strong>$2,000 threshold.</strong> Nonemployee compensation, rents, medical payments and other income are reportable at $2,000 or more for 2026 payments (it was $600 for 2025). Royalties stay at $10 and gross proceeds paid to attorneys at $600.</li>
<li><strong>Card and app payments are excluded.</strong> Payments by credit or debit card or through a payment network are reported by the processor on Form 1099-K.</li>
<li><strong>Corporations are generally exempt,</strong> except for legal services and medical and health care payments.</li>
<li><strong>Backup withholding.</strong> If you withheld federal income tax because the payee didn't provide a tax ID, you file no matter the amount.</li></ul>
<p>Want the full walkthrough, including the QuickBooks steps? Read our <a href="/blog/form-1099-preparation-guide-2026/">Form 1099 preparation guide</a> or grab the <a href="/tools/w-9-request-email-template/">W-9 request email templates</a>.</p>
{sources_block("1099")}
</article></div>"""
    body = tool_header("1099 checker", "Do I need to send a 1099?", "Four quick questions for each payee. You'll see the form, the deadline and what to do next, based on the IRS rules for payments made in 2026.") + \
        f'<main><div class="tool">{form}{result}</div>{info}</main>' + js + cta("Want your 1099s handled?", "We collect W-9s, clean up vendor records in QuickBooks and file every 1099 on time. Book a 30-minute consultation.")
    return write("tools/do-i-need-to-send-a-1099", page(title + " | MFA", desc, url, body, clean_ld(tool_ld("Do I need to send a 1099? checker", url, desc))))


# ------------------------------------------------------------------ tool: W-9 email templates
def build_w9():
    url = BASE + "/tools/w-9-request-email-template/"
    title = "W-9 Request Email Templates for Vendors"
    desc = "Copy-ready W-9 request emails for new vendors, year-end 1099 prep and reminders. Personalize the names and deadline, then copy with one click."
    T = [
        ("new", "1. New vendor: before the first payment", "Subject: Quick request before we send your first payment\n\nHi {vendor},\n\nThanks for working with {biz}. Before we send your first payment, we need a completed and signed IRS Form W-9 for our records. It confirms your legal name, business type and taxpayer identification number so we can report payments correctly at year-end.\n\nYou can download the current form here: https://www.irs.gov/pub/irs-pdf/fw9.pdf\n\nPlease upload the completed form using {upload}. For your security, please don't email your Social Security number or EIN in the body of an email.\n\nCould you send it by {due}? Thank you!\n\nBest regards,\n{you}\n{biz}"),
        ("year", "2. Year-end: missing W-9 before 1099s", "Subject: W-9 needed for year-end tax forms\n\nHi {vendor},\n\nWe're preparing our year-end tax forms and don't have a Form W-9 on file for you. Because we paid you for services this year, we may need to issue you a Form 1099 in January, and the W-9 makes sure your name and tax ID are correct.\n\nThe current form is here: https://www.irs.gov/pub/irs-pdf/fw9.pdf\n\nPlease upload the signed form using {upload} by {due}. If your business name, address or tax classification has changed this year, the new form will update our records too.\n\nThank you,\n{you}\n{biz}"),
        ("remind", "3. Friendly reminder", "Subject: Reminder: Form W-9 still needed\n\nHi {vendor},\n\nJust a friendly reminder that we still need your signed Form W-9 (https://www.irs.gov/pub/irs-pdf/fw9.pdf). We need it to report this year's payments correctly, and without a tax ID we may be required to withhold federal income tax from future payments.\n\nPlease upload it using {upload} by {due}. If you've already sent it, thank you, and please ignore this note.\n\nBest,\n{you}\n{biz}"),
    ]
    tpls = "".join(f'<div class="tpl" data-id="{k}"><h3>{esc(h)}</h3><button class="copy" type="button">Copy</button><pre data-t="{esc(t)}"></pre></div>' for k, h, t in T)
    form = """<div class="tcard"><h2>Personalize</h2><p class="sub">Fill these in and every template below updates. Nothing you type leaves your browser.</p>
<div class="fld"><label for="f-vendor">Vendor's name</label><input type="text" id="f-vendor" placeholder="Alex"/></div>
<div class="fld"><label for="f-biz">Your business name</label><input type="text" id="f-biz" placeholder="Your Business LLC"/></div>
<div class="fld"><label for="f-you">Your name</label><input type="text" id="f-you" placeholder="Your name"/></div>
<div class="fld"><label for="f-due">Please send by</label><input type="text" id="f-due" placeholder="Friday, Dec. 11"/></div>
<div class="fld"><label for="f-upload">How they should send it</label><input type="text" id="f-upload" placeholder="our secure upload link"/><span class="hint">Use a secure upload or portal link rather than plain email, since the form contains a tax ID.</span></div></div>"""
    side = """<div class="tcard tres"><h2>Tips</h2><ol class="steps-out" style="margin-top:4px">
<li>Ask for the W-9 <b>before</b> the first payment; it's much harder in January.</li>
<li>Check that the name and tax ID match, and note the tax classification (box 3).</li>
<li>Store W-9s securely, outside your inbox, and re-request when a vendor's name, address or entity type changes.</li>
<li>Not sure who needs a 1099? Use the <a href="/tools/do-i-need-to-send-a-1099/">1099 checker</a>.</li></ol>
<div class="acts"><a class="btn btn-gold" href="/book/" data-conv="book">Have MFA handle your 1099s</a></div>
<p class="muted">Educational information, not tax or legal advice.</p></div>"""
    js = """<script>
(function(){var ids=['vendor','biz','you','due','upload'],def={vendor:'[Vendor name]',biz:'[Your business]',you:'[Your name]',due:'[date]',upload:'[secure upload link]'};
var pres=[].slice.call(document.querySelectorAll('.tpl pre'));
function fill(){var v={};ids.forEach(function(k){var x=document.getElementById('f-'+k).value.trim();v[k]=x||def[k];});
pres.forEach(function(p){p.textContent=p.getAttribute('data-t').replace(/\\{(\\w+)\\}/g,function(m,k){return v[k]||m;});});}
ids.forEach(function(k){document.getElementById('f-'+k).addEventListener('input',fill);});fill();
[].slice.call(document.querySelectorAll('.tpl .copy')).forEach(function(b){b.addEventListener('click',function(){var t=b.parentNode.querySelector('pre').textContent;
var done=function(){b.textContent='Copied';b.classList.add('ok');setTimeout(function(){b.textContent='Copy';b.classList.remove('ok');},1800);};
if(navigator.clipboard&&window.isSecureContext)navigator.clipboard.writeText(t).then(done);else{var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(a);}});});})();
</script>"""
    info = f'<div class="tinfo"><article class="article"><h2>The templates</h2>{tpls}{sources_block("w9")}</article></div>'
    body = tool_header("W-9 templates", "W-9 request email templates", "Three copy-ready emails for collecting Form W-9 from vendors: before the first payment, at year-end, and as a reminder.") + \
        f'<main><div class="tool">{form}{side}</div>{info}</main>' + js + cta("Behind on W-9s and 1099s?", "We'll chase the missing W-9s, clean up your vendor list and file your 1099s. Book a 30-minute consultation.")
    return write("tools/w-9-request-email-template", page(title + " | MFA", desc, url, body, clean_ld(tool_ld("W-9 request email templates", url, desc))))


# ------------------------------------------------------------------ tool: break-even
def build_breakeven():
    url = BASE + "/tools/break-even-calculator/"
    title = "Break-Even Calculator for Small Businesses"
    desc = "Find your break-even point in sales and units from monthly fixed costs, price and variable cost. For product and service businesses, with a profit goal."
    form = """<div class="tcard"><h2>Your numbers</h2><p class="sub">Use monthly figures. Fixed costs stay the same however much you sell; variable costs rise with each sale.</p>
<div class="seg" role="group" aria-label="Business type"><button type="button" data-m="unit" aria-pressed="true">Per unit</button><button type="button" data-m="pct" aria-pressed="false">Service (% of sales)</button></div>
<div class="fld"><label for="fc">Monthly fixed costs</label><div class="money"><input type="number" id="fc" min="0" step="1" inputmode="decimal" placeholder="8,000"/></div><span class="hint">Rent, salaries, software, insurance, loan payments, your own pay</span></div>
<div class="fld u"><label for="pr">Price per unit or sale</label><div class="money"><input type="number" id="pr" min="0" step="0.01" inputmode="decimal" placeholder="120"/></div></div>
<div class="fld u"><label for="vc">Variable cost per unit or sale</label><div class="money"><input type="number" id="vc" min="0" step="0.01" inputmode="decimal" placeholder="45"/></div><span class="hint">Materials, packaging, shipping, card fees, commissions</span></div>
<div class="fld p" hidden><label for="vp">Variable costs as % of sales</label><input type="number" id="vp" min="0" max="99" step="0.1" inputmode="decimal" placeholder="30"/><span class="hint">Subcontractors, card fees, commissions, supplies</span></div>
<div class="fld"><label for="tp">Monthly profit goal (optional)</label><div class="money"><input type="number" id="tp" min="0" step="1" inputmode="decimal" placeholder="5,000"/></div></div></div>"""
    res = """<div class="tcard tres" aria-live="polite"><h2>Break-even</h2><p class="sub" id="bsub">Enter your numbers to see the result.</p>
<div class="kpis"><div class="kpi wide gold"><b id="k1">—</b><span id="k1l">Break-even sales per month</span></div>
<div class="kpi"><b id="k2">—</b><span id="k2l">Units per month</span></div><div class="kpi"><b id="k3">—</b><span>Contribution margin</span></div>
<div class="kpi wide"><b id="k4">—</b><span id="k4l">Sales needed for your profit goal</span></div></div>
<p class="muted" id="bnote">Break-even point = fixed costs ÷ (price − variable cost per unit).</p>
<div class="acts"><a class="btn btn-gold" href="/book/" data-conv="book">Get help with pricing &amp; budgets</a></div></div>"""
    js = """<script>
(function(){var mode='unit',g=function(i){var v=parseFloat(document.getElementById(i).value);return isNaN(v)?null:v;};
var $=function(i){return document.getElementById(i);},m0=function(n){return '$'+Math.ceil(n).toLocaleString('en-US');},n0=function(n){return Math.ceil(n).toLocaleString('en-US');};
function set(a,b,c,d){$('k1').textContent=a;$('k2').textContent=b;$('k3').textContent=c;$('k4').textContent=d;}
function run(){var fc=g('fc'),tp=g('tp')||0;if(fc===null){set('—','—','—','—');$('bsub').textContent='Enter your numbers to see the result.';return;}
if(mode==='unit'){var pr=g('pr'),vc=g('vc');if(pr===null||vc===null){set('—','—','—','—');return;}var cm=pr-vc;
if(cm<=0){set('Not reachable','—','$'+cm.toFixed(2),'—');$('bsub').textContent='Each sale costs more than it brings in. Raise the price or cut variable costs.';return;}
var u=fc/cm,ut=(fc+tp)/cm;set(m0(u*pr),n0(u),'$'+cm.toFixed(2)+' ('+Math.round(cm/pr*100)+'%)',tp?m0(ut*pr)+' · '+n0(ut)+' units':'—');
$('bsub').textContent='You cover your costs at about '+n0(u)+' sales a month.';}
else{var vp=g('vp');if(vp===null){set('—','—','—','—');return;}var r=1-vp/100;if(r<=0){set('Not reachable','—','0%','—');return;}
var s=fc/r;set(m0(s),'—',Math.round(r*100)+'% of sales',tp?m0((fc+tp)/r):'—');$('bsub').textContent='You cover your costs at about '+m0(s)+' in monthly sales.';}}
[].slice.call(document.querySelectorAll('.seg button')).forEach(function(b){b.addEventListener('click',function(){mode=b.getAttribute('data-m');
[].slice.call(document.querySelectorAll('.seg button')).forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
[].slice.call(document.querySelectorAll('.fld.u')).forEach(function(e){e.hidden=mode!=='unit';});[].slice.call(document.querySelectorAll('.fld.p')).forEach(function(e){e.hidden=mode==='unit';});
$('k2l').textContent=mode==='unit'?'Units per month':'Units (n/a)';$('bnote').textContent=mode==='unit'?'Break-even point = fixed costs ÷ (price − variable cost per unit).':'Break-even sales = fixed costs ÷ (1 − variable cost %).';run();});});
document.addEventListener('input',run);run();})();
</script>"""
    info = f"""<div class="tinfo"><article class="article"><h2>How to read your break-even point</h2>
<p>Your <strong>contribution margin</strong> is what each sale leaves over after its own costs. Divide your fixed costs by it and you get the number of sales that covers the month. Every sale after that is profit.</p>
<ul><li><strong>Below break-even?</strong> The levers are price, variable cost per sale, and fixed costs, in that order of speed.</li>
<li><strong>Include your own pay</strong> in fixed costs if you're a sole owner; otherwise "break-even" means working without pay.</li>
<li><strong>Use real numbers from your books.</strong> A month-end profit and loss statement shows your actual fixed and variable costs.</li></ul>
<p>Next: check your pricing with the <a href="/tools/profit-margin-calculator/">profit margin &amp; markup calculator</a>.</p>
{sources_block("breakeven")}</article></div>"""
    body = tool_header("Break-even calculator", "Break-even calculator", "How much you need to sell each month to cover your costs, and to reach the profit you want. For product and service businesses.") + \
        f'<main><div class="tool">{form}{res}</div>{info}</main>' + js + cta("Want numbers you can trust?", "Accurate monthly books make every calculation better. Book a 30-minute consultation about bookkeeping, budgeting or pricing.")
    return write("tools/break-even-calculator", page(title + " | MFA", desc, url, body, clean_ld(tool_ld("Break-even calculator", url, desc))))


# ------------------------------------------------------------------ tool: margin & markup
def build_margin():
    url = BASE + "/tools/profit-margin-calculator/"
    title = "Profit Margin & Markup Calculator"
    desc = "Calculate gross profit margin and markup from cost and price, or the selling price for a target margin or markup. Includes a margin vs. markup guide."
    form = """<div class="tcard"><h2>Your numbers</h2><p class="sub">Pick what you know.</p>
<div class="seg" role="group" aria-label="Mode"><button type="button" data-m="cp" aria-pressed="true">Cost + price</button><button type="button" data-m="cm" aria-pressed="false">Target margin</button><button type="button" data-m="ck" aria-pressed="false">Target markup</button></div>
<div class="fld"><label for="c">Cost per unit</label><div class="money"><input type="number" id="c" min="0" step="0.01" inputmode="decimal" placeholder="40"/></div></div>
<div class="fld m-cp"><label for="p">Selling price</label><div class="money"><input type="number" id="p" min="0" step="0.01" inputmode="decimal" placeholder="100"/></div></div>
<div class="fld m-cm" hidden><label for="tm">Target margin (%)</label><input type="number" id="tm" min="0" max="99.9" step="0.1" inputmode="decimal" placeholder="40"/></div>
<div class="fld m-ck" hidden><label for="tk">Target markup (%)</label><input type="number" id="tk" min="0" step="0.1" inputmode="decimal" placeholder="60"/></div></div>"""
    res = """<div class="tcard tres" aria-live="polite"><h2>Result</h2><p class="sub" id="msub">Enter your numbers.</p>
<div class="kpis"><div class="kpi gold"><b id="r1">—</b><span>Gross margin</span></div><div class="kpi"><b id="r2">—</b><span>Markup</span></div>
<div class="kpi"><b id="r3">—</b><span>Selling price</span></div><div class="kpi"><b id="r4">—</b><span>Profit per unit</span></div></div>
<p class="muted">Margin = profit ÷ price. Markup = profit ÷ cost. A 50% markup is only a 33% margin.</p>
<div class="acts"><a class="btn btn-gold" href="/book/" data-conv="book">Talk pricing with MFA</a></div></div>"""
    js = """<script>
(function(){var mode='cp',$=function(i){return document.getElementById(i);},g=function(i){var v=parseFloat($(i).value);return isNaN(v)?null:v;};
var d=function(n){return '$'+n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});},pc=function(n){return (Math.round(n*10)/10)+'%';};
function show(p,c){if(p<=0){return;}var pr=p-c;$('r1').textContent=pc(pr/p*100);$('r2').textContent=c>0?pc(pr/c*100):'—';$('r3').textContent=d(p);$('r4').textContent=d(pr);
$('msub').textContent=pr<0?'You lose money on each sale at this price.':'Each sale keeps '+d(pr)+' toward your fixed costs and profit.';}
function clear(){['r1','r2','r3','r4'].forEach(function(i){$(i).textContent='—';});$('msub').textContent='Enter your numbers.';}
function run(){var c=g('c');if(c===null)return clear();
if(mode==='cp'){var p=g('p');if(p===null)return clear();show(p,c);}
else if(mode==='cm'){var m=g('tm');if(m===null||m>=100)return clear();show(c/(1-m/100),c);}
else{var k=g('tk');if(k===null)return clear();show(c*(1+k/100),c);}}
[].slice.call(document.querySelectorAll('.seg button')).forEach(function(b){b.addEventListener('click',function(){mode=b.getAttribute('data-m');
[].slice.call(document.querySelectorAll('.seg button')).forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
['cp','cm','ck'].forEach(function(k){[].slice.call(document.querySelectorAll('.m-'+k)).forEach(function(e){e.hidden=k!==mode;});});run();});});
document.addEventListener('input',run);run();})();
</script>"""
    info = f"""<div class="tinfo"><article class="article"><h2>Margin vs. markup</h2>
<table class="tbl"><thead><tr><th>Markup</th><th>Equals this margin</th></tr></thead><tbody>
<tr><td>25%</td><td>20%</td></tr><tr><td>50%</td><td>33.3%</td></tr><tr><td>75%</td><td>42.9%</td></tr><tr><td>100%</td><td>50%</td></tr><tr><td>150%</td><td>60%</td></tr></tbody></table>
<p><strong>Margin</strong> is profit as a share of the selling price; <strong>markup</strong> is profit as a share of cost. Mixing them up is one of the most common pricing mistakes: pricing at a "50% markup" when you meant a 50% margin leaves you a third short.</p>
<p>Next: see how many sales cover your costs with the <a href="/tools/break-even-calculator/">break-even calculator</a>.</p>
<p class="factline">Calculated with standard formulas: margin = (price − cost) ÷ price; markup = (price − cost) ÷ cost. {esc(NOTE)}</p></article></div>"""
    body = tool_header("Margin calculator", "Profit margin & markup calculator", "Turn cost and price into margin and markup, or find the selling price for the margin you want.") + \
        f'<main><div class="tool">{form}{res}</div>{info}</main>' + js + cta("Not sure your prices cover your costs?", "We'll look at your margins with real numbers from your books. Book a 30-minute consultation.")
    return write("tools/profit-margin-calculator", page(title + " | MFA", desc, url, body, clean_ld(tool_ld("Profit margin and markup calculator", url, desc))))


if __name__ == "__main__":
    posts = B.load_posts()
    import build_calculators  # noqa: E402  (tax calculators + trackers; adds the "Tax calculators" hub group)
    build_calculators.register(GROUPS, TOOLS)
    urls = [build_hub(posts), build_1099(), build_w9(), build_breakeven(), build_margin()]
    import build_llc  # noqa: E402  (LLC formation pages share this file's helpers)
    urls += build_llc.build_all()
    urls += build_calculators.build_all()
    import build_deductible  # noqa: E402  (/tools/is-it-deductible/, data/deductions.json; Zain 2026-10-21)
    urls.append(build_deductible.build())
    import build_services  # noqa: E402  (/services/, moved off the home page 2026-10-20)
    urls.append(build_services.build())
    import build_shop  # noqa: E402  (/shop/, Gumroad overlay; Zain 2026-10-21)
    urls.append(build_shop.build())
    import build_cleanup  # noqa: E402  (/bookkeeping-cleanup/, quoted service with a quote-request form; Zain 2026-10-21)
    urls.append(build_cleanup.build())
    import build_book  # noqa: E402  (/book/, booking calendar moved off the home page; Zain 2026-10-23)
    urls.append(build_book.build())
    import build_intl  # noqa: E402  (/international-students/, 1040-NR / 8843 / FICA refund service; Zain 2026-10-24)
    urls.append(build_intl.build())
    import build_artists  # noqa: E402  (/artists/, taxes for artists & creatives; Zain 2026-10-25)
    urls.append(build_artists.build())
    import build_offers  # noqa: E402  (fixed-price services with pay-now checkout; Zain 2026-10-25 standing price approval)
    urls.extend(build_offers.build_all())
    urls.append(BASE + "/new-york-ny/")  # Site-owned landing page (build_landing.py); NJ pages are listed by build_blog.py
    (ROOT / "tools" / "site_pages.json").write_text(json.dumps({"updated": date.today().isoformat(), "urls": urls}, indent=1), encoding="utf-8")
    print("Built:\n  " + "\n  ".join(urls))
