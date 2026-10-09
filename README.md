# mfa-advisory.com

Source for Merchant Financial Advisory LLC's website, deployed by Netlify from `main`.

- `site/` – everything that is published (index.html, icons, `_headers`, and later `blog/`).
- `netlify.toml` – tells Netlify to publish `site/` (no build step).

Every push to `main` goes live automatically. Roll back from the Netlify Deploys tab or with `git revert`.
