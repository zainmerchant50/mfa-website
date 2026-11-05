#!/usr/bin/env python3
"""Shop card images (site/shop/img/<slug>.webp, 400x400) for products that have none yet, in the house style:
navy card, gold frame, MFA brandline, gold pill, Cormorant title with an italic gold second line, and paper
mock-ups of what's inside. HTML goes to content/graphics/shop-<slug>.html (uses _base.css + logo.png) and is
rendered by tools/render_graphics.js (Playwright) at 1000x1000, then saved as:
  site/shop/img/<slug>.webp   400px (what /shop/ shows)
  site/feeds/img/<slug>.jpg   800px (Pinterest catalog image; build_pinterest_catalog.py keeps it while newer)
Mock-ups show only what the product contains (from its catalog blurb); sample figures are illustrative.
Usage: python3 tools/build_shop_images.py [slug ...]   (no args = every product listed in PRODUCTS)
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GFX = ROOT / "content" / "graphics"
SHOP = ROOT / "site" / "shop" / "img"
FEED = ROOT / "site" / "feeds" / "img"

CSS = """
:root{--w:1000px;--h:1000px}
body{background:#0C1B31;position:relative}
.card{position:absolute;inset:44px;border-radius:30px;border:1.5px solid rgba(216,183,105,.32);overflow:hidden;
 background:radial-gradient(110% 90% at 100% 0%,#1B3557 0%,#12284A 50%,#0E2141 100%)}
.in{position:absolute;left:58px;top:52px;right:58px}
.brandline img{width:54px;height:54px;border-radius:13px}
.brandline b{font-size:30px}.brandline i{font-size:11px}
.pill{display:inline-block;margin-top:44px;font-size:13px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
 color:var(--navy);background:var(--gold-b);padding:9px 16px;border-radius:999px}
h1{font-family:Cormorant,serif;font-weight:400;font-size:70px;line-height:1.02;margin-top:24px;color:#fff}
h1 em{display:block;color:var(--gold-b);font-style:italic}
.stage{position:absolute;left:-14px;right:0;bottom:-40px;height:560px;transform:scale(1.16);transform-origin:0 0}
.sheet{position:absolute;background:var(--paper);color:var(--ink);border-radius:10px;
 box-shadow:0 24px 60px rgba(0,0,0,.45),0 2px 6px rgba(0,0,0,.3);overflow:hidden;font-size:12px}
.sheet .hd{background:var(--navy);color:#fff;padding:10px 14px;font-size:12px;font-weight:600;letter-spacing:.04em;display:flex;justify-content:space-between}
.sheet .hd span{color:var(--gold-b);font-weight:700;letter-spacing:.14em;font-size:10px;text-transform:uppercase}
.sheet h3{font-size:13px;font-weight:700;color:var(--navy);padding:12px 14px 6px}
table{width:100%;border-collapse:collapse}
th{background:var(--gold-b);color:var(--navy);font-size:10.5px;font-weight:700;text-align:left;padding:6px 8px;letter-spacing:.02em}
td{padding:6px 8px;border-bottom:1px solid rgba(21,21,21,.08);font-size:11.5px;white-space:nowrap}
td.n{text-align:right;font-variant-numeric:tabular-nums}
tr:nth-child(even) td{background:#F5F4EF}
tr.tot td{font-weight:700;color:var(--navy);background:#FBF3DE;border-top:1.5px solid var(--gold)}
.doc{padding:0 0 10px}
.doc .t{font-family:Cormorant,serif;font-size:26px;color:var(--navy);padding:16px 18px 2px;line-height:1.05}
.doc .t em{color:var(--gold);font-style:italic}
.doc .s{font-size:10.5px;color:#6b6b6b;padding:0 18px 10px}
.ck{display:flex;gap:10px;align-items:flex-start;padding:8px 18px;border-top:1px solid rgba(21,21,21,.07)}
.ck i{flex:0 0 15px;height:15px;border:1.5px solid var(--gold);border-radius:3px;margin-top:1px;position:relative}
.ck i.on:after{content:"";position:absolute;left:4px;top:0;width:4px;height:9px;border:solid var(--navy);border-width:0 2px 2px 0;transform:rotate(45deg)}
.ck b{display:block;font-size:12px;color:var(--navy)}
.ck span{display:block;font-size:10.5px;color:#555;margin-top:2px;line-height:1.35;white-space:normal}
.tagrow{position:absolute;left:58px;bottom:40px;display:flex;gap:8px}
.tagrow span{font-size:12px;font-weight:500;color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:6px 12px;background:rgba(12,27,49,.75)}
.letter{padding:18px 20px;font-size:11px;line-height:1.55;color:#333}
.letter .lh{font-weight:700;color:var(--navy);font-size:12px;margin-bottom:8px}
.letter .ln{height:7px;background:#E7E4DA;border-radius:4px;margin:7px 0}
.letter .ln.s{width:62%}.letter .ln.m{width:84%}
.chip{display:inline-block;font-size:9.5px;font-weight:700;letter-spacing:.08em;padding:2px 7px;border-radius:999px}
.chip.g{background:#E3F1E6;color:#22663A}.chip.y{background:#FBF0D2;color:#8A6412}.chip.b{background:#E2E9F4;color:#1B3557}
"""

HEAD = '<!doctype html><html><head><meta charset="utf-8"/><link rel="stylesheet" href="_base.css"/><style>{css}</style></head><body>'
TOP = ('<div class="card"><div class="in"><div class="brandline"><img src="logo.png"/><span><b>Merchant</b><i>Financial Advisory</i>'
       '</span></div><span class="pill">{pill}</span><h1>{t1}<em>{t2}</em></h1></div><div class="stage">{stage}</div>'
       '<div class="tagrow">{tags}</div></div></body></html>')


def table(cols, rows, tot=None, num=()):
    h = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f'<td class="n">{v}</td>' if i in num else f"<td>{v}</td>" for i, v in enumerate(r)) + "</tr>"
    if tot:
        body += '<tr class="tot">' + "".join(f'<td class="n">{v}</td>' if i in num else f"<td>{v}</td>" for i, v in enumerate(tot)) + "</tr>"
    return f"<table><tr>{h}</tr>{body}</table>"


def sheet(style, title, tag, inner):
    return f'<div class="sheet" style="{style}"><div class="hd">{title}<span>{tag}</span></div>{inner}</div>'


def checks(items):
    return "".join(f'<div class="ck"><i class="{"on" if on else ""}"></i><div><b>{b}</b><span>{s}</span></div></div>'
                   for on, b, s in items)


PRODUCTS = {
    "artist-tax-sales-tracker-2026": dict(
        pill="Artists · Schedule C · 2026", t1="Artist Tax &amp;", t2="Sales Tracker",
        tags=["Excel", "PDF guide", "Tax year 2026"],
        stage=sheet("left:505px;top:30px;width:375px;transform:rotate(4deg)", "Schedule C summary", "2026",
                    "<h3>Profit or loss from your art business</h3>" + table(
                        ["Line", "Amount"],
                        [["Gross sales (all channels)", "18,420"], ["Fees &amp; commissions", "1,236"], ["Cost of goods sold", "3,905"],
                         ["Booth &amp; show costs", "1,150"], ["Car / mileage", "842"], ["Home studio", "1,500"]],
                        ["Net profit", "9,787"], num=(1,)))
        + sheet("left:62px;top:70px;width:480px;transform:rotate(-2.5deg)", "Sales by channel", "Tracker",
                table(["Date", "Piece", "Channel", "Sale", "Fees", "COGS"],
                      [["Mar 02", "Harbor print #4", "Etsy", "85.00", "8.92", "14.20"],
                       ["Mar 09", "Study in blue", "Website", "240.00", "7.26", "38.00"],
                       ["Apr 13", "Mini set (3)", "Art fair", "120.00", "0.00", "21.50"],
                       ["Apr 20", "Pet portrait", "Commission", "350.00", "10.45", "26.00"],
                       ["May 04", "Harbor print #5", "Etsy", "85.00", "8.92", "14.20"],
                       ["May 18", "Tote bag", "Art fair", "32.00", "0.00", "9.40"],
                       ["Jun 01", "Garden diptych", "Website", "410.00", "12.19", "62.00"]],
                      ["", "Year to date", "", "1,322", "47.74", "185.30"], num=(3, 4, 5)))),
    "art-fair-sales-tax-permit-planner": dict(
        pill="Art fairs · NJ NY PA DE MD CT", t1="Art Fair Sales Tax", t2="&amp; Permit Planner",
        tags=["Excel", "PDF guide", "Official state links"],
        stage=sheet("left:525px;top:40px;width:345px;transform:rotate(4deg)", "Price tag calculator", "Tax included",
                    "<h3>Sticker price with sales tax built in</h3>" + table(
                        ["State", "Rate", "Tag", "Pre-tax"],
                        [["NJ", "6.625%", "50.00", "46.89"], ["NY (local)", "8.875%", "50.00", "45.92"],
                         ["PA", "6.00%", "50.00", "47.17"], ["MD", "6.00%", "50.00", "47.17"], ["CT", "6.35%", "50.00", "47.01"]],
                        num=(1, 2, 3)))
        + sheet("left:62px;top:72px;width:500px;transform:rotate(-2.5deg)", "Show-by-show log", "Planner",
                table(["Show", "State", "Dates", "Permit", "Register by", "Status"],
                      [["Spring Arts Fest", "NJ", "Apr 18-19", "NJ-REG", "Mar 20", '<span class="chip g">Done</span>'],
                       ["Riverside Market", "PA", "May 9", "PA sales tax", "Apr 10", '<span class="chip g">Done</span>'],
                       ["Harbor Craft Show", "MD", "Jun 6-7", "Temp. vendor", "May 8", '<span class="chip y">Apply</span>'],
                       ["Village Art Walk", "NY", "Jul 11", "Cert. of Auth.", "Jun 11", '<span class="chip y">Apply</span>'],
                       ["Shoreline Fair", "DE", "Aug 1-2", "Business lic.", "Jul 1", '<span class="chip b">Plan</span>'],
                       ["Autumn Makers", "CT", "Sep 26", "Sales permit", "Aug 27", '<span class="chip b">Plan</span>']]))),
    "f1-j1-student-tax-checklist-form-8843": dict(
        pill="F-1 · J-1 · Tax year 2026", t1="Student Tax Checklist", t2="+ Form 8843 walkthrough",
        tags=["PDF guide", "Checklist sheet", "Tax year 2026"],
        stage='<div class="sheet doc" style="left:525px;top:44px;width:340px;transform:rotate(4deg)">'
              '<div class="t">Form 8843, <em>line by line</em></div><div class="s">Statement for exempt individuals</div>'
              + checks([(True, "Part I: general information", "Visa type, dates in the U.S., days present"),
                        (True, "Part III: students (F, J, M, Q)", "School, program director, prior years as a student"),
                        (False, "Sign and send", "Mail by the deadline, even with no income"),
                        (False, "Keep a copy", "With your I-20 / DS-2019 and I-94")]) + "</div>"
              '<div class="sheet doc" style="left:62px;top:70px;width:460px;transform:rotate(-2.5deg)">'
              '<div class="t">2026 tax checklist <em>for F-1 / J-1 students</em></div><div class="s">Work through it in order before you file</div>'
              + checks([(True, "Resident or nonresident?", "The 5-calendar-year rule for students, in plain English"),
                        (True, "Who files Form 8843, and when", "Everyone on F-1 / J-1 status, income or not"),
                        (True, "Form 1040-NR or Form 1040", "Which return fits your status"),
                        (False, "Treaty and state checks", "Your country's treaty, and where you lived and worked in 2026"),
                        (False, "Documents and deadlines", "W-2, 1042-S, 1098-T, passport, I-20 / DS-2019")]) + "</div>"),
    "fica-refund-kit-f1-opt-students": dict(
        pill="F-1 · OPT · CPT · J-1", t1="FICA Refund Kit", t2="for F-1 / OPT students",
        tags=["PDF guide", "Word letter", "Excel tracker"],
        stage='<div class="sheet" style="left:520px;top:34px;width:330px;transform:rotate(5deg)"><div class="hd">Employer request letter<span>Word</span></div>'
              '<div class="letter"><div class="lh">Re: Refund of Social Security and Medicare withheld in error</div>'
              '<div class="ln"></div><div class="ln m"></div><div class="ln"></div><div class="ln s"></div><div class="ln m"></div>'
              '<div class="ln"></div><div class="ln s"></div></div></div>'
              '<div class="sheet doc" style="left:72px;top:66px;width:460px;transform:rotate(-2.5deg)">'
              '<div class="t">When FICA <em>shouldn\'t apply</em></div><div class="s">Your route to a refund, step by step</div>'
              + checks([(True, "Check your status and dates", "F-1 on-campus, OPT or CPT, J-1 / M-1, nonresident years"),
                        (True, "Ask your employer first", "Use the editable request letter"),
                        (False, "Form 843 + Form 8316", "If the employer can't refund it, file with the IRS"),
                        (False, "Gather documents", "W-2, pay stubs, I-20 / DS-2019, EAD, I-94")]) + "</div>"
              ),
    "artist-commission-business-kit": dict(
        pill="Commissions · Pricing · 1099", t1="Artist Commission", t2="Business Kit",
        tags=["Excel", "PDF checklist", "2026 rules"],
        stage=sheet("left:525px;top:40px;width:345px;transform:rotate(4deg)", "Invoices &amp; deposits", "Tracker",
                    table(["Client", "Quote", "Deposit", "Due"],
                          [["M. Lee", "350.00", "175.00", "Paid"], ["Studio Nine", "1,200", "600.00", "Jun 30"],
                           ["R. Patel", "480.00", "240.00", "Jul 15"], ["Cafe mural", "2,400", "1,200", "Aug 01"]],
                          num=(1, 2)))
        + sheet("left:72px;top:72px;width:470px;transform:rotate(-2.5deg)", "Commission price calculator", "Calculator",
                "<h3>Custom pet portrait, 16 x 20 in</h3>" + table(
                    ["Item", "Detail", "Amount"],
                    [["Materials", "Canvas, paint, varnish", "42.00"], ["Your time", "9 hrs x 30.00", "270.00"],
                     ["Card / platform fees", "Card processing", "12.32"], ["Tax set-aside", "Your set-aside rate", "60.00"],
                     ["Shipping &amp; packing", "Insured", "24.00"]],
                    ["Suggested quote", "", "408.32"], num=(2,)))),
}


def render(slug):
    p = PRODUCTS[slug]
    html = HEAD.format(css=CSS) + TOP.format(pill=p["pill"], t1=p["t1"], t2=p["t2"], stage=p["stage"],
                                             tags="".join(f"<span>{t}</span>" for t in p["tags"]))
    src = GFX / f"shop-{slug}.html"
    src.write_text(html, encoding="utf-8")
    png = GFX / f"shop-{slug}.png"
    subprocess.run(["node", str(ROOT / "tools" / "render_graphics.js"), str(src), str(png), "1000", "1000", "1"], check=True)
    im = Image.open(png).convert("RGB")
    SHOP.mkdir(parents=True, exist_ok=True)
    FEED.mkdir(parents=True, exist_ok=True)
    im.resize((400, 400), Image.LANCZOS).save(SHOP / f"{slug}.webp", "WEBP", quality=88, method=6)
    im.resize((800, 800), Image.LANCZOS).save(FEED / f"{slug}.jpg", "JPEG", quality=90, optimize=True)
    png.unlink()
    print("wrote", SHOP / f"{slug}.webp", "and", FEED / f"{slug}.jpg")


if __name__ == "__main__":
    for s in sys.argv[1:] or PRODUCTS:
        render(s)
