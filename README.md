# mfa-advisory.com

Source for Merchant Financial Advisory LLC's website. Static site: everything published lives in `site/` (no build step on the host).

- `site/` – published folder (index.html, blog/, union-city-nj/ landing page, icons, `_headers`, `_redirects`).
- `tools/build_blog.py` – builds the blog, feed, sitemap, robots.txt and llms.txt.
- `tools/build_landing.py` – builds the Google Ads landing page (`/union-city-nj/`).
- `netlify.toml` – Netlify config (publish `site/`). Can be deleted once the move to Cloudflare Pages is done.

Forms post to FormSubmit (emails info@mfa-advisory.com), so they work on any host.

## Hosting on Cloudflare Pages (free, no bandwidth/request credits)
Cloudflare dashboard → Workers & Pages → Create → Pages → Connect to Git → `zainmerchant50/mfa-website`.
- Project name: `mfa-advisory`
- Production branch: `main`
- Framework preset: None · Build command: *(leave empty)* · Build output directory: `site`

Every push to `main` goes live automatically; other branches get free preview URLs.
