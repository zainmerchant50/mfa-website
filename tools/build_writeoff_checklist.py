#!/usr/bin/env python3
"""Builds the 59-expense write-off checklist PDF that the Is It Deductible? email capture sends.

Output: site/downloads/write-off-checklist-2026.pdf (served at /downloads/write-off-checklist-2026.pdf).
Data: data/deductions.json (same entries as the tool page; nothing new is claimed here).
Delivered by the MailerLite automation "Write-off checklist" (group 202772408633918719). Hub, 2026-10-30.
Run: python3 tools/build_writeoff_checklist.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data" / "deductions.json").read_text(encoding="utf-8"))
E = D["entries"]
OUT = ROOT / "site" / "downloads" / "write-off-checklist-2026.pdf"
FONTS = ROOT / "social" / "fonts"
GROUPS = {"home": "Home and workspace", "vehicle": "Car and travel", "meals": "Food and entertaining",
          "tech": "Phone, internet and software", "equip": "Equipment and bigger buys", "people": "Paying people",
          "insurance": "Insurance and health", "retire": "Saving for retirement", "pro": "Accountants, lawyers and dues",
          "marketing": "Marketing and gifts", "education": "Courses and learning", "banking": "Bank fees, loans and unpaid bills",
          "startup": "Starting a business", "inventory": "Products and shipping", "taxes": "Taxes and licenses",
          "not": "Things that usually don't count"}
LABEL = {"yes": "Yes", "partly": "Partly", "no": "Usually not"}
esc = html.escape


def font(name, fam, weight, style="normal"):
    return (f"@font-face{{font-family:'{fam}';src:url('file://{FONTS / name}') format('woff2');"
            f"font-weight:{weight};font-style:{style}}}")


def page():
    n = len(E)
    rows = []
    for g, title in GROUPS.items():
        items = [e for e in E if e["category"] == g]
        if not items:
            continue
        trs = "".join(
            f'<tr><td class="bx">&#9744;</td><td><b>{esc(e["name"])}</b></td>'
            f'<td class="a a-{e["answer"]}">{LABEL[e["answer"]]}</td>'
            f'<td class="k">{esc(e["keep"][0])}</td></tr>' for e in items)
        rows.append(f'<section><h2>{esc(title)}</h2><table>{trs}</table></section>')
    css = "".join([font("inter-latin-400-normal.woff2", "Inter", 400), font("inter-latin-600-normal.woff2", "Inter", 600),
                   font("cormorant-garamond-latin-500-normal.woff2", "Cormorant", 500)])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}
@page{{size:Letter;margin:0.55in 0.6in 0.6in}}
body{{font-family:Inter,sans-serif;font-size:9pt;color:#1B2638;margin:0}}
.top{{border-bottom:2px solid #B08D3F;padding-bottom:8px;margin-bottom:10px}}
.ey{{font-size:7.5pt;letter-spacing:.18em;text-transform:uppercase;color:#B08D3F;font-weight:600}}
h1{{font-family:Cormorant,serif;font-weight:500;font-size:25pt;margin:2px 0 4px;color:#13213A}}
.lede{{color:#4A5568;font-size:9pt;line-height:1.45;margin:0}}
.key{{margin:8px 0 2px;font-size:8pt;color:#4A5568}}
.key span{{display:inline-block;margin-right:14px}}
section{{break-inside:avoid;margin-top:9px}}
h2{{font-size:9.5pt;margin:0 0 3px;color:#13213A;border-bottom:1px solid #E5DFD0;padding-bottom:2px}}
table{{width:100%;border-collapse:collapse}}
td{{padding:2.6px 4px;vertical-align:top;border-bottom:1px solid #F1ECE1}}
td.bx{{width:14px;color:#B08D3F;font-size:10pt;padding-top:1px}}
td.a{{width:62px;font-weight:600;font-size:8pt}}
.a-yes{{color:#1F6F43}} .a-partly{{color:#9A6B00}} .a-no{{color:#9B2C2C}}
td.k{{color:#4A5568;font-size:8pt;width:48%}}
.foot{{margin-top:12px;padding-top:8px;border-top:2px solid #B08D3F;font-size:8pt;color:#4A5568;line-height:1.5}}
.foot b{{color:#13213A}}
</style></head><body>
<div class="top"><div class="ey">MFA · Merchant Financial Advisory · 2026 tax year</div>
<h1>{n} small-business write-offs: your checklist</h1>
<p class="lede">Tick each expense you had this year. "Partly" means only the business share counts, or a limit applies.
The last column is the proof to keep. Full answers, limits and IRS sources for every line:
<b>mfa-advisory.com/tools/is-it-deductible</b></p>
<div class="key"><span class="a-yes"><b>Yes</b> counts as a business expense</span><span class="a-partly"><b>Partly</b> business share or a limit</span><span class="a-no"><b>Usually not</b> narrow exceptions only</span></div></div>
{''.join(rows)}
<div class="foot"><b>Want this done for you?</b> We set up your books so write-offs are tracked all year, and go through your expenses with you before you file.
Book a 30-minute consultation at <b>mfa-advisory.com/book</b> or email <b>info@mfa-advisory.com</b>.<br>
General information for the 2026 tax year, not tax, legal or accounting advice. Rules depend on your facts. Data checked {D["meta"]["checked"][:10]}.
© Merchant Financial Advisory LLC.</div>
</body></html>"""


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    h = page()
    low = h.lower()
    assert " free " not in low and "cpa firm" not in low, "banned wording"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.set_content(h, wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.pdf(path=str(OUT), format="Letter", print_background=True, prefer_css_page_size=True)
        b.close()
    return OUT


if __name__ == "__main__":
    print(build())
