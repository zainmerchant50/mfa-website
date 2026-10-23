# MFA Social agent: daily Instagram + LinkedIn posts

Last updated: 2026-10-22 19:40 ET by Hub (agent created on Zain's instruction).

## What it does
Every weekday, the agent makes **one post** (Instagram image + LinkedIn image + both captions + sources) and saves it to
Zain's iCloud folder on the Windows PC:

`C:\Users\MFA\iCloudDrive\Documents\MFA\Social Media Management\Ready to Post\<YYYY-MM-DD Day> - <Title>\`

Zain's social media helper posts straight from that folder. **Zain gave standing approval (2026-10-22): everything saved
there must already be fact-checked and ready to post. Nobody reviews it after you.** That makes accuracy your job.

## Daily run (in order)
1. `git clone` zainmerchant50/mfa-website (or pull) and `cd` into it. Install once: `pip install playwright --break-system-packages`
   (Chromium is already in the container; do not run `playwright install`).
2. Read `social/log.json` (posts already made) and `social/queue.md` (ideas). Pick the next post date: the next weekday
   that has no post yet (Mon–Fri only; skip US federal holidays). If the next 2 weekdays are already covered, stop and log "ahead".
3. Choose the topic: follow the mix and rotation rules below. Prefer anything with a deadline in the next 3 weeks.
4. **Verify every figure** (dollar amounts, %, dates, thresholds, form names) on an official source (irs.gov, the state
   revenue site, ssa.gov, fincen.gov). Repo data in `data/*.json` was checked by Blog and lists its `source_url`;
   you may use it but re-open the source if `checked` is older than 30 days. If a figure can't be confirmed, cut it.
5. Write `social/posts/<date>-<slug>.json` (fields below) and render:
   `python3 social/render.py social/posts/<file>.json /mnt/user-data/outputs/social/<folder name>`
   The renderer refuses banned words and layout overflow; fix the copy and re-run. Then **look at both PNGs** (Read tool)
   and check for clipped text, orphan words and anything that looks off.
6. Write `00_POST-NOTES.md` into the same output folder: date, LinkedIn time 8:00 AM ET, Instagram time 12:00 PM ET,
   which image goes with which caption, the CTA keyword and the link to send people who comment it, and the sources table.
7. Copy the folder to the PC with `mcp__remote-devices__device_commit_files` (one entry per file; devicePath under the
   Ready to Post folder above). Confirm with `device_list_dir`.
8. Append the post to `social/log.json`, commit (`social: <date> <slug>`) and push to main. The Cloudflare site only deploys
   `site/`, so this does not change the website.
9. Email Abiha at **abihamerchant1@gmail.com** (Zain 2026-10-23; not the iCloud address), who posts for Zain:
   - Images: `python3 social/email.py --images social/posts/<file>.json /mnt/user-data/outputs/social/<folder>` writes HD JPEGs to
     `site/ready/<date>/<slug>-INSTAGRAM.jpg` and `-LINKEDIN.jpg` (noindex via site/_headers). Commit and push, wait for the
     Cloudflare Pages check to pass, then confirm both URLs return 200 image/jpeg (Chrome tab fetch from mfa-advisory.com).
   - Email: `python3 social/email.py social/posts/<file>.json "<exact reply text from 00_POST-NOTES.md>"` writes
     /tmp/abiha-email/subject.txt, body.html and body.txt. Send with the Gmail send tool: to abihamerchant1@gmail.com only,
     subject = subject.txt, htmlBody = body.html, body = body.txt, no attachments. Each caption sits alone in a box so she
     can copy it straight into LinkedIn / Instagram.
10. Update the agent dashboard (see `claude/site/agent-dashboard.md` in the project) with what was made and the next idea.

## Content mix (per 5 weekdays)
- 2 **product posts** (layout `product`): a real screenshot of one of our trackers/checklists from `social/products/<id>/`
  (`photo-3.jpg` is usually the in-app screenshot; `photo-1.jpg` the hero; `cover.jpg` for 01–03), 3–4 features,
  CTA word = the product type (TRACKER, CHECKLIST, CALCULATOR, KIT, TEMPLATE). Link: `mfa-advisory.com/shop`.
  **Protect the product:** set `product.crop` to the useful part of the screenshot and `product.blur` to boxes over the
  figures/formulas (fractions of the cropped image; see the 2026-10-23 post). The renderer always adds a diagonal
  "SAMPLE · mfa-advisory.com" watermark and renders at 2x (Instagram 2160x2700, LinkedIn 2400x2400).
  Only use products whose `status` is `live` in `catalog/products.json`.
  **Discount code (Zain 2026-10-23):** every product post's captions (IG and LinkedIn) include the line
  "Use code MFASITE10 for 10% off on Etsy or Gumroad." right after the CTA line. The code is NOT shown on the website
  or on the image. Never show a price on the image; the caption may
  give the catalog price.
- 2 **"save this" value posts** (layout `hero` or `list`): one money-saving rule, deadline or threshold, tied to a guide,
  calculator or tool on the site. CTA word = GUIDE (blog post) or CALCULATOR / TOOL (site tool), link = that page.
- 1 **service post**: what MFA does for that problem (bookkeeping, 1099 filing $25/form with $75 minimum, LLC formation from
  $150, cleanup quote, monthly bookkeeping from $199/mo). CTA word = CALL, link = `mfa-advisory.com`.
- Calendar anchoring: about one post in three ties to a real date (estimated tax Jan 15, 1099s Feb 1 2027, Dec 31 planning,
  Mar 15 S corp/partnership returns, Apr 15).
- Never repeat a topic within 6 posts; rotate the angle (checklist / myth vs fact / deadline / mistake we see / how-to).

## Copy rules (from Zain's original social chat, still binding)
- Firm voice: "we", never "I". Calm, practical, plain English, like a controller talking to an owner.
- **Never** the word "free". Never call MFA a CPA firm or Zain a CPA. No street address. No attest/audit-service claims
  (only "audit support"). No client names. No invented stories or statistics.
- Banned words: here's why, here's the thing, unlock, game changer, leverage, navigate, dive into, thrilled, excited,
  revolutionary, cutting edge, transform, seamless, robust, empower, elevate, "let's be honest", "the truth is".
- Instagram caption: 60–140 words, may use ✔️ checkmarks for lists (no other emojis), CTA line
  "Comment WORD and we'll send you the link, or find it at <link>", then "General information, not tax advice.",
  then 16 hashtags (8 general, 8 specific) on two lines.
- LinkedIn caption: 120–200 words, flat opening statement, numbered list when it really is a list, no emojis, CTA
  "Comment WORD and we will send it, or see <link>", 3–5 hashtags.
- Image: headline ≤ 9 words (one gold *italic* accent word or number), kicker ≤ 6 words, label like "1099 SEASON / TRACKER".
  Footer, logo and "General information, not tax advice. Facts checked <date>." are added by the renderer.

## Post JSON fields
`date, number (1..n within the folder, normally 1), slug (Title-Case-Hyphens), topic, type (product|value|service),
accent (burgundy|amber|teal|plum|forest|slate), label, kicker, headline, headline_size (default 76), layout
(hero|list|product), hero {value, sub} | items [{title, text}] | product {id, image, crop [l,t,r,b], features[]},
body [paragraphs], cta_word, link, checked ("October 22, 2026"), ig_caption, li_caption, sources [{fact, url}], post_times`.
Example: `social/posts/2026-10-23-1099-contractor-tracker.json`.

## Comment-keyword replies
Instagram auto-DMs need a tool such as ManyChat (not set up yet). Until then Zain's helper replies to "TRACKER", "GUIDE"
etc. by hand with the link in `00_POST-NOTES.md`.
