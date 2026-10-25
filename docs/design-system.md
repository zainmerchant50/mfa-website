# MFA site design system: use it on every page, from the first version

Last updated: 2026-10-24 by Site (copy and layout audit rules after Zain's /book/ review).

**Standing rule (Zain, 2026-10-23):** every new page and every update on mfa-advisory.com must match the rest of the site from its first version, with UI animations wherever they fit. Zain should never have to point out an inconsistency. The interface should look polished and interactive.

## Before you push any page change
1. Build the page from the components below, never from bare HTML defaults. Copy the closest existing page builder: `tools/build_book.py`, `build_llc.py`, `build_services.py` or `build_landing.py`.
2. Run `tools/build_resources.py`, then `tools/build_blog.py`.
3. Run the checks. **All three must pass:** `tools/check_ui.py`, `tools/check_seo.py` and `tools/check_catalog.py`. Where Playwright is installed, run `tools/check_ui.py --render` too: it opens every page at 390 and 1300 px and measures the fine-print spacing.
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
| Disclaimer / footnote at the end of a page | `ui_kit.fineprint("text")`: muted italic `.disclaimer`, 48px above it (0 straight after a CTA card), 72px above the footer | A bare `<section><p class="disclaimer">` (check_ui.py fails it; it sat on the footer line on /book/, /shop/, /services/ and /bookkeeping-cleanup/) |
| Embeds (calendar etc.) | A framed card with a soft shadow; add `book-frame` to it so it reveals on scroll | A raw iframe |

## Motion
- **Built in:** scroll reveal (`.rv` is added automatically to `.sec-hd`, `.card`, `.step`, `.faq-l`, `.book-frame` and similar), hero entrance, hover lift on cards, steps and buttons, the FAQ open and close, and the sticky-header shadow.
- **New components:** add a tasteful hover state and an entrance (fade up, 0.5–0.9 s, `cubic-bezier(.16,1,.3,1)`), staggered for lists.
- **Accessibility:** always respect `prefers-reduced-motion`. Without JavaScript, everything must still be visible.

## Copy and layout rules (Zain, 2026-10-24: "you need to catch these things")
Checked automatically by `tools/check_ui.py`; read the page yourself as well.
- **Point to things where they really are.** Before writing "below" or "above", check where the target sits on the page at 390 and 1300 px. On /book/ the calendar is the first section, so the text says "the calendar at the top of this page" and links to `#calendar`. Prefer a link over a direction word. check_ui fails a "below"/"above" reference to the booking calendar, a form, the sources list or add-to-calendar links when the target isn't on that side. Avoid "left"/"right": the columns stack on phones.
- **We, not I.** MFA works with a team of tax and accounting experts. Write "we" or "our team" for the firm and "Zain" for the person. "Who will I meet with?" is answered with "Zain and/or a member of his team". Visitor-voice labels ("Start my LLC", "Can I deduct…?") are fine. check_ui fails firm-voice phrases such as "contact me" or "I'll review".
- **Fine print never touches the footer.** Use `ui_kit.fineprint()`. The kit keeps 72px under the last `.llc-sec` and 40px under a last `.tinfo`. check_ui fails the build if those CSS values are lowered or `.disclaimer` margin-top drops below 16px.
- **Links must work.** Same-page `#anchors` must exist, and internal links must resolve to a built page or a `_redirects` rule, with any `#fragment` present on that page. A bad find-and-replace once produced `/services/book/keeping`.
- **One phone, one email.** (347) 205-4468 (`tel:+13472054468`) and info@mfa-advisory.com. Leftover placeholders (lorem ipsum, TODO, TBD, `[insert`, `{VAR}`) and any sentence repeated back to back fail the check.
- **Credential line** (use it as written): CPA candidate · ACCA · Big Four (ex-PwC) · PTIN/EFIN tax preparer.

## Content rules (unchanged)
Never use the word "free". Never call MFA a CPA firm or Zain a CPA. No street address. Prices and new public claims need Zain's yes. Customer-facing dates show the date only.
