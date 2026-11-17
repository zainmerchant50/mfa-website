#!/usr/bin/env python3
"""Builds /rental-property-taxes/ (Site session): tax returns and bookkeeping for landlords and short-term rental hosts.

Zain approved the page in chat on 2026-11-16 ("go ahead on the rental property page"; standing rule the same night:
a new niche gets its own page without asking). Real estate / STR lane (rule 24, sprint 1).
No new prices: tax preparation is "quoted up front" and monthly bookkeeping is "from $199/month" (both already approved,
see build_services.py). Every fact in the FAQ was checked on irs.gov (or the NJ/NY sources the Nov 16 rental post uses)
on CHECKED and is listed in SOURCES. Never "free", never "CPA", no street address.
Run via tools/build_resources.py (it calls build()).
"""
from datetime import date

import re

import build_blog as B
import seo
import ui_kit
from build_resources import page, write, esc, BASE, cta

URL = BASE + "/rental-property-taxes/"
CHECKED = "2026-11-16"
POST = "/blog/rental-property-repairs-vs-improvements-2026/"
KEYWORDS = ["rental property tax preparation", "Schedule E tax help", "landlord accountant NJ", "rental property accountant NY",
            "short-term rental taxes", "Airbnb host taxes", "rental property bookkeeping", "rental property depreciation",
            "rental property tax deductions", "passive loss rental property"]
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'
TEL = '<a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>'

WHO = [
    ("Long-term landlords", "One rental or a small portfolio of houses, condos or multi-family units, reported on Schedule E."),
    ("Short-term rental hosts", "Airbnb and Vrbo hosts, including hosts who offer cleaning or linen service, which can move the rental to Schedule C."),
    ("Owners who also use the home", "A vacation home or a room you rent part of the year, where personal-use days change what you can deduct."),
    ("New or first-year owners", "You just bought or converted a property and need depreciation set up correctly from day one."),
]

SERVICES = [
    ("Every tax season", "Rental property tax return", "Quoted", "up front, by return",
     "Your Form 1040 with Schedule E (or Schedule C for a short-term rental with substantial services), federal and state.",
     ["Rental income and expenses sorted and checked", "Depreciation schedule set up or reviewed",
      "Repairs vs improvements and safe-harbor elections", "Passive loss limits applied"],
     "/book/", "Get a quote", True),
    ("All year", "Rental property bookkeeping", "From $199", "/ month",
     "Monthly books for your rentals, so tax season is a review, not a scramble.",
     ["Income and expenses tracked by property", "Bank and card reconciliations", "Repairs and improvements kept separate",
      "Year-end package ready for your return"],
     "/services/#bookkeeping", "How bookkeeping works", False),
    ("Behind on records?", "Rental books cleanup", "Quoted", "up front",
     "Missing statements, mixed personal and rental spending, or a property you never set up for depreciation.",
     ["Past-year transactions sorted by property", "Missed depreciation identified", "Clean starting point for this year"],
     "/bookkeeping-cleanup/", "Request a cleanup quote", False),
]

STEPS = [
    ("Book a call", 'Pick a time on our <a href="/book/" data-conv="book">booking page</a> or call ' + TEL +
     ". We ask how many properties you have, how you rent them and what records you keep."),
    ("Get your price", "You get a written quote before any work starts. Nothing is charged until you agree to it."),
    ("We prepare and file", "We sort your rental income and expenses, set up depreciation, prepare your return and walk you through it before we e-file."),
]

# Answer-first: every answer starts with the direct answer in one sentence (AI-search friendly), then the detail.
FAQ = [
    ("Where do I report rental income?",
     "On Schedule E (Form 1040), which carries to your Form 1040. If you provide substantial services mainly for your guests' "
     "convenience, such as regular cleaning, changing linen or maid service, the IRS says to report the income and expenses on "
     "Schedule C instead. That is common for short-term rentals with hotel-style service."),
    ("What rental property expenses can I deduct?",
     "Ordinary rental costs such as mortgage interest, property tax, insurance, repairs, maintenance and management fees. "
     "Improvements are different: they are capitalized and depreciated instead of deducted in one year. The IRS advises keeping "
     "repairs and improvements separate in your records."),
    ("How does rental property depreciation work?",
     "Residential rental property is depreciated over 27.5 years, starting when it is ready and available for rent, even before "
     "the first tenant moves in. Land can't be depreciated, so only the building's share of your cost counts."),
    ("Is a new roof a repair or an improvement?",
     "Generally an improvement, depreciated over 27.5 years. IRS Publication 527 lists a new roof, a furnace, central air and "
     "kitchen modernization as improvements. Three safe harbors can let you deduct more in the year you pay, including the "
     f'$2,500 per item de minimis safe harbor. Our <a href="{POST}">repairs vs improvements guide</a> explains all three.'),
    ("Do I pay tax if I rent my home for fewer than 15 days?",
     "No. If you use a dwelling unit as a home and rent it for fewer than 15 days in the year, you don't report the rental income "
     "and you don't deduct the rental expenses."),
    ("When does personal use make my rental a home for tax purposes?",
     "When your personal use is more than the greater of 14 days or 10% of the days you rent it at a fair price. Then your "
     "rental deductions are limited, so a vacation home you also use needs a careful split of days and expenses."),
    ("Can I deduct a rental loss against my salary?",
     "Sometimes, up to $25,000 a year. If you actively participate in the rental, you may deduct up to $25,000 of rental loss "
     "from other income. The allowance shrinks once your modified AGI passes $100,000 and is generally gone at $150,000 "
     "($50,000 and $75,000 if married filing separately). Losses above that carry forward."),
    ("Are security deposits and advance rent taxable?",
     "Advance rent is taxable in the year you receive it. A security deposit you plan to return isn't income when you get it; "
     "if you keep part of it, or apply it as final rent, that part is income then."),
    ("Do you handle New Jersey and New York rentals?",
     "Yes. New York starts from your federal adjusted gross income, so your federal Schedule E figures generally carry over. "
     "New Jersey treats net rental income as its own category and has its own depreciation rules, so some federal amounts need "
     "a state adjustment. We prepare state returns for every state except Connecticut, Maryland and Oregon."),
]

SOURCES = [
    ("IRS: Publication 527, Residential Rental Property", "https://www.irs.gov/publications/p527"),
    ("IRS: Topic 415, Renting residential and vacation property", "https://www.irs.gov/taxtopics/tc415"),
    ("IRS: Tangible property final regulations (repairs, improvements, safe harbors)",
     "https://www.irs.gov/businesses/small-businesses-self-employed/tangible-property-final-regulations"),
    ("NJ Division of Taxation: GIT-DEP, Depreciation and other adjustments", "https://www.nj.gov/treasury/taxation/pdf/current/gitdep.pdf"),
    ("NY Department of Taxation and Finance: Instructions for Form IT-201", "https://www.tax.ny.gov/pdf/current_forms/it/it201i.pdf"),
]

CSS = """<style>
.rp-who{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:6px}
.rp-who .card{padding:22px 24px;background:#fff;border:1px solid var(--hair);border-radius:16px}
.rp-who h3{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:1.35rem;color:var(--navy);margin:0 0 6px}
.rp-who p{margin:0;font-size:.92rem;line-height:1.6;color:var(--muted)}
.pk.rp-pk{grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
@media (max-width:1000px){.pk.rp-pk{grid-template-columns:1fr}}
.rp-pk .pkc{padding:28px 24px 24px}.rp-pk .pk-price b{font-size:2.3rem}
.rp-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;counter-reset:s;margin-top:6px}
.rp-steps .step{padding:26px;border-top:2px solid var(--gold,#B08D3F);background:#fff;border-radius:0 0 12px 12px}
.rp-steps .step:before{counter-increment:s;content:"0" counter(s);font-family:'Cormorant Garamond',Georgia,serif;font-size:38px;color:var(--gold,#B08D3F);display:block;line-height:1;margin-bottom:10px}
.rp-steps .step h3{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.6rem;font-weight:500;margin:0 0 8px;color:var(--ink,#10233F)}
.rp-steps .step p{margin:0;color:var(--muted);font-size:.95rem;line-height:1.7}
.rp-steps .step p a,#faqs .faq-a-in a,.rp-note a{color:var(--navy);border-bottom:1px solid var(--gold);transition:color .3s}
.rp-steps .step p a:hover,#faqs .faq-a-in a:hover,.rp-note a:hover{color:var(--gold)}
@media (max-width:860px){.rp-steps{grid-template-columns:1fr}}
.rp-cred,.rp-note{margin:18px 0 0;font-size:.88rem;color:var(--muted)}
.rp-src{max-width:860px}.rp-src ul{margin:6px 0 0;padding-left:20px;display:grid;gap:8px}.rp-src li{font-size:.92rem;line-height:1.55}
.rp-src li::marker{color:var(--gold)}.rp-src li a{color:var(--navy);border-bottom:1px solid rgba(176,141,63,.5);text-decoration:none}
.rp-src li a:hover{color:var(--gold)}.rp-src .factline{margin:16px 0 0;font-size:.86rem;color:var(--muted)}
</style>"""

TITLE = "Rental Property Tax Preparation & Bookkeeping | MFA"
DESC = ("Rental property tax returns (Schedule E), depreciation and short-term rental taxes for landlords and Airbnb hosts "
        "in NJ, NY and nationwide.")


def service_node():
    o = seo._offer
    return {"@type": "Service", "@id": URL + "#service", "name": "Rental property tax preparation and bookkeeping", "url": URL,
            "serviceType": "Tax preparation and bookkeeping for rental property owners (Schedule E, depreciation, short-term rentals)",
            "description": DESC, "provider": {"@id": seo.ORG_ID}, "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "Audience", "audienceType": "Landlords and short-term rental hosts"},
            "offers": [o("Rental property tax return (Schedule E or Schedule C)", None, "Quoted up front by return type.", url=URL + "#services"),
                       o("Rental property bookkeeping", 199, "Monthly bookkeeping from $199/month.", url=BASE + "/services/#bookkeeping")]}


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
    faq = ui_kit.faq_accordion([(esc(q), a) for q, a in FAQ], prefix="rp")
    src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in SOURCES)
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Landlords &amp; short-term rentals</span>
<h1>Rental property tax preparation <em>for landlords and Airbnb hosts.</em></h1>
<p>Schedule E returns, depreciation set up right, repairs sorted from improvements and passive loss limits applied, for long-term rentals and short-term rentals in New Jersey, New York and across the US. You see the price before we start.</p>
<div class="hero-btns"><a class="btn btn-gold" href="/book/" data-conv="book">Book a 30-minute call</a><a class="btn btn-line" href="#faqs">Rental tax answers</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="who-h"><div class="sec-hd"><span class="eyebrow eb-dark">Who it's for</span><h2 id="who-h">Rental property owners we help.</h2>
<p>How you rent decides which form you file and what you can deduct, so we start there.</p></div>
<div class="rp-who">{who}</div></section>
<section class="wrap llc-sec" id="services" aria-labelledby="sv-h"><div class="sec-hd"><span class="eyebrow eb-dark">Services</span><h2 id="sv-h">Rental property tax and bookkeeping services.</h2>
<p>Pick one or combine them. Tax returns and cleanups are quoted up front once we know your properties.</p></div>
<div class="pk rp-pk">{"".join(cards)}</div>
<p class="rp-note">Fixing up a rental this year? Read <a href="{POST}">rental property repairs vs improvements</a> before you pay the invoices.</p></section>
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="how-h">How rental property tax prep works with us.</h2></div>
<div class="rp-steps">{steps}</div>
<p class="rp-cred">Your return is prepared by Zain Merchant and his team of tax and accounting experts. Zain: ACCA · Big Four (ex-PwC) · PTIN/EFIN tax preparer.</p></section>
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">Rental property tax questions</h2></div>{faq}</section>
<section class="wrap llc-sec" aria-labelledby="src-h"><div class="sec-hd"><span class="eyebrow eb-dark">Sources</span><h2 id="src-h">Checked against the IRS.</h2></div>
<div class="rp-src"><div class="sources"><ul>{src}</ul><p class="factline">Facts checked against the pages above on {nice}.</p></div></div></section>
{cta("Own a rental? Let's get it right.", "Book a 30-minute call or phone " + TEL + ". Tell us how many properties you have and how you rent them, and we'll quote your return before any work starts.")}
{ui_kit.fineprint("General information, not tax advice for your situation. State returns are not available for Connecticut, Maryland or Oregon. "
                  "Reading this page or booking a call doesn't create a client relationship.")}
</main>'''
    faq_ld = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
        for q, a in FAQ]}
    ld = seo.graph(URL, "Rental property tax preparation and bookkeeping", DESC, service_node(), faq_ld,
                   crumb=[("Home", BASE + "/"), ("Services", BASE + "/services/"), ("Rental property taxes", URL)],
                   extra={"mainEntity": {"@id": URL + "#service"}})
    return write("rental-property-taxes", page(TITLE, DESC, URL, body, ld, active="s", keywords=KEYWORDS))


if __name__ == "__main__":
    print(build())
