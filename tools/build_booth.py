#!/usr/bin/env python3
"""Builds /booth-renters/ (Site session): taxes and bookkeeping for salon booth renters, barbers, nail techs,
lash and brow artists and other chair renters (self-employed beauty pros).

Rule 25 (Zain 2026-11-16 21:39): every niche gets its own page. Zain 22:05: TikTok/IG/Pinterest niche reels for
"airbnb hosts, rental properties, booth rentals, those small businesses".
No new prices: tax returns quoted up front; bookkeeping from $199/month; quarterly estimates link to the approved page.
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

URL = BASE + "/booth-renters/"
CHECKED = "2026-11-16"
POST = "/quarterly-estimated-taxes/"
KEYWORDS = ["booth renter taxes", "salon booth rental taxes", "barber taxes", "hair stylist tax deductions",
            "nail tech taxes", "lash tech taxes", "self-employed cosmetologist taxes", "no tax on tips self-employed",
            "booth rent deduction", "quarterly taxes for hair stylists"]
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'
TEL = '<a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>'

WHO = [
    ("Booth and chair renters", "You pay the salon or shop for your chair or suite and keep your own clients, prices and schedule."),
    ("Barbers and stylists", "Haircuts, color and extensions, paid in cash, card, app payments and tips."),
    ("Nail, lash and brow techs", "Manicurists, lash and brow artists, makeup artists and skincare specialists working for themselves."),
    ("Suite owners and salon owners", "You rent chairs to other pros, or you just moved into your own suite and need the books set up."),
]

SERVICES = [
    ("Every tax season", "Booth renter tax return", "Quoted", "up front, by return",
     "Your Form 1040 with Schedule C and Schedule SE, federal and state, with every chair-renter deduction checked.",
     ["Booth rent, products and tools sorted", "Card, app and cash income matched to your 1099-K and 1099-NEC forms",
      "Tips reported and the tips deduction checked", "Self-employment tax worked out"],
     "/book/", "Get a quote", True),
    ("All year", "Bookkeeping for beauty pros", "From $199", "/ month",
     "Monthly books so you always know what you made after booth rent and products.",
     ["Income tracked by payment app and cash", "Booth rent, supplies and education logged", "Mileage and phone business share",
      "Year-end package ready for your return"],
     "/services/#bookkeeping", "How bookkeeping works", False),
    ("Four times a year", "Quarterly estimated taxes", "Planned", "with you",
     "No employer withholds tax for you, so we work out what to send the IRS and your state each quarter.",
     ["Payment amounts and due dates", "Reminders before each deadline", "Adjusted when your income changes"],
     "/quarterly-estimated-taxes/", "See quarterly estimates", False),
]

STEPS = [
    ("Book a call", 'Pick a time on our <a href="/book/" data-conv="book">booking page</a> or call ' + TEL +
     ". Tell us how you get paid (cash, card, apps) and what you pay for your booth."),
    ("Get your price", "You get a written quote before any work starts. Nothing is charged until you agree to it."),
    ("We prepare and file", "We match your income forms, sort your expenses, prepare your return and walk you through it before we e-file."),
]

# Answer-first: every answer starts with the direct answer in one sentence (AI-search friendly), then the detail.
FAQ = [
    ("Am I self-employed if I rent a booth?",
     "Usually yes. If you rent your chair or suite, keep your own clients and set your own prices and hours, you are generally "
     "running your own business. You report your income and expenses on Schedule C and pay self-employment tax on your profit."),
    ("How much is self-employment tax?",
     "15.3% of your net earnings from self-employment: 12.4% for Social Security and 2.9% for Medicare. It usually applies once "
     "your net earnings are $400 or more, and it's figured on Schedule SE. Half of it is deductible when you work out your income tax."),
    ("Is my booth rent tax deductible?",
     "Yes. Rent you pay for the chair, booth or suite you work from is a business expense on Schedule C, along with products, tools, "
     "license renewals, education, booking software and the business share of your phone."),
    ("Do I have to report cash tips?",
     "Yes. Tips are income whether they come in cash, by card or through an app. When you're self-employed they're part of your "
     "business income on Schedule C. Keep a daily record so your numbers match what your payment apps report."),
    ("Does no tax on tips apply to booth renters?",
     "It can. From 2025 through 2028, employees and self-employed people may deduct qualified tips, up to $25,000 a year, whether or "
     "not they itemize. Barbers, hairdressers, hairstylists, cosmetologists, manicurists, makeup artists, skincare specialists and "
     "eyebrow and eyelash technicians are on the IRS list of tipped occupations. The deduction phases out above $150,000 of modified "
     "AGI ($300,000 joint), and some self-employed businesses are excluded, so we check that you qualify."),
    ("Do I need to pay quarterly taxes?",
     'Most booth renters do, because no employer withholds tax from what clients pay you. Federal estimates for 2026 income are due '
     'April 15, June 15 and September 15, 2026 and January 15, 2027. See <a href="/quarterly-estimated-taxes/">quarterly estimated taxes</a>.'),
    ("Will I get a 1099 from Square, Venmo or my booking app?",
     "You may get a Form 1099-K from a payment app or card processor, and a 1099-NEC from a salon that pays you $2,000 or more for "
     "work in 2026. Either way, all your income is taxable, including cash, so we match every form to your records."),
    ("Do you work with booth renters outside New Jersey?",
     "Yes. We prepare federal returns for every state and state returns for every state except Connecticut, Maryland and Oregon."),
]

SOURCES = [
    ("IRS: Topic 554, Self-employment tax", "https://www.irs.gov/taxtopics/tc554"),
    ("IRS: One, Big, Beautiful Bill Act tax deductions for working Americans and seniors (no tax on tips)",
     "https://www.irs.gov/newsroom/one-big-beautiful-bill-act-tax-deductions-for-working-americans-and-seniors"),
    ("IRS: Occupations that customarily and regularly received tips on or before Dec. 31, 2024",
     "https://www.irs.gov/forms-pubs/occupations-that-customarily-and-regularly-received-tips-on-or-before-dec-31-2024"),
    ("IRS: Publication 334, Tax Guide for Small Business", "https://www.irs.gov/publications/p334"),
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

TITLE = "Booth Renter Taxes for Stylists, Barbers & Nail Techs | MFA"
DESC = ("Tax returns, bookkeeping and quarterly taxes for salon booth renters, barbers, nail and lash techs. Schedule C, tips, "
        "booth rent deductions.")


def service_node():
    o = seo._offer
    return {"@type": "Service", "@id": URL + "#service", "name": "Taxes and bookkeeping for booth renters and beauty pros", "url": URL,
            "serviceType": "Tax preparation and bookkeeping for self-employed booth renters (Schedule C, Schedule SE, tips, estimated taxes)",
            "description": DESC, "provider": {"@id": seo.ORG_ID}, "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "Audience", "audienceType": "Salon booth renters, barbers, nail, lash and brow technicians"},
            "offers": [o("Booth renter tax return (Schedule C + SE)", None, "Quoted up front by return type.", url=URL + "#services"),
                       o("Bookkeeping for booth renters", 199, "Monthly bookkeeping from $199/month.", url=BASE + "/services/#bookkeeping")]}


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
    faq = ui_kit.faq_accordion([(esc(q), a) for q, a in FAQ], prefix="br")
    src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in SOURCES)
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Booth renters &amp; beauty pros</span>
<h1>Booth renter taxes <em>for stylists, barbers and nail techs.</em></h1>
<p>Schedule C returns, booth rent and supply deductions, tips reported the right way and quarterly taxes planned, for chair and suite renters in New Jersey, New York and across the US. You see the price before we start.</p>
<div class="hero-btns"><a class="btn btn-gold" href="/book/" data-conv="book">Book a 30-minute call</a><a class="btn btn-line" href="#faqs">Booth renter tax answers</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="who-h"><div class="sec-hd"><span class="eyebrow eb-dark">Who it's for</span><h2 id="who-h">Beauty pros we help.</h2>
<p>If you rent your chair and run your own book, the IRS usually treats you as a business owner. We start there.</p></div>
<div class="br-who">{who}</div></section>
<section class="wrap llc-sec" id="services" aria-labelledby="sv-h"><div class="sec-hd"><span class="eyebrow eb-dark">Services</span><h2 id="sv-h">Tax and bookkeeping for booth renters.</h2>
<p>Pick one or combine them. Tax returns are quoted up front once we know how you get paid.</p></div>
<div class="pk br-pk">{"".join(cards)}</div>
<p class="br-note">Behind on records? Our <a href="/bookkeeping-cleanup/">bookkeeping cleanup</a> sorts past months by payment app and expense type.</p></section>
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="how-h">How booth renter tax prep works with us.</h2></div>
<div class="br-steps">{steps}</div>
<p class="br-cred">Your return is prepared by Zain Merchant and his team of tax and accounting experts. Zain: ACCA · Big Four (ex-PwC) · PTIN/EFIN tax preparer.</p></section>
<section class="wrap llc-sec" id="compare" aria-labelledby="cmp-h"><div class="sec-hd"><span class="eyebrow eb-dark">Compare</span><h2 id="cmp-h">Booth renter or salon employee: how are taxes different?</h2>
<p>The same chair, two very different tax returns.</p></div>
<div class="cmp-tw"><table class="tbl br-cmp"><thead><tr><th></th><th>Booth renter</th><th>Salon employee</th></tr></thead><tbody>
<tr><th scope="row">Tax form</th><td>Schedule C and Schedule SE</td><td>W-2 from the salon</td></tr>
<tr><th scope="row">Social Security and Medicare</th><td>You pay all 15.3% as self-employment tax</td><td>7.65% withheld; the salon pays the other 7.65%</td></tr>
<tr><th scope="row">Income tax</th><td>Nothing withheld: pay quarterly estimates</td><td>Withheld from each paycheck</td></tr>
<tr><th scope="row">Booth rent, supplies, tools</th><td>Deductible on Schedule C</td><td>Generally not deductible on your federal return</td></tr>
<tr><th scope="row">Tips</th><td>Business income; tips deduction up to your net profit</td><td>Reported to the salon, on your W-2; tips deduction applies</td></tr>
<tr><th scope="row">Prices, hours, clients</th><td>You decide</td><td>The salon decides</td></tr>
</tbody></table></div>
<p class="br-note">Run your numbers: <a href="/tools/no-tax-on-tips-calculator/">no tax on tips calculator</a> · <a href="/tools/quarterly-estimated-tax-calculator/">quarterly estimated tax calculator</a> · <a href="/answers/">short tax answers for booth renters</a></p></section>
{lead_box.lead_box("Booth renter taxes", "page-booth", "Get your booth renter price.",
    "Tell us what you do and how you get paid, and we'll email a fixed quote within one business day.",
    [("tax-return", "Tax return (Schedule C)"), ("estimates", "Quarterly estimated taxes"), ("bookkeeping", "Monthly bookkeeping"), ("question", "A quick question first")],
    ["Stylists, barbers, nail, lash and brow techs", "Tips, booth rent and self-employment tax handled together", "Price confirmed before any work starts"])}
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">Booth renter tax questions</h2></div>{faq}</section>
<section class="wrap llc-sec" aria-labelledby="src-h"><div class="sec-hd"><span class="eyebrow eb-dark">Sources</span><h2 id="src-h">Checked against the IRS.</h2></div>
<div class="br-src"><div class="sources"><ul>{src}</ul><p class="factline">Facts checked against the pages above on {nice}.</p></div></div></section>
{cta("Rent a booth? Let's get your taxes right.", "Book a 30-minute call or phone " + TEL + ". Tell us how you get paid and what you pay for your booth, and we'll quote your return before any work starts.")}
{ui_kit.fineprint("General information, not tax advice for your situation. State returns are not available for Connecticut, Maryland or Oregon. "
                  "Reading this page or booking a call doesn't create a client relationship.")}
</main>'''
    faq_ld = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
        for q, a in FAQ]}
    ld = seo.graph(URL, "Taxes and bookkeeping for booth renters and beauty pros", DESC, service_node(), faq_ld,
                   crumb=[("Home", BASE + "/"), ("Services", BASE + "/services/"), ("Booth renter taxes", URL)],
                   extra={"mainEntity": {"@id": URL + "#service"}})
    return write("booth-renters", page(TITLE, DESC, URL, body, ld, active="s", keywords=KEYWORDS))


if __name__ == "__main__":
    print(build())
