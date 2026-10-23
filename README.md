# mfa-advisory.com

**Design (Zain, 2026-10-23):** every new page or update must match the site's design system from the first version, with animations where they fit. Read `docs/design-system.md`, and run `tools/check_ui.py` together with `check_seo.py` and `check_catalog.py` before every push.

Source for Merchant Financial Advisory LLC's website. Static site: everything published lives in `site/` (no build step on the host).

- `site/` – published folder (index.html, blog/, union-city-nj/ landing page, icons, `_headers`, `_redirects`).
- `tools/build_blog.py` – builds the blog and feed; its last step calls `tools/seo.py` for sitemap, robots.txt, llms.txt, llms-full.txt and catalog.json.
- `tools/build_landing.py` – builds the local landing pages (`/union-city-nj/`, `/princeton-nj/`, `/new-york-ny/`).
- `tools/ads.py` – the one Google Ads tag/conversion helper (AW-18505873837): writes `site/assets/ads.js` (tel: clicks → call, booking-calendar links → booking, `window.mfaLead()` after a lead form is confirmed sent) and its `<!--ads:tag-->` block in the hand-built `site/index.html` and `site/404.html`; every builder's `<head>` uses `ads.TAG`.
- `tools/seo.py` – shared JSON-LD building blocks and the machine-readable root files (sitemap.xml, robots.txt, llms.txt, llms-full.txt, catalog.json); run by `build_blog.py` as its last step. `tools/check_seo.py` checks the built site, `tools/indexnow.py` pings Bing after a deploy. See `docs/seo-ai-report.md`.
- Hosting: **Cloudflare Pages** (project `mfa-website`, output dir `site`, no build command), live since Oct 9, 2026. Netlify is retired.

Forms post to FormSubmit (emails info@mfa-advisory.com), so they work on any host.

## Hosting on Cloudflare Pages (free, no bandwidth/request credits)
Cloudflare dashboard → Workers & Pages → `mfa-website` (connected to `zainmerchant50/mfa-website`).
- Project name: `mfa-website` (pages.dev: mfa-website-83y.pages.dev)
- Production branch: `main`
- Framework preset: None · Build command: *(leave empty)* · Build output directory: `site`

Every push to `main` goes live automatically; other branches get free preview URLs.
