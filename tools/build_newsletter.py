#!/usr/bin/env python3
"""Build the MFA Insights newsletter email for one published post.

    python3 tools/build_newsletter.py <slug> --mailerlite                  # list send via MailerLite (merge tags)
    python3 tools/build_newsletter.py <slug> [--to someone@example.com]   # one-off copy

Writes:
    site/newsletter/issues/<slug>/index.html   "View in browser" copy (noindex), published with the site
    newsletter/out/<slug>.email.html           email-ready HTML (inline longhand CSS, 600px table layout)
    newsletter/out/<slug>.txt                  plain-text alternative
    newsletter/out/<slug>.json                 subject, preheader, paths (used by the publish job)

Design (B2B services newsletter best practice): the email is a brand piece from MFA Insights, not a
personal letter. It is a scannable teaser that drives readers to the full article on the site:
  personal greeting -> short intro -> "At a glance" takeaways -> keep-handy graphic + download ->
  what's inside the full guide + primary CTA -> upcoming key dates (add to calendar) ->
  a reader question -> how MFA can help (services + booking) -> more articles -> share -> footer
  (CAN-SPAM postal address, unsubscribe, disclaimer). One primary CTA (read the guide), one
  secondary CTA (book a consultation). Longhand CSS + bgcolor so Gmail/Outlook/Apple Mail match.
Standard library only.
"""
import html, json, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_blog as B  # noqa: E402

OUT = B.ROOT / "newsletter" / "out"
NAVY, NAVY2, GOLD, GOLDB, PAPER, PAPER2, INK, BODY, MUTED, LINE = (
    "#10233F", "#1B3557", "#B08D3F", "#D8B769", "#ECEAE3", "#F5F4EF", "#151515", "#2E2E2E", "#6B6B6B", "#E6E3DA")
SERIF = "Georgia,'Times New Roman',Times,serif"
SANS = "Helvetica,Arial,sans-serif"
# CAN-SPAM: every commercial email must show a valid physical postal address. Email only; never on the website.
MAILING_ADDRESS = "28 Spring St #5114, Princeton, NJ 08542"
SENDER_EMAIL = "insights@mfa-advisory.com"   # MailerLite sender (domain authenticated Oct 2026)
DEFAULT_INTRO = ("Here's what's new from MFA Insights. The key points are right below, "
                 "and the full article is one click away when you want the details.")
UTM = "utm_source=newsletter&utm_medium=email&utm_campaign="

# Services shown in "How MFA can help", matched to the post's category (wording mirrors the site).
SERVICES = {
    "prep": ("Tax preparation and filing", "Federal, New Jersey, New York and multi-state returns for individuals and businesses, filed accurately and on time."),
    "plan": ("Tax planning", "Year-round planning on your real numbers: estimated payments, entity elections, retirement accounts and deductions."),
    "books": ("Bookkeeping and accounting", "Reconciliations, AP/AR and a clean monthly close, so your books are ready when a deadline arrives."),
    "report": ("Financial reporting", "P&L, balance sheet and cash flow you can act on, with simple dashboards."),
    "cfo": ("Fractional CFO", "Forecasting, budgeting and margin analysis without the cost of a full-time executive."),
    "qb": ("QuickBooks setup and cleanup", "Set up right, cleaned up, and kept current, so your reports match reality."),
    "gaap": ("Technical accounting", "US GAAP and IFRS guidance on revenue recognition, leases and other hard areas."),
}


def services_for(category):
    c = category.lower()
    if "quickbooks" in c or "business" in c:
        return ["qb", "books", "cfo"]
    if "accounting" in c or "bookkeeping" in c:
        return ["books", "report", "gaap"]
    if "planning" in c:
        return ["plan", "prep", "cfo"]
    return ["prep", "plan", "books"]


# ---------- style helpers (longhand CSS: Gmail and Outlook handle it more reliably than `font:` shorthand)
def f(size, lh, weight=400, family=SANS, color=BODY, extra=""):
    return f"font-family:{family};font-size:{size}px;line-height:{lh}px;font-weight:{weight};color:{color};{extra}"


def eyebrow(text, color=GOLD):
    return f'<p style="margin:0 0 10px;{f(11, 16, 700, color=color, extra="letter-spacing:2.5px;text-transform:uppercase;")}">{text}</p>'


def h2(text, mt=0):
    return f'<h2 style="margin:{mt}px 0 14px;{f(24, 30, 400, SERIF, NAVY)}">{text}</h2>'


def para(text, mb=18, size=16, lh=26, color=BODY):
    return f'<p style="margin:0 0 {mb}px;{f(size, lh, color=color)}">{text}</p>'


def button(href, label, bg=NAVY, fg="#ffffff", border=None, size=15):
    bd = f"border:1px solid {border};" if border else ""
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 8px 10px 0"><tr>'
            f'<td bgcolor="{bg}" style="background:{bg};{bd}border-radius:6px;mso-padding-alt:15px 26px">'
            f'<a href="{href}" style="display:inline-block;padding:15px 26px;{f(size, 18, 700, color=fg, extra="text-decoration:none;letter-spacing:.3px;")}">{label}</a>'
            f'</td></tr></table>')


def divider(mt=36, mb=36):
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:{mt}px 0 {mb}px">'
            f'<tr><td style="border-top:1px solid {LINE};font-size:0;line-height:0;height:1px">&nbsp;</td></tr></table>')


def section(inner, pad_top=0, pad_bottom=0, bg=None):
    bgs = f'bgcolor="{bg}" ' if bg else ""
    bgc = f"background:{bg};" if bg else ""
    return f'<tr><td {bgs}class="pad" style="{bgc}padding:{pad_top}px 48px {pad_bottom}px">{inner}</td></tr>'


def track(url, slug):
    if not url.startswith(B.BASE) or re.search(r"\.(png|ics|pdf)$", url):
        return url
    base, _, frag = url.partition("#")
    return base + ("&" if "?" in base else "?") + UTM + slug + ("#" + frag if frag else "")


def inline_rich(s):
    """Style the few inline tags allowed in short-version bullets and FAQ answers."""
    s = re.sub(r"<strong>", f'<strong style="font-weight:700;color:{INK}">', s)
    s = re.sub(r"<a [^>]*>(.*?)</a>", r"\1", s)
    return s.strip()


# ---------- pieces pulled from the article
def parts(p):
    body = p["body"]
    m = re.search(r'<div class="tldr">.*?<ul>(.*?)</ul>', body, re.S)
    glance = re.findall(r"<li>(.*?)</li>", m.group(1), re.S) if m else []
    bl = re.search(r'<p class="bottom-line">(.*?)</p>', body, re.S)
    bottom = bl.group(1) if bl else None
    heads = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", body, re.S)]
    heads = [h for h in heads if h.lower() not in ("the short version", "executive summary", "quick answers", "sources")]
    faq = None
    q = re.search(r"<h2>Quick answers</h2>\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>", body, re.S)
    if q:
        faq = (re.sub(r"<[^>]+>", "", q.group(1)).strip(), q.group(2))
    return glance, heads, faq, bottom


def upcoming_dates(p, limit=5):
    today = (datetime.now(timezone.utc) - timedelta(hours=5)).date().isoformat()
    ev = [e for e in B.post_events(p) if e["date"] >= today]
    return ev[:limit], len(ev)


def keydates_block(p, post_url, slug):
    ev, total = upcoming_dates(p)
    if not ev:
        return ""
    rows = ""
    for i, e in enumerate(ev):
        d = datetime.fromisoformat(e["date"])
        top = "" if i == 0 else f"border-top:1px solid {LINE};"
        rows += (f'<tr><td width="64" valign="top" style="{top}padding:16px 16px 16px 0">'
                 f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="56"><tr><td bgcolor="{NAVY}" align="center" style="background:{NAVY};border-radius:6px;padding:7px 0 8px">'
                 f'<div style="{f(10, 12, 700, color=GOLDB, extra="letter-spacing:1.5px;text-transform:uppercase;")}">{d:%b}</div>'
                 f'<div style="{f(22, 26, 700, SERIF, "#ffffff")}">{d.day}</div>'
                 f'<div style="{f(10, 12, 400, color="#C9D1DC")}">{d.year}</div></td></tr></table></td>'
                 f'<td valign="top" style="{top}padding:16px 0">'
                 f'<p style="margin:0 0 4px;{f(16, 22, 700, color=NAVY)}">{B.esc(e["title"])}</p>'
                 + (f'<p style="margin:0 0 6px;{f(14, 21, color=MUTED)}">{B.esc(e["note"])}</p>' if e["note"] else "")
                 + f'<a href="{B.esc(B.gcal_link(e))}" style="{f(13, 18, 700, color=GOLD, extra="text-decoration:none;")}">Add to Google Calendar</a>'
                 f'</td></tr>')
    more = (para(f'Showing the next {len(ev)} of {total} dates. <a href="{track(post_url, slug)}" style="color:{NAVY};text-decoration:underline">See them all in the full guide</a>.', 16, 14, 21, MUTED)
            if total > len(ev) else "")
    return (eyebrow("Coming up") + h2("Key dates to save")
            + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 18px">{rows}</table>'
            + more
            + button(post_url + "key-dates.ics", "Add all to my calendar", NAVY)
            + button(track(B.BASE + "/newsletter/#calendar", slug), "Subscribe to MFA tax dates", "#ffffff", NAVY, NAVY)
            + para("Works with Apple Calendar, Outlook and Google Calendar. The subscription updates itself when we add new deadlines.", 0, 13, 20, MUTED))


def services_block(p, slug):
    picks = services_for(p.get("category", ""))
    items = ""
    for k in picks:
        name, desc = SERVICES[k]
        items += (f'<tr><td width="22" valign="top" style="padding:3px 0 14px"><div style="width:8px;height:8px;background:{GOLDB};border-radius:2px;margin-top:6px;font-size:0;line-height:0">&nbsp;</div></td>'
                  f'<td valign="top" style="padding:0 0 14px"><p style="margin:0;{f(15, 23, color="#DCE2EA")}"><strong style="color:#ffffff;font-weight:700">{name}.</strong> {desc}</p></td></tr>')
    book = track(B.BOOK_URL.replace("/#book", "/#book"), slug)
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td bgcolor="{NAVY}" class="box" style="background:{NAVY};border-radius:10px;padding:36px 34px 28px">'
            + eyebrow("How MFA can help", GOLDB)
            + f'<h2 style="margin:0 0 14px;{f(25, 31, 400, SERIF, "#ffffff")}">{B.esc(p.get("ctaHeadline", "Want a second set of eyes before you act?"))}</h2>'
            + f'<p style="margin:0 0 22px;{f(16, 25, color="#DCE2EA")}">Merchant Financial Advisory helps individuals and small and mid-sized businesses in New Jersey, New York and nationwide get this right. In a 30-minute consultation we can talk through {B.esc(p.get("ctaTopic", "your situation"))}.</p>'
            + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 14px">{items}</table>'
            + button(book, "Book a consultation", GOLDB, NAVY)
            + button("mailto:" + B.EMAIL + "?subject=" + quote("Question: " + p["title"]), "Email our team", NAVY2, "#ffffff", "#3A5478")
            + "</td></tr></table>")


def more_articles(p, posts, slug):
    others = [x for x in posts if x["slug"] != slug][:2]
    if not others:
        return ""
    cells = ""
    for i, x in enumerate(others):
        u = track(f'{B.BASE}/blog/{x["slug"]}/', slug)
        pad = "padding:0 10px 0 0" if i == 0 else "padding:0 0 0 10px"
        cells += (f'<td class="stack" width="50%" valign="top" style="{pad}">'
                  f'<a href="{u}" style="text-decoration:none"><img src="{B.BASE}/blog/{x["slug"]}/og.png" width="242" alt="" class="fluid" style="display:block;width:100%;max-width:242px;height:auto;border:0;border-radius:6px;margin:0 0 12px"/></a>'
                  f'<p style="margin:0 0 6px;{f(11, 16, 700, color=GOLD, extra="letter-spacing:2px;text-transform:uppercase;")}">{B.esc(x["category"])}</p>'
                  f'<p style="margin:0 0 6px;{f(17, 23, 400, SERIF, NAVY)}"><a href="{u}" style="color:{NAVY};text-decoration:none">{B.esc(x["title"])}</a></p>'
                  f'<p style="margin:0 0 18px;{f(14, 21, color=MUTED)}">{B.esc(x["description"])}</p></td>')
    return (eyebrow("Also on MFA Insights") + h2("More articles you might find useful")
            + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>{cells}</tr></table>')


def build(slug, to_email=None, mailerlite=False):
    posts = B.load_posts()
    p = next((x for x in posts if x["slug"] == slug), None)
    if not p:
        sys.exit(f"No published post with slug '{slug}'")
    post_url = f"{B.BASE}/blog/{slug}/"
    read_url = track(post_url, slug)
    issue_url = f"{B.BASE}/newsletter/issues/{slug}/"
    unsub = "{$unsubscribe}" if mailerlite else (f"{B.BASE}/newsletter/unsubscribe/?e={quote(to_email)}" if to_email else f"{B.BASE}/newsletter/unsubscribe/")
    greeting = "Hi {$name|default('there')}," if mailerlite else "Hi there,"
    browser_url = "{$url}" if mailerlite else issue_url
    nice = p["dt"].strftime("%B %-d, %Y")
    asof = datetime.fromisoformat(p.get("factsAsOf", p["date"])).strftime("%B %-d, %Y")
    subject = p["title"]
    preheader = p["description"]
    glance, heads, faq, bottom = parts(p)
    share_li = f"https://www.linkedin.com/sharing/share-offsite/?url={quote(post_url, safe='')}"
    fwd = f"mailto:?subject={quote(p['title'])}&body={quote('Thought you might find this useful: ' + p['description'] + ' ' + post_url)}"
    # Keep Gmail/iOS from turning the postal address into a blue map link.
    addr_html = (f'<a href="{B.BASE}/" style="color:{MUTED};text-decoration:none">'
                 + B.esc(MAILING_ADDRESS).replace(" ", "&nbsp;", 1).replace(",", "&zwnj;,") + "</a>")

    glance_rows = "".join(
        f'<tr><td width="26" valign="top" style="padding:2px 0 14px">'
        f'<div style="width:18px;height:18px;border-radius:9px;background:{GOLDB};text-align:center;{f(11, 18, 700, color=NAVY)}">{i}</div></td>'
        f'<td valign="top" style="padding:0 0 14px 10px;{f(16, 25)}">{inline_rich(li)}</td></tr>'
        for i, li in enumerate(glance, 1))
    glance_block = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                    f'<td bgcolor="{PAPER2}" style="background:{PAPER2};border-radius:10px;border-left:4px solid {GOLD};padding:26px 26px 14px">'
                    + eyebrow("Executive summary")
                    + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{glance_rows}</table>'
                    + (f'<p style="margin:2px 0 12px;padding-top:14px;border-top:1px solid #E2D6B8;{f(16, 25)}">{inline_rich(bottom)}</p>' if bottom else "")
                    + "</td></tr></table>") if glance else ""

    cover = (f'<a href="{read_url}" style="text-decoration:none"><img src="{post_url}{p["cover"]}" width="504" alt="{B.esc(p.get("coverAlt", p["title"]))}" '
             f'style="display:block;width:100%;max-width:504px;height:auto;border:0;border-radius:8px;margin:0 0 16px"/></a>'
             + button(post_url + p["cover"], "Download the checklist", GOLDB, NAVY, size=14)
             + para("Save it to your phone or print it. It's yours to keep.", 0, 13, 20, MUTED)) if p.get("cover") else ""

    inside = ""
    if heads:
        lis = "".join(f'<tr><td width="20" valign="top" style="padding:0 0 10px;{f(16, 24, 700, color=GOLD)}">&#8226;</td>'
                      f'<td valign="top" style="padding:0 0 10px;{f(16, 24)}">{B.esc(h)}</td></tr>' for h in heads)
        inside = (eyebrow("In the full guide") + h2(B.esc(p["title"]) if len(p["title"]) < 60 else "What's inside")
                  + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 22px">{lis}</table>'
                  + button(read_url, "Read the full guide", NAVY, size=16)
                  + para(f'{p["minutes"]}-minute read on mfa-advisory.com, with every source linked.', 0, 13, 20, MUTED))

    faq_block = ""
    if faq:
        faq_block = (eyebrow("Reader question")
                     + f'<p style="margin:0 0 12px;{f(21, 29, 400, SERIF, NAVY)}">&ldquo;{B.esc(faq[0])}&rdquo;</p>'
                     + para(inline_rich(faq[1]), 14))

    rows = [
        # top bar
        f'<tr><td align="center" style="padding:0 0 14px;{f(12, 18, color=MUTED)}">{B.esc(B.NEWSLETTER_NAME)} &nbsp;|&nbsp; {nice} &nbsp;|&nbsp; <a href="{browser_url}" style="color:{MUTED};text-decoration:underline">View in browser</a></td></tr>',
        # masthead + hero
        f'''<tr><td bgcolor="{NAVY}" class="pad" style="background:{NAVY};border-radius:10px 10px 0 0;padding:30px 48px 40px">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
  <td width="54" valign="middle"><a href="{track(B.BASE + '/', slug)}"><img src="{B.BASE}/apple-touch-icon.png" width="42" height="42" alt="MFA" style="display:block;border:0;border-radius:9px"/></a></td>
  <td valign="middle"><span style="{f(20, 22, 400, SERIF, '#ffffff')}">Merchant</span><br/><span style="{f(9, 16, 700, color='#AEB8C6', extra='letter-spacing:3px;text-transform:uppercase;')}">Financial Advisory</span></td>
  <td align="right" valign="middle" style="{f(10, 14, 700, color=GOLDB, extra='letter-spacing:3px;text-transform:uppercase;')}">MFA Insights</td></tr></table>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:34px 0 0"><tr><td>
  {eyebrow(B.esc(p["category"]), GOLDB)}
  <h1 class="h1" style="margin:0 0 16px;{f(32, 40, 400, SERIF, '#ffffff')}">{B.esc(p["title"])}</h1>
  <p style="margin:0;{f(17, 27, color='#DCE2EA')}">{B.esc(p["dek"])}</p>
  </td></tr></table>
</td></tr>''',
        # greeting + intro
        section(f'<p style="margin:0 0 14px;{f(17, 26, 700, color=INK)}">{greeting}</p>' + para(B.esc(p.get("emailIntro", DEFAULT_INTRO)), 0, 17, 28), 40, 0, "#ffffff"),
        section(glance_block, 30, 0, "#ffffff") if glance_block else "",
        section(cover, 32, 0, "#ffffff") if cover else "",
        section(divider(36, 36) + inside, 0, 0, "#ffffff") if inside else "",
        section(divider(40, 36) + keydates_block(p, post_url, slug), 0, 0, "#ffffff"),
        section(divider(30, 36) + faq_block + para(f'<a href="{read_url}" style="color:{NAVY};text-decoration:underline;font-weight:700">More answers in the full guide</a>', 0, 15, 22), 0, 0, "#ffffff") if faq_block else "",
        section(divider(36, 0), 0, 0, "#ffffff"),
        section(services_block(p, slug), 36, 0, "#ffffff"),
        section(divider(40, 36) + more_articles(p, posts, slug), 0, 0, "#ffffff"),
        # share
        section(f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:22px 0 0"><tr><td bgcolor="{PAPER2}" align="center" style="background:{PAPER2};border-radius:10px;padding:26px 24px">
  <p style="margin:0 0 6px;{f(19, 26, 400, SERIF, NAVY)}">Know someone who'd find this useful?</p>
  <p style="margin:0 0 16px;{f(15, 23, color=MUTED)}">Forward this email, or share the article with your network.</p>
  {button(fwd, "Forward to a friend", "#ffffff", NAVY, NAVY, 14)}{button(share_li, "Share on LinkedIn", "#ffffff", NAVY, NAVY, 14)}
  </td></tr></table>''', 0, 44, "#ffffff"),
        # footer
        f'''<tr><td class="pad" align="center" style="padding:30px 48px 10px;{f(12, 19, color=MUTED)}">
  <p style="margin:0 0 4px;{f(15, 20, 400, SERIF, NAVY)}">Merchant Financial Advisory</p>
  <p style="margin:0 0 14px;{f(12, 19, color=MUTED)}">Accounting, tax and advisory for individuals and growing businesses</p>
  <p style="margin:0 0 14px;{f(12, 19, color=MUTED)}"><a href="{track(B.BASE + '/', slug)}" style="color:{NAVY};text-decoration:underline">mfa-advisory.com</a> &nbsp;|&nbsp; <a href="mailto:{B.EMAIL}" style="color:{NAVY};text-decoration:underline">{B.EMAIL}</a> &nbsp;|&nbsp; <a href="{track(B.BASE + '/newsletter/', slug)}" style="color:{NAVY};text-decoration:underline">Subscribe</a></p>
  <p style="margin:0 0 14px;{f(12, 19, color=MUTED)}">Facts checked against IRS and state sources as of {asof}; every source is linked in the online article. This email is general information, not tax, accounting, legal or financial advice, and reading it doesn't create a client relationship.</p>
  <p style="margin:0 0 6px;{f(12, 19, color=MUTED)}">You're receiving this because you subscribed to {B.esc(B.NEWSLETTER_NAME)} at mfa-advisory.com. <a href="{unsub}" style="color:{NAVY};text-decoration:underline;font-weight:700">Unsubscribe</a> &nbsp;|&nbsp; <a href="{B.BASE}/privacy.html" style="color:{MUTED};text-decoration:underline">Privacy</a></p>
  <p style="margin:0 0 24px;{f(12, 19, color=MUTED)}">Merchant Financial Advisory LLC &nbsp;|&nbsp; {addr_html}</p>
</td></tr>''',
    ]

    email = f'''<!doctype html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="x-apple-disable-message-reformatting"/><meta name="format-detection" content="telephone=no,address=no,email=no,date=no"/>
<title>{B.esc(subject)}</title>
<style>
body{{margin:0;padding:0;-webkit-text-size-adjust:100%}} img{{border:0;outline:none;text-decoration:none}}
@media (max-width:620px){{
 .wrap{{width:100%!important}} .pad{{padding-left:24px!important;padding-right:24px!important}}
 .h1{{font-size:27px!important;line-height:34px!important}}
 .stack{{display:block!important;width:100%!important;padding:0 0 10px 0!important}}
 .box{{padding:28px 22px 20px!important}} .fluid{{max-width:100%!important}}
}}
</style>
</head>
<body style="margin:0;padding:0;background:{PAPER}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;mso-hide:all">{B.esc(preheader)}&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{PAPER}" style="background:{PAPER}"><tr><td align="center" style="padding:24px 12px 32px">
<table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px">
{"".join(r for r in rows if r)}
</table></td></tr></table></body></html>'''
    # Round the bottom of the white card: the share section is its last white row.
    email = email.replace(f'<tr><td bgcolor="#ffffff" class="pad" style="background:#ffffff;padding:0px 48px 44px">',
                          f'<tr><td bgcolor="#ffffff" class="pad" style="background:#ffffff;border-radius:0 0 10px 10px;padding:0px 48px 44px">')

    # Plain-text alternative
    def strip(s):
        return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
    ev, total = upcoming_dates(p)
    plain = (f"{B.NEWSLETTER_NAME} | {nice}\n\n{p['title'].upper()}\n{p['dek']}\n\n"
             f"{greeting}\n\n"
             f"{strip(p.get('emailIntro', DEFAULT_INTRO))}\n\n"
             + ("EXECUTIVE SUMMARY\n" + "".join(f" {i}. {strip(li)}\n" for i, li in enumerate(glance, 1)) + (strip(bottom) + "\n" if bottom else "") + "\n" if glance else "")
             + f"Read the full guide: {read_url}\n\n"
             + ("KEY DATES\n" + "".join(f" - {datetime.fromisoformat(e['date']):%a, %b %-d, %Y}: {e['title']}\n" for e in ev)
                + f"Add them all: {post_url}key-dates.ics\n\n" if ev else "")
             + (f"READER QUESTION\n{faq[0]}\n{strip(faq[1])}\n\n" if faq else "")
             + f"HOW MFA CAN HELP\n{p.get('ctaHeadline', '')}\nBook a 30-minute consultation: {track(B.BOOK_URL, slug)}\nOr email {B.EMAIL}\n\n"
             f"General information, not tax advice. Facts checked as of {asof}.\n"
             f"Unsubscribe: {unsub}\nMerchant Financial Advisory LLC | {MAILING_ADDRESS}\n")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{slug}.email.html").write_text(email, encoding="utf-8")
    (OUT / f"{slug}.txt").write_text(plain, encoding="utf-8")
    web = B.SITE / "newsletter" / "issues" / slug
    web.mkdir(parents=True, exist_ok=True)
    web_html = (email.replace(unsub, f"{B.BASE}/newsletter/unsubscribe/").replace("{$url}", issue_url)
                .replace("Hi {$name|default('there')},", "Hi there,")
                .replace(addr_html, "Princeton, New Jersey")
                .replace("<head>", '<head><meta name="robots" content="noindex"/>', 1))
    assert "Spring St" not in web_html, "street address must never appear on the website"
    (web / "index.html").write_text(web_html, encoding="utf-8")
    meta = {"slug": slug, "subject": subject, "preheader": preheader, "post_url": post_url, "issue_url": issue_url,
            "html": str(OUT / f"{slug}.email.html"), "text": str(OUT / f"{slug}.txt"),
            "bytes": len(email.encode("utf-8")), "built": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (OUT / f"{slug}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    if meta["bytes"] > 100_000:
        print(f"  WARNING: email is {meta['bytes']} bytes; Gmail clips messages over ~102 KB")
    print(json.dumps(meta, indent=1))
    return meta


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    to = args[args.index("--to") + 1] if "--to" in args else None
    build(args[0], to, mailerlite="--mailerlite" in args)
