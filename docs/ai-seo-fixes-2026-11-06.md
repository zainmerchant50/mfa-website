# AI crawler failures and SEO/AI-visibility fixes (Site, 2026-11-06)

Commits: `16118cc` (crawl fixes), `13d1228` (keywords, guide strips, post-to-service links, category pages, areaServed), `95d906d` (FAQs, HowTo, IndexNow, llms topics), plus this report. All three deployed; Cloudflare Pages check-run green.

## 1. Why crawlers "fail" (Cloudflare AI Crawl Control, Oct 31 to Nov 6)

Status mix of AI-crawler requests: 2.88k 200, 709 3xx (666 x 301, 11 x 302, 32 x 308), **992 x 404 and 59 x 403**. "Unsuccessful" in AI Crawl Control is the 4xx group. Nothing in robots.txt or AI Crawl Control blocks any bot.

| Cause | Evidence | Share | Fix |
|---|---|---|---|
| An assistant client polling the old WordPress MCP endpoint `/wp-json/wp/v2/wpmcp/streamable` | 251 requests, user agent Claude-User; we are not on WordPress | about a quarter of all 4xx; most of Claude-User's 290 | Now a tiny cacheable **410 Gone**. The real fix is removing the old connector (see 4.2) |
| Vulnerability scanners using AI user agents | `/.env`, `/.aws/credentials`, `/.git/`, `*.php`, `/proc/self/environ`, `docker-compose.yml`, `terraform.tfstate`... (218 distinct 4xx paths, ~150 of them probes) | most of the rest of the 404s | 410 for WordPress, PHP, dotfile and traversal probes; other unknown files keep the normal 404. These will always count as "unsuccessful", and should |
| Old WordPress pages | `/portfolio/*`, `/header/sticky-header/`, `/press/`, `/news/`, `/cms/`, `/wp/`, `/wordpress/`, `/services/book/keeping` | small | `/portfolio/` and `/header/` give 410; `/news` goes to `/blog/`, `/services/book/keeping` to `/services/#bookkeeping`, `/sitemap_index.xml` to `/sitemap.xml` |
| **Bot Fight Mode challenges (403)** | Security, Events: "Managed Challenge, Service: Bot fight mode" on a `PerplexityBot/1.0` user agent from AWS (`/tools/paycheck-tax-calculator/`), and on real pages like `/llc-formation/pa/`, `/year-end-tax-planning/` | 59 x 403 a week; this is why PerplexityBot shows 62 unsuccessful vs 16 allowed | Can't be fixed in the repo or with a WAF skip rule: Cloudflare docs say Bot Fight Mode "cannot be bypassed or skipped" by custom rules on the Free plan. Needs Zain's decision (4.1) |
| Our own redirects | Canonical, sitemap, llms.txt and 115 pages linked `/privacy.html`, `/terms.html`, `/disclaimer.html`; Cloudflare Pages 308-redirects those to the bare path | part of the 3xx | All now use `/privacy`, `/terms`, `/disclaimer` (canonical = served URL) |
| Missing `/favicon.ico` | 404 for every crawler and browser that asks | small | `site/favicon.ico` added |
| Brief image 404s | `/shop/img/*.webp` (5 files) requested by the Pinterest feed 14 minutes before the images were committed on Nov 4 | transient | Already fixed (all 200 now) |
| API GETs | `/api/svc-checkout`, `/api/llc-checkout` are POST-only and fell through to the HTML 404 | small | GET now returns a clean JSON 405 with `Allow: POST` |

No 5xx in the period. All real pages tested live return 200 (home, /llc-formation/, state pages, the ANCHOR post, tools, shop images).

## 2. What changed in the repo

- **Crawl hygiene:** `functions/_middleware.js` (410 for junk; unit test walks every file in `site/` to prove no real file matches), `_redirects` additions, bare legal URLs everywhere, favicon.ico, API 405s, a broken `/bookkeeping/` link in a post.
- **Guards in `tools/check_seo.py`:** canonical must equal the URL the file is served at; no internal links to `.html` URLs; no broken internal links; warning for links to `_redirects` sources; required JSON-LD fields per type (BlogPosting, Service, Offer price, FAQPage/Question/Answer, HowTo/HowToStep, BreadcrumbList, Product, WebApplication, Person); a service page that loses its guide strip fails the build.
- **Meta:** `<meta name="keywords">` on all 113 indexable pages, from each page's real topics (`seo.PAGE_KEYWORDS`; state pages generated per state). Blog posts add `article:tag` (one per keyword) and `article:author`. Titles (60 or fewer) and descriptions (155 or fewer) were already unique and in range; still enforced.
- **Internal links:** every blog post links a matching service page: 15 of 21 get a new "Related MFA service" line (map in `tools/build_blog.py`), the other 6 already linked theirs in the text, and every service, local and LLC state page has a "Guides on this topic" strip with 2 to 4 top guides (65 pages, `seo.PAGE_GUIDES`).
- **Category pages:** `/blog/category/tax-planning/`, `/tax-deadlines/`, `/bookkeeping/` (CollectionPage + ItemList + BreadcrumbList), linked from each post's breadcrumb, a "Filed under" line, the blog index topic pills and llms.txt. Keyword tags stay unlinked on purpose (one page per keyword would be dozens of thin pages).
- **Schema:** Organization (AccountingService) `areaServed` now leads with Princeton (City) and Mercer County, then NJ, NY, New York City, US; no street address. Person (Zain Merchant, ACCA) carries a description with only the facts on his author page (founder, formerly PwC New York); post authors carry the visible bio. Listing pages' BlogPosting nodes now have dateModified, author and image. Invalid `keywords` removed from 10 Service nodes (the schema.org vocabulary check failed on them).
- **Answer-first FAQs:** `/services/` (6 questions) and `/bookkeeping-cleanup/` (5) get visible accordions plus FAQPage; HowTo from the visible steps on `/llc-formation/` and `/bookkeeping-cleanup/`. Every answer restates facts already on the site.
- **IndexNow:** `tools/indexnow.py --send --wait --changed <sha>` sends just the changed indexable pages after a deploy; documented in `tools/skills/mfa-contentcreator/SKILL.md` as a step after every blog publish. The cloud sandbox can't reach api.indexnow.org, so the script prints GET links to open in Chrome when that happens.
- **llms.txt / llms-full.txt:** regenerated by every `build_blog.py` run (unchanged mechanism); they list every service page, local page, tool, product and article, now with the category pages and bare legal URLs.

## 3. Cloudflare changes

**None.** Everything in Cloudflare was read-only: AI Crawl Control (Metrics, Security), Security Events, Security Settings, Security rules. The only exception that would fix the 403s (letting AI bots past Bot Fight Mode) is not possible with a skip rule on the Free plan, so nothing was changed. Plan, billing and DNS untouched.

## 4. Needs Zain's yes

1. **Bot Fight Mode (Security, Settings, Bot traffic): keep it on, or turn it off?** It is the only thing returning 403s to AI crawlers (PerplexityBot most of all). It can't have exceptions on the Free plan. Turning it off lets Perplexity and other unverified assistants read the site; the trade-off is more scraper traffic, which matters little here (static site, the hub is behind Cloudflare Access, scanners get 404/410). Pro plan (Super Bot Fight Mode with skip rules) costs money. Recommendation: turn it off and recheck AI Crawl Control in a week; turning it back on is one switch.
2. **Remove the old WordPress MCP connector.** Something is calling `https://mfa-advisory.com/wp-json/wp/v2/wpmcp/streamable` as Claude-User about 35 times a day. That looks like an MCP connector set up for the old WordPress site in a Claude account or app (claude.ai Settings, Connectors, or a Claude Desktop config). It now gets 410 Gone; deleting the connector stops the noise.
3. **Email Address Obfuscation (Scrape Shield) is on.** Cloudflare rewrites some visible `info@mfa-advisory.com` links, so crawlers that don't run JavaScript read "[email protected]" there (the JSON-LD and llms.txt still carry the real address). Turning it off makes the email consistent for assistants; the trade-off is a little more spam.
4. **H1 wording (copy change):** `/services/` ("Services built to work together.") and `/llc-formation/` ("Form your LLC with an accountant, not a call center.") don't contain the words people search. Proposal: "Accounting, tax and bookkeeping services, built to work together." and "LLC formation in any state, with an accountant." Titles and descriptions already carry the keywords, so this is optional.
5. **Still open from the Oct 21 report:** the author bio says "QuickBooks ProAdvisor" and "over 10 years"; make sure that matches every other profile. "5.0 stars" on the home and local pages has no source on the page (say "5.0 on Fiverr and Upwork" with the count if that's what it is).

## 5. Schema coverage (after)

| Page type (count) | JSON-LD types | FAQ | Meta keywords | Other |
|---|---|---|---|---|
| Home (1) | AccountingService (full: areaServed Princeton/Mercer, NJ, NY, NYC, US; knowsAbout; sameAs x11; offers), WebSite, WebPage, Person, FAQPage | yes | yes | hours, ReserveAction |
| Services (1) | CollectionPage, OfferCatalog, Service x8 + Offer (public prices only), FAQPage, BreadcrumbList | **new** | **new** | guide strip |
| Offer pages: 1099, late return, quarterly, S corp, year-end, annual report (6) | Service + Offer (prices as on page), FAQPage, BreadcrumbList | yes | yes | guide strip **new** |
| LLC formation (1) + states (51) | Service + 3 Offers + add-on catalog, FAQPage, **HowTo** (main page); state: Service + Offer, FAQPage (the H1 question), BreadcrumbList | yes | **new** | guide strip **new** |
| Cleanup, intl students, artists (3) | Service + Offer/quote, FAQPage (**new** on cleanup), **HowTo** (cleanup), BreadcrumbList | yes | yes | guide strip **new** |
| Local pages (3) + Princeton bookkeeping (1) | AccountingService with local areaServed, Service + Offer, FAQPage, BreadcrumbList | yes | **new** | guide strip on the 3 local pages |
| Blog posts (21) | BlogPosting (author Person with bio, dateModified, citation, wordCount), FAQPage, BreadcrumbList (with category), Product where linked | yes | yes | article:tag **new**, service link **new** |
| Blog index, categories (1 + **3 new**), author (1) | Blog/CollectionPage/ItemList, ProfilePage + Person | n/a | yes | |
| Tools (13) | WebApplication, BreadcrumbList; Is It Deductible adds Dataset + FAQPage | 1 of 13 | **new** | Related on MFA strip |
| Shop, resources, book, newsletter, legal (8) | CollectionPage + Product/ItemList (shop), WebPage, BreadcrumbList, FAQPage (book) | book only | **new** | |

Validation: `python3 tools/check_seo.py --vocab schema-dts-2.1.0/package/dist/schema.d.ts` checks every block parses, every type and property exists in schema.org (1022 types), every `@id` resolves on its page, and the required fields above. 113 pages pass.

## 6. Tests

Before and after: `node tools/test_hub.mjs` (90 then 92 with the new junk-path tests), `python3 tools/check_ui.py` (115 then 118 pages), `python3 tools/check_seo.py` (110 then 113 pages, plus the vocabulary check), `python3 tools/check_catalog.py` (52 live). All builders run. Playwright at 1300 and 390 px: `/services/`, `/bookkeeping-cleanup/`, `/blog/category/tax-planning/`, `/blog/2027-tax-calendar/`, `/princeton-nj/`; no horizontal scroll, no page errors. New copy spell-checked with pyspellchecker.

Live, after deploy (Chrome on the Windows PC): `/services/`, `/bookkeeping-cleanup/`, `/llc-formation/`, `/blog/category/tax-planning/`, `/blog/2027-tax-calendar/`, `/princeton-nj/`, `/privacy` and `/` all 200, one JSON-LD block each that parses, FAQPage/HowTo where expected, meta keywords present, guide strips present, canonical = served URL. `/wp-json/wp/v2/wpmcp/streamable`, `/wp-login.php`, `/.env`, `/portfolio/business-growth/` answer 410; `/favicon.ico` 200; `/news/` redirects; `/api/svc-checkout` GET 405; `/privacy.html` redirects to `/privacy`; sitemap has 113 URLs, no `.html` legal URLs, includes the category pages. FAQ accordion on `/bookkeeping-cleanup/` renders and reveals on scroll.

IndexNow: all 114 changed URLs (113 pages + sitemap.xml) submitted Nov 6 from a Chrome tab on api.indexnow.org (the sandbox can't reach it): HTTP 200, accepted.
