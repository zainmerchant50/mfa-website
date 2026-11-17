"""Shared "Get my price" quote box for niche pages and niche calculators (Site, 2026-11-17).

Zain (2026-11-17): "Add the website features you recommended above" (niche-growth-plan #2 and #4: a quote form on every
niche page, and "email me my results / get my quote" on the niche calculators).
Posts to FormSubmit like every other MFA lead form; site/assets/forms.js (loaded site-wide) also saves each send to
MailerLite and fires the lead event. On a calculator page the result tiles (.tres .kpi) are added to the email so we
can quote from the visitor's own numbers. No prices are shown. Never "free".
QA: send a test with the MFA QA TEST identity after any change (rule 22, claude/site/hub-qa-checklist.md).
"""
import build_blog as B
from build_resources import esc

ENDPOINT = "https://formsubmit.co/ajax/" + B.EMAIL

CSS = """<style>
.lbx{max-width:var(--maxw,1180px);margin:0 auto;padding:0 24px}
.lbx-card{background:var(--navy,#0f2340);color:#fff;border-radius:22px;padding:30px 28px;display:grid;grid-template-columns:1fr 1.25fr;gap:28px;align-items:start}
.lbx-card h2{color:#fff;font-size:clamp(1.45rem,2.6vw,1.9rem);margin:6px 0 10px}
.lbx-card .eyebrow{color:var(--gold,#b08d3f)}
.lbx-card p{color:rgba(255,255,255,.82);margin:0 0 10px;font-weight:300}
.lbx-card ul{margin:10px 0 0;padding-left:18px;color:rgba(255,255,255,.82);font-weight:300}
.lbx-card ul li{margin:4px 0}
.lbx-f{background:#fff;color:var(--ink,#151515);border-radius:16px;padding:20px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
.lbx-f .fld{margin:0}.lbx-f .full{grid-column:1/-1}
.lbx-f label{display:block;font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--navy,#0f2340);margin-bottom:6px}
.lbx-f input,.lbx-f select,.lbx-f textarea{width:100%;min-width:0;height:46px;border:1px solid rgba(21,21,21,.16);border-radius:12px;padding:0 12px;font:400 15px Inter,sans-serif;background:#fff;color:var(--ink,#151515)}
.lbx-f textarea{height:84px;padding:10px 12px;resize:vertical}
.lbx-f input:focus,.lbx-f select:focus,.lbx-f textarea:focus{outline:none;border-color:var(--gold,#b08d3f);box-shadow:0 0 0 3px rgba(176,141,63,.15)}
.lbx-f .req{color:#b42318;margin-left:3px}
.lbx-f .opt-l{font-weight:400;letter-spacing:0;text-transform:none;color:var(--muted,#666)}
.lbx-f .btn{width:100%;justify-content:center}
.lbx-f .lbx-st{font-size:.85rem;color:#b42318;margin:0}
.lbx-f .lbx-fine{font-size:.78rem;color:var(--muted,#666);margin:0}
.lbx-f .lbx-hp{position:absolute;left:-5000px;width:1px;height:1px;overflow:hidden}
@media(max-width:820px){.lbx-card{grid-template-columns:1fr;padding:24px 18px}.lbx-f{grid-template-columns:1fr;padding:16px}}
.lbx-sticky{display:none}
@media(max-width:720px){.lbx-sticky{display:flex;position:fixed;left:12px;right:12px;bottom:12px;z-index:60;gap:8px}
.lbx-sticky a{flex:1;justify-content:center;box-shadow:0 8px 24px rgba(15,35,64,.25)}
body.lbx-on{padding-bottom:76px}}
</style>"""

JS = r"""(function(){var f=document.getElementById('lbx-form');if(!f)return;var st=f.querySelector('.lbx-st'),b=f.querySelector('button');
var EM=/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;
function results(){var out=[];[].slice.call(document.querySelectorAll('.tres .kpi')).forEach(function(k){var v=k.querySelector('b'),l=k.querySelector('span');
if(v&&l&&v.textContent.trim()&&v.textContent.trim()!=='—')out.push(l.textContent.trim()+': '+v.textContent.trim());});
var s=document.getElementById('rsub');if(out.length&&s&&s.textContent.trim())out.unshift(s.textContent.trim());return out.join(' | ');}
f.addEventListener('submit',function(e){e.preventDefault();if(f._honey.value)return;st.textContent='';
var nm=f.name.value.trim(),em=f.email.value.trim();
if(nm.length<2){st.textContent='Please enter your name.';f.name.focus();return;}
if(!EM.test(em)){st.textContent='Please enter a valid email address, like name@example.com.';f.email.focus();return;}
var l=b.textContent;b.disabled=true;b.textContent='Sending…';f.email.value=em;
var d=new FormData(f);d.append('page',location.href);d.append('_replyto',em);var r=results();if(r)d.append('calculator_results',r);
d.append('_subject','Quote request: __TOPIC__ / '+nm);d.append('_captcha','false');d.append('_template','table');
fetch('__ENDPOINT__',{method:'POST',headers:{'Accept':'application/json'},body:d}).then(function(x){return x.json().catch(function(){return {success:x.ok};});})
.then(function(j){if(!j||j.success===false||j.success==='false')throw new Error((j&&j.message)||'Send failed');
try{sessionStorage.setItem('mfa_contact_sent','__SLUG__');}catch(e){}location.href='/contact/thanks/';})
.catch(function(err){st.innerHTML='We couldn’t send this just now. Please email <a href="mailto:__EMAIL__">__EMAIL__</a> or call (347) 205-4468.';
b.disabled=false;b.textContent=l;if(window.console)console.warn('Quote box:',err&&err.message);});});
var sk=document.querySelector('.lbx-sticky');if(sk){document.body.classList.add('lbx-on');if(window.IntersectionObserver){new IntersectionObserver(function(es){sk.style.display=es[0].isIntersecting?'none':'';}).observe(document.getElementById('get-price'));}}
})();"""


def lead_box(topic, slug, heading, sub, needs, bullets=(), calc=False, sticky=True):
    """topic: short label for the email subject; slug: lead source id; needs: [(value, label)] for 'What do you need?'."""
    opts = '<option value="">Choose one</option>' + "".join(f'<option value="{esc(v)}">{esc(t)}</option>' for v, t in needs)
    lis = "".join(f"<li>{esc(x)}</li>" for x in bullets)
    btn = "Email me my quote" if not calc else "Send my results and get a quote"
    note = ("We'll reply from hello@mfa-advisory.com within one business day with a fixed quote or a few questions. "
            + ("Your calculator results are included so we can quote from your numbers. " if calc else ""))
    sticky_html = ('<div class="lbx-sticky"><a class="btn btn-gold" href="#get-price">Get my price</a>'
                   '<a class="btn btn-ink" href="tel:+13472054468" data-conv="call">Call</a></div>') if sticky else ""
    js = JS.replace("__ENDPOINT__", ENDPOINT).replace("__EMAIL__", B.EMAIL).replace("__TOPIC__", topic.replace("'", "\\'")).replace("__SLUG__", slug)
    return f'''{CSS}<section class="lbx" id="get-price" aria-labelledby="lbx-h"><div class="lbx-card"><div>
<span class="eyebrow">Get my price</span><h2 id="lbx-h">{esc(heading)}</h2><p>{esc(sub)}</p>{f"<ul>{lis}</ul>" if lis else ""}</div>
<form class="lbx-f" id="lbx-form" novalidate>
<div class="fld"><label for="lbx-name">Name<span class="req" aria-hidden="true">*</span></label><input id="lbx-name" name="name" autocomplete="name" required aria-required="true"/></div>
<div class="fld"><label for="lbx-email">Email<span class="req" aria-hidden="true">*</span></label><input id="lbx-email" name="email" type="email" autocomplete="email" required aria-required="true"/></div>
<div class="fld"><label for="lbx-phone">Phone <span class="opt-l">(optional)</span></label><input id="lbx-phone" name="phone" type="tel" autocomplete="tel"/></div>
<div class="fld"><label for="lbx-need">What do you need?</label><select id="lbx-need" name="need">{opts}</select></div>
<div class="fld full"><label for="lbx-note">Anything we should know? <span class="opt-l">(optional)</span></label><textarea id="lbx-note" name="details" placeholder="For example: 2 rentals in NJ, one on Airbnb"></textarea></div>
<input type="hidden" name="lead_source" value="{esc(slug)}"/><div class="lbx-hp" aria-hidden="true"><label>Leave blank<input name="_honey" tabindex="-1" autocomplete="off"/></label></div>
<div class="full"><button class="btn btn-gold" type="submit">{btn}</button></div>
<p class="lbx-st full" role="alert"></p><p class="lbx-fine full">{esc(note)}No spam. We never share your details.</p>
</form></div></section>{sticky_html}<script>{js}</script>'''
