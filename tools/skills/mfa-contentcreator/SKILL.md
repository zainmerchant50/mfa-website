---
name: mfa-contentcreator
description: Research, write, design and publish an SEO-optimized MFA Insights post (tax, accounting, QuickBooks, small-business finance) with a keep-handy branded graphic and booking CTA to mfa-advisory.com, or repurpose it for LinkedIn, Instagram or the newsletter. Use for any MFA blog or content request.
---

# MFA Content Creator

Produces content for **Merchant Financial Advisory LLC** (MFA), a New Jersey **accounting and tax solutions provider** (never position it as only tax or only accounting) (mfa-advisory.com, info@mfa-advisory.com). The primary output is an MFA Insights blog post. The same research can be repurposed for LinkedIn, Instagram and the weekly newsletter.

## Standing requirements (from Zain)
- **Audience:** individuals, and small and mid-sized businesses.
- **Topic mix (rotate so no area dominates):**
  1. *Tax filing & deadlines:* IRS updates (Newsroom, IR- releases, tax tips, disaster relief), key dates, filing and preparation. Include NJ angles when they apply.
  2. *Tax planning:* individuals and business owners (entity choice, estimated taxes, retirement contributions, deductions).
  3. *Accrual accounting:* revenue recognition basics, accruals vs. cash, month-end close, why lenders and buyers want accrual books.
  4. *QuickBooks:* QuickBooks Online and Desktop product updates and release notes, practical tips, setup and cleanup.
  5. *Bookkeeping best practices* for SMBs: reconciliations, chart of accounts, internal controls, documentation.
  6. *Small & mid-sized business finance:* cash flow, KPIs, budgeting, fractional CFO topics.
  - Suggested rhythm: **Mon = tax**, **Wed = accounting/bookkeeping**, **Fri = QuickBooks or business finance**. Breaking IRS news can override any slot.
- **Category labels** (meta `category`): Tax Deadlines, Tax Planning, Accrual Accounting, QuickBooks, Bookkeeping, Business Finance.
- **Every post must have:** target keywords, key dates, current and accurate facts, practical tips, a keep-handy graphic, and an ending CTA. The CTA is "Book a consultation" (https://mfa-advisory.com/#book) or "email info@mfa-advisory.com".
- **Graphic:** use only the site's navy, white and gold theme. It must be *useful*, not decorative. Good formats are a timeline, key-numbers cards, a checklist, a "who this affects" chart or a decision tree: something a reader would save and keep handy. One main graphic per post, plus a 1200×630 social card.
- **Cadence:** 3 posts a week (Mon, Wed, Fri), live at **7:30am ET**, plus a bonus post when the IRS releases major news.
- **Approval:** draft the night before (around 8pm ET) and email Zain a preview link. Publish only after he replies "Approve". If no approval arrives, hold the post. (Trial posts Zain asks for directly can publish right away.)
- **Tone:** plain English, confident and helpful. No hype and no fearmongering. Write for individuals and small-business owners.

## Accuracy rules (non-negotiable)
1. **Primary sources only for facts:** irs.gov (newsroom, forms, publications, payment and penalty pages), nj.gov/treasury/taxation, federal law and regulations, FASB/AICPA for accounting standards, and Intuit's official QuickBooks release notes, blog and support pages for QuickBooks features. Secondary sites may be used to find leads, never as the citation.
2. **Verify every number and date** on the primary page this session: deadlines, penalty rates, inflation-adjusted amounts, AGI limits, interest rates. Don't rely on memory. If a fact can't be verified, cut it.
3. Watch for **year confusion.** Tax year ≠ filing year. Inflation-adjusted figures change every year.
4. **Disaster relief is county-specific.** Name states only from IRS releases and always point to the IRS disaster-relief page.
5. Every post gets a **Sources** list (built automatically from the meta) and the standard disclaimer with a "facts checked as of" date.
6. Never imply MFA or Zain holds a credential they don't. The byline is "Merchant Financial Advisory". Don't put "CPA" in the copy. Never imply Intuit endorses MFA.
7. Don't fabricate client stories, testimonials or statistics.
8. Every page carries the legal disclaimer automatically (article footer and site footer). Don't remove it. Link /disclaimer.html when relevant.

## Topic discovery: monitor what's trending (do this first, every run)
Check these, then pick the most timely and useful topic that isn't already covered (compare with `content/posts/`):
- **IRS:** Newsroom (irs.gov/newsroom), latest IR- news releases, Tax Tips, disaster-relief releases, new or draft forms and inflation adjustments, and upcoming deadlines in the next 2–6 weeks.
- **Accounting:** FASB news and ASU releases, AICPA & CIMA news, and small-business accounting changes (e.g. 1099/W-2 thresholds, BOI/FinCEN updates if relevant).
- **QuickBooks:** Intuit's QuickBooks blog, "What's new in QuickBooks Online" release notes, and Intuit price and plan changes.
- **NJ:** NJ Division of Taxation news (NJ-1040, sales tax, ANCHOR and other programs) for local relevance.
- **Demand signals:** WebSearch for what people are asking right now ("<topic> 2026", "how do I…", "best way to…") and seasonal search interest. Prefer topics with clear search intent.
Log the chosen topic and why in the commit message.

## Search & AI-search optimization
- Write to **search intent**. Use phrases people actually type or ask an AI: "best way to…", "best accounting software for small business", "best practices for month-end close", "how to…", "what is…", "do I need to…", "<deadline> 2026". Put the primary phrase in the title, first paragraph, one H2 and the meta description.
- "Best" phrasing is for **topics** ("best practices", "best QuickBooks settings for…"). **Never claim MFA is "the best" or "top-rated"** or make other unverifiable superlatives about the firm. That risks FTC and false-advertising problems and hurts credibility. Let verifiable facts do the selling: 5.0 average rating on Fiverr and Upwork, QuickBooks ProAdvisor, ACCA (UK), 10+ years, PwC background.
- **Answer-first structure** helps AI engines (ChatGPT, Perplexity, Google AI Overviews, Claude) quote you. Open with "The short version". Use clear H2 questions and a "Quick answers" FAQ (the build turns it into FAQPage schema automatically; keep the `<h2>Quick answers</h2>` + `<h3>question</h3><p>answer</p>` pattern). Use specific numbers, dates and named sources, and add a one-line definition when you introduce a term.
- **Entity consistency:** always "Merchant Financial Advisory (MFA), an accounting and tax solutions provider in Princeton, New Jersey, serving individuals and small and mid-sized businesses nationwide". The build regenerates `/llms.txt` and `robots.txt` (AI crawlers allowed) on every run.
- Link internally: 1–2 links to related MFA posts and one to the relevant service on the home page.

## Graphic formats (rotate)
Timeline, key-numbers cards, checklist, decision flowchart ("Do I need to file…?"), comparison table (cash vs. accrual), flashcard set (term → plain-English meaning), and QuickBooks "where to click" step cards (described, never Intuit screenshots or logos). Every graphic: navy/white/gold, MFA lockup, mfa-advisory.com, and "General information, not tax advice. Facts checked <date>."

## Built-in page features (automatic, no action needed)
Author byline and "About the author" box (Zain Merchant, ACCA, linked to LinkedIn; set in AUTHOR at the top of tools/build_blog.py, override per post with an "author" meta field), share bar (Post on LinkedIn, X, Facebook, email, copy link, native share on phones) at the top and bottom of each article, CTA block, sources, disclaimer, the home-page "Latest Insights" window (reads `/blog/latest.json`), the RSS feed, sitemap, FAQ schema and llms.txt.

## SEO checklist
- **Keywords must be used on the page, not just listed.** Google ignores the meta-keywords tag; rankings come from where the phrases appear. The first keyword in `keywords` is the **primary** one: put it in the title or seoTitle, the first paragraph or an H2, and the description. Every other keyword must appear naturally somewhere in the article (an H2, an FAQ question, a sentence). Write them as people search: "1099 threshold for 2026", "who needs a 1099", "do I send a 1099 to an LLC".
- `python3 tools/build_blog.py` runs an SEO check and prints `SEO [...]` warnings. **Fix every warning before committing.** The keywords also render as a visible "Topics covered" list at the end of each article.
- `title`: about 50–65 characters, with the primary keyword and the date or year. `seoTitle` can differ for the <title> tag.
- `description`: 140–160 characters. It should answer "what and when", with a hook.
- 5–8 `keywords`: primary, secondary, long-tail and a local NJ variant where relevant.
- H2s phrased the way people search ("Who the October 15 deadline applies to", "If you can't pay the full balance").
- A "The short version" box at the top (good for featured snippets) and a "Quick answers" FAQ near the end.
- Descriptive slug: lowercase with hyphens, no stop-word padding. Include dates.
- Alt text on the graphic describes what it teaches.
- Length: 700–1,300 words. One idea per paragraph; tables for numbers.
- Avoid scaled-content patterns. Each post must add something specific (dates, numbers, steps). Don't rewrite the same topic every week; update the existing post instead (set `updated`).

## Repo and build (zainmerchant50/mfa-website, Netlify auto-deploys `main`)
```
content/posts/<slug>.html          post source: <!--meta {json} --> + body HTML
content/graphics/<slug>-cover.html  keep-handy graphic (HTML/CSS, links _base.css)
content/graphics/<slug>-og.html     1200x630 social card
content/graphics/_base.css          brand fonts/colors (fonts vendored in tools/fonts)
tools/build_blog.py                 builds site/blog/*, blog/latest.json (feeds the home-page "Latest Insights" window), feed.xml, legal pages (content/pages), sitemap.xml, robots.txt
tools/render_graphics.js            renders graphics → PNG (Playwright)
site/                               published folder
```
**Meta fields:** title, seoTitle, slug, date (YYYY-MM-DD), factsAsOf, category, description, dek, keywords[], cover ("cover.png"), coverAlt, og ("og.png"), ctaHeadline, ctaTopic, sources[{title,url}]. Optional: updated, status ("draft" to exclude).

**Body building blocks** (styled by site/blog/blog.css): `<div class="tldr">`, `<figure class="figure"><img src="cover.png" ...>`, `<table class="tbl">`, `<h2>`, `<h3>`, `<ol>`, `<ul>`. The CTA, sources and disclaimer are added automatically.

**Steps:**
1. Research (WebSearch/WebFetch on irs.gov first). Note each fact with its source URL.
2. Write `content/posts/<slug>.html`.
3. Copy the previous post's graphics as templates, adapt them, then render:
   `node tools/render_graphics.js content/graphics/<slug>-cover.html site/blog/<slug>/cover.png 1200 <height> 1`
   `node tools/render_graphics.js content/graphics/<slug>-og.html site/blog/<slug>/og.png 1200 630 1`
   Look at both PNGs. Fix any overflow, empty space or wrong figures. Keep the cover height tight to its content.
4. `python3 tools/build_blog.py`
5. QA: screenshot the post at 1300px and 390px (no horizontal scroll, image not distorted). Re-read every number against its source.
6. **Draft mode:** commit to branch `draft/<slug>`, push, and email Zain the Netlify branch preview link (`https://draft-<slug>--mfa-advisory.netlify.app/blog/<slug>/`) with a 3-line summary. Subject: "Approve? MFA post for <date>".
   **Publish:** merge to `main` (or commit directly for an approved or trial post) and push. Then verify the live URL and that `/blog/feed.xml` includes it.
7. Commit messages end with the session attribution lines.

## Repurposing (on request)
- **LinkedIn:** 120–220 words. Lead with the date or number, give 3 bullet takeaways, end with the post link and "Book a consultation". 3–5 hashtags (#TaxDeadline #IRS #SmallBusiness #NewJersey).
- **Instagram:** a carousel built from the cover graphic sections (1080×1350), with a short caption and the link in bio.
- **Newsletter:** a weekly digest of that week's approved posts, with title, 2-line summary and link each, plus one "date to remember". It goes out via the email service's RSS-to-email feature from `/blog/feed.xml`.
