#!/usr/bin/env python3
"""/answers/ Q&A library (Site, 2026-11-17). Zain: "Add the website features you recommended above" (niche-growth-plan #1).

One short page per question people ask Copilot, Bing and Google in our niches (Bing grounding queries + Search Console,
claude/site/search-content-plan-2026-11-16.md). Built for AI answers: the question is the H1 and title, a 40-60 word direct
answer comes first, then a key-facts table, detail, links to the niche page and calculator, sources and the checked date,
with FAQPage schema. Every fact was read on irs.gov on CHECKED (see SOURCES per answer). Add a row to ANSWERS to add a page.
Never "free", never "CPA", no prices, no street address.
"""
import re
from datetime import date

import build_blog as B
import seo
import ui_kit
from build_resources import page, write, esc, BASE, cta

CHECKED = "2026-11-17"
I415 = ("IRS: Topic 415, Renting residential and vacation property", "https://www.irs.gov/taxtopics/tc415")
P527 = ("IRS: Publication 527, Residential Rental Property", "https://www.irs.gov/publications/p527")
T554 = ("IRS: Topic 554, Self-employment tax", "https://www.irs.gov/taxtopics/tc554")
P334 = ("IRS: Publication 334, Tax Guide for Small Business", "https://www.irs.gov/publications/p334")
OBBBA = ("IRS: One, Big, Beautiful Bill Act deductions for working Americans and seniors",
         "https://www.irs.gov/newsroom/one-big-beautiful-bill-act-tax-deductions-for-working-americans-and-seniors")
TIPLIST = ("IRS: Occupations that customarily and regularly received tips",
           "https://www.irs.gov/forms-pubs/occupations-that-customarily-and-regularly-received-tips-on-or-before-dec-31-2024")
S1A = ("IRS: Schedule 1-A (Form 1040), Additional Deductions", "https://www.irs.gov/pub/irs-pdf/f1040s1a.pdf")
ES = ("IRS: Form 1040-ES, Estimated Tax for Individuals (2026)", "https://www.irs.gov/pub/irs-pdf/f1040es.pdf")
T425 = ("IRS: Topic 425, Passive activities, losses and credits", "https://www.irs.gov/taxtopics/tc425")

LANES = [("booth", "Booth renters and beauty pros", "/booth-renters/", "Booth renter taxes"),
         ("airbnb", "Airbnb and short-term rental hosts", "/rental-property-taxes/", "Rental property taxes"),
         ("landlord", "Landlords", "/rental-property-taxes/", "Rental property taxes")]

# slug, lane, question, answer (40-60 words, plain text), facts [(k, v)], detail html, tool (href, label) or None, sources
ANSWERS = [
    ("do-booth-renters-pay-self-employment-tax", "booth", "Do salon booth renters pay self-employment tax?",
     "Yes. A booth renter runs their own business, so the profit goes on Schedule C and self-employment tax of 15.3% applies "
     "once net earnings are $400 or more. That is 12.4% for Social Security and 2.9% for Medicare. Nobody withholds it, "
     "so most booth renters pay quarterly estimated tax.",
     [("Forms", "Schedule C and Schedule SE with Form 1040"), ("Rate", "15.3% (12.4% Social Security + 2.9% Medicare)"),
      ("Applies from", "$400 of net earnings from self-employment"), ("Paid through", "Quarterly estimated payments (Form 1040-ES)")],
     "<p>Self-employment tax is figured on your <strong>profit</strong>, not your total sales, so every booth rent payment, supply order and "
     "license fee you record lowers it. The Social Security part stops at the yearly wage base; the Medicare part does not. "
     "You can deduct half of your self-employment tax when you figure your income tax.</p>",
     ("/tools/1099-tax-calculator/", "1099 tax calculator"), [T554, P334, ES]),
    ("is-booth-rent-tax-deductible", "booth", "Is booth rent tax deductible?",
     "Yes. If you rent a chair, booth or suite to run your own beauty business, the rent is a business expense you deduct on "
     "Schedule C. So are the supplies, tools, license renewals and education you pay for. Keep the lease or receipts, "
     "because the deduction lowers both income tax and self-employment tax.",
     [("Where it goes", "Schedule C, rent or lease line"), ("Also deductible", "Supplies, tools, licenses, education, booking apps"),
      ("Not deductible", "Personal haircuts, clothes you could wear anywhere"), ("Lowers", "Income tax and self-employment tax")],
     "<p>Booth rent paid to the salon owner is rent for business property. If you pay it weekly by app, download the yearly "
     "history so you can match it to your bank account. Mixed personal and business costs, like a phone, are deducted only for the business share.</p>",
     ("/tools/is-it-deductible/", "Is it deductible? checker"), [P334, T554]),
    ("do-hairstylists-qualify-for-no-tax-on-tips", "booth", "Do hairstylists qualify for no tax on tips?",
     "Yes. Barbers, hairstylists, cosmetologists, nail techs, lash and brow techs and makeup artists are on the IRS tipped "
     "occupations list. For 2025 through 2028 you can deduct up to $25,000 of qualified tips. The deduction shrinks above "
     "$150,000 of modified AGI ($300,000 joint). Booth renters qualify too, up to their net profit.",
     [("Years", "2025 through 2028"), ("Cap", "$25,000 of qualified tips a year"),
      ("Phase-out", "$100 less for each $1,000 of MAGI over $150,000 ($300,000 joint)"), ("Form", "Schedule 1-A, Part II"),
      ("Rules", "Valid SSN; married couples must file jointly")],
     "<p>The deduction lowers federal income tax only. Social Security and Medicare tax, or self-employment tax for booth renters, "
     "still applies to every tip. Some self-employed service businesses are excluded, and a required service charge is not a tip.</p>",
     ("/tools/no-tax-on-tips-calculator/", "No tax on tips calculator"), [OBBBA, TIPLIST, S1A]),
    ("estimated-tax-due-dates-2026", "booth", "When are 2026 estimated tax payments due?",
     "The four 2026 federal estimated tax payments are due April 15, June 15 and September 15, 2026, and January 15, 2027. "
     "Self-employed people, booth renters and landlords generally pay them if they expect to owe $1,000 or more for the year, "
     "because no employer withholds tax for them.",
     [("1st payment", "April 15, 2026"), ("2nd payment", "June 15, 2026"), ("3rd payment", "September 15, 2026"),
      ("4th payment", "January 15, 2027"), ("Form", "1040-ES (pay online with IRS Direct Pay or EFTPS)")],
     "<p>Each payment covers income earned in its period, so a slow first quarter can mean a smaller first payment. "
     "Paying too little, or late, can mean an underpayment penalty. New Jersey and New York use the same four dates for their own estimates.</p>",
     ("/tools/quarterly-estimated-tax-calculator/", "Quarterly estimated tax calculator"), [ES]),
    ("do-i-report-airbnb-income-under-15-days", "airbnb", "Do I report Airbnb income under 15 days?",
     "Not if the place is also your home. If you use a dwelling as a home and rent it for fewer than 15 days in the year, "
     "you don't report the rental income or deduct rental expenses. From 15 rental days on, you report all of it "
     "and split expenses between rental and personal use.",
     [("Rule", "Rented under 15 days and used as a home"), ("Income", "Not reported"), ("Rental expenses", "Not deducted"),
      ("Still deductible", "Mortgage interest and property taxes, if you itemize"), ("Source", "IRS Topic 415")],
     "<p>“Used as a home” means your personal days are more than the greater of 14 days or 10% of the days it was rented "
     "at a fair price. A property you never stay in doesn't get this rule: rent it even a few nights and the income is reported.</p>",
     ("/tools/airbnb-host-tax-checker/", "Airbnb host tax checker"), [I415, P527]),
    ("airbnb-income-schedule-c-or-schedule-e", "airbnb", "Is Airbnb income reported on Schedule C or Schedule E?",
     "Most hosts use Schedule E. If you provide substantial services mainly for guests' convenience, such as regular cleaning "
     "during stays, changing linens or maid service, the income goes on Schedule C instead, like a hotel. Schedule C income "
     "is usually also subject to 15.3% self-employment tax.",
     [("Space only, cleaning between guests", "Schedule E"), ("Hotel-style services during stays", "Schedule C"),
      ("Self-employment tax", "Usually only on Schedule C"), ("Source", "IRS Publication 527")],
     "<p>Utilities, trash collection and cleaning of common areas don't count as substantial services. "
     "The choice changes your tax, so decide it from what you actually provide, not from what the platform calls you.</p>",
     ("/tools/airbnb-host-tax-checker/", "Airbnb host tax checker"), [P527, T554]),
    ("airbnb-personal-use-days-limit", "airbnb", "How many personal days can an Airbnb host use?",
     "Up to 14 days or 10% of the days it was rented at a fair price, whichever is more. Go over that and the IRS treats the "
     "rental as your home: you still deduct the rental share of expenses, but they can't be more than your rental income, "
     "so the rental can't show a loss.",
     [("Limit", "Greater of 14 days or 10% of fair-rental days"), ("Counts as personal", "You, family, friends, below-market rentals"),
      ("Over the limit", "No rental loss allowed"), ("Source", "IRS Topic 415, Publication 527")],
     "<p>Example: rented 200 nights, personal limit 20 nights (10% of 200). Days spent mainly repairing or maintaining the "
     "property don't count as personal days.</p>",
     ("/tools/airbnb-host-tax-checker/", "Airbnb host tax checker"), [I415, P527]),
    ("how-many-years-to-depreciate-rental-property", "landlord", "How many years do you depreciate a rental property?",
     "27.5 years for a residential rental building, using the mid-month convention. Divide the building's basis by 27.5 for "
     "each full year; the first and last years are partial. Land is never depreciated, so take its value out of the price "
     "before you start.",
     [("Recovery period", "27.5 years (residential rental)"), ("Method", "Straight line, mid-month convention"),
      ("Not depreciated", "Land"), ("First year", "Partial, from the middle of the month placed in service"), ("Form", "Form 4562, then Schedule E")],
     "<p>Basis is usually the purchase price plus certain closing costs, minus land. Improvements, like a new roof, start their "
     "own 27.5-year schedule. When you sell, depreciation you took, or could have taken, is taxed back.</p>",
     ("/tools/rental-depreciation-calculator/", "Rental depreciation calculator"), [P527]),
    ("when-does-rental-property-depreciation-start", "landlord", "When does depreciation start on a rental property?",
     "When the property is placed in service, meaning ready and available to rent, not when the first tenant moves in. "
     "A house listed for rent in March starts depreciating in March even if it stays empty until June. Depreciation stops "
     "when you have recovered its cost or take it out of service.",
     [("Starts", "Ready and available for rent"), ("Not", "The first tenant's move-in date"),
      ("First-year amount", "Mid-month convention"), ("Stops", "Cost fully recovered, or retired from service")],
     "<p>Keep proof of the date: the listing, photos of the finished unit, or the agent's email. It sets every year of your schedule.</p>",
     ("/tools/rental-depreciation-calculator/", "Rental depreciation calculator"), [P527]),
    ("is-a-new-roof-on-a-rental-a-repair-or-improvement", "landlord", "Is a new roof on a rental a repair or improvement?",
     "A new roof is an improvement. You add it to the property's basis and depreciate it over 27.5 years. Fixing a leak or "
     "replacing a few shingles is a repair, deducted in the year you pay. Items costing $2,500 or less per invoice or item can be "
     "deducted under the de minimis safe harbor if you elect it.",
     [("Whole new roof", "Improvement, 27.5 years"), ("Patch or a few shingles", "Repair, deduct now"),
      ("De minimis safe harbor", "$2,500 per invoice or item, elected each year"), ("Source", "IRS Publication 527")],
     "<p>The test is whether the work betters, restores or adapts the property. Read the full guide: "
     "<a href=\"/blog/rental-property-repairs-vs-improvements-2026/\">rental property repairs vs improvements</a>.</p>",
     ("/tools/rental-depreciation-calculator/", "Rental depreciation calculator"), [P527]),
    ("can-a-rental-loss-offset-w2-income", "landlord", "Can a rental property loss offset my W-2 income?",
     "Up to $25,000 a year, if you actively participate in managing the rental. The allowance phases out as modified AGI "
     "goes from $100,000 to $150,000, and married couples filing separately get less. Losses you can't use carry forward "
     "to future years or until you sell.",
     [("Allowance", "Up to $25,000 a year"), ("Requires", "Active participation (approving tenants, setting rent, approving repairs)"),
      ("Phase-out", "MAGI $100,000 to $150,000"), ("Unused loss", "Carries forward"), ("Form", "Form 8582")],
     "<p>Real estate professionals follow different rules. A short-term rental with a short average stay may not count as a "
     "rental activity at all, so ask before counting on this allowance.</p>",
     None, [T425, P527]),
    ("is-a-security-deposit-taxable-income", "landlord", "Is a security deposit taxable rental income?",
     "Not when you get it, if you may have to return it. It becomes income in the year you keep any of it, for example for "
     "damage or unpaid rent. A deposit that will be used as the last month's rent is advance rent, which is income in the year "
     "you receive it.",
     [("Refundable deposit", "Not income when received"), ("Deposit you keep", "Income in the year you keep it"),
      ("Last month's rent paid upfront", "Advance rent, income when received"), ("Source", "IRS Publication 527")],
     "<p>Keep deposits in a separate account or ledger line so they don't get counted as rent by mistake.</p>",
     None, [P527]),
]


def url(slug):
    return f"{BASE}/answers/{slug}/"


CSS = """<style>
.ans{max-width:820px;margin:0 auto;padding:0 24px}
.ans-box{background:#faf7f0;border:1px solid rgba(176,141,63,.35);border-left:4px solid var(--gold,#b08d3f);border-radius:14px;padding:18px 20px;margin:8px 0 22px}
.ans-box p{margin:0;font-size:1.06rem;line-height:1.6}
.ans-box .lbl{display:block;font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--navy,#0f2340);margin-bottom:6px}
.ans table{width:100%;border-collapse:collapse;margin:6px 0 22px;font-size:.95rem}
.ans th,.ans td{text-align:left;padding:10px 12px;border-bottom:1px solid rgba(21,21,21,.1);vertical-align:top}
.ans th{width:38%;color:var(--navy,#0f2340);font-weight:600}
.ans h2{font-size:1.25rem;margin:26px 0 10px}
.ans .ans-next{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 20px}
.ans .sources ul{padding-left:18px}.ans .sources li{margin:4px 0}
.ans-idx{max-width:var(--maxw,1180px);margin:0 auto;padding:0 24px}
.ans-lane{margin:0 0 30px}.ans-lane h2{font-size:1.3rem;margin:0 0 12px}
.ans-list{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.ans-list a{display:block;background:#fff;border:1px solid rgba(21,21,21,.1);border-radius:14px;padding:14px 16px;text-decoration:none;color:var(--ink,#151515);height:100%}
.ans-list a:hover{border-color:var(--gold,#b08d3f)}
.ans-list b{display:block;color:var(--navy,#0f2340);margin-bottom:4px}.ans-list span{font-size:.9rem;color:var(--muted,#666);font-weight:300}
@media(max-width:720px){.ans-list{grid-template-columns:1fr}.ans th{width:44%}}
</style>"""


def desc_of(answer):
    """First sentence(s) of the answer, trimmed to 155 characters for the meta description."""
    out = ""
    for s in re.split(r"(?<=\.)\s+", answer):
        if len(out) + len(s) + 1 > 155:
            break
        out = (out + " " + s).strip()
    return out if len(out) >= 50 else answer[:152].rsplit(" ", 1)[0] + "…"


def build_one(a, nice):
    slug, lane, q, ans, facts, detail, tool, srcs = a
    ln = next(x for x in LANES if x[0] == lane)
    u = url(slug)
    rows = "".join(f"<tr><th scope=\"row\">{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in facts)
    src = "".join(f'<li><a href="{esc(s[1])}" target="_blank" rel="noopener">{esc(s[0])}</a></li>' for s in srcs)
    btns = (f'<a class="btn btn-gold" href="{ln[2]}#get-price">Get my price</a>'
            + (f'<a class="btn btn-ink" href="{tool[0]}">Try the {esc(tool[1])}</a>' if tool else "")
            + f'<a class="btn btn-line" href="{ln[2]}">{esc(ln[3])}</a>')
    others = [x for x in ANSWERS if x[1] == lane and x[0] != slug][:3]
    more = "".join(f'<li><a href="/answers/{x[0]}/">{esc(x[2])}</a></li>' for x in others)
    body = f'''{CSS}<header class="bhero"><div class="wrap"><span class="eyebrow">Tax answers · {esc(ln[1])}</span>
<h1>{esc(q)}</h1><p>Short answer first, checked against IRS sources on {nice}.</p></div></header>
<main><article class="ans">
<div class="ans-box"><span class="lbl">Short answer</span><p>{esc(ans)}</p></div>
<h2>Key facts</h2><table><tbody>{rows}</tbody></table>
<h2>What else to know</h2>{detail}
<div class="ans-next">{btns}</div>
<h2>Related questions</h2><ul>{more}<li><a href="/answers/">All tax answers</a></li></ul>
<section class="sources"><h2>Sources</h2><ul>{src}</ul><p class="factline">Checked against the sources above on {nice}.</p></section>
</article>
{cta("Want this applied to your return?", "Book a 30-minute call or phone <a href=\"tel:+13472054468\" data-conv=\"call\">(347) 205-4468</a>. We quote before any work starts.")}
{ui_kit.fineprint("General information, not tax advice for your situation. Reading this page doesn't create a client relationship.")}
</main>'''
    d = desc_of(ans)
    faq = {"@type": "FAQPage", "@id": u + "#faq", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}]}
    ld = seo.graph(u, q, d, faq, crumb=[("Home", BASE + "/"), ("Tax answers", BASE + "/answers/"), (q, u)])
    return write(f"answers/{slug}", page(f"{q} | MFA", d, u, body, ld, active="res", keywords=[q.rstrip("?").lower(), ln[3].lower(), "tax answers"]))


def build_index(nice):
    u = BASE + "/answers/"
    lanes = ""
    for key, name, href, label in LANES:
        items = "".join(f'<li><a href="/answers/{a[0]}/"><b>{esc(a[2])}</b><span>{esc(desc_of(a[3]))}</span></a></li>' for a in ANSWERS if a[1] == key)
        lanes += f'<section class="ans-lane" aria-label="{esc(name)}"><h2>{esc(name)}</h2><ul class="ans-list">{items}</ul><p><a href="{href}">{esc(label)} →</a></p></section>'
    title = "Tax Answers for Booth Renters, Hosts & Landlords | MFA"
    d = "Short, sourced answers to the tax questions booth renters, Airbnb hosts and landlords ask most, checked against IRS publications."
    body = f'''{CSS}<header class="bhero"><div class="wrap"><span class="eyebrow">Tax answers</span>
<h1>Tax answers, <em>short and sourced.</em></h1><p>The questions our niche clients ask most, each answered in a few sentences first, then the facts and the IRS source. Checked {nice}.</p></div></header>
<main><div class="ans-idx">{lanes}</div>
{cta("Have a question that isn't here?", "Book a 30-minute call or email us. We answer before we quote.")}
</main>'''
    items = [{"@type": "ListItem", "position": i + 1, "url": url(a[0]), "name": a[2]} for i, a in enumerate(ANSWERS)]
    ld = seo.graph(u, "Tax answers", d, {"@type": "ItemList", "@id": u + "#list", "itemListElement": items},
                   crumb=[("Home", BASE + "/"), ("Tax answers", u)], kind="CollectionPage")
    return write("answers", page(title, d, u, body, ld, active="res", keywords=["tax answers", "booth renter taxes", "Airbnb host taxes", "landlord taxes"]))


def build():
    nice = date.fromisoformat(CHECKED).strftime("%B %-d, %Y")
    for a in ANSWERS:
        n = len(a[3].split())
        assert 40 <= n <= 62, f"{a[0]}: answer is {n} words (want 40-60)"
    return [build_index(nice)] + [build_one(a, nice) for a in ANSWERS]


if __name__ == "__main__":
    print("\n".join(build()))
