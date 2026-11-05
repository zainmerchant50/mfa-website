#!/usr/bin/env python3
"""Builds the private MFA Hub shells in site/hub/ (hub.mfa-advisory.com).

The pages hold NO data: hub.js loads everything from /api/hub/* (Cloudflare D1) after the
site middleware has checked the Cloudflare Access login. noindex, no canonical, not linked
from anywhere on the public site, so tools/seo.py keeps them out of the sitemap and llms files.
"""
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
NAV = [("", "Home"), ("board/", "Agent Board"), ("calendar/", "Calendar"), ("ads/", "Ads"), ("finance/", "Finance")]

HEAD = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="robots" content="noindex,nofollow,noarchive"/><meta name="referrer" content="no-referrer"/>
<title>{title} | MFA Hub</title>
<link rel="icon" href="/favicon.png"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="/blog/blog.css"/><link rel="stylesheet" href="/hub/hub.css?v=1"/>
</head><body class="hub" data-page="{page}">
<header class="hub-top"><div class="wrap">
<a class="hub-brand" href="/hub/"><img src="/apple-touch-icon.png" alt=""/><span><b>MFA Hub</b><i>Private</i></span></a>
<nav class="hub-nav" aria-label="Hub">{nav}</nav>
</div></header>
<div class="wrap">
<div class="hub-head"><span class="eyebrow">{eyebrow}</span><h1>{h1}</h1><p>{lead}</p>
<p class="hub-status" id="hubStatus" role="status" aria-live="polite">Loading…</p></div>
<main class="hub-main">
"""
FOOT = """</main></div>
<script src="/hub/hub.js?v=1"></script>
</body></html>
"""

PAGES = {
    "home": ("", "Home", "Merchant Financial Advisory", "Your <em>MFA Hub</em>",
             "Everything the agents are doing, in one private place. Comments and answers you leave here go straight to the agents.",
             """<section class="hub-sec"><div class="tiles" id="tiles"></div></section>
<section class="hub-sec"><h2>Agent replies</h2><p class="muted" id="ccount"></p><div class="grid" id="replies"></div></section>
"""),
    "board": ("board/", "Agent Board", "Agents", "Agent <em>Board</em>",
              "Each agent's status, what needs you, the ideas list and recent activity. Leave a comment on any card and the agent acts on it next run.",
              """<section class="hub-sec"><h2>Needs you</h2><div class="grid" id="needs"></div></section>
<section class="hub-sec"><h2>Agents</h2><div class="grid" id="agents"></div></section>
<section class="hub-sec"><h2>Ideas to grow MFA</h2><div class="chips" id="ideaChips" role="group" aria-label="Filter ideas"></div><div class="grid" id="ideas" style=""></div></section>
<section class="hub-sec"><h2>Recent activity</h2><div class="grid" id="activity"></div></section>
"""),
    "calendar": ("calendar/", "Content Calendar", "Content", "Content <em>Calendar</em>",
                 "Every post, pin, video, blog and newsletter with its time (ET) and results. Comment on any item to change it.",
                 """<section class="hub-sec"><div class="calhead"><div class="chips" role="group" aria-label="View">
<button class="chip" type="button" id="vMonth">Month</button><button class="chip" type="button" id="vList">List</button></div></div></section>
<section class="hub-sec" id="monthBox"><div class="calhead"><button class="hbtn line" type="button" id="prevM" aria-label="Previous month">&larr;</button>
<h2 id="monthLabel"></h2><button class="hbtn line" type="button" id="nextM" aria-label="Next month">&rarr;</button></div>
<div class="cal" id="calGrid"></div></section>
<section class="hub-sec"><h2 id="calListHead"></h2><div class="grid" id="calItems"></div></section>
"""),
    "ads": ("ads/", "Ads Monitor", "Paid and organic", "Ads <em>Monitor</em>",
            "All platforms: today and the last 7 days, from the analytics runs. Comment on a platform to ask for a change; spend changes still need your yes.",
            """<section class="hub-sec"><div class="kpis"><div class="kpi"><span>7-day impressions</span><b id="kImp">—</b></div>
<div class="kpi"><span>7-day clicks</span><b id="kClk">—</b></div><div class="kpi"><span>7-day spend</span><b id="kSp">—</b></div></div></section>
<section class="hub-sec"><h2>By platform</h2><div class="tblwrap"><table class="tbl"><thead><tr><th>Platform</th><th class="num">Today impr / clicks</th>
<th class="num">7d impr</th><th class="num">7d clicks</th><th class="num">CTR</th><th class="num">7d spend</th><th class="num">CPC</th><th class="num">Conv.</th></tr></thead>
<tbody id="adsBody"></tbody></table></div></section>
<section class="hub-sec"><h2>Last 14 days</h2><div class="tblwrap"><table class="tbl"><thead><tr><th>Day</th><th>Platform</th><th>Campaign</th>
<th class="num">Impr</th><th class="num">Clicks</th><th class="num">Spend</th><th class="num">Conv.</th></tr></thead><tbody id="dailyBody"></tbody></table></div></section>
"""),
    "finance": ("finance/", "Finance questions", "Finance", "Finance <em>questions</em>",
                "Bank-feed items Finance needs you to label. Type your answer (business or personal, account, purpose) and save; Finance posts it to QuickBooks on its next run.",
                """<section class="hub-sec"><div class="chips" id="finChips" role="group" aria-label="Filter questions"></div></section>
<section class="hub-sec"><div class="grid" id="fin"></div></section>
"""),
}


def main():
    for page, (path, title, eyebrow, h1, lead, body) in PAGES.items():
        nav = "".join(f'<a href="/hub/{p}"{" aria-current=\"page\"" if p == path else ""}>{label}</a>' for p, label in NAV)
        html = HEAD.format(title=title, page=page, nav=nav, eyebrow=eyebrow, h1=h1, lead=lead) + body.replace(' style=""', "") + FOOT
        out = SITE / "hub" / path / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print("wrote", out.relative_to(SITE))


if __name__ == "__main__":
    main()
