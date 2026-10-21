# SEO and AI-discovery report (branch `draft/seo-ai`, 2026-10-21)

Goal (Zain, 2026-10-21): every page, product and tool should be optimized for search engines and for AI assistants and agents, so people and agents looking for bookkeepers, tax preparers, small-business accounting help or tax tools in NJ and NYC (or online) find and recommend MFA.

Short version: the site was already in decent shape (every page had a canonical, titles, Open Graph tags and some JSON-LD, robots.txt allowed the AI bots, llms.txt existed). The work was making the facts consistent and complete on every page and in machine-readable files, fixing the homepage canonical, and listing the things only Zain can do. The biggest levers for being recommended are off-site (Google Business Profile, Bing Webmaster Tools, directory listings, real reviews); see section 6.

## 1. Research: how assistants find and choose providers (2026)

| Topic | What the sources say | What we did |
|---|---|---|
| Google AI Overviews and AI Mode | Google: "There are no additional requirements to appear in AI Overviews or AI Mode, nor other special optimizations necessary." No special schema, no AI text files needed; the page must be indexed and snippet-eligible. Standard SEO, crawlable, good internal links, text content. [1] | Fixed basics (canonical, unique titles/descriptions, internal links, sitemap). Structured data kept strictly matching visible content. |
| ChatGPT search | OpenAI lists `OAI-SearchBot` (surfaces sites in ChatGPT search; allow it to appear), `GPTBot` (model training), `ChatGPT-User` (user-initiated fetches; robots.txt may not apply). Settings are independent. [2] Several vendor articles say ChatGPT search leans on Bing's index; this is not confirmed in OpenAI's own page, so treat as likely but unproven. [7] | All three allowed explicitly. Bing Webmaster Tools and IndexNow set up (key file and script included; verification is Zain's step). |
| Claude | Anthropic lists `ClaudeBot` (training), `Claude-User` (fetch when a user asks), `Claude-SearchBot` (search indexing); blocking SearchBot or User "may reduce visibility". All honor robots.txt. [3] | All three allowed explicitly. |
| Perplexity | `PerplexityBot` surfaces and links sites in results (allow it); `Perplexity-User` is user-initiated and "generally ignores robots.txt". [4] | Both listed. |
| Microsoft Copilot and Bing | Bing launched an AI Performance report in Bing Webmaster Tools (public preview 2026-02-10) showing citations in Copilot and Bing AI answers. Bing recommends IndexNow and fresh content. [8] | `tools/indexnow.py` and key file. Zain verifies the site in Bing Webmaster Tools to see the report. |
| Apple | `Applebot` powers Siri, Spotlight and Safari suggestions; `Applebot-Extended` only controls training use. If robots.txt does not mention Applebot it follows Googlebot rules. [6] | `Applebot` and `Applebot-Extended` listed. |
| DuckDuckGo | `DuckAssistBot` is DuckDuckGo's AI-answer crawler (DuckDuckGo help page; found via search, not fetched). | Listed. |
| `llms.txt` | Proposed in Sept 2024. As of 2025-2026 no major AI provider says it uses it, and Google says it does not need AI-specific files. Some developer tools and agents do read it. [5] [1] | Kept and extended (cheap, harmless, generated from the same data as the pages). Treat as low priority, not a ranking lever. `llms-full.txt` generated too, same caveat. |
| Schema.org | Google's LocalBusiness guidance: `address` and `name` required; `priceRange`, `telephone`, `url`, `openingHoursSpecification` recommended. [9] FAQ rich results were removed from Google Search (feature stopped May 7, 2026; docs removed June 15, 2026). [10] FAQPage markup is still valid schema.org and still gives assistants clean question-answer pairs, so it stays where the FAQ is visible. | JSON-LD on every indexable page (section 3). No `aggregateRating` or `review` markup. |
| Local presence | Google Business Profile: a business that does not serve customers at its address must remove the address and list a service area; hybrid or storefront listings need permanent signage. [11] | Because MFA publishes no street address, a service-area profile is the right type (section 6). |
| Agentic commerce | Google's Universal Commerce Protocol (UCP) and OpenAI's Agentic Commerce Protocol (ACP) let agents browse and buy from merchants that supply product feeds (Google Merchant Center data) and checkout integrations; the merchant stays seller of record. Sources are secondary and focus on physical goods. [12] | Does not apply to a Gumroad-hosted shop: Gumroad owns checkout and the product pages, and MFA cannot expose ACP/UCP endpoints. What does apply: accurate Product/Offer markup on `/shop/` and `/catalog.json`, which agents and crawlers can read. Revisit if Gumroad announces ACP/UCP support, or if the shop ever moves to Shopify/Stripe-hosted product pages. |
| Cloudflare | Cloudflare changed its AI-crawler defaults on 2026-07-01: from 2026-09-15 new domains block "Agent" and "Training" bots by default on pages that show ads; search bots stay allowed; the bot policy panel can override robots.txt. [13] (secondary source) | Zain should check the Cloudflare AI bot settings (section 6, action 2). The live site could not be reached from this sandbox, so bot access was not tested end to end. |

## 2. Audit of the repo and site (before)

90 indexable pages. Findings:

- Homepage canonical and `og:url` pointed to `https://www.mfa-advisory.com/` (www 301s to apex). Fixed.
- 79 of 90 titles were over 60 characters (blog posts up to 94, state LLC pages up to 85) and 75 descriptions were over 155 (blog index 248, home 209).
- No page had `twitter:title` or `twitter:description`; the homepage had no `og:image`; the three local pages had no `twitter:card` at all.
- Homepage JSON-LD: `areaServed` was only "US", no `@id`, no WebSite, no FAQ although the FAQ is visible, no offers or prices, no contact point. Other builders each wrote their own partial organization node with different `@id`s (`#org`) or none, so the entity was not consistent.
- Missing JSON-LD entirely: blog index, newsletter, legal pages, 5 pages in total. BreadcrumbList missing on resources, local pages and the homepage graph.
- Sitemap had all 90 URLs but every `lastmod` was the build date for the home, local pages and `site_pages.json` URLs, which teaches crawlers to ignore it. `robots.txt` lacked `Claude-User`, `Perplexity-User`, `Googlebot`, `Applebot`, `DuckAssistBot`.
- The three local pages (`/princeton-nj/`, `/union-city-nj/`, `/new-york-ny/`) had zero inbound links from any page in the site (only the sitemap and `llms.txt`).
- Shop product images had empty `alt` text.
- `llms.txt` listed only the home page, two of the three local pages, blog and author, with no services, prices, tools or products.
- Tool pages linked to a CTA but not to the matching service, shop product or guide.
- Not changed (noted): the homepage requests up to 11 font styles from Google Fonts (Cormorant Garamond x6, Inter x5) and has a splash loader; blog and tool pages request up to 8. `og:image` on every page except blog posts is the 180x180 app icon.

## 3. What changed

New shared module `tools/seo.py` (standard library only), called by all builders:

- **JSON-LD on every indexable page** as one `@graph`: the firm as `AccountingService` with a single stable `@id` (`https://mfa-advisory.com/#organization`), `WebSite`, the page itself (`WebPage`, `CollectionPage`, `ProfilePage`), `BreadcrumbList`, plus the page's own node. Every `@id` reference resolves inside its page.
  - Firm: name, legal name, phone (+13472054468), email, `address` = Princeton, NJ only (no street), `areaServed` (NJ, NY, New York City, US), `knowsAbout`, `knowsLanguage` (en, hi, ur), `priceRange` "From $150", `contactPoint`, `ReserveAction` to the booking section, `sameAs` (LinkedIn company, Instagram, Upwork, Fiverr, Gumroad store), `founder` -> Zain.
  - Public prices as `Offer`s with `price` in USD: LLC formation $150 / $249 / $649 plus state fee, monthly bookkeeping from $199/month, quarterly estimated tax service $250/year, 1099 preparation $25/form ($75 minimum), sales tax registration $99, S corp election $149. Cleanup, tax preparation, tax planning, financial reporting, CFO, audit support and technical accounting are marked "quoted up front" (no price). The unconfirmed bookkeeping step-ups (+$50 per account, +$100 for 101-200 transactions) are not published anywhere.
  - Person: Zain Merchant, `honorificSuffix` "ACCA", `memberOf` ACCA, Founder & Principal. No years of experience, no employer history, no other credentials.
  - Pages: home (adds the visible FAQ as `FAQPage`, regenerated at build time between `<!--seo:jsonld-->` markers so it cannot drift), `/services/` (one `Service` per service, with price or "quoted"), `/llc-formation/` (`Service` + 3 offers + add-ons catalog + FAQ), 51 state pages (`Service` for that state), `/bookkeeping-cleanup/`, `/shop/` (`ItemList` of `Product` with `Offer`, `sku`, `seller`, return policy "not permitted" matching "All sales final", format and delivery), `/resources/` (`CollectionPage` + `ItemList`), 12 tools (`WebApplication`, offer price 0, publisher), blog posts (`BlogPosting` with `citation` list from the article's sources, `wordCount`, `articleSection`, `isPartOf` Blog, FAQ), blog index, newsletter, author page, legal pages, the 3 local pages (areaServed = that area, FAQ).
- **Head tags** (`head()` in `tools/build_blog.py`, home page, landing pages): `robots` meta with `max-image-preview:large,max-snippet:-1`, `og:locale`, `twitter:title`, `twitter:description` on every page; homepage canonical and `og:url` now `https://mfa-advisory.com/`; homepage `og:image` added.
- **Titles and descriptions**: all 90 indexable pages now have a unique title of 60 characters or fewer and a unique description of 155 or fewer. Blog posts keep their own headline and card text; the search-engine versions live in `tools/seo_overrides.json` (the build prints a warning when a new post needs one). Local pages: "Bookkeeping & Tax Preparation in Princeton, NJ | MFA" and so on.
- **Root files** (all generated, so they cannot go stale): `sitemap.xml` (auto-discovers every indexable page from its canonical tag; `lastmod` from git history, or today when the file has uncommitted changes; blog posts use their own date), `robots.txt` (every search, AI-search, user-fetch and training bot allowed explicitly, with comments saying which is which), `llms.txt` (who, services and public prices, local pages, tools, shop products with prices, about, articles), `llms-full.txt` (adds service detail, LLC packages, a state fee table, products, FAQ), `catalog.json` (schema.org `DataFeed` of services with prices, LLC packages, tools and shop products for agents).
- **Internal links**: `/services/` now links to the three local pages, LLC formation, cleanup quote, shop, resources, blog and the author page; each local page links to the other two and to services, LLC formation, resources and shop in its footer row; each tool page gets a "Related on MFA" strip (service, shop product, guide) via `seo.RELATED`.
- **Images**: shop product images now have descriptive alt text.
- **Headers**: `site/_headers` serves `llms.txt`, `llms-full.txt` and `catalog.json` with explicit types and `Access-Control-Allow-Origin: *`.
- **IndexNow**: key file `site/<key>.txt` and `tools/indexnow.py` (dry run by default; `--send` after deploy).
- **Guard**: `tools/check_seo.py` fails the build on titles/descriptions out of range or duplicated, missing or extra canonical or h1, www canonicals, missing OG/Twitter tags, JSON-LD that does not parse or has unresolved `@id`s, ratings markup, sitemap gaps, robots.txt bot coverage, broken `llms.txt` links, and banned wording in machine-readable output. With `--vocab` it also validates every JSON-LD type and property against schema.org (schema-dts 2.1.0); the build passes that check.
- Visible copy was not changed. Additions to visible text are navigation only: the "Related on MFA" strip, the "Local pages and related pages" link row on `/services/`, and extra footer links on the local pages.

Before/after: titles over 60: 79 -> 0; descriptions over 155: 75 -> 0; pages with JSON-LD 85 -> 90; pages with `twitter:title` 0 -> 90; `www` references 1 -> 0.

## 4. NAP consistency and the no-street-address trade-off

Name: "Merchant Financial Advisory LLC" (MFA). Phone: (347) 205-4468 (one visible format on every page; +13472054468 in structured data). Email: info@mfa-advisory.com. Location: "Princeton, New Jersey". All consistent across pages, JSON-LD, llms files and the catalog. No street address appears in `site/`. The only address in the repo is the newsletter mailing address in `tools/build_newsletter.py` (needed in marketing emails; it is not published on the site).

Trade-offs of publishing no street address:
1. No Google Maps storefront or local-pack listing tied to a location; Google Business Profile has to be a service-area business with the address hidden (Google's rule for businesses that do not serve customers at their address) [11].
2. Weaker "near me" signals for Princeton; the 347 phone number is a New York City area code. A local 609 number forwarded to the same line would give a Princeton signal if the number is ever changed, but NAP must stay identical everywhere, so change it everywhere at once or not at all.
3. Structured data cannot include `streetAddress`; locality and region only. That is valid, and the rest of the profile (areaServed, sameAs, phone) carries the entity.

## 5. Changes for other work streams and proposals for Zain (not applied)

For the footer / is-it-deductible agents (I did not touch `FOOT`, nav or `/tools/is-it-deductible/`):
- The footer should link to `/llc-formation/`, `/princeton-nj/`, `/union-city-nj/`, `/new-york-ny/`, `/bookkeeping-cleanup/` and `/authors/zain-merchant/` (the local pages are linked only from `/services/` and other local pages today). The site nav has no LLC formation link.
- New tool pages should use `build_resources.tool_ld(...)` and `page(...)`, a title of 60 characters or fewer with " | MFA", a description of 155 or fewer, and add their slug to `seo.RELATED` in `tools/seo.py` (service, shop product, guide). They are picked up automatically by the sitemap, `llms.txt`, `llms-full.txt` and `catalog.json` on the next `build_blog.py` run. `tools/check_seo.py` will tell them if anything is off.
- `tools/site_pages.json` is no longer needed for the sitemap (pages are discovered from the built files); leave it alone to avoid merge conflicts.
- Merge note: `tools/build_blog.py` conflicts should be limited to the `head()` function and the author/index/newsletter builders; `FOOT` is untouched.

Copy proposals for Zain (public claims need his yes; none applied):
1. `/authors/zain-merchant/` says "certified QuickBooks ProAdvisor" and "eight years" at Big Four firms; the project rules avoid "certified", and other profiles of Zain may state a different number of years; whichever number is public should be the same everywhere. Also `AUTHOR["bio"]` in `tools/build_blog.py` repeats "QuickBooks ProAdvisor with eight years of Big Four audit and tax experience". JSON-LD avoids both claims for now.
2. "5.0 stars" / "Five stars, client after client": the home page `og:description`, the home reviews heading and the landing pages say this. If it refers to Upwork/Fiverr ratings, say so on the page (for example "5.0 on Fiverr and Upwork" with the review count, if accurate) and link to the profiles; unsourced rating claims are the first thing assistants and Google discount. I did not add `aggregateRating` markup because it needs a review source on the page.
3. Add a short About page (`/about/`; today `/about` redirects to the home page section): who the firm is, ACCA, languages, service areas, how engagements work, what MFA does not do (audits, legal advice), contact and reply time. Assistants build their picture of a firm from a clear About page. Founding date and team only if Zain wants them public.
4. Public "from" prices for tax preparation (for example individual 1040, Schedule C, S corp return) would let assistants quote MFA in "how much does a tax preparer cost" answers; "quoted up front" gives them nothing to repeat. Needs Zain's numbers.
5. Add visible FAQs to `/services/`, `/shop/` and `/bookkeeping-cleanup/` (price, turnaround, what is included, refund policy "all sales final", software supported). Then the page can carry `FAQPage` markup like the other pages.
6. Business hours or "by appointment, replies in 1-3 business days" line in the footer (matches the contact point) once Zain confirms.
7. A 1200x630 branded share image and a larger square logo (512x512). Today the share image is the 180x180 app icon; the blog posts have proper covers.
8. Homepage performance: trim Google Fonts to the weights actually used (up to 11 font styles today), and consider self-hosting; the splash loader adds time before content is visible to people (crawlers are not affected).

## 6. Things only Zain can do (prioritized)

1. **Merge and deploy** `draft/seo-ai` after a review, then run `python3 tools/indexnow.py --send` once the key file is live at `https://mfa-advisory.com/c95c3d7515b8318fccc55074c359a88f.txt` .
2. **Check Cloudflare is not blocking AI search crawlers.** Cloudflare dashboard for mfa-advisory.com, bot settings (the menu is named "Configure AI bot policies" or "AI Crawl Control"; the exact path changes): Search must be Allow; Agent and Training allowed if you want assistants to fetch pages for users; make sure the managed robots.txt option is off (it can prepend its own rules to `robots.txt`). Then open `https://mfa-advisory.com/robots.txt` and confirm it matches this repo's file. [13]
3. **Google Search Console**: add `mfa-advisory.com` as a Domain property (DNS TXT record in Cloudflare), submit `https://mfa-advisory.com/sitemap.xml`, inspect the homepage URL and request indexing, and confirm Google chose the apex URL as canonical.
4. **Bing Webmaster Tools** (https://www.bing.com/webmasters): sign in, import the site from Google Search Console, submit the sitemap, and check the AI Performance report weekly (Copilot and Bing AI citations). ChatGPT search, Copilot and Bing all lean on Bing's index, so this is the cheapest AI-visibility step. [7] [8]
5. **Google Business Profile**: check whether one already exists (the landing page quotes a "Google review"), and claim it. Set it up as a service-area business with the address hidden, primary category "Accountant" (add "Tax preparation service" and "Bookkeeping service"), service areas Princeton and Mercer County, Union City and Hudson County, New York City, phone (347) 205-4468, website `https://mfa-advisory.com/`, the services list with the public prices (LLC formation from $150, bookkeeping from $199/month), and the shop items as Products. Use the exact name "Merchant Financial Advisory LLC". [11]
6. **Directory listings with identical name, phone and email**: Apple Business Connect (feeds Siri and Apple Maps), Bing Places (can import from Google), Yelp, Better Business Bureau, LinkedIn company page (already linked), Facebook, Nextdoor, the Princeton/Mercer regional chamber, NJ and NYC small-business directories, Upwork and Fiverr profile websites (add the site link), Gumroad profile (link back to `/shop/`). Same business name, "Princeton, NJ", same phone, same site URL everywhere.
7. **Reviews from real clients**: ask existing clients (not employees or relatives) for a Google review after each completed engagement, send the direct review link, reply to each. Reviews are the strongest local ranking and "recommended by AI" signal. Do not buy or script reviews.
8. **Decide the training-bot policy.** Today `GPTBot`, `ClaudeBot`, `Google-Extended` and `Applebot-Extended` (training controls) are allowed, which is the current behavior. Blocking them does not affect search or citations; allowing them does not hurt either. Change in `tools/seo.py` `build_robots()` if you want to opt out.
9. **Approve or reject the copy proposals in section 5**, especially 1 and 2 (public claims) and 4 (prices).
10. **Ask Gumroad whether they plan to support ChatGPT/Google agent checkout** (ACP/UCP); until then the shop's agent visibility depends on `catalog.json` and on-page Product markup.

## 7. Tests run

- `python3 tools/build_resources.py`, `python3 tools/build_landing.py`, `python3 tools/build_blog.py`, `git checkout -- '*.ics'`; `python3 tools/check_catalog.py` passes (10 live, 8 not live).
- `python3 tools/check_seo.py --vocab <schema-dts>/dist/schema.d.ts`: 90 indexable pages, 90 sitemap URLs, every JSON-LD block parses, every type and property valid in schema.org (1022 types), `@id`s resolve, titles and descriptions unique and in range.
- Playwright (Chromium, served with `python3 -m http.server`): `/`, `/services/`, `/llc-formation/`, `/llc-formation/nj/`, `/shop/`, `/resources/`, `/tools/do-i-need-to-send-a-1099/`, `/tools/quarterly-estimated-tax-calculator/`, a blog post, `/blog/`, `/authors/zain-merchant/`, `/bookkeeping-cleanup/`, `/new-york-ny/`, `/princeton-nj/`, `/union-city-nj/` at 390 and 1300 px: no page errors, no horizontal scroll, one canonical and one h1 on each (external requests blocked in the sandbox).
- Not tested: the live site (sandbox cannot reach mfa-advisory.com), Google's Rich Results Test and the Schema Markup Validator (no network access to them). Run both on the homepage, `/services/`, `/shop/` and one blog post after deploy.

## Sources

1. Google Search Central, AI features and your website: https://developers.google.com/search/docs/appearance/ai-features
2. OpenAI, Overview of OpenAI crawlers: https://developers.openai.com/api/docs/bots
3. Anthropic, About Claude's web crawler: https://support.claude.com/en/articles/8896518-about-claude-s-web-crawler
4. Perplexity, Crawlers: https://docs.perplexity.ai/docs/resources/perplexity-crawlers.md
5. PPC Land, llms.txt adoption stalls as major AI platforms ignore the proposed standard: https://ppc.land/llms-txt-adoption-stalls-as-major-ai-platforms-ignore-proposed-standard/
6. Apple, About Applebot: https://support.apple.com/en-us/119829
7. Tenten GEO, Bing Webmaster Tools and ChatGPT visibility (vendor article; claims not confirmed by OpenAI or Microsoft): https://geo.tenten.co/en/blog/bing-webmaster-chatgpt-visibility
8. PPC Land, Bing AI Performance report (public preview 2026-02-10): https://ppc.land/bing-gives-publishers-first-look-at-how-ai-systems-cite-their-content/ ; IndexNow: https://www.bing.com/indexnow and https://www.indexnow.org/documentation
9. Google Search Central, LocalBusiness structured data: https://developers.google.com/search/docs/appearance/structured-data/local-business
10. Google Search Central, FAQPage (FAQ rich result no longer shown, change log 2026-05-08 and 2026-06-15): https://developers.google.com/search/docs/appearance/structured-data/faqpage
11. Google Business Profile Help, guidelines for representing your business (service-area businesses): https://support.google.com/business/answer/9157481
12. dataiads, Google UCP and OpenAI ACP checklist (2026-02-10, secondary source): https://www.dataiads.io/en/blog/google-ucp-openai-acp-protocol-checklist-agentic-commerce
13. Suganthan, Cloudflare changed its AI crawler defaults (secondary source; verify in the Cloudflare dashboard and docs): https://suganthan.com/notes/cloudflare-ai-crawler-defaults/
14. DuckDuckGo, DuckAssistBot: https://duckduckgo.com/duckduckgo-help-pages/results/duckassistbot
15. schema.org vocabulary checked offline with schema-dts 2.1.0 (npm), since schema.org is not reachable from the build sandbox.
