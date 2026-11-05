#!/usr/bin/env python3
"""Builds the private MFA Hub v2 shells in site/hub/ (hub.mfa-advisory.com).

The pages hold NO data: hub.js loads everything from /api/hub/* (Cloudflare D1) after the
site middleware has checked the Cloudflare Access login. noindex, no canonical, not linked
from anywhere on the public site, so tools/seo.py keeps them out of the sitemap and llms files.
"""
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
NAV = [("", "Home"), ("board/", "Board"), ("calendar/", "Calendar"), ("ads/", "Ads"), ("finance/", "Finance"),
       ("leads/", "Leads"), ("tasks/", "Tasks"), ("log/", "Live log")]

HEAD = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="robots" content="noindex,nofollow,noarchive"/><meta name="referrer" content="no-referrer"/>
<title>{title} | MFA Hub</title>
<link rel="icon" href="/favicon.png"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="/blog/blog.css"/><link rel="stylesheet" href="/hub/hub.css?v=10"/>
</head><body class="hub" data-page="{page}">
<header class="hub-top"><div class="wrap">
<a class="hub-brand" href="/hub/"><img src="/apple-touch-icon.png" alt=""/><b>MFA Hub</b><i>Private</i></a>
<nav class="hub-nav" aria-label="Hub">{nav}</nav>
<div class="hub-stat"><span class="hub-status" id="hubStatus" role="status" aria-live="polite">Loading…</span><button type="button" id="refresh">Refresh</button></div>
</div></header>
<div class="wrap"><main class="hub-main">
"""
FOOT = """</main></div>
<script src="/hub/hub_links.js?v=9"></script>
<script src="/hub/hub.js?v=10"></script>
</body></html>
"""


def pn(title, body_id, sub="", np=True, extra=""):
    return (f'<section class="pn"><div class="pn-h"><h2>{title}</h2><span class="sub" id="{body_id}Sub">{sub}</span>{extra}</div>'
            f'<div class="pn-b{" np" if np else ""}" id="{body_id}"></div></section>')


def chart(title, cid, sub=""):
    return pn(title, cid, sub, np=False)


PAGES = {
    "home": ("", "Home", f"""<div class="rbar" id="rbar"></div><div class="kpis" id="kpis"></div>
<div class="g4">{chart("Spend vs clicks · 7 days", "chSpend", "per ad platform")}{chart("Impressions · 7 days", "chImpr", "paid + organic")}{chart("Top 10 posts · 30 days", "chTop", "by impressions")}{chart("Leads per day · 30 days", "chLeads", "website forms")}</div>
<div class="g2 g-main">{pn("Needs you", "needs", "one click answers; Undo for 10 s")}{pn("Live log", "log", "", extra='<span class="sub" id="logUpd"></span>')}</div>
{pn("Ask the agents", "reqForm", "goes to Tasks", np=False)}
"""),
    "board": ("board/", "Agent Board", f"""<div class="rbar" id="rbar"></div><div class="kpis" id="kpis"></div>
{pn("Agents", "agents", "status, last run, next run, what blocks them")}
{pn("Needs you", "needs", "approvals and blocks from the agents")}
<div class="g2">{pn("Ideas", "ideas", "approve or comment on any row")}{pn("Activity · 30 days", "activity")}</div>"""),
    "calendar": ("calendar/", "Content Calendar", f"""<div class="rbar" id="rbar"></div><div class="kpis" id="kpis"></div>
<section class="pn"><div class="pn-h"><h2>Content matrix</h2><span class="sub" id="calMeta"></span></div>
<div class="slicers" id="slicers"></div><div class="tw tall" id="cal"></div></section>"""),
    "ads": ("ads/", "Ads Monitor", f"""<div class="rbar" id="rbar"></div>
{pn("Platforms · today and 7 days", "plat", "▲▼ vs prior 7 days")}
<div class="g2">{chart("Spend per day · 14 days", "chSpend", "paid platforms")}{chart("Impressions per day · 14 days", "chImpr", "all platforms")}</div>
{pn("Daily rows · 30 days", "daily")}"""),
    "finance": ("finance/", "Finance questions", f"""<div class="rbar" id="rbar"></div><div class="kpis" id="kpis"></div>
{pn("Ask Finance a question", "finAsk", "the Finance agent answers here", np=False)}
<div id="finFilter" hidden></div>
{pn("Transaction questions", "finTxn", "bank/card items: date, payee, amount, account")}
{pn("Other finance questions", "finOther", "decisions and setup not tied to one transaction")}"""),
    "leads": ("leads/", "Leads", f"""<div class="rbar" id="rbar"></div><div class="kpis" id="kpis"></div>
{pn("Leads", "leads", "names masked to first name + email domain")}"""),
    "tasks": ("tasks/", "Tasks", f"""{pn("New request", "reqForm", "the agents pick it up on their next run", np=False)}
{pn("Requests", "reqs")}
{pn("Everything you sent from the hub", "inputs", "comments and answers, with the agents' replies")}"""),
    "log": ("log/", "Live log", f"""<section class="pn"><div class="pn-h"><h2>Live log</h2><span class="sub" id="logUpd"></span>
<select class="fld" id="logAgent" aria-label="Agent"><option value="">All agents</option></select></div><div class="pn-b np" id="log"></div></section>"""),
}


def main():
    for page, (path, title, body) in PAGES.items():
        nav = "".join(f'<a href="/hub/{p}"{" aria-current=\"page\"" if p == path else ""}>{label}</a>' for p, label in NAV)
        html = HEAD.format(title=title, page=page, nav=nav) + body.replace(' style=""', "") + FOOT
        out = SITE / "hub" / path / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print("wrote", out.relative_to(SITE))


if __name__ == "__main__":
    main()
