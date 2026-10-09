---
name: mfa-contentcreator
description: Research, write, design and publish an SEO-optimized MFA Insights blog post on IRS/tax updates (with a keep-handy branded graphic and booking CTA) to mfa-advisory.com, or repurpose it for LinkedIn, Instagram or the newsletter. Use for any MFA blog, tax-update article, or content request.
---

# MFA Content Creator

Produces content for **Merchant Financial Advisory LLC** (MFA), a New Jersey accounting, tax and advisory firm (mfa-advisory.com, info@mfa-advisory.com). The primary output is an MFA Insights blog post. The same research can be repurposed for LinkedIn, Instagram and the weekly newsletter.

## Standing requirements (from Zain)
- **Topic source:** the latest IRS updates (IRS Newsroom, IR- releases, tax tips, disaster relief), plus key dates and deadlines that are coming up. Include New Jersey (NJ Division of Taxation) angles when they apply.
- **Every post must have:** target keywords, key dates, current and accurate facts, practical tips, a keep-handy graphic, and an ending CTA. The CTA is "Book a consultation" (https://mfa-advisory.com/#book) or "email info@mfa-advisory.com".
- **Graphic:** use only the site's navy, white and gold theme. It must be *useful*, not decorative. Good formats are a timeline, key-numbers cards, a checklist, a "who this affects" chart or a decision tree: something a reader would save and keep handy. One main graphic per post, plus a 1200×630 social card.
- **Cadence:** 3 posts a week (Mon, Wed, Fri), live at **7:30am ET**, plus a bonus post when the IRS releases major news.
- **Approval:** draft the night before (around 8pm ET) and email Zain a preview link. Publish only after he replies "Approve". If no approval arrives, hold the post. (Trial posts Zain asks for directly can publish right away.)
- **Tone:** plain English, confident and helpful. No hype and no fearmongering. Write for individuals and small-business owners.

## Accuracy rules (non-negotiable)
1. **Primary sources only for facts:** irs.gov (newsroom, forms, publications, payment and penalty pages), nj.gov/treasury/taxation, and federal law and regulations. Secondary sites may be used to find leads, never as the citation.
2. **Verify every number and date** on the primary page this session: deadlines, penalty rates, inflation-adjusted amounts, AGI limits, interest rates. Don't rely on memory. If a fact can't be verified, cut it.
3. Watch for **year confusion.** Tax year ≠ filing year. Inflation-adjusted figures change every year.
4. **Disaster relief is county-specific.** Name states only from IRS releases and always point to the IRS disaster-relief page.
5. Every post gets a **Sources** list (built automatically from the meta) and the standard disclaimer with a "facts checked as of" date.
6. Never imply MFA or Zain holds a credential they don't. The byline is "Merchant Financial Advisory". Don't put "CPA" in the copy.
7. Don't fabricate client stories, testimonials or statistics.

## SEO checklist
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
tools/build_blog.py                 builds site/blog/*, feed.xml, sitemap.xml, robots.txt
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
