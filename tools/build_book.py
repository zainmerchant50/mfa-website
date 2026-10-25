#!/usr/bin/env python3
"""Builds /book/ (Site/Hub): the booking page, moved off the home page on Zain's request (2026-10-23 02:20 ET).
The Google Calendar appointment schedule is embedded here; every "Book" link on the site points here.
Ad landing pages (/princeton-nj/, /union-city-nj/, /new-york-ny/) keep their own on-page calendar for conversions.
Also builds /contact/thanks/ (build_contact_thanks, called from build()): where the general contact/quote forms
land after a confirmed send (home, landing pages, /bookkeeping-cleanup/; see tools/ads.py). noindex, so the sitemap
skips it; it fires the Google Ads "Contact form submitted" conversion once per send via mfaContactThanks().
Never "free", never "CPA", no street address. Run via tools/build_resources.py (it calls build()).
"""
import ads
import build_blog as B
import seo
import ui_kit
from build_resources import page, write, esc, BASE

CAL = ("https://calendar.google.com/calendar/appointments/schedules/"
       "AcZssZ2z1XCM1FcZDRE6VnHyWPfqXcgkL1-kxgrTJaKaM-0VCun9u0cVIziW87B0XAQGVXE51SZ0LOo9")
# Step and FAQ text is trusted HTML (links allowed). The calendar is the FIRST section on this page, so
# anything that points to it says "above" / "at the top of this page" and links to #calendar.
# tools/check_ui.py fails the build if a "below"/"above" booking reference contradicts the page order.
CAL_LINK = '<a href="#calendar">calendar at the top of this page</a>'
EXPECT = [
    ("Before the call", f'Pick a time in the {CAL_LINK}. You get a Google Meet link by email. If you like, send a few lines about '
     'your business or a recent statement to <a href="mailto:info@mfa-advisory.com">info@mfa-advisory.com</a> so we come prepared.'),
    ("On the call", "Thirty minutes on your books, taxes or a decision in front of you. We ask about your setup, look at what you share, and tell you what we'd fix first."),
    ("After the call", "If it makes sense to work together, we send a written scope and a price agreed before any work starts. No obligation either way."),
]
TOPICS = ["Monthly bookkeeping and catch-up", "Business tax returns (Schedule C, 1065, 1120-S)", "Quarterly estimates and year-end planning",
          "LLC formation and S corp elections", "1099 filing for your contractors", "QuickBooks Online setup and cleanup"]
FAQ = [
    ("Is there a cost for the consultation?", "No. The first 30-minute consultation has no charge and no obligation."),
    ("Who will I meet with?", "Zain Merchant, the founder of Merchant Financial Advisory, or a member of his team of tax and "
     "accounting experts, depending on what you'd like to discuss. Zain's background: CPA candidate · ACCA · Big Four (ex-PwC) · "
     "PTIN/EFIN tax preparer."),
    ("Can we talk by phone instead?", f'Yes. Call <a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>, or pick a time in the '
     f"{CAL_LINK} and add a note that you'd prefer a phone call."),
    ("What if none of the times work?", 'Email <a href="mailto:info@mfa-advisory.com">info@mfa-advisory.com</a> with two or three times that suit you and we\'ll make one of them work.'),
]
CSS = """<style>
.bk-wrap{max-width:1080px;margin:0 auto}
.bk-frame{background:#fff;border:1px solid var(--line, #e3dfd3);border-radius:14px;overflow:hidden;box-shadow:0 10px 30px rgba(16,35,63,.08)}
.bk-frame iframe{display:block;width:100%;height:760px;border:0}
.bk-alt{text-align:center;margin:14px 0 0;font-size:.9rem;color:var(--muted)}
.bk-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;counter-reset:s;margin-top:6px}
.bk-steps .step{padding:26px;border-top:2px solid var(--gold, #B08D3F);background:#fff;border-radius:0 0 12px 12px}
.bk-steps .step:before{counter-increment:s;content:"0" counter(s);font-family:'Cormorant Garamond',Georgia,serif;font-size:38px;color:var(--gold, #B08D3F);display:block;line-height:1;margin-bottom:10px}
.bk-steps .step h3{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.6rem;font-weight:500;margin:0 0 8px;color:var(--ink, #10233F)}
.bk-steps .step p{margin:0;color:var(--muted);font-size:.95rem;line-height:1.7}
.bk-steps .step p a,#faqs .faq-a-in a{color:var(--navy);border-bottom:1px solid var(--gold);transition:color .3s}
.bk-steps .step p a:hover,#faqs .faq-a-in a:hover{color:var(--gold)}
#calendar{scroll-margin-top:96px}
.bk-topics{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 0;padding:0;list-style:none}
.bk-topics li{border:1px solid var(--gold, #B08D3F);border-radius:999px;padding:7px 16px;font-size:.92rem;cursor:default;transition:background .3s,color .3s,transform .35s cubic-bezier(.16,1,.3,1)}
.bk-topics li:hover{background:var(--gold, #B08D3F);color:#fff;transform:translateY(-2px)}
.js .bk-topics li{opacity:0;transform:translateY(12px);transition:opacity .6s cubic-bezier(.16,1,.3,1),transform .6s cubic-bezier(.16,1,.3,1),background .3s,color .3s}
.js .bk-topics.in li{opacity:1;transform:none}
.bk-frame{transition:box-shadow .5s cubic-bezier(.16,1,.3,1)}
.bk-frame:hover{box-shadow:0 18px 44px rgba(16,35,63,.14)}
@media(max-width:860px){.bk-steps{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){.js .bk-topics li{opacity:1;transform:none;transition:none}}
@media(max-width:860px){.bk-frame iframe{height:1000px}}
</style>"""


# Staggered entrance for the topic pills (outside the f-string because of its braces).
TOPICS_JS = """<script>(function(){var u=document.getElementById('bk-topics');if(!u)return;var li=[].slice.call(u.children);li.forEach(function(e,i){e.style.transitionDelay=(i*70)+'ms';});
function go(){u.classList.add('in');setTimeout(function(){li.forEach(function(e){e.style.transitionDelay='';});},1200);}
if(!('IntersectionObserver' in window))return go();var io=new IntersectionObserver(function(en){if(en[0].isIntersecting){go();io.disconnect();}},{threshold:.2});io.observe(u);setTimeout(go,4000);})();</script>"""


def build():
    url = BASE + "/book/"
    title = "Book a 30-Minute Consultation | Merchant Financial Advisory"
    desc = ("Book a 30-minute call about bookkeeping, business taxes, LLC formation or year-end planning. "
            "Pick a time on Google Meet or call (347) 205-4468.")
    expect = "".join(f'<div class="step"><h3>{esc(h)}</h3><p>{p}</p></div>' for h, p in EXPECT)
    topics = "".join(f"<li>{esc(t)}</li>" for t in TOPICS)
    faq = ui_kit.faq_accordion([(esc(q), a) for q, a in FAQ], prefix="bk")
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Book a call</span>
<h1>Thirty minutes. <em>Your numbers, our full attention.</em></h1>
<p>Pick a time that works for you. It's 30 minutes on Google Meet, and you'll leave with a clear read on what to fix first.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#calendar">Choose a time</a><a class="btn btn-line" href="tel:+13472054468" data-conv="call">Call (347) 205-4468</a></div></div></header>
<main>
<section class="wrap llc-sec" id="calendar" aria-label="Booking calendar"><div class="bk-wrap">
<div class="bk-frame book-frame"><iframe src="{CAL}?gv=true" title="Book a consultation with Merchant Financial Advisory" loading="lazy"></iframe></div>
<p class="bk-alt">Calendar not loading? <a href="{CAL}" target="_blank" rel="noopener noreferrer" data-conv="book">Open the booking page</a> or email <a href="mailto:{B.EMAIL}">{B.EMAIL}</a>.</p>
</div></section>
<section class="wrap llc-sec" aria-labelledby="exp-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="exp-h">What to expect</h2></div>
<div class="bk-steps">{expect}</div></section>
<section class="wrap llc-sec" aria-labelledby="top-h"><div class="sec-hd"><span class="eyebrow eb-dark">Common topics</span><h2 id="top-h">What people book us for</h2></div>
<ul class="bk-topics" id="bk-topics">{topics}</ul></section>
<section class="wrap llc-sec faqs" id="faqs" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">Before you book</h2></div>{faq}</section>
{ui_kit.fineprint("A consultation is general information and does not create a client relationship until we both agree to a written scope.")}
</main>
{TOPICS_JS}'''
    ld = seo.graph(url, "Book a consultation", desc,
                   {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
                       {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ui_kit._plain(a)}} for q, a in FAQ]},
                   crumb=[("Home", BASE + "/"), ("Book a consultation", url)])
    build_contact_thanks()
    return write("book", page(title, desc, url, body, ld, active="b"))


NEXT = [
    ("We read your message", "Our team reviews what you sent so the right person picks it up."),
    ("We reply", "You'll hear back from us by email, or by phone if you asked for a call. If we need anything else, we'll ask then."),
    ("You decide", "If it makes sense to work together, we send a written scope and a price agreed before any work starts. No obligation either way."),
]
TY_CSS = """<style>
.ty-cards{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:6px}
.ty-cards .card{padding:26px;display:flex;flex-direction:column;gap:10px;background:#fff;border:1px solid var(--hair);border-radius:16px}
.ty-cards h3{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.6rem;font-weight:500;margin:0;color:var(--ink, #10233F)}
.ty-cards p{margin:0;color:var(--muted);font-size:.95rem;line-height:1.7;flex:1}
.ty-cards .btn{align-self:flex-start;margin-top:6px}
@media(max-width:860px){.ty-cards{grid-template-columns:1fr}}
</style>"""


def build_contact_thanks():
    url = BASE + ads.THANKS.rstrip("/") + "/"
    title = "Message Received | Merchant Financial Advisory"
    desc = "Thanks for contacting Merchant Financial Advisory. We got your message and will reply soon."
    steps = "".join(f'<div class="step"><h3>{esc(h)}</h3><p>{esc(t)}</p></div>' for h, t in NEXT)
    body = f'''{CSS}{TY_CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Message sent</span>
<h1>Thanks — we got your message. <em>We'll reply soon.</em></h1>
<p>Your details reached our team. There's nothing else you need to do right now.</p>
<div class="hero-btns"><a class="btn btn-gold" href="/book/">Book a 30-minute call</a><a class="btn btn-line" href="/resources/">Browse resources</a></div></div></header>
<main>
<section class="wrap llc-sec" aria-labelledby="next-h"><div class="sec-hd"><span class="eyebrow eb-dark">What happens next</span><h2 id="next-h">From your message to a clear next step</h2></div>
<div class="bk-steps">{steps}</div></section>
<section class="wrap llc-sec" aria-labelledby="wait-h"><div class="sec-hd"><span class="eyebrow eb-dark">While you wait</span><h2 id="wait-h">Want to move faster?</h2></div>
<div class="ty-cards">
<div class="card"><h3>Talk sooner</h3><p>Pick a 30-minute slot on Google Meet. Mention your message and we'll come prepared.</p><a class="btn btn-gold" href="/book/">Choose a time</a></div>
<div class="card"><h3>Guides and calculators</h3><p>Checkers, calculators, tax calendars and checklists for small business owners.</p><a class="btn btn-line-ink" href="/resources/">Open resources</a></div>
</div>
<p class="bk-alt">Questions in the meantime: <a href="mailto:{B.EMAIL}">{B.EMAIL}</a> or <a href="tel:+13472054468" data-conv="call">(347) 205-4468</a>.</p></section>
</main>
<script>if(window.mfaContactThanks)mfaContactThanks();</script>'''
    html = page(title, desc, url, body, None, active="b")
    html = html.replace('<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"/>',
                        '<meta name="robots" content="noindex"/>', 1)
    assert 'content="noindex"' in html
    return write(ads.THANKS.strip("/"), html)


if __name__ == "__main__":
    print(build())
