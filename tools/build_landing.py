#!/usr/bin/env python3
"""Builds the Google Ads landing pages: site/union-city-nj/ and site/princeton-nj/ (one per LOCATIONS entry)

Edit the CONFIG block below, then run:  python3 tools/build_landing.py
(build_blog.py also adds this page to sitemap.xml and llms.txt.)

Ad final URLs (one per ad group) — the ?s= value swaps the headline and pre-selects the form
(?go=book|quote|reviews|services scrolls to that section, for sitelinks):
  https://mfa-advisory.com/union-city-nj/?s=bookkeeping
  https://mfa-advisory.com/union-city-nj/?s=tax
  https://mfa-advisory.com/union-city-nj/?s=accounting
"""
import json, subprocess, sys
from html import escape as esc
from pathlib import Path

# ---------------------------------------------------------------- CONFIG
PHONE = "(347) 205-4468"   # Leave "" to hide all call buttons.
EMAIL = "info@mfa-advisory.com"
LOCATIONS = {
    "union-city": dict(slug="union-city-nj", city="Union City", region="Hudson County",
                       area=["Union City", "West New York", "North Bergen", "Weehawken", "Hoboken", "Jersey City", "Guttenberg", "Secaucus"]),
    "princeton": dict(slug="princeton-nj", city="Princeton", region="Mercer County",
                      area=["Princeton", "West Windsor", "Plainsboro", "Lawrenceville", "Montgomery", "Hopewell", "Kingston"]),
    # NYC (Zain, 2026-10-20: Google Ads now also targets New York City's five boroughs)
    "new-york": dict(slug="new-york-ny", city="New York", region="the five boroughs", st="NY", state="New York",
                     eyebrow="New York City · All five boroughs",
                     area=["Manhattan", "Brooklyn", "Queens", "The Bronx", "Staten Island"]),
}
# NJ pages default to st="NJ", state="New Jersey", eyebrow="<city> · <region>, NJ".
BOOK_URL = "https://calendar.google.com/calendar/appointments/schedules/AcZssZ2z1XCM1FcZDRE6VnHyWPfqXcgkL1-kxgrTJaKaM-0VCun9u0cVIziW87B0XAQGVXE51SZ0LOo9"
# Form delivery (works on any host, incl. Cloudflare Pages). First submission sends a one-time
# activation email to EMAIL from FormSubmit; click it and every later lead arrives in the inbox.
FORM_ENDPOINT = "https://formsubmit.co/ajax/" + EMAIL
# Google Ads tag + conversion labels live in tools/ads.py (shared site-wide via /assets/ads.js).
# ---------------------------------------------------------------- /CONFIG

# Single-service ad landing pages (one per ad group that needs its own page). Same header-without-menu pattern,
# CSS, Ads tag and form flow as the city pages, but one service and a short form above the fold.
# Zain, 2026-10-25 ("4 yes"): /bookkeeping/princeton-nj/ for the Princeton Bookkeeping ad group (landing-page
# experience "Below average", Quality Score 3/10 on the city page). Ad final URL:
#   https://mfa-advisory.com/bookkeeping/princeton-nj/
SERVICE_PAGES = {
    "bookkeeping-princeton": dict(loc="princeton", slug="bookkeeping/princeton-nj"),
}

if len(sys.argv) < 2:   # build every location page, then every service landing page
    for key in list(LOCATIONS) + list(SERVICE_PAGES):
        subprocess.run([sys.executable, __file__, key], check=True)
    sys.exit(0)
SP = SERVICE_PAGES.get(sys.argv[1])
L = LOCATIONS[SP["loc"] if SP else sys.argv[1]]
SLUG = SP["slug"] if SP else L["slug"]
AREA = L["area"]
ST = L.get("st", "NJ")
STATE = L.get("state", "New Jersey")
EYEBROW = L.get("eyebrow", L["city"] + " · " + L["region"] + ", " + ST)
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / SLUG / "index.html"
URL = f"https://mfa-advisory.com/{SLUG}/"

tel = "+1" + "".join(c for c in PHONE if c.isdigit())[-10:] if PHONE else ""

VARIANTS = {
    "default": {
        "h1": "Bookkeeping, Accounting &amp; Tax Preparation in §CITY§, §ST§",
        "lead": "One team for your books and your taxes. Small businesses, self-employed professionals and households in §REGION§ get clean monthly books, accurate returns and a clear quote before we start: a flat monthly fee or hourly, whichever suits you.",
        "svc": "",
    },
    "bookkeeping": {
        "h1": "Bookkeeping Services in §CITY§, §ST§",
        "lead": "Monthly bookkeeping, catch-up work and QuickBooks cleanup for small businesses. Reconciled every month, ready for tax time and for your lender, at a flat monthly fee or hourly.",
        "svc": "Bookkeeping & Accounting",
    },
    "tax": {
        "h1": "Tax Preparation in §CITY§, §ST§",
        "lead": "Individual, self-employed and small-business returns, federal and §STATE§, prepared accurately and filed on time. Behind on filings? We can help you catch up.",
        "svc": "Tax Preparation & Filing",
    },
    "hindi-urdu": {
        "h1": "Accountant &amp; Tax Preparer Who Speaks Hindi &amp; Urdu",
        "lead": "Bookkeeping, accounting and tax preparation for families and small businesses in §CITY§ and across §REGION§, explained in English, Hindi or Urdu, with a clear quote up front.",
        "svc": "",
    },
    "accounting": {
        "h1": "Small Business Accounting in §CITY§, §ST§",
        "lead": "Monthly close, financial statements and accrual-basis accounting that you, your bank and your tax return can rely on. Big Four training, small-firm attention.",
        "svc": "Bookkeeping & Accounting",
    },
}

SERVICES = [
    ("Bookkeeping", "bookkeeping", [
        "Monthly bookkeeping and bank/credit card reconciliations",
        "Catch-up bookkeeping if you're months (or years) behind",
        "QuickBooks Online setup and cleanup (QuickBooks ProAdvisor)",
        "Payables, receivables and sales tax tracking",
    ]),
    ("Accounting", "accounting", [
        "Month-end close with P&amp;L, balance sheet and cash flow",
        "Accrual-basis books for lenders, investors and buyers",
        "Budgets, cash-flow forecasts and fractional CFO support",
        "Year-end adjustments handed straight to your tax return",
    ]),
    ("Tax preparation", "tax", [
        "Individual returns (1040), including self-employed and 1099 income",
        "Business returns for LLCs, S corps, partnerships and C corps",
        "§STATE§ and multi-state returns",
        "Extensions, amended returns, and prior-year or late filings",
    ]),
]

REVIEWS = [
    ("Merchant Financial Advisory has been outstanding in providing fractional CFO and bookkeeping services… They are responsive, professional, and truly feel like an extension of your team.", "B. Malik", "Google review"),
    ("He set up QuickBooks Online for my new LLC and made sure everything was organized in a way that makes sense for both day-to-day bookkeeping and year-end taxes…", "QuickBooks setup &amp; LLC tax client", "Verified review · Upwork"),
    ("He really does make the whole process insanely easy. His communication is super clear and quick, and he checks in to make sure he's actually building what you need.", "Repeat client", "Verified review · Fiverr"),
]

FAQ = [
    ("Where are you located?", f"We're based in Princeton, NJ and work with clients across §REGION§, including {', '.join(AREA[:-1])} and {AREA[-1]}. Most work happens by video call, phone and secure document upload, so you don't need to take time off to drop off paperwork."),
    ("Who will work on my account?", "A senior team of experienced accountants and tax professionals, led by founder Zain Merchant, a member of ACCA (the Association of Chartered Certified Accountants, UK) with Big Four audit and assurance experience. For engagements that require a licensed CPA, we partner with licensed CPAs. You get one point of contact who knows your file."),
    ("How much do you charge?", "You choose how you pay. Ongoing bookkeeping and advisory are usually a flat monthly fee, so your cost is predictable. One-off projects like cleanups and catch-up work get a project quote, and we also work on hourly contracts if you prefer to pay as you go. Bookkeeping pricing depends mainly on how many transactions you have each month, the number of accounts, the complexity of your business, and whether your books are kept on a cash or accrual basis. Every engagement is quoted up front after an initial consultation."),
    ("I'm behind on my books or haven't filed. Can you help?", "Yes. Catch-up bookkeeping and prior-year returns are a regular part of our work. We rebuild the records, reconcile every account and get your filings current."),
    ("Do you work in QuickBooks, Xero, Sage, Wave and FreshBooks?", "Yes. We keep books in QuickBooks (Online and Desktop), Xero, Sage, Wave and FreshBooks. Our founder is a QuickBooks ProAdvisor, and we handle QuickBooks setup, cleanup and ongoing bookkeeping in both QuickBooks Online and QuickBooks Desktop. We can also work from spreadsheets and bank statements if you don't use accounting software yet."),
    ("What should I bring to the first call?", "For bookkeeping, tell us roughly how many accounts your business has, including bank accounts, credit cards and loans (an estimate is fine). That tells us your approximate monthly transaction volume, which, together with complexity, is what drives bookkeeping pricing. If you know whether your books are on a cash or accrual basis, mention that too; if not, we'll work it out together. For tax returns, have last year's return handy if you can."),
]

check = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
phone_ico = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>'
cal_ico = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>'

def call_btn(cls, label):
    return f'<a href="tel:{tel}" class="{cls}" data-conv="call">{phone_ico}{label}</a>' if tel else ""

svc_html = "".join(
    f'<article class="card" id="svc-{k}"><h3>{t}</h3><ul>' + "".join(f"<li>{check}<span>{i}</span></li>" for i in items) + "</ul></article>"
    for t, k, items in SERVICES)
rev_html = "".join(
    f'<figure class="rev"><div class="stars" aria-label="5 out of 5 stars">★★★★★</div><blockquote>“{q}”</blockquote><figcaption><b>{n}</b><span>{s}</span></figcaption></figure>'
    for q, n, s in REVIEWS)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui_kit  # noqa: E402  shared FAQ accordion + animations
import seo  # noqa: E402  JSON-LD building blocks (tools/seo.py)
import ads  # noqa: E402  Google Ads tag + conversions (tools/ads.py)
faq_html = ui_kit.faq_accordion(FAQ)
opts = "".join(f"<option>{esc(o)}</option>" for o in ["Bookkeeping & Accounting", "Tax Preparation & Filing", "Tax Planning & Strategy", "QuickBooks Setup / Cleanup", "Fractional CFO", "Other"])

if ST == "NY":   # New York City: the five boroughs
    LOCAL_AREAS = [{"@type": "AdministrativeArea", "name": f"{c}, New York City", "containedInPlace": {"@type": "City", "name": "New York"}} for c in AREA]
else:
    LOCAL_AREAS = [{"@type": "City", "name": c, "containedInPlace": {"@type": "State", "name": STATE}} for c in AREA]
LOCAL_AREAS.append({"@type": "State", "name": STATE})
LOCAL_DESC = "Bookkeeping, accounting and tax preparation in §CITY§, §ST§. QuickBooks ProAdvisor, Big Four trained, quoted up front. Book a 30-minute consultation."
ld = seo.graph(URL, "Bookkeeping & Tax Preparation in §CITY§, §ST§", LOCAL_DESC,
               {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
               kind="WebPage", full_org=True, areas=LOCAL_AREAS, crumb=[("Home", "https://mfa-advisory.com/"), ("§CITY§, §ST§", URL)])

gtag = ads.TAG   # tel: clicks, booking links and window.mfaLead() handled by /assets/ads.js

CSS = """
:root{--paper:#FDFDFC;--paper-2:#F5F4EF;--ink:#151515;--navy:#10233F;--navy-2:#1B3557;--gold:#B08D3F;--gold-b:#D8B769;--muted:rgba(21,21,21,.62);--hair:rgba(21,21,21,.1)}
*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth;scroll-padding-top:80px}
body{background:var(--paper);color:var(--ink);font:400 16px/1.65 Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit;text-decoration:none}img{max-width:100%;display:block}svg{width:16px;height:16px;flex:none}
h1,h2,h3{font-family:'Cormorant Garamond',Georgia,serif;font-weight:500;line-height:1.1;letter-spacing:-.01em}
.wrap{max-width:1140px;margin:0 auto;padding:0 20px}
.eyebrow{display:block;font-size:11px;font-weight:700;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;padding:16px 26px;border-radius:999px;border:1px solid transparent;transition:background .3s,color .3s,border-color .3s;cursor:pointer;font-family:inherit}
.btn-gold{background:var(--gold);color:#fff}.btn-gold:hover{background:#9a7a33}
.btn-line{border-color:rgba(255,255,255,.35);color:#fff}.btn-line:hover{border-color:#fff}
.btn-ink{background:var(--navy);color:#fff}.btn-ink:hover{background:var(--navy-2)}
/* top bar */
.top{position:sticky;top:0;z-index:20;background:rgba(253,253,252,.96);backdrop-filter:blur(8px);border-bottom:1px solid var(--hair)}
.top .wrap{display:flex;align-items:center;justify-content:space-between;height:68px;gap:12px}
.brand{display:flex;align-items:center;gap:10px}.brand img{width:38px;height:38px}
.brand b{display:block;font-family:'Cormorant Garamond',serif;font-size:20px;font-weight:600;line-height:1}.brand i{font-style:normal;font-size:9px;letter-spacing:.28em;text-transform:uppercase;color:var(--muted)}
.top-act{display:flex;gap:10px;align-items:center}.top-act .tel{display:flex;gap:8px;align-items:center;font-weight:600;font-size:15px;color:var(--navy)}
.top-act .btn{padding:12px 20px}
/* hero */
.hero{background:var(--navy);color:#fff;padding:64px 0 72px;position:relative;overflow:hidden}
.price-note{margin:-6px 0 18px;font-size:15px;font-weight:600;color:var(--gold-b)}
.hero:after{content:"";position:absolute;right:-180px;top:-180px;width:520px;height:520px;border-radius:50%;border:1px solid rgba(216,183,105,.18)}
.hero-g{display:grid;grid-template-columns:1.25fr 1fr;gap:56px;align-items:center;position:relative;z-index:1}
.hero h1{font-size:clamp(38px,5vw,60px);margin-bottom:20px}
.hero .lead{font-size:18px;color:rgba(255,255,255,.78);max-width:600px;margin-bottom:30px}
.hero .ctas{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:30px}
.trust{display:flex;flex-wrap:wrap;gap:10px 22px;font-size:13px;color:rgba(255,255,255,.75)}
.trust span{display:flex;gap:8px;align-items:center}.trust svg{color:var(--gold-b)}
.hero-card{background:#fff;color:var(--ink);border-radius:14px;padding:28px;box-shadow:0 30px 60px rgba(0,0,0,.25)}
.hero-card h2{font-size:28px;margin-bottom:6px}.hero-card p.s{font-size:14px;color:var(--muted);margin-bottom:18px}
.rating{display:flex;align-items:center;gap:12px;margin-top:18px;padding-top:16px;border-top:1px solid var(--hair);font-size:13px;color:var(--muted)}
.rating b{font-family:'Cormorant Garamond',serif;font-size:30px;color:var(--ink)}.rating .st{color:var(--gold);letter-spacing:2px}
/* form */
form .f{margin-bottom:12px}form label{display:block;font-size:12px;font-weight:600;margin-bottom:5px}
form input,form select,form textarea{width:100%;font:inherit;font-size:15px;padding:12px 14px;border:1px solid rgba(21,21,21,.18);border-radius:8px;background:#fff;color:var(--ink)}
form textarea{min-height:84px;resize:vertical}form input:focus,form select:focus,form textarea:focus{outline:2px solid var(--gold);border-color:var(--gold)}
form .row{display:grid;grid-template-columns:1fr 1fr;gap:10px}form .btn{width:100%;margin-top:4px}
.hp{position:absolute;left:-9999px}.f-stat{font-size:13px;margin:6px 0;color:#a33}
.fine{font-size:11px;color:var(--muted);margin-top:14px;text-align:center}
/* sections */
.sec{padding:84px 0}.sec.alt{background:var(--paper-2)}
.sec-hd{max-width:720px;margin-bottom:40px}.sec-hd h2{font-size:clamp(32px,4vw,46px);margin-bottom:12px}.sec-hd p{color:var(--muted);font-size:17px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.card{background:#fff;border:1px solid var(--hair);border-radius:14px;padding:28px;transition:border-color .3s,box-shadow .3s}
.card.hl{border-color:var(--gold);box-shadow:0 12px 30px rgba(176,141,63,.15)}
.card h3{font-size:28px;margin-bottom:14px;color:var(--navy)}.card ul{list-style:none;display:grid;gap:10px}
.card li{display:flex;gap:10px;font-size:15px}.card li svg{color:var(--gold);margin-top:5px}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;counter-reset:s}
.step{padding:26px;border-top:2px solid var(--gold);background:#fff;border-radius:0 0 12px 12px}
.step:before{counter-increment:s;content:"0" counter(s);font-family:'Cormorant Garamond',serif;font-size:38px;color:var(--gold);display:block;line-height:1;margin-bottom:10px}
.step h3{font-size:24px;margin-bottom:6px}.step p{color:var(--muted);font-size:15px}
.why{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.why div{padding:22px;border:1px solid var(--hair);border-radius:12px;background:#fff}.why b{display:block;font-family:'Cormorant Garamond',serif;font-size:24px;color:var(--navy);margin-bottom:4px}.why span{font-size:14px;color:var(--muted)}
.revs{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.rev{background:#fff;border:1px solid var(--hair);border-radius:14px;padding:26px;display:flex;flex-direction:column}
.rev .stars{color:var(--gold);letter-spacing:3px;margin-bottom:10px}.rev blockquote{font-family:'Cormorant Garamond',serif;font-size:21px;line-height:1.35;flex:1;margin-bottom:16px}
.rev figcaption b{display:block;font-size:14px}.rev figcaption span{font-size:12px;color:var(--muted)}
.area{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.area span{font-size:13px;padding:7px 14px;border-radius:999px;background:#fff;border:1px solid var(--hair)}
.book-frame{background:#fff;border:1px solid var(--hair);border-radius:14px;overflow:hidden}.book-frame iframe{width:100%;height:640px;border:0;display:block}
.book-alt{font-size:14px;color:var(--muted);margin-top:12px}.book-alt a{color:var(--navy);font-weight:600;text-decoration:underline}
.final{background:var(--navy);color:#fff;text-align:center;padding:72px 0}.final h2{font-size:clamp(32px,4vw,46px);margin-bottom:12px}.final p{color:rgba(255,255,255,.75);margin-bottom:26px}
.final .ctas{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
footer{padding:34px 0 100px;font-size:13px;color:var(--muted)}footer nav{display:flex;flex-wrap:wrap;gap:16px;margin:8px 0}footer a{text-decoration:underline}
footer .legal{font-size:12px;max-width:820px}
.mbar{display:none}
@media (max-width:900px){
  .hero-g,.cards,.revs,.steps{grid-template-columns:1fr}.why{grid-template-columns:1fr 1fr}
  .hero{padding:40px 0 48px}.sec{padding:60px 0}.top-act .btn,.top-act .tel span{display:none}
  .mbar{display:grid;grid-template-columns:1fr 1fr;gap:8px;position:fixed;left:0;right:0;bottom:0;z-index:30;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:var(--navy);box-shadow:0 -8px 20px rgba(0,0,0,.15)}
  .mbar .btn{padding:14px 10px}.mbar.one{grid-template-columns:1fr}
}
@media (max-width:480px){form .row{grid-template-columns:1fr}.why{grid-template-columns:1fr}.book-frame iframe{height:720px}}
"""

JS = """
(function(){
  var V=%s, ENDPOINT=%s;
  var s=(new URLSearchParams(location.search).get('s')||'').toLowerCase();
  var v=V[s]; if(v){
    document.getElementById('h1').innerHTML=v.h1; document.getElementById('lead').textContent=v.lead;
    var sel=document.getElementById('f-svc'); if(sel&&v.svc){sel.value=v.svc;}
    var c=document.getElementById('svc-'+s); if(c)c.classList.add('hl');
  }
  var go=(new URLSearchParams(location.search).get('go')||'').toLowerCase();
  if(go&&!location.hash){var t=document.getElementById(go);if(t)setTimeout(function(){t.scrollIntoView();},150);}
  var f=document.getElementById('lf'), btn=document.getElementById('lbtn'), st=document.getElementById('lstat');
  f.addEventListener('submit',function(e){
    e.preventDefault(); if(f._honey.value)return; if(!f.checkValidity()){f.reportValidity();return;}
    var label=btn.innerHTML; btn.disabled=true; btn.textContent='Sending…';
    var d=new FormData(f); d.append('_subject','New lead (§CITY§ page): '+(d.get('service')||'')); d.append('_captcha','false'); d.append('_template','table');
    d.append('source', '§SLUG§' + (s ? ' / ' + s : '') + (location.search.indexOf('gclid')>-1?' / Google Ads':''));
    fetch(ENDPOINT,{method:'POST',headers:{'Accept':'application/json'},body:d})
      .then(function(r){if(!r.ok)throw 0;return r.json();})
      .then(function(j){ if(j.success===false||j.success==='false')throw 0; try{sessionStorage.setItem('mfa_contact_sent','landing_§SLUG§');}catch(e){}location.href='/contact/thanks/'; })
      .catch(function(){ st.textContent='Couldn\\'t send. Please email %s directly.'; btn.disabled=false; btn.innerHTML=label; });
  });
  document.getElementById('yr').textContent=new Date().getFullYear();
})();
"""

variants_js = {k: {"h1": v["h1"], "lead": v["lead"], "svc": v["svc"]} for k, v in VARIANTS.items() if k != "default"}
d = VARIANTS["default"]
other_locs = "".join(f'<a href="/{o["slug"]}/">{"Bookkeeping in " + o["city"] + ", " + o.get("st", "NJ")}</a>' for k, o in LOCATIONS.items() if o["slug"] != L["slug"])
call_top = f'<a href="tel:{tel}" class="tel" data-conv="call">{phone_ico}<span>{esc(PHONE)}</span></a>' if tel else ""

BK_CSS = """
.hero.bk{padding:56px 0 64px}.hero.bk h1{margin-bottom:14px}.hero.bk .lead{margin-bottom:24px}
.hero.bk .ctas{margin-bottom:24px}
.hero-card .row3{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.inc{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.inc .card{padding:26px}.inc .card h3{font-size:24px;margin-bottom:8px}.inc .card p{font-size:15px;color:var(--muted)}
.inc .ic{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;background:rgba(176,141,63,.12);color:var(--gold);margin-bottom:14px}
.inc .ic svg{width:18px;height:18px}
.prices{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.prices .card{display:flex;flex-direction:column}
.pt{font-size:11px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);margin-bottom:10px}
.pp{display:flex;align-items:baseline;gap:8px;margin-bottom:10px}.pp b{font-family:'Cormorant Garamond',serif;font-size:44px;font-weight:500;line-height:1;color:var(--navy)}
.pp span{font-size:14px;color:var(--muted)}.prices .card p.d{font-size:15px;color:var(--muted);flex:1;margin-bottom:20px}
.prices .card .btn{align-self:flex-start}
.fit{display:grid;grid-template-columns:1.1fr 1fr;gap:48px;align-items:start}
.pills{display:flex;flex-wrap:wrap;gap:10px}
.pills span{font-size:14px;padding:9px 16px;border-radius:999px;border:1px solid rgba(176,141,63,.45);background:#fff;transition:background .3s,color .3s,border-color .3s}
.pills span:hover{background:var(--gold);border-color:var(--gold);color:#fff}
.js .pills span{animation:uiUp .7s var(--ui-ease) both}
.pills span:nth-child(2){animation-delay:.05s}.pills span:nth-child(3){animation-delay:.1s}.pills span:nth-child(4){animation-delay:.15s}
.pills span:nth-child(5){animation-delay:.2s}.pills span:nth-child(n+6){animation-delay:.25s}
.fit h3{font-size:24px;margin:26px 0 12px;color:var(--navy)}.fit h3:first-child{margin-top:0}
.creds{background:#fff;border:1px solid var(--hair);border-radius:14px;padding:28px}
.creds .cl{font-weight:600;color:var(--navy);font-size:15px;line-height:1.7}.creds p{font-size:15px;color:var(--muted);margin-top:10px}
.revs-sum{display:flex;align-items:center;gap:14px;margin:-18px 0 30px;font-size:14px;color:var(--muted)}
.revs-sum b{font-family:'Cormorant Garamond',serif;font-size:40px;color:var(--ink);line-height:1}.revs-sum .st{color:var(--gold);letter-spacing:2px}
@media (max-width:900px){.inc{grid-template-columns:1fr 1fr}.prices,.fit{grid-template-columns:1fr}.fit{gap:28px}.hero.bk{padding:28px 0 40px}
  .hero.bk h1{font-size:38px;margin-bottom:10px}.hero.bk .lead{font-size:17px;margin-bottom:18px}.hero.bk .ctas{margin-bottom:0}.hero.bk .ctas .btn-line,.hero.bk .trust{display:none}
  .hero.bk .hero-g{gap:24px}.hero.bk .hero-card h2{font-size:24px}.hero.bk .hero-card p.s{margin-bottom:12px}}
@media (max-width:480px){.inc{grid-template-columns:1fr}.hero-card{padding:22px}}
"""


def bookkeeping_page():
    """/bookkeeping/princeton-nj/: the Princeton Bookkeeping ad group's landing page.
    Prices are the site's published ones only (/services/ OFFERS and build_llc.MONTHLY); nothing new."""
    import build_llc
    price = build_llc.MONTHLY["price"]   # $199: Zain, 2026-10-20 (same figure as /services/)
    city = L["city"] + ", " + ST
    title = f"Bookkeeping in {city} | Flat Monthly or Hourly | MFA"
    desc = (f"Monthly bookkeeping for {city} small businesses from ${price}/month: reconciliations, P&amp;L and balance sheet. "
            "Flat monthly or hourly, senior team.")
    ico = lambda p: f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>'
    INCLUDED = [
        ("Reconciliations", ico('<path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 21v-5h5"/>'),
         "Bank, credit card and loan accounts reconciled to the statements every month."),
        ("Categorizing", ico('<path d="M4 6h16M4 12h10M4 18h7"/>'),
         "Every transaction categorized to a chart of accounts built for your business, with owner draws, loans and transfers kept separate."),
        ("Monthly P&amp;L and balance sheet", ico('<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>'),
         "Your profit and loss and balance sheet each month, with a short note on what changed."),
        ("Sales-tax-ready reports", ico('<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h8M8 15h5"/>'),
         f"Taxable sales tracked and totaled by period, ready for your {STATE} sales tax return."),
    ]
    inc_html = "".join(f'<article class="card"><span class="ic">{i}</span><h3>{t}</h3><p>{d}</p></article>' for t, i, d in INCLUDED)
    PRICES = [   # copy from /services/ (OFFERS, bookkeeping price line) and the cleanup offer; no new prices
        ("Monthly bookkeeping", f"From ${price}", "/ month",
         "One bank, one card, up to 100 transactions a month. Month to month; bigger books quoted up front.",
         '<a class="btn btn-gold" href="#quote">Get my quote</a>'),
        ("Hourly", "Hourly", "pay as you go",
         "Prefer not to commit to a monthly fee? We also work on hourly contracts, with the rate agreed before any work starts.",
         call_btn("btn btn-ink", "Call " + esc(PHONE)) or '<a class="btn btn-ink" href="#quote">Ask about hourly</a>'),
        ("Cleanup &amp; catch-up", "Quoted", "up front",
         "Months or years behind? We rebuild and reconcile the records first. Fixed quote after a review of a sample of your accounts.",
         '<a class="btn btn-ink" href="/bookkeeping-cleanup/">Request a cleanup quote</a>'),
    ]
    price_html = "".join(f'<div class="card"><span class="pt">{n}</span><p class="pp"><b>{p}</b><span>{s}</span></p><p class="d">{t}</p>{b}</div>'
                         for n, p, s, t, b in PRICES)
    WHO = [f"Small businesses in {L['city']} &amp; {L['region']}", "Sole proprietors and freelancers", "Single- and multi-member LLCs",
           "S corporations", "Retail and e-commerce sellers who collect sales tax"]
    SOFT = ["QuickBooks Online", "QuickBooks Desktop", "Xero", "Sage", "Wave", "FreshBooks", "Spreadsheets and bank statements"]   # Zain, 2026-10-25: QuickBooks (Online and Desktop), Xero, Sage, Wave and FreshBooks
    pills = lambda xs: '<div class="pills">' + "".join(f"<span>{x}</span>" for x in xs) + "</div>"
    FAQ_BK = [
        ("How much does monthly bookkeeping cost?",
         f"Monthly bookkeeping starts at ${price} a month for one bank account, one card and up to 100 transactions a month. "
         "Larger books are quoted up front after a short call, and we also work hourly if you prefer to pay as you go. "
         "Cleanup and catch-up projects get a fixed quote after we review a sample of your accounts."),
        ("Do you work in QuickBooks, Xero, Sage, Wave and FreshBooks?",
         "Yes. Our founder is a QuickBooks ProAdvisor, and we keep books in QuickBooks (Online and Desktop), Xero, Sage, Wave and FreshBooks. If you don't use accounting "
         "software yet, we can set up QuickBooks Online for you or start from your spreadsheets and bank statements."),
        ("Will my books be ready for sales tax and tax time?",
         f"Yes. We track taxable sales so the totals for your {STATE} sales tax return are ready each period, and at year-end we hand "
         "reconciled books to your tax preparer, or to us. Sales tax filings and tax returns are quoted separately."),
        ("Do I need to come to an office?",
         f"No. We're based in {city} and work with businesses across {L['region']}, including {', '.join(AREA[1:4])} and {AREA[4]}. "
         "Most work happens by video call, phone and secure document upload."),
    ]
    faq_bk = ui_kit.faq_accordion(FAQ_BK, prefix="bkfaq")
    acct_opts = "".join(f"<option>{o}</option>" for o in ["1 to 2 accounts", "3 to 4 accounts", "5 or more accounts", "Not sure yet"])
    service = {"@type": "Service", "@id": URL + "#service", "name": f"Bookkeeping in {city}", "serviceType": "Bookkeeping",
               "url": URL, "provider": {"@id": seo.ORG_ID}, "areaServed": LOCAL_AREAS, "termsOfService": "https://mfa-advisory.com/terms.html",
               "description": seo.plain("Monthly bookkeeping: reconciliations, transaction categorizing, a monthly P&amp;L and balance sheet "
                                        "and sales-tax-ready reports, at a flat monthly fee or hourly, in QuickBooks, Xero, Sage, Wave and FreshBooks. Cleanup and catch-up quoted up front."),
               "offers": [seo._offer("Monthly bookkeeping", price, "Starting price per month for one bank account, one card and up to 100 transactions a month. "
                                     "Month to month; larger books are quoted up front.", unit=("MON", "month"))]}
    faq_ld = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": seo.plain(a)}} for q, a in FAQ_BK]}
    ld_bk = seo.graph(URL, f"Bookkeeping in {city}", seo.plain(desc), service, faq_ld, kind="WebPage", full_org=True, areas=LOCAL_AREAS,
                      crumb=[("Home", "https://mfa-advisory.com/"), (city, f"https://mfa-advisory.com/{L['slug']}/"), ("Bookkeeping", URL)])
    form_id = "landing_" + SLUG.replace("/", "-")
    js = """
(function(){
  var f=document.getElementById('lf'), btn=document.getElementById('lbtn'), st=document.getElementById('lstat');
  var q=location.search;
  f.addEventListener('submit',function(e){
    e.preventDefault(); if(f._honey.value)return; if(!f.checkValidity()){f.reportValidity();return;}
    var label=btn.innerHTML; btn.disabled=true; btn.textContent='Sending…';
    var d=new FormData(f); d.append('_subject','New bookkeeping lead (§CITY§ bookkeeping page): '+(d.get('accounts')||''));
    d.append('_captcha','false'); d.append('_template','table');
    d.append('source','§PAGE§'+(q.indexOf('gclid')>-1?' / Google Ads':''));
    fetch(§ENDPOINT§,{method:'POST',headers:{'Accept':'application/json'},body:d})
      .then(function(r){if(!r.ok)throw 0;return r.json();})
      .then(function(j){ if(j.success===false||j.success==='false')throw 0; §THANKS§ })
      .catch(function(){ st.textContent='Couldn\\'t send. Please call §PHONE§ or email §EMAIL§.'; btn.disabled=false; btn.innerHTML=label; });
  });
  document.getElementById('yr').textContent=new Date().getFullYear();
})();
""".replace("§PAGE§", SLUG).replace("§ENDPOINT§", json.dumps(FORM_ENDPOINT)).replace("§THANKS§", ads.contact_redirect(form_id)) \
   .replace("§PHONE§", PHONE).replace("§EMAIL§", EMAIL)
    call_top = f'<a href="tel:{tel}" class="tel" data-conv="call">{phone_ico}<span>{esc(PHONE)}</span></a>' if tel else ""
    return f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)}</title>
<meta name="description" content="{desc}"/>
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"/>
<link rel="canonical" href="{URL}"/>
<meta property="og:type" content="website"/><meta property="og:site_name" content="Merchant Financial Advisory"/><meta property="og:locale" content="en_US"/>
<meta property="og:title" content="Bookkeeping in {city}"/>
<meta property="og:description" content="{desc}"/>
<meta property="og:url" content="{URL}"/><meta property="og:image" content="https://mfa-advisory.com/apple-touch-icon.png"/>
<meta name="twitter:card" content="summary"/><meta name="twitter:title" content="Bookkeeping in {city}"/><meta name="twitter:description" content="{desc}"/>
<link rel="icon" href="/favicon.png"/><link rel="apple-touch-icon" href="/apple-touch-icon.png"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<script type="application/ld+json">{seo.dumps(ld_bk, ascii_only=False)}</script>
{gtag}
<style>{CSS}{BK_CSS}{ui_kit.UI_CSS}</style></head><body>

<header class="top"><div class="wrap">
  <a href="/" class="brand" aria-label="Merchant Financial Advisory home"><img src="/apple-touch-icon.png" alt="" width="38" height="38"/><span><b>Merchant</b><i>Financial Advisory</i></span></a>
  <div class="top-act">{call_top}<a href="#quote" class="btn btn-ink">Get a quote</a></div>
</div></header>

<main>
<section class="hero bk"><div class="wrap hero-g">
  <div>
    <span class="eyebrow">§EYEBROW§</span>
    <h1>Bookkeeping in {city}</h1>
    <p class="lead">Flat monthly or hourly pricing, from a senior accounting team. Monthly bookkeeping from ${price}/month.</p>
    <div class="ctas">{call_btn("btn btn-gold", "Call " + esc(PHONE))}<a href="#included" class="btn btn-line">What's included</a></div>
    <div class="trust"><span>{check}QuickBooks ProAdvisor</span><span>{check}Big Four (ex-PwC)</span><span>{check}Flat monthly or hourly</span><span>{check}Senior accounting team</span></div>
  </div>
  <div class="hero-card" id="quote">
    <h2>Get a bookkeeping quote</h2>
    <p class="s">Four quick questions. We reply within one to three business days.</p>
    <form id="lf" method="POST" action="https://formsubmit.co/{EMAIL}" novalidate>
      {ads.next_field()}<input type="hidden" name="service" value="Bookkeeping"/>
      <div class="f"><label for="f-n">Name *</label><input id="f-n" name="name" autocomplete="name" required/></div>
      <div class="f"><label for="f-e">Email *</label><input id="f-e" name="email" type="email" autocomplete="email" required/></div>
      <div class="row3"><div class="f"><label for="f-p">Phone (optional)</label><input id="f-p" name="phone" type="tel" autocomplete="tel"/></div>
      <div class="f"><label for="f-a">Bank &amp; card accounts? *</label><select id="f-a" name="accounts" required><option value="" disabled selected>Select…</option>{acct_opts}</select></div></div>
      <input class="hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
      <div class="f-stat" id="lstat" role="status" aria-live="polite"></div>
      <button class="btn btn-gold" id="lbtn" type="submit">Get my bookkeeping quote</button>
      <p class="fine">Confidential. No obligation. We never share your details.</p>
    </form>
  </div>
</div></section>

<section class="sec" id="included"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">What's included</span><h2>Monthly bookkeeping, done properly every month</h2>
  <p>Your books closed each month, so you know where you stand and your accounts are ready for your lender, your sales tax return and tax time.</p></div>
  <div class="inc">{inc_html}</div>
</div></section>

<section class="sec alt" id="pricing"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">Pricing</span><h2>Flat monthly or hourly. You choose.</h2>
  <p>Every engagement is quoted up front, before any work starts. Pricing depends mainly on how many accounts and transactions you have each month.</p></div>
  <div class="prices">{price_html}</div>
</div></section>

<section class="sec"><div class="wrap fit">
  <div>
    <div class="sec-hd"><span class="eyebrow">Who it's for</span><h2>Built for {L["city"]}-area small businesses</h2></div>
    <h3>Businesses we work with</h3>{pills(WHO)}
    <h3>Software</h3>{pills(SOFT)}
  </div>
  <div class="creds">
    <span class="eyebrow">Senior accounting team</span>
    <p class="cl">Big Four (ex-PwC) · Over 10 years in accounting, audit and tax · PTIN/EFIN tax preparer</p>
    <p>Over 10 years of accounting, audit and tax experience. Your books are handled by Zain Merchant and/or a member of his team of accounting and tax professionals, with one point of contact who knows your file.</p>
    <div class="area" aria-label="Areas served">{"".join(f"<span>{c}</span>" for c in AREA)}</div>
  </div>
</div></section>

<section class="sec alt" id="reviews"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">Client reviews</span><h2>5.0 stars, client after client</h2></div>
  <div class="revs-sum"><b>5.0</b><div><div class="st">★★★★★</div>Average across verified reviews on Google, Upwork &amp; Fiverr</div></div>
  <div class="revs">{rev_html}</div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">How it works</span><h2>From first call to closed books</h2></div>
  <div class="steps">
    <div class="step"><h3>Tell us about your books</h3><p>How many bank and card accounts you have, what software you use and how far behind you are, if at all.</p></div>
    <div class="step"><h3>A clear quote</h3><p>A flat monthly fee or an hourly rate, agreed before any work starts. Behind? We quote the cleanup separately.</p></div>
    <div class="step"><h3>Books closed every month</h3><p>Secure document upload, reconciled accounts and your monthly reports, with one person you can call.</p></div>
  </div>
</div></section>

<section class="sec alt" id="faq"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">FAQs</span><h2>Bookkeeping questions</h2></div>
  <div class="faqs-lp">{faq_bk}</div>
</div></section>

<section class="final"><div class="wrap">
  <h2>Let's get your books closed every month.</h2>
  <p>Flat monthly or hourly. A clear quote before we start. No obligation.</p>
  <div class="ctas">{call_btn("btn btn-gold", "Call " + esc(PHONE))}<a href="#quote" class="btn btn-line">Get a quote</a><a href="{BOOK_URL}" target="_blank" rel="noopener" class="btn btn-line" data-conv="book">{cal_ico}Book a 30-min call</a></div>
</div></section>
</main>

<footer><div class="wrap">
  <span>© <span id="yr">2026</span> Merchant Financial Advisory LLC · Accounting, tax and business solutions · {city} · Serving {L["region"]} · <a href="mailto:{EMAIL}">{EMAIL}</a></span>
  <nav><a href="/">Main site</a><a href="/services/#bookkeeping">Services</a><a href="/{L["slug"]}/">Bookkeeping &amp; tax in {city}</a><a href="/bookkeeping-cleanup/">Bookkeeping cleanup</a><a href="/blog/">Insights</a><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a><a href="/disclaimer.html">Disclaimer</a></nav>
  <p class="legal">Content on this page is general information only and is not tax, accounting, legal, or financial advice. Contacting us does not create a client relationship until an engagement letter is signed. QuickBooks is a trademark of Intuit Inc., Xero is a trademark of Xero Limited, Sage is a trademark of The Sage Group plc, and Wave and FreshBooks are trademarks of their respective owners; MFA is not affiliated with or endorsed by any of them.</p>
</div></footer>

<div class="mbar{"" if tel else " one"}">{call_btn("btn btn-line", "Call")}<a href="#quote" class="btn btn-gold">Get a quote</a></div>
<script>{js}</script>
{ui_kit.UI_JS}
</body></html>
'''


page = f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Bookkeeping &amp; Tax Preparation in §CITY§, §ST§ | MFA</title>
<meta name="description" content="{LOCAL_DESC}"/>
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"/>
<link rel="canonical" href="{URL}"/>
<meta property="og:type" content="website"/><meta property="og:site_name" content="Merchant Financial Advisory"/><meta property="og:locale" content="en_US"/>
<meta property="og:title" content="Bookkeeping &amp; Tax Preparation in §CITY§, §ST§"/>
<meta property="og:description" content="Clean monthly books and accurate tax returns for small businesses and households in §REGION§. 30-minute consultation, clear quote up front."/>
<meta property="og:url" content="{URL}"/><meta property="og:image" content="https://mfa-advisory.com/apple-touch-icon.png"/>
<meta name="twitter:card" content="summary"/><meta name="twitter:title" content="Bookkeeping &amp; Tax Preparation in §CITY§, §ST§"/><meta name="twitter:description" content="{LOCAL_DESC}"/>
<link rel="icon" href="/favicon.png"/><link rel="apple-touch-icon" href="/apple-touch-icon.png"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<script type="application/ld+json">{seo.dumps(ld, ascii_only=False)}</script>
{gtag}
<style>{CSS}{ui_kit.UI_CSS}</style></head><body>

<header class="top"><div class="wrap">
  <a href="/" class="brand" aria-label="Merchant Financial Advisory home"><img src="/apple-touch-icon.png" alt="" width="38" height="38"/><span><b>Merchant</b><i>Financial Advisory</i></span></a>
  <div class="top-act">{call_top}<a href="#book" class="btn btn-ink" data-conv="book">{cal_ico}Book a consultation</a></div>
</div></header>

<main>
<section class="hero"><div class="wrap hero-g">
  <div>
    <span class="eyebrow">§EYEBROW§</span>
    <h1 id="h1">{d["h1"]}</h1>
    <p class="lead" id="lead">{d["lead"]}</p>
    <p class="price-note">Monthly bookkeeping from ${__import__("build_llc").MONTHLY["price"]}/month. Tax returns quoted up front, before we start.</p>
    <div class="ctas"><a href="#book" class="btn btn-gold" data-conv="book">{cal_ico}Book a 30-min call</a>{call_btn("btn btn-line", "Call " + esc(PHONE))}</div>
    <div class="trust"><span>{check}QuickBooks ProAdvisor</span><span>{check}Ex-PwC (Big Four)</span><span>{check}5.0 on Google, Upwork &amp; Fiverr</span><span>{check}Flat-fee or hourly pricing</span></div>
  </div>
  <div class="hero-card" id="quote">
    <h2>Get a quote</h2>
    <p class="s">Tell us what you need. We reply within one to three business days.</p>
    <form id="lf" method="POST" action="https://formsubmit.co/{EMAIL}" novalidate>
      {ads.next_field()}
      <div class="row"><div class="f"><label for="f-n">Name *</label><input id="f-n" name="name" autocomplete="name" required/></div>
      <div class="f"><label for="f-p">Phone</label><input id="f-p" name="phone" type="tel" autocomplete="tel"/></div></div>
      <div class="f"><label for="f-e">Email *</label><input id="f-e" name="email" type="email" autocomplete="email" required/></div>
      <div class="f"><label for="f-svc">I need help with *</label><select id="f-svc" name="service" required><option value="" disabled selected>Select a service…</option>{opts}</select></div>
      <div class="f"><label for="f-m">Anything we should know?</label><textarea id="f-m" name="message" placeholder="e.g. LLC, about 80 transactions a month, two years behind on bookkeeping"></textarea></div>
      <input class="hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
      <div class="f-stat" id="lstat" role="status" aria-live="polite"></div>
      <button class="btn btn-gold" id="lbtn" type="submit">Request my quote</button>
      <p class="fine">Confidential. No obligation. We never share your details.</p>
    </form>
    <div class="rating"><b>5.0</b><div><div class="st">★★★★★</div>Average across verified reviews on Google, Upwork &amp; Fiverr</div></div>
  </div>
</div></section>

<section class="sec" id="services"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">What we do</span><h2>Bookkeeping, accounting and tax preparation under one roof</h2>
  <p>Most small businesses hire a bookkeeper and a tax preparer separately, then pay for the gaps between them. We handle both, so your books are ready when your return is due.</p></div>
  <div class="cards">{svc_html}</div>
</div></section>

<section class="sec alt"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">How it works</span><h2>Three steps to books and taxes you don't have to think about</h2></div>
  <div class="steps">
    <div class="step"><h3>30-minute call</h3><p>We look at where you are today: your books, your last return and what's coming up.</p></div>
    <div class="step"><h3>A clear quote</h3><p>You get the scope and price before any work starts: a flat monthly fee, a project fee, or hourly if you prefer.</p></div>
    <div class="step"><h3>We take it from there</h3><p>Secure document upload, monthly books, and returns filed on time, with one person you can call.</p></div>
  </div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">Why MFA</span><h2>Big Four training. Local, small-firm attention.</h2></div>
  <div class="why">
    <div><b>Senior team</b><span>experienced accountants and tax professionals with 10+ years in accounting, audit and tax, including at Big Four firms</span></div>
    <div><b>ProAdvisor</b><span>QuickBooks Online setup, cleanup and support</span></div>
    <div><b>Flexible pricing</b><span>flat monthly, project or hourly, quoted up front after an initial consultation</span></div>
    <div><b>Direct access</b><span>you talk to your advisor, not a call center or a seasonal temp</span></div>
  </div>
</div></section>

<section class="sec alt" id="reviews"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">Client reviews</span><h2>5.0 stars, client after client</h2></div>
  <div class="revs">{rev_html}</div>
</div></section>

<section class="sec" id="book"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">Book a call</span><h2>Thirty minutes. Your numbers, our full attention.</h2>
  <p>Pick a time that works for you. It's 30 minutes on Google Meet, and you'll leave knowing what to fix first and what it will cost.</p></div>
  <div class="book-frame"><iframe src="{BOOK_URL}?gv=true" title="Book a consultation with Merchant Financial Advisory" loading="lazy"></iframe></div>
  <p class="book-alt">Calendar not loading? <a href="{BOOK_URL}" target="_blank" rel="noopener" data-conv="book">Open the booking page</a> or email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
  <div class="area" aria-label="Areas served">{"".join(f"<span>{c}</span>" for c in AREA)}</div>
</div></section>

<section class="sec alt"><div class="wrap">
  <div class="sec-hd"><span class="eyebrow">FAQs</span><h2>Before you reach out</h2></div>
  <div class="faqs-lp">{faq_html}</div>
</div></section>

<section class="final"><div class="wrap">
  <h2>Let's get your books and taxes in order.</h2>
  <p>A 30-minute call. A clear quote. No obligation.</p>
  <div class="ctas"><a href="#book" class="btn btn-gold" data-conv="book">{cal_ico}Book a call</a>{call_btn("btn btn-line", "Call " + esc(PHONE))}<a href="#quote" class="btn btn-line">Get a quote</a></div>
</div></section>
</main>

<footer><div class="wrap">
  <span>© <span id="yr">2026</span> Merchant Financial Advisory LLC · Accounting, tax and business solutions · Princeton, NJ · Serving §CITY§ &amp; §REGION§ · <a href="mailto:{EMAIL}">{EMAIL}</a></span>
  <nav><a href="/">Main site</a><a href="/services/">Services</a><a href="/llc-formation/">LLC formation</a><a href="/resources/">Resources</a><a href="/shop/">Shop</a>{other_locs}<a href="/blog/">Insights</a><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a><a href="/disclaimer.html">Disclaimer</a></nav>
  <p class="legal">Content on this page is general information only and is not tax, accounting, legal, or financial advice. Contacting us does not create a client relationship until an engagement letter is signed. QuickBooks is a trademark of Intuit Inc., Xero is a trademark of Xero Limited, Sage is a trademark of The Sage Group plc, and Wave and FreshBooks are trademarks of their respective owners; MFA is not affiliated with or endorsed by any of them.</p>
</div></footer>

<div class="mbar{"" if tel else " one"}">{call_btn("btn btn-line", "Call")}<a href="#book" class="btn btn-gold" data-conv="book">Book a call</a></div>
<script>{JS % (json.dumps(variants_js, ensure_ascii=False), json.dumps(FORM_ENDPOINT), EMAIL)}</script>
{ui_kit.UI_JS}
</body></html>
'''

if SP:
    page = bookkeeping_page()

page = page.replace("§EYEBROW§", EYEBROW).replace("§ST§", ST).replace("§STATE§", STATE).replace("§CITY§", L["city"]).replace("§REGION§", L["region"]).replace("§SLUG§", L["slug"])
import tool_products
page = tool_products.inject_page(SLUG, page)   # 'Related products in our shop' (princeton-nj, new-york-ny, union-city-nj)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8")
print(f"Wrote {OUT.relative_to(ROOT)}  (phone {'ON' if tel else 'OFF'}, ads tag {ads.ADS['id']})")
