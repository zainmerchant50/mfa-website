#!/usr/bin/env python3
"""Printable 2027 Tax Calendar (PDF product). Same verified data as /tools/2027-tax-calendar/ (data/tax-calendar-2027.json).
Run: python3 tools/render_calendar_2027.py OUT_DIR  -> writes calendar-2027.html; then Playwright prints the PDF.
Price and listing need Zain's yes (Gumroad only; rule 8: no new Etsy listings)."""
import calendar as pc, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_calendar_2027 as K
from build_resources import esc

NAVY, GOLD = "#0f2340", "#b08d3f"
CSS = f"""@page{{size:Letter landscape;margin:0}}*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,Helvetica,Arial,sans-serif;color:#151515}}
.pg{{width:11in;height:8.5in;padding:.45in .5in .4in;page-break-after:always;position:relative;overflow:hidden}}
.cover{{background:{NAVY};color:#fff;display:flex;flex-direction:column;justify-content:center}}
.cover .eb{{color:{GOLD};letter-spacing:.2em;text-transform:uppercase;font-size:12pt;font-weight:700}}
.cover h1{{font-family:Georgia,serif;font-weight:400;font-size:64pt;margin:.15in 0}}.cover h1 em{{color:{GOLD}}}
.cover p{{font-size:15pt;max-width:7.5in;color:rgba(255,255,255,.85);line-height:1.5}}
.cover .ft{{position:absolute;bottom:.4in;left:.5in;right:.5in;font-size:10pt;color:rgba(255,255,255,.7);display:flex;justify-content:space-between}}
.hd{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px solid {GOLD};padding-bottom:6px;margin-bottom:12px}}
.hd h2{{font-family:Georgia,serif;font-weight:400;font-size:30pt;margin:0;color:{NAVY}}}.hd span{{font-size:10pt;color:#666}}
.body{{display:grid;grid-template-columns:5.2in 1fr;gap:.3in;height:6.9in}}
table.g{{width:100%;border-collapse:collapse;table-layout:fixed;height:100%}}
table.g th{{font-size:9pt;color:#666;padding:4px;text-align:left;border-bottom:1px solid #ccc;height:.25in}}
table.g td{{border:1px solid #ddd;vertical-align:top;padding:4px 5px;font-size:10pt}}
table.g td.on{{background:#faf3e3}}table.g td.on b{{background:{GOLD};color:#fff;border-radius:4px;padding:0 4px}}
table.g td.x{{background:#f6f6f6}}
ul{{list-style:none;margin:0;padding:0;font-size:9.4pt;line-height:1.35}}
li{{display:grid;grid-template-columns:.62in 1fr;gap:6px;padding:5px 0;border-bottom:1px solid #eee}}
li .d{{font-weight:700;color:{NAVY}}}li .t{{display:inline-block;font-size:7pt;font-weight:700;color:#fff;border-radius:3px;padding:1px 4px;margin-right:4px;background:{NAVY}}}
li .t.NJ{{background:#2f6f5e}}li .t.NY{{background:#6b3f8f}}li .y{{font-size:7pt;color:#7a6326;font-weight:700}}
.notes{{margin-top:8px;font-size:9pt;color:#888}}.notes div{{border-bottom:1px solid #ddd;height:.3in}}
.pf{{position:absolute;bottom:.22in;left:.5in;right:.5in;font-size:8pt;color:#888;display:flex;justify-content:space-between}}
.list h2{{font-family:Georgia,serif;font-weight:400;color:{NAVY};margin:0 0 8px}}.cols{{columns:2;column-gap:.35in;font-size:8.6pt}}
.cols p{{margin:0 0 4px;break-inside:avoid}}"""
YT = {"2026": "2026 return", "2027": "2027 tax year", "both": "2026 + 2027"}
FT = '<div class="pf"><span>Merchant Financial Advisory · mfa-advisory.com · (347) 205-4468</span><span>General information, not tax advice. Dates checked October 20, 2026; check the source before you rely on an extension.</span></div>'


def month(y, m, evs):
    on = {e["date"] for e in evs}
    weeks = pc.Calendar(0).monthdayscalendar(y, m)
    rows = "".join("<tr>" + "".join(('<td class="x"></td>' if d == 0 else f'<td class="{"on" if f"{y}-{m:02d}-{d:02d}" in on else ""}"><b>{d}</b></td>') for d in w) + "</tr>" for w in weeks)
    lis = "".join(f'<li><span class="d">{date.fromisoformat(e["date"]).strftime("%b %-d")}</span><span><span class="t {e["jurisdiction"]}">{K.JL[e["jurisdiction"]]}</span>'
                  f'<strong>{esc(e["form"])}</strong> {esc(e["what"])} <span class="y">{YT[e["ty"]]}</span></span></li>' for e in evs) or "<li><span></span><span>No federal, NJ or NY deadlines this month.</span></li>"
    name = date(y, m, 1).strftime("%B %Y")
    return (f'<section class="pg"><div class="hd"><h2>{name}</h2><span>2027 Tax Calendar · Federal, NJ, NY</span></div><div class="body">'
            f'<table class="g"><thead><tr>{"".join(f"<th>{d}</th>" for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])}</tr></thead><tbody>{rows}</tbody></table>'
            f'<div><ul>{lis}</ul><div class="notes">Notes<div></div><div></div><div></div><div></div></div></div></div>{FT}</section>')


def main(out):
    evs = K.events()
    cover = ('<section class="pg cover"><span class="eb">Merchant Financial Advisory</span><h1>2027 <em>Tax Calendar</em></h1>'
             f'<p>Every federal, New Jersey and New York deadline for 2027, month by month: your 2026 returns and payments, plus 2027 estimated taxes, payroll and sales tax. {len(evs)} dates, each with its form.</p>'
             '<div class="ft"><span>mfa-advisory.com</span><span>Calendar-year filers · General information, not tax advice</span></div></section>')
    pages = "".join(month(y, m, [e for e in evs if e["date"].startswith(f"{y}-{m:02d}")]) for y, m in [(2027, i) for i in range(1, 13)] + [(2028, 1)])
    allp = "".join(f'<p><b>{date.fromisoformat(e["date"]).strftime("%b %-d, %Y")}</b> · {"" if e["form"].startswith(K.JL[e["jurisdiction"]]) else K.JL[e["jurisdiction"]] + " "}{esc(e["form"])}: {esc(e["what"])} ({", ".join(K.SHORT[x] for x in e["ents"])})</p>' for e in evs)
    lst = f'<section class="pg list"><h2>All {len(evs)} dates at a glance</h2><div class="cols">{allp}</div>{FT}</section>'
    html = f'<!doctype html><html><head><meta charset="utf-8"><title>2027 Tax Calendar | MFA</title><style>{CSS}</style></head><body>{cover}{pages}{lst}</body></html>'
    Path(out, "calendar-2027.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
