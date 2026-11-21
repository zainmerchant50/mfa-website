#!/usr/bin/env python3
"""Builds the private MFA Hub v2 shells in site/hub/ (hub.mfa-advisory.com).

The pages hold NO data: hub.js loads everything from /api/hub/* (Cloudflare D1) after the
site middleware has checked the Cloudflare Access login. noindex, no canonical, not linked
from anywhere on the public site, so tools/seo.py keeps them out of the sitemap and llms files.
"""
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
# Zain 2026-11-16: "my focus is on operations not the finances" -> Finance left out of the menu (page still at /hub/finance/).
# v3 shell (Zain 2026-11-20: "i dont see everything and its not easily navigatable... too scattered... looks like a cheap
# knock off"): grouped left sidebar with live counts, one search box, every external board in one place, an
# Everything page that lists all items from every table. Finance stays reachable (Money group) but out of the way.
NAV_GROUPS = [
    ("Start here", [("", "Today", "home", None), ("all/", "Everything", "all", None)]),
    ("Clients", [("leads/", "Leads", "leads", "leads"), ("all/#type=deadline", "Deadlines", "-", "due7"), ("tasks/", "Requests", "tasks", "reqs")]),
    ("Marketing", [("calendar/", "Content calendar", "calendar", "posts7"), ("ads/", "Ads", "ads", None)]),
    ("Team", [("board/", "Agents", "board", "needs"), ("log/", "Live log", "log", None)]),
    ("Money", [("finance/", "Finance questions", "finance", None)]),
]
BOARDS = [("Agent Board", "https://claude.ai/artifact/7PGKtjMDLUPFLx2TKGPRnV"),
          ("Content Calendar", "https://claude.ai/artifact/MAVJc78qTBWyGdtBnaXtdd"),
          ("Social & Ads Daily", "https://claude.ai/artifact/Bbrv5AQuGdY1P8oBg3rVML"),
          ("Google Ads Monitor", "https://claude.ai/artifact/JAtVn9cFznHVcSJeup8PWM"),
          ("Finance Review", "https://claude.ai/artifact/92M5Pg4A1ArwvSeFjUerE4")]
NAV = [(path, label) for _, items in NAV_GROUPS for path, label, _, _ in items]   # kept for older tools
BLURB = {"home": "What needs you, what's due and what's going out.", "all": "Every deadline, lead, request, decision and post in one list.",
         "board": "What each agent is doing, what's blocked, and ideas waiting for you.", "calendar": "Every scheduled and published post, by channel.",
         "ads": "Paid and organic numbers, today and the last 7 days.", "finance": "Questions the Finance agent needs you to answer.",
         "leads": "Every lead, its stage and the next follow-up.", "tasks": "Ask the agents for something and see their replies.",
         "log": "Everything the agents did, newest first."}

HEAD = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="robots" content="noindex,nofollow,noarchive"/><meta name="referrer" content="no-referrer"/>
<title>{title} | MFA Hub</title>
<link rel="icon" href="/favicon.png"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="/blog/blog.css"/><link rel="stylesheet" href="/hub/hub.css?v=13"/>
</head><body class="hub v3" data-page="{page}">
<aside class="hs" id="hubSide" aria-label="Hub menu">
<a class="hs-brand" href="/hub/"><img src="/apple-touch-icon.png" alt=""/><span><b>MFA Hub</b><i>Private workspace</i></span></a>
<form class="hs-search" action="/hub/all/" method="get" role="search"><input type="search" name="q" id="hubQ" placeholder="Search everything…" aria-label="Search everything" autocomplete="off"/></form>
<nav class="hs-nav">{nav}</nav>
<div class="hs-grp"><span class="hs-gl">Boards</span>{boards}</div>
<div class="hs-grp" id="sideLinksGrp"><span class="hs-gl">Accounts</span><div id="sideLinks"></div></div>
</aside>
<div class="hs-scrim" id="hubScrim" hidden></div>
<div class="hw">
<header class="hh"><button type="button" class="hh-menu" id="hubMenu" aria-label="Open menu" aria-controls="hubSide" aria-expanded="false"><span></span><span></span><span></span></button>
<div class="hh-t"><h1>{title}</h1><p>{blurb}</p></div>
<div class="hub-stat"><span class="hub-status" id="hubStatus" role="status" aria-live="polite">Loading…</span><button type="button" id="refresh">Refresh</button></div>
</header>
<main class="hub-main">
"""
FOOT = """</main></div>
<script src="/hub/hub_links.js?v=11"></script>
<script src="/hub/hub.js?v=13"></script>
</body></html>
"""


def nav_html(cur_page):
    out = []
    for g, items in NAV_GROUPS:
        lis = "".join(f'<a href="/hub/{p}"{" aria-current=\"page\"" if pg == cur_page and "#" not in p else ""}><span>{label}</span>'
                      f'{f"<em class=\"cnt\" data-count=\"{c}\" hidden></em>" if c else ""}</a>' for p, label, pg, c in items)
        out.append(f'<div class="hs-grp"><span class="hs-gl">{g}</span>{lis}</div>')
    return "".join(out)


def pn(title, body_id, sub="", np=True, extra=""):
    return (f'<section class="pn"><div class="pn-h"><h2>{title}</h2><span class="sub" id="{body_id}Sub">{sub}</span>{extra}</div>'
            f'<div class="pn-b{" np" if np else ""}" id="{body_id}"></div></section>')


def chart(title, cid, sub=""):
    return pn(title, cid, sub, np=False)


PAGES = {
    "home": ("", "Today", f"""<div class="rbar" id="rbar" hidden></div><div class="kpis" id="kpis"></div>
<div class="g2 g-main today"><div class="stack">{pn("Needs you", "needs", "one click answers; Undo for 10 s")}{pn("Next 7 days · every channel", "chm", "click a cell for the posts · red = nothing scheduled")}{pn("Lead pipeline", "pipe", "by stage · days since first contact")}</div><div class="stack">{pn("Deadlines & follow-ups", "dls", "next 14 days · hover for notes")}{pn("Agents", "agl", "what each one is doing · last run")}</div></div>
<div class="g2 g-main">{pn("Niche lanes · next 14 days", "lanes", "posts per niche across channels")}{pn("Live log", "log", "", extra='<span class="sub" id="logUpd"></span>')}</div>
<details class="more-pn"><summary>Search &amp; AI visibility</summary>{pn("Search & AI visibility", "srch", "Google, Bing, AI assistants · updated by AI-SEO")}</details>
{pn("Ask the agents", "reqForm", "goes to Requests", np=False)}
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
<div id="finFilter" hidden></div><div class="confwrap" id="finConf" hidden></div>
{pn("Transaction questions", "finTxn", "bank/card items: date, payee, amount, account")}
{pn("Other finance questions", "finOther", "decisions and setup not tied to one transaction")}"""),
    "leads": ("leads/", "Leads", f"""<div class="rbar" id="rbar"></div><div class="kpis" id="kpis"></div>
{pn("Leads", "leads", "names masked to first name + email domain")}"""),
    "tasks": ("tasks/", "Tasks", f"""{pn("New request", "reqForm", "the agents pick it up on their next run", np=False)}
{pn("Requests", "reqs")}
{pn("Everything you sent from the hub", "inputs", "comments and answers, with the agents' replies")}"""),
    "all": ("all/", "Everything", f"""<div class="ev-bar" id="evBar"></div>{pn("All items", "ev", "deadlines, leads, decisions, requests, posts and agents")}"""),
    "log": ("log/", "Live log", f"""<section class="pn"><div class="pn-h"><h2>Live log</h2><span class="sub" id="logUpd"></span>
<select class="fld" id="logAgent" aria-label="Agent"><option value="">All agents</option></select></div><div class="pn-b np" id="log"></div></section>"""),
}


def main():
    boards = "".join(f'<a href="{u}" target="_blank" rel="noopener"><span>{t}</span><em class="ext-i">↗</em></a>' for t, u in BOARDS)
    for page, (path, title, body) in PAGES.items():
        html = HEAD.format(title=title, page=page, nav=nav_html(page), boards=boards, blurb=BLURB.get(page, "")) + body.replace(' style=""', "") + FOOT
        out = SITE / "hub" / path / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print("wrote", out.relative_to(SITE))


if __name__ == "__main__":
    main()
