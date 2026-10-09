# mfa-advisory.com

Source for Merchant Financial Advisory LLC's website. Static site: everything published lives in `site/` (no build step on the host).

- `site/` – published folder (index.html, blog/, union-city-nj/ landing page, icons, `_headers`, `_redirects`).
- `tools/build_blog.py` – builds the blog, feed, sitemap, robots.txt and llms.txt.
- `tools/build_landing.py` – builds the Google Ads landing page (`/union-city-nj/`).
- Hosting: **Cloudflare Pages** (project `mfa-website`, output dir `site`, no build command), live since Oct 9, 2026. Netlify is retired.

Forms post to FormSubmit (emails info@mfa-advisory.com), so they work on any host.

## Hosting on Cloudflare Pages (free, no bandwidth/request credits)
Cloudflare dashboard → Workers & Pages → `mfa-website` (connected to `zainmerchant50/mfa-website`).
- Project name: `mfa-website` (pages.dev: mfa-website-83y.pages.dev)
- Production branch: `main`
- Framework preset: None · Build command: *(leave empty)* · Build output directory: `site`

Every push to `main` goes live automatically; other branches get free preview URLs.
