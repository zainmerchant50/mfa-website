#!/usr/bin/env python3
"""Builds the MFA tax calculators and trackers (/tools/<slug>/). Site session owns this file.

Called from tools/build_resources.py (register() for the hub cards, build_all() for the pages).
Every tax figure is read at build time from data/tax-figures-2026.json and data/tax-calendar-2027.json
(each figure is {value, source_url, checked}) and embedded in the page as JSON (#calc-data).
The browser code (site/resources/calc.js) contains no tax numbers. 1099 thresholds come from the
FACTS["1099"] block in build_resources.py (same source as the 1099 checker page).
Customer-facing dates show the date only.
"""
import hashlib
import json
import re
from datetime import date
from pathlib import Path

import build_blog as B
from build_resources import (BASE, EXTRA_CSS, FACTS, NOTE, OG, SITE, clean_ld, cta, esc, svg, tool_header, tool_ld, write)

ROOT = Path(__file__).resolve().parent.parent
FIG = json.loads((ROOT / "data" / "tax-figures-2026.json").read_text(encoding="utf-8"))
CAL = json.loads((ROOT / "data" / "tax-calendar-2027.json").read_text(encoding="utf-8"))
JS_V = hashlib.md5((SITE / "resources" / "calc.js").read_bytes()).hexdigest()[:10]
CSS_V = hashlib.md5((SITE / "resources" / "calc.css").read_bytes()).hexdigest()[:10]
CALC_CSS = f'<link rel="stylesheet" href="/resources/calc.css?v={CSS_V}"/>'

TITLES = {
    "https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-and-medicare-taxes": "IRS: Self-employment tax (Social Security and Medicare taxes)",
    "https://www.irs.gov/pub/irs-pdf/f1040es.pdf": "IRS: Form 1040-ES, Estimated Tax for Individuals (2026)",
    "https://www.ssa.gov/oact/cola/cbb.html": "Social Security Administration: Contribution and benefit base",
    "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf": "IRS Rev. Proc. 2025-32: 2026 inflation-adjusted tax figures",
    "https://www.nj.gov/treasury/taxation/pdf/current/1040esi.pdf": "NJ Division of Taxation: NJ-1040-ES instructions",
    "https://www.tax.ny.gov/pdf/2026/inc/it2105i_2026.pdf": "NY Tax Department: IT-2105 estimated tax instructions (2026)",
    "https://www.tax.ny.gov/pdf/current_forms/it/it2105i.pdf": "NY Tax Department: IT-2105 estimated tax instructions",
    "https://www.irs.gov/tax-professionals/standard-mileage-rates": "IRS: Standard mileage rates",
    "https://www.irs.gov/businesses/small-businesses-self-employed/simplified-option-for-home-office-deduction": "IRS: Simplified option for the home office deduction",
    "https://mfa-advisory.com/blog/2027-tax-calendar/": "MFA Insights: 2027 tax calendar",
    "https://www.irs.gov/pub/irs-dft/p509--dft.pdf": "IRS: Publication 509 (2027 draft), Tax Calendars",
    "https://www.nj.gov/treasury/taxation/njit20.shtml": "NJ Division of Taxation: Income tax filing",
    "https://www.tax.ny.gov/forms/current-forms/it/it370i.htm": "NY Tax Department: Form IT-370 instructions",
    "https://www.tax.ny.gov/bus/ptet/": "NY Tax Department: Pass-through entity tax",
    "https://www.nj.gov/treasury/taxation/pdf/current/part/1065i.pdf": "NJ Division of Taxation: NJ-1065 instructions",
    "https://www.tax.ny.gov/help/calendar/2026.htm": "NY Tax Department: Tax calendar",
    "https://www.irs.gov/charities-non-profits/annual-exempt-organization-return-due-date": "IRS: Annual exempt organization return due date",
    "https://www.nj.gov/treasury/taxation/su_12.shtml": "NJ Division of Taxation: Sales and use tax filing",
    "https://www.tax.ny.gov/pubs_and_bulls/tg_bulletins/st/filing_requirements_for_sales_and_use_tax_returns.htm": "NY Tax Department: Sales tax filing requirements",
}


# ------------------------------------------------------------------ formatting + data access
def usd(x, cents=False):
    return f"${x:,.2f}" if (cents or x != int(x)) else f"${int(x):,}"


def pc(x):
    return f"{x * 100:g}%"


def day(ts):
    """Date only, e.g. 'October 20, 2026' (drops any time part of a checked stamp)."""
    return date.fromisoformat(ts[:10]).strftime("%B %-d, %Y")


class Facts:
    """Reads figures from the data files and remembers which ones a page used (for its sources + checked date)."""

    def __init__(self):
        self.used = []

    def node(self, *path, src=None):
        n = (src or FIG)
        for p in path:
            n = n[p]
        self.used.append(n)
        return n

    def get(self, *path):
        return self.node(*path)["value"]

    def checked(self, extra=()):
        stamps = [n["checked"][:10] for n in self.used] + [e[:10] for e in extra]
        return min(stamps)

    def sources(self, extra=()):
        seen, out = set(), []
        for n in self.used:
            u = n["source_url"]
            if u not in seen:
                seen.add(u)
                out.append((TITLES.get(u, u), u))
        for t, u in extra:
            if u not in seen:
                seen.add(u)
                out.append((t, u))
        return out


def fed_bundle(f):
    g = lambda *p: f.get("federal", *p)
    d = {
        "se_rate": g("self_employment_tax_rate"), "ss_rate": g("social_security_rate_se"), "med_rate": g("medicare_rate_se"),
        "factor": g("net_earnings_factor"), "se_min": g("se_tax_minimum_net_earnings"), "half_share": g("se_tax_deduction_share"),
        "wage_base": g("social_security_wage_base"), "addl_rate": g("additional_medicare_rate"), "addl_thr": g("additional_medicare_thresholds"),
        "brackets": g("brackets"), "std": g("standard_deduction"), "due": g("estimated_tax_due_dates_2026"),
        "est_threshold": g("estimated_tax_threshold"), "safe": g("estimated_tax_safe_harbor"),
    }
    assert abs(d["ss_rate"] + d["med_rate"] - d["se_rate"]) < 1e-9, "SE rate parts don't add up"
    return d


def state_bundle(f, ny=True):
    nj = {"brackets": f.get("new_jersey", "brackets"), "threshold": f.get("new_jersey", "estimated_tax_threshold"),
          "due_note": "New Jersey: " + f.node("new_jersey", "estimated_tax_due_dates_2026")["note"].rstrip(".") + "."}
    nyd = {"brackets": f.get("new_york_state", "brackets"), "std": f.get("new_york_state", "standard_deduction"),
           "threshold": f.get("new_york_state", "estimated_tax_threshold")}
    m = re.search(r"Simplified estimating schedule:.*", f.node("new_york_state", "brackets")["note"])
    nyd["note"] = "New York figures are an estimate. " + (m.group(0).replace("Simplified estimating schedule:", "This uses a simplified estimating schedule:") if m else "")
    nyc = {"brackets": f.get("new_york_city", "brackets")}
    # State due dates must match federal ones: the page shows one date column.
    fed_due = FIG["federal"]["estimated_tax_due_dates_2026"]["value"]
    assert fed_due == FIG["new_jersey"]["estimated_tax_due_dates_2026"]["value"] == FIG["new_york_state"]["estimated_tax_due_dates_2026"]["value"], \
        "Federal/NJ/NY 2026 estimated tax dates differ: the quarterly page needs separate date columns"
    return nj, nyd, nyc


# ------------------------------------------------------------------ html helpers
def money(i, label, hint="", ph="", val="", tag=""):
    h = f'<span class="hint">{hint}</span>' if hint else ""
    t = f'<span class="tag-a">{tag}</span>' if tag else ""
    return (f'<div class="fld"><label for="{i}">{label}{t}</label><div class="money"><input type="number" id="{i}" min="0" step="any" '
            f'inputmode="decimal" placeholder="{ph}" value="{val}"/></div>{h}</div>')


def numf(i, label, hint="", ph="", val="", wid="", hidden=False):
    h = f'<span class="hint">{hint}</span>' if hint else ""
    return (f'<div class="fld"{f" id={chr(34)}{wid}{chr(34)}" if wid else ""}{" hidden" if hidden else ""}><label for="{i}">{label}</label>'
            f'<input type="number" id="{i}" min="0" step="any" inputmode="decimal" placeholder="{ph}" value="{val}"/>{h}</div>')


def select(i, label, opts, hint="", val=None):
    o = "".join(f'<option value="{v}"{" selected" if v == val else ""}>{t}</option>' for v, t in opts)
    h = f'<span class="hint">{hint}</span>' if hint else ""
    return f'<div class="fld"><label for="{i}">{label}</label><select id="{i}">{o}</select>{h}</div>'


STATUS = [("single", "Single"), ("married_joint", "Married filing jointly"), ("married_separate", "Married filing separately"), ("head_of_household", "Head of household")]
STATE_EST = [("NJ", "New Jersey"), ("NY", "New York State"), ("NYC", "New York City resident (state + city)"), ("OTHER", "Another state (enter a flat rate)")]
fgh = lambda t: f'<p class="fgh">{t}</p>'


def kpi(i, label, cls=""):
    return f'<div class="kpi {cls}"><b id="{i}">—</b><span>{label}</span></div>'


def result_card(title, kpis, extra="", cta_label="Talk to MFA about your taxes"):
    return (f'<div class="tcard tres" aria-live="polite"><h2>{title}</h2><p class="sub" id="rsub">Enter your numbers to see the result.</p>{extra}'
            f'<div class="kpis">{kpis}</div><p class="muted" id="rnote"></p>'
            f'<div class="acts"><a class="btn btn-gold" href="/book/" data-conv="book">{cta_label}</a></div>'
            f'<p class="muted">General information, not tax advice.</p></div>')


def math_card(sub="Every step uses the 2026 figures listed under Sources. Nothing is rounded until the end.", head=False, tid="math", title="The math, step by step"):
    th = '<thead><tr><th>Step</th><th class="num">Amount</th></tr></thead>' if not head else head
    return (f'<section class="tcard" aria-label="Breakdown"><h2>{title}</h2><p class="sub">{sub}</p>'
            f'<table class="tbl ctbl">{th}<tbody id="{tid}"></tbody></table></section>')


def factline(f, extra=()):
    return f'<p class="factline">Facts checked {day(f.checked(extra))} · 2026 tax year</p>'


def sources_block(f, extra=(), extra_note="", extra_checked=()):
    lis = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in f.sources(extra))
    return (f'<section class="sources"><h2>Sources</h2><ul>{lis}</ul>'
            f'<p class="disclaimer">Facts checked against the sources above as of {day(f.checked(extra_checked))}. {extra_note}{NOTE}</p></section>')


PAGES = {}  # slug -> dict(title, card_desc, icon, group, kw, eyebrow)


def also_useful(slug):
    rel = RELATED[slug]
    items = "".join(
        f'<li><a href="/tools/{s}/"><span class="m">{esc(PAGES[s]["kind"])}</span><b>{esc(PAGES[s]["name"])}</b><span class="d">{esc(PAGES[s]["card_desc"])}</span></a></li>' for s in rel
        if s in PAGES)
    return f'<h2>Also useful</h2><ul class="alist">{items}</ul>'


def data_script(d):
    return '<script type="application/json" id="calc-data">' + json.dumps(d, separators=(",", ":")).replace("</", "<\\/") + "</script>"


def build_page(slug, title, desc, eyebrow, h1, dek, grid, below, info, data, init, f, cta_head, cta_text, extra_src=(), extra_note="", extra_checked=(), callout=True, llc=False):
    url = f"{BASE}/tools/{slug}/"
    data = dict(data, page_url=url)
    ld = json.dumps(clean_ld(tool_ld(PAGES[slug]["name"], url, desc)))
    head = B.head(f"{title} | MFA", desc, url, OG, EXTRA_CSS + CALC_CSS + f'<script type="application/ld+json">{ld}</script>')
    body = (tool_header(eyebrow, h1, dek) +
            f'<main><div class="tool">{grid}</div><div class="tstack">{below}</div>'
            f'<div class="tinfo"><article class="article">{info}{also_useful(slug)}'
            f'{"<!-- product-callout:" + slug + " -->" if callout else ""}'
            f'{sources_block(f, extra_src, extra_note, extra_checked)}</article></div></main>' +
            data_script(data) + f'<script src="/resources/calc.js?v={JS_V}"></script><script>MFA.init("{init}");</script>' +
            cta(cta_head, cta_text))
    html = f'{head}\n<body>{B.nav("res")}\n{body}\n{B.FOOT}</body></html>'
    return write(f"tools/{slug}", html)


def spaced(*parts):
    return "".join(parts)


def pad_cards(*cards):
    return "".join(cards)


# ------------------------------------------------------------------ related links + registry
def reg(slug, name, kind, card_desc, icon, group, kw, badge="New"):
    PAGES[slug] = {"name": name, "kind": kind, "card_desc": card_desc, "icon": icon, "group": group, "kw": kw, "badge": badge}


reg("quarterly-estimated-tax-calculator", "Quarterly estimated tax calculator", "Calculator",
    "Your four 2026 estimated payments and their due dates, federal and NJ/NY, with the amount that avoids an underpayment penalty.", "calc", "taxcalcs",
    "estimated tax quarterly 1040-es safe harbor self employed")
reg("1099-tax-calculator", "1099 tax calculator", "Calculator",
    "Estimate self-employment tax, federal income tax and NJ/NY tax on freelance income, and how much of each payment to set aside.", "calc", "taxcalcs",
    "1099 self employment tax freelancer independent contractor set aside")
reg("s-corp-tax-savings-calculator", "S corp tax savings calculator", "Calculator",
    "See whether an S corp election could save tax once payroll taxes and extra costs are counted.", "scale", "taxcalcs",
    "s corp llc election salary reasonable compensation payroll tax savings")
reg("paycheck-tax-calculator", "Paycheck tax calculator", "Calculator",
    "W-2 take-home pay after federal, Social Security, Medicare and NJ or NY tax, per paycheck.", "calc", "taxcalcs",
    "paycheck take home pay w-2 salary withholding fica")
reg("home-office-deduction-calculator", "Home office deduction calculator", "Calculator",
    "Compare the simplified ($5 per sq ft) and regular home office methods.", "home", "taxcalcs", "home office deduction simplified regular method 8829")
reg("mileage-deduction-calculator", "Mileage deduction calculator", "Calculator",
    "Business miles times the 2026 IRS standard rates, including the July rate change.", "car", "taxcalcs", "mileage standard rate deduction business miles")
reg("1099-contractor-tracker", "1099 contractor tracker", "Tracker",
    "Log vendors and payments, see who needs a 1099-NEC at the 2026 threshold, and export to CSV. Stays in your browser.", "list", "checkers",
    "1099 tracker contractor vendor w-9 payments log nec")
reg("tax-deadlines-2027", "2027 business tax deadlines by entity", "Calendar",
    "Every 2027 federal, NJ and NY deadline for your entity type, with add-to-calendar files.", "cal", "calendars",
    "tax deadlines 2027 calendar entity s corp partnership c corp employer nonprofit sales tax ics")

RELATED = {
    "quarterly-estimated-tax-calculator": ["1099-tax-calculator", "tax-deadlines-2027", "s-corp-tax-savings-calculator"],
    "1099-tax-calculator": ["quarterly-estimated-tax-calculator", "mileage-deduction-calculator", "home-office-deduction-calculator"],
    "s-corp-tax-savings-calculator": ["1099-tax-calculator", "quarterly-estimated-tax-calculator", "paycheck-tax-calculator"],
    "paycheck-tax-calculator": ["s-corp-tax-savings-calculator", "1099-tax-calculator", "tax-deadlines-2027"],
    "home-office-deduction-calculator": ["mileage-deduction-calculator", "1099-tax-calculator", "quarterly-estimated-tax-calculator"],
    "mileage-deduction-calculator": ["home-office-deduction-calculator", "1099-tax-calculator", "quarterly-estimated-tax-calculator"],
    "1099-contractor-tracker": ["tax-deadlines-2027", "1099-tax-calculator", "quarterly-estimated-tax-calculator"],
    "tax-deadlines-2027": ["quarterly-estimated-tax-calculator", "1099-contractor-tracker", "s-corp-tax-savings-calculator"],
}

SUPERSEDED = ["Self-employment (1099) tax calculator", "Quarterly estimated tax calculator", "S corp vs LLC savings estimator",
              "Home office deduction calculator", "Mileage deduction calculator", "Business tax deadlines by entity"]


def register(groups, tools):
    """Called by build_resources before the hub is built: adds the 'Tax calculators' group and the cards, and drops the
    'coming soon' placeholders these tools replace."""
    tools[:] = [t for t in tools if t[1] not in SUPERSEDED]
    gi = [g[0] for g in groups].index("calculators") + 1
    groups.insert(gi, ("taxcalcs", "Tax calculators", "2026 estimates for self-employed people, owners and employees, built on checked IRS, NJ and NY figures."))
    for slug, p in PAGES.items():
        tools.append((p["group"], p["name"] if slug != "tax-deadlines-2027" else "2027 business tax deadlines by entity", p["card_desc"], f"/tools/{slug}/", p["icon"], p["kw"], p["badge"]))


# ------------------------------------------------------------------ 1. quarterly
def build_quarterly():
    slug = "quarterly-estimated-tax-calculator"
    f = Facts()
    fed = fed_bundle(f)
    nj, nyd, nyc = state_bundle(f)
    S = fed["safe"]
    due = fed["due"]
    grid = (
        '<div class="tcard"><h2>Your 2026 numbers</h2><p class="sub">Estimates for the 2026 tax year. Nothing you type leaves your browser.</p>' + factline(f) +
        fgh("Income") +
        money("q-net", "Expected net self-employment profit", "After business expenses (income minus expenses)", "85,000") +
        '<div class="fgrid">' + money("q-w2", "Your W-2 wages", "Optional. They use up part of the Social Security wage base", "0") +
        money("q-other", "Other taxable income", "Optional. Interest, rent, a spouse's wages", "0") + "</div>" +
        fgh("Filing status and state") +
        select("q-status", "Filing status", STATUS) + select("q-state", "State", STATE_EST, "Full-year resident assumed") +
        numf("q-flat", "Flat state tax rate (%)", "Applied to your adjusted gross income", "4", wid="q-flat-wrap", hidden=True) +
        money("q-stex", "State deductions and exemptions", "Optional. Reduces income taxed by the state", "0") +
        fgh("Withholding and payments made") +
        '<div class="fgrid">' + money("q-fedwh", "Federal tax withheld for 2026", "Optional. From W-2 pay", "0") + money("q-stwh", "State tax withheld for 2026", "Optional", "0") +
        money("q-paidf", "Federal estimated payments already made", "Optional", "0") + money("q-paids", "State estimated payments already made", "Optional", "0") + "</div>" +
        fgh("Safe harbor (optional)") +
        '<div class="fgrid">' + money("q-prior", "Last year's total federal tax", "From your 2025 Form 1040", "0") + money("q-prioragi", "Last year's AGI", "Decides 100% vs. 110%", "0") + "</div></div>")
    kp = (kpi("k-total", "Estimated 2026 tax (all taxes)", "wide gold") + kpi("k-fedq", "Federal, per quarter") + kpi("k-stq", "State, per quarter") +
          kpi("k-totq", "Total, per quarter", "wide") + kpi("k-safeq", "Federal safe-harbor minimum, per quarter", "wide"))
    res = result_card("Your estimate", kp, extra="", cta_label="Have MFA handle your estimates")
    res = res.replace('<p class="muted" id="rnote"></p>', '<ul class="steps-out" id="qnotes"></ul><p class="muted" id="left"></p><p class="muted" id="rnote"></p>')
    sched = ('<section class="tcard" aria-label="Payment schedule"><h2>Payment schedule</h2><p class="sub">Four equal payments on the 2026 due dates. The state column is the same date for New Jersey and New York.</p>'
             '<table class="tbl ctbl"><thead><tr><th>Due date</th><th class="num">Federal</th><th class="num">State</th><th class="num">Total</th></tr></thead><tbody id="dues"></tbody></table></section>')
    below = sched + '<section class="tcard safe" id="safe"></section>' + math_card()
    hi = S["high_income_agi_over"]
    info = f"""<h2>How this estimate works</h2>
<p>This calculator follows the 2026 Form 1040-ES worksheet in plain steps. It starts with self-employment tax, takes the deduction for half of it, applies the standard deduction and the 2026 tax brackets, then adds your state tax. The total is split into four payments.</p>
<ul><li><strong>Self-employment tax.</strong> {pc(fed["se_rate"])} ({pc(fed["ss_rate"])} Social Security + {pc(fed["med_rate"])} Medicare) on {pc(fed["factor"])} of your net profit. Social Security stops at the {usd(fed["wage_base"])} wage base, and your W-2 wages use that up first.</li>
<li><strong>Additional Medicare Tax.</strong> {pc(fed["addl_rate"])} on wages plus self-employment earnings above {usd(fed["addl_thr"]["single"])} ({usd(fed["addl_thr"]["married_joint"])} if married filing jointly).</li>
<li><strong>Half of self-employment tax is deductible.</strong> It lowers your income for income tax, not your self-employment tax.</li>
<li><strong>State.</strong> New Jersey and New York use the 2026 rate schedules in their estimated tax instructions. For another state, enter a flat rate. New York City residents add the city tax.</li></ul>
<h2>Due dates for 2026 estimated payments</h2>
<p>Federal, New Jersey and New York all use the same four dates: {", ".join(day(d) for d in due[:3])} and {day(due[3])}. Estimated payments are generally required if you expect to owe {usd(fed["est_threshold"])} or more after withholding. New Jersey's threshold is {usd(nj["threshold"])} and New York's is {usd(nyd["threshold"])}. {esc(nj["due_note"])}</p>
<h2>Safe harbor in one paragraph</h2>
<p>You avoid the underpayment penalty if your withholding and estimated payments total at least {pc(S["current_year_pct"])} of this year's tax or {pc(S["prior_year_pct"])} of last year's tax, whichever is smaller. The prior-year rule rises to {pc(S["prior_year_pct_high_income"])} if last year's AGI was over {usd(hi)} ({usd(S["high_income_agi_over_mfs"])} if married filing separately). The calculator shows both so you can pick.</p>
<h2>What this estimate leaves out</h2>
<ul><li>The qualified business income (QBI) deduction, which can lower your federal tax. Leaving it out makes the estimate higher, not lower.</li>
<li>Itemized deductions, tax credits, and other adjustments such as retirement contributions or the self-employed health insurance deduction.</li>
<li>Self-employment income of a spouse. Married couples should enter only their own profit and wages for self-employment tax, and add a spouse's other income in the other income box.</li>
<li>{esc(nyd["note"])}</li></ul>
<p>Planning for 2027? The 2027 estimated payment dates are on the <a href="/tools/tax-deadlines-2027/">2027 deadlines page</a>. We will update this calculator when the 2027 figures are final.</p>"""
    data = {"fed": fed, "nj": nj, "ny": nyd, "nyc": nyc}
    return build_page(slug, "Quarterly Estimated Tax Calculator 2026: Fed, NJ & NY",
                      "Estimate your four 2026 quarterly tax payments: self-employment tax, federal income tax and NJ or NY tax, with due dates and the penalty-safe amount.",
                      "Quarterly estimated tax", "Quarterly estimated tax calculator",
                      "Enter your expected 2026 profit and see what to pay on each due date, with the math shown, federal and state.",
                      grid + res, below, info, data, "quarterly", f, "Not sure what to pay?", "We calculate your estimates, track what you have paid and keep you ahead of every due date. Book a 30-minute consultation.")


# ------------------------------------------------------------------ 2. 1099 tax calculator
def build_1099calc():
    slug = "1099-tax-calculator"
    f = Facts()
    fed = fed_bundle(f)
    nj, nyd, nyc = state_bundle(f)
    grid = (
        '<div class="tcard"><h2>Your 1099 income</h2><p class="sub">For the 2026 tax year. Nothing you type leaves your browser.</p>' + factline(f) +
        money("t-inc", "1099 income for the year", "Total paid to you by clients (1099-NEC, 1099-K or not reported)", "90,000") +
        money("t-exp", "Business expenses", "Software, supplies, mileage, insurance, a home office", "12,000") +
        select("t-status", "Filing status", STATUS) + select("t-state", "State", STATE_EST, "Full-year resident assumed") +
        numf("t-flat", "Flat state tax rate (%)", "Applied to your adjusted gross income", "4", wid="t-flat-wrap", hidden=True) + "</div>")
    kp = (kpi("k-set", "Set aside from every payment", "wide gold") + kpi("k-total", "Total estimated tax") + kpi("k-eff", "Effective rate on profit") +
          kpi("k-net", "Net profit") + kpi("k-se", "Self-employment tax") + kpi("k-inc", "Federal + state income tax", "wide"))
    res = result_card("Your estimate", kp, cta_label="Get help with your 1099 taxes")
    below = math_card()
    info = f"""<h2>What you owe on 1099 income</h2>
<p>Income reported on a 1099 has no tax taken out. You owe three things on the profit, which is income minus business expenses:</p>
<ul><li><strong>Self-employment tax of {pc(fed["se_rate"])}.</strong> This covers Social Security and Medicare, both the employee and employer halves, on {pc(fed["factor"])} of profit.</li>
<li><strong>Federal income tax.</strong> Figured with the 2026 brackets after the standard deduction and the deduction for half of your self-employment tax.</li>
<li><strong>State income tax.</strong> New Jersey and New York use the 2026 rate schedules; for another state, enter its flat rate.</li></ul>
<h2>How to use the "set aside" percentage</h2>
<p>The set-aside figure is your total estimated tax divided by your 1099 income. Move that share of every client payment into a separate savings account, and use it to make quarterly estimated payments. Try the <a href="/tools/quarterly-estimated-tax-calculator/">quarterly estimated tax calculator</a> for the payment dates and the amount that avoids an underpayment penalty.</p>
<h2>What this estimate leaves out</h2>
<ul><li>The qualified business income (QBI) deduction, itemized deductions and tax credits. They can lower your tax, so the estimate errs high.</li>
<li>Other income such as a W-2 job or a spouse's wages. Those change your bracket and the Social Security wage base. Use the quarterly calculator if you have them.</li>
<li>{esc(nyd["note"])}</li></ul>"""
    return build_page(slug, "1099 Tax Calculator 2026: Self-Employment, NJ & NY",
                      "Estimate the self-employment tax, federal income tax and NJ or NY tax on your 1099 income, plus the share of every payment to set aside.",
                      "1099 tax calculator", "1099 tax calculator",
                      "Enter your 1099 income and expenses to see your tax bill and the share of every payment to set aside, with the math shown.",
                      grid + res, below, info, {"fed": fed, "nj": nj, "ny": nyd, "nyc": nyc}, "t1099", f, "Want a plan for your 1099 income?",
                      "We prepare self-employed returns, set up quarterly payments and find the deductions you are missing. Book a 30-minute consultation.")


# ------------------------------------------------------------------ 3. S corp
def build_scorp():
    slug = "s-corp-tax-savings-calculator"
    f = Facts()
    fed = fed_bundle(f)
    notes = {
        "NJ": "New Jersey has separate S corporation rules, filings and state-level fees, so confirm your New Jersey S status when you elect federally. State income tax differences are not included here.",
        "NY": "New York has its own S corporation election and filing requirements, and New York City has business taxes that can apply to S corporations. State income tax differences are not included here.",
        "OTHER": "State rules for S corporations vary. Check your state's election, fees and tax treatment. State income tax differences are not included here.",
    }
    grid = (
        '<div class="tcard"><h2>Your business</h2><p class="sub">Compare the two ways of being paid. Nothing you type leaves your browser.</p>' + factline(f) +
        money("s-profit", "Net profit before paying yourself", "What the business earns after expenses, before any owner salary", "120,000") +
        money("s-salary", "Salary you would pay yourself", "Must be reasonable for the work you do", "60,000") +
        select("s-state", "State", [("NJ", "New Jersey"), ("NY", "New York"), ("OTHER", "Another state")]) +
        '<p class="hint" id="s-statenote" style="margin:-8px 0 18px;font-size:.8rem;color:var(--muted)"></p>'
        '<div class="assump"><p><strong>Assumptions you can change.</strong> These are examples, not tax figures. Replace them with real quotes from your payroll provider and tax preparer.</p>' +
        money("s-cost1", "Payroll service and filings, per year", "", "600", "600", "Assumption") +
        money("s-cost2", "Extra tax return prep and bookkeeping, per year", "An S corporation files its own return (Form 1120-S)", "1500", "1500", "Assumption") + "</div></div>")
    verdict = '<div class="verdict" id="verdict"><span class="vk">Start here</span><h3>Enter your profit and salary.</h3><p>We compare self-employment tax as an LLC with payroll taxes as an S corporation.</p></div>'
    kp = (kpi("k-save", "Annual savings after costs", "wide gold") + kpi("k-llc", "Self-employment tax as an LLC") + kpi("k-scorp", "Payroll taxes as S corp") + kpi("k-be", "Break-even profit", "wide"))
    res = result_card("Is an S corp worth it?", kp, extra=verdict, cta_label="Ask MFA about an S corp election")
    below = math_card(sub="Self-employment tax on the whole profit versus payroll taxes on the salary. Income tax and the QBI deduction are not part of this comparison.")
    info = f"""<h2>What this compares</h2>
<p>An LLC owner who is taxed as a sole proprietor pays self-employment tax ({pc(fed["se_rate"])} on {pc(fed["factor"])} of profit) on all of the profit. An S corporation owner who works in the business is paid a salary and the company pays payroll taxes on that salary only (the same {pc(fed["se_rate"])}, split between employee and employer, on the full salary). Profit left over as distributions is not subject to payroll or self-employment tax. The savings come from that difference, minus the extra costs of running a corporation.</p>
<p><strong>Not included:</strong> federal and state income tax differences, the qualified business income (QBI) deduction, and the deduction effects of half of self-employment tax versus the employer payroll tax. Those can move the answer in either direction, so use this as a first filter, not a final answer.</p>
<h2>What else to weigh</h2>
<ul><li><strong>Reasonable compensation.</strong> The IRS expects an owner-employee to be paid a reasonable salary before taking distributions. A very low salary is a common audit trigger. Base it on what the role would cost to hire.</li>
<li><strong>Form 2553 timing.</strong> The S corporation election is made on Form 2553. For 2027, calendar-year entities have until March 15, 2027; check the <a href="/tools/tax-deadlines-2027/">2027 deadlines</a> for the date for your entity.</li>
<li><strong>Payroll obligations.</strong> You must run payroll, make payroll tax deposits and file quarterly and year-end payroll returns, and the state may add its own payroll registrations.</li>
<li><strong>Extra filings and fees.</strong> A separate corporate return (Form 1120-S), K-1s, and state-level fees or taxes for S corporations.</li>
<li><strong>Retirement, health insurance and loans.</strong> Salary affects retirement contribution limits, and owner health insurance has its own S corporation rules.</li>
<li><strong>Formation first.</strong> You need a corporation or an LLC before electing S status. See our <a href="/llc-formation/">LLC formation service</a> for any state.</li></ul>"""
    d = {"fed": fed, "notes": notes}
    return build_page(slug, "S Corp Tax Savings Calculator: Is an S Corp Worth It?",
                      "Compare self-employment tax as an LLC with payroll taxes as an S corporation. See annual savings after costs and the break-even profit.",
                      "S corp calculator", "S corp tax savings calculator",
                      "Is an S corp worth it? Compare self-employment tax as an LLC with payroll taxes on a reasonable salary, after the extra costs.",
                      grid + res, below, info, d, "scorp", f, "Thinking about an S corp election?",
                      "We run the numbers with your real income, set up payroll and handle the election and filings. Book a 30-minute consultation.")


# ------------------------------------------------------------------ 5. paycheck
def build_paycheck():
    slug = "paycheck-tax-calculator"
    f = Facts()
    fed = fed_bundle(f)
    nj, nyd, nyc = state_bundle(f)
    freq = [("52", "Weekly (52)"), ("26", "Every two weeks (26)"), ("24", "Twice a month (24)"), ("12", "Monthly (12)")]
    grid = (
        '<div class="tcard"><h2>Your pay</h2><p class="sub">An annualized estimate for the 2026 tax year. Nothing you type leaves your browser.</p>' + factline(f) +
        money("p-gross", "Annual salary before taxes", "", "95,000") + select("p-freq", "Pay frequency", freq, val="26") +
        select("p-status", "Filing status", STATUS) +
        select("p-state", "State", [("NJ", "New Jersey"), ("NY", "New York State"), ("NYC", "New York City resident (state + city)"), ("NONE", "Other state (state tax not included)")]) +
        fgh("Pre-tax deductions, per paycheck") +
        money("p-k401", "401(k) or traditional retirement", "Lowers federal income tax. Social Security and Medicare still apply", "0") +
        money("p-s125", "Health insurance and other pre-tax benefits (Section 125)", "Lowers income tax and Social Security and Medicare", "0") + "</div>")
    kp = kpi("k-net", "Take-home per paycheck", "wide gold") + kpi("k-gross", "Gross per paycheck") + kpi("k-tax", "Taxes per paycheck") + kpi("k-rate", "Taxes as % of gross", "wide")
    res = result_card("Your take-home pay", kp, cta_label="Talk to MFA about your taxes")
    head = '<thead><tr><th>Item</th><th class="num">Per paycheck</th><th class="num">Per year</th></tr></thead>'
    below = math_card(sub="Annual amounts divided by your number of paychecks. This is the tax on your salary for the year, not the amount your employer withholds under your Form W-4.", head=head, tid="pmath")
    info = f"""<h2>How take-home pay is figured</h2>
<ul><li><strong>Federal income tax.</strong> Salary minus pre-tax retirement and Section 125 deductions and the {usd(fed["std"]["single"])} single ({usd(fed["std"]["married_joint"])} joint) standard deduction, then the 2026 brackets.</li>
<li><strong>Social Security and Medicare (FICA).</strong> {pc(fed["ss_rate"] / 2)} Social Security on wages up to {usd(fed["wage_base"])}, and {pc(fed["med_rate"] / 2)} Medicare on all wages, plus {pc(fed["addl_rate"])} Additional Medicare on wages over {usd(fed["addl_thr"]["single"])}. Your employer pays a matching amount that is not shown here.</li>
<li><strong>New Jersey.</strong> Rate schedule on wages less 401(k) and Section 125 health deductions, with no standard deduction. New Jersey excludes 401(k) deferrals but taxes 403(b) and 457 deferrals (<a href="https://www.nj.gov/treasury/taxation/njit5.shtml" target="_blank" rel="noopener">NJ Division of Taxation</a>). This estimate treats the amount entered as a 401(k).</li>
<li><strong>New York.</strong> Rate schedule on income after the NY standard deduction, with New York City tax added for city residents. {esc(nyd["note"])}</li></ul>
<h2>What this estimate leaves out</h2>
<ul><li>State payroll deductions such as NJ and NY disability and family leave contributions, and local taxes other than New York City.</li>
<li>Tax credits (such as child credits), itemized deductions, other income, and a second job or a working spouse.</li>
<li>Your actual W-4 withholding. Employers withhold using the IRS tables and your W-4, which can differ from the full-year tax shown here. Adjust your W-4 if you want a refund or balance due closer to zero.</li></ul>"""
    return build_page(slug, "Paycheck Tax Calculator 2026 (Federal, FICA, NJ & NY)",
                      "Estimate W-2 take-home pay per paycheck after federal income tax, Social Security, Medicare and New Jersey or New York tax.",
                      "Paycheck calculator", "Paycheck tax calculator",
                      "See your take-home pay per paycheck after federal tax, Social Security, Medicare and NJ or NY tax, with the math shown.",
                      grid + res, below, info, {"fed": fed, "nj": nj, "ny": nyd, "nyc": nyc}, "paycheck", f, "Want a second look at your taxes?",
                      "We review your withholding, find deductions and file your return. Book a 30-minute consultation.")


# ------------------------------------------------------------------ 6. home office
def build_home():
    slug = "home-office-deduction-calculator"
    f = Facts()
    h = {"rate": f.get("home_office_simplified", "rate_per_sq_ft"), "max_sqft": f.get("home_office_simplified", "max_sq_ft"),
         "max_deduction": f.get("home_office_simplified", "max_deduction"), "limit_note": f.get("home_office_simplified", "limit_note")}
    grid = (
        '<div class="tcard"><h2>Your home office</h2><p class="sub">For the 2026 tax year, full-year use. Nothing you type leaves your browser.</p>' + factline(f) +
        '<div class="fgrid">' + numf("h-home", "Total square feet of your home", "", "1,500") + numf("h-office", "Square feet used for the office", "Used regularly and only for business", "150") + "</div>" +
        fgh("Regular method: yearly home expenses (total for the whole home)") +
        '<div class="fgrid">' + money("h-rent", "Rent", "Renters", "0") + money("h-mint", "Mortgage interest", "Owners", "0") + money("h-tax", "Real estate taxes", "Owners", "0") +
        money("h-ins", "Home or renter's insurance", "", "0") + money("h-util", "Utilities", "Electric, gas, water, internet", "0") + money("h-rep", "Repairs and maintenance", "", "0") +
        money("h-dep", "Depreciation", "Owners, from Form 8829", "0") + money("h-other", "Other home expenses", "HOA fees, security", "0") + "</div>" +
        money("h-direct", "Direct office expenses", "Costs only for the office, such as painting it. Deducted in full", "0") +
        money("h-limit", "Income limit (optional)", "Profit before this deduction. The deduction can't exceed it", "0") + "</div>")
    verdict = '<div class="verdict" id="verdict"><span class="vk">Start here</span><h3>Enter your square footage.</h3><p>We compare the simplified method with the regular method side by side.</p></div>'
    kp = kpi("k-best", "Higher method", "wide gold") + kpi("k-simple", "Simplified deduction") + kpi("k-regular", "Regular deduction") + kpi("k-pct", "Business-use percentage", "wide")
    res = result_card("Your deduction", kp, extra=verdict, cta_label="Get help with deductions")
    below = math_card()
    info = f"""<h2>The two methods</h2>
<ul><li><strong>Simplified method.</strong> {usd(h["rate"])} per square foot of office space, up to {h["max_sqft"]} square feet, so the most you can deduct is {usd(h["max_deduction"])}. There is no depreciation and no record of actual expenses to keep. Mortgage interest and real estate taxes are not split; you claim them in full on Schedule A if you itemize.</li>
<li><strong>Regular method.</strong> Business-use percentage (office square feet divided by total square feet) times your actual home expenses, plus direct office costs. It takes more records and Form 8829, and owners must account for depreciation, but it can be larger for a bigger office or a higher-cost home.</li></ul>
<h2>The rules that apply to both</h2>
<ul><li>The space must be used regularly and exclusively for business, and it must be your principal place of business.</li>
<li>{esc(h["limit_note"])}.</li>
<li>The deduction is for self-employed people who file Schedule C. W-2 employees generally can't claim it.</li></ul>
<p>Keep a floor plan or measurements, photos of the space and the bills behind every expense. Once you have your deduction, see how it changes your tax in the <a href="/tools/1099-tax-calculator/">1099 tax calculator</a>.</p>
<p>Wondering about your phone, internet or utilities? <a href="/tools/is-it-deductible/#home-office">Check other expenses →</a></p>"""
    return build_page(slug, "Home Office Deduction Calculator 2026",
                      "Compare the simplified ($5 per square foot, up to 300) and regular home office deduction methods for 2026 side by side.",
                      "Home office calculator", "Home office deduction calculator",
                      "Compare the simplified and regular home office methods and see which gives the larger deduction.",
                      grid + res, below, info, {"home": h}, "homeoffice", f, "Not sure which deduction you qualify for?",
                      "We review your home office, vehicle and other deductions before you file. Book a 30-minute consultation.")


# ------------------------------------------------------------------ 7. mileage
def build_mileage():
    slug = "mileage-deduction-calculator"
    f = Facts()
    mg = lambda k: f.get("mileage", k)
    n1, n2 = f.node("mileage", "business_rate_2026_jan_jun"), f.node("mileage", "business_rate_2026_jul_dec")
    m = {"r1": mg("business_rate_2026_jan_jun"), "r2": mg("business_rate_2026_jul_dec")}
    cents = lambda r: f"{r * 100:g}"
    grid = (
        '<div class="tcard"><h2>Your business miles</h2><p class="sub">The IRS changed the business rate on July 1, 2026, so enter miles for each half of the year. Nothing you type leaves your browser.</p>' + factline(f) +
        numf("m-h1", f"Business miles, Jan. 1 to June 30 ({cents(m['r1'])} cents per mile)", "Only miles driven for business, not commuting", "4,200") +
        numf("m-h2", f"Business miles, July 1 to Dec. 31 ({cents(m['r2'])} cents per mile)", "", "3,800") +
        money("m-park", "Parking and tolls for business trips", "Optional. Deductible on top of the standard rate", "0") + "</div>")
    kp = kpi("k-total", "Mileage deduction", "wide gold") + kpi("k-miles", "Business miles") + kpi("k-h1", "Jan. to June") + kpi("k-h2", "July to Dec.")
    res = result_card("Your deduction", kp, cta_label="Get help with deductions")
    other = (f'<table class="tbl ctbl"><thead><tr><th>2026 rate</th><th class="num">Per mile</th></tr></thead><tbody>'
             f'<tr><td>Business, Jan. 1 to June 30</td><td class="num">{cents(m["r1"])} cents</td></tr>'
             f'<tr><td>Business, July 1 to Dec. 31</td><td class="num">{cents(m["r2"])} cents</td></tr>'
             f'<tr><td>Medical and military moving, Jan. 1 to June 30</td><td class="num">{cents(mg("medical_military_moving_rate_2026_jan_jun"))} cents</td></tr>'
             f'<tr><td>Medical and military moving, July 1 to Dec. 31</td><td class="num">{cents(mg("medical_military_moving_rate_2026_jul_dec"))} cents</td></tr>'
             f'<tr><td>Charitable (set by law, all year)</td><td class="num">{cents(mg("charitable_rate_2026"))} cents</td></tr></tbody></table>')
    below = math_card() + f'<section class="tcard"><h2>All 2026 IRS standard mileage rates</h2><p class="sub">This calculator uses the business rates. The others are shown for reference.</p>{other}</section>'
    info = f"""<h2>How the standard mileage rate works</h2>
<p>Instead of tracking gas, repairs and insurance, you can deduct a set amount per business mile. For 2026 the rate is {cents(m["r1"])} cents for miles driven January 1 through June 30 and {cents(m["r2"])} cents for miles driven July 1 through December 31. Split your miles by date, since each period has its own rate.</p>
<ul><li><strong>Commuting doesn't count.</strong> Business miles are trips between work locations, to clients, or for business errands, not the drive from home to your regular workplace.</li>
<li><strong>Keep a mileage log.</strong> Record the date, destination, purpose and miles for each trip, as it happens. A log is what the IRS asks for.</li>
<li><strong>Parking and tolls</strong> for business trips can be deducted in addition to the standard rate.</li>
<li><strong>Choosing the method.</strong> If you want to use the standard rate for a car you own, you generally have to use it in the first year the car is used for business. Ask us before you choose.</li></ul>
<p>Mileage reduces the profit you pay tax on. See the effect in the <a href="/tools/1099-tax-calculator/">1099 tax calculator</a>.</p>
<p>Parking, tolls, travel and meals have their own rules. <a href="/tools/is-it-deductible/#mileage">Check other expenses →</a></p>"""
    return build_page(slug, "Mileage Deduction Calculator 2026 (IRS Standard Rates)",
                      "Calculate your 2026 business mileage deduction with the IRS standard rates, including the split between the January to June and July to December rates.",
                      "Mileage calculator", "Mileage deduction calculator",
                      "Business miles times the 2026 IRS standard rate, split at the July 1 rate change.",
                      grid + res, below, info, {"mileage": m}, "mileage", f, "Want your deductions checked?",
                      "We review your mileage, vehicle and business deductions before you file. Book a 30-minute consultation.")


# ------------------------------------------------------------------ 4. contractor tracker
ENTITIES = [
    {"id": "indiv", "label": "Individual or sole proprietor", "corp": False, "exempt": False, "foreign": False},
    {"id": "llc", "label": "LLC taxed as a sole proprietor or partnership", "corp": False, "exempt": False, "foreign": False},
    {"id": "partnership", "label": "Partnership", "corp": False, "exempt": False, "foreign": False},
    {"id": "ccorp", "label": "C corporation", "corp": True, "exempt": False, "foreign": False},
    {"id": "scorp", "label": "S corporation", "corp": True, "exempt": False, "foreign": False},
    {"id": "llccorp", "label": "LLC taxed as a corporation", "corp": True, "exempt": False, "foreign": False},
    {"id": "exempt", "label": "Tax-exempt organization or government agency", "corp": False, "exempt": True, "foreign": False},
    {"id": "foreign", "label": "Foreign person or business (Form W-8)", "corp": False, "exempt": False, "foreign": True},
]
METHODS = [
    {"id": "check", "label": "Check", "reportable": True}, {"id": "ach", "label": "ACH or bank transfer", "reportable": True},
    {"id": "wire", "label": "Wire", "reportable": True}, {"id": "cash", "label": "Cash", "reportable": True},
    {"id": "zelle", "label": "Zelle", "reportable": True}, {"id": "personal_app", "label": "Personal app transfer (PayPal Friends & Family, personal Venmo or Cash App)", "reportable": True},
    {"id": "card", "label": "Credit or debit card", "reportable": False},
    {"id": "processor", "label": "Business payment app (PayPal Goods & Services, Stripe, Square)", "reportable": False},
]


def build_tracker():
    slug = "1099-contractor-tracker"
    f = Facts()
    T = FACTS["1099"]
    nec = T["nec_threshold"]
    dl = [e for e in CAL["entities"]["sole_proprietor"] if e["form"] == "1099-NEC"][0]
    f.used.append(dl)
    fact_checked = (T["checked"],)
    ent_opts = "".join(f'<option value="{e["id"]}">{esc(e["label"])}</option>' for e in ENTITIES)
    meth_opts = "".join(f'<option value="{m["id"]}">{esc(m["label"])}</option>' for m in METHODS)
    lock = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10.5" width="16" height="10" rx="2.5"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/></svg>'
    left = (
        '<div><div class="tcard"><h2>1. Add a vendor</h2><p class="sub">The people and businesses you pay for services.</p>' + factline(f, fact_checked) +
        f'<div class="privacy">{lock}<span>Your list stays on your device, in this browser. Nothing is uploaded or sent to MFA. Never type a Social Security number or EIN here: we only track whether you have one on file.</span></div>'
        '<p class="notice" id="st-note" hidden></p>'
        '<div class="fld"><label for="v-name">Vendor name</label><input type="text" id="v-name" maxlength="80" autocomplete="off" placeholder="Alex Rivera Design"/></div>'
        f'<div class="fgrid"><div class="fld"><label for="v-entity">Entity type</label><select id="v-entity">{ent_opts}</select></div>'
        '<div class="fld"><label for="v-tin">Taxpayer ID (W-9) on file?</label><select id="v-tin"><option value="N">No</option><option value="Y">Yes</option></select></div></div>'
        '<div class="fld"><label for="v-w9">Date of the W-9 (optional)</label><input type="date" id="v-w9"/></div>'
        '<div class="fld"><label class="opt"><input type="checkbox" id="v-lm"/><span>Attorney or law firm<small>Reportable even if the firm is a corporation</small></span></label></div>'
        '<div class="btnrow"><button type="button" class="btn btn-ink" id="v-add">Add vendor</button><button type="button" class="btn btn-line-ink" id="v-cancel" hidden>Cancel</button></div><p class="tmsg" id="v-msg" aria-live="polite"></p></div>'
        '<div class="tcard" style="margin-top:24px"><h2>2. Log a payment</h2><p class="sub">One line per payment made in 2026.</p>'
        '<div class="fld"><label for="p-vendor">Vendor</label><select id="p-vendor"></select></div>'
        '<div class="fgrid"><div class="fld"><label for="p-date">Date paid</label><input type="date" id="p-date"/></div>' + money("p-amount", "Amount", "", "1,250") + "</div>"
        f'<div class="fld"><label for="p-method">How you paid</label><select id="p-method">{meth_opts}</select>'
        '<span class="hint">Card and payment-app payments are reported by the processor on Form 1099-K, so they are tracked but not counted toward a 1099-NEC.</span></div>'
        '<div class="btnrow"><button type="button" class="btn btn-ink" id="p-add">Log payment</button></div><p class="tmsg" id="p-msg" aria-live="polite"></p></div></div>')
    kp = kpi("s-needed", "1099-NECs needed", "wide gold") + kpi("s-vendors", "Vendors") + kpi("s-missing", "Missing a W-9") + kpi("s-total", "Counts toward 1099s", "wide")
    res = (f'<div class="tcard tres" aria-live="polite"><h2>Your 2026 summary</h2><p class="sub">Updates as you add vendors and payments.</p><div class="kpis">{kp}</div>'
           f'<p class="muted">Threshold: <b>{usd(nec)}</b> or more paid to a vendor in 2026 by check, ACH, wire, cash, Zelle or a personal app transfer.</p>'
           '<div class="verdict yes" style="margin-top:16px"><span class="vk">Deadline</span><h3 style="font-size:1.4rem">1099-NEC due <span id="s-deadline">—</span></h3>'
           f'<p>Send each contractor a copy and file with the IRS by this date. There is no automatic extension.</p></div>'
           '<div class="acts"><button type="button" class="btn btn-gold" id="s-cal">Add the deadline to my calendar</button><a class="btn btn-line" href="/tools/do-i-need-to-send-a-1099/">Open the 1099 checker</a></div>'
           '<p class="muted">General information, not tax advice.</p></div>')
    below = ('<section class="tcard"><h2>Your vendors</h2><p class="sub">Totals are for payments dated in 2026.</p><div id="vlist"></div></section>'
             '<section class="tcard"><h2>Payments</h2><div id="plist"></div></section>'
             '<section class="tcard"><h2>Save or move your list</h2><p class="sub">Export a CSV to back up your list or open it in a spreadsheet, and import it on another device. Files stay on your device.</p>'
             '<div class="btnrow"><button type="button" class="btn btn-ink" id="b-export">Export CSV</button><button type="button" class="btn btn-line-ink" id="b-clear">Delete all data</button></div>'
             '<div class="fld" style="margin-top:18px"><label for="f-import">Import a CSV exported from this tool</label><input type="file" id="f-import" accept=".csv,text/csv"/></div><p class="tmsg" id="io-msg" aria-live="polite"></p></section>')
    info = f"""<h2>How the tracker decides</h2>
<p>For payments made in 2026, a vendor needs a Form 1099-NEC when you paid them {usd(nec)} or more for services by check, ACH, wire, cash, Zelle or a personal app transfer. Nonemployee compensation goes in box 1a of the 2026 Form 1099-NEC (revised 12/2026). Send it to the contractor and file it with the IRS by {day(dl["date"])}.</p>
<ul><li><strong>{usd(nec)} threshold.</strong> The same {usd(nec)} threshold applies to most Form 1099-MISC payments for 2026 (it was $600 for 2025). Royalties stay at {usd(T["royalties"])}, and gross proceeds paid to attorneys at {usd(T["attorney_proceeds"])}.</li>
<li><strong>Card and app payments are excluded.</strong> Payments by credit or debit card or through a payment network are reported by the processor on Form 1099-K, so they don't count toward the 1099-NEC. They are listed separately so you can see the full picture.</li>
<li><strong>Corporations are generally exempt,</strong> except for legal services. Check the attorney box for a law firm.</li>
<li><strong>Tax-exempt organizations, government agencies and foreign payees</strong> generally don't receive a 1099-NEC.</li>
<li><strong>Get the W-9 first.</strong> Ask for a Form W-9 before the first payment. The <a href="/tools/w-9-request-email-template/">W-9 request email templates</a> make it quick.</li></ul>
<p>This tracker treats every payment as payment for services (Form 1099-NEC). Rent, medical payments, royalties and prizes use Form 1099-MISC and other rules: run those through the <a href="/tools/do-i-need-to-send-a-1099/">1099 checker</a>. For the full walkthrough, read the <a href="/blog/form-1099-preparation-guide-2026/">Form 1099 preparation guide</a>.</p>
<h2>Where your data lives</h2>
<p>Your vendors and payments are saved in this browser's local storage on this device. MFA never receives them. Clearing site data, using a private window or switching browsers will remove or hide the list, so export a CSV for a backup. Do not enter Social Security numbers or EINs: the tracker only records whether a taxpayer ID is on file.</p>"""
    data = {"year": 2026, "threshold": nec, "entities": ENTITIES, "methods": METHODS, "deadline": {"date": dl["date"], "what": dl["what"]}}
    return build_page(slug, "1099 Contractor Tracker: Who Needs a 1099-NEC in 2026",
                      "Track vendors, W-9s and payments, see who needs a 1099-NEC at the 2026 $2,000 threshold, and export to CSV. Data stays in your browser.",
                      "1099 tracker", "1099 contractor tracker",
                      "Log your vendors and payments, see who needs a 1099-NEC at the 2026 threshold, and keep the W-9s straight. It all stays on your device.",
                      left + res, below, info, data, "tracker", f, "Want your 1099s handled?",
                      "We collect W-9s, clean up vendor records and file every 1099 on time. Book a 30-minute consultation.",
                      extra_src=T["sources"], extra_checked=fact_checked)


# ------------------------------------------------------------------ 8. deadlines
ENTITY_INFO = [
    ("sole_proprietor", "Sole proprietor or single-member LLC", "Schedule C filers: estimated tax payments, your personal return, 1099s and state returns."),
    ("partnership", "Partnership or multi-member LLC", "Form 1065 and K-1s, 1099s and state partnership filings."),
    ("s_corporation", "S corporation", "Form 1120-S, K-1s, the Form 2553 election deadline and 1099s."),
    ("c_corporation", "C corporation", "Form 1120, corporate estimated tax deposits and 1099s."),
    ("employer", "Employer (payroll)", "W-2s, quarterly payroll returns and New York payroll filings."),
    ("nonprofit", "Nonprofit", "Form 990 and extended due dates."),
    ("sales_tax_seller", "Sales tax seller (NJ and NY)", "Quarterly sales and use tax returns in New Jersey and New York."),
]


def build_deadlines():
    slug = "tax-deadlines-2027"
    f = Facts()
    cal = {}
    for k, _, _ in ENTITY_INFO:
        cal[k] = []
        for e in CAL["entities"][k]:
            f.used.append(e)
            cal[k].append({kk: e[kk] for kk in ("date", "form", "what", "jurisdiction", "source_url") } | ({"note": e["note"]} if e.get("note") else {}))
    ent_opts = "".join(f'<option value="{k}">{esc(t)}</option>' for k, t, _ in ENTITY_INFO)
    grid = (
        '<div class="tcard"><h2>Find your deadlines</h2><p class="sub">Calendar-year filers. Fiscal-year entities have different dates.</p>'
        f'<p class="factline">Facts checked {{CHK}}</p>'
        f'<div class="fld"><label for="d-entity">Your entity type</label><select id="d-entity">{ent_opts}</select><span class="hint" id="d-desc"></span></div>'
        '<div class="fld"><span class="lbl">Show</span><div class="opts opts-2">'
        '<label class="opt"><input type="checkbox" id="d-j-federal" checked/><span>Federal</span></label>'
        '<label class="opt"><input type="checkbox" id="d-j-NJ" checked/><span>New Jersey</span></label>'
        '<label class="opt"><input type="checkbox" id="d-j-NY" checked/><span>New York</span></label></div></div></div>'
        '<div class="tcard tres"><h2>Your 2027 calendar</h2><p class="sub" id="d-next"></p><div class="kpis"><div class="kpi wide gold"><b id="d-count">—</b><span>Deadlines shown</span></div></div>'
        '<div class="acts"><button type="button" class="btn btn-gold" id="d-all">Add all to calendar (.ics)</button></div>'
        '<p class="muted">The .ics file opens in Apple Calendar, Outlook and Google Calendar. Each date has a reminder 7 days before.</p><p class="muted">General information, not tax advice.</p></div>')
    below = '<section class="tcard"><h2>Deadlines</h2><div id="dlist"></div></section>'
    info = """<h2>How to use this calendar</h2>
<p>Pick the entity you file as. The list shows federal, New Jersey and New York dates for calendar-year filers, in date order. Add one date to your calendar, or add everything on the list in one file. Dates that fall on a weekend or holiday move to the next business day, and the IRS or a state can change a date when it announces disaster relief, so check the source link before you rely on an extension.</p>
<ul><li><strong>Estimated tax.</strong> Use the <a href="/tools/quarterly-estimated-tax-calculator/">quarterly estimated tax calculator</a> to work out each payment.</li>
<li><strong>1099s.</strong> Track who needs one with the <a href="/tools/1099-contractor-tracker/">1099 contractor tracker</a>.</li>
<li><strong>S corporation election.</strong> The Form 2553 date is listed under S corporation. See whether an election makes sense with the <a href="/tools/s-corp-tax-savings-calculator/">S corp calculator</a>.</li></ul>
<p>Prefer an article? Read the <a href="/blog/2027-tax-calendar/">2027 tax calendar</a> on MFA Insights.</p>"""
    f.used.append({"checked": CAL["meta"]["checked"], "source_url": "https://www.irs.gov/pub/irs-dft/p509--dft.pdf"})
    chk = day(f.checked())
    grid = grid.replace("{CHK}", chk)
    ents = [{"id": k, "label": t, "desc": d} for k, t, d in ENTITY_INFO]
    return build_page(slug, "2027 Business Tax Deadlines by Entity: Fed, NJ & NY",
                      "Every 2027 federal, New Jersey and New York tax deadline for sole proprietors, partnerships, S and C corporations, employers and nonprofits.",
                      "2027 tax deadlines", "2027 business tax deadlines by entity",
                      "Choose your entity and get every 2027 federal, NJ and NY deadline, with an add-to-calendar file for each date or the whole list.",
                      grid, below, info, {"cal": cal, "entities": ents}, "deadlines", f, "Want someone to watch the dates for you?",
                      "We track your deadlines, prepare the filings and make the payments on time. Book a 30-minute consultation.",
                      extra_note="Federal dates are checked against the IRS draft Publication 509 for 2027. ")


def build_all():
    return [build_quarterly(), build_1099calc(), build_scorp(), build_tracker(), build_paycheck(), build_home(), build_mileage(), build_deadlines()]
