#!/usr/bin/env python3
"""Builds /rideshare-driver-taxes/ (Site/Hub): taxes and bookkeeping for Uber, Lyft and delivery drivers
(DoorDash, Instacart, Uber Eats, Grubhub, Amazon Flex).

Rule 25 (Zain 2026-11-16): every niche gets its own page. Zain 2026-11-24 14:01: "do the rideshare page now".
No new prices: tax returns quoted up front; bookkeeping from $300/month; quarterly estimates link to the approved page.
Facts checked on irs.gov on CHECKED (SOURCES). Never "free", never "CPA", no street address.
Run via tools/build_resources.py (it calls build()).
"""
from datetime import date
import re

import build_blog as B
import lead_box
import seo
import ui_kit
from build_resources import page, write, esc, BASE, cta

URL = BASE + "/rideshare-driver-taxes/"
CHECKED = "2026-11-24"
KEYWORDS = ["rideshare driver taxes", "uber driver taxes", "lyft driver taxes", "doordash taxes", "delivery driver taxes",
            "uber 1099 taxes", "mileage deduction for uber drivers", "instacart shopper taxes", "gig worker taxes",
            "no tax on tips delivery drivers", "quarterly taxes for uber drivers"]
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'
TEL = '<a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>'

WHO = [
    ("Rideshare drivers", "Uber, Lyft and other app-based drivers who use their own car and pick their own hours."),
    ("Food and grocery delivery", "DoorDash, Uber Eats, Grubhub and Instacart drivers and shoppers, full time or on the side."),
    ("Package and courier drivers", "Amazon Flex and other app-based couriers paid per block or per delivery."),
    ("Drivers with a day job", "A W-2 job plus app driving at night or on weekends, where two kinds of income meet on one return."),
]

SERVICES = [
    ("Every tax season", "Driver tax return", "Quoted", "up front, by return",
     "Your Form 1040 with Schedule C and Schedule SE, federal and state, with every driver deduction checked.",
     ["Uber, Lyft and delivery app forms matched to your tax summaries", "Mileage or actual car costs, whichever is allowed and better",
      "Tips reported and the tips deduction checked", "Self-employment tax worked out"],
     "/book/", "Get a quote", True),
    ("All year", "Bookkeeping for drivers", "From $300", "/ month",
     "Monthly books so you know what you really made after gas, fees and the car.",
     ["Income tracked by app", "Mileage log kept up to date", "Phone, tolls, parking and supplies logged",
      "Year-end package ready for your return"],
     "/services/#bookkeeping", "How bookkeeping works", False),
    ("Four times a year", "Quarterly estimated taxes", "Planned", "with you",
     "The apps don't withhold tax, so we work out what to send the IRS and your state each quarter.",
     ["Payment amounts and due dates", "Reminders before each deadline", "Adjusted when your driving income changes"],
     "/quarterly-estimated-taxes/", "See quarterly estimates", False),
]

STEPS = [
    ("Book a call", 'Pick a time on our <a href="/book/" data-conv="book">booking page</a> or call ' + TEL +
     ". Tell us which apps you drive for and whether you keep a mileage log."),
    ("Get your price", "You get a written quote before any work starts. Nothing is charged until you agree to it."),
    ("We prepare and file", "We match your app tax summaries, work out your car deduction, prepare your return and walk you through it before we e-file."),
]

FAQ = [
    ("Are Uber, Lyft and DoorDash drivers self-employed?",
     "Usually yes. App drivers are generally treated as independent contractors, so you report your driving income and expenses on "
     "Schedule C and pay self-employment tax on your profit. Nobody withholds tax from your payouts."),
    ("How much tax do rideshare drivers pay?",
     "Two taxes apply to your profit: income tax at your normal rate, and self-employment tax of 15.3% (12.4% Social Security plus "
     "2.9% Medicare) once your net earnings are $400 or more. Half of the self-employment tax is deductible when you work out your income tax."),
    ("What is the 2026 mileage rate for Uber and delivery drivers?",
     "For business miles driven in 2026, the IRS standard mileage rate is 72.5 cents a mile from January 1 to June 30 and 76 cents "
     "a mile from July 1 to December 31. Instead of the standard rate you can deduct the business share of your actual car costs. "
     "Either way, you need a mileage log."),
    ("Can I deduct tolls and parking on top of mileage?",
     "Yes. Business tolls and parking fees are deductible in addition to the standard mileage rate. Gas, oil, repairs, insurance and "
     "depreciation are already built into the standard rate, so you don't deduct those separately when you use it."),
    ("Will I get a 1099 from Uber, Lyft or DoorDash?",
     "You may get a Form 1099-K for payments processed through the app and a Form 1099-NEC for other payments such as bonuses. Many "
     "apps also give a yearly tax summary. Either way, all your driving income is taxable, even if no form arrives."),
    ("Does no tax on tips apply to delivery and rideshare drivers?",
     "It can. From 2025 through 2028, qualified tips can be deducted up to $25,000 a year, whether or not you itemize. Rideshare "
     "drivers and app-based delivery people are on the IRS list of tipped occupations. For self-employed drivers the deduction can't be "
     "more than the net profit from driving, and it phases out above $150,000 of modified AGI ($300,000 joint)."),
    ("Do I need to pay quarterly taxes as a driver?",
     'Most full-time drivers do, because the apps don\'t withhold tax. Federal estimates for 2026 income are due April 15, June 15 and '
     'September 15, 2026 and January 15, 2027. If you also have a W-2 job, raising your withholding there can cover it instead. See '
     '<a href="/quarterly-estimated-taxes/">quarterly estimated taxes</a>.'),
    ("Do you work with drivers outside New Jersey?",
     "Yes. We prepare federal returns for every state and state returns for every state except Connecticut, Maryland and Oregon."),
]

SOURCES = [
    ("IRS: Gig economy tax center", "https://www.irs.gov/businesses/gig-economy-tax-center"),
    ("IRS: Topic 554, Self-employment tax", "https://www.irs.gov/taxtopics/tc554"),
    ("IRS: Standard mileage rates", "https://www.irs.gov/tax-professionals/standard-mileage-rates"),
    ("IRS: Understanding your Form 1099-K", "https://www.irs.gov/businesses/understanding-your-form-1099-k"),
    ("IRS: One, Big, Beautiful Bill Act tax deductions for working Americans and seniors (no tax on tips)",
     "https://www.irs.gov/newsroom/one-big-beautiful-bill-act-tax-deductions-for-working-americans-and-seniors"),
    ("IRS: Occupations that customarily and regularly received tips on or before Dec. 31, 2024",
     "https://www.irs.gov/forms-pubs/occupations-that-customarily-and-regularly-received-tips-on-or-before-dec-31-2024"),
    ("IRS: Publication 463, Travel, Gift, and Car Expenses", "https://www.irs.gov/publications/p463"),
    ("IRS: Estimated taxes", "https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes"),
]
CSS = """<style>
.cmp-tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.br-cmp{min-width:560px}.br-cmp td,.br-cmp th{vertical-align:top;text-align:left}.br-cmp tbody th{font-size:.88rem;font-weight:600;letter-spacing:0;text-transform:none;color:var(--navy);border-top:0;border-bottom:1px solid rgba(21,21,21,.1)}@media(max-width:720px){.br-cmp{min-width:0;table-layout:fixed;font-size:.84rem}.br-cmp th,.br-cmp td{padding:9px 6px}}
.br-who{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:6px}
.br-who .card{padding:22px 24px;background:#fff;border:1px solid var(--hair);border-radius:16px}
.br-who h3{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:1.35rem;color:var(--navy);margin:0 0 6px}
.br-who p{margin:0;font-size:.92rem;line-height:1.6;color:var(--muted)}
.pk.br-pk{grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
@media (max-width:1000px){.pk.br-pk{grid-template-columns:1fr}}
.br-pk .pkc{padding:28px 24px 24px}.br-pk .pk-price b{font-size:2.3rem}
.br-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;counter-reset:s;margin-top:6px}
.br-steps .step{padding:26px;border-top:2px solid var(--gold,#B08D3F);background:#fff;border-radius:0 0 12px 12px}
.br-steps .step:before{counter-increment:s;content:"0" counter(s);font-family:'Cormorant Garamond',Georgia,serif;font-size:38px;color:var(--gold,#B08D3F);display:block;line-height:1;margin-bottom:10px}
.br-steps .step h3{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.6rem;font-weight:500;margin:0 0 8px;color:var(--ink,#10233F)}
.br-steps .step p{margin:0;color:var(--muted);font-size:.95rem;line-height:1.7}
.br-steps .step p a,#faqs .faq-a-in a,.br-note a{color:var(--navy);border-bottom:1px solid var(--gold);transition:color .3s}
.br-steps .step p a:hover,#faqs .faq-a-in a:hover,.br-note a:hover{color:var(--gold)}
@media (max-width:860px){.br-steps{grid-template-columns:1fr}}
.br-cred,.br-note{margin:18px 0 0;font-size:.88rem;color:var(--muted)}
.br-src{max-width:860px}.br-src ul{margin:6px 0 0;padding-left:20px;display:grid;gap:8px}.br-src li{font-size:.92rem;line-height:1.55}
.br-src li::marker{color:var(--gold)}.br-src li a{color:var(--navy);border-bottom:1px solid rgba(176,141,63,.5);text-decoration:none}
.br-src li a:hover{color:var(--gold)}.br-src .factline{margin:16px 0 0;font-size:.86rem;color:var(--muted)}
</style>"""

TITLE = "Rideshare & Delivery Driver Taxes (Uber, DoorDash) | MFA"
DESC = ("Tax returns, bookkeeping and quarterly taxes for Uber, Lyft and delivery drivers. Schedule C, 2026 mileage rates, "
        "1099-K, tips and self-employment tax.")


def service_node():
    o = seo._offer
    return {"@type": "Service", "@id": URL + "#service", "name": "Taxes and bookkeeping for rideshare and delivery drivers", "url": URL,
            "serviceType": "Tax preparation and bookkeeping for self-employed rideshare and delivery drivers (Schedule C, Schedule SE, mileage, estimated taxes)",
            "description": DESC, "provider": {"@id": seo.ORG_ID}, "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "Audience", "audienceType": "Uber, Lyft, DoorDash, Instacart and other app-based drivers"},
            "offers": [o("Rideshare and delivery driver tax return (Schedule C + SE)", None, "Quoted up front by return type.", url=URL + "#services"),
                       o("Bookkeeping for drivers", 300, "Monthly bookkeeping from $300/month.", url=BASE + "/services/#bookkeeping")]}


def build():
    nice = date.fromisoformat(CHECKED).strftime("%B %-d, %Y")
    who = "".join(f'<div class="card"><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for a, b in WHO)
    cards = []
    for tag, name, price, note, lead, items, href, btn, feat in SERVICES:
        lis = "".join(f"<li>{ICO}<span>{esc(x)}</span></li>" for x in items)
        conv = ' data-conv="book"' if href == "/book/" else ""
        cards.append(f'''<div class="pkc card{" feat" if feat else ""}"><span class="pk-tag">{esc(tag)}</span><h3>{esc(name)}</h3>
<p class="pk-price"><b>{esc(price)}</b><span>{esc(note)}</span></p><p class="pk-lead">{esc(lead)}</p><ul class="pk-list">{lis}</ul>
<a class="btn {"btn-gold" if feat else "btn-ink"}" href="{href}"{conv}>{esc(btn)}</a></div>''')
    steps = "".join(f'<div class="step"><h3>{esc(h)}</h3><p>{p}</p></div>' for h, p in STEPS)
    faq = ui_kit.faq_accordion([(esc(q), a) for q, a in FAQ], prefix="rd")
    src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in SOURCES)
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Rideshare &amp; delivery drivers</span>
<h1>Rideshare and delivery driver taxes <em>for Uber, Lyft and DoorDash drivers.</em></h1>
<p>Schedule C returns, the 2026 mileage deduction, app 1099s matched, tips reported the right way and quarterly taxes planned, for drivers in New Jersey, New York and across the US. You see the price before we start.</p>
<div class="hero-btns"><a class="btn btn-gold" href="/book/" data-conv="book">Book a 30-minute call</a><a class="btn btn-line" href="#faqs">Driver tax answers</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="who-h"><div class="sec-hd"><span class="eyebrow eb-dark">Who it's for</span><h2 id="who-h">Drivers we help.</h2>
<p>If an app pays you and nobody withholds tax, the IRS usually treats you as running your own business. We start there.</p></div>
<div class="br-who">{who}</div></section>
<section class="wrap llc-sec" id="services" aria-labelledby="sv-h"><div class="sec-hd"><span class="eyebrow eb-dark">Services</span><h2 id="sv-h">Tax and bookkeeping for drivers.</h2>
<p>Pick one or combine them. Tax returns are quoted up front once we know which apps you drive for.</p></div>
<div class="pk br-pk">{"".join(cards)}</div>
<p class="br-note">No mileage log? Our <a href="/bookkeeping-cleanup/">bookkeeping cleanup</a> rebuilds past months from your app trip history and bank records.</p></section>
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="how-h">How driver tax prep works with us.</h2></div>
<div class="br-steps">{steps}</div>
<p class="br-cred">Your return is prepared by Zain Merchant and his team of tax and accounting experts. Zain: ACCA · Big Four (ex-PwC) · PTIN/EFIN tax preparer.</p></section>
<section class="wrap llc-sec" id="compare" aria-labelledby="cmp-h"><div class="sec-hd"><span class="eyebrow eb-dark">Compare</span><h2 id="cmp-h">Standard mileage or actual car costs: which should a driver use?</h2>
<p>Two ways to deduct your car. Both need a mileage log.</p></div>
<div class="cmp-tw"><table class="tbl br-cmp"><thead><tr><th></th><th>Standard mileage rate</th><th>Actual car expenses</th></tr></thead><tbody>
<tr><th scope="row">2026 amount</th><td>72.5¢ a mile (Jan 1–Jun 30), 76¢ a mile (Jul 1–Dec 31)</td><td>Business share of what you actually spent</td></tr>
<tr><th scope="row">What it covers</th><td>Gas, oil, repairs, insurance, tires and depreciation, all built in</td><td>Gas, repairs, insurance, registration, lease or depreciation, each tracked</td></tr>
<tr><th scope="row">Tolls and parking</th><td>Deducted on top</td><td>Deducted on top</td></tr>
<tr><th scope="row">Records</th><td>Mileage log (date, miles, purpose)</td><td>Mileage log plus every receipt</td></tr>
<tr><th scope="row">Often better for</th><td>High-mileage drivers with an efficient car</td><td>Expensive or costly-to-run cars with fewer miles</td></tr>
</tbody></table></div>
<p class="br-note">Run your numbers: <a href="/tools/mileage-deduction-calculator/">mileage deduction calculator</a> · <a href="/tools/quarterly-estimated-tax-calculator/">quarterly estimated tax calculator</a> · <a href="/tools/no-tax-on-tips-calculator/">no tax on tips calculator</a> · <a href="/shop/">rideshare and delivery driver tax tracker</a></p></section>
{lead_box.lead_box("Rideshare and delivery driver taxes", "page-rideshare", "Get your driver tax price.",
    "Tell us which apps you drive for and how you track miles, and we'll email a fixed quote within one business day.",
    [("tax-return", "Tax return (Schedule C)"), ("estimates", "Quarterly estimated taxes"), ("bookkeeping", "Monthly bookkeeping"), ("question", "A quick question first")],
    ["Uber, Lyft, DoorDash, Instacart and Amazon Flex", "Mileage, tips and self-employment tax handled together", "Price confirmed before any work starts"],
    example="For example: I drive Uber full time in NJ and do DoorDash on weekends, about 30,000 miles")}
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">Rideshare and delivery driver tax questions</h2></div>{faq}</section>
<section class="wrap llc-sec" aria-labelledby="src-h"><div class="sec-hd"><span class="eyebrow eb-dark">Sources</span><h2 id="src-h">Checked against the IRS.</h2></div>
<div class="br-src"><div class="sources"><ul>{src}</ul><p class="factline">Facts checked against the pages above on {nice}.</p></div></div></section>
{cta("Drive for the apps? Let's get your taxes right.", "Book a 30-minute call or phone " + TEL + ". Tell us which apps you drive for and how many miles you put on, and we'll quote your return before any work starts.")}
{ui_kit.fineprint("General information, not tax advice for your situation. State returns are not available for Connecticut, Maryland or Oregon. "
                  "Reading this page or booking a call doesn't create a client relationship.")}
</main>'''
    faq_ld = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
        for q, a in FAQ]}
    ld = seo.graph(URL, "Taxes and bookkeeping for rideshare and delivery drivers", DESC, service_node(), faq_ld,
                   crumb=[("Home", BASE + "/"), ("Services", BASE + "/services/"), ("Rideshare driver taxes", URL)],
                   extra={"mainEntity": {"@id": URL + "#service"}})
    return write("rideshare-driver-taxes", page(TITLE, DESC, URL, body, ld, active="s", keywords=KEYWORDS))


if __name__ == "__main__":
    print(build())
