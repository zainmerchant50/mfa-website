#!/usr/bin/env python3
"""Builds /artists/ (Site session): taxes for artists and creatives.

Zain, 2026-10-25: "can we add tags to SEO for international students and art folks' tax filings and their tax savings."
For freelance and self-employed visual artists, illustrators, photographers, musicians, crafters and Etsy art sellers.
No new prices: every price here is an existing public price (Schedule C returns are quoted up front like every tax return;
monthly bookkeeping from $199/month; LLC formation from $150 plus the state fee; quarterly estimated tax service $250 for the
year). Shop products are pulled from catalog/products.json (status "live" only). Every tax fact was checked on irs.gov on
CHECKED and is listed in SOURCES; sales tax stays general and points to each state's revenue department.
Never "free", never "CPA" (except the approved credential line), no street address, no partner or software vendor names.
Run via tools/build_resources.py (it calls build()).
"""
from datetime import date

import build_blog as B
import build_llc as L
import seo
import ui_kit
from build_resources import page, write, esc, BASE, cta

URL = BASE + "/artists/"
OG_IMG = URL + "og.png"   # rendered from content/graphics/artists-og.html (tools/render_graphics.js)
CHECKED = "2026-10-25"
STATES_OUT = "Connecticut, Maryland or Oregon"
STATES_EXCEPT = "Connecticut, Maryland and Oregon"
STATE_CODES = ["CT", "MD", "OR"]   # the only states we don't prepare returns for (Zain, 2026-10-25)
KEYWORDS = ["artist taxes", "tax deductions for artists", "self-employed artist tax return", "do artists need an LLC",
            "art business bookkeeping", "Etsy artist 1099-K", "tax savings for artists", "Schedule C for artists",
            "musician taxes", "photographer taxes", "art fair sales tax"]
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'
TEL = '<a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>'
LNK = lambda href, text: f'<a href="{href}">{text}</a>'

WHO = [
    ("Visual artists & illustrators", "Commissions, originals, prints and licensing, paid by clients, galleries or platforms."),
    ("Photographers & filmmakers", "Shoots, prints and stock sales, with cameras, lenses and editing software to write off."),
    ("Musicians & performers", "Gigs, lessons, session work and merch, plus instruments, gear and travel to shows."),
    ("Crafters & Etsy art sellers", "Handmade goods sold online and at art fairs, with a Form 1099-K from the platform or payment app."),
]

# Tax deductions for artists: (title, body). Only rules verified on irs.gov (see SOURCES).
DEDUCT = [
    ("Art supplies and materials", "Paint, canvas, paper, clay, film, strings. Supplies go on Schedule C line 22; materials that "
     "become pieces you sell are counted in cost of goods sold instead."),
    ("Studio rent or a home studio", "Studio rent is a business expense. A home studio counts only if that space is used regularly "
     "and exclusively for your art business; the simplified method allows $5 per square foot, up to 300 square feet."),
    ("Equipment and software", "Cameras, computers, instruments, kilns and design software are usually depreciated, but Section 179 "
     "or bonus depreciation can let you deduct them in the first year."),
    ("Art-fair booth fees and marketing", "Booth and jury fees, your website, ads, business cards and portfolio printing are costs of "
     "selling your work."),
    ("Shipping and packaging", "Postage, boxes, tubes and packing materials for the orders you ship."),
    ("Platform and payment fees", "Marketplace listing and transaction fees, payment-processing fees and commissions galleries keep."),
    ("Business mileage", "Driving to fairs, galleries, suppliers and clients, at the IRS standard mileage rate or your actual costs. "
     "Keep a log as you go."),
    ("Classes and workshops", "Deductible when they maintain or improve skills you already use in your art business, not when they "
     "qualify you for a new line of work."),
]

FAQ = [
    ("Is my art a hobby or a business for taxes?",
     "It depends on whether you run it to make a profit. The IRS weighs nine factors, including whether you keep complete books and "
     "records, the time and effort you put in, whether you change methods to improve profitability, and whether you've made a "
     "profit in some years. No single factor decides it. Either way, the income has to be reported. Running it as a business is what "
     "lets you deduct your expenses on Schedule C. Hobby expenses can't be deducted at all, and a 2025 tax law made that permanent."),
    ("What tax deductions can artists take?",
     "Expenses that are ordinary (common and accepted in your field) and necessary (helpful and appropriate for your business): "
     "supplies and materials, studio rent or a home studio, equipment and software, booth fees and marketing, shipping, platform and "
     "payment fees, business mileage and classes that improve the skills you already use. Keep receipts and a mileage log. "
     "See the list of tax deductions for artists on this page."),
    ("I got a 1099-K from Etsy or a payment app. Is all of it taxable?",
     "No. Form 1099-K shows the gross amount of payments, with nothing taken off for fees, refunds, shipping or discounts. Those "
     "aren't income, so you report your real sales and then deduct fees, shipping and your other costs on Schedule C. Payment apps "
     "and marketplaces send a 1099-K when your payments top $20,000 and 200 transactions. Card payments have no minimum, "
     "and some states set lower limits. Income is taxable whether or not you get a form."),
    ("Do artists pay self-employment tax?",
     "Yes, once your net earnings from self-employment reach $400. Self-employment tax is 15.3%: 12.4% for Social Security and 2.9% "
     "for Medicare, figured on Schedule SE. You can deduct half of it from your income on Form 1040."),
    ("Do I need to make quarterly estimated tax payments?",
     "Usually, if you expect to owe $1,000 or more when you file, because no employer is withholding tax from your art income. Most "
     "people avoid the underpayment penalty by paying at least 90% of this year's tax or 100% of the tax on last year's return, "
     "whichever is smaller. Payments are figured with Form 1040-ES across four payment periods a year. Our quarterly estimated tax "
     "service is $250 for the year."),
    ("Do artists need an LLC?",
     "Not for taxes. By default the IRS ignores a single-member LLC for income tax (a \"disregarded entity\"), so you still report your art income on Schedule C with "
     "your Form 1040 and still pay self-employment tax. An LLC can elect to be taxed as a corporation, which only makes sense once "
     "profits are steady; we run the numbers first. What an LLC does add is a separate legal business for contracts, bank accounts and "
     "state filings, with state fees that vary by state. Questions about personal liability are for an attorney."),
    ("Do I charge sales tax at art fairs?",
     "Sales tax is set by each state, not the IRS, and rules, rates and temporary-vendor permits differ by state and sometimes by city. "
     "Selling in person can mean registering with that state and collecting its sales tax, and some events ask for your permit number. "
     "Check the revenue department for each state where you sell. Sales tax you collect from buyers and pass on to the state isn't your income."),
    ("Which state returns don't you prepare?",
     f"State returns are available for every state except {STATES_EXCEPT}, the same as our other tax services. That includes New Jersey, New York and California, and we can do your federal return wherever you live."),
]
FAQ_LINKS = {   # answer index -> (phrase in the answer, link) for the on-page version (JSON-LD keeps plain text)
    1: ("See the list of tax deductions for artists on this page.", LNK("#deductions", "See the list of tax deductions for artists") + " on this page."),
    4: ("Our quarterly estimated tax service is $250 for the year.", "Our " + LNK("/tools/quarterly-estimated-tax-calculator/", "quarterly estimated tax calculator")
        + " shows the numbers, and our quarterly estimated tax service is $250 for the year."),
    5: ("which only makes sense once profits are steady; we run the numbers first.", "which only makes sense once profits are steady; "
        + LNK("/tools/s-corp-tax-savings-calculator/", "we run the numbers first") + "."),
    6: ("Check the revenue department for each state where you sell.", "Check the revenue department for each state where you sell. "
        "Selling in New Jersey? Read our " + LNK("/blog/nj-sales-tax-st50-filing-guide/", "NJ sales tax guide") + "."),
}

SOURCES = [
    ("IRS: Earning side income: is it a hobby or a business? (the nine factors)", "https://www.irs.gov/newsroom/earning-side-income-is-it-a-hobby-or-a-business"),
    ("IRS: Paying taxes on hobby activities (reporting hobby income)", "https://www.irs.gov/newsroom/heres-what-taxpayers-need-to-know-about-paying-taxes-on-their-hobby-activities"),
    ("IRS: Publication 525 (2025), Taxable and Nontaxable Income (activity not for profit: hobby income and expenses)", "https://www.irs.gov/publications/p525"),
    ("IRS: Schedule C (Form 1040) 2025, Profit or Loss From Business", "https://www.irs.gov/pub/irs-pdf/f1040sc.pdf"),
    ("IRS: Publication 334 (2025), Tax Guide for Small Business", "https://www.irs.gov/pub/irs-prior/p334--2025.pdf"),
    ("IRS: Guide to business expense resources", "https://www.irs.gov/forms-pubs/guide-to-business-expense-resources"),
    ("IRS: About Form 2106 (what ordinary and necessary means)", "https://www.irs.gov/forms-pubs/about-form-2106"),
    ("IRS: Simplified option for home office deduction", "https://www.irs.gov/businesses/small-businesses-self-employed/simplified-option-for-home-office-deduction"),
    ("IRS: Topic no. 513, Work-related education expenses", "https://www.irs.gov/taxtopics/tc513"),
    ("IRS: Form 1099-K FAQs, general information", "https://www.irs.gov/newsroom/form-1099-k-frequently-asked-questions-general-information"),
    ("IRS: Self-employment tax (Social Security and Medicare taxes)", "https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-and-medicare-taxes"),
    ("IRS: Estimated taxes", "https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes"),
    ("IRS: Single member limited liability companies", "https://www.irs.gov/node/10442"),
]

# Shop products for artists (catalog/products.json slugs; only status "live" ones are shown).
PRODUCTS = ["self-employed-tax-deduction-tracker-2026", "1099-self-employed-tax-calculator-2026", "online-seller-bookkeeping-sheet",
            "irs-mileage-log-2026"]

STEPS = [
    ("Book a call", 'Pick a time on our <a href="/book/" data-conv="book">booking page</a> or call ' + TEL +
     ". We look at what you sell and where, and quote before any work starts."),
    ("Send your records", "Your 1099s and 1099-Ks, sales reports, receipts and mileage log through a secure upload link. "
     "No books yet? We set them up."),
    ("We prepare and file", "We prepare your return with Schedule C, walk you through it and e-file once you've signed. "
     "Then we map out next year's quarterly payments."),
]

CSS = """<style>
.ar-who{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:6px}
.ar-who .card{padding:22px 24px;background:#fff;border:1px solid var(--hair);border-radius:16px}
.ar-who h3,.ar-prod h3{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:1.35rem;color:var(--navy);margin:0 0 6px;line-height:1.2}
.ar-who p{margin:0;font-size:.92rem;line-height:1.6;color:var(--muted)}
.ar-ded{list-style:none;padding:0;margin:6px 0 0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.ar-ded li{display:flex;gap:12px;align-items:flex-start;background:#fff;border:1px solid var(--hair);border-radius:14px;padding:16px 18px}
.ar-ded svg{width:18px;height:18px;flex-shrink:0;margin-top:3px;color:var(--gold)}
.ar-ded b{display:block;font-size:.98rem;color:var(--navy);margin-bottom:2px}.ar-ded span{font-size:.9rem;line-height:1.55;color:var(--muted)}
.js .ar-ded li{opacity:0;transform:translateY(12px);transition:opacity .6s cubic-bezier(.16,1,.3,1),transform .6s cubic-bezier(.16,1,.3,1),border-color .3s}
.js .ar-ded.in li{opacity:1;transform:none}.ar-ded li:hover{border-color:var(--gold)}
@media (max-width:760px){.ar-ded{grid-template-columns:1fr}}
.pk.ar-pk{grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}
@media (max-width:1180px){.pk.ar-pk{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:640px){.pk.ar-pk{grid-template-columns:1fr}}
.ar-pk .pkc{padding:28px 24px 24px}.ar-pk .pk-price b{font-size:2.3rem}.ar-pk .pk-price span{flex-basis:100%}
.ar-note{max-width:980px;margin:16px 0 0;font-size:.88rem;color:var(--muted)}
.ar-note a,.ar-steps .step p a,#faqs .faq-a-in a{color:var(--navy);border-bottom:1px solid var(--gold);transition:color .3s}
.ar-note a:hover,.ar-steps .step p a:hover,#faqs .faq-a-in a:hover{color:var(--gold)}
.ar-prod{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:6px}
.ar-prod .card{display:flex;flex-direction:column;padding:20px 22px;background:#fff;border:1px solid var(--hair);border-radius:16px}
.ar-prod .pb-fmt{font-size:9.5px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--gold)}
.ar-prod h3{font-size:1.22rem;margin:6px 0}.ar-prod p{margin:0 0 14px;font-size:.88rem;line-height:1.55;color:var(--muted);flex:1}
.ar-prod .pb-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.ar-prod .pb-price{font-size:1.1rem;font-weight:700;color:var(--navy)}
.ar-prod .btn{padding:10px 18px}
.ar-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;counter-reset:s;margin-top:6px}
.ar-steps .step{padding:26px;border-top:2px solid var(--gold, #B08D3F);background:#fff;border-radius:0 0 12px 12px}
.ar-steps .step:before{counter-increment:s;content:"0" counter(s);font-family:'Cormorant Garamond',Georgia,serif;font-size:38px;color:var(--gold, #B08D3F);display:block;line-height:1;margin-bottom:10px}
.ar-steps .step h3{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.6rem;font-weight:500;margin:0 0 8px;color:var(--ink, #10233F)}
.ar-steps .step p{margin:0;color:var(--muted);font-size:.95rem;line-height:1.7}
.ar-cred{margin:18px 0 0;font-size:.88rem;color:var(--muted)}
@media (max-width:860px){.ar-steps{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){.js .ar-ded li{opacity:1;transform:none;transition:none}}
.ar-src{max-width:860px}.ar-src .sources{margin-top:0;padding-top:0;border-top:0}
.ar-src ul{margin:6px 0 0;padding-left:20px;display:grid;gap:8px}.ar-src li{font-size:.92rem;line-height:1.55}.ar-src li::marker{color:var(--gold)}
.ar-src li a{color:var(--navy);border-bottom:1px solid rgba(176,141,63,.5);text-decoration:none;transition:color .3s,border-color .3s}.ar-src li a:hover{color:var(--gold);border-color:var(--gold)}
.ar-src .factline{margin:16px 0 0;font-size:.86rem;color:var(--muted)}
</style>"""

# Staggered entrance for the deductions list (same pattern as the /international-students/ checklist).
DED_JS = """<script>(function(){var u=document.getElementById('ar-ded');if(!u)return;var li=[].slice.call(u.children);li.forEach(function(e,i){e.style.transitionDelay=(i*60)+'ms';});
function go(){u.classList.add('in');setTimeout(function(){li.forEach(function(e){e.style.transitionDelay='';});},1200);}
if(!('IntersectionObserver' in window))return go();var io=new IntersectionObserver(function(en){if(en[0].isIntersecting){go();io.disconnect();}},{threshold:.15});io.observe(u);setTimeout(go,4000);})();</script>"""


def services():
    """What we do for artists, at existing public prices only. (tag, title, price, note, lead, items, href, button, featured)"""
    fm = L.PACKAGES[0]["price"]
    return [
        ("Tax return", "Self-employed artist tax return", "Quoted", "up front, by return type",
         "Your Form 1040 with Schedule C and Schedule SE, federal and state, prepared and e-filed.",
         ["Every deduction you can support, with the records to back it", "1099-K and 1099-NEC income matched to your sales",
          "Next year's quarterly payments mapped out"], "/services/#tax-preparation", "See tax preparation", True),
        ("Monthly", "Bookkeeping for artists", f"${L.MONTHLY['price']}", "per month, starting price",
         f"Art business bookkeeping for {L.MONTHLY['scope']}. Larger books are quoted up front.",
         ["Sales, fees and refunds separated, so the 1099-K makes sense", "Supplies, gear and booth fees categorized for Schedule C",
          "Monthly profit and loss"], "/llc-formation/#monthly", "See bookkeeping", False),
        ("Set up", "LLC formation", f"${fm}", "plus the state fee, paid once",
         "If an LLC makes sense for you, we form it in any state, with an EIN and an operating agreement template.",
         ["State filing", "EIN", "Operating agreement template"], "/llc-formation/", "See LLC packages", False),
        ("Year-round", "Quarterly estimates", f"${L.ADDONS['quarterly']['price']}", "for the year",
         "Four federal and state estimate calculations with due dates, so April isn't a surprise.",
         ["Based on your real year-to-date numbers", "Federal and state", "Due-date reminders"], "/services/#tax-planning", "See tax planning", False),
    ]


def offers():
    o = seo._offer
    tax = o("Self-employed artist tax return (Form 1040 with Schedule C)", None,
            f"Quoted up front by return type. Federal returns for every US state; state returns for every state except {STATES_EXCEPT}.",
            url=BASE + "/services/#tax-preparation")
    tax["ineligibleRegion"] = seo.states_excluded(STATE_CODES)
    return [tax,
            o("Bookkeeping for artists", L.MONTHLY["price"], f"Starting price per month for {L.MONTHLY['scope']}.", unit=("MON", "month"),
              url=BASE + "/llc-formation/#monthly"),
            o("LLC formation", L.PACKAGES[0]["price"], "Plus the state filing fee at cost, paid once.", url=BASE + "/llc-formation/"),
            o("Quarterly estimated tax service", L.ADDONS["quarterly"]["price"], "Price for the year: four federal and state estimate calculations with due dates.",
              unit=("ANN", "year"), url=BASE + "/services/#tax-planning")]


def service_node(desc=None):
    return {"@type": "Service", "@id": URL + "#service", "name": "Taxes and bookkeeping for artists and creatives", "url": URL,
            "serviceType": "Tax preparation, bookkeeping and LLC formation for self-employed artists",
            "description": (desc or "Schedule C tax returns, art business bookkeeping, LLC formation and quarterly estimated taxes "
                            "for self-employed artists, illustrators, photographers, musicians, crafters and Etsy art sellers.")
            + f" Federal returns for every US state; state returns for every state except {STATES_EXCEPT}.",
            "provider": {"@id": seo.ORG_ID}, "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "Audience", "audienceType": "Self-employed visual artists, illustrators, photographers, musicians, crafters and Etsy art sellers"},
            "keywords": ", ".join(KEYWORDS), "offers": offers()}


def build():
    title = "Artist Taxes: Deductions, 1099-K & Schedule C | MFA"
    desc = ("Tax help for self-employed artists: deductions for supplies, studio and gear, Etsy 1099-K, quarterly tax and LLC questions. "
            "Schedule C returns.")
    checked = date.fromisoformat(CHECKED).strftime("%B %-d, %Y")
    who = "".join(f'<div class="card"><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for a, b in WHO)
    ded = "".join(f"<li>{ICO}<div><b>{esc(a)}</b><span>{esc(b)}</span></div></li>" for a, b in DEDUCT)
    cards = []
    for tag, name, price, note, lead, items, href, btn, feat in services():
        lis = "".join(f"<li>{ICO}<span>{esc(x)}</span></li>" for x in items)
        cards.append(f'''<div class="pkc card{" feat" if feat else ""}"><span class="pk-tag">{esc(tag)}</span><h3>{esc(name)}</h3>
<p class="pk-price"><b>{esc(price)}</b><span>{esc(note)}</span></p><p class="pk-lead">{esc(lead)}</p><ul class="pk-list">{lis}</ul>
<a class="btn {"btn-gold" if feat else "btn-ink"}" href="{href}">{esc(btn)}</a></div>''')
    live = {p["slug"]: p for p in seo.live_products()}
    prods = [live[s] for s in PRODUCTS if s in live]
    pcards = "".join(f'''<div class="card"><span class="pb-fmt">{esc(x["format"])}</span><h3>{esc(x["name"])}</h3><p>{esc(x["blurb"])}</p>
<div class="pb-foot"><span class="pb-price">${esc(x["price"])}</span>{B.buy_btn(x, "btn btn-gold")}</div></div>''' for x in prods)
    shop = (f'''<section class="wrap llc-sec" id="tools" aria-labelledby="sh-h"><div class="sec-hd"><span class="eyebrow eb-dark">Do it yourself</span><h2 id="sh-h">Trackers and calculators for your art business.</h2>
<p>Spreadsheets from <a href="/shop/" style="border-bottom:1px solid var(--gold)">our shop</a> for keeping your own records. Instant download.</p></div>
<div class="ar-prod">{pcards}</div></section>''' if prods else "")
    steps = "".join(f'<div class="step"><h3>{esc(h)}</h3><p>{p}</p></div>' for h, p in STEPS)
    pairs = []
    for i, (q, a) in enumerate(FAQ):
        a_html = esc(a)
        if i in FAQ_LINKS:
            old, new = FAQ_LINKS[i]
            assert esc(old) in a_html, (i, old)
            a_html = a_html.replace(esc(old), new)
        pairs.append((esc(q), a_html))
    faq = ui_kit.faq_accordion(pairs, prefix="ar")
    src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in SOURCES)
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Artists &amp; creatives</span>
<h1>Taxes for artists <em>and creatives.</em></h1>
<p>Self-employed artist tax returns, art business bookkeeping and straight answers on deductions, the 1099-K, quarterly tax and whether you need an LLC. For visual artists, illustrators, photographers, musicians, crafters and Etsy art sellers.</p>
<div class="hero-btns"><a class="btn btn-gold" href="/book/" data-conv="book">Book a 30-minute call</a><a class="btn btn-line" href="#deductions">See what you can deduct</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="who-h"><div class="sec-hd"><span class="eyebrow eb-dark">Who it's for</span><h2 id="who-h">Artists who get paid for their work.</h2>
<p>Whether art is your full-time living or a side business, the tax rules are the same once you're running it to make a profit.</p></div>
<div class="ar-who">{who}</div></section>
<section class="wrap llc-sec" id="deductions" aria-labelledby="ded-h"><div class="sec-hd"><span class="eyebrow eb-dark">Tax deductions for artists</span><h2 id="ded-h">Tax savings for artists start with what you can deduct.</h2>
<p>Business expenses come off your art income before income tax and self-employment tax are figured. They need to be ordinary (common for artists) and necessary (helpful for your art business), and you need the records to back them up.</p></div>
<ul class="ar-ded" id="ar-ded">{ded}</ul>
<p class="ar-note">Not sure about an expense? Search it in <a href="/tools/is-it-deductible/">Is It Deductible?</a>, or work out a home studio with the <a href="/tools/home-office-deduction-calculator/">home office calculator</a> and your driving with the <a href="/tools/mileage-deduction-calculator/">mileage calculator</a>.</p></section>
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Common questions</span><h2 id="faq-h">Artist tax questions, answered</h2></div>{faq}</section>
<section class="wrap llc-sec" id="services" aria-labelledby="pr-h"><div class="sec-hd"><span class="eyebrow eb-dark">What we do</span><h2 id="pr-h">Tax returns, bookkeeping and setup for artists.</h2>
<p>The same services and prices as the rest of MFA, with an eye for how artists actually get paid.</p></div>
<div class="pk ar-pk">{"".join(cards)}</div>
<p class="ar-note">State returns are not available for {STATES_OUT}. Behind on your books? Ask for a <a href="/bookkeeping-cleanup/">bookkeeping cleanup quote</a>.</p></section>
{shop}
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="how-h">Three steps, mostly online.</h2></div>
<div class="ar-steps">{steps}</div>
<p class="ar-cred">Your return is prepared by Zain Merchant and his team of tax and accounting experts. Zain: CPA candidate · ACCA · Big Four (ex-PwC) · PTIN/EFIN tax preparer.</p></section>
<section class="wrap llc-sec" aria-labelledby="src-h"><div class="sec-hd"><span class="eyebrow eb-dark">Sources</span><h2 id="src-h">Checked against the IRS.</h2></div>
<div class="ar-src"><div class="sources"><ul>{src}</ul><p class="factline">Facts checked against the IRS pages above on {checked}. Sales tax is a state rule: check the revenue department for each state where you sell.</p></div></div></section>
{cta("Want a second pair of eyes on your art business taxes?", "Book a 30-minute call or phone " + TEL + ". We'll look at what you sell and where, and tell you what we'd do and what it costs before any work starts.")}
{ui_kit.fineprint("General information, not tax or legal advice. Deductions depend on your facts and records. "
                  f"State returns are not available for {STATES_OUT}. Reading this page or booking a call doesn't create a client relationship.")}
</main>
{DED_JS}{B.GUMROAD_JS if any(x.get("via") == "gumroad" for x in prods) else ""}'''
    faq_ld = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    ld = seo.graph(URL, "Taxes for artists and creatives", desc, service_node(), faq_ld,
                   crumb=[("Home", BASE + "/"), ("Services", BASE + "/services/"), ("Artists & creatives", URL)],
                   extra={"mainEntity": {"@id": URL + "#service"}, "primaryImageOfPage": {"@type": "ImageObject", "url": OG_IMG}})
    return write("artists", page(title, desc, URL, body, ld, active="s", image=OG_IMG, keywords=KEYWORDS))


if __name__ == "__main__":
    print(build())
