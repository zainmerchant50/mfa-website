#!/usr/bin/env python3
"""Builds /bookkeeping-cleanup/ (Site session): a QUOTED service, never a flat rate.

Zain 2026-10-21: "it should be sold as service but can't do a flat rate". So the page shows no prices:
the visitor sends a short quote request, we look at a sample of their accounts and give a fixed quote
before any work starts. No payment on this page.

The form copies the LLC intake form (tools/build_llc.py intake_form): FormSubmit AJAX to info@mfa-advisory.com,
honeypot field _honey, inline validation with an error summary, a mailto fallback if the send fails, a thank-you panel
on success, and the Google Ads lead-form conversion (label rNQJCK2_kJsdEK3zpPhE) only after FormSubmit confirms.
Never "free", never "CPA", no street address, no assurance wording. Customer-facing dates: date only.
Run via tools/build_resources.py (it calls build()).
"""
import json

import build_blog as B
from build_resources import page, write, esc, BASE, cta

ENDPOINT = "https://formsubmit.co/ajax/" + B.EMAIL
CONV = B.ADS["id"] + "/rNQJCK2_kJsdEK3zpPhE"
ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.2 4.2L19 7"/></svg>'

COVERS = [
    ("Catch-up categorization", "Every transaction since the point you fell behind sorted to a chart of accounts that fits your business."),
    ("Bank and card reconciliations", "Each bank and credit card account reconciled to its statements, month by month, with differences explained."),
    ("Payables and receivables tidy-up", "Unpaid bills and open invoices matched to payments, duplicates and stale items cleared out."),
    ("Opening balances", "Starting balances set correctly, so the books agree with where the accounts stand today."),
    ("A short written summary", "A plain-English note of what we found and fixed, and what to do differently going forward."),
]
STEPS = [
    ("Send the form", "Tell us about your books: how far behind, what software, how many accounts. It takes about three minutes."),
    ("We look at a sample", "We review a sample of your accounts and give you a fixed quote before any work starts."),
    ("You decide", "If the quote works, we begin. If not, you owe nothing."),
]
SOFTWARE = ["QuickBooks Online", "QuickBooks Desktop", "Xero", "Wave", "FreshBooks", "Spreadsheets only", "No system yet", "Other"]
MONTHS = ["1 to 3 months", "4 to 6 months", "7 to 12 months", "13 to 24 months", "More than 24 months"]
ACCOUNTS = ["1 to 2", "3 to 4", "5 to 8", "9 or more"]
TXNS = ["Up to 100", "101 to 300", "301 to 600", "601 to 1,000", "More than 1,000"]

CSS = """<style>
.cu-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-top:6px}
.cu-list .card{padding:20px 22px}.cu-list h3{font-size:1.1rem;margin:0 0 6px}.cu-list p{margin:0;font-size:.92rem;line-height:1.55}
.cu-ok{display:flex;gap:8px;align-items:flex-start}.cu-ok svg{width:18px;height:18px;flex-shrink:0;margin-top:3px;color:var(--gold)}
.cu-note{max-width:980px;margin:14px 0 0;font-size:.85rem;color:var(--muted)}
</style>"""

JS = r"""(function(){var f=document.getElementById('cform'),st=f.querySelector('.ask-st'),box=document.getElementById('form-err');
var EM=/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;
var RULES=[['c-name','Please enter your name.',function(v){return v.length>1;}],
['c-email','Please enter a valid email address, like name@example.com.',function(v){return EM.test(v);}],
['c-type','Please tell us what kind of business it is.',function(v){return v.length>1;}],
['c-soft','Please choose your accounting software.',function(v){return !!v;}],
['c-months','Please choose how many months behind you are.',function(v){return !!v;}],
['c-accts','Please choose how many bank and card accounts you have.',function(v){return !!v;}],
['c-txns','Please choose roughly how many transactions you have each month.',function(v){return !!v;}]];
function mark(id,msg){var el=document.getElementById(id),w=document.getElementById('w-'+id),e=document.getElementById('e-'+id);
if(msg){w.classList.add('has-err');el.setAttribute('aria-invalid','true');el.setAttribute('aria-describedby','e-'+id);e.textContent=msg;}
else{w.classList.remove('has-err');el.removeAttribute('aria-invalid');e.textContent='';}}
function check(id){for(var i=0;i<RULES.length;i++)if(RULES[i][0]===id){var v=document.getElementById(id).value.trim(),ok=RULES[i][2](v);mark(id,ok?'':RULES[i][1]);return ok;}return true;}
RULES.forEach(function(r){var el=document.getElementById(r[0]);
el.addEventListener('blur',function(){if(el.value.trim()||el.getAttribute('aria-invalid'))check(r[0]);});
el.addEventListener('input',function(){if(el.getAttribute('aria-invalid'))check(r[0]);});
el.addEventListener('change',function(){if(el.getAttribute('aria-invalid'))check(r[0]);});});
function showErr(html){box.innerHTML=html;box.hidden=false;box.focus();box.scrollIntoView({block:'center',behavior:'smooth'});}
f.addEventListener('submit',function(e){e.preventDefault();if(f._honey.value)return;st.textContent='';
var bad=RULES.filter(function(r){return !check(r[0]);});
if(bad.length){showErr('<strong>Please fix '+(bad.length===1?'1 field':bad.length+' fields')+':</strong><ul>'+bad.map(function(r){return '<li><a href="#'+r[0]+'">'+r[1]+'</a></li>';}).join('')+'</ul>');
[].slice.call(box.querySelectorAll('a')).forEach(function(a){a.addEventListener('click',function(ev){ev.preventDefault();var t=document.getElementById(a.getAttribute('href').slice(1));t.focus();t.scrollIntoView({block:'center'});});});return;}
box.hidden=true;var b=document.getElementById('csubmit'),l=b.textContent;b.disabled=true;b.textContent='Sending…';
f.email.value=f.email.value.trim();var d=new FormData(f);d.append('page',location.href);d.append('_replyto',f.email.value);
d.append('_subject','Bookkeeping cleanup quote request: '+f.name.value.trim()+' / '+f.months_behind.value);d.append('_captcha','false');d.append('_template','table');
fetch('__ENDPOINT__',{method:'POST',headers:{'Accept':'application/json'},body:d}).then(function(r){return r.json().catch(function(){return {success:r.ok};});})
.then(function(j){if(!j||j.success===false||j.success==='false')throw new Error((j&&j.message)||'Send failed');
if(window.gtag){gtag('event','conversion',{send_to:'__CONV__'});gtag('event','generate_lead',{form:'bookkeeping_cleanup',months_behind:f.months_behind.value});}
f.hidden=true;var dn=document.getElementById('cdone');dn.hidden=false;dn.focus();dn.scrollIntoView({block:'center'});})
.catch(function(err){var body=encodeURIComponent('Name: '+f.name.value+'\nEmail: '+f.email.value+'\nPhone: '+f.phone.value+'\nBusiness type: '+f.business_type.value+'\nSoftware: '+f.accounting_software.value+'\nMonths behind: '+f.months_behind.value+'\nBank + card accounts: '+f.accounts.value+'\nTransactions a month: '+f.transactions_per_month.value+'\nPayroll: '+f.payroll.value+'\nSales tax: '+f.sales_tax.value+'\nNotes: '+f.notes.value);
showErr('<strong>We couldn’t send your request just now.</strong> Please <a href="mailto:__EMAIL__?subject='+encodeURIComponent('Bookkeeping cleanup quote request')+'&body='+body+'">email your details to __EMAIL__</a> (we’ve filled in the email for you) or call (347) 205-4468.');
b.disabled=false;b.textContent=l;if(window.console)console.warn('Cleanup form:',err&&err.message);});});
})();"""


def form_html():
    R = '<span class="req" aria-hidden="true">*</span>'
    req = ' required aria-required="true"'

    def fld(fid, label, ctrl, required=False, hint=""):
        return (f'<div class="fld" id="w-{fid}"><label for="{fid}">{label}{R if required else ""}</label>{ctrl}'
                f'{f"<span class=hint>{hint}</span>" if hint else ""}<span class="err-msg" id="e-{fid}" role="alert"></span></div>')

    def sel(fid, name, opts, required=False, ph="Choose one"):
        o = f'<option value="">{ph}</option>' + "".join(f'<option value="{esc(x)}">{esc(x)}</option>' for x in opts)
        return f'<select id="{fid}" name="{name}"{req if required else ""}>{o}</select>'

    yn = ["Yes", "No", "Not sure"]
    return f'''<section class="wrap llc-sec" id="quote" aria-labelledby="quote-h">
<div class="sec-hd"><span class="eyebrow eb-dark">Request a quote</span><h2 id="quote-h">Tell us about your books.</h2>
<p>This is a quote request, not an order. Nothing is charged, and you'll get a fixed quote from us by email before any work starts.</p></div>
<form class="tcard lform" id="cform" novalidate>
<p class="req-note"><span class="req">*</span> Required</p>
<div class="form-err" id="form-err" role="alert" tabindex="-1" hidden></div>
<div class="lgrid">
{fld("c-name", "Your name", f'<input type="text" id="c-name" name="name" autocomplete="name"{req}/>', True)}
{fld("c-email", "Email", f'<input type="email" id="c-email" name="email" autocomplete="email" inputmode="email" autocapitalize="off" spellcheck="false"{req}/>', True)}
{fld("c-phone", "Phone (optional)", '<input type="tel" id="c-phone" name="phone" autocomplete="tel" inputmode="tel"/>')}
{fld("c-type", "Business type", f'<input type="text" id="c-type" name="business_type"{req} placeholder="e.g. restaurant, consultant, online store"/>', True)}
{fld("c-soft", "Accounting software", sel("c-soft", "accounting_software", SOFTWARE, True), True)}
{fld("c-months", "How far behind are the books?", sel("c-months", "months_behind", MONTHS, True), True)}
{fld("c-accts", "Bank and credit card accounts", sel("c-accts", "accounts", ACCOUNTS, True), True, "Count every bank account and card the business uses.")}
{fld("c-txns", "Transactions a month (about)", sel("c-txns", "transactions_per_month", TXNS, True), True, "Across all accounts. A rough guess is fine.")}
{fld("c-pay", "Do you run payroll?", sel("c-pay", "payroll", yn, False, "Choose one (optional)"))}
{fld("c-tax", "Do you collect sales tax?", sel("c-tax", "sales_tax", yn, False, "Choose one (optional)"))}
</div>
{fld("c-notes", "Anything else? (optional)", '<textarea id="c-notes" name="notes" rows="4" placeholder="What happened, what you need the books for (tax return, lender, a sale), any deadline"></textarea>', False, "Please don't include Social Security or bank account numbers. We'll ask for access securely after you accept a quote.")}
<input class="ask-hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
<div class="lsubmit"><button class="btn btn-ink" type="submit" id="csubmit">Request my quote</button><p class="ask-st" role="status" aria-live="polite"></p></div>
<p class="pay-note">No payment on this page. We reply by email, usually within one business day.</p>
</form>
<div class="tcard ldone" id="cdone" tabindex="-1" hidden><h2>Thanks, we have your request.</h2><p>We'll look over what you sent and email you next steps, usually within one business day. You'll get a fixed quote before any work starts. Questions in the meantime: <a href="mailto:{B.EMAIL}">{B.EMAIL}</a> or (347) 205-4468.</p></div>
</section>
<script>{JS.replace("__ENDPOINT__", ENDPOINT).replace("__CONV__", CONV).replace("__EMAIL__", B.EMAIL)}</script>'''


def build():
    url = BASE + "/bookkeeping-cleanup/"
    title = "Bookkeeping Cleanup and Catch-Up: Get a Fixed Quote | MFA"
    desc = ("Books months behind? Catch-up categorization, bank and card reconciliations, payables and receivables tidy-up "
            "and opening balances, with a written summary. Send a few details and get a fixed quote before any work starts.")
    cov = "".join(f'<div class="card"><h3 class="cu-ok">{ICO}<span>{esc(a)}</span></h3><p>{esc(b)}</p></div>' for a, b in COVERS)
    steps = "".join(f'<div class="st3 card"><span class="st3-n">{i}</span><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for i, (a, b) in enumerate(STEPS, 1))
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Bookkeeping cleanup</span>
<h1>Behind on your books? <em>We'll get you caught up.</em></h1>
<p>Cleanup depends on how many months, accounts and transactions are involved, so we don't guess at a flat rate. Send a few details, and we'll give you a fixed quote before any work starts.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#quote">Request a quote</a><a class="btn btn-line" href="/services/#bookkeeping">All bookkeeping services</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="cov-h"><div class="sec-hd"><span class="eyebrow eb-dark">What cleanup covers</span><h2 id="cov-h">From a pile of transactions to books you can use.</h2></div>
<div class="cu-list">{cov}</div>
<p class="cu-note">Once the books are current, monthly bookkeeping keeps them that way. <a href="/llc-formation/#monthly">See how monthly bookkeeping works</a>.</p></section>
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How quoting works</span><h2 id="how-h">A fixed quote first. Work only after you say yes.</h2>
<p>We review a sample of your accounts and give you a fixed quote before any work starts. The quote is the price; it doesn't grow as we go.</p></div>
<div class="st3s">{steps}</div></section>
{form_html()}
{cta("Prefer to talk it through?", "Book a 30-minute call and tell us where the books stand. We'll suggest the smallest cleanup that gets you current.")}
<section class="wrap llc-sec"><p class="disclaimer">Bookkeeping cleanup is bookkeeping work prepared for your own use. It is general accounting support, not tax or legal advice, and sending this form doesn't create a client relationship until you accept a written quote.</p></section>
</main>'''
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Service", "name": "Bookkeeping cleanup and catch-up", "url": url, "serviceType": "Bookkeeping",
         "description": desc, "provider": {"@type": "AccountingService", "name": "Merchant Financial Advisory LLC", "url": BASE},
         "areaServed": ["New Jersey", "New York", "United States"]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Services", "item": BASE + "/services/"},
            {"@type": "ListItem", "position": 3, "name": "Bookkeeping cleanup", "item": url}]}]}
    return write("bookkeeping-cleanup", page(title, desc, url, body, ld, active="s"))


if __name__ == "__main__":
    print(build())
