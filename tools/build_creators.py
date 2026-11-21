#!/usr/bin/env python3
"""Builds /content-creator-taxes/ (Site session): taxes and bookkeeping for content creators, streamers, YouTubers,
TikTokers, podcasters and influencers.

Zain 2026-11-18 18:26: "Get the creators page built so we can enter that market as well" (rule 25, every niche gets a page).
No new prices: tax returns quoted up front; bookkeeping from $300/month; quarterly estimates link to the approved page.
Facts checked on irs.gov on CHECKED (SOURCES). Never "free", never "CPA", no street address. No game or platform logos.
Run via tools/build_resources.py (it calls build()).
"""
from datetime import date
import re

import build_blog as B
import lead_box
import seo
import ui_kit
from build_resources import page, write, esc, BASE, cta

URL = BASE + "/content-creator-taxes/"
CHECKED = "2026-11-18"
KEYWORDS = ["content creator taxes", "streamer taxes", "Twitch streamer taxes", "YouTuber taxes", "influencer taxes",
            "TikTok creator taxes", "podcaster taxes", "content creator tax deductions", "hobby or business streaming",
            "do influencers pay taxes on gifted products", "1099-K content creator", "quarterly taxes for creators"]
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'
TEL = '<a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>'

WHO = [
    ("Streamers and gamers", "You go live on Twitch, YouTube or Kick and earn subs, bits, tips, ad share and sponsor deals."),
    ("YouTubers and TikTokers", "Ad revenue, creator funds, brand deals, affiliate links and channel memberships."),
    ("Influencers and UGC creators", "Paid posts, gifted products in exchange for content, affiliate commissions and agency payments."),
    ("Podcasters and educators", "Sponsors, listener support, courses, coaching and digital products."),
]

SERVICES = [
    ("Every tax season", "Creator tax return", "Quoted", "up front, by return",
     "Your Form 1040 with Schedule C and Schedule SE, federal and state, with every platform payout and creator deduction checked.",
     ["Platform payouts matched to your 1099-K, 1099-NEC and 1099-MISC forms", "Sponsor deals and gifted products sorted",
      "Equipment, software and editing costs split by business use", "Self-employment tax worked out"],
     "/book/", "Get a quote", True),
    ("All year", "Bookkeeping for creators", "From $300", "/ month",
     "Monthly books so you know what you actually earned after gear, software and editors.",
     ["Income tracked by platform and sponsor", "Gear, software and contractors logged", "Business share of phone, internet and home office",
      "Year-end package ready for your return"],
     "/services/#bookkeeping", "How bookkeeping works", False),
    ("Four times a year", "Quarterly estimated taxes", "Planned", "with you",
     "Platforms usually don't withhold tax for you, so we work out what to send the IRS and your state each quarter.",
     ["Payment amounts and due dates", "Reminders before each deadline", "Adjusted when a big sponsor deal lands"],
     "/quarterly-estimated-taxes/", "See quarterly estimates", False),
]

STEPS = [
    ("Book a call", 'Pick a time on our <a href="/book/" data-conv="book">booking page</a> or call ' + TEL +
     ". Tell us which platforms pay you and roughly what you spend on gear and software."),
    ("Get your price", "You get a written quote before any work starts. Nothing is charged until you agree to it."),
    ("We prepare and file", "We match every payout, sort your expenses by business use, prepare your return and walk you through it before we e-file."),
]

FAQ = [
    ("Do content creators have to pay taxes?",
     "Yes. Money from ads, subs, bits, tips, memberships, sponsors and affiliate links is taxable income, whether or not you get a 1099. "
     "If you create content to make a profit, you report it as a business on Schedule C and pay self-employment tax on the profit."),
    ("Is my streaming a hobby or a business?",
     "It depends on whether you run it to make a profit. The IRS looks at factors such as keeping complete books, the time you put in, "
     "changing what you do to earn more, and whether you have made a profit in some years. No single factor decides it. "
     "Hobby income is still reported, but hobby costs generally can't be deducted."),
    ("Can I write off a video game I play on stream?",
     "Only if streaming is a business you run for profit, and only the business-use share. A game you buy to play for fun is a personal "
     "cost. If you buy it for content and also play it off stream, keep a record of how you use it."),
    ("Can I deduct my camera, PC, mic and lights?",
     "Usually yes, for the share you use for your content business. Gear that lasts more than a year is generally depreciated, or "
     "expensed in one year under Section 179 or bonus depreciation if you qualify. Personal use reduces the deduction."),
    ("Are gifted products from brands taxable?",
     "If a brand gives you a product in exchange for a post, video or review, its fair market value is generally income, the same as "
     "being paid in cash. The IRS treats goods received in exchange for services as income in the year you receive them."),
    ("How much is self-employment tax for creators?",
     "15.3% of your net earnings from self-employment: 12.4% for Social Security and 2.9% for Medicare. It usually applies once your net "
     "earnings are $400 or more. Half of it is deductible when you work out your income tax."),
    ("When will I get a 1099-K from a platform or payment app?",
     "For 2026, payment platforms send a Form 1099-K when your payments are over $20,000 and you have more than 200 transactions. "
     "Sponsors may send a 1099-NEC instead. Income below those amounts is still taxable, so we match every payout to your records."),
    ("Do I need to pay quarterly taxes as a creator?",
     'Most creators do, because platforms and sponsors usually don\'t withhold tax. Federal estimates for 2026 income are due '
     'April 15, June 15 and September 15, 2026 and January 15, 2027. See <a href="/quarterly-estimated-taxes/">quarterly estimated taxes</a>.'),
    ("Should a creator form an LLC or an S corp?",
     'An LLC can separate your business from your personal finances, but on its own it doesn\'t lower your tax. Once your profit is '
     'steady, an S corp election may cut self-employment tax. See <a href="/s-corp-election/">S corp election</a> and '
     '<a href="/llc-formation/">LLC formation</a>.'),
    ("Do you work with creators outside New Jersey?",
     "Yes. We prepare federal returns for every state and state returns for every state except Connecticut, Maryland and Oregon."),
]

SOURCES = [
    ("IRS: Topic 554, Self-employment tax", "https://www.irs.gov/taxtopics/tc554"),
    ("IRS: Here's how to tell the difference between a hobby and a business",
     "https://www.irs.gov/newsroom/heres-how-to-tell-the-difference-between-a-hobby-and-a-business-for-tax-purposes"),
    ("IRS: Tips for taxpayers who make money from a hobby", "https://www.irs.gov/newsroom/tips-for-taxpayers-who-make-money-from-a-hobby"),
    ("IRS: Topic 420, Bartering income", "https://www.irs.gov/taxtopics/tc420"),
    ("IRS: Form 1099-K threshold reverts to $20,000 (FAQs)",
     "https://www.irs.gov/newsroom/irs-issues-faqs-on-form-1099-k-threshold-under-the-one-big-beautiful-bill-dollar-limit-reverts-to-20000"),
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

TITLE = "Content Creator Taxes for Streamers & YouTubers | MFA"
DESC = ("Tax returns, bookkeeping and quarterly taxes for streamers, YouTubers, TikTokers and influencers. Hobby vs business, gear, "
        "sponsors.")


def service_node():
    o = seo._offer
    return {"@type": "Service", "@id": URL + "#service", "name": "Taxes and bookkeeping for content creators and streamers", "url": URL,
            "serviceType": "Tax preparation and bookkeeping for self-employed content creators (Schedule C, Schedule SE, 1099-K, estimated taxes)",
            "description": DESC, "provider": {"@id": seo.ORG_ID}, "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "Audience", "audienceType": "Streamers, YouTubers, TikTok creators, influencers and podcasters"},
            "offers": [o("Content creator tax return (Schedule C + SE)", None, "Quoted up front by return type.", url=URL + "#services"),
                       o("Bookkeeping for content creators", 300, "Monthly bookkeeping from $300/month.", url=BASE + "/services/#bookkeeping")]}


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
    faq = ui_kit.faq_accordion([(esc(q), a) for q, a in FAQ], prefix="cc")
    src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in SOURCES)
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Content creators &amp; streamers</span>
<h1>Content creator taxes <em>for streamers, YouTubers and influencers.</em></h1>
<p>Schedule C returns, every platform payout matched, gear and software deductions split by business use, gifted products handled and quarterly taxes planned, for creators in New Jersey, New York and across the US. You see the price before we start.</p>
<div class="hero-btns"><a class="btn btn-gold" href="/book/" data-conv="book">Book a 30-minute call</a><a class="btn btn-line" href="#faqs">Creator tax answers</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="who-h"><div class="sec-hd"><span class="eyebrow eb-dark">Who it's for</span><h2 id="who-h">Creators we help.</h2>
<p>If you create content to earn money, the IRS usually treats it as a business. We start there.</p></div>
<div class="br-who">{who}</div></section>
<section class="wrap llc-sec" id="services" aria-labelledby="sv-h"><div class="sec-hd"><span class="eyebrow eb-dark">Services</span><h2 id="sv-h">Tax and bookkeeping for creators.</h2>
<p>Pick one or combine them. Tax returns are quoted up front once we know which platforms pay you.</p></div>
<div class="pk br-pk">{"".join(cards)}</div>
<p class="br-note">Behind on records? Our <a href="/bookkeeping-cleanup/">bookkeeping cleanup</a> sorts past months by platform and expense type.</p></section>
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="how-h">How creator tax prep works with us.</h2></div>
<div class="br-steps">{steps}</div>
<p class="br-cred">Your return is prepared by Zain Merchant and his team of tax and accounting experts. Zain: ACCA · Big Four (ex-PwC) · PTIN/EFIN tax preparer.</p></section>
<section class="wrap llc-sec" id="compare" aria-labelledby="cmp-h"><div class="sec-hd"><span class="eyebrow eb-dark">Compare</span><h2 id="cmp-h">Hobby or business: how are creator taxes different?</h2>
<p>The same channel, two very different tax returns.</p></div>
<div class="cmp-tw"><table class="tbl br-cmp"><thead><tr><th></th><th>Business (run for profit)</th><th>Hobby (for fun)</th></tr></thead><tbody>
<tr><th scope="row">Where income goes</th><td>Schedule C</td><td>Schedule 1 as other income</td></tr>
<tr><th scope="row">Gear, software, editors</th><td>Deductible for the business-use share</td><td>Generally not deductible</td></tr>
<tr><th scope="row">Self-employment tax</th><td>15.3% on net earnings of $400 or more</td><td>Doesn't apply</td></tr>
<tr><th scope="row">Losses</th><td>Can offset other income, within the rules</td><td>Can't offset other income</td></tr>
<tr><th scope="row">Records</th><td>Complete books expected</td><td>Still report every dollar</td></tr>
<tr><th scope="row">What the IRS looks at</th><td colspan="2">Profit motive: businesslike books, time and effort, changes to earn more, profit in some years. No single factor decides.</td></tr>
</tbody></table></div>
<p class="br-note">Run your numbers: <a href="/tools/quarterly-estimated-tax-calculator/">quarterly estimated tax calculator</a> · <a href="/tools/is-it-deductible/">is it deductible?</a> · <a href="/answers/">short tax answers</a></p></section>
{lead_box.lead_box("Content creator taxes", "page-creators", "Get your creator tax price.",
    "Tell us which platforms pay you and what you create, and we'll email a fixed quote within one business day.",
    [("tax-return", "Tax return (Schedule C)"), ("estimates", "Quarterly estimated taxes"), ("bookkeeping", "Monthly bookkeeping"), ("question", "A quick question first")],
    ["Streamers, YouTubers, TikTokers, influencers and podcasters", "Payouts, sponsors, gear and self-employment tax handled together", "Price confirmed before any work starts"],
    example="For example: Twitch + YouTube, about $3,000 a month in sponsors")}
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">Content creator tax questions</h2></div>{faq}</section>
<section class="wrap llc-sec" aria-labelledby="src-h"><div class="sec-hd"><span class="eyebrow eb-dark">Sources</span><h2 id="src-h">Checked against the IRS.</h2></div>
<div class="br-src"><div class="sources"><ul>{src}</ul><p class="factline">Facts checked against the pages above on {nice}.</p></div></div></section>
{cta("Creating for a living? Let's get your taxes right.", "Book a 30-minute call or phone " + TEL + ". Tell us which platforms pay you and what you spend on gear, and we'll quote your return before any work starts.")}
{ui_kit.fineprint("General information, not tax advice for your situation. State returns are not available for Connecticut, Maryland or Oregon. "
                  "Reading this page or booking a call doesn't create a client relationship.")}
</main>'''
    faq_ld = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
        for q, a in FAQ]}
    ld = seo.graph(URL, "Taxes and bookkeeping for content creators and streamers", DESC, service_node(), faq_ld,
                   crumb=[("Home", BASE + "/"), ("Services", BASE + "/services/"), ("Content creator taxes", URL)],
                   extra={"mainEntity": {"@id": URL + "#service"}})
    return write("content-creator-taxes", page(TITLE, DESC, URL, body, ld, active="s", keywords=KEYWORDS))


if __name__ == "__main__":
    print(build())
