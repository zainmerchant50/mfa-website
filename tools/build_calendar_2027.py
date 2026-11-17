#!/usr/bin/env python3
"""/tools/2027-tax-calendar/ (Site, 2026-11-17). Zain: "create an entire tax calendar ... calendar year 2027 with key tax
dates for 2026 tax returns but also include relevant dates for 2027 as well" (site page + printable product; federal + NJ + NY).

Month-by-month view of every date in data/tax-calendar-2027.json (all entities merged, verified by Blog against the IRS draft
Pub 509 for 2027, NJ and NY sources). Everything is in the HTML (SEO / AI answers); JS only filters, highlights and makes
.ics files (MFA.pages.cal2027 in site/resources/calc.js). Each date is tagged "2026 return" or "2027 tax year".
The printable PDF product is rendered from the same data by tools/render_calendar_2027.py.
Registered in build_calculators.py (reg + RELATED). Never "free", never "CPA", no prices.
"""
import calendar as pycal
import json
import re
from datetime import date

import build_calculators as C
import lead_box
from build_resources import esc

ENTS = {k: t for k, t, _ in C.ENTITY_INFO}
SHORT = {"sole_proprietor": "Self-employed", "partnership": "Partnership", "s_corporation": "S corp", "c_corporation": "C corp",
         "employer": "Employer", "nonprofit": "Nonprofit", "sales_tax_seller": "Sales tax"}
JL = {"federal": "IRS", "NJ": "NJ", "NY": "NY"}


def tax_year(form, what):
    t = form + " " + what
    has26, has27 = "2026" in t, bool(re.search(r"2027|\bQ[123]\b", t))
    if has26 and has27:
        return "both"
    return "2027" if has27 else "2026"


def events():
    """Unique events (date, jurisdiction, form) with the entity types they apply to, in date order."""
    seen = {}
    for ent, lst in C.CAL["entities"].items():
        for e in lst:
            k = (e["date"], e["jurisdiction"], e["form"])
            if k not in seen:
                seen[k] = dict(e, ents=[])
            seen[k]["ents"].append(ent)
    out = sorted(seen.values(), key=lambda e: (e["date"], {"federal": 0, "NJ": 1, "NY": 2}[e["jurisdiction"]], e["form"]))
    for e in out:
        e["ty"] = tax_year(e["form"], e["what"])
    return out


YT = {"2026": "2026 return", "2027": "2027 tax year", "both": "2026 + 2027"}


def month_card(y, m, evs):
    first = date(y, m, 1)
    days = pycal.monthrange(y, m)[1]
    on = {e["date"] for e in evs}
    cells = "".join(f'<span class="cm-h">{d}</span>' for d in "MTWTFSS")
    cells += '<span class="cm-x"></span>' * first.weekday()
    for d in range(1, days + 1):
        iso = f"{y}-{m:02d}-{d:02d}"
        cells += f'<span class="cm-d{" on" if iso in on else ""}" data-date="{iso}">{d}</span>'
    lis = ""
    for i, e in enumerate(evs):
        dd = date.fromisoformat(e["date"])
        note = f' <small>{esc(e["note"])}</small>' if e.get("note") else ""
        who = ", ".join(SHORT[x] for x in e["ents"])
        lis += (f'<li data-ents="{" ".join(e["ents"])}" data-j="{e["jurisdiction"]}" data-ty="{e["ty"]}" data-date="{e["date"]}">'
                f'<span class="ce-d">{dd.strftime("%b")} {dd.day}<em>{dd.strftime("%a")}</em></span>'
                f'<span class="ce-b"><span class="ce-tags"><b class="j-{e["jurisdiction"]}">{JL[e["jurisdiction"]]}</b><i class="ty-{e["ty"]}">{YT[e["ty"]]}</i></span>'
                f'<strong>{esc(e["form"])}</strong> {esc(e["what"])}{note}<span class="ce-who">{esc(who)} · '
                f'<a href="{esc(e["source_url"])}" target="_blank" rel="noopener">source</a> · <button type="button" class="ce-add" data-i="{e["_i"]}">Add to calendar</button></span></span></li>')
    name = first.strftime("%B %Y")
    return (f'<section class="cm" id="m-{y}-{m:02d}" aria-label="{name}"><h3>{name}</h3><div class="cm-g" aria-hidden="true">{cells}</div>'
            f'<ul class="ce">{lis}</ul><p class="cm-none" hidden>No dates for your filters this month.</p></section>')


CSS = """<style>
.cal-wrap{max-width:var(--maxw,1180px);margin:0 auto;padding:0 24px}
.cal-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:8px 0 28px}
.cm{background:#fff;border:1px solid rgba(21,21,21,.1);border-radius:18px;padding:16px 16px 10px;break-inside:avoid}
.cm h3{font-size:1.15rem;margin:0 0 10px;color:var(--navy)}
.cm-g{display:grid;grid-template-columns:repeat(7,1fr);gap:3px;margin-bottom:12px;font-size:.78rem;text-align:center}
.cm-h{font-weight:700;color:var(--muted);font-size:.68rem}
.cm-d{padding:4px 0;border-radius:7px;color:var(--ink)}
.cm-d.on{background:var(--gold);color:#fff;font-weight:700}
.ce{list-style:none;margin:0;padding:0}
.ce li{display:grid;grid-template-columns:54px 1fr;gap:10px;padding:9px 0;border-top:1px solid rgba(21,21,21,.08);font-size:.86rem;line-height:1.45}
.ce li[hidden]{display:none}
.ce-d{font-weight:700;color:var(--navy);line-height:1.2}.ce-d em{display:block;font-style:normal;font-weight:400;color:var(--muted);font-size:.75rem}
.ce-tags{display:flex;gap:6px;margin-bottom:3px}
.ce-tags b,.ce-tags i{font-style:normal;font-size:.66rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;border-radius:6px;padding:2px 6px}
.ce-tags b{background:var(--navy);color:#fff}.ce-tags b.j-NJ{background:#2f6f5e}.ce-tags b.j-NY{background:#6b3f8f}
.ce-tags i{background:#f3eee2;color:#7a6326}.ce-tags i.ty-2027{background:#e7eef8;color:#1f4a7a}
.ce-who{display:block;color:var(--muted);font-size:.78rem;margin-top:3px}
.ce-who a{color:var(--muted)}
.ce-add{background:none;border:0;padding:0;font:inherit;color:var(--navy);text-decoration:underline;cursor:pointer}
.cm-none{color:var(--muted);font-size:.85rem}
.cal-chips{display:flex;flex-wrap:wrap;gap:8px}
.cal-chips label{display:inline-flex;align-items:center;gap:6px;border:1px solid rgba(21,21,21,.16);border-radius:999px;padding:7px 12px;font-size:.86rem;cursor:pointer;background:#fff}
.cal-chips input{accent-color:var(--gold)}
.fld .cal-chips label{text-transform:none;letter-spacing:0;font-weight:500;font-size:.86rem;color:var(--ink);margin:0}
.tres #c-print{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.45)}
@media(max-width:980px){.cal-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:640px){.cal-grid{grid-template-columns:1fr}.cal-wrap{padding:0 16px}}
@media print{nav,header.th,.tool,.tinfo,.cta-block,.relnav,.lbx,.lbx-sticky,footer,#shop-products,.ce-add,.ce-who a{display:none!important}
body{background:#fff}.cal-grid{grid-template-columns:repeat(2,1fr);gap:10px}.cm{border-color:#bbb}.cal-wrap h2{margin-top:0}}
</style>"""


def build():
    slug = "2027-tax-calendar"
    f = C.Facts()
    evs = events()
    for i, e in enumerate(evs):
        e["_i"] = i
        f.used.append(e)
    months = [(2027, m) for m in range(1, 13)] + [(2028, 1)]
    cards = "".join(month_card(y, m, [e for e in evs if e["date"].startswith(f"{y}-{m:02d}")]) for y, m in months)
    chips = "".join(f'<label><input type="checkbox" class="f-ent" value="{k}" checked/>{esc(SHORT[k])}</label>' for k in ENTS)
    grid = (CSS + '<div class="tcard"><h2>Show dates for</h2><p class="sub">Calendar-year filers. Untick what doesn\'t apply to you.</p>'
            f'<p class="factline">Facts checked {C.day(C.CAL["meta"]["checked"])}</p>'
            f'<div class="fld"><span class="lbl">Who files</span><div class="cal-chips">{chips}</div></div>'
            '<div class="fld"><span class="lbl">Where</span><div class="cal-chips">'
            '<label><input type="checkbox" class="f-j" value="federal" checked/>Federal (IRS)</label>'
            '<label><input type="checkbox" class="f-j" value="NJ" checked/>New Jersey</label>'
            '<label><input type="checkbox" class="f-j" value="NY" checked/>New York</label></div></div>' +
            C.select("f-ty", "Tax year", [("all", "Everything in 2027"), ("2026", "Only 2026 returns and payments"), ("2027", "Only 2027 tax year dates")]) +
            '</div>'
            '<div class="tcard tres"><h2>Your 2027 calendar</h2><p class="sub" id="rsub">Every date for 2027.</p>'
            '<div class="kpis"><div class="kpi wide gold"><b id="k-next">—</b><span>Next deadline</span></div>'
            '<div class="kpi"><b id="k-count">—</b><span>Dates shown</span></div><div class="kpi"><b id="k-2026">—</b><span>For 2026 returns</span></div></div>'
            '<div class="acts"><button type="button" class="btn btn-gold" id="c-all">Add these dates to my calendar (.ics)</button>'
            '<button type="button" class="btn btn-line" id="c-print">Print or save as PDF</button></div>'
            '<p class="muted">The .ics file works in Apple Calendar, Outlook and Google Calendar, with a reminder 7 days before each date.</p>'
            '<p class="muted">General information, not tax advice.</p></div>')
    below = (f'<section class="cal-wrap" aria-labelledby="cal-h"><h2 id="cal-h">2027 tax calendar, month by month</h2>'
             f'<div class="cal-grid">{cards}</div></section>')
    n26 = sum(1 for e in evs if e["ty"] != "2027")
    info = f"""<h2>What are the key tax deadlines in 2027?</h2>
<p><strong>The big ones: January 15 (last 2026 estimated payment), February 1 (W-2s and 1099-NECs), March 15 (partnership and S corp returns, and the S corp election for 2027), April 15 (individual and C corp returns, plus the first 2027 estimated payment), June 15 and September 15 (2027 estimates), and October 15 (extended individual and C corp returns).</strong> This calendar lists {len(evs)} federal, New Jersey and New York dates in all, {n26} of them for 2026 returns and payments.</p>
<h2>How to use this calendar</h2>
<ul><li><strong>Filter</strong> by who files (self-employed, partnership, S corp, C corp, employer, nonprofit, sales tax seller), by federal, NJ or NY, and by tax year.</li>
<li><strong>Add to your calendar</strong> one date or everything you see, with a 7-day reminder.</li>
<li><strong>Weekends and holidays</strong> are already applied: a date that falls on a weekend or legal holiday moves to the next business day (for example, January 18, 2028 for the last 2027 estimate).</li>
<li><strong>Disaster relief</strong> can push a date back. Check the source link before relying on it.</li></ul>
<p>Work out each estimated payment with the <a href="/tools/quarterly-estimated-tax-calculator/">quarterly estimated tax calculator</a>. Want only your entity? Use <a href="/tools/tax-deadlines-2027/">2027 deadlines by entity</a>, or read the <a href="/blog/2027-tax-calendar/">2027 tax calendar article</a>.</p>"""
    data = {"ev": [{"date": e["date"], "j": e["jurisdiction"], "form": e["form"], "what": e["what"], "ty": e["ty"], "ents": e["ents"], "note": e.get("note", "")} for e in evs]}
    lead = lead_box.lead_box("2027 tax calendar", "calendar-2027", "Want us to handle the dates for you?",
                             "We file the returns, make the payments on time and remind you before each deadline.",
                             [("tax-return", "2026 tax return"), ("estimates", "Quarterly estimated taxes for 2027"), ("payroll-1099", "1099s, W-2s or payroll filings"),
                              ("bookkeeping", "Monthly bookkeeping"), ("question", "A quick question first")],
                             ["A fixed quote before any work starts", "Federal, New Jersey and New York"], sticky=False)
    return C.build_page(slug, "2027 Tax Calendar: Federal, NJ & NY Dates by Month",
                        "Every 2027 tax deadline by month: 2026 returns, 1099s, W-2s, estimated taxes, payroll and sales tax, federal, New Jersey and New York.",
                        "2027 tax calendar", "2027 tax calendar",
                        "Every 2027 date, month by month: 2026 returns and payments, plus 2027 estimates, payroll and sales tax. Federal, New Jersey and New York.",
                        grid, below, info, data, "cal2027", f, "Never miss a 2027 deadline",
                        "We track your dates, prepare the filings and make the payments on time. Book a 30-minute consultation.",
                        extra_note="Federal dates are checked against the IRS draft Publication 509 for 2027. ", lead=lead)
