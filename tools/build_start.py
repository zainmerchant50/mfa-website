#!/usr/bin/env python3
"""Builds /start/ (Site + Growth): the 2026 Small Business Tax Starter Kit page, the ONE place every product, book and pin
leads back to (Zain 2026-10-23 12:58 ET). People get the kit for their email; a 5-email MailerLite automation follows and
ends in booking a consult.

Email capture: MailerLite (account 2707043), group "Starter Kit 2026" (202139152397895078), embedded form
"Starter Kit 2026 – /start signup" (202139155569837874), double opt-in ON, posted to MailerLite's form endpoint the same way
as the newsletter form in build_blog.py. The kit PDF itself (site/start/kit/, noindex in site/_headers) is only linked from
email #1 of the automation, never from this page. Kit content: tools/build_start_kit.py.

Links in from Etsy, Gumroad, KDP and Pinterest use ?utm_source=<platform>&utm_medium=<product|book|pin>&utm_campaign=<slug>.
Never "free", never "CPA firm", no street address. Run via tools/build_resources.py (it calls build()).
"""
import re

import build_blog as B
import seo
import ui_kit
from build_book import TOPICS_JS, CSS as BOOK_CSS   # pills (.bk-topics) share /book/'s styles
from build_resources import page, write, esc, BASE, cta, svg

ML_ENDPOINT = "https://assets.mailerlite.com/jsonp/2707043/forms/202139155569837874/subscribe"
CHECKED = "October 20, 2026"
CRED = ["CPA candidate", "ACCA", "Big Four (ex-PwC)", "PTIN/EFIN tax preparer"]   # line approved for this page (Hub brief 2026-10-23)

INSIDE = [
    ("cal", "Page 2", "Key tax dates for 2026 returns", "Every federal date from the January estimate to October extensions, with New Jersey and New York notes."),
    ("calc", "Page 3", "Quarterly estimates in one page", "Who has to pay, the safe harbors that keep you clear of penalties, and a payment tracker."),
    ("list", "Page 4", "Deduction checklist", "Twenty write-offs owners miss, with the 2026 limits, and the common traps that don't count."),
    ("check", "Page 5", "1099 readiness checklist", "The new $2,000 threshold, the W-9 steps and every early-2027 filing deadline."),
    ("doc", "Page 6", "Monthly bookkeeping close", "Ten steps, one day a month, so tax season takes days instead of weeks."),
    ("scale", "Page 7", "LLC vs S corp, in one page", "When an S corp election is worth a look, with a worked example at 2026 rates."),
]
FOR = ["Freelancers and 1099 contractors", "Single-member LLCs", "New business owners", "Side businesses",
       "Etsy and online sellers", "Owners weighing an S corp", "New Jersey and New York businesses"]
FAQ = [
    ("What's in the kit?", "An 8-page PDF: key tax dates for 2026 returns, quarterly estimated taxes, a deduction checklist, a 1099 readiness checklist, a 10-step monthly bookkeeping close, and LLC vs S corp in one page."),
    ("How do I get it?", "Enter your email above, then confirm your address from the short email we send. The kit arrives in your inbox right after you confirm."),
    ("What else will you email me?", "Four short emails over the next 10 days: the deductions owners miss most, quarterly estimate and 1099 deadlines, how monthly bookkeeping pays off at tax time, and an invitation to book a consult. You can unsubscribe from any email in one click."),
    ("Is it up to date for 2026?", f"Yes. Every figure is for the 2026 tax year and was checked against IRS and state sources as of {CHECKED}. When a rule changes, we update the kit."),
    ("Does it cover New Jersey and New York?", "The kit is mostly federal, so it works in any state. It adds the New Jersey and New York estimated tax thresholds and return dates."),
    ("Is this tax advice?", "No. It's general information to help you get organized, and it doesn't create a client relationship. For advice on your own situation, book a consultation."),
    ("Can MFA do this for me instead?", "Yes. We prepare business tax returns, keep monthly books from $199 a month, and form LLCs from $150 plus the state fee. Book a 30-minute consult and we'll tell you what we'd fix first."),
]

CSS = """<style>
.st-hero .llc-trust span{white-space:nowrap}
.st-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
@media (max-width:960px){.st-grid{grid-template-columns:1fr 1fr}}@media (max-width:600px){.st-grid{grid-template-columns:1fr}}
.st-grid .rcard{transition:transform .5s var(--ui-ease),box-shadow .5s var(--ui-ease),border-color .3s}
.st-grid .rcard:hover{transform:translateY(-4px);box-shadow:0 18px 40px rgba(16,35,63,.1);border-color:rgba(176,141,63,.45)}
.st-pg{position:absolute;top:22px;right:22px;font-size:9.5px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--gold)}
.st-cred{display:flex;flex-wrap:wrap;align-items:center;gap:22px 28px;background:#fff;border:1px solid var(--hair);border-radius:18px;padding:26px 30px}
.st-av{width:64px;height:64px;border-radius:50%;background:var(--navy);color:var(--gold-b);display:grid;place-items:center;font-family:'Cormorant Garamond',serif;font-size:1.6rem;flex-shrink:0}
.st-who{flex:1;min-width:240px}
.st-who b{display:block;font-family:'Cormorant Garamond',serif;font-weight:500;font-size:1.5rem;color:var(--navy);line-height:1.15}
.st-who p{margin:4px 0 0;font-size:.92rem;line-height:1.6;color:var(--muted)}
.st-pills{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.st-pills li{border:1px solid var(--gold);border-radius:999px;padding:6px 14px;font-size:.86rem;font-weight:500;color:var(--navy)}
.st-check{flex-basis:100%;display:flex;gap:10px;align-items:center;padding-top:16px;border-top:1px solid var(--hair);font-size:.86rem;color:var(--muted)}
.st-check svg{width:18px;height:18px;color:var(--gold);flex-shrink:0}
.st-get{scroll-margin-top:96px}
.st-box{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);border-radius:20px;overflow:hidden;border:1px solid var(--hair);background:#fff;box-shadow:0 18px 50px rgba(16,35,63,.08)}
@media (max-width:860px){.st-box{grid-template-columns:1fr}}
.st-side{position:relative;overflow:hidden;background:var(--navy);color:#fff;padding:40px 36px;display:flex;flex-direction:column;align-items:center;gap:26px}
.st-side::after{content:"";position:absolute;left:-120px;bottom:-140px;width:340px;height:340px;border-radius:50%;border:1px solid rgba(216,183,105,.22)}
.st-cover{width:min(240px,64%);height:auto;border-radius:8px;outline:1px solid rgba(216,183,105,.45);outline-offset:-1px;box-shadow:0 26px 50px rgba(0,0,0,.4);transform:rotate(-3deg);animation:stFloat 7s ease-in-out infinite}
@keyframes stFloat{0%,100%{transform:rotate(-3deg) translateY(0)}50%{transform:rotate(-1.5deg) translateY(-8px)}}
.st-side ul{list-style:none;padding:0;margin:0;display:grid;gap:10px;font-size:.92rem;line-height:1.5;color:rgba(255,255,255,.82);position:relative;z-index:1;align-self:stretch}
.st-side li{display:flex;gap:10px}.st-side li svg{width:17px;height:17px;flex-shrink:0;margin-top:2px;color:var(--gold-b)}
.st-form{padding:40px 38px;display:flex;flex-direction:column;justify-content:center}
.st-form .eyebrow{color:var(--gold)}
.st-form h3{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:2rem;line-height:1.1;color:var(--navy);margin:8px 0 6px}
.st-form>p{color:var(--muted);font-size:.95rem;line-height:1.65;margin:0 0 18px}
.st-f{display:grid;gap:14px}
.st-f label{display:grid;gap:6px;font-size:.78rem;font-weight:600;letter-spacing:.02em;color:var(--navy)}
.st-f input{font:inherit;font-size:1rem;padding:13px 14px;border:1px solid rgba(21,21,21,.18);border-radius:10px;background:#fff;color:var(--ink);width:100%;outline:none;transition:border-color .3s,box-shadow .3s}
.st-f input:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(176,141,63,.15)}
.st-f .btn{justify-self:start;cursor:pointer;border:0;padding:16px 30px}
.st-f .btn[disabled]{opacity:.7;cursor:wait}
.st-fine{font-size:.8rem;line-height:1.6;color:var(--muted);margin:0}.st-fine a{color:var(--navy);border-bottom:1px solid var(--gold)}
.st-st{font-size:.88rem;color:#B42318;margin:0;min-height:1px}
.st-done[hidden]{display:none}
.st-done{display:flex;gap:16px;align-items:flex-start;padding:22px;border-radius:14px;background:var(--paper-2);border:1px solid rgba(176,141,63,.4);animation:uiUp .7s var(--ui-ease) both}
.st-done svg{width:34px;height:34px;color:var(--gold);flex-shrink:0}
.st-done b{display:block;font-family:'Cormorant Garamond',serif;font-weight:500;font-size:1.5rem;color:var(--navy);margin-bottom:4px}
.st-done p{margin:0;font-size:.94rem;line-height:1.6;color:var(--muted)}.st-done a{color:var(--navy);border-bottom:1px solid var(--gold)}
@media (max-width:560px){.st-form,.st-side{padding:28px 22px}.st-f .btn{justify-self:stretch;justify-content:center}.st-cred{padding:22px 20px}}
@media (prefers-reduced-motion:reduce){.st-cover{animation:none}}
</style>"""

FORM_JS = """<script>
(function(){var f=document.getElementById('st-f');if(!f)return;var st=f.querySelector('.st-st'),ok=document.getElementById('st-done');
function done(){f.hidden=true;ok.hidden=false;try{if(window.mfaLead)window.mfaLead('starter_kit',{kit:'2026'});}catch(e){}}
f.addEventListener('submit',function(e){e.preventDefault();if(f._honey.value)return;if(!f.checkValidity()){f.reportValidity();return;}
var b=f.querySelector('button'),l=b.textContent;b.disabled=true;b.textContent='Sending\\u2026';st.textContent='';
function fail(){st.textContent='Couldn\\u2019t send. Please email %(email)s with the word KIT and we\\u2019ll send it.';b.disabled=false;b.textContent=l;}
var m=new URLSearchParams();m.append('fields[email]',f.email.value.trim());if(f.name.value)m.append('fields[name]',f.name.value.trim());
m.append('ml-submit','1');m.append('anticsrf','true');
fetch('%(ml)s',{method:'POST',headers:{'Accept':'application/json'},body:m}).then(function(r){return r.json();})
.then(function(j){if(j&&j.success===false)throw 0;done();})
.catch(function(){fetch('%(ml)s',{method:'POST',mode:'no-cors',body:m}).then(done).catch(fail);});});})();
</script>""" % {"ml": ML_ENDPOINT, "email": B.EMAIL}

TICK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="4.5" width="19" height="15" rx="2"/><path d="m21.5 7-9.5 6.5L2.5 7"/></svg>'
SHIELD = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 4.5 6v6c0 4.5 3.2 7.8 7.5 9 4.3-1.2 7.5-4.5 7.5-9V6z"/><path d="m8.8 12 2.2 2.2 4.3-4.4"/></svg>'


def build():
    url = BASE + "/start/"
    title = "2026 Small Business Tax Starter Kit | MFA"
    desc = ("Get the 2026 Small Business Tax Starter Kit by email: key tax dates, quarterly estimates, deduction and 1099 "
            "checklists, and LLC vs S corp basics.")
    cards = "".join(f'<div class="rcard card"><span class="st-pg">{esc(pg)}</span><span class="ri">{svg(ic)}</span>'
                    f'<h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for ic, pg, t, d in INSIDE)
    pills = "".join(f"<li>{esc(t)}</li>" for t in FOR)
    cred = "".join(f"<li>{esc(c)}</li>" for c in CRED)
    side = "".join(f"<li>{TICK}<span>{esc(t)}</span></li>" for t in
                   ["Eight pages, ready to print or fill in on screen", "Every figure dated for 2026 and checked against IRS sources",
                    "Federal rules, with New Jersey and New York notes"])
    faq = ui_kit.faq_accordion([(esc(q), esc(a)) for q, a in FAQ], prefix="st")
    body = f'''{BOOK_CSS}{CSS}<header class="bhero rhero st-hero"><div class="wrap"><span class="eyebrow">2026 Tax Starter Kit</span>
<h1>Your 2026 business taxes, <em>organized from the start.</em></h1>
<p>The dates, checklists and one-page answers we walk new clients through first, in one 8-page kit. Tell us where to send it and it's in your inbox in a minute.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#get">Send me the kit</a><a class="btn btn-line" href="/book/" data-conv="book">Book a consult</a></div>
<p class="llc-trust"><span>8-page PDF</span> · <span>Dated for 2026</span> · <span>By Zain Merchant, ACCA</span></p></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="in-h"><div class="sec-hd"><span class="eyebrow eb-dark">What's inside</span><h2 id="in-h">Six one-page tools for the year ahead</h2>
<p>Each page answers one question owners ask us every season. The last page shows how to hand any of it off.</p></div>
<div class="st-grid">{cards}</div></section>
<section class="wrap llc-sec" aria-labelledby="for-h"><div class="sec-hd"><span class="eyebrow eb-dark">Who it's for</span><h2 id="for-h">Built for owners who do their own books, or want to</h2>
<p>If you're self-employed, run a small LLC or sell online, and you'd rather not find out about a deadline from a penalty notice, this is for you.</p></div>
<ul class="bk-topics" id="bk-topics">{pills}</ul></section>
<section class="wrap llc-sec" aria-labelledby="cred-h"><div class="sec-hd"><span class="eyebrow eb-dark">Who wrote it</span><h2 id="cred-h">From an accountant, not a content mill</h2></div>
<div class="st-cred card"><div class="st-av" aria-hidden="true">ZM</div><div class="st-who"><b>Zain Merchant</b><p>Founder of Merchant Financial Advisory in Princeton, NJ, with about seven years in accounting and audit.</p></div>
<ul class="st-pills" aria-label="Credentials">{cred}</ul>
<p class="st-check">{SHIELD}<span>Every figure in the kit is for 2026 and was checked against IRS and state sources as of {CHECKED}. Sources are listed on the last page.</span></p></div></section>
<section class="wrap llc-sec st-get" id="get" aria-labelledby="get-h"><div class="sec-hd"><span class="eyebrow eb-dark">Get the kit</span><h2 id="get-h">Where should we send it?</h2></div>
<div class="st-box book-frame"><div class="st-side"><img class="st-cover" src="/start/kit-cover.webp" alt="Cover of the 2026 Small Business Tax Starter Kit by Merchant Financial Advisory" width="560" height="724"/><ul>{side}</ul></div>
<div class="st-form"><span class="eyebrow">Yours when you join</span><h3>Send me the kit</h3>
<p>Add your email and confirm it from the short message we send. The kit link arrives right after.</p>
<form class="st-f" id="st-f" novalidate>
<label>First name<input name="name" autocomplete="given-name"/></label>
<label>Email<input name="email" type="email" autocomplete="email" required/></label>
<input class="ask-hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true"/>
<button class="btn btn-gold" type="submit">Send me the kit</button>
<p class="st-fine">You'll also get four short emails over the next 10 days with tips and an invitation to book a consult. Unsubscribe from any email in one click. We never sell or share your address. <a href="/privacy.html">Privacy Policy</a>.</p>
<p class="st-st" role="status" aria-live="polite"></p></form>
<div class="st-done" id="st-done" hidden>{MAIL}<div><b>Check your inbox</b><p>Click the confirmation link in the email from Merchant Financial Advisory and your kit arrives right after. Not there in a minute? Look in Promotions or Spam. Meanwhile, you can <a href="/book/" data-conv="book">book a 30-minute consult</a>.</p></div></div>
</div></div></section>
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">About the kit</h2></div>{faq}</section>
{cta("Rather talk it through?", "Book a 30-minute consultation about your taxes, bookkeeping or LLC. We'll tell you what we'd fix first, with the price agreed before any work starts.")}
<section class="wrap llc-sec"><p class="disclaimer">The kit is general information for the 2026 tax year, not tax, legal or accounting advice, and requesting it doesn't create a client relationship. Merchant Financial Advisory is not affiliated with the IRS.</p></section>
</main>
{TOPICS_JS}{FORM_JS}'''
    ld = seo.graph(url, "2026 Small Business Tax Starter Kit", desc,
                   {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
                       {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
                   crumb=[("Home", BASE + "/"), ("2026 Tax Starter Kit", url)])
    html = page(title, desc, url, body, ld, active="res")
    low = ui_kit._plain(html).lower()
    assert not re.search(r"\bfree\b|\bcpa firm\b", low), "banned wording on /start/"
    return write("start", html)


if __name__ == "__main__":
    print(build())
