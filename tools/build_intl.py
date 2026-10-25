#!/usr/bin/env python3
"""Builds /international-students/ (Site session): US tax returns for international students, scholars and H-1B workers.

Zain approved the service line and these prices in chat on 2026-10-24:
  Form 8843 only (no US income) $25; student package (Form 1040-NR + Form 8843 + tax treaty check) $99 federal,
  $129 with one state return; Social Security/Medicare (FICA) refund claim, Forms 843 + 8316, $49;
  H-1B and others who are US residents for tax: standard Form 1040 pricing (link to /services/#tax-preparation, no number).
  State returns for every state except CT, MD and OR (same as our other tax services; Zain, 2026-10-25: CA and NY are in).
Targeted by visa and tax situation, never nationality. No immigration advice. Every fact in the FAQ was checked on irs.gov
on CHECKED and is listed in SOURCES. Never "free", never "CPA" (except the approved credential line), no street address,
no software vendor or partner names. Run via tools/build_resources.py (it calls build()).
"""
from datetime import date

import build_blog as B
import seo
import ui_kit
from build_resources import page, write, esc, BASE, cta
import build_offers as O

URL = BASE + "/international-students/"
OG_IMG = URL + "og.png"   # rendered from content/graphics/international-students-og.html (tools/render_graphics.js)
CHECKED = "2026-10-24"
CHECKED_SAVE = "2026-10-25"   # treaty and refund pages for the tax-savings section and the treaty FAQ
# Search phrases this page is written for (Zain, 2026-10-25: "add tags to SEO for international students ... and their tax savings")
KEYWORDS = ["international student tax filing", "F-1 student tax return", "1040-NR preparer", "Form 8843 help",
            "OPT tax refund Social Security Medicare", "H-1B tax return", "nonresident tax treaty",
            "tax savings for international students", "J-1 tax return", "FICA refund F-1 student"]
STATE_CODES = ["CT", "MD", "OR"]   # the only states we don't prepare returns for (Zain, 2026-10-25)
STATES_OUT = "Connecticut, Maryland or Oregon"
STATES_EXCEPT = "Connecticut, Maryland and Oregon"
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'
TEL = '<a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>'

WHO = [
    ("F-1 and J-1 students", "Including OPT and CPT. In your first US years you are usually a nonresident for tax, which means Form 1040-NR and Form 8843."),
    ("J-1 scholars, researchers and teachers", "Teachers and trainees follow a different exempt-years rule than students, so we check your years in the US carefully."),
    ("H-1B and other work visas", "Most H-1B workers pass the substantial presence test and file Form 1040. A first or last year in the US can be dual-status (part nonresident, part resident)."),
    ("No US income this year", "Students and scholars who were in the US but earned nothing usually still need to send Form 8843."),
]

# (tag, title, price, price note, lead, [included], href, button, featured)
PRICES = [
    ("No US income", "Form 8843 only", "$25", "per person",
     "For F, J, M or Q students and scholars with no US income who still need to send Form 8843.",
     ["Form 8843 prepared from your visa and travel dates", "Day count for the substantial presence test",
      "Ready for you to sign and mail, with the IRS address"], "pay:f8843", "Pay $25", False),
    ("Most students", "Student package", "$99", "federal · $129 with one state return",
     "Your nonresident federal return, prepared and e-filed, with Form 8843 attached.",
     ["Form 1040-NR, e-filed", "Form 8843", "Tax treaty check for your wages or scholarship",
      "One state return in the $129 option"], "pay:nr-fed|nr-state", "Pay $99|Pay $129 with state", True),
    ("OPT and campus jobs", "Social Security refund claim", "$49", "Forms 843 + 8316",
     "Social Security and Medicare withheld from your pay while you were exempt, and your employer won't refund it.",
     ["Form 843 claim for refund", "Form 8316 statement", "Supporting documents checklist and filing instructions"],
     "pay:fica", "Pay $49", False),
    ("Filed the wrong form?", "Wrong-form fix", "$129", "amended return",
     "You filed a Form 1040 (often through TurboTax) while you were a nonresident. We fix it with the right amended return.",
     ["Your residency checked year by year", "Amended return prepared, with Form 1040-NR and Form 8843", "Any credits you weren't entitled to identified"],
     "pay:nr-fix", "Pay $129", False),
    ("F-1 to H-1B this year", "First-year H-1B return", "$249", "federal · dual-status year",
     "The year you switched from F-1 or J-1 to H-1B is often dual-status: part nonresident, part resident. We work out the best way to file.",
     ["Residency start date worked out", "Dual-status return or first-year choice compared", "State return quoted up front"],
     "pay:dual", "Pay $249", False),
    ("Residents for tax", "H-1B and US tax residents", "Form 1040", "standard pricing",
     "If you pass the substantial presence test, you file the same Form 1040 as a US citizen, at our standard tax return pricing.",
     ["Form 1040 with your state return", "Dual-status first or last year reviewed", "Quoted up front by return type"],
     "/services/#tax-preparation", "See tax return pricing", False),
]

NEED = [
    ("Passport and visa details", "The visa type and the dates on it."),
    ("Form I-20 or Form DS-2019", "I-20 for F-1 students, DS-2019 for J-1 students and scholars."),
    ("Income forms", "W-2 for wages, 1042-S for scholarships, fellowships or treaty-exempt pay, and any 1099s."),
    ("SSN or ITIN", "If you have one."),
    ("US entry and exit dates", "For this year and earlier years. Your I-94 travel history is the easiest record."),
    ("Prior US returns", "Any earlier Form 1040-NR, Form 1040 or Form 8843 you filed."),
]

STEPS = [
    ("Pay online or book a call", 'Pay for your package above, or pick a time on our <a href="/book/" data-conv="book">booking page</a> or call ' + TEL +
     ". If we find you need different forms, we adjust the price or refund the difference before any work starts."),
    ("Upload your documents", "We send a secure upload link and a checklist. Please don't email passport pages or tax forms."),
    ("We prepare and e-file", "We prepare your return and walk you through it. You review and sign, then we e-file. "
     "Form 8843 on its own can't be e-filed, so you sign and mail it."),
]

FAQ = [
    ("Form 8843 help: do I need to file if I had no US income?",
     "Usually yes, but only Form 8843. If you were in the US as an F, J, M or Q student, or a J or Q teacher or trainee, and you "
     "don't count those days toward the substantial presence test, the IRS requires Form 8843 to explain why. With no tax return "
     "to file, you mail Form 8843 on its own by the Form 1040-NR due date. If you file late, the IRS can count those days, "
     "which can change your tax status. Our Form 8843-only service is $25."),
    ("F-1 student tax return: am I a resident or a nonresident for tax?",
     "It depends on the substantial presence test: at least 31 days in the US this year and 183 days over three years, counting "
     "all of this year's days, one-third of last year's and one-sixth of the year before. Days as an exempt individual don't count. "
     "Students on F, J, M or Q visas are generally exempt for up to five calendar years; J and Q teachers and trainees lose the "
     "exemption if they were exempt in two of the six years before. H-1B workers count every day, so most become residents and "
     "file Form 1040. Tax residency is separate from immigration status."),
    ("Do I need a 1040-NR preparer, or can I use regular tax software?",
     "Only if it prepares Form 1040-NR. Nonresidents who have to file must use Form 1040-NR, not Form 1040, so a program that "
     "only prepares Form 1040 won't produce the right return. Check that it supports Form 1040-NR and Form 8843 before you "
     "start. The IRS accepts Form 1040-NR electronically, and we e-file it for you."),
    ("OPT tax refund: can I get back Social Security and Medicare taken from my pay?",
     "Often, yes. The IRS says F-1, J-1 and M-1 students who are nonresident aliens are exempt from Social Security and Medicare "
     "tax on wages for permitted work, including practical training on or off campus. The exemption ends once you become a "
     "resident for tax, and it doesn't cover F-2, J-2 or M-2 family members or H-1B wages. Ask your employer for a refund first. "
     "If they won't refund all of it, we prepare Form 843 with Form 8316 and the supporting documents for $49."),
    ("Does a nonresident tax treaty lower my US tax?",
     "It can. If the US has an income tax treaty with your country of residence, students, trainees and researchers may be "
     "exempt from US tax on certain income, such as some wages or a scholarship. Each treaty is different, so your country and "
     "the treaty article decide what qualifies. To stop withholding on treaty-exempt wages or scholarship, you give the payer "
     "Form 8233. Our student package includes a treaty check, and we apply any treaty benefit when we prepare your Form 1040-NR."),
    ("Do H-1B workers file Form 1040 or Form 1040-NR?",
     "Most H-1B workers count every day in the US, pass the substantial presence test and file Form 1040 as US residents for tax. "
     "A first or last year in the US can be dual-status, which needs extra care. An H-1B tax return is at our standard Form 1040 "
     "pricing, quoted up front. Social Security and Medicare apply to H-1B wages, so the student refund of those taxes doesn't apply."),
    ("When is the international student tax deadline?",
     "For 2026 income, generally April 15, 2027 if you were paid US wages with income tax withheld, and June 15, 2027 if you "
     "weren't. Form 8843 sent on its own follows the same Form 1040-NR due date. H-1B workers filing Form 1040 file by "
     "April 15, 2027. Need more time? File Form 4868 by the regular due date."),
    ("Which state returns don't you prepare?",
     f"State returns are available for every state except {STATES_EXCEPT}, the same as our other tax services. That includes "
     "New Jersey, New York and California, and we can do your federal return and Form 8843 wherever you live."),
    ("Can you help with my visa or immigration status?",
     "No. We prepare tax returns and don't give immigration advice. For questions about your visa, OPT or a change of status, "
     "talk to your school's international student office or an immigration attorney."),
]

SOURCES = [
    ("IRS: Substantial presence test", "https://www.irs.gov/individuals/international-taxpayers/substantial-presence-test"),
    ("IRS: Publication 519 (2025), U.S. Tax Guide for Aliens", "https://www.irs.gov/publications/p519"),
    ("IRS: Form 8843 (2025), Statement for Exempt Individuals, with instructions", "https://www.irs.gov/pub/irs-pdf/f8843.pdf"),
    ("IRS: Taxation of nonresident aliens (who files Form 1040-NR, due dates)", "https://www.irs.gov/individuals/international-taxpayers/taxation-of-nonresident-aliens"),
    ("IRS: Instructions for Form 1040-NR (2025)", "https://www.irs.gov/instructions/i1040nr"),
    ("IRS: Taxation of alien individuals by immigration status, H-1B", "https://www.irs.gov/individuals/taxation-of-alien-individuals-by-immigration-status-h-1b"),
    ("IRS: Foreign student liability for Social Security and Medicare taxes", "https://www.irs.gov/individuals/international-taxpayers/foreign-student-liability-for-social-security-and-medicare-taxes"),
    ("IRS: Social Security tax/Medicare tax and self-employment (refunds of taxes withheld in error, Form 843)", "https://www.irs.gov/individuals/international-taxpayers/social-security-tax-medicare-tax-and-self-employment"),
    ("IRS: Publication 901, U.S. Tax Treaties", "https://www.irs.gov/publications/p901"),
    ("IRS: Claiming tax treaty benefits", "https://www.irs.gov/individuals/international-taxpayers/claiming-tax-treaty-benefits"),
    ("IRS: Withholding certificates and exemptions for personal services and students (Form 8233)",
     "https://www.irs.gov/individuals/international-taxpayers/withholding-certificates-and-exemptions-for-personal-services-and-students"),
]

# "Tax savings for international students" (Zain, 2026-10-25). Only what irs.gov says; no promised amounts.
SAVE = [
    ("Treaty benefits", "Nonresident tax treaty",
     "If the US has an income tax treaty with your country of residence, students and trainees may be exempt from US tax on some "
     "income, such as wages or a scholarship. We check your treaty in every student package.", "#is-5", "Read the answer"),
    ("OPT and campus jobs", "Social Security and Medicare refund",
     "F-1, J-1 and M-1 students who are nonresidents for tax don't owe Social Security or Medicare on wages for permitted work, "
     "including OPT. If it was withheld anyway, it can be claimed back.", "#is-4", "Read the answer"),
    ("Withheld income tax", "Your federal refund",
     "If more federal income tax was taken from your pay than you owe, the IRS says you must file a return to claim the refund. "
     "For most students that return is Form 1040-NR.", "#prices", "See the student package"),
]

CSS = """<style>
.pk.is-pk{grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}
@media (max-width:1180px){.pk.is-pk{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:640px){.pk.is-pk{grid-template-columns:1fr}}
.is-pk .pkc{padding:28px 24px 24px}.is-pk .pk-price b{font-size:2.5rem}
.is-pk .pk-price span{flex-basis:100%}
.is-who{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:6px}
.is-who .card{padding:22px 24px;background:#fff;border:1px solid var(--hair);border-radius:16px}.is-who h3{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:1.35rem;color:var(--navy);margin:0 0 6px}
.is-who p{margin:0;font-size:.92rem;line-height:1.6;color:var(--muted)}
.is-note{max-width:980px;margin:16px 0 0;font-size:.88rem;color:var(--muted)}
.is-note a,.is-steps .step p a,#faqs .faq-a-in a{color:var(--navy);border-bottom:1px solid var(--gold);transition:color .3s}
.is-note a:hover,.is-steps .step p a:hover,#faqs .faq-a-in a:hover{color:var(--gold)}
.is-need{list-style:none;padding:0;margin:6px 0 0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.is-need li{display:flex;gap:12px;align-items:flex-start;background:#fff;border:1px solid var(--hair);border-radius:14px;padding:16px 18px}
.is-need svg{width:18px;height:18px;flex-shrink:0;margin-top:3px;color:var(--gold)}
.is-need b{display:block;font-size:.98rem;color:var(--navy)}.is-need span{font-size:.9rem;line-height:1.55;color:var(--muted)}
.js .is-need li{opacity:0;transform:translateY(12px);transition:opacity .6s cubic-bezier(.16,1,.3,1),transform .6s cubic-bezier(.16,1,.3,1),border-color .3s}
.js .is-need.in li{opacity:1;transform:none}.is-need li:hover{border-color:var(--gold)}
@media (max-width:760px){.is-need{grid-template-columns:1fr}}
.is-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;counter-reset:s;margin-top:6px}
.is-steps .step{padding:26px;border-top:2px solid var(--gold, #B08D3F);background:#fff;border-radius:0 0 12px 12px}
.is-steps .step:before{counter-increment:s;content:"0" counter(s);font-family:'Cormorant Garamond',Georgia,serif;font-size:38px;color:var(--gold, #B08D3F);display:block;line-height:1;margin-bottom:10px}
.is-steps .step h3{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.6rem;font-weight:500;margin:0 0 8px;color:var(--ink, #10233F)}
.is-steps .step p{margin:0;color:var(--muted);font-size:.95rem;line-height:1.7}
.is-btns{display:flex;flex-wrap:wrap;gap:8px}.is-btns .btn{flex:1 1 auto;justify-content:center}
.is-cred{margin:18px 0 0;font-size:.88rem;color:var(--muted)}
@media (max-width:860px){.is-steps{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){.js .is-need li{opacity:1;transform:none;transition:none}}
.nw{white-space:nowrap}
.is-save .pk-tag{display:block;margin:0 0 6px}
.is-more{display:inline-flex;gap:6px;margin-top:12px;font-size:.86rem;font-weight:600;color:var(--navy);border-bottom:1px solid var(--gold);transition:color .3s,gap .3s}
.is-more:hover{color:var(--gold);gap:10px}.is-more i{font-style:normal;color:var(--gold)}
.is-src{max-width:860px}.is-src .sources{margin-top:0;padding-top:0;border-top:0}
.is-src ul{margin:6px 0 0;padding-left:20px;display:grid;gap:8px}.is-src li{font-size:.92rem;line-height:1.55}.is-src li::marker{color:var(--gold)}
.is-src li a{color:var(--navy);border-bottom:1px solid rgba(176,141,63,.5);text-decoration:none;transition:color .3s,border-color .3s}.is-src li a:hover{color:var(--gold);border-color:var(--gold)}
.is-src .factline{margin:16px 0 0;font-size:.86rem;color:var(--muted)}
</style>"""

# Staggered entrance for the checklist (same pattern as the /book/ topic pills).
NEED_JS = """<script>(function(){var u=document.getElementById('is-need');if(!u)return;var li=[].slice.call(u.children);li.forEach(function(e,i){e.style.transitionDelay=(i*70)+'ms';});
function go(){u.classList.add('in');setTimeout(function(){li.forEach(function(e){e.style.transitionDelay='';});},1200);}
if(!('IntersectionObserver' in window))return go();var io=new IntersectionObserver(function(en){if(en[0].isIntersecting){go();io.disconnect();}},{threshold:.2});io.observe(u);setTimeout(go,4000);})();</script>"""


def offers():
    """schema.org Offers for the approved prices (the H-1B card has no number: standard Form 1040 pricing, quoted up front)."""
    o = seo._offer
    u = URL + "#prices"
    return [o("Form 8843 only (no US income)", 25, "Form 8843 prepared for an exempt individual with no US income, ready to sign and mail.", url=u),
            o("Student package: Form 1040-NR + Form 8843 + tax treaty check", 99, "Federal nonresident return, e-filed. $129 with one state return.", url=u),
            {**o("Student package with one state return", 129, f"Form 1040-NR, Form 8843, tax treaty check and one state return (not {STATES_OUT}).", url=u),
             "eligibleRegion": {"@type": "Country", "name": "United States"}, "ineligibleRegion": seo.states_excluded(STATE_CODES)},
            o("Social Security and Medicare refund claim (Forms 843 + 8316)", 49, "Claim for refund of Social Security and Medicare tax withheld in error.", url=u),
            o("Wrong-form fix: amended return when a 1040 was filed instead of a 1040-NR", 129, "Residency checked and the correct amended return prepared.", url=u),
            o("First-year H-1B (dual-status) tax return, federal", 249, "Dual-status return or first-year choice compared; state return quoted up front.", url=u),
            o("Form 1040 for H-1B workers and other US tax residents", None, "Standard tax return pricing, quoted up front by return type.",
              url=BASE + "/services/#tax-preparation")]


TITLE = "International Student Tax Filing: 1040-NR & 8843 | MFA"
DESC = ("F-1 student tax return on Form 1040-NR $99, Form 8843 help $25, OPT Social Security refund $49, tax treaty check. "
        "H-1B returns too. E-filed.")


def service_node():
    return {"@type": "Service", "@id": URL + "#service", "name": "US tax returns for international students and H-1B workers", "url": URL,
            "serviceType": "Tax preparation for international students and nonresident aliens (Form 1040-NR, Form 8843, Forms 843 and 8316)",
            "description": DESC + f" Federal returns for every US state. State returns for every state except {STATES_EXCEPT}.",
            "provider": {"@id": seo.ORG_ID}, "areaServed": {"@type": "Country", "name": "United States"},
            "keywords": ", ".join(KEYWORDS),
            "audience": {"@type": "Audience", "audienceType": "F-1 and J-1 students, J-1 scholars and H-1B workers in the United States"},
            "offers": offers()}


def build():
    title, desc = TITLE, DESC
    nice = lambda d: date.fromisoformat(d).strftime("%B %-d, %Y")
    checked = f"{nice(CHECKED)}; the treaty and refund pages on {nice(CHECKED_SAVE)}"
    who = "".join(f'<div class="card"><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for a, b in WHO)
    save = "".join(f'<div class="card"><span class="pk-tag">{esc(t)}</span><h3>{esc(h)}</h3><p>{esc(p)}</p>'
                   f'<a class="is-more" href="{u}">{esc(l)} <i aria-hidden="true">→</i></a></div>' for t, h, p, u, l in SAVE)
    cards = []
    for tag, name, price, note, lead, items, href, btn, feat in PRICES:
        lis = "".join(f"<li>{ICO}<span>{esc(x)}</span></li>" for x in items)
        conv = ' data-conv="book"' if href == "/book/" else ""
        if href.startswith("pay:"):
            cls = "btn btn-gold" if feat else "btn btn-ink"
            btns = "".join(O.pay_btn(sid, lab, cls if i == 0 else "btn btn-line") for i, (sid, lab) in enumerate(zip(href[4:].split("|"), btn.split("|"))))
        else:
            btns = f'<a class="btn {"btn-gold" if feat else "btn-ink"}" href="{href}"{conv}>{esc(btn)}</a>'
        cards.append(f'''<div class="pkc card{" feat" if feat else ""}"><span class="pk-tag">{esc(tag)}</span><h3>{esc(name)}</h3>
<p class="pk-price"><b>{esc(price)}</b><span>{esc(note)}</span></p><p class="pk-lead">{esc(lead)}</p><ul class="pk-list">{lis}</ul>
<div class="is-btns">{btns}</div></div>''')
    need = "".join(f"<li>{ICO}<div><b>{esc(a)}</b><span>{esc(b)}</span></div></li>" for a, b in NEED)
    steps = "".join(f'<div class="step"><h3>{esc(h)}</h3><p>{p}</p></div>' for h, p in STEPS)
    faq = ui_kit.faq_accordion([(esc(q), esc(a)) for q, a in FAQ], prefix="is")
    src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in SOURCES)
    body = f'''{CSS}{O.DIALOG_CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Nonresident tax returns</span>
<h1>International student tax filing <em>for F-1, J-1 and <span class="nw">H-1B</span>.</em></h1>
<p>Your F-1 or J-1 student tax return on Form 1040-NR, Form 8843 help, a nonresident tax treaty check and OPT Social Security and Medicare refund claims, plus H-1B tax returns. We prepare and e-file, at a set price you see before we start.</p>
<div class="hero-btns"><a class="btn btn-gold" href="/book/" data-conv="book">Book a 30-minute call</a><a class="btn btn-line" href="#prices">See prices</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="who-h"><div class="sec-hd"><span class="eyebrow eb-dark">Who it's for</span><h2 id="who-h">F-1, J-1 and H-1B tax returns: who we help.</h2>
<p>The right forms depend on your visa, how long you've been in the US and what you earned, not on where you're from.</p></div>
<div class="is-who">{who}</div></section>
<section class="wrap llc-sec" id="prices" aria-labelledby="pr-h"><div class="sec-hd"><span class="eyebrow eb-dark">Prices</span><h2 id="pr-h">Form 1040-NR preparation prices, agreed before we start.</h2>
<p>We confirm which one fits on a short call before any work starts.</p></div>
<div class="pk is-pk">{"".join(cards)}</div>
<p class="is-note">State returns are not available for {STATES_OUT}. Not sure if you're a resident or a nonresident for tax? See <a href="#is-2">the FAQ on residency</a>.</p></section>
<section class="wrap llc-sec" id="savings" aria-labelledby="sv-h"><div class="sec-hd"><span class="eyebrow eb-dark">Tax savings</span><h2 id="sv-h">Tax savings for international students: what's real.</h2>
<p>Three ways students on F-1 and J-1 visas legitimately pay less or get money back. What you get depends on your income, withholding, visa and treaty, so we never promise an amount.</p></div>
<div class="is-who is-save">{save}</div></section>
<section class="wrap llc-sec" aria-labelledby="need-h"><div class="sec-hd"><span class="eyebrow eb-dark">What you'll need</span><h2 id="need-h">What you'll need for Form 1040-NR and Form 8843.</h2>
<p>Missing something? Send what you have and we'll tell you what else to get.</p></div>
<ul class="is-need" id="is-need">{need}</ul></section>
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="how-h">How our 1040-NR preparation works.</h2></div>
<div class="is-steps">{steps}</div>
<p class="is-cred">Your return is prepared by Zain Merchant and his team of tax and accounting experts. Zain: CPA candidate · ACCA · Big Four (ex-PwC) · PTIN/EFIN tax preparer.</p></section>
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">International student tax questions</h2></div>{faq}</section>
<section class="wrap llc-sec" aria-labelledby="src-h"><div class="sec-hd"><span class="eyebrow eb-dark">Sources</span><h2 id="src-h">Checked against the IRS.</h2></div>
<div class="is-src"><div class="sources"><ul>{src}</ul><p class="factline">Facts checked against the IRS pages above on {checked}.</p></div></div></section>
{cta("Not sure which forms you need?", "Book a 30-minute call or phone " + TEL + ". We'll work out your tax residency, the forms you need and the price before any work starts.")}
{ui_kit.fineprint("General information, not tax or immigration advice. Tax residency is separate from immigration status; for visa questions, talk to your school's international student office or an immigration attorney. "
                  f"State returns are not available for {STATES_OUT}. Reading this page or booking a call doesn't create a client relationship.")}
</main>{O.DIALOG}{O.dialog_js()}
{NEED_JS}'''
    svc = service_node()
    faq_ld = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    ld = seo.graph(URL, "US tax returns for international students and H-1B workers", desc, svc, faq_ld,
                   crumb=[("Home", BASE + "/"), ("Services", BASE + "/services/"), ("International students & H-1B", URL)],
                   extra={"mainEntity": {"@id": URL + "#service"}, "primaryImageOfPage": {"@type": "ImageObject", "url": OG_IMG}})
    return write("international-students", page(title, desc, URL, body, ld, active="s", image=OG_IMG, keywords=KEYWORDS))


if __name__ == "__main__":
    print(build())
