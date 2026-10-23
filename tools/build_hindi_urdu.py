#!/usr/bin/env python3
"""Builds /hindi-urdu-accountant/ (Site): bilingual landing page for South Asian business owners in Edison, Iselin
and Central NJ (Middlesex County), ahead of tax season. Idea approved by Zain 2026-10-23.

DRAFT: every Hindi and Urdu string below is listed with its English meaning in TRANSLATIONS-FOR-ZAIN.md and needs
Zain's review before this page goes to main.
Claims reuse the approved ?s=hindi-urdu landing variant (tools/build_landing.py) and the site's existing public prices
(tools/build_services.py, tools/seo.py offers). No new prices.
Never "free", never "CPA firm" and never call Zain a CPA ("CPA candidate" only), no street address.
Run via tools/build_resources.py (it calls build()).
"""
import re

import build_blog as B
import seo
import ui_kit
from build_resources import page, write, esc, BASE

SLUG = "hindi-urdu-accountant"
FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600'
         '&family=Noto+Nastaliq+Urdu:wght@400;600&display=swap" rel="stylesheet"/>')
H1 = "Accountant and tax preparer who speaks Hindi and Urdu, serving Edison, Iselin and Central NJ"
LEAD = ("Bookkeeping, tax returns, 1099s and LLC setup for small businesses and families in Middlesex County, "
        "explained in English, Hindi or Urdu, with a clear quote upfront.")

# ---- Hindi (Devanagari) and Urdu (Nastaliq). Keep in sync with TRANSLATIONS-FOR-ZAIN.md.
HI = {
    "label": "हिंदी",
    "head": "एडिसन, आइसलिन और सेंट्रल न्यू जर्सी में हिंदी और उर्दू बोलने वाले अकाउंटेंट और टैक्स प्रिपेयरर",
    "msg": ("आपके बिज़नेस और परिवार के लिए बुककीपिंग, टैक्स रिटर्न, 1099 और LLC सेटअप। "
            "हमसे हिंदी, उर्दू या अंग्रेज़ी में बात करें। काम शुरू होने से पहले साफ़ कीमत बताई जाती है।"),
    "book": "कॉल बुक करें",
}
UR = {
    "label": "اردو",
    "head": "ایڈیسن، آئسلن اور سینٹرل نیو جرسی میں ہندی اور اردو بولنے والے اکاؤنٹنٹ اور ٹیکس پریپیئرر",
    "msg": ("آپ کے کاروبار اور فیملی کے لیے بک کیپنگ، ٹیکس ریٹرن، 1099 اور LLC سیٹ اپ۔ "
            "ہم سے اردو، ہندی یا انگریزی میں بات کریں۔ کام شروع ہونے سے پہلے صاف قیمت بتائی جاتی ہے۔"),
    "book": "کال بک کریں",
}

# (name, price, unit, text). Prices are the site's existing public prices only.
SERVICES = [
    ("Monthly bookkeeping", "From $199", "/ month",
     "One bank account, one card and up to 100 transactions a month, reconciled every month. Month to month; larger books are quoted up front."),
    ("Business and individual tax returns", "Quoted", "up front",
     "Form 1040 with Schedule C, partnerships (1065), S corporations (1120-S) and C corporations (1120), federal and New Jersey. You see the price before we start."),
    ("1099 filing", "$25", "per form, $75 minimum",
     "We collect W-9s from your contractors and e-file their 1099-NEC and 1099-MISC forms on time."),
    ("LLC formation", "From $150", "+ state fee, paid once",
     "State filing, EIN and operating agreement for your new business, in New Jersey or any other state."),
    ("Sales tax filing", "Quoted", "up front",
     "New Jersey sales and use tax returns filed on schedule, for shops, restaurants, services and online sellers."),
]
WHY = [
    ("Big Four experience", "Founder Zain Merchant worked at PwC in New York on audits and internal controls before starting MFA."),
    ("ACCA member", "A member of ACCA, the UK accountancy body, and a US CPA candidate. When an engagement needs a licensed CPA, we work with partner CPAs."),
    ("PTIN and EFIN tax preparer", "Registered with the IRS as a paid tax preparer (PTIN) and as an authorized e-file provider (EFIN)."),
    ("Your language", "Meetings on Google Meet or by phone, in English, Hindi or Urdu. One person who knows your file."),
]
FAQ = [
    ("Can we talk in Hindi or Urdu?",
     "Yes. Zain Merchant speaks English, Hindi and Urdu. Meetings are on Google Meet or by phone, in whichever language you're most "
     "comfortable with. Tax forms and filings are in English, and we explain each one in the language you prefer."),
    ("How much do you charge?",
     "Monthly bookkeeping starts at $199 a month for one bank account, one card and up to 100 transactions a month. 1099 filing is $25 "
     "per form with a $75 minimum, and LLC formation starts at $150 plus the state fee. Tax returns and sales tax filing are quoted "
     "up front, after a short call and before any work starts."),
    ("Do I need to come to an office?",
     "No. We work with clients in Edison, Iselin, Woodbridge, Piscataway and across Central New Jersey by Google Meet, phone and secure "
     "document upload, so you don't have to close the shop or take time off to drop off paperwork."),
    ("Who will work on my file?",
     "Zain Merchant, ACCA, the founder of Merchant Financial Advisory, with Big Four (PwC) audit and accounting experience. He is a US CPA "
     "candidate; for engagements that require a licensed CPA, we partner with licensed CPAs. You get one point of contact who knows your file."),
]
# Short Hindi and Urdu versions of the first two FAQs: (question, answer)
FAQ_HI = [
    ("क्या हम हिंदी या उर्दू में बात कर सकते हैं?",
     "हाँ। Google Meet या फ़ोन पर, हिंदी, उर्दू या अंग्रेज़ी में। टैक्स फ़ॉर्म अंग्रेज़ी में होते हैं, पर हम आपको हर चीज़ आपकी भाषा में समझाते हैं।"),
    ("आपकी फ़ीस कितनी है?",
     "मंथली बुककीपिंग $199 प्रति माह से शुरू होती है। टैक्स रिटर्न की कीमत काम शुरू होने से पहले बता दी जाती है।"),
]
FAQ_UR = [
    ("کیا ہم اردو یا ہندی میں بات کر سکتے ہیں؟",
     "جی ہاں۔ Google Meet یا فون پر، اردو، ہندی یا انگریزی میں۔ ٹیکس فارم انگریزی میں ہوتے ہیں، لیکن ہم آپ کو ہر چیز آپ کی زبان میں سمجھاتے ہیں۔"),
    ("آپ کی فیس کتنی ہے؟",
     "ماہانہ بک کیپنگ $199 فی مہینہ سے شروع ہوتی ہے۔ ٹیکس ریٹرن کی قیمت کام شروع ہونے سے پہلے بتا دی جاتی ہے۔"),
]
AREAS = ["Edison", "Iselin", "Woodbridge", "Piscataway", "Princeton"]

PHONE_ICO = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>')
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'

CSS = """<style>
:root{--f-hi:'Noto Sans Devanagari','Nirmala UI','Kohinoor Devanagari','Mangal',sans-serif;
--f-ur:'Noto Nastaliq Urdu','Jameel Noori Nastaleeq','Urdu Typesetting','Noto Naskh Arabic','Geeza Pro',serif}
[lang="hi"]{font-family:var(--f-hi)}
[lang="ur"]{font-family:var(--f-ur);text-align:right}
.hu-hero h1{font-size:clamp(2.1rem,4.6vw,3.5rem);max-width:900px}
.hu-langs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:34px;max-width:1040px}
.hu-lang{background:rgba(255,255,255,.06);border:1px solid rgba(216,183,105,.35);border-radius:16px;padding:22px 24px}
.hu-lang .tag{display:inline-block;font-size:.85rem;font-weight:600;color:var(--navy);background:var(--gold-b);border-radius:999px;padding:2px 12px;margin-bottom:10px}
.bhero .hu-lang .hh{font-size:1.12rem;font-weight:600;color:#fff;line-height:1.7;margin:0 0 8px;max-width:none}
.bhero .hu-lang .hm{font-size:1rem;font-weight:400;color:rgba(255,255,255,.82);line-height:1.8;margin:0 0 12px;max-width:none}
.bhero .hu-lang[lang="ur"] .hh{font-size:1.18rem;line-height:2.3}
.bhero .hu-lang[lang="ur"] .hm{font-size:1.02rem;line-height:2.4}
.hu-lang a{color:var(--gold-b);font-weight:600;border-bottom:1px solid rgba(216,183,105,.5)}
.hu-svcs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.hu-svc{display:flex;flex-direction:column;background:#fff;border:1px solid var(--hair);border-radius:16px;padding:24px 24px 22px}
.hu-svc h3{font-size:1.25rem;margin:0 0 10px}
.hu-svc .pk-price{margin-bottom:10px}.hu-svc .pk-price b{font-size:2.2rem}.hu-svc .pk-price span{color:var(--muted)}
.hu-svc p{margin:0;font-size:.93rem;line-height:1.6}
.hu-why{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
.hu-why div{background:#fff;border:1px solid var(--hair);border-radius:14px;padding:22px}
.hu-why b{display:flex;gap:8px;align-items:center;font-family:'Cormorant Garamond',serif;font-size:1.35rem;font-weight:500;color:var(--navy);margin-bottom:6px}
.hu-why b svg{width:18px;height:18px;color:var(--gold);flex:none}
.hu-why span{font-size:.92rem;line-height:1.6;color:var(--muted)}
.hu-cta{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-top:8px}
.hu-hero .btn svg,.hu-cta .btn svg{width:15px;height:15px;flex:none}
.hu-areas{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 0;padding:0;list-style:none}
.hu-areas li{border:1px solid var(--gold);border-radius:999px;padding:5px 14px;font-size:.9rem}
.hu-faqx{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:26px}
.hu-faqx section{background:var(--paper-2);border-radius:14px;padding:22px 24px}
.hu-faqx h3{font-size:.85rem;font-weight:600;color:var(--gold);margin:0 0 10px;font-family:inherit;letter-spacing:.04em}
.hu-faqx dt{font-weight:600;margin:12px 0 4px;line-height:1.7}.hu-faqx dd{margin:0;line-height:1.8;font-size:.95rem}
.hu-faqx [lang="ur"] dt{line-height:2.3}.hu-faqx [lang="ur"] dd{line-height:2.4}
.hu-faqx [lang="ur"] h3{text-align:right}
@media(max-width:900px){.hu-why,.hu-svcs{grid-template-columns:1fr 1fr}}
@media(max-width:720px){.hu-langs,.hu-faqx,.hu-svcs{grid-template-columns:1fr}.hu-why{grid-template-columns:1fr}.hu-lang{padding:18px}}
</style>"""


def ltr_money(h):
    """Keep "$199" reading left to right inside Urdu (RTL) text."""
    return re.sub(r"\$\d[\d,]*", lambda m: f'<span dir="ltr">{m.group(0)}</span>', h)


def lang_block(d, code):
    rtl = ' dir="rtl"' if code == "ur" else ""
    return (f'<div class="hu-lang" lang="{code}"{rtl}><span class="tag">{esc(d["label"])}</span>'
            f'<p class="hh">{esc(d["head"])}</p><p class="hm">{ltr_money(esc(d["msg"]))}</p>'
            f'<a href="/book/" data-conv="book">{esc(d["book"])} {"&larr;" if code == "ur" else "&rarr;"}</a></div>')


def faq_x(pairs, code, label):
    rtl = ' dir="rtl"' if code == "ur" else ""
    items = "".join(f"<dt>{esc(q)}</dt><dd>{ltr_money(esc(a))}</dd>" for q, a in pairs)
    return f'<section lang="{code}"{rtl}><h3>{esc(label)}</h3><dl>{items}</dl></section>'


def build():
    url = f"{BASE}/{SLUG}/"
    title = "Hindi & Urdu Speaking Accountant, Edison NJ | MFA"
    desc = ("Hindi speaking accountant in Edison, NJ and Urdu speaking tax preparer for Iselin and Central NJ. "
            "Bookkeeping from $199/mo, tax returns, 1099s, LLCs.")
    tel = f'<a class="btn btn-line" href="tel:{B.TEL}" data-conv="call">{PHONE_ICO}Call {B.PHONE}</a>'
    svcs = "".join(f'<article class="hu-svc"><h3>{esc(n)}</h3><p class="pk-price"><b>{esc(p)}</b><span>{esc(u)}</span></p>'
                   f'<p>{esc(t)}</p></article>' for n, p, u, t in SERVICES)
    why = "".join(f"<div><b>{ICO}{esc(h)}</b><span>{esc(t)}</span></div>" for h, t in WHY)
    areas = "".join(f"<li>{esc(a)}</li>" for a in AREAS + ["Middlesex County"])
    body = f'''<header class="bhero rhero hu-hero"><div class="wrap"><span class="eyebrow">Edison · Iselin · Central New Jersey</span>
<h1>{esc(H1)}</h1>
<p>{esc(LEAD)}</p>
<div class="hero-btns"><a class="btn btn-gold" href="/book/" data-conv="book">Book a call</a>{tel}</div>
<div class="hu-langs">{lang_block(HI, "hi")}{lang_block(UR, "ur")}</div>
</div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="svc-h"><div class="sec-hd"><span class="eyebrow eb-dark">Services</span><h2 id="svc-h">Books, taxes and setup for your business.</h2>
<p>Prices shown are our standard public prices. Everything else is quoted up front, before any work starts.</p></div>
<div class="hu-svcs">{svcs}</div></section>
<section class="wrap llc-sec" aria-labelledby="why-h"><div class="sec-hd"><span class="eyebrow eb-dark">Why MFA</span><h2 id="why-h">Big Four training. A person who speaks your language.</h2></div>
<div class="hu-why">{why}</div>
<ul class="hu-areas" aria-label="Areas served">{areas}</ul></section>
<section class="wrap llc-sec" aria-labelledby="book-h"><div class="sec-hd"><span class="eyebrow eb-dark">Talk to us</span><h2 id="book-h">Tax season is close. Get your books ready now.</h2>
<p>Book a 30-minute call on Google Meet, or call us. English, Hindi or Urdu, whichever you prefer.</p></div>
<div class="hu-cta"><a class="btn btn-ink" href="/book/" data-conv="book">Book a call</a><a class="btn btn-line-ink" href="tel:{B.TEL}" data-conv="call">{PHONE_ICO}Call {B.PHONE}</a></div></section>
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><h2 id="faq-h">FAQs</h2>{ui_kit.faq_accordion(FAQ, prefix="hu")}
<div class="hu-faqx">{faq_x(FAQ_HI, "hi", "हिंदी में")}{faq_x(FAQ_UR, "ur", "اردو میں")}</div></section>
<section class="wrap llc-sec"><p class="disclaimer">Merchant Financial Advisory provides accounting, bookkeeping, tax preparation and advisory services from Princeton, NJ. We do not perform audits or issue audit, review or compilation reports, and we are not a law firm. Contacting us does not create a client relationship until we both agree a written scope.</p></section>
</main>'''
    areas_ld = [{"@type": "City", "name": a, "containedInPlace": {"@type": "State", "name": "New Jersey"}} for a in AREAS]
    areas_ld.append({"@type": "AdministrativeArea", "name": "Middlesex County", "containedInPlace": {"@type": "State", "name": "New Jersey"}})
    ld = seo.graph(url, "Hindi and Urdu speaking accountant and tax preparer, Edison NJ", desc,
                   {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
                       {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
                   kind="WebPage", full_org=True, areas=areas_ld,
                   crumb=[("Home", BASE + "/"), ("Hindi and Urdu speaking accountant", url)],
                   extra={"inLanguage": ["en-US", "hi", "ur"]})
    ld["@graph"][0]["@type"] = ["AccountingService", "ProfessionalService"]   # both LocalBusiness subtypes
    html = page(title, desc, url, body, ld, active="").replace("</head>", FONTS + CSS + "</head>", 1)
    return write(SLUG, html)


if __name__ == "__main__":
    print(build())
