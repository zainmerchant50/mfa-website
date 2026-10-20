#!/usr/bin/env python3
"""Builds the LLC formation service pages: /llc-formation/ and /llc-formation/<state>/.

Site session owns this file (see claude/site-session-brief.md and claude/site/llc-competitor-research.md).
State facts come only from data/llc-states.json (verified by the Blog session). Prices and package scope
were set by Zain on 2026-10-20 (claude/digital-products-plan.md, "LLC formation service").
Customer-facing dates show the date only. Run via tools/build_resources.py (it calls build_all()).
"""
import json
from datetime import datetime
from pathlib import Path

import build_blog as B
import ui_kit
from build_resources import page, write, esc, BASE, svg

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "llc-states.json").read_text(encoding="utf-8"))
STATES = DATA["states"]
ORDER = [s for s in DATA["meta"]["order"] if s in STATES]
COMING = DATA["meta"].get("coming_next", [])
FORM_ENDPOINT = "https://formsubmit.co/ajax/" + B.EMAIL
LEGAL = ("MFA is not a law firm and does not provide legal advice. We prepare and file formation documents "
         "based on the information you provide.")


def d(ts):
    return datetime.fromisoformat(ts).strftime("%B %-d, %Y")


CHECKED = d(DATA["meta"]["checked"])

PACKAGES = [
    {"id": "formation", "name": "Formation", "price": 99, "tag": "File it right",
     "lead": "Your LLC filed, with the EIN and paperwork you need on day one.",
     "items": ["Review of your details and a name availability check",
               "State formation filing prepared and submitted",
               "EIN from the IRS (we apply for you)",
               "Operating agreement template, filled in with your owners and percentages",
               "First-year compliance calendar",
               "Document pack: filed certificate, EIN letter, operating agreement"]},
    {"id": "setup", "name": "Formation + Business Setup", "price": 249, "tag": "Most complete start", "feat": True,
     "lead": "Everything in Formation, plus the tax and books setup most new owners miss.",
     "items": ["Everything in Formation",
               "Tax classification review: default LLC vs S corp, in writing",
               "State tax registration (NJ-REG in New Jersey), including employer setup if you'll hire",
               "Bank-ready document checklist",
               "QuickBooks Online setup: chart of accounts, bank feeds, invoice template",
               "45-minute onboarding call"]},
    {"id": "launch", "name": "Complete Launch", "price": 499, "tag": "Launch-ready",
     "lead": "Everything in Business Setup, plus your elections, sales tax and first month of books.",
     "items": ["Everything in Formation + Business Setup",
               "S corp election (Form 2553) filed if it fits, with salary guidance",
               "Sales tax registration and filing calendar, if you sell taxable goods or services",
               "First month of bookkeeping: one bank, one card, up to 100 transactions, first P&amp;L",
               "Our DIY guides and checklists included",
               "30-day check-in call"]},
]

ROWS = [  # (feature, formation, setup, launch)
    ("State filing + name check", 1, 1, 1), ("EIN application", 1, 1, 1), ("Operating agreement template", 1, 1, 1),
    ("First-year compliance calendar", 1, 1, 1), ("Tax classification review (LLC vs S corp)", 0, 1, 1),
    ("State tax registration", 0, 1, 1), ("QuickBooks Online setup", 0, 1, 1), ("Onboarding call", 0, 1, 1),
    ("S corp election (Form 2553), if it fits", 0, 0, 1), ("Sales tax registration", 0, 0, 1),
    ("First month of bookkeeping", 0, 0, 1), ("DIY guides and checklists", 0, 0, 1), ("Renews every year?", "No", "No", "No"),
]

ICO_OK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'


def v(s, k):
    f = s.get(k)
    return f.get("value") if isinstance(f, dict) else None


def picker_data():
    out = {}
    for code in ORDER:
        s = STATES[code]
        pub = v(s, "publication")
        out[code] = {
            "name": s["name"], "fee": v(s, "filing_fee"),
            "annual": v(s, "annual_report_fee"), "annual_due": v(s, "annual_report_due"),
            "annual_note": (s.get("annual_report_fee") or {}).get("note", ""),
            "biennial": v(s, "biennial_statement_fee"),
            "reg": v(s, "state_tax_registration"),
            "pub_fee": pub.get("certificate_of_publication_fee") if pub else None,
            "url": f"/llc-formation/{code.lower()}/",
        }
    return out


def ld_service(url):
    return {"@context": "https://schema.org", "@graph": [
        {"@type": "Service", "name": "LLC formation", "serviceType": "LLC formation and business setup", "url": url,
         "provider": {"@type": "AccountingService", "name": "Merchant Financial Advisory LLC", "url": BASE},
         "areaServed": [STATES[c]["name"] for c in ORDER],
         "offers": [{"@type": "Offer", "name": p["name"], "price": p["price"], "priceCurrency": "USD",
                     "description": "Plus the state filing fee, paid at cost. One-time; does not renew."} for p in PACKAGES]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "LLC formation", "item": url}]}]}


def faq_ld(pairs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": ui_kit._plain(q), "acceptedAnswer": {"@type": "Answer", "text": ui_kit._plain(a)}} for q, a in pairs]}


def packages_html():
    cards = []
    for p in PACKAGES:
        lis = "".join(f"<li>{ICO_OK}<span>{i}</span></li>" for i in p["items"])
        cards.append(f'''<div class="pkc card{" feat" if p.get("feat") else ""}">
<span class="pk-tag">{esc(p["tag"])}</span><h3>{esc(p["name"])}</h3>
<p class="pk-price"><b>${p["price"]}</b><span>+ state fee · paid once</span></p>
<p class="pk-lead">{esc(p["lead"])}</p><ul class="pk-list">{lis}</ul>
<a class="btn {"btn-gold" if p.get("feat") else "btn-ink"}" href="#start" data-pk="{p["id"]}">Choose {esc(p["name"])}</a></div>''')
    return '<div class="pk">' + "".join(cards) + "</div>"


def table_html():
    head = "".join(f"<th>{esc(p['name'])}<br><small>${p['price']}</small></th>" for p in PACKAGES)
    body = ""
    for f, *cells in ROWS:
        tds = "".join(f'<td>{c if isinstance(c, str) else (ICO_OK if c else "<span class=dash>—</span>")}</td>' for c in cells)
        body += f"<tr><td>{esc(f)}</td>{tds}</tr>"
    return f'<div class="tbl-wrap"><table class="tbl pk-tbl"><thead><tr><th>What\'s included</th>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def state_picker():
    opts = "".join(f'<option value="{c}">{esc(STATES[c]["name"])}</option>' for c in ORDER)
    pk = "".join(f'<label class="opt"><input type="radio" name="pk" value="{p["id"]}" data-price="{p["price"]}"{" checked" if p.get("feat") else ""}/>'
                 f'<span>{esc(p["name"])} <small>${p["price"]}</small></span></label>' for p in PACKAGES)
    soon = ", ".join(COMING)
    return f'''<section class="wrap llc-sec" id="cost" aria-labelledby="cost-h">
<div class="sec-hd"><span class="eyebrow eb-dark">Your real first-year cost</span><h2 id="cost-h">Pick your state. See the whole number.</h2>
<p>Our fee plus the state's fee, before you commit. State fees are passed through at cost.</p></div>
<div class="tool tool-llc"><div class="tcard"><h2>Your LLC</h2><p class="sub">Choose a state and a package.</p>
<div class="fld"><label for="st">State</label><select id="st">{opts}</select>
<span class="hint">More states coming: {esc(soon)}. Forming somewhere else? <a href="#start">Ask us</a>.</span></div>
<div class="fld"><span class="lbl">Package</span><div class="opts">{pk}</div></div></div>
<div class="tcard tres" aria-live="polite"><h2 id="c-h">New Jersey LLC</h2><p class="sub" id="c-sub">First-year cost with MFA</p>
<div class="kpis"><div class="kpi gold wide"><b id="c-tot">—</b><span>Due at formation</span></div>
<div class="kpi"><b id="c-pk">—</b><span>MFA package</span></div><div class="kpi"><b id="c-fee">—</b><span>State filing fee</span></div></div>
<ul class="steps-out" id="c-notes"></ul>
<div class="acts"><a class="btn btn-gold" href="#start">Start my LLC</a><a class="btn btn-line" id="c-link" href="#">State details</a></div>
<p class="muted">State fees as published by the state and checked {CHECKED}. Card convenience fees and county costs may apply.</p></div></div></section>'''


def picker_js():
    data = json.dumps(picker_data())
    return """<script>
(function(){var S=%s,st=document.getElementById('st'),$=function(i){return document.getElementById(i);};
var m=function(n){return '$'+Number(n).toLocaleString('en-US');};
function run(){var s=S[st.value],r=document.querySelector('input[name=pk]:checked'),p=r?+r.getAttribute('data-price'):0;
$('c-h').textContent=s.name+' LLC';$('c-pk').textContent=m(p);$('c-fee').textContent=s.fee!=null?m(s.fee):'Varies';
var tot=p+(s.fee||0)+(s.pub_fee||0);$('c-tot').textContent=m(tot)+(s.pub_fee?' +':'');
var n=[];if(s.pub_fee)n.push('Includes the '+m(s.pub_fee)+' Certificate of Publication fee. Newspaper publication costs vary by county and are quoted at cost.');
if(s.annual)n.push('Then '+m(s.annual)+' a year for the annual report, due '+s.annual_due.charAt(0).toLowerCase()+s.annual_due.slice(1)+'.');
if(s.biennial)n.push('Then '+m(s.biennial)+' every two years for the biennial statement.');
if(s.reg)n.push('Tax registration: '+s.reg+'.');n.push('Nothing from MFA renews. Bookkeeping after month one is optional.');
$('c-notes').innerHTML=n.map(function(t){return '<li>'+t.replace(/</g,'&lt;')+'</li>';}).join('');$('c-link').href=s.url;
$('c-link').textContent=s.name+' details';var f=document.getElementById('f-state');if(f)f.value=st.value;}
st.addEventListener('change',run);document.addEventListener('change',function(e){if(e.target.name==='pk'){var f=document.getElementById('f-pk');if(f)f.value=e.target.value;run();}});
[].slice.call(document.querySelectorAll('[data-pk]')).forEach(function(a){a.addEventListener('click',function(){var f=document.getElementById('f-pk');if(f)f.value=a.getAttribute('data-pk');});});
var q=new URLSearchParams(location.search).get('state');if(q&&S[q.toUpperCase()])st.value=q.toUpperCase();run();})();
</script>""" % data


def intake_form():
    st_opts = "".join(f'<option value="{c}">{esc(STATES[c]["name"])}</option>' for c in ORDER) + '<option value="Other">Another state</option>'
    pk_opts = "".join(f'<option value="{p["id"]}"{" selected" if p.get("feat") else ""}>{esc(p["name"])} (${p["price"]})</option>' for p in PACKAGES)
    return f'''<section class="wrap llc-sec" id="start" aria-labelledby="start-h">
<div class="sec-hd"><span class="eyebrow eb-dark">Start my LLC</span><h2 id="start-h">Tell us about your business.</h2>
<p>No payment is taken on this page. We review your details, confirm the name is available, and email you an invoice for your package plus the state fee. We file once it's paid.</p></div>
<form class="tcard lform" id="lform" novalidate>
<div class="lgrid">
<div class="fld"><label for="f-name">Your name</label><input type="text" id="f-name" name="name" autocomplete="name" required/></div>
<div class="fld"><label for="f-email">Email</label><input type="text" inputmode="email" id="f-email" name="email" autocomplete="email" required/></div>
<div class="fld"><label for="f-phone">Phone (optional)</label><input type="text" inputmode="tel" id="f-phone" name="phone" autocomplete="tel"/></div>
<div class="fld"><label for="f-state">State to form in</label><select id="f-state" name="state">{st_opts}</select></div>
<div class="fld"><label for="f-pk">Package</label><select id="f-pk" name="package">{pk_opts}</select></div>
<div class="fld"><label for="f-llc">LLC name you want</label><input type="text" id="f-llc" name="llc_name" required placeholder="e.g. Brightline Studio LLC"/></div>
<div class="fld"><label for="f-alt">Backup name (optional)</label><input type="text" id="f-alt" name="backup_name"/></div>
<div class="fld"><label for="f-own">Number of owners</label><select id="f-own" name="owners"><option>1 (single-member)</option><option>2</option><option>3–5</option><option>6 or more</option></select></div>
<div class="fld"><label for="f-mgmt">Managed by</label><select id="f-mgmt" name="managed_by"><option>The owners (member-managed)</option><option>Appointed managers (manager-managed)</option><option>Not sure, help me decide</option></select></div>
<div class="fld"><label for="f-act">What will the business do?</label><input type="text" id="f-act" name="activity" required placeholder="e.g. graphic design services"/></div>
</div>
<div class="fld"><span class="lbl">Check any that apply</span><div class="opts opts-2">
<label class="opt"><input type="checkbox" name="will_hire" value="yes"/><span>I'll hire employees in the first year</span></label>
<label class="opt"><input type="checkbox" name="sells_taxable" value="yes"/><span>I'll sell products or taxable services</span></label>
<label class="opt"><input type="checkbox" name="has_agent" value="yes"/><span>I already have a registered agent or in-state street address</span></label>
<label class="opt"><input type="checkbox" name="s_corp_interest" value="yes"/><span>I want to know if an S corp makes sense</span></label></div></div>
<div class="fld"><label for="f-notes">Anything else? (optional)</label><textarea id="f-notes" name="notes" rows="3" placeholder="Timing, partners, questions"></textarea>
<span class="hint">Please don't include Social Security or bank account numbers. We collect what the IRS needs securely after we've confirmed your order.</span></div>
<input class="ask-hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
<button class="btn btn-ink" type="submit">Send my details</button><p class="ask-st" role="status" aria-live="polite"></p>
</form>
<div class="tcard ldone" id="ldone" hidden><h2>Thanks, we have your details.</h2><p>We'll review them, check the name and email you an invoice for your package plus the state fee. Questions in the meantime: <a href="mailto:{B.EMAIL}">{B.EMAIL}</a> or (347) 205-4468.</p></div>
</section>
<script>
(function(){{var f=document.getElementById('lform'),st=f.querySelector('.ask-st');
f.addEventListener('submit',function(e){{e.preventDefault();if(f._honey.value)return;
var ok=['name','email','llc_name','activity'].every(function(n){{return f[n].value.trim();}})&&/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(f.email.value.trim());
if(!ok){{st.textContent='Please fill in your name, a valid email, the LLC name and what the business will do.';return;}}
var b=f.querySelector('button'),l=b.textContent;b.disabled=true;b.textContent='Sending…';var d=new FormData(f);
d.append('page',location.href);d.append('_subject','LLC formation request: '+f.package.value+' / '+f.state.value+' / '+f.llc_name.value);d.append('_captcha','false');d.append('_template','table');
fetch('{FORM_ENDPOINT}',{{method:'POST',headers:{{'Accept':'application/json'}},body:d}}).then(function(r){{if(!r.ok)throw 0;return r.json();}})
.then(function(j){{if(j.success===false||j.success==='false')throw 0;f.hidden=true;document.getElementById('ldone').hidden=false;
if(window.gtag)gtag('event','generate_lead',{{form:'llc_formation',package:f.package.value,state:f.state.value}});}})
.catch(function(){{st.textContent='Couldn’t send. Please email {B.EMAIL} directly.';b.disabled=false;b.textContent=l;}});}});}})();
</script>'''


FAQ = [
    ("Why form my LLC with an accountant?",
     "Filing the paperwork is the easy part. The decisions that cost money come right after: how the LLC is taxed, whether an S corp election makes sense, state tax registration, and setting up books that are ready for tax time. We handle those from day one."),
    ("Is there anything that renews or bills me later?",
     "No. Each package is a one-time fee plus the state's filing fee at cost. Ongoing bookkeeping or tax work is optional and quoted separately."),
    ("How do I pay?",
     "Send us your details with the form. We review them, confirm the name, and email you an invoice for your package plus the state fee as a separate line. We file once it's paid."),
    ("Do I need a registered agent?",
     "New Jersey requires a registered agent with a New Jersey street address. That can be you, if you have one, or a commercial agent. New York names the Secretary of State as your agent for service of process. We don't sell registered agent service; we'll tell you what your state requires."),
    ("What does New York's publication requirement involve?",
     "Within 120 days of forming, a New York LLC must publish a notice once a week for six weeks in two newspapers chosen by the county clerk, then file a Certificate of Publication ($50). Newspaper costs vary by county, so we quote them at cost."),
    ("Is the operating agreement a legal document?",
     "Yes. We provide a template filled in with your owners, percentages and management, for you to review and sign. MFA is not a law firm and doesn't give legal advice; for complex ownership or investor terms, have an attorney review it."),
    ("What if the state rejects the filing?",
     "We correct the filing and resubmit it. State fees are non-refundable once a filing is submitted, so we confirm every detail with you before we file."),
    ("Can you form my LLC in another state?",
     "We're adding more states. Send us your details with the form and we'll confirm the state fee and timeline before you pay anything."),
]


def build_main():
    url = BASE + "/llc-formation/"
    title = "LLC Formation by an Accountant: NJ & NY, One Price, Paid Once | MFA"
    desc = ("Form your New Jersey or New York LLC with an accountant: state filing, EIN and operating agreement from $99 "
            "plus the state fee, paid once. Tax and QuickBooks setup included in our Business Setup package.")
    steps = [("Tell us about your business", "A short form: the name you want, owners, what you'll do. No payment yet."),
             ("We review, invoice and file", "We check the name, email your invoice (package + state fee), and file once it's paid."),
             ("You're ready to operate", "Your documents, EIN and calendar, plus tax registration and QuickBooks if your package includes them.")]
    steps_html = "".join(f'<div class="st3 card"><span class="st3-n">{i}</span><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for i, (a, b) in enumerate(steps, 1))
    first_year = [
        ("Week 1", "LLC filed, EIN issued, operating agreement signed. Open your business bank account."),
        ("Within 60 days (NJ)", "File NJ-REG for state tax registration, sooner if you'll collect sales tax. New York has no general registration, but sales tax sellers register at least 20 days before starting."),
        ("Within 120 days (NY)", "Finish the publication requirement and file the Certificate of Publication."),
        ("If an S corp fits", "File Form 2553 on time and set up payroll for a reasonable salary."),
        ("Each January", "Send 1099s to contractors you paid last year. Our <a href=\"/tools/do-i-need-to-send-a-1099/\">1099 checker</a> tells you who needs one."),
        ("Each anniversary month", "New Jersey annual report ($75). New York biennial statement every two years ($9)."),
    ]
    fy = "".join(f'<li><span class="ft-k">{esc(k)}</span><p>{t}</p></li>' for k, t in first_year)
    why = [("Tax setup from day one", "Your classification, state registration and S corp question answered before the first invoice goes out."),
           ("Books ready for tax time", "QuickBooks set up with a chart of accounts that fits your business, not a blank file."),
           ("A real reviewer, not a script", "A Big Four trained accountant checks every filing before it goes to the state."),
           ("No surprise renewals", "One fee, paid once. If you want ongoing help, we'll quote it, and you decide.")]
    why_html = "".join(f'<div class="wy card"><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for a, b in why)
    srcs = sorted({(STATES[c]["name"] + ": " + k.replace("_", " "), STATES[c][k]["source_url"]) for c in ORDER for k in ("filing_fee", "annual_report_due", "state_tax_registration") if isinstance(STATES[c].get(k), dict)})
    src_html = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in srcs)
    state_links = " · ".join(f'<a href="/llc-formation/{c.lower()}/">{esc(STATES[c]["name"])} LLC fees and rules</a>' for c in ORDER)
    body = f'''<header class="bhero rhero llc-hero"><div class="wrap"><span class="eyebrow">LLC formation</span>
<h1>Form your LLC with an accountant, <em>not a call center.</em></h1>
<p>Your state filing, EIN, operating agreement and first-year calendar from <strong>$99 plus your state's fee, paid once.</strong> No renewals, and no add-on charges for the basics.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#start">Start my LLC</a><a class="btn btn-line" href="#cost">See my state's total</a></div>
<p class="llc-trust">Big Four trained · Accounting, tax and business solutions · Princeton, NJ, serving clients nationwide</p></div></header>
<main>
<section class="wrap llc-sec" id="packages" aria-labelledby="pk-h"><div class="sec-hd"><span class="eyebrow eb-dark">Packages</span>
<h2 id="pk-h">Three ways to start. One price each.</h2><p>Every package includes the filing, your EIN and an operating agreement template. State fees are added at cost.</p></div>
{packages_html()}{table_html()}</section>
{state_picker()}
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="how-h">Three steps, and a person on the other end.</h2></div>
<div class="st3s">{steps_html}</div></section>
<section class="wrap llc-sec" aria-labelledby="fy-h"><div class="sec-hd"><span class="eyebrow eb-dark">After you form</span><h2 id="fy-h">Your first year, in order.</h2>
<p>What comes due after the LLC exists. Our packages cover the setup; this keeps you on track.</p></div><ol class="ftl">{fy}</ol></section>
<section class="wrap llc-sec" aria-labelledby="why-h"><div class="sec-hd"><span class="eyebrow eb-dark">Why MFA</span><h2 id="why-h">Formation is a tax decision, too.</h2></div>
<div class="wys">{why_html}</div>
<div class="diy card"><div><span class="eyebrow eb-dark">Prefer to do it yourself?</span><h3>DIY guides and checklists</h3>
<p>Our step-by-step LLC setup guide and new business checklist are coming to the MFA shop. Until then, our <a href="/resources/">resources</a> cover the basics.</p></div>
<a class="btn btn-ink" href="/resources/">Browse resources</a></div></section>
{intake_form()}
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><h2 id="faq-h">FAQs</h2>{ui_kit.faq_accordion(FAQ, prefix="llc")}</section>
<section class="wrap llc-sec"><section class="sources"><h2>Sources</h2><ul>{src_html}</ul>
<p class="disclaimer">State facts checked against the official sources above as of {CHECKED}. State fees change; we confirm the current fee before invoicing. {esc(LEGAL)} Educational information, not tax or legal advice.</p>
<p class="disclaimer">{state_links}</p></section></section>
</main>{picker_js()}'''
    ld = ld_service(url)
    page_html = page(title, desc, url, body, ld, active="llc")
    page_html = page_html.replace("</head>", f'<script type="application/ld+json">{json.dumps(faq_ld(FAQ))}</script></head>', 1)
    return write("llc-formation", page_html)


def build_state(code):
    s = STATES[code]
    name = s["name"]
    url = f"{BASE}/llc-formation/{code.lower()}/"
    fee = v(s, "filing_fee")
    pub = v(s, "publication")
    rows = [("Formation document", esc(s.get("formation_document", ""))),
            ("Filing office", esc(v(s, "office") or "")),
            ("State filing fee", f"${fee}" if fee is not None else "Varies"),
            ("Name reservation (optional)", f"${v(s, 'name_reservation_fee')}" if v(s, "name_reservation_fee") is not None else "—")]
    if v(s, "annual_report_fee") is not None:
        rows.append(("Annual report", f"${v(s, 'annual_report_fee')}; due {esc((v(s, 'annual_report_due') or '').lower())}"))
    else:
        note = (s.get("annual_report_fee") or {}).get("note", "")
        bi = v(s, "biennial_statement_fee")
        rows.append(("Annual report", esc(note) + (f" Biennial statement: ${bi}; {esc((v(s, 'annual_report_due') or '').lower())}." if bi else "")))
    if pub:
        rows.append(("Publication", f"Publish once a week for {pub['weeks']} weeks in {pub['newspapers']} newspapers designated by the county clerk, "
                                    f"then file the Certificate of Publication (${pub['certificate_of_publication_fee']}) within {pub['deadline_days']} days of forming."))
    rows.append(("State tax registration", esc(v(s, "state_tax_registration") or "")))
    rows.append(("Registered agent", esc(v(s, "registered_agent") or "")))
    pnote = (s.get("processing_online") or {}).get("note", "")
    if pnote:
        rows.append(("Processing time", esc(pnote)))
    tbl = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in rows)
    extra = pub["certificate_of_publication_fee"] if pub else 0
    tot = "".join(f'<tr><td>{esc(p["name"])}</td><td>${p["price"]}</td><td>${fee}</td><td><strong>${p["price"] + (fee or 0) + extra}{" + newspapers" if pub else ""}</strong></td></tr>' for p in PACKAGES)
    srcs = sorted({u["source_url"] for u in s.values() if isinstance(u, dict) and u.get("source_url")})
    src_html = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u.replace("https://", ""))}</a></li>' for u in srcs)
    title = f"How Much Does an LLC Cost in {name}? Fees, Rules & Formation Help | MFA"
    desc = (f"{name} LLC filing fee ${fee}, annual requirements, tax registration and registered agent rules, checked {CHECKED}. "
            f"Form your {name} LLC with an accountant from $99 plus the state fee, paid once.")
    body = f'''<header class="ahead"><div class="wrap">
<div class="crumbs"><a href="/">Home</a> / <a href="/llc-formation/">LLC formation</a> / {esc(name)}</div>
<span class="eyebrow">{esc(name)} LLC</span><h1>Forming an LLC in {esc(name)}: fees, rules and timing</h1>
<p class="dek">The state's own numbers, checked {CHECKED}, and what your first-year total looks like with MFA.</p></div></header>
<main><div class="tinfo"><article class="article">
<h2>{esc(name)} LLC at a glance</h2><table class="tbl"><tbody>{tbl}</tbody></table>
<h2>Your total with MFA</h2><div class="tbl-wrap tw-s"><table class="tbl"><thead><tr><th>Package</th><th>MFA fee</th><th>State fee</th><th>Due at formation</th></tr></thead><tbody>{tot}</tbody></table></div>
<p>MFA fees are one-time and never renew. {"Newspaper publication costs vary by county and are quoted at cost. " if pub else ""}See <a href="/llc-formation/#packages">what each package includes</a>.</p>
<p><a class="btn btn-ink" href="/llc-formation/?state={code}#start">Start my {esc(name)} LLC</a></p>
<section class="sources"><h2>Sources</h2><ul>{src_html}</ul>
<p class="disclaimer">Facts checked against the official sources above as of {CHECKED}. State fees change; we confirm the current fee before invoicing. {esc(LEGAL)} Educational information, not tax or legal advice.</p></section>
</article></div></main>'''
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": "LLC formation", "item": BASE + "/llc-formation/"},
        {"@type": "ListItem", "position": 3, "name": name, "item": url}]}
    return write(f"llc-formation/{code.lower()}", page(title, desc, url, body, ld, active="llc"))


def build_all():
    return [build_main()] + [build_state(c) for c in ORDER]


if __name__ == "__main__":
    print("\n".join(build_all()))
