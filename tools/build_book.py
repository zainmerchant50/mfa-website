#!/usr/bin/env python3
"""Builds /book/ (Site/Hub): the booking page, moved off the home page on Zain's request (2026-10-23 02:20 ET).
The Google Calendar appointment schedule is embedded here; every "Book" link on the site points here.
Ad landing pages (/princeton-nj/, /union-city-nj/, /new-york-ny/) keep their own on-page calendar for conversions.
Never "free", never "CPA", no street address. Run via tools/build_resources.py (it calls build()).
"""
import build_blog as B
import seo
from build_resources import page, write, esc, BASE

CAL = ("https://calendar.google.com/calendar/appointments/schedules/"
       "AcZssZ2z1XCM1FcZDRE6VnHyWPfqXcgkL1-kxgrTJaKaM-0VCun9u0cVIziW87B0XAQGVXE51SZ0LOo9")
EXPECT = [
    ("Before the call", "Pick a time below. You get a Google Meet link by email. If you like, send a few lines about your business or a recent statement to info@mfa-advisory.com so we come prepared."),
    ("On the call", "Thirty minutes on your books, taxes or a decision in front of you. We ask about your setup, look at what you share, and tell you what we'd fix first."),
    ("After the call", "If it makes sense to work together, we send a written scope and a price agreed before any work starts. No obligation either way."),
]
TOPICS = ["Monthly bookkeeping and catch-up", "Business tax returns (Schedule C, 1065, 1120-S)", "Quarterly estimates and year-end planning",
          "LLC formation and S corp elections", "1099 filing for your contractors", "QuickBooks Online setup and cleanup"]
FAQ = [
    ("Is there a cost for the consultation?", "No. The first 30-minute consultation has no charge and no obligation."),
    ("Who will I speak with?", "Zain Merchant, ACCA, the founder of Merchant Financial Advisory, with Big Four audit and accounting experience."),
    ("Can we talk by phone instead?", "Yes. Call (347) 205-4468, or choose a time below and mention in the notes that you'd prefer a phone call."),
    ("What if none of the times work?", "Email info@mfa-advisory.com with two or three times that suit you and we'll make one of them work."),
]
CSS = """<style>
.bk-wrap{max-width:1080px;margin:0 auto}
.bk-frame{background:#fff;border:1px solid var(--line, #e3dfd3);border-radius:14px;overflow:hidden;box-shadow:0 10px 30px rgba(16,35,63,.08)}
.bk-frame iframe{display:block;width:100%;height:760px;border:0}
.bk-alt{text-align:center;margin:14px 0 0;font-size:.9rem;color:var(--muted)}
.bk-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;margin-top:6px}
.bk-grid .card{padding:20px 22px}.bk-grid h3{font-size:1.1rem;margin:0 0 6px}.bk-grid p{margin:0;font-size:.93rem;line-height:1.55}
.bk-topics{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 0;padding:0;list-style:none}
.bk-topics li{border:1px solid var(--gold, #B08D3F);border-radius:999px;padding:6px 14px;font-size:.9rem}
.bk-faq details{border-bottom:1px solid var(--line, #e3dfd3);padding:14px 0}.bk-faq summary{cursor:pointer;font-weight:600}
.bk-faq p{margin:8px 0 0;line-height:1.6}
@media(max-width:860px){.bk-frame iframe{height:1000px}}
</style>"""


def build():
    url = BASE + "/book/"
    title = "Book a 30-Minute Consultation | Merchant Financial Advisory"
    desc = ("Book a 30-minute call about bookkeeping, business taxes, LLC formation or year-end planning. "
            "Pick a time on Google Meet or call (347) 205-4468.")
    expect = "".join(f'<article class="card"><h3>{esc(h)}</h3><p>{esc(p)}</p></article>' for h, p in EXPECT)
    topics = "".join(f"<li>{esc(t)}</li>" for t in TOPICS)
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in FAQ)
    body = f'''{CSS}<header class="bhero rhero"><div class="wrap"><span class="eyebrow">Book a call</span>
<h1>Thirty minutes. <em>Your numbers, our full attention.</em></h1>
<p>Pick a time that works for you. It's 30 minutes on Google Meet, and you'll leave with a clear read on what to fix first.</p>
<div class="hero-btns"><a class="btn btn-gold" href="#calendar">Choose a time</a><a class="btn btn-line" href="tel:+13472054468" data-conv="call">Call (347) 205-4468</a></div></div></header>
<main>
<section class="wrap llc-sec" id="calendar" aria-label="Booking calendar"><div class="bk-wrap">
<div class="bk-frame"><iframe src="{CAL}?gv=true" title="Book a consultation with Merchant Financial Advisory" loading="lazy"></iframe></div>
<p class="bk-alt">Calendar not loading? <a href="{CAL}" target="_blank" rel="noopener noreferrer" data-conv="book">Open the booking page</a> or email <a href="mailto:{B.EMAIL}">{B.EMAIL}</a>.</p>
</div></section>
<section class="wrap llc-sec" aria-labelledby="exp-h"><div class="sec-hd"><span class="eyebrow eb-dark">How it works</span><h2 id="exp-h">What to expect</h2></div>
<div class="bk-grid">{expect}</div></section>
<section class="wrap llc-sec" aria-labelledby="top-h"><div class="sec-hd"><span class="eyebrow eb-dark">Common topics</span><h2 id="top-h">What people book us for</h2></div>
<ul class="bk-topics">{topics}</ul></section>
<section class="wrap llc-sec bk-faq" aria-labelledby="faq-h"><div class="sec-hd"><span class="eyebrow eb-dark">Questions</span><h2 id="faq-h">Before you book</h2></div>{faq}</section>
<section class="wrap llc-sec"><p class="disclaimer">A consultation is general information and does not create a client relationship until we both agree a written scope.</p></section>
</main>'''
    ld = seo.graph(url, "Book a consultation", desc,
                   {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
                       {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
                   crumb=[("Home", BASE + "/"), ("Book a consultation", url)])
    return write("book", page(title, desc, url, body, ld, active="b"))


if __name__ == "__main__":
    print(build())
