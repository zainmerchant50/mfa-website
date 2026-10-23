# MFA site design system: use it on every page, from the first version

Last updated: 2026-10-23 by Hub.

**Standing rule (Zain, 2026-10-23):** every new page and every update on mfa-advisory.com must match the rest of the site from its first version, with UI animations wherever they fit. Zain should never have to point out an inconsistency. The interface should look polished and interactive.

## Before you push any page change
1. Build the page from the components below, never from bare HTML defaults. Copy the closest existing page builder: `tools/build_book.py`, `build_llc.py`, `build_services.py` or `build_landing.py`.
2. Run `tools/build_resources.py`, then `tools/build_blog.py`.
3. Run the checks. **All three must pass:** `tools/check_ui.py`, `tools/check_seo.py` and `tools/check_catalog.py`.
4. Take Playwright screenshots at **390px and 1300px**, full page, after scrolling so the reveal animations have finished. Look at both. Then compare the new section side by side with the same kind of section on an existing page: section headers, cards and steps, FAQ, buttons, pills, spacing. Fix any differences before pushing.

## Components (CSS and JS come from `tools/ui_kit.py` → `site/blog/ui.css` plus `UI_JS`)

| Need | Use | Don't |
|---|---|---|
| Section title | `<div class="sec-hd"><span class="eyebrow eb-dark">LABEL</span><h2>Title</h2></div>`, which uses the Cormorant serif heading | A plain `<h2>` with no eyebrow (FAQ sections may use `<h2>FAQs</h2>`) |
| Hero | `<header class="bhero rhero"><div class="wrap">` with eyebrow, h1 (gold italic `<em>` accent), lead and `.hero-btns`. It gets the staggered entrance automatically | A hero with no buttons, or a full-screen `100vh` hero |
| A sequence (how it works, steps) | Numbered steps: a 01/02/03 gold counter, a gold top border and white cards (`.steps` / `.step`, see build_landing.py and build_book.py) | Unstyled `.card` divs, or numbers on items that aren't a sequence |
| Parallel items (services, packages, features) | `.card` with a border, radius and white background (see build_services.py) | Bare `<article>` elements with no border |
| FAQ | `ui_kit.faq_accordion(pairs, prefix="xx")`: hairline rows and a gold plus that turns into a minus. Also add FAQPage JSON-LD | `<details><summary>` (check_ui.py fails the build) |
| Buttons | `btn btn-gold` (primary) and `btn btn-line` (secondary). Both lift on hover | Plain links styled as buttons inline |
| Tags and topics | Gold-outline pills that fill gold on hover, with a staggered entrance (`.bk-topics` on /book/) | Bullet lists for short topic sets |
| Tables | `.tbl`, which highlights rows on hover | Unstyled tables |
| Embeds (calendar etc.) | A framed card with a soft shadow; add `book-frame` to it so it reveals on scroll | A raw iframe |

## Motion
- **Built in:** scroll reveal (`.rv` is added automatically to `.sec-hd`, `.card`, `.step`, `.faq-l`, `.book-frame` and similar), hero entrance, hover lift on cards, steps and buttons, the FAQ open and close, and the sticky-header shadow.
- **New components:** add a tasteful hover state and an entrance (fade up, 0.5–0.9 s, `cubic-bezier(.16,1,.3,1)`), staggered for lists.
- **Accessibility:** always respect `prefers-reduced-motion`. Without JavaScript, everything must still be visible.

## Content rules (unchanged)
Never use the word "free". Never call MFA a CPA firm or Zain a CPA. No street address. Prices and new public claims need Zain's yes. Customer-facing dates show the date only.
