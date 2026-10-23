#!/usr/bin/env python3
"""Builds the 2026 Small Business Tax Starter Kit (the /start/ lead magnet) as HTML, then renders it to PDF.

Zain (2026-10-23 12:58 ET): every product, book and pin leads back to mfa-advisory.com/start, where people get this kit
for their email and then a 5-email series that ends in booking a consult.

  python3 tools/build_start_kit.py            -> content/start-kit/starter-kit.html + site/start/kit/<KIT_FILE>
Needs Node + Playwright (tools/render_pdf.js). Not part of build_resources.py: re-run only when the kit content changes.

Rules: every figure comes from data/*.json (verified by the Blog session, each with an irs.gov / state source and a
"checked" stamp) and is labelled "for 2026". Never "free", never "CPA firm", no street address, no legal advice.
The PDF is delivered by email (MailerLite automation, email #1), never linked from a page; /start/kit/* is noindex (site/_headers).
It is a starter kit, not a paid product: short checklists that point to the full tools, guides and services.
"""
import html
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_HTML = ROOT / "content" / "start-kit" / "starter-kit.html"
KIT_DIR = ROOT / "site" / "start" / "kit"
KIT_FILE = "mfa-2026-small-business-tax-starter-kit-q7k3.pdf"   # unlisted name; the link only goes out by email
KIT_URL = "https://mfa-advisory.com/start/kit/" + KIT_FILE
UTM = "utm_source=starter-kit&utm_medium=pdf&utm_campaign=start-2026"
SITE = "https://mfa-advisory.com"
esc = lambda s: html.escape(str(s), quote=True)

F = json.loads((DATA / "tax-figures-2026.json").read_text(encoding="utf-8"))
CAL = json.loads((DATA / "tax-calendar-2027.json").read_text(encoding="utf-8"))
DED = {e["slug"]: e for e in json.loads((DATA / "deductions.json").read_text(encoding="utf-8"))["entries"]}
fed, nj, ny = F["federal"], F["new_jersey"], F["new_york_state"]


def checked_ok():
    """Every figure used must have been checked within 30 days (rule for using repo data instead of re-checking irs.gov)."""
    today = date.today()
    stamps = [F["meta"]["checked"], CAL["meta"]["checked"]] + [DED[k]["checked"] for k in DED]
    old = [s for s in stamps if (today - datetime.fromisoformat(s[:10]).date()).days > 30]
    if old:
        sys.exit(f"Data older than 30 days ({old[:3]}...). Re-verify data/*.json on irs.gov before rebuilding the kit.")
    return min(datetime.fromisoformat(s[:10]).date() for s in stamps)


def money(n, cents=False):
    return f"${n:,.2f}" if cents else f"${n:,.0f}"


def d(iso, fmt="%b %-d, %Y"):
    return datetime.fromisoformat(iso).strftime(fmt)


def link(path, text=None):
    url = f"{SITE}{path}{'&' if '?' in path else '?'}{UTM}"
    return f'<a href="{esc(url)}">{esc(text or "mfa-advisory.com" + path)}</a>'


# ------------------------------------------------------------------ figures (all from data/*.json)
SE = fed["self_employment_tax_rate"]["value"]           # 0.153
NEF = fed["net_earnings_factor"]["value"]               # 0.9235
WAGE_BASE = fed["social_security_wage_base"]["value"]   # 184,500
SH = fed["estimated_tax_safe_harbor"]["value"]
EST_THR = fed["estimated_tax_threshold"]["value"]
NJ_THR = nj["estimated_tax_threshold"]["value"]
NY_THR = ny["estimated_tax_threshold"]["value"]
EST26 = fed["estimated_tax_due_dates_2026"]["value"]
EST27 = fed["estimated_tax_due_dates_2027"]["value"]
MILE1 = F["mileage"]["business_rate_2026_jan_jun"]["value"]
MILE2 = F["mileage"]["business_rate_2026_jul_dec"]["value"]
HO = F["home_office_simplified"]
HO_RATE, HO_MAX_SQ, HO_MAX = HO["rate_per_sq_ft"]["value"], HO["max_sq_ft"]["value"], HO["max_deduction"]["value"]

# Worked examples
EX_PROFIT = 60000
EX_SE = EX_PROFIT * NEF * SE
SC_PROFIT, SC_SALARY = 100000, 60000
SC_LLC_SE = SC_PROFIT * NEF * SE
SC_PAYROLL = SC_SALARY * SE          # 7.65% employee + 7.65% employer on wages below the wage base
SC_DIFF = SC_LLC_SE - SC_PAYROLL


def fed_entry(ent, form_start):
    for e in CAL["entities"][ent]:
        if e["jurisdiction"] == "federal" and e["form"].startswith(form_start):
            return e
    raise KeyError(ent + " " + form_start)


CSS = """
@font-face{font-family:Cormorant;font-weight:400;src:url(../../tools/fonts/cormorant-garamond-latin-400-normal.woff2)}
@font-face{font-family:Cormorant;font-weight:400;font-style:italic;src:url(../../tools/fonts/cormorant-garamond-latin-400-italic.woff2)}
@font-face{font-family:Cormorant;font-weight:500;src:url(../../tools/fonts/cormorant-garamond-latin-500-normal.woff2)}
@font-face{font-family:Cormorant;font-weight:500;font-style:italic;src:url(../../tools/fonts/cormorant-garamond-latin-500-italic.woff2)}
@font-face{font-family:Inter;font-weight:300;src:url(../../tools/fonts/inter-latin-300-normal.woff2)}
@font-face{font-family:Inter;font-weight:400;src:url(../../tools/fonts/inter-latin-400-normal.woff2)}
@font-face{font-family:Inter;font-weight:500;src:url(../../tools/fonts/inter-latin-500-normal.woff2)}
@font-face{font-family:Inter;font-weight:600;src:url(../../tools/fonts/inter-latin-600-normal.woff2)}
@font-face{font-family:Inter;font-weight:700;src:url(../../tools/fonts/inter-latin-700-normal.woff2)}
@page{size:Letter;margin:0}
:root{--navy:#10233F;--navy-2:#1B3557;--gold:#B08D3F;--gold-b:#D8B769;--paper:#FDFDFC;--paper-2:#F5F4EF;--ink:#151515;--muted:#555b66;--hair:#E4E1D6}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,sans-serif;color:var(--ink);font-size:8.9pt;line-height:1.45;font-variant-numeric:lining-nums;-webkit-print-color-adjust:exact;print-color-adjust:exact}
a{color:var(--navy);text-decoration:none;border-bottom:1px solid var(--gold-b)}
.page{width:8.5in;height:11in;position:relative;background:var(--paper);page-break-after:always;overflow:hidden}
.page:last-child{page-break-after:auto}
.head{background:var(--navy);color:#fff;padding:.42in .6in .3in;position:relative}
.head::after{content:'';position:absolute;left:0;right:0;bottom:0;height:3px;background:var(--gold)}
.kick{display:flex;justify-content:space-between;align-items:center;font-size:6.6pt;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:var(--gold-b);margin-bottom:10px}
.kick span:last-child{color:rgba(255,255,255,.55)}
h1{font-family:Cormorant,serif;font-weight:500;font-size:28pt;line-height:1.02}
h1 em,h2 em{color:var(--gold-b);font-style:italic}
.sub{color:#C9D2E0;margin-top:7px;font-size:9.4pt;font-weight:300;max-width:6.4in}
.body{padding:.26in .6in 0}
h2{font-family:Cormorant,serif;font-weight:500;font-size:15pt;color:var(--navy);margin:14px 0 6px;line-height:1.1}
h2:first-child{margin-top:0}
h3{font-size:7.4pt;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);margin:12px 0 5px}
p{margin:0 0 6px}
.lead{font-size:9.6pt;color:#2b2f36;margin-bottom:10px}
table{width:100%;border-collapse:collapse}
th{background:var(--navy);color:#fff;font-weight:600;font-size:6.9pt;letter-spacing:.08em;text-transform:uppercase;text-align:left;padding:5px 8px}
td{padding:5px 8px;border-bottom:1px solid var(--hair);vertical-align:top}
tr:nth-child(even) td{background:#FAF9F5}
td.dt{white-space:nowrap;font-family:Cormorant,serif;font-weight:500;font-size:11.5pt;color:var(--navy);width:1.05in;line-height:1.15}
td.who{color:var(--muted);font-size:7.8pt;width:1.6in}
.tag{display:inline-block;font-size:6.2pt;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:1px 6px;border-radius:99px;border:1px solid var(--gold);color:var(--gold);margin-left:4px;vertical-align:1px}
.box{background:var(--paper-2);border-left:3px solid var(--gold);padding:8px 11px;margin:10px 0;font-size:8.4pt}
.box b{color:var(--navy)}
.nbox{background:var(--navy);color:#fff;border-radius:8px;padding:12px 14px;margin:10px 0}
.nbox b{color:var(--gold-b)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:0 .3in}
.cols3{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
.stat{border:1px solid var(--gold-b);border-radius:7px;padding:8px 10px;background:#fff}
.stat .v{font-family:Cormorant,serif;font-weight:500;font-size:19pt;color:var(--navy);line-height:1}
.stat .t{font-size:6.8pt;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--gold);margin:4px 0 2px}
.stat .d{font-size:7.5pt;color:var(--muted);line-height:1.35}
ul.ck{list-style:none}
ul.ck li{position:relative;padding:4px 0 4px 19px;border-bottom:1px dotted #d9d5c8;font-size:8.3pt;line-height:1.38;break-inside:avoid}
ul.ck li::before{content:'';position:absolute;left:0;top:5.5px;width:10px;height:10px;border:1.3px solid var(--gold);border-radius:2px;background:#fff}
ul.ck li b{color:var(--navy)}
ul.ck li small{display:block;color:var(--muted);font-size:7.5pt}
ul.no li::before{border-color:#b9504a}
ol.steps{list-style:none;counter-reset:s}
ol.steps li{counter-increment:s;position:relative;padding:7px 0 7px 34px;border-bottom:1px solid var(--hair);break-inside:avoid}
ol.steps li::before{content:counter(s,decimal-leading-zero);position:absolute;left:0;top:4px;font-family:Cormorant,serif;font-weight:500;font-size:16pt;color:var(--gold);line-height:1}
ol.steps li b{color:var(--navy);display:block;font-size:8.8pt}
ol.steps li span{color:#3b3f48;font-size:8.2pt}
.ws td{height:26px}
.ft{position:absolute;left:.6in;right:.6in;bottom:.32in;border-top:1px solid var(--gold-b);padding-top:5px;font-size:6.6pt;color:#6b707a;display:flex;justify-content:space-between;gap:20px}
.ft .src{max-width:5.6in}
.ft a{color:#6b707a;border:0}
/* cover */
.cover{background:var(--navy);color:#fff}
.cover .frame{position:absolute;inset:.32in;border:1px solid rgba(216,183,105,.38);border-radius:16px;pointer-events:none}
.cover .ring{position:absolute;right:-1.6in;top:-1.6in;width:5in;height:5in;border-radius:50%;border:1px solid rgba(216,183,105,.22)}
.cover .in{position:absolute;inset:.75in .8in}
.brand{display:flex;align-items:center;gap:11px}
.brand img{width:40px;height:40px;border-radius:9px}
.brand b{display:block;font-family:Cormorant,serif;font-weight:500;font-size:17pt;line-height:1}
.brand i{display:block;font-style:normal;font-size:6.4pt;font-weight:600;letter-spacing:.3em;text-transform:uppercase;color:rgba(255,255,255,.6);margin-top:3px}
.cover .eb{margin-top:1.05in;font-size:8pt;font-weight:700;letter-spacing:.32em;text-transform:uppercase;color:var(--gold-b)}
.cover h1{font-size:46pt;line-height:.98;margin-top:12px;max-width:6in}
.cover .sub{font-size:11pt;margin-top:16px;max-width:5.6in;color:rgba(255,255,255,.75)}
.toc{margin-top:.42in;display:grid;grid-template-columns:1fr 1fr;gap:0 .35in;max-width:6.4in}
.toc div{display:flex;gap:10px;align-items:baseline;padding:7px 0;border-bottom:1px solid rgba(216,183,105,.25);font-size:9pt}
.toc span{font-family:Cormorant,serif;font-size:13pt;color:var(--gold-b);width:22px}
.first{margin-top:.38in;background:rgba(255,255,255,.06);border:1px solid rgba(216,183,105,.35);border-radius:10px;padding:13px 16px;max-width:6.4in}
.first .t{font-size:7pt;font-weight:700;letter-spacing:.24em;text-transform:uppercase;color:var(--gold-b);margin-bottom:6px}
.first ol{padding-left:16px;font-size:8.8pt;line-height:1.55;color:rgba(255,255,255,.88)}
.cover .by{position:absolute;left:0;right:0;bottom:0;display:flex;justify-content:space-between;align-items:flex-end;font-size:7.4pt;color:rgba(255,255,255,.62);gap:20px}
.cover .by b{color:#fff;font-weight:600}
/* last page */
.svc{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:8px 0 12px}
.svc div{background:#fff;border:1px solid var(--hair);border-top:2px solid var(--gold);border-radius:0 0 8px 8px;padding:11px 12px}
.svc h4{font-family:Cormorant,serif;font-weight:500;font-size:13.5pt;color:var(--navy);line-height:1.1;margin-bottom:4px}
.svc .pr{font-size:7.3pt;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--gold);margin-bottom:5px}
.svc p{font-size:7.9pt;color:#3b3f48;margin:0}
.book{background:var(--navy);color:#fff;border-radius:12px;padding:18px 20px;display:flex;justify-content:space-between;align-items:center;gap:18px;margin:12px 0}
.book h2{color:#fff;margin:0 0 4px;font-size:18pt}
.book p{color:rgba(255,255,255,.75);margin:0;font-size:8.6pt}
.book a.btn{flex-shrink:0;background:var(--gold-b);color:var(--navy);border:0;border-radius:99px;padding:10px 18px;font-size:7.4pt;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.cred{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}
.cred span{border:1px solid var(--gold);color:var(--navy);border-radius:99px;padding:3px 10px;font-size:7.4pt;font-weight:600}
.srcs{font-size:6.9pt;color:var(--muted);columns:2;column-gap:.3in}
.srcs li{margin:0 0 3px 12px;break-inside:avoid}
.srcs a{color:var(--muted);border:0}
.fine{font-size:7pt;color:var(--muted);font-style:italic}
"""


def page(num, kick, title, sub, body, src):
    return f'''<section class="page"><div class="head"><div class="kick"><span>{esc(kick)}</span><span>2026 Small Business Tax Starter Kit · {num:02d}</span></div>
<h1>{title}</h1><p class="sub">{sub}</p></div>
<div class="body">{body}</div>
<div class="ft"><span class="src">{src}</span><span>mfa-advisory.com · General information for 2026, not tax or legal advice</span></div></section>'''


def build_html():
    asof = checked_ok()
    asof_txt = asof.strftime("%B %-d, %Y")
    logo = "../../site/apple-touch-icon.png"
    nec = fed_entry("sole_proprietor", "1099-NEC")
    s_ret, s_2553 = fed_entry("s_corporation", "1120-S"), fed_entry("s_corporation", "2553")
    p_ret = fed_entry("partnership", "1065")
    c_ret = fed_entry("c_corporation", "1120")
    misc_paper = fed_entry("partnership", "1099 (paper)")
    misc_e = fed_entry("partnership", "1099 (electronic)")
    w2 = fed_entry("employer", "W-2")

    # ---- 1. cover
    toc = [("01", "Key tax dates for 2026 returns"), ("02", "Quarterly estimated taxes"), ("03", "Deduction checklist"),
           ("04", "1099 readiness checklist"), ("05", "Monthly bookkeeping close"), ("06", "LLC vs S corp, in one page"),
           ("07", "When to hand it off")]
    cover = f'''<section class="page cover"><div class="ring"></div><div class="frame"></div><div class="in">
<div class="brand"><img src="{logo}" alt="MFA logo"/><div><b>Merchant</b><i>Financial Advisory</i></div></div>
<p class="eb">For 2026 · Small business edition</p>
<h1>Small Business Tax <em>Starter Kit</em></h1>
<p class="sub">The dates, checklists and one-page answers we walk new clients through first. For freelancers, single-member LLCs and small businesses, with New Jersey and New York notes.</p>
<div class="toc">{"".join(f"<div><span>{n}</span>{esc(t)}</div>" for n, t in toc)}</div>
<div class="first"><p class="t">Start here: three things to do this week</p><ol>
<li>Put the next estimated tax date ({d(EST26[3], "%b %-d, %Y")}) in your calendar. Page 3.</li>
<li>Ask every contractor you paid in 2026 for a signed Form W-9. Page 5.</li>
<li>Pick one day each month for your bookkeeping close and block it. Page 6.</li></ol></div>
<div class="by"><span>Prepared by <b>Zain Merchant, ACCA</b><br/>Merchant Financial Advisory · Princeton, NJ</span>
<span style="text-align:right">Figures checked against IRS and state sources as of {asof_txt}.<br/>General information, not tax or legal advice.</span></div>
</div></section>'''

    # ---- 2. key dates
    rows = [
        (EST26[3], f"Fourth 2026 estimated tax payment (Form 1040-ES). NJ and NY fourth estimates are due the same day.", "Self-employed, owners with untaxed income"),
        (nec["date"], f"Form 1099-NEC to contractors <b>and</b> the IRS for 2026 payments of $2,000 or more. Also W-2s to employees and the SSA, and Forms 941 (Q4) and 940.", "Anyone who paid contractors or employees"),
        (misc_paper["date"], "Paper Forms 1099 other than 1099-NEC (for example 1099-MISC) due to the IRS with Form 1096.", "Payers filing on paper"),
        (s_ret["date"], "Form 1120-S (S corporations) and Form 1065 (partnerships and multi-member LLCs) due, with K-1s to owners. Form 7004 extends to Sept. 15. Last day to file Form 2553 for S corp status starting in 2027.", "S corps, partnerships, LLCs electing S corp"),
        (misc_e["date"], "E-filed Forms 1099 other than 1099-NEC due to the IRS.", "Payers filing electronically"),
        ("2027-04-15", "Form 1040 with Schedule C and SE, and any balance due. Form 1120 for C corporations. First 2027 estimated payment. Form 4868 extends filing, not payment, to Oct. 15. NJ-1040 and NY IT-201 / IT-203 are due the same day.", "Sole proprietors, single-member LLCs, C corps"),
        ("2027-06-15", "Second 2027 estimated tax payment (federal, NJ and NY).", "Anyone paying estimates"),
        ("2027-09-15", "Third 2027 estimated payment. Extended Forms 1120-S and 1065 due.", "Estimates; extended S corps and partnerships"),
        ("2027-10-15", "Extended Form 1040 and Form 1120 due.", "Extended individual and C corp returns"),
    ]
    tr = "".join(f'<tr><td class="dt">{d(a, "%b %-d")}<br/><small style="font-family:Inter;font-size:6.6pt;color:#6b707a">{d(a, "%A, %Y")}</small></td><td>{b}</td><td class="who">{c}</td></tr>' for a, b, c in rows)
    p2 = page(2, "01 · Key dates", "Key tax dates for <em>2026 returns</em>",
              "Calendar-year businesses. These are the dates that cost money when they're missed: late-filing and late-payment penalties start the next day.",
              f'''<table><thead><tr><th>Date</th><th>What's due</th><th>Who it's for</th></tr></thead><tbody>{tr}</tbody></table>
<div class="box"><b>Before Dec. 31, 2026:</b> spending you want to deduct for 2026, like equipment, software and supplies, generally has to be paid (and equipment placed in service) by year-end. Talk it through before you buy just for the deduction.</div>
<div class="box"><b>Dates move.</b> When the IRS or a state announces disaster relief, deadlines shift for the affected area. Fiscal-year businesses have different dates. Save every date to your calendar: {link("/blog/2027-tax-calendar/", "mfa-advisory.com/blog/2027-tax-calendar")}.</div>''',
              f'Sources: IRS Publication 509 (draft for 2027), Form 1040-ES (2026), Instructions for Forms 1099-MISC and 1099-NEC, NJ Division of Taxation, NY Department of Taxation. Checked {asof_txt}.')

    # ---- 3. quarterly estimates
    q = "".join(f'<tr><td class="dt">{d(x, "%b %-d, %Y")}</td><td>{lbl}</td><td></td><td></td><td></td></tr>' for x, lbl in zip(EST26[3:] + EST27, ["Q4 2026", "Q1 2027", "Q2 2027", "Q3 2027", "Q4 2027"]))
    p3 = page(3, "02 · Estimates", "Quarterly estimated taxes, <em>in one page</em>",
              "No employer is withholding tax from business profit, so the IRS expects you to pay as you go, four times a year.",
              f'''<div class="cols3">
<div class="stat"><div class="v">{money(EST_THR)}</div><div class="t">Federal trigger</div><div class="d">Estimates are generally required if you expect to owe {money(EST_THR)} or more for 2026 after withholding and credits.</div></div>
<div class="stat"><div class="v">{money(NJ_THR)} / {money(NY_THR)}</div><div class="t">NJ / NY trigger</div><div class="d">New Jersey: if you expect to owe more than {money(NJ_THR)}. New York: {money(NY_THR)} or more of state, NYC or Yonkers tax.</div></div>
<div class="stat"><div class="v">{SE * 100:.1f}%</div><div class="t">Self-employment tax</div><div class="d">On {NEF * 100:.2f}% of net profit, on top of income tax. The Social Security part stops at {money(WAGE_BASE)} for 2026.</div></div></div>
<h2>Avoid the underpayment penalty: the safe harbors</h2>
<p>For 2026 you generally owe no federal underpayment penalty if your withholding and on-time estimates cover the smaller of:</p>
<ul class="ck"><li><b>{SH["current_year_pct"] * 100:.0f}% of your 2026 tax</b>, or</li>
<li><b>{SH["prior_year_pct"] * 100:.0f}% of your 2025 tax</b> ({SH["prior_year_pct_high_income"] * 100:.0f}% if your 2025 adjusted gross income was over {money(SH["high_income_agi_over"])}, or {money(SH["high_income_agi_over_mfs"])} if married filing separately).</li></ul>
<div class="box"><b>Quick example.</b> {money(EX_PROFIT)} of 2026 net profit means about {money(EX_SE)} of self-employment tax ({money(EX_PROFIT)} × {NEF * 100:.2f}% × {SE * 100:.1f}%) before any income tax. Half of the self-employment tax is deductible on your Form 1040. Run your own numbers with the {link("/tools/quarterly-estimated-tax-calculator/", "quarterly estimated tax calculator")}.</div>
<h2>Your payment tracker</h2>
<table class="ws"><thead><tr><th>Due date</th><th>Quarter</th><th>Planned</th><th>Paid on</th><th>Confirmation #</th></tr></thead><tbody>{q}</tbody></table>
<p class="fine" style="margin-top:6px">Pay federal estimates through IRS Direct Pay, EFTPS or your IRS Online Account; NJ and NY take payments on their own sites. The {d(EST27[3], "%b %-d, %Y")} date reflects a weekend and holiday; confirm when the 2027 forms are released.</p>''',
              f'Sources: IRS Form 1040-ES (2026); IRS Self-Employment Tax page; SSA contribution and benefit base; NJ-1040-ES and NY IT-2105 instructions. Checked {asof_txt}.')

    # ---- 4. deductions
    def ck(name, note):
        return f"<li><b>{name}</b><small>{note}</small></li>"
    left = "".join([
        ck("Home office", f"Simplified method: {money(HO_RATE)} per sq ft, up to {HO_MAX_SQ} sq ft ({money(HO_MAX)} max). The space must be used only and regularly for work."),
        ck("Business mileage", f"{MILE1 * 100:.1f}¢ a mile Jan. to June 2026, {MILE2 * 100:.0f}¢ July to Dec. Keep a log. Commuting never counts."),
        ck("Parking and tolls", "On business trips, on top of mileage."),
        ck("Phone and internet", "The business-use share of the bill."),
        ck("Software and subscriptions", "QuickBooks, Canva, Zoom and the like; business share only."),
        ck("Small equipment", "Items of $2,500 or less each (or per invoice) can be written off at once if you elect the de minimis safe harbor."),
        ck("Larger equipment", "Section 179 up to $2,560,000 for 2026, or 100% bonus depreciation for property acquired after Jan. 19, 2025."),
        ck("Business meals", "50% with a client or contact, with a real business purpose."),
        ck("Travel away overnight", "Flights, hotels and rides in full; meals on the trip at 50%."),
        ck("Contractors", "In full. Send a 1099-NEC at $2,000 or more for 2026 payments."),
    ])
    right = "".join([
        ck("Self-employed health insurance", "Premiums for you and your family, if the business made a profit."),
        ck("Retirement savings", "SEP-IRA: the lesser of 25% of pay or $72,000 for 2026. Solo 401(k): $24,500 deferral, plus $8,000 at 50 or older."),
        ck("Half of self-employment tax", "Deducted on your Form 1040; it lowers income tax."),
        ck("Startup costs", "Up to $5,000 in your first year, phased out above $50,000 of costs; the rest over 180 months."),
        ck("Bank and card processing fees", "Stripe, Square and PayPal fees on business sales."),
        ck("Accounting, legal and tax-prep fees", "Business share in full."),
        ck("Advertising and marketing", "Ads, website, business cards."),
        ck("Client gifts", "Up to $25 per person per year."),
        ck("Business insurance", "Liability, property, professional coverage."),
        ck("Courses and training", "When they keep up skills for the work you already do."),
    ])
    no = "".join(f"<li><b>{a}</b><small>{b}</small></li>" for a, b in [
        ("Commuting", "Home to your regular workplace."), ("Entertainment", "Game tickets, golf, shows, even with a client."),
        ("Fines and penalties", "Parking tickets, IRS penalties."), ("Club and gym dues", "Social, athletic and fitness clubs."),
        ("Snacks and meals for staff at work", "New for 2026: no longer deductible, with narrow exceptions.")])
    p4 = page(4, "03 · Deductions", "Deduction checklist <em>for 2026</em>",
              "Tick what applies to you, then make sure your books show it. Each item needs a receipt or record: date, amount, who and the business purpose.",
              f'''<div class="cols"><ul class="ck">{left}</ul><ul class="ck">{right}</ul></div>
<h3>Common traps: not deductible</h3><ul class="ck no" style="columns:2;column-gap:.3in">{no}</ul>
<div class="box"><b>Not sure about an expense?</b> Search {len(DED)} common expenses, with the limits and records to keep, on {link("/tools/is-it-deductible/", "mfa-advisory.com/tools/is-it-deductible")}.</div>''',
              f'Sources: IRS Publications 463, 587, 946, 560 and 15-B; Schedule C instructions; IRS standard mileage rates (Notice 2026-10, Announcement 2026-11). Checked {asof_txt}.')

    # ---- 5. 1099
    items = "".join(f"<li><b>{a}</b><small>{b}</small></li>" for a, b in [
        ("List everyone you paid for services in 2026", "Freelancers, contractors, attorneys, landlords, repair and cleaning services."),
        ("Take out card and payment-app payments", "Paid by credit card, PayPal Goods & Services, Stripe or Square? The processor reports those on Form 1099-K, not you."),
        ("Check each payee's Form W-9", "Individuals, sole proprietors and LLCs taxed as partnerships generally get a 1099. Corporations generally don't, except attorneys and medical providers."),
        ("Collect missing W-9s now", "Before January, when people are slow to answer. Use a secure upload, not plain email, since the form has a tax ID."),
        ("Total what you paid each payee", "Flag anyone at $2,000 or more for services, rent or other income; $10 or more in royalties; $600 or more in gross proceeds to an attorney."),
        ("Check names and tax IDs match", "A mismatch can bring IRS notices and backup withholding."),
        ("Choose how you'll file", "The IRS IRIS portal or a provider such as QuickBooks. E-filing is required if you file 10 or more information returns in total."),
        ("Send 1099-NECs by " + d(nec["date"], "%b %-d, %Y"), "To each payee and to the IRS. There is no automatic extension."),
        ("Send 1099-MISCs on time", f"Payee copies by {d(nec['date'], '%b %-d, %Y')} (Feb. 16, 2027 for box 8 or 10); IRS by {d(misc_paper['date'], '%b %-d')} on paper or {d(misc_e['date'], '%b %-d, %Y')} electronically."),
        ("Check your state", "Some states, including New Jersey, need their own copy or annual reconciliation."),
        ("Withheld tax because there was no tax ID?", "Then you file the 1099 whatever the amount."),
    ])
    p5 = page(5, "04 · 1099s", "1099 readiness <em>checklist</em>",
              "For payments made in 2026, filed in early 2027. The big change: the threshold for most 1099s went from $600 to $2,000.",
              f'''<div class="cols3">
<div class="stat"><div class="v">$2,000</div><div class="t">1099-NEC / 1099-MISC</div><div class="d">Services, rent, medical and other income paid in 2026 ($600 for 2025 payments).</div></div>
<div class="stat"><div class="v">{d(nec["date"], "%b %-d")}</div><div class="t">1099-NEC deadline</div><div class="d">To contractors and the IRS, {d(nec["date"], "%A, %B %-d, %Y")}.</div></div>
<div class="stat"><div class="v">$20,000</div><div class="t">1099-K (processors)</div><div class="d">Plus more than 200 transactions. Card and app payments you make are on the processor's form.</div></div></div>
<h2 style="margin-top:12px">Work through it in this order</h2>
<ul class="ck">{items}</ul>
<div class="box"><b>Payee by payee:</b> the {link("/tools/do-i-need-to-send-a-1099/", "Do I need to send a 1099? checker")} answers it in four questions, and the {link("/tools/w-9-request-email-template/", "W-9 request email templates")} are ready to copy.</div>''',
              f'Sources: IRS Instructions for Forms 1099-MISC and 1099-NEC; IRS IR-2025-107 (Form 1099-K); IRS Backup withholding; About Form W-9. Checked {asof_txt}.')

    # ---- 6. monthly close
    steps = "".join(f"<li><b>{a}</b><span>{b}</span></li>" for a, b in [
        ("Download every statement", "Each bank, credit card, loan and payment app (PayPal, Stripe, Square, Venmo business) for the month."),
        ("Categorize every transaction", "Nothing left in \"uncategorized\" or \"ask my accountant\". Split mixed charges."),
        ("Reconcile each account", "Your books should match each statement's ending balance to the cent. Investigate any difference now, not in March."),
        ("Match receipts", "Attach or file receipts and note the business purpose for meals, travel and anything unusual."),
        ("Separate personal from business", "Record owner draws and contributions; move personal charges out of business expenses."),
        ("Review who owes you", "Follow up on invoices more than 30 days old."),
        ("Review what you owe", "Schedule bills; check nothing was paid twice."),
        ("Record the non-obvious", "Payroll, loan payments split into principal and interest, processor fees netted from deposits."),
        ("Read your P&amp;L and balance sheet", "Compare with last month and last year. Ask why anything moved a lot."),
        ("Set aside tax", "Move your estimate share to a separate tax savings account and note the next due date (page 3)."),
    ])
    p6 = page(6, "05 · Bookkeeping", "A 10-step <em>monthly close</em>",
              "Clean monthly books are what make tax season short. Pick the same day each month, for example the 10th, and work down the list.",
              f'''<ol class="steps">{steps}</ol>
<div class="cols" style="margin-top:10px"><div class="box" style="margin:0"><b>At year-end, add:</b> count inventory, list equipment bought during the year with dates and costs, total your mileage log, and confirm every contractor's W-9 (page 5).</div>
<div class="box" style="margin:0"><b>Behind already?</b> Catch up oldest month first and reconcile as you go. If it's more than a few months, a one-time cleanup is usually faster: {link("/bookkeeping-cleanup/", "mfa-advisory.com/bookkeeping-cleanup")}.</div></div>''',
              'Practice checklist from Merchant Financial Advisory. Software menus differ; the steps work in QuickBooks Online, Xero or a spreadsheet.')

    # ---- 7. LLC vs S corp
    p7 = page(7, "06 · Entity choice", "LLC vs S corp: <em>when it's worth a look</em>",
              "An S corporation is a tax election, not a different kind of company. An LLC can keep its default tax treatment or elect S corp status on Form 2553.",
              f'''<div class="cols"><div><h3>Default LLC (sole owner)</h3><p>Profit goes on Schedule C. All of it is subject to self-employment tax of {SE * 100:.1f}% on {NEF * 100:.2f}% of net profit (the Social Security part up to {money(WAGE_BASE)} for 2026), plus income tax.</p></div>
<div><h3>LLC taxed as an S corp</h3><p>You pay yourself a <b>reasonable salary</b> through payroll, and Social Security and Medicare apply to that salary. The rest of the profit passes to you on a K-1 without self-employment tax. You file Form 1120-S by {d(s_ret["date"], "%B %-d, %Y")}.</p></div></div>
<h2>An illustration, not a recommendation</h2>
<table><thead><tr><th></th><th>Default LLC</th><th>S corp election</th></tr></thead><tbody>
<tr><td>Net profit before owner pay</td><td>{money(SC_PROFIT)}</td><td>{money(SC_PROFIT)}</td></tr>
<tr><td>Owner salary through payroll</td><td>None</td><td>{money(SC_SALARY)}</td></tr>
<tr><td>Self-employment or payroll tax</td><td>{money(SC_LLC_SE)} (SE tax)</td><td>{money(SC_PAYROLL)} (employee + employer shares)</td></tr>
<tr><td><b>Difference before added costs</b></td><td colspan="2"><b>about {money(SC_DIFF)} a year</b>, before payroll service fees, the 1120-S return, state taxes and fees, and income tax effects</td></tr></tbody></table>
<div class="cols" style="margin-top:8px"><div><h3>Worth a look when</h3><ul class="ck">
<li>Profit is steady and well above a reasonable salary for your role</li><li>You're ready to run payroll every month, on time</li>
<li>Your books are clean and business money has its own account</li><li>You expect the business to keep earning at this level</li></ul></div>
<div><h3>Probably not yet when</h3><ul class="ck no">
<li>Profit is small, uneven or still unknown</li><li>You'd pay yourself an unrealistically low salary to make it work</li>
<li>Payroll filings and a separate return feel like a burden</li><li>You live or work in a state where the election adds tax or fees</li></ul></div></div>
<div class="box"><b>Timing:</b> to be taxed as an S corp for all of 2027, a calendar-year business generally files Form 2553 by {d(s_2553["date"], "%B %-d, %Y")}. New Jersey and New York have their own S corp rules, so check both before electing. Try the {link("/tools/s-corp-tax-savings-calculator/", "S corp vs LLC savings estimator")} with your numbers.</div>''',
              f'Sources: IRS Self-Employment Tax page; SSA contribution and benefit base; IRS Instructions for Form 2553 and Form 1120-S; IRS Publication 509 (draft for 2027). Illustration uses 2026 rates. Checked {asof_txt}.')

    # ---- 8. hand-off
    srcs = [("IRS Form 1040-ES (2026)", "https://www.irs.gov/pub/irs-pdf/f1040es.pdf"),
            ("IRS Publication 509, draft for 2027", "https://www.irs.gov/pub/irs-dft/p509--dft.pdf"),
            ("IRS Self-employment tax", "https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-and-medicare-taxes"),
            ("IRS Instructions for Forms 1099-MISC and 1099-NEC", "https://www.irs.gov/instructions/i1099mec"),
            ("IRS Form 1099-K threshold FAQs", "https://www.irs.gov/newsroom/irs-issues-faqs-on-form-1099-k-threshold-under-the-one-big-beautiful-bill-dollar-limit-reverts-to-20000"),
            ("IRS Standard mileage rates", "https://www.irs.gov/tax-professionals/standard-mileage-rates"),
            ("IRS Publication 587, Business use of your home", "https://www.irs.gov/publications/p587"),
            ("IRS Publication 463, Travel, gift and car expenses", "https://www.irs.gov/publications/p463"),
            ("IRS Publication 946, Depreciation", "https://www.irs.gov/publications/p946"),
            ("IRS Publication 560, Retirement plans", "https://www.irs.gov/publications/p560"),
            ("SSA Contribution and benefit base", "https://www.ssa.gov/oact/cola/cbb.html"),
            ("NJ-1040-ES instructions", "https://www.nj.gov/treasury/taxation/pdf/current/1040esi.pdf"),
            ("NY IT-2105 instructions", "https://www.tax.ny.gov/pdf/current_forms/it/it2105i.pdf")]
    src_li = "".join(f'<li><a href="{esc(u)}">{esc(t)}</a></li>' for t, u in srcs)
    p8 = page(8, "07 · Next step", "When you'd rather <em>hand it off</em>",
              "This kit covers the basics. If your situation has more moving parts, or you'd simply rather not do it yourself, this is what we do every day.",
              f'''<div class="svc">
<div><h4>Business tax returns</h4><p class="pr">Quoted up front</p><p>Schedule C, Form 1065 and Form 1120-S, plus quarterly estimates and year-end planning. Federal, New Jersey and New York.</p></div>
<div><h4>Monthly bookkeeping</h4><p class="pr">From $199 a month</p><p>One bank account, one card and up to 100 transactions a month, reconciled and closed every month. Bigger books quoted up front.</p></div>
<div><h4>LLC formation</h4><p class="pr">From $150 plus the state fee</p><p>State filing, EIN and operating agreement, in any state. Tax registration and bookkeeping setup come in the larger packages.</p></div></div>
<div class="book"><div><h2>Book a 30-minute consultation</h2><p>On Google Meet. Bring your questions and, if you like, a recent statement or last year's return. You'll leave knowing what to fix first.</p></div>
<a class="btn" href="{esc(SITE + "/book/?" + UTM)}">mfa-advisory.com/book</a></div>
<h3>Who you'll talk to</h3>
<p><b>Zain Merchant</b>, founder of Merchant Financial Advisory, with about seven years in accounting and audit.</p>
<div class="cred"><span>CPA candidate</span><span>ACCA</span><span>Big Four (ex-PwC)</span><span>PTIN/EFIN tax preparer</span></div>
<p>{link("/book/", "mfa-advisory.com/book")} · <a href="mailto:info@mfa-advisory.com">info@mfa-advisory.com</a> · (347) 205-4468 · Princeton, NJ, serving New Jersey, New York and clients nationwide</p>
<h3 style="margin-top:12px">Sources for this kit</h3><ul class="srcs">{src_li}</ul>
<p class="fine" style="margin-top:8px">This kit is general information for the 2026 tax year, not tax, legal or accounting advice, and it doesn't create a client relationship. Figures were checked against the sources above as of {asof_txt}; tax rules change and depend on your facts. Merchant Financial Advisory LLC does not provide legal advice and is not affiliated with the IRS. © {date.today().year} Merchant Financial Advisory LLC.</p>''',
              "Prices as shown on mfa-advisory.com/services. Every engagement starts with a written scope and a price agreed before work begins.")

    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"/><title>2026 Small Business Tax Starter Kit | Merchant Financial Advisory</title>
<meta name="author" content="Merchant Financial Advisory"/><style>{CSS}</style></head><body>
{cover}{p2}{p3}{p4}{p5}{p6}{p7}{p8}</body></html>'''


def main():
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(build_html(), encoding="utf-8")
    low = OUT_HTML.read_text(encoding="utf-8").lower()
    import re
    for bad in (r"\bfree\b", r"\bcpa firm\b", r"\bcertified public\b"):
        if re.search(bad, re.sub(r"<[^>]+>", " ", low)):
            sys.exit(f"banned wording {bad} in the kit")
    KIT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = KIT_DIR / KIT_FILE
    subprocess.run(["node", str(ROOT / "tools" / "render_pdf.js"), str(OUT_HTML), str(pdf)], check=True)
    print("kit:", OUT_HTML.relative_to(ROOT), "->", pdf.relative_to(ROOT), f"({pdf.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
