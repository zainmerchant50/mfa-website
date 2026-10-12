#!/usr/bin/env python3
"""Build the MFA Insights newsletter email for one published post.

    python3 tools/build_newsletter.py <slug> [--to someone@example.com]   # Gmail copy to one person
    python3 tools/build_newsletter.py <slug> --mailerlite                  # list send via MailerLite ({$unsubscribe})

Writes:
    site/newsletter/issues/<slug>/index.html   "View in browser" copy (noindex), published with the site
    newsletter/out/<slug>.email.html           email-ready HTML (inline styles, 600px table layout)
    newsletter/out/<slug>.txt                  plain-text alternative
    newsletter/out/<slug>.json                 subject, preheader, paths (used by the publish job)

The email carries the full article (short version, cover graphic, tables, key dates with
add-to-calendar links), a CTA, a subscribe link (for forwards) and an unsubscribe link.
Placeholders an email service (ESP) can swap for its own merge tags:
    {{UNSUBSCRIBE_URL}}  per-recipient unsubscribe link  (default: our /newsletter/unsubscribe/?e=<email>)
Standard library only.
"""
import html, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_blog as B  # noqa: E402

OUT = B.ROOT / "newsletter" / "out"
NAVY, NAVY2, GOLD, GOLDB, PAPER2, INK, MUTED = "#10233F", "#1B3557", "#B08D3F", "#D8B769", "#F5F4EF", "#151515", "#5b5b5b"
SERIF = "Georgia,'Times New Roman',serif"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
# CAN-SPAM: every commercial email must show a valid physical postal address (a registered PO box or
# private mailbox is acceptable). Set this before mailing anyone other than Zain.
MAILING_ADDRESS = ""
UTM = "utm_source=newsletter&utm_medium=email&utm_campaign="


def absolutize(body, post_url, slug):
    def fix(m):
        attr, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            full = url
        elif url.startswith("/"):
            full = B.BASE + url
        else:
            full = post_url + url
        if full.startswith(B.BASE) and attr == "href" and not re.search(r"\.(png|ics|pdf)$", full):
            base, _, frag = full.partition("#")
            full = base + ("&" if "?" in base else "?") + UTM + slug + ("#" + frag if frag else "")
        return f'{attr}="{full}"'
    return re.sub(r'(href|src)="([^"]+)"', fix, body)


def style_body(body):
    """Inline the article's blog.css look so it renders in Gmail, Outlook and Apple Mail."""
    s = body
    s = re.sub(r'\s+download="[^"]*"', "", s)
    s = re.sub(r'<a class="dl"', '<a', s)
    # Short version box
    s = re.sub(r'<div class="tldr">(.*?)</div>',
               lambda m: (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 26px">'
                          f'<tr><td style="background:{PAPER2};border-left:3px solid {GOLD};padding:20px 22px">{m.group(1)}</td></tr></table>'),
               s, flags=re.S)
    # Figure
    s = re.sub(r'<figure class="figure">\s*(<img[^>]*>)\s*<figcaption>(.*?)</figcaption>\s*</figure>',
               lambda m: (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0 26px"><tr><td style="padding:0">'
                          + re.sub(r'\s(width|height)="\d+"', "", m.group(1)).replace(
                              "<img", f'<img width="552" style="display:block;width:100%;max-width:552px;height:auto;border:0;border-radius:10px"')
                          + f'<p style="margin:10px 0 0;font:13px/1.5 {SANS};color:{MUTED}">{m.group(2)}</p></td></tr></table>'),
               s, flags=re.S)
    # Tables
    s = s.replace('<table class="tbl">', f'<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:6px 0 24px;font:14px/1.5 {SANS}">')
    s = re.sub(r"<th>", f'<th align="left" style="background:{NAVY};color:#fff;padding:10px 12px;font-weight:600;font-size:13px">', s)
    s = re.sub(r"<td>", f'<td valign="top" style="padding:10px 12px;border-bottom:1px solid #e6e3da;color:{INK}">', s)
    s = re.sub(r"</?(thead|tbody)>", "", s)
    # Headings, text, lists
    s = re.sub(r"<h2>", f'<h2 style="margin:30px 0 12px;font:500 25px/1.2 {SERIF};color:{NAVY}">', s)
    s = re.sub(r"<h3>", f'<h3 style="margin:22px 0 6px;font:700 16px/1.4 {SANS};color:{NAVY}">', s)
    s = re.sub(r"<p>", f'<p style="margin:0 0 16px;font:16px/1.65 {SANS};color:{INK}">', s)
    s = re.sub(r"<ul>", f'<ul style="margin:0 0 18px;padding:0 0 0 22px;font:16px/1.6 {SANS};color:{INK}">', s)
    s = re.sub(r"<ol>", f'<ol style="margin:0 0 18px;padding:0 0 0 22px;font:16px/1.6 {SANS};color:{INK}">', s)
    s = re.sub(r"<li>", '<li style="margin:0 0 8px">', s)
    s = re.sub(r"<strong>", f'<strong style="color:{INK}">', s)
    s = re.sub(r'<a ([^>]*)href=', f'<a style="color:{NAVY};text-decoration:underline;text-decoration-color:{GOLDB}" \\1href=', s)
    # The short-version heading inside the box is smaller
    s = s.replace(f'<td style="background:{PAPER2};border-left:3px solid {GOLD};padding:20px 22px">\n  <h2 style="margin:30px 0 12px;font:500 25px/1.2 {SERIF};color:{NAVY}">',
                  f'<td style="background:{PAPER2};border-left:3px solid {GOLD};padding:20px 22px">\n  <h2 style="margin:0 0 10px;font:500 21px/1.2 {SERIF};color:{NAVY}">')
    return s


def btn(href, label, bg=NAVY, fg="#ffffff"):
    return (f'<a href="{href}" style="display:inline-block;background:{bg};color:{fg};text-decoration:none;'
            f'font:700 12px/1 {SANS};letter-spacing:.12em;text-transform:uppercase;padding:14px 22px;border-radius:999px;margin:4px 6px 4px 0">{label}</a>')


def keydates_email(p, post_url):
    ev = B.post_events(p)
    if not ev:
        return ""
    rows = "".join(
        f'<tr><td valign="top" style="padding:10px 12px 10px 0;border-bottom:1px solid #e6e3da;font:700 12px/1.5 {SANS};letter-spacing:.06em;text-transform:uppercase;color:{GOLD};white-space:nowrap">'
        f'{datetime.fromisoformat(e["date"]):%a, %b %-d, %Y}</td>'
        f'<td valign="top" style="padding:10px 0;border-bottom:1px solid #e6e3da;font:15px/1.5 {SANS};color:{INK}"><b style="color:{NAVY}">{B.esc(e["title"])}</b>'
        f'{("<br/>" + B.esc(e["note"])) if e["note"] else ""}<br/>'
        f'<a href="{B.esc(B.gcal_link(e))}" style="font-size:13px;color:{NAVY}">+ Add to Google Calendar</a></td></tr>' for e in ev)
    return f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:26px 0 8px;border:1px solid #e6e3da;border-top:3px solid {GOLD}">
<tr><td style="padding:20px 22px">
<h2 style="margin:0 0 10px;font:500 23px/1.2 {SERIF};color:{NAVY}">Save the key dates</h2>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table>
<p style="margin:16px 0 0">{btn(post_url + "key-dates.ics", "Add to my calendar (.ics)")}{btn("webcal://mfa-advisory.com/newsletter/mfa-key-dates.ics", "Subscribe to all MFA dates", "#ffffff", NAVY).replace("background:#ffffff", "background:#ffffff;border:1px solid " + NAVY)}</p>
<p style="margin:10px 0 0;font:12px/1.5 {SANS};color:{MUTED}">The .ics file works with Apple Calendar, Outlook and Google Calendar. The subscription updates itself whenever we publish a new deadline.</p>
</td></tr></table>'''


def build(slug, to_email=None, mailerlite=False):
    posts = B.load_posts()
    p = next((x for x in posts if x["slug"] == slug), None)
    if not p:
        sys.exit(f"No published post with slug '{slug}'")
    post_url = f"{B.BASE}/blog/{slug}/"
    track = f"?{UTM}{slug}"
    issue_url = f"{B.BASE}/newsletter/issues/{slug}/"
    if mailerlite:   # MailerLite swaps in each recipient's one-click unsubscribe link
        unsub = "{$unsubscribe}"
    else:
        unsub = (f"{B.BASE}/newsletter/unsubscribe/?e={quote(to_email)}" if to_email else "{{UNSUBSCRIBE_URL}}")
    nice = p["dt"].strftime("%B %-d, %Y")
    asof = datetime.fromisoformat(p.get("factsAsOf", p["date"])).strftime("%B %-d, %Y")
    subject = p["title"]
    preheader = p["description"]
    body = style_body(absolutize(p["body"], post_url, slug))
    sources = "".join(f'<li style="margin:0 0 6px"><a href="{B.esc(s["url"])}" style="color:{NAVY}">{B.esc(s["title"])}</a></li>' for s in p["sources"])
    addr = B.esc(MAILING_ADDRESS) if MAILING_ADDRESS else "Princeton, New Jersey"
    share_li = f"https://www.linkedin.com/sharing/share-offsite/?url={quote(post_url, safe='')}"
    fwd = f"mailto:?subject={quote(p['title'])}&body={quote(p['description'] + ' ' + post_url)}"

    email = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="x-apple-disable-message-reformatting"/><title>{B.esc(subject)}</title>
<style>@media (max-width:620px){{.wrap{{width:100%!important}}.pad{{padding-left:20px!important;padding-right:20px!important}}h1{{font-size:28px!important}}}}</style>
</head>
<body style="margin:0;padding:0;background:#ECEAE3">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent">{B.esc(preheader)}&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ECEAE3"><tr><td align="center" style="padding:20px 10px">
<table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:#ffffff">
<tr><td style="padding:10px 0 10px;background:#ECEAE3;font:12px/1.4 {SANS};color:{MUTED}" align="center">
  {B.esc(B.NEWSLETTER_NAME)} · {nice} · <a href="{issue_url}" style="color:{MUTED}">View in browser</a></td></tr>
<tr><td class="pad" style="background:{NAVY};padding:26px 40px 30px">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
  <td width="52" valign="middle"><a href="{B.BASE}/{track}"><img src="{B.BASE}/apple-touch-icon.png" width="44" height="44" alt="MFA" style="display:block;border:0;border-radius:10px"/></a></td>
  <td valign="middle" style="font:500 22px/1 {SERIF};color:#ffffff">Merchant<br/><span style="font:600 10px/1.8 {SANS};letter-spacing:.3em;text-transform:uppercase;color:rgba(255,255,255,.65)">Financial Advisory</span></td>
  <td align="right" valign="middle" style="font:700 10px/1 {SANS};letter-spacing:.3em;text-transform:uppercase;color:{GOLDB}">MFA Insights</td></tr></table>
  <p style="margin:28px 0 8px;font:700 11px/1 {SANS};letter-spacing:.28em;text-transform:uppercase;color:{GOLDB}">{B.esc(p["category"])}</p>
  <h1 style="margin:0 0 12px;font:500 32px/1.15 {SERIF};color:#ffffff">{B.esc(p["title"])}</h1>
  <p style="margin:0 0 18px;font:300 16px/1.6 {SANS};color:rgba(255,255,255,.82)">{B.esc(p["dek"])}</p>
  <p style="margin:0;font:13px/1.4 {SANS};color:rgba(255,255,255,.6)">By {B.esc(B.AUTHOR["name"])}, {B.esc(B.AUTHOR["credential"])} · {p["minutes"]} min read</p>
</td></tr>
<tr><td class="pad" style="padding:32px 40px 8px">
{body}
{keydates_email(p, post_url)}
</td></tr>
<tr><td class="pad" style="padding:8px 40px 28px">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{NAVY}"><tr><td style="padding:26px 26px 22px">
  <p style="margin:0 0 6px;font:700 11px/1 {SANS};letter-spacing:.28em;text-transform:uppercase;color:{GOLDB}">Talk to MFA</p>
  <p style="margin:0 0 10px;font:500 24px/1.2 {SERIF};color:#ffffff">{B.esc(p.get("ctaHeadline", "Want a second set of eyes before you act?"))}</p>
  <p style="margin:0 0 16px;font:15px/1.6 {SANS};color:rgba(255,255,255,.8)">Book a free 30-minute consultation to talk through {B.esc(p.get("ctaTopic", "your situation"))}, or just reply to this email.</p>
  {btn(B.BOOK_URL.replace("/#book", "/" + track + "#book"), "Book a consultation", GOLDB, NAVY)}{btn("mailto:" + B.EMAIL + "?subject=" + quote(p["title"]), "Email us", NAVY2)}
  </td></tr></table>
  <p style="margin:22px 0 6px;font:14px/1.6 {SANS};color:{INK}">Read it on the web: <a href="{post_url}{track}" style="color:{NAVY}">{post_url}</a><br/>
  Know someone who needs this? <a href="{fwd}" style="color:{NAVY}">Forward it</a> or <a href="{share_li}" style="color:{NAVY}">share on LinkedIn</a>.</p>
  <p style="margin:18px 0 6px;font:700 12px/1 {SANS};letter-spacing:.12em;text-transform:uppercase;color:{MUTED}">Sources</p>
  <ul style="margin:0 0 12px;padding:0 0 0 18px;font:13px/1.5 {SANS};color:{MUTED}">{sources}</ul>
  <p style="margin:0;font:12px/1.6 {SANS};color:{MUTED}">Facts checked against the sources above as of {asof}. This email is general information, not tax, accounting, legal or financial advice, and reading it doesn't create a client relationship.</p>
</td></tr>
<tr><td class="pad" style="background:{PAPER2};padding:24px 40px;font:12px/1.7 {SANS};color:{MUTED}" align="center">
  <b style="color:{NAVY}">Was this forwarded to you?</b> <a href="{B.BASE}/newsletter/{track}" style="color:{NAVY}">Subscribe to {B.esc(B.NEWSLETTER_NAME)}</a> for free: new articles, key tax dates and a savable calendar.<br/><br/>
  You're receiving this because you subscribed to {B.esc(B.NEWSLETTER_NAME)} at mfa-advisory.com.<br/>
  <a href="{unsub}" style="color:{NAVY};font-weight:600">Unsubscribe</a> · <a href="{B.BASE}/privacy.html" style="color:{MUTED}">Privacy</a> · <a href="{B.BASE}/{track}" style="color:{MUTED}">mfa-advisory.com</a><br/>
  Merchant Financial Advisory LLC · {addr} · (347) 205-4468 · {B.EMAIL}
</td></tr>
</table></td></tr></table></body></html>'''

    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", p["body"], flags=re.S)
    text = re.sub(r"<li[^>]*>", "\n - ", text)
    text = re.sub(r"<(h2|h3)[^>]*>(.*?)</\1>", lambda m: "\n\n" + m.group(2).upper() + "\n", text, flags=re.S)
    text = re.sub(r"<tr[^>]*>", "\n", text)
    text = re.sub(r"</t[dh]>", " | ", text)
    text = re.sub(r"<p[^>]*>", "\n\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    text = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()
    kd = "".join(f"\n - {datetime.fromisoformat(e['date']):%a, %b %-d, %Y}: {e['title']}" for e in B.post_events(p))
    plain = (f"{B.NEWSLETTER_NAME} · {nice}\n\n{p['title'].upper()}\n{p['dek']}\n\n{text}\n"
             + (f"\nKEY DATES{kd}\nAdd to calendar: {post_url}key-dates.ics\n" if kd else "")
             + f"\nRead on the web: {post_url}\nBook a consultation: {B.BOOK_URL}\n\n"
             f"General information, not tax advice. Facts checked as of {asof}.\n"
             f"Unsubscribe: {unsub}\nMerchant Financial Advisory LLC · {MAILING_ADDRESS or 'Princeton, New Jersey'} · {B.EMAIL}\n")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{slug}.email.html").write_text(email, encoding="utf-8")
    (OUT / f"{slug}.txt").write_text(plain, encoding="utf-8")
    web = B.SITE / "newsletter" / "issues" / slug
    web.mkdir(parents=True, exist_ok=True)
    (web / "index.html").write_text(
        email.replace(unsub, f"{B.BASE}/newsletter/unsubscribe/").replace("<head>", '<head><meta name="robots" content="noindex"/>', 1),
        encoding="utf-8")
    meta = {"slug": slug, "subject": subject, "preheader": preheader, "post_url": post_url, "issue_url": issue_url,
            "html": str(OUT / f"{slug}.email.html"), "text": str(OUT / f"{slug}.txt"),
            "bytes": len(email.encode("utf-8")), "built": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (OUT / f"{slug}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    if meta["bytes"] > 100_000:
        print(f"  WARNING: email is {meta['bytes']} bytes; Gmail clips messages over ~102 KB")
    if not MAILING_ADDRESS:
        print("  NOTE: MAILING_ADDRESS is empty. Set a postal address (PO box is fine) before mailing real subscribers (CAN-SPAM).")
    print(json.dumps(meta, indent=1))
    return meta


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    to = args[args.index("--to") + 1] if "--to" in args else None
    build(args[0], to, mailerlite="--mailerlite" in args)
