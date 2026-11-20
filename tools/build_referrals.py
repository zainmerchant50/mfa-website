#!/usr/bin/env python3
"""Builds /referrals/ (Hub): client referral program, sent directly to clients (noindex, not in the menu or sitemap).

Zain 2026-11-19 21:27: "create a referral page that we can send directly to the clients where each referral the client
brings, they get 10% of the fee we make from them". Terms (Zain 21:54): 10% of the referral's first invoice, paid within 30 days of their payment. Supersedes the Nov 17 "Referral Partner Program" removal (that was a
public partner program; this one is client-to-client, sent by link only).
Never "free", never "CPA", no street address. The form posts to the same FormSubmit endpoint as the quote boxes.
Run via tools/build_resources.py (it calls build(); the URL is NOT added to site_pages.json, so it stays out of the sitemap).
"""
import re

import build_blog as B
import lead_box
import ui_kit
from build_resources import page, write, esc, BASE

URL = BASE + "/referrals/"
TITLE = "Refer a Friend to MFA: Earn 10% of Their First Invoice | MFA"
DESC = "For MFA clients: refer a friend, family member or business owner and earn 10% of their first invoice."
TEL = '<a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>'

STEPS = [
    ("Tell us who", "Use the form below, or ask them to mention your name when they contact us."),
    ("We help them", "They get our usual written quote and service. You don't have to do anything else."),
    ("You get 10%", "When they pay their first invoice, we pay you 10% of it."),
]

TERMS = [
    "You earn 10% of the first invoice we send each new client you refer.",
    "We pay you within 30 days of receiving their payment, by bank transfer or check.",
    "A referral counts if the person hasn't contacted or worked with MFA before. If two people refer the same person, the first referral we receive counts.",
    "There's no limit on how many people you can refer.",
    "Taxes, penalties and interest that clients pay to the IRS or a state are not our fees and don't count. If we refund any of that invoice, the reward is reduced to match.",
    "Referral rewards are income to you. We may ask you for a Form W-9 before paying and send you a Form 1099 where the rules require one.",
    "Your friend's tax and financial details stay confidential. We'll only tell you that they became a client and the reward you earned.",
    "We may change or end the program at any time; referrals we've already received are paid under the terms in place when you sent them.",
]

FAQ = [
    ("Who can I refer?", "Anyone who needs tax returns, bookkeeping, LLC setup, payroll or other accounting help: friends, family, "
     "classmates, coworkers and business owners. They can be anywhere in the US."),
    ("Does my friend pay more because they were referred?", "No. They get the same written quote as any other client."),
    ("How do I know my referral went through?", "We email you when we receive it, and again when they become a client and when we pay your reward."),
    ("Can I refer someone who already contacted MFA?", "Only new contacts count. If they already reached out to us, the referral won't qualify."),
]

CSS = """<style>
.rf-hero{background:var(--navy,#10233F);color:#fff;padding:72px 0 56px}.rf-hero h1{color:#fff;font-family:'Cormorant Garamond',Georgia,serif;font-size:clamp(34px,5vw,54px);line-height:1.08;margin:10px 0 14px}
.rf-hero h1 em{color:#E7C873;font-style:italic}.rf-hero p{max-width:640px;font-size:18px;color:#E8ECF2}
.rf-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.rf-steps .step{background:#fff;border:1px solid #E3E6EC;border-radius:14px;padding:22px}
.rf-steps .num{display:inline-flex;width:34px;height:34px;border-radius:50%;background:#B08D3F;color:#fff;align-items:center;justify-content:center;font-weight:700;margin-bottom:10px}
.rf-terms{max-width:860px}.rf-terms li{margin:0 0 10px;line-height:1.55}
.rf-f{display:grid;grid-template-columns:1fr 1fr;gap:14px 18px;background:#fff;border:1px solid #E3E6EC;border-radius:16px;padding:28px;max-width:860px}
.rf-f .full{grid-column:1/-1}.rf-f label{display:block;font-weight:600;font-size:14px;margin-bottom:6px}.rf-f input,.rf-f select,.rf-f textarea{width:100%;padding:12px 14px;border:1px solid #C9CED8;border-radius:10px;font:inherit}
.rf-f textarea{min-height:90px}.rf-f h3{grid-column:1/-1;margin:6px 0 0;font-size:17px}.rf-f .btn{border:0;cursor:pointer;padding:16px 28px}
.rf-st{color:#A3311F;min-height:1em;margin:0}.rf-hp{position:absolute;left:-9999px}.rf-fine{font-size:13px;color:#5A5A5A;margin:0}
@media(max-width:760px){.rf-steps{grid-template-columns:1fr}.rf-f{grid-template-columns:1fr;padding:20px}}
</style>"""

JS = r"""(function(){var f=document.getElementById('rf-form');if(!f)return;var st=f.querySelector('.rf-st'),b=f.querySelector('button');
var EM=/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;
f.addEventListener('submit',function(e){e.preventDefault();if(f._honey.value)return;st.textContent='';
var nm=f.name.value.trim(),em=f.email.value.trim(),fn=f.friend_name.value.trim(),fe=f.friend_email.value.trim(),fp=f.friend_phone.value.trim();
if(nm.length<2){st.textContent='Please enter your name.';f.name.focus();return;}
if(!EM.test(em)){st.textContent='Please enter your email address, like name@example.com.';f.email.focus();return;}
if(fn.length<2){st.textContent='Please enter the name of the person you are referring.';f.friend_name.focus();return;}
if(!EM.test(fe)&&fp.length<7){st.textContent='Please add their email or phone so we can reach them.';f.friend_email.focus();return;}
var l=b.textContent;b.disabled=true;b.textContent='Sending…';
var d=new FormData(f);d.append('page',location.href);d.append('_replyto',em);
d.append('_subject','Referral: '+fn+' (referred by '+nm+')');d.append('_captcha','false');d.append('_template','table');
fetch('__ENDPOINT__',{method:'POST',headers:{'Accept':'application/json'},body:d}).then(function(x){return x.json().catch(function(){return {success:x.ok};});})
.then(function(j){if(!j||j.success===false||j.success==='false')throw new Error((j&&j.message)||'Send failed');
try{sessionStorage.setItem('mfa_contact_sent','referral');}catch(e){}location.href='/contact/thanks/';})
.catch(function(err){st.innerHTML='We couldn’t send this just now. Please email <a href="mailto:__EMAIL__">__EMAIL__</a> or call (347) 205-4468.';
b.disabled=false;b.textContent=l;if(window.console)console.warn('Referral form:',err&&err.message);});});})();"""

NEEDS = [("tax-return", "Tax return"), ("bookkeeping", "Bookkeeping"), ("llc", "LLC setup"), ("payroll", "Payroll"),
         ("intl-student", "International student taxes"), ("other", "Something else / not sure")]


def build():
    steps = "".join(f'<div class="step"><span class="num">{i}</span><h3>{esc(h)}</h3><p>{esc(p)}</p></div>'
                    for i, (h, p) in enumerate(STEPS, 1))
    terms = "".join(f"<li>{esc(x)}</li>" for x in TERMS)
    opts = '<option value="">Choose one</option>' + "".join(f'<option value="{esc(v)}">{esc(t)}</option>' for v, t in NEEDS)
    faq = ui_kit.faq_accordion([(esc(q), esc(a)) for q, a in FAQ], prefix="rf")
    js = JS.replace("__ENDPOINT__", lead_box.ENDPOINT).replace("__EMAIL__", B.EMAIL)
    body = f'''{CSS}<header class="rf-hero"><div class="wrap"><span class="eyebrow">For MFA clients</span>
<h1>Refer a friend. <em>Earn 10% of their first invoice.</em></h1>
<p>Know someone who needs help with taxes, bookkeeping or setting up a business? Send them our way. When they become a client and pay their first invoice, you get 10% of it.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#refer">Refer someone</a><a class="btn btn-line" href="#terms">How rewards work</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="how-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="how-h">Three simple steps.</h2></div>
<div class="rf-steps">{steps}</div></section>
<section class="wrap llc-sec" id="refer" aria-labelledby="rf-h"><div class="sec-hd"><span class="eyebrow eb-dark">Refer someone</span><h2 id="rf-h">Send us their details.</h2>
<p>Please let them know you're passing on their details. We'll reach out within one business day.</p></div>
<form class="rf-f" id="rf-form" novalidate>
<h3>About you</h3>
<div><label for="rf-name">Your name *</label><input id="rf-name" name="name" autocomplete="name" required/></div>
<div><label for="rf-email">Your email *</label><input id="rf-email" name="email" type="email" autocomplete="email" required/></div>
<h3>Who you're referring</h3>
<div><label for="rf-fname">Their name *</label><input id="rf-fname" name="friend_name" required/></div>
<div><label for="rf-femail">Their email</label><input id="rf-femail" name="friend_email" type="email"/></div>
<div><label for="rf-fphone">Their phone</label><input id="rf-fphone" name="friend_phone" type="tel"/></div>
<div><label for="rf-need">What do they need?</label><select id="rf-need" name="need">{opts}</select></div>
<div class="full"><label for="rf-note">Anything we should know? (optional)</label><textarea id="rf-note" name="details" placeholder="For example: F-1 student, needs 2025 return"></textarea></div>
<input type="hidden" name="lead_source" value="referral"/><div class="rf-hp" aria-hidden="true"><label>Leave blank<input name="_honey" tabindex="-1" autocomplete="off"/></label></div>
<div class="full"><button class="btn btn-gold" type="submit">Send referral</button></div>
<p class="rf-st full" role="alert"></p><p class="rf-fine full">We only use these details to contact the person you refer and to track your reward. No spam.</p>
</form></section>
<section class="wrap llc-sec" id="terms" aria-labelledby="t-h"><div class="sec-hd"><span class="eyebrow eb-dark">The details</span><h2 id="t-h">How rewards work.</h2></div>
<ul class="rf-terms">{terms}</ul></section>
<section class="wrap llc-sec faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">Referral questions</h2></div>{faq}</section>
<p class="wrap llc-sec">Questions? Email <a href="mailto:{B.EMAIL}">{B.EMAIL}</a> or call {TEL}.</p>
</main><script>{js}</script>'''
    html = page(TITLE, DESC, URL, body, None, active="", keywords=None)
    html = re.sub(r'<meta name="robots" content="[^"]*"/>', '<meta name="robots" content="noindex,follow"/>', html, count=1)
    return write("referrals", html)


if __name__ == "__main__":
    print(build())
