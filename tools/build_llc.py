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
import seo
import ui_kit
from build_resources import page, write, esc, BASE, svg

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "llc-states.json").read_text(encoding="utf-8"))
STATES = DATA["states"]
ORDER = sorted(STATES, key=lambda c: STATES[c]["name"])  # every state in the data file, A–Z by name
COMING = [c for c in DATA["meta"].get("coming_next", []) if c not in STATES]
FORM_ENDPOINT = "https://formsubmit.co/ajax/" + B.EMAIL
LEGAL = ("MFA is not a law firm and does not provide legal advice. We prepare and file formation documents "
         "based on the information you provide.")


def d(ts):
    return datetime.fromisoformat(ts).strftime("%B %-d, %Y")


CHECKED = d(DATA["meta"]["checked"])
import hashlib
ORDER_JS_V = hashlib.md5((ROOT / "site" / "resources" / "llc-order.js").read_bytes()).hexdigest()[:10]

PACKAGES = [
    {"id": "formation", "name": "Formation", "price": 150, "tag": "File it right",
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
    {"id": "launch", "name": "Complete Launch", "price": 649, "tag": "Launch-ready",
     "lead": "Everything in Business Setup, plus your elections, sales tax and first month of books.",
     "items": ["Everything in Formation + Business Setup",
               "S corp election (Form 2553) filed if it fits, with salary guidance",
               "Sales tax registration and filing calendar, if you sell taxable goods or services",
               "First month of bookkeeping: one bank, one card, up to 100 transactions, first P&amp;L",
               "Then continue monthly from $199/month, if you want (optional, month to month)",
               "Our DIY guides and checklists included",
               "30-day check-in call"]},
]

ROWS = [  # (feature, formation, setup, launch)
    ("State filing + name check", 1, 1, 1), ("EIN application", 1, 1, 1), ("Operating agreement template", 1, 1, 1),
    ("First-year compliance calendar", 1, 1, 1), ("Tax classification review (LLC vs S corp)", 0, 1, 1),
    ("State tax registration", 0, 1, 1), ("QuickBooks Online setup", 0, 1, 1), ("Onboarding call", 0, 1, 1),
    ("S corp election (Form 2553), if it fits", 0, 0, 1), ("Sales tax registration", 0, 0, 1),
    ("First month of bookkeeping", 0, 0, 1), ("DIY guides and checklists", 0, 0, 1),
    ("Monthly bookkeeping after that", "Optional add-on", "Optional add-on", "Optional, from $199/mo"), ("Renews every year?", "No", "No", "No"),
]

ICO_OK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'


MONTHLY = {"price": 199, "scope": "one bank account, one credit card, up to 100 transactions a month",
           "items": ["Transactions categorized to your chart of accounts every month",
                     "Bank and credit card accounts reconciled to the statements",
                     "Monthly P&amp;L and balance sheet, with a short note on what changed",
                     "Owner draws, loans and transfers kept separate from income and expenses",
                     "Year-end books handed to your tax preparer (or to us) ready to file",
                     "Questions by email between closes"]}


# Add-ons sold in the LLC cart (Zain, 2026-10-20 23:3x). Bookkeeping: up to 4 accounts and 200 transactions/month
# is priced here; anything bigger is quoted. Billed monthly by Stripe, first charge 30 days after checkout.
ADDONS = {
    # Price = base (covers 2 accounts, up to 100 txns) + per extra account + volume add-on. Over 4 accounts or 200 txns: quoted.
    # Base $199 and the quote line (over 4 accounts / 200 txns) are Zain's (2026-10-20 23:28). The +$50/account and
    # +$100 for 101-200 txns steps are the Hub's proposal, flagged to Zain for confirmation.
    "bk": {"name": "Monthly bookkeeping", "base": 199, "incl_accounts": 2, "per_account": 50, "max_accounts": 4, "trial_days": 30,
           "tiers": [{"id": "100", "max": 100, "label": "up to 100 transactions/mo", "add": 0},
                     {"id": "200", "max": 200, "label": "101 to 200 transactions/mo", "add": 100}]},
    "f1099": {"name": "1099 preparation and e-filing", "per": 25, "min": 75},
    "salestax": {"name": "Sales tax registration", "price": 99, "included_in": ["launch"]},
    "scorp": {"name": "S corp election (Form 2553)", "price": 149, "included_in": ["launch"]},
    "quarterly": {"name": "Quarterly estimated tax service", "price": 250},  # Zain 2026-10-21 01:57: $250 for the year (was $49/quarter)
}


def pricing_obj():
    data = {"packages": {p["id"]: {"name": p["name"], "price": p["price"]} for p in PACKAGES}, "states": {}, "addons": ADDONS}
    for c in ORDER:
        s = STATES[c]
        pub = v(s, "publication")
        data["states"][c] = {"code": c, "name": s["name"], "fee": v(s, "filing_fee"), "extra": v(s, "formation_extra") or 0,
                             "pub_fee": pub.get("certificate_of_publication_fee") if isinstance(pub, dict) else None,
                             "pub": bool(pub) and not (isinstance(pub, dict) and pub.get("required") is False)}
    return data


def monthly_html():
    lis = "".join(f"<li>{ICO_OK}<span>{i}</span></li>" for i in MONTHLY["items"])
    return f'''<section class="wrap llc-sec" id="monthly" aria-labelledby="mo-h">
<div class="sec-hd"><span class="eyebrow eb-dark">After month one</span><h2 id="mo-h">From your first month of books to every month.</h2>
<p>Complete Launch includes your first month of bookkeeping. If you like how it works, keep going: same accountant, same file, no handoff.</p></div>
<div class="pk pk-mo"><div class="pkc card feat"><span class="pk-tag">Optional · month to month</span><h3>Monthly Bookkeeping</h3>
<p class="pk-price"><b>${MONTHLY["price"]}</b><span>/ month · starting price</span></p>
<p class="pk-lead">For {MONTHLY["scope"]}. More accounts or volume? We quote it up front before you start.</p>
<ul class="pk-list">{lis}</ul>
<a class="btn btn-gold" href="#start" data-mo="1">Add monthly bookkeeping</a></div>
<div class="pkc card"><span class="pk-tag">How the switch works</span><h3>No gap between month one and month two</h3>
<ol class="mo-steps"><li><b>Month one</b><span>Included in Complete Launch: we set up QuickBooks and close your first month.</span></li>
<li><b>Day 30 check-in</b><span>We review the first P&amp;L together and confirm your monthly scope and price.</span></li>
<li><b>Month two onward</b><span>We close your books each month and bill you monthly. Stop whenever you want.</span></li></ol>
<p class="muted">On Formation or Business Setup? You can add monthly bookkeeping too; tick the box in the form below. Bookkeeping doesn't include tax returns, payroll or sales tax filings; we quote those separately.</p></div></div></section>'''


import re as _re
_INTERNAL = _re.compile(r"confirm|likely|this page|I used|older|could not|couldn't|blocked|third-party|unclear|conflict|not stated|page says|pages? (?:still|disagree)|from memory|fetch|portal before|quot", _re.I)


def pubnote(t):
    """Research notes in the data file are for us; show a note publicly only if it reads as a plain fact."""
    return "" if (not t or _INTERNAL.search(t)) else t


_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def lc1(t):
    if not t or t.startswith(_MONTHS):
        return t or ""
    return t[:1].lower() + t[1:]


def v(s, k):
    f = s.get(k)
    return f.get("value") if isinstance(f, dict) else None


def picker_data():
    out = {}
    for code in ORDER:
        s = STATES[code]
        pub = v(s, "publication")
        pubf = s.get("publication") if isinstance(s.get("publication"), dict) else {}
        out[code] = {
            "name": s["name"], "fee": v(s, "filing_fee"), "extra": v(s, "formation_extra") or 0,
            "extra_note": (s.get("formation_extra") or {}).get("note", ""),
            "annual": v(s, "annual_report_fee"), "annual_due": v(s, "annual_report_due"),
            "annual_note": (s.get("annual_report_fee") or {}).get("note", ""),
            "biennial": v(s, "biennial_statement_fee"),
            "reg": v(s, "state_tax_registration"),
            "pub_fee": pub.get("certificate_of_publication_fee") if isinstance(pub, dict) else None,
            "pub_note": (pubnote(pubf.get("note") or (pub if isinstance(pub, str) else "")) or "see the state page for the steps.") if pub else "",
            "freq": v(s, "annual_report_frequency"),
            "special": [x for x in (x if isinstance(x, str) else (x.get("value") or "") for x in (s.get("special_rules") or [])) if x and not _INTERNAL.search(x)][:3],
            "url": f"/llc-formation/{code.lower()}/",
        }
    return out


def ld_service(url, title="LLC formation", desc=""):
    """Page graph for /llc-formation/: the firm, the LLC formation Service with its three public prices, the FAQ and the breadcrumb."""
    faq = {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": faq_ld(FAQ)["mainEntity"]}
    return seo.graph(url, title, desc, seo.llc_service(url), faq, *seo.llc_addon_catalog(), kind="WebPage", full_org=True,
                     crumb=[("Home", BASE + "/"), ("LLC formation", url)], extra={"mainEntity": {"@id": url + "#service"}})


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
<span class="hint">{("More states coming: " + esc(soon) + ". ") if soon else ""}All 50 states and Washington, DC. Already formed and need tax setup? <a href="#start">Ask us</a>.</span></div>
<div class="fld"><span class="lbl">Package</span><div class="opts">{pk}</div></div></div>
<div class="tcard tres" aria-live="polite"><h2 id="c-h">Your LLC</h2><p class="sub" id="c-sub">First-year cost with MFA</p>
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
$('c-h').textContent=s.name+' LLC';$('c-pk').textContent=m(p);$('c-fee').textContent=s.fee!=null?m(s.fee+s.extra):'Confirmed at quote';
var tot=p+(s.fee||0)+(s.extra||0)+(s.pub_fee||0);$('c-tot').textContent=m(tot)+(s.pub_fee||s.fee==null?' +':'');
var n=[];if(s.fee==null)n.push('We confirm the current state filing fee before invoicing and add it at cost.');if(s.extra_note)n.push(s.extra_note);if(s.pub_fee)n.push('Includes the '+m(s.pub_fee)+' Certificate of Publication fee. Newspaper publication costs vary by county and are quoted at cost.');
else if(s.pub_note)n.push('Publication required: '+s.pub_note);
if(s.annual){var fq=String(s.freq||'').toLowerCase();var per=/bienn|two|2/.test(fq)?' every two years':(fq&&!/annual|year/.test(fq)?' ('+s.freq+')':' a year');
n.push('Then '+m(s.annual)+per+' to the state (annual report or tax)'+(s.annual_due?', due '+(/^(January|February|March|April|May|June|July|August|September|October|November|December)/.test(s.annual_due)?s.annual_due:s.annual_due.charAt(0).toLowerCase()+s.annual_due.slice(1)):'')+'.');}
else if(s.annual===0)n.push('No state annual report fee.');
(s.special||[]).forEach(function(t){if(t)n.push(t);});
if(s.biennial)n.push('Then '+m(s.biennial)+' every two years for the biennial statement.');
if(s.reg)n.push('Tax registration: '+String(s.reg).replace(/\\.$/,'')+'.');n.push('Nothing from MFA renews. Bookkeeping after month one is optional.');
$('c-notes').innerHTML=n.map(function(t){return '<li>'+t.replace(/</g,'&lt;')+'</li>';}).join('');$('c-link').href=s.url;
$('c-link').textContent=s.name+' details';var f=document.getElementById('f-state');if(f&&f.value!==st.value){f.value=st.value;f.dispatchEvent(new Event('change',{bubbles:true}));}}
st.addEventListener('change',run);document.addEventListener('change',function(e){if(e.target.name==='pk'){var f=document.getElementById('f-pk');if(f&&f.value!==e.target.value){f.value=e.target.value;f.dispatchEvent(new Event('change',{bubbles:true}));}run();}});
[].slice.call(document.querySelectorAll('[data-mo]')).forEach(function(a){a.addEventListener('click',function(){var c=document.getElementById('f-mo');if(c&&!c.checked){c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));}});});
[].slice.call(document.querySelectorAll('[data-pk]')).forEach(function(a){a.addEventListener('click',function(){var f=document.getElementById('f-pk');if(f){f.value=a.getAttribute('data-pk');f.dispatchEvent(new Event('change',{bubbles:true}));}});});
var q=new URLSearchParams(location.search).get('state');if(q&&S[q.toUpperCase()])st.value=q.toUpperCase();else if(S.NJ)st.value='NJ';run();})();
</script>""" % data


def addons_html():
    A = ADDONS
    t = A["bk"]["tiers"]
    B = A["bk"]
    vol = "".join(f'<option value="{x["id"]}">{"Up to " + str(x["max"]) if i == 0 else str(t[i-1]["max"] + 1) + " to " + str(x["max"])}{" (+$" + str(x["add"]) + "/mo)" if x["add"] else " (included)"}</option>' for i, x in enumerate(t))
    acc = "".join(f'<option value="{i}">{i}{" (+$" + str((i - B["incl_accounts"]) * B["per_account"]) + "/mo)" if i > B["incl_accounts"] else " (included)"}</option>' for i in range(1, B["max_accounts"] + 1))
    return f'''<div class="fld"><span class="lbl">Add-ons</span><div class="addons">
<div class="addon"><label class="opt opt-wide"><input type="checkbox" id="f-mo" name="monthly_bookkeeping" value="yes"/><span><b>Monthly bookkeeping</b> <small>${B["base"]}/month for up to {B["incl_accounts"]} accounts and {t[0]["max"]} transactions · first charge {A["bk"]["trial_days"]} days after checkout · cancel anytime</small></span></label>
<div class="addon-sub" id="bk-sub" hidden><div class="lgrid">
<div class="fld"><label for="bk-acc">Bank and credit card accounts</label><select id="bk-acc" name="bk_accounts"><option value="">Choose</option>{acc}<option value="5+">{A["bk"]["max_accounts"] + 1} or more (quoted)</option></select></div>
<div class="fld"><label for="bk-vol">Transactions a month, all accounts</label><select id="bk-vol" name="bk_volume"><option value="">Choose</option>{vol}<option value="over">More than {t[-1]["max"]} (quoted)</option></select></div></div>
<p class="hint" id="bk-price">Choose your accounts and monthly transactions to see the price.</p></div></div>
<div class="addon"><label class="opt opt-wide"><input type="checkbox" id="f-1099" name="addon_1099" value="yes"/><span><b>{A["f1099"]["name"]}</b> <small>${A["f1099"]["per"]} per form, ${A["f1099"]["min"]} minimum</small></span></label>
<div class="addon-sub" id="f1099-sub" hidden><div class="fld fld-n"><label for="f1099-n">How many 1099s?</label><input type="number" id="f1099-n" name="f1099_forms" min="1" max="250" value="3" inputmode="numeric"/></div></div></div>
<label class="opt opt-wide" id="ad-st"><input type="checkbox" id="f-st" name="addon_salestax" value="yes"/><span><b>{A["salestax"]["name"]}</b> <small class="ad-pr" data-price="${A["salestax"]["price"]}">${A["salestax"]["price"]}</small></span></label>
<label class="opt opt-wide" id="ad-sc"><input type="checkbox" id="f-sc" name="addon_scorp" value="yes"/><span><b>{A["scorp"]["name"]}</b> <small class="ad-pr" data-price="${A["scorp"]["price"]}">${A["scorp"]["price"]}</small></span></label>
<label class="opt opt-wide"><input type="checkbox" id="f-q" name="addon_quarterly" value="yes"/><span><b>{A["quarterly"]["name"]}</b> <small>${A["quarterly"]["price"]} for the year: four federal and state estimate calculations with due dates. Based on books reconciled through each quarter-end (automatic if we keep your books); if they aren't current, we use the prior-year safe harbor.</small></span></label>
</div></div>'''


def cart_html():
    return '''<aside class="tcard lcart" id="lcart" aria-labelledby="cart-h"><h3 id="cart-h">Your order</h3>
<ul class="cart-lines" id="cart-today" aria-live="polite"></ul>
<div class="cart-tot"><span>Due today</span><b id="cart-total">—</b></div>
<div class="cart-rec" id="cart-rec" hidden></div>
<ul class="cart-notes" id="cart-notes"></ul>
<button type="button" class="btn btn-gold cart-go" id="cart-go">Continue to secure checkout</button>
<p class="cart-fine">Full refund if we can't file your LLC. State fees can't be refunded once the state accepts the filing.</p></aside>
<div class="cart-bar" id="cartbar" hidden><span>Due today <b id="cartbar-t">—</b></span><a href="#lcart">Review order</a></div>'''


def cart_js():
    return ("<script type=\"module\">import {selectionFromForm, computeOrder} from '/resources/llc-order.js?v=" + ORDER_JS_V + "';"
            "const P=" + json.dumps(pricing_obj()) + ";" + r'''
const f=document.getElementById('lform'),$=id=>document.getElementById(id);
const usd=c=>'$'+(c/100).toLocaleString('en-US',{minimumFractionDigits:c%100?2:0,maximumFractionDigits:2});
const esc=t=>String(t).replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
function fields(){const o={};new FormData(f).forEach((v,k)=>{if(k[0]!=='_')o[k]=v;});return o;}
function render(){
  const o=fields(),sel=selectionFromForm(o),r=computeOrder(P,sel),launch=sel.package==='launch';
  $('bk-sub').hidden=!sel.bk.on;$('f1099-sub').hidden=!sel.f1099.on;
  for(const [id,lab] of [['f-st','ad-st'],['f-sc','ad-sc']]){const c=$(id),s=$(lab).querySelector('.ad-pr');c.disabled=launch;if(launch)c.checked=false;
    s.textContent=launch?'Included in Complete Launch':s.dataset.price;$(lab).classList.toggle('opt-inc',launch);}
  const bp=$('bk-price');
  if(sel.bk.on)bp.textContent=r.bk&&r.bk.price?('$'+r.bk.price+'/month, first charge 30 days after checkout. Cancel anytime.'):r.bk&&r.bk.quote?'Quoted after a short review: nothing is charged for bookkeeping today.':'Choose your accounts and monthly transactions to see the price.';
  $('cart-today').innerHTML=r.today.map(l=>'<li><span>'+esc(l.name)+'</span><b>'+usd(l.amount)+'</b></li>').join('')+r.included.map(l=>'<li class="inc"><span>'+esc(l.name)+'</span><b>Included</b></li>').join('');
  $('cart-total').textContent=r.ok?usd(r.total):'—';$('cartbar-t').textContent=r.ok?usd(r.total):'—';
  const rec=$('cart-rec');rec.hidden=!r.recurring.length;rec.innerHTML=r.recurring.map(l=>'<div><span>Then '+esc(l.name)+'</span><b>'+usd(l.amount)+'/mo</b><small>First charge in '+l.trial_days+' days</small></div>').join('');
  $('cart-notes').innerHTML=r.notes.map(n=>'<li>'+esc(n)+'</li>').join('');
  window.MFA_ORDER=r;
}
f.addEventListener('input',render);f.addEventListener('change',e=>{
  if(e.target.id==='f-state'){const s=$('st');if(s&&s.value!==e.target.value&&P.states[e.target.value]){s.value=e.target.value;s.dispatchEvent(new Event('change'));}}
  if(e.target.id==='f-pk'){const r=document.querySelector('input[name=pk][value="'+e.target.value+'"]');if(r&&!r.checked){r.checked=true;}}
  render();});
document.addEventListener('change',e=>{if(e.target.id==='st'||e.target.name==='pk')setTimeout(render,0);});
$('cart-go').addEventListener('click',()=>{if(f.requestSubmit)f.requestSubmit();else $('lsubmit').click();});
const bar=$('cartbar'),sec=document.getElementById('start');
if('IntersectionObserver' in window){new IntersectionObserver(es=>{bar.hidden=!es[0].isIntersecting;}).observe(sec);}
render();
</script>''')


def intake_form():
    st_opts = '<option value="">Choose a state</option>' + "".join(f'<option value="{c}"{" selected" if c == "NJ" else ""}>{esc(STATES[c]["name"])}</option>' for c in ORDER) + '<option value="Unsure">Not sure yet</option>'
    pk_opts = "".join(f'<option value="{p["id"]}"{" selected" if p.get("feat") else ""}>{esc(p["name"])} (${p["price"]})</option>' for p in PACKAGES)
    R = '<span class="req" aria-hidden="true">*</span>'

    def fld(fid, label, ctrl, req=False, hint=""):
        return (f'<div class="fld" id="w-{fid}"><label for="{fid}">{label}{R if req else ""}</label>{ctrl}'
                f'{f"<span class=hint>{hint}</span>" if hint else ""}<span class="err-msg" id="e-{fid}" role="alert"></span></div>')
    req = ' required aria-required="true"'
    return f'''<section class="wrap llc-sec" id="start" aria-labelledby="start-h">
<div class="sec-hd"><span class="eyebrow eb-dark">Start my LLC</span><h2 id="start-h">Tell us about your business.</h2>
<p>Fill in your details, then pay securely by card or bank account at checkout, right on this page (powered by Stripe). One total: your package plus your state's fee at cost. If we can't file your LLC (for example, the name isn't available), we refund you in full; state fees can't be refunded once the state accepts the filing.</p></div>
<div class="lbuy">{cart_html()}
<form class="tcard lform" id="lform" novalidate>
<p class="req-note"><span class="req">*</span> Required</p>
<div class="form-err" id="form-err" role="alert" tabindex="-1" hidden></div>
<div class="lgrid">
{fld("f-name", "Your name", f'<input type="text" id="f-name" name="name" autocomplete="name"{req}/>', True)}
{fld("f-email", "Email", f'<input type="email" id="f-email" name="email" autocomplete="email" inputmode="email" autocapitalize="off" spellcheck="false"{req}/>', True)}
{fld("f-phone", "Phone (optional)", '<input type="tel" id="f-phone" name="phone" autocomplete="tel" inputmode="tel"/>')}
{fld("f-state", "State to form in", f'<select id="f-state" name="state"{req}>{st_opts}</select>', True)}
{fld("f-pk", "Package", f'<select id="f-pk" name="package"{req}>{pk_opts}</select>', True)}
{fld("f-llc", "LLC name you want", f'<input type="text" id="f-llc" name="llc_name"{req} placeholder="e.g. Brightline Studio LLC"/>', True)}
{fld("f-alt", "Backup name (optional)", '<input type="text" id="f-alt" name="backup_name"/>')}
{fld("f-own", "Number of owners", '<select id="f-own" name="owners"><option>1 (single-member)</option><option>2</option><option>3–5</option><option>6 or more</option></select>')}
{fld("f-mgmt", "Managed by", '<select id="f-mgmt" name="managed_by"><option>The owners (member-managed)</option><option>Appointed managers (manager-managed)</option><option>Not sure, help me decide</option></select>')}
{fld("f-act", "What will the business do?", f'<input type="text" id="f-act" name="activity"{req} placeholder="e.g. graphic design services"/>', True)}
</div>
<div class="fld"><span class="lbl">Check any that apply</span><div class="opts opts-2 opts-eq">
<label class="opt"><input type="checkbox" name="will_hire" value="yes"/><span>I'll hire employees in the first year</span></label>
<label class="opt"><input type="checkbox" name="sells_taxable" value="yes"/><span>I'll sell products or taxable services</span></label>
<label class="opt"><input type="checkbox" name="has_agent" value="yes"/><span>I already have a registered agent or in-state street address</span></label>
<label class="opt"><input type="checkbox" name="s_corp_interest" value="yes"/><span>I want to know if an S corp makes sense</span></label></div></div>
{addons_html()}
{fld("f-notes", "Anything else? (optional)", '<textarea id="f-notes" name="notes" rows="3" placeholder="Timing, partners, questions"></textarea>', False, "Please don't include Social Security or bank account numbers. We collect what the IRS needs securely after we've confirmed your order.")}
<input class="ask-hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
<div class="lsubmit"><button class="btn btn-ink" type="submit" id="lsubmit">Continue to secure checkout</button><p class="ask-st" role="status" aria-live="polite"></p></div>
<p class="pay-note" id="paynote">Card or bank account via Stripe. You'll see the full total before you pay.</p>
</form></div>
<div class="paymodal" id="paymodal" role="dialog" aria-modal="true" aria-labelledby="pay-h" hidden><div class="paybox">
<div class="pay-hd"><div><h2 id="pay-h">Secure checkout</h2><p id="pay-sum" class="pay-sum"></p></div><button type="button" class="pay-x" id="payclose" aria-label="Close checkout">×</button></div>
<div id="paymount"></div><p class="pay-foot">Payments are processed by Stripe. MFA never sees or stores your card number.</p></div></div>
<div class="tcard ldone" id="ldone" tabindex="-1" hidden><h2>Thanks, we have your details.</h2><p>We'll check the name and email you a secure checkout link for your package plus the state fee, usually within one to three business days. Questions in the meantime: <a href="mailto:{B.EMAIL}">{B.EMAIL}</a> or (347) 205-4468.</p></div>
</section>
<script>
(function(){{var f=document.getElementById('lform'),st=f.querySelector('.ask-st'),box=document.getElementById('form-err');
var EM=/^[^@\\s]+@[^@\\s]+\\.[A-Za-z]{{2,}}$/;
var RULES=[['f-name','Please enter your name.',function(v){{return v.length>1;}}],
['f-email','Please enter a valid email address, like name@example.com.',function(v){{return EM.test(v);}}],
['f-state','Please choose a state.',function(v){{return !!v;}}],
['f-pk','Please choose a package.',function(v){{return !!v;}}],
['f-llc','Please enter the LLC name you want.',function(v){{return v.length>1;}}],
['f-act','Please tell us what the business will do.',function(v){{return v.length>1;}}]];
function mark(id,msg){{var el=document.getElementById(id),w=document.getElementById('w-'+id),e=document.getElementById('e-'+id);
if(msg){{w.classList.add('has-err');el.setAttribute('aria-invalid','true');el.setAttribute('aria-describedby','e-'+id);e.textContent=msg;}}
else{{w.classList.remove('has-err');el.removeAttribute('aria-invalid');e.textContent='';}}}}
function check(id){{for(var i=0;i<RULES.length;i++)if(RULES[i][0]===id){{var v=document.getElementById(id).value.trim(),ok=RULES[i][2](v);mark(id,ok?'':RULES[i][1]);return ok;}}return true;}}
RULES.forEach(function(r){{var el=document.getElementById(r[0]);
el.addEventListener('blur',function(){{if(el.value.trim()||el.getAttribute('aria-invalid'))check(r[0]);}});
el.addEventListener('input',function(){{if(el.getAttribute('aria-invalid'))check(r[0]);}});
el.addEventListener('change',function(){{if(el.getAttribute('aria-invalid'))check(r[0]);}});}});
function showErr(html){{box.innerHTML=html;box.hidden=false;box.focus();box.scrollIntoView({{block:'center',behavior:'smooth'}});}}
f.addEventListener('submit',function(e){{e.preventDefault();if(f._honey.value)return;st.textContent='';
var bad=RULES.filter(function(r){{return !check(r[0]);}});
if(bad.length){{showErr('<strong>Please fix '+(bad.length===1?'1 field':bad.length+' fields')+':</strong><ul>'+bad.map(function(r){{return '<li><a href="#'+r[0]+'">'+r[1]+'</a></li>';}}).join('')+'</ul>');
[].slice.call(box.querySelectorAll('a')).forEach(function(a){{a.addEventListener('click',function(ev){{ev.preventDefault();var t=document.getElementById(a.getAttribute('href').slice(1));t.focus();t.scrollIntoView({{block:'center'}});}});}});return;}}
box.hidden=true;var b=document.getElementById('lsubmit'),l=b.textContent;b.disabled=true;b.textContent=PAY.enabled?'Opening checkout…':'Sending…';
f.email.value=f.email.value.trim();var d=new FormData(f);d.append('page',location.href);d.append('_replyto',f.email.value);
d.append('_subject',(PAY.enabled?'LLC order started (awaiting payment): ':'LLC formation request: ')+f.package.value+' / '+f.state.value+' / '+f.llc_name.value);d.append('_captcha','false');d.append('_template','table');
var lead=fetch('{FORM_ENDPOINT}',{{method:'POST',headers:{{'Accept':'application/json'}},body:d}}).then(function(r){{return r.json().catch(function(){{return {{success:r.ok}};}});}})
.then(function(j){{if(!j||j.success===false||j.success==='false')throw new Error((j&&j.message)||'Send failed');
if(window.mfaLead)mfaLead('llc_formation',{{package:f.package.value,state:f.state.value}});return true;}});
function fallback(err){{var body=encodeURIComponent('Name: '+f.name.value+'\\nEmail: '+f.email.value+'\\nPhone: '+f.phone.value+'\\nState: '+f.state.value+'\\nPackage: '+f.package.value+'\\nLLC name: '+f.llc_name.value+'\\nBusiness: '+f.activity.value+'\\nNotes: '+f.notes.value);
showErr('<strong>We couldn’t '+(PAY.enabled?'open checkout':'send your details')+' just now.</strong> Please <a href="mailto:{B.EMAIL}?subject='+encodeURIComponent('LLC formation request')+'&body='+body+'">email your details to {B.EMAIL}</a> (we’ve filled in the email for you) or call (347) 205-4468.');
b.disabled=false;b.textContent=l;if(window.console)console.warn('LLC form:',err&&err.message);}}
if(!PAY.enabled){{lead.then(function(){{f.hidden=true;var dn=document.getElementById('ldone');dn.hidden=false;dn.focus();dn.scrollIntoView({{block:'center'}});}}).catch(fallback);return;}}
lead.catch(function(e){{if(window.console)console.warn('LLC lead email:',e&&e.message);}});
var data={{}};new FormData(f).forEach(function(v,k){{if(k.charAt(0)!=='_')data[k]=v;}});
fetch('/api/llc-checkout',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}}).then(function(r){{return r.json().then(function(j){{if(!r.ok||!j.clientSecret)throw new Error(j.message||j.error||('HTTP '+r.status));return j;}});}})
.then(function(j){{return stripeReady().then(function(S){{return S.initEmbeddedCheckout({{fetchClientSecret:function(){{return Promise.resolve(j.clientSecret);}}}});}}).then(function(co){{
openPay(co,j);if(window.gtag)gtag('event','begin_checkout',{{value:j.total,currency:'USD',items:[{{item_name:'LLC formation '+f.package.value}}]}});b.disabled=false;b.textContent=l;}});}}).catch(fallback);}});
var CO=null,modal=document.getElementById('paymodal');
function openPay(co,j){{CO=co;document.getElementById('pay-sum').textContent='Total today: $'+Number(j.total).toLocaleString('en-US',{{minimumFractionDigits:2}})+(j.feeKnown?'':' (state fee confirmed and charged separately)')+((j.recurring||[]).map(function(x){{return ' · then $'+x.amount+'/mo bookkeeping from day 30';}}).join(''));
modal.hidden=false;document.body.style.overflow='hidden';co.mount('#paymount');document.getElementById('payclose').focus();}}
function closePay(){{if(CO){{try{{CO.destroy();}}catch(e){{}}CO=null;}}modal.hidden=true;document.body.style.overflow='';}}
document.getElementById('payclose').addEventListener('click',closePay);document.addEventListener('keydown',function(e){{if(e.key==='Escape'&&!modal.hidden)closePay();}});
var PAY={{enabled:false}},SP=null;function stripeReady(){{if(SP)return SP;SP=new Promise(function(res,rej){{var s=document.createElement('script');s.src='https://js.stripe.com/v3/';s.onload=function(){{res(window.Stripe(PAY.pk));}};s.onerror=function(){{SP=null;rej(new Error('Stripe.js failed to load'));}};document.head.appendChild(s);}});return SP;}}
fetch('/api/llc-config').then(function(r){{return r.ok?r.json():{{enabled:false}};}}).then(function(c){{PAY=c||{{enabled:false}};if(!PAY.enabled){{document.getElementById('lsubmit').textContent='Send my details';var n=document.getElementById('paynote');if(n)n.textContent='Card checkout is being set up. Send your details and we’ll email you a secure checkout link.';}}
else if(PAY.mode==='test'){{var n2=document.getElementById('paynote');if(n2)n2.textContent='Test mode: no real charges.';}}}}).catch(function(){{document.getElementById('lsubmit').textContent='Send my details';}});
}})();
</script>
</script>'''

FAQ = [
    ("Why form my LLC with an accountant?",
     "Filing the paperwork is the easy part. The decisions that cost money come right after: how the LLC is taxed, whether an S corp election makes sense, state tax registration, and setting up books that are ready for tax time. We handle those from day one."),
    ("Is there anything that renews or bills me later?",
     "No. Each package is a one-time fee plus the state's filing fee at cost. Monthly bookkeeping is optional: it starts only if you ask for it, runs month to month, and you can stop anytime."),
    ("What happens after the first month of bookkeeping?",
     "Complete Launch includes your first month. At the 30-day check-in we review it with you. If you want to continue, monthly bookkeeping starts at $199 a month for up to two accounts (for example one bank account and one credit card) and up to 100 transactions a month. Each extra account adds $50 a month and 101 to 200 transactions add $100 a month. More than four accounts or 200 transactions a month is quoted up front. If not, you keep your QuickBooks file and everything we set up."),
    ("How do I pay?",
     "By card or bank account at checkout on this page, powered by Stripe. You pay one total: your package plus your state's filing fee at cost, shown as separate lines on your receipt. We check the name and file right after. If we can't file, we refund you in full; state fees can't be refunded once the state accepts the filing."),
    ("Which states do you form LLCs in?",
     "All 50 states and Washington, DC. Our package price is the same everywhere; only the state's own fee changes. Pick your state above to see the total, or open your state's page for its fees, annual report and tax registration rules."),
    ("Which state should I form in?",
     "Usually the state where you live and do business. Forming in Delaware, Wyoming or Nevada and operating somewhere else normally means registering in your home state too, so you pay two sets of fees. We'll tell you if another state makes sense for you."),
    ("Do I need a registered agent?",
     "Almost every state requires a registered agent with a street address in the state where the LLC is formed. If you live there, that can be you. If you form somewhere you don't have an address, you'll need a commercial registered agent. We don't sell registered agent service; each state page lists what that state requires."),
    ("Do any states require newspaper publication?",
     "A few do. New York requires publication in two newspapers for six weeks, then a $50 Certificate of Publication. Some other states have their own publication rules; your state's page lists them. Newspaper costs vary by county, so we quote them at cost."),
    ("Is the operating agreement a legal document?",
     "Yes. We provide a template filled in with your owners, percentages and management, for you to review and sign. MFA is not a law firm and doesn't give legal advice; for complex ownership or investor terms, have an attorney review it."),
    ("What if the state rejects the filing?",
     "We correct the filing and resubmit it. State fees are non-refundable once a filing is submitted, so we confirm every detail with you before we file."),
    ("What does the state charge after formation?",
     "Most states charge an annual or biennial report fee, and a few charge an annual franchise or privilege tax (California, for example). We show each state's figure on its page and in the cost picker, and your first-year compliance calendar lists the due dates."),
]


def build_main():
    url = BASE + "/llc-formation/"
    title = "LLC Formation in All 50 States, From $150 | MFA"
    desc = ("Form your LLC in any state with an accountant: filing, EIN and operating agreement from $150 plus the state fee, "
            "paid once. Tax and QuickBooks setup.")
    steps = [("Tell us about your business", "A short form: the name you want, owners, and what you'll do."),
             ("Pay securely at checkout", "Card or bank account through Stripe, right on this page: package + state fee, one total. We check the name and file."),
             ("You're ready to operate", "Your documents, EIN and calendar, plus tax registration and QuickBooks if your package includes them.")]
    steps_html = "".join(f'<div class="st3 card"><span class="st3-n">{i}</span><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for i, (a, b) in enumerate(steps, 1))
    first_year = [
        ("Right after filing", "LLC filed, EIN issued, operating agreement signed. Open your business bank account."),
        ("In the first weeks", "Register with your state's tax agency if your state or business needs it, for example NJ-REG in New Jersey within 60 days, and a sales tax permit before your first taxable sale."),
        ("If your state requires it", "Finish any publication requirement (New York: within 120 days) and file the proof with the state."),
        ("If an S corp fits", "File Form 2553 on time and set up payroll for a reasonable salary."),
        ("Each January", "Send 1099s to contractors you paid last year. Our <a href=\"/tools/do-i-need-to-send-a-1099/\">1099 checker</a> tells you who needs one."),
        ("Every year (or two)", "Your state's annual or biennial report and any franchise tax. Your state's page shows the fee and due date."),
    ]
    fy = "".join(f'<li><span class="ft-k">{esc(k)}</span><p>{t}</p></li>' for k, t in first_year)
    why = [("Tax setup from day one", "Your classification, state registration and S corp question answered before your first sale."),
           ("Books ready for tax time", "QuickBooks set up with a chart of accounts that fits your business, not a blank file."),
           ("A real reviewer, not a script", "A Big Four trained accountant checks every filing before it goes to the state."),
           ("No surprise renewals", "One fee, paid once. If you want ongoing help, we'll quote it, and you decide.")]
    why_html = "".join(f'<div class="wy card"><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for a, b in why)
    def _fee(c):
        f = v(STATES[c], "filing_fee")
        return f"${f:,}" if isinstance(f, (int, float)) else "See page"
    directory = "".join(f'<li><a href="/llc-formation/{c.lower()}/"><span>{esc(STATES[c]["name"])}</span><b>{_fee(c)}</b></a></li>' for c in ORDER)
    body = f'''<header class="bhero rhero llc-hero"><div class="wrap"><span class="eyebrow">LLC formation</span>
<h1>Form your LLC with an accountant, <em>not a call center.</em></h1>
<p>Any state, one price. Your state filing, EIN, operating agreement and first-year calendar from <strong>$150 plus your state's fee, paid once.</strong> No renewals, and no add-on charges for the basics.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#start">Start my LLC</a><a class="btn btn-line" href="#cost">See my state's total</a></div>
<p class="llc-trust">Big Four trained · Accounting, tax and business solutions · Princeton, NJ, serving clients nationwide</p></div></header>
<main>
<section class="wrap llc-sec" id="packages" aria-labelledby="pk-h"><div class="sec-hd"><span class="eyebrow eb-dark">Packages</span>
<h2 id="pk-h">Three ways to start. One price each.</h2><p>Every package includes the filing, your EIN and an operating agreement template. State fees are added at cost.</p></div>
{packages_html()}{table_html()}</section>
{state_picker()}
{monthly_html()}
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
{cart_js()}
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><h2 id="faq-h">FAQs</h2>{ui_kit.faq_accordion(FAQ, prefix="llc")}</section>
<section class="wrap llc-sec" id="states" aria-labelledby="dir-h"><div class="sec-hd"><span class="eyebrow eb-dark">LLC fees by state</span><h2 id="dir-h">State filing fees, all 50 states and DC.</h2>
<p>The state's own formation fee for a domestic LLC filed online. Open a state for its annual report, tax registration, registered agent rules and official sources.</p></div>
<ul class="st-dir">{directory}</ul>
<p class="disclaimer">State facts checked against each state's official sources as of {CHECKED}. State fees change; we confirm the current fee before invoicing. {esc(LEGAL)} Educational information, not tax or legal advice.</p></section>
</main>{picker_js()}'''
    ld = ld_service(url, "LLC formation in all 50 states", desc)
    return write("llc-formation", page(title, desc, url, body, ld, active="llc"))


def build_state(code):
    s = STATES[code]
    name = s["name"]
    url = f"{BASE}/llc-formation/{code.lower()}/"
    fee = v(s, "filing_fee")
    pub = v(s, "publication")
    rows = [("Formation document", esc(s.get("formation_document", ""))),
            ("Filing office", esc(v(s, "office") or "")),
            ("State filing fee", (f"${fee:,}" + (f" (plus ${v(s, 'formation_extra'):,} also due at formation: {esc((s.get('formation_extra') or {}).get('note', ''))})" if v(s, "formation_extra") else "")) if fee is not None else "Confirmed when we quote; the state fee is added at cost"),
            ("Name reservation (optional)", f"${v(s, 'name_reservation_fee')}" if v(s, "name_reservation_fee") is not None else "—")]
    arf = v(s, "annual_report_fee")
    arnote = pubnote((s.get("annual_report_fee") or {}).get("note", "") if isinstance(s.get("annual_report_fee"), dict) else "")
    freq = v(s, "annual_report_frequency")
    due = v(s, "annual_report_due")
    if isinstance(arf, (int, float)):
        txt = f"${arf:,}" + (f" ({esc(str(freq))})" if freq else "") + (f"; due {esc(lc1(str(due)))}" if due else "")
        rows.append(("Annual report", txt + (f". {esc(arnote)}" if arnote else "")))
    else:
        bi = v(s, "biennial_statement_fee")
        rows.append(("Annual report", esc(arnote or ("None required." if (due and str(due).lower().startswith("none")) else "See the state's official page in the sources below; we confirm current state fees before invoicing.")) + (f" Biennial statement: ${bi}; {esc(lc1(str(due or '')))}." if bi else "")))
    if isinstance(pub, dict) and pub.get("newspapers") and pub.get("certificate_of_publication_fee"):
        rows.append(("Publication", f"Publish once a week for {pub['weeks']} weeks in {pub['newspapers']} newspapers designated by the county clerk, "
                                    f"then file the Certificate of Publication (${pub['certificate_of_publication_fee']}) within {pub['deadline_days']} days of forming."))
    elif pub:
        pn = (s.get("publication") or {}).get("note", "") if isinstance(s.get("publication"), dict) else ""
        rows.append(("Publication", esc(pubnote(pub if isinstance(pub, str) else pn) or "Required. See the state's instructions in the sources below; publication costs are quoted at cost.")))
    sr = [x if isinstance(x, str) else (x.get("value") or "") for x in (s.get("special_rules") or [])]
    if sr:
        sr = [x for x in sr if x and not _INTERNAL.search(x)]
        if sr:
            rows.append(("Also know", "<br>".join(esc(x) for x in sr)))
    if v(s, "state_tax_registration"):
        rows.append(("State tax registration", esc(v(s, "state_tax_registration"))))
    if v(s, "registered_agent"):
        rows.append(("Registered agent", esc(v(s, "registered_agent"))))
    pnote = pubnote((s.get("processing_online") or {}).get("note", ""))
    if pnote:
        rows.append(("Processing time", esc(pnote)))
    tbl = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in rows)
    extra = (pub.get("certificate_of_publication_fee", 0) if isinstance(pub, dict) else 0) or 0
    fx = v(s, "formation_extra") or 0
    news = " + newspapers" if (isinstance(pub, dict) and pub.get("newspapers")) else (" + publication" if pub else "")
    fee_s = (f"${fee + fx:,}" if isinstance(fee, (int, float)) else "Confirmed at quote")
    tot = "".join(f'<tr><td>{esc(p["name"])}</td><td>${p["price"]}</td><td>{fee_s}</td><td><strong>${p["price"] + (fee or 0) + fx + extra:,}{news}{" + state fee" if fee is None else ""}</strong></td></tr>' for p in PACKAGES)
    srcs = sorted({u["source_url"] for u in s.values() if isinstance(u, dict) and u.get("source_url")})
    src_html = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u.replace("https://", ""))}</a></li>' for u in srcs)
    title = f"How Much Does an LLC Cost in {name}? | MFA"
    desc = next(c for c in (f"{name} LLC filing fee {fee_s}, annual report, tax registration and agent rules, checked {CHECKED}. MFA forms it from $150 plus the state fee.",
                            f"{name} LLC filing fee {fee_s}, annual report and tax registration rules. MFA forms it from $150 plus the state fee.",
                            f"{name} LLC fees and rules. MFA forms it from $150 plus the state fee.") if len(c) <= 155)
    body = f'''<header class="ahead"><div class="wrap">
<div class="crumbs"><a href="/">Home</a> / <a href="/llc-formation/">LLC formation</a> / {esc(name)}</div>
<span class="eyebrow">{esc(name)} LLC</span><h1>Forming an LLC in {esc(name)}: fees, rules and timing</h1>
<p class="dek">The state's own numbers, checked {d(s["filing_fee"]["checked"]) if isinstance(s.get("filing_fee"), dict) and s["filing_fee"].get("checked") else CHECKED}, and what your first-year total looks like with MFA.</p></div></header>
<main><div class="tinfo"><article class="article">
<h2>{esc(name)} LLC at a glance</h2><table class="tbl"><tbody>{tbl}</tbody></table>
<h2>Your total with MFA</h2><div class="tbl-wrap tw-s"><table class="tbl"><thead><tr><th>Package</th><th>MFA fee</th><th>State fee</th><th>Due at formation</th></tr></thead><tbody>{tot}</tbody></table></div>
<p>MFA fees are one-time and never renew. {"Publication costs vary and are quoted at cost. " if pub else ""}See <a href="/llc-formation/#packages">what each package includes</a>, or add <a href="/llc-formation/#monthly">monthly bookkeeping from $199/month</a>.</p>
<p><a class="btn btn-ink" href="/llc-formation/?state={code}#start">Start my {esc(name)} LLC</a></p>
<section class="sources"><h2>Sources</h2><ul>{src_html}</ul>
<p class="disclaimer">Facts checked against the official sources above as of {CHECKED}. State fees change; we confirm the current fee before invoicing. {esc(LEGAL)} Educational information, not tax or legal advice.</p></section>
</article></div></main>'''
    ld = seo.graph(url, f"LLC formation in {name}", desc, seo.llc_service(url, name), kind="WebPage",
                   crumb=[("Home", BASE + "/"), ("LLC formation", BASE + "/llc-formation/"), (name, url)], extra={"mainEntity": {"@id": url + "#service"}})
    return write(f"llc-formation/{code.lower()}", page(title, desc, url, body, ld, active="llc"))


def write_pricing():
    """Server-side price list for functions/api/llc-checkout.js (the browser's numbers are never trusted)."""
    data = pricing_obj()
    out = ROOT / "functions" / "_shared" / "llc-pricing.js"
    out.write_text("// Generated by tools/build_llc.py from data/llc-states.json and PACKAGES. Do not edit by hand.\nexport default "
                   + json.dumps(data, indent=1) + ";\n", encoding="utf-8")


def build_thanks():
    url = BASE + "/llc-formation/thanks/"
    body = f'''<header class="ahead"><div class="wrap"><div class="crumbs"><a href="/">Home</a> / <a href="/llc-formation/">LLC formation</a> / Order</div>
<span class="eyebrow">LLC formation</span><h1 id="t-h">Checking your payment…</h1><p class="dek" id="t-dek">One moment.</p></div></header>
<main><div class="tinfo"><article class="article" id="t-body" aria-live="polite"></article></div></main>
<script>
(function(){{var id=new URLSearchParams(location.search).get('session_id'),b=document.getElementById('t-body'),h=document.getElementById('t-h'),dk=document.getElementById('t-dek');
var esc=function(t){{return String(t==null?'':t).replace(/[&<>"]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];}});}};
function fail(msg){{h.textContent='We couldn\u2019t confirm your payment';dk.textContent=msg;b.innerHTML='<p>If you completed checkout, you\u2019ll get a Stripe receipt by email and we\u2019ll be in touch. Otherwise, <a href="/llc-formation/#start">return to the form</a> or contact <a href="mailto:{B.EMAIL}">{B.EMAIL}</a>, (347) 205-4468.</p>';}}
if(!id)return fail('No order reference was found.');
fetch('/api/llc-session?session_id='+encodeURIComponent(id)).then(function(r){{return r.json();}}).then(function(s){{
if(!s||!s.paid)return fail(s&&s.status==='open'?'Checkout wasn\u2019t finished.':'Payment is not complete.');
h.textContent='Thank you. Your LLC order is in.';dk.textContent='Paid $'+Number(s.amount).toLocaleString('en-US',{{minimumFractionDigits:2}})+'. A receipt is on its way to '+(s.email||'your email')+'.';
b.innerHTML='<h2>What happens next</h2><ol><li>We check that <strong>'+esc(s.llc_name)+'</strong> is available in '+esc(s.state)+' (usually within one to three business days). If it isn\u2019t, we\u2019ll contact you about your backup name.</li><li>We file with the state and apply for your EIN.</li><li>You get your document pack by email: filed certificate, EIN letter, operating agreement and first-year calendar.</li></ol>'
+(s.state_fee_confirmed&&s.state_fee_confirmed.indexOf('no')===0?'<p>Your state\u2019s filing fee wasn\u2019t included at checkout. We\u2019ll confirm it and collect it at cost before filing.</p>':'')
+(s.subscription?'<p>Monthly bookkeeping: your first monthly charge is 30 days from today. You can cancel anytime by emailing us.</p>':'')+(s.monthly_bookkeeping==='quote'?'<p>Monthly bookkeeping: we\u2019ll send you a quote after reviewing your accounts. Nothing was charged for it today.</p>':'')+'<p>Questions: <a href="mailto:{B.EMAIL}">{B.EMAIL}</a> or (347) 205-4468.</p>';
try{{if(!sessionStorage.getItem('llc-paid-'+id)){{sessionStorage.setItem('llc-paid-'+id,'1');var d=new FormData();d.append('_subject','PAID LLC order: '+s.package+' / '+s.state+' / '+s.llc_name+' ($'+s.amount+')');
d.append('name',s.name||'');d.append('email',s.email||'');d.append('amount_paid','$'+s.amount);d.append('package',s.package);d.append('state',s.state);d.append('llc_name',s.llc_name);d.append('activity',s.activity||'');
d.append('monthly_bookkeeping',s.monthly_bookkeeping||'');d.append('addons',s.addons||'');d.append('state_fee_confirmed',s.state_fee_confirmed||'');d.append('stripe_session',id);d.append('_captcha','false');d.append('_template','table');
fetch('{FORM_ENDPOINT}',{{method:'POST',headers:{{'Accept':'application/json'}},body:d}}).catch(function(){{}});}}}}catch(e){{}}
if(window.gtag)gtag('event','purchase',{{transaction_id:id,value:s.amount,currency:'USD',items:[{{item_name:'LLC formation '+s.package}}]}});
}}).catch(function(){{fail('We couldn\u2019t reach the payment service.');}});}})();
</script>'''
    html = page("LLC Order Confirmation | MFA", "Your LLC formation order with Merchant Financial Advisory.", url, body, None, active="llc")
    html = html.replace('<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"/>', '<meta name="robots" content="noindex"/>', 1)
    write("llc-formation/thanks", html)


def build_all():
    write_pricing()
    build_thanks()
    return [build_main()] + [build_state(c) for c in ORDER]


if __name__ == "__main__":
    print("\n".join(build_all()))
