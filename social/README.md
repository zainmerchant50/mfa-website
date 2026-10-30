# MFA Social agent: daily Instagram + LinkedIn posts

Last updated: 2026-10-25 by the content-pack agent (Shorts standing rules: plain wording, NJ/NY states, "Comment WORD" end cards, CTA by platform). Created 2026-10-22 by Hub on Zain's instruction.

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

## Shorts (Reels, YouTube Shorts, Pinterest video pins)

Added 2026-10-24 on Zain's instruction: "start creating pins, they should also be moving shorts/videos ... the goal is to
get views, have people go from those videos to the site/store and buy our digital products or hire us ... everything to
ALL work in SYNC."

**Status.** Batch 1 (5 shorts, 2026-10-24) was approved by Zain on 2026-10-24 ("the 5 are ok, email to Abiha") and emailed
to Abiha the same night with a Mon/Wed/Fri 6:00 PM ET schedule (Oct 26 to Nov 4). Batch 2 (the first 5 tip shorts from
`social/shorts/IDEAS.md`, 2026-10-24) **waits for Zain's review: don't email or post it**. Until Zain confirms the tip
format, every new batch waits for his review in chat.

### Content rule (Zain, 2026-10-24): practical tips that make people follow, then buy
"Going forward the video reels, shorts, pinterest etc should all be tips and tricks for small sized businesses/individuals
so they are encouraged and then want to follow and then buy our digital products. It should be real helpful practical stuff."
- **Every short, Reel and video pin is a practical tip that helps the viewer today**: one problem real people ask about
  (see the research in `social/shorts/IDEAS.md`), then the fix in 2-4 concrete steps they can do this week.
- **It ends on a soft CTA** to the page that matches the tip: a site tool, a guide, or the matching live product. "Link in
  bio" plus one line naming it ("1099 tax calculator on our site"). No hard sell, no price on the video.
- **Mix: about 80% pure tips, 20% product-led.** Pure tips have no product beat; product-led shorts (about 1 in 5) show the
  product in a `product` beat after the tip.
- **Series formats** people can follow: **1-minute bookkeeping fix**, **Tax myth vs fact**, **Gig worker money tip**,
  **Seller money tip**, **Owner pay 101**. Put the series name in the label or the hook sub.
- **Pick from the top of `social/shorts/IDEAS.md`** (ranked backlog; mark an idea "made <date>" when you render it). Re-verify
  every figure on its primary source on the day you render, whatever the backlog says.
- Audiences to rotate: individuals with side income, 1099/gig workers, small business owners, Etsy/online sellers.

### Standing rules (Zain, 2026-10-25: "do what works")
**MUST (non-negotiable)**
- Accurate facts, each verified on a primary source (irs.gov, ssa.gov, uscis.gov, nj.gov / tax.ny.gov) on the day you
  render, listed in `sources`. If you can't verify it, cut it.
- Plain, everyday wording a busy person reads in one second. Read every on-screen line out loud; if it sounds stiff or
  odd, rewrite it. No jargon without a plain explanation ("businesslike", "substantiate", "expensed", "de minimis",
  "P&L" on its own). Example: "You run it in a businesslike way" became "You run it like a real business".
- MFA rules: never the word "free", never call MFA a CPA firm or Zain a CPA, no street address, no prices on the video.

**DEFAULTS (use judgment; vary when something performs better)**
- A curiosity hook that stops the scroll (a surprising question, a common mistake, a number), then a practical tip that
  helps an everyday person, small business owner, artist or student today.
- State examples: NJ or NY (our market), or no state at all and say "varies by state". No other states on screen.
- Mix formats: story, myth vs fact, 3-step fix, "stop doing this", checklist, Q&A. Track which wins through the UTMs;
  the weekly report should say which hooks and formats got the most views and clicks, so we do more of those.

**CTA by platform (one video file serves all three)**
- End card: "Comment *WORD*" (one keyword per short, tied to the page or product it promotes: ARTIST, LLC, 1099, 8843)
  with the page's short URL in the pill (e.g. `mfa-advisory.com/artists`; paths over 26 characters get a smaller pill).
  `shorts.py` defaults `cta.big` to "Comment *WORD*" from `captions.comment_word`.
- Instagram Reels: comment-to-DM. `INSTAGRAM.txt` ends "Comment WORD and we'll DM you the link. Or visit <url>.";
  `00_SHORT-NOTES.md` holds the exact DM reply (`captions.dm_reply`, or the default: thanks + link label + Instagram UTM
  link) for Abiha, Zain or us to send by hand until ManyChat exists.
- YouTube Shorts: no comment-to-DM there, so `YOUTUBE.txt` puts the UTM link on the first line of the description and
  gives a PINNED COMMENT with the same link.
- Pinterest video pins: the pin links to the page (`PINTEREST.txt` destination URL with UTM).

### Hashtags (Zain, 2026-10-25)
- **Instagram:** 5-10 tags, broad + niche (`shorts.py` lints 5-10). **YouTube Shorts:** 3-5 in `captions.youtube_hashtags`,
  always including `#shorts` (printed at the end of the description). **Pinterest:** no hashtags; put the search words in a
  keyword-rich title and description instead.
- Use real, active tags. Checked 2026-10-25 on displaypurposes.com: #internationalstudents (~356k posts), #f1visa and
  #artistsoninstagram are active and unflagged. Re-check a tag before leaning on it, and drop any that Instagram
  restricts. Never tag by nationality or ethnicity; tag the visa or tax situation.
- Reusable sets (pick 5-10; mix 3-4 broad with niche):
  - Small business: #smallbusinesstips #smallbusiness #bookkeeping #taxtips #smallbusinesstaxes #entrepreneur #accounting #bookkeepingtips #llc #businessowner
  - 1099 / gig: #1099 #selfemployed #gigworker #sidehustle #freelancer #estimatedtaxes #uberdriver #doordashdriver #mileagelog #taxwriteoffs
  - Sellers: #etsyseller #etsyshop #onlineseller #1099k #sidehustle #smallbusinesstips
  - Artists: #artistsoninstagram #artbusiness #artist #sellingart #artfair #etsyseller #taxwriteoffs #salestax #taxtips #smallbusinesstips
  - Stylists: #hairstylist #boothrenter #salonowner #taxwriteoffs #selfemployed
  - F-1 / OPT students: #f1visa #internationalstudents #optstudents #studentsinusa #studyinusa #nonresident #taxseason #taxtips
  - H-1B / H-4: #h1b #h1bvisa #workinusa #h4visa #h4ead #nonresident #taxseason #taxtips
  - YouTube sets: `#shorts #smallbusiness #taxtips #bookkeeping` · `#shorts #artists #artbusiness #taxtips` ·
    `#shorts #f1visa #internationalstudents #taxtips` · `#shorts #h1b #taxtips #taxseason` · `#shorts #selfemployed #gigworker #taxtips`

### Make one
1. Write `social/shorts/specs/<date>-<slug>.json` (copy a 2026-10-24 spec; every field is documented at the top of
   `social/shorts.py`). Pattern, 4-7 beats between the hook and the CTA: **hook** (on screen at frame 0, ≤ 7 words, one gold
   *accent*) → **story** (2-3 short lines, invented first name, never a client) → **twist / question** → **the fix** (list,
   stat, values or rows) → **product or service** (image in `social/shorts/img/`, 1200 px JPEG of the public listing hero)
   → **CTA** end card "Comment *WORD*" + the page's short URL in the pill (see "Standing rules" below). Never "click",
   "tap the link", "swipe up" or "link below" on the video (nothing in a Reel is clickable); never a price on the video;
   no IRS logos or form look-alikes. Not every short needs a story: vary the format (see below).
2. Verify every figure exactly as for posts (irs.gov / ssa.gov / state site, or `data/*.json` checked within 30 days) and
   list each in `sources`. No refund or savings promises ("deduction", not "you'll save").
3. Render: `python3 social/shorts.py social/shorts/specs/<file>.json /home/claude/mfa-hub/shorts/<date>/<slug> --frames 0,1,3,6,10,end`
   (about 3-4 minutes per short; run long batches in the background). It refuses banned words, captions over the
   platform limits, durations outside 12-30 s, any text outside the safe area (top 250 px, bottom 350 px) and any frame
   where nothing is readable (scenes cross-fade: the next one starts 0.3 s before the cut, so no blank frames).
4. **Look at the check frames** (`frames/`) yourself: clipped words, orphans, overlaps. Then move `frames/` out of the
   folder (they are for you, not for Abiha).
5. Output per short: `<slug>.mp4` (1080x1920, H.264/AAC, 30 fps, ≤ 50 MB), `<slug>-cover.jpg`, `INSTAGRAM.txt`,
   `YOUTUBE.txt`, `PINTEREST.txt`, `00_SHORT-NOTES.md` (beats, UTM links, comment keyword, sync row, sources).
6. Copy the folder to the PC: `C:\Users\MFA\iCloudDrive\Documents\MFA\Social Media Management\Ready to Post\Shorts\<YYYY-MM-DD - Title>\`
   with `device_commit_files`, confirm with `device_list_dir`. Commit the spec (`social: short <slug>`) and push.

### Cadence and who posts where
- **2-3 shorts a week** (for example Tue / Thu / Sat), on top of the daily weekday post. Never two shorts on the same topic
  within 3 weeks; rotate product, value (guide/tool) and service shorts like the post mix.
- **Instagram Reels:** Abiha posts from the Shorts folder (same email flow as daily posts once Zain approves: video link +
  INSTAGRAM.txt in its own box). Reels from @mfa_advisory auto-publish to Pinterest, so a Reel *is* a Pinterest video pin;
  don't upload the same video to Pinterest by hand as well.
  **Hosting for the email:** MP4s are about 10 MB each, too big to attach several. Copy each approved `<slug>.mp4` and
  `<slug>-cover.jpg` to `site/ready/shorts/<batch date>/` (noindex via `/ready/*` in site/_headers), commit
  `shorts: <date> batch for Abiha`, push, wait for the Cloudflare Pages check, then send ONE email listing the schedule
  and, per short, the download links plus the Instagram caption, comment reply, YouTube title/description and Pinterest
  title/description, each in its own box (the 2026-10-24 email is the model).
- **Pinterest direct video pins** (only for shorts that were not posted as a Reel, or a second cut with a different hook):
  the Pinterest daily task may upload 2-3 a week from the Shorts folder, using PINTEREST.txt (title, description,
  destination URL with `utm_source=pinterest&utm_medium=video`, alt text, board). Count them in the daily cap:
  **never more than 5 pins a day in total**, images and videos together.
- **YouTube Shorts:** LIVE on the MFA-Advisory channel (Studio: studio.youtube.com/channel/UCLNPu802SdUCkrjLeIqgM_g; switch to the
  zainmerchant@mfa-advisory.com channel, never Zain's personal one). **Zain (Oct 30): at least one Short published every week.**
  Upload with YOUTUBE.txt (title, description with the UTM link first), "not made for kids", Visibility > Schedule (Tuesdays
  12:00 PM ET). Scheduled as of Oct 30: Oct 30 art-fair-sales-tax, Nov 3 rideshare-miles, Nov 10 1099-2000-rule,
  Nov 17 s-corp-yet, Nov 24 hair-stylist-write-offs, Dec 1 month-end-close. Next batch (render from specs: etsy-1099-k,
  no-1099-still-taxable, set-aside-for-taxes, how-long-keep-receipts, personal-charge-business-card, F-1/H-1B pack)
  must be scheduled from Dec 8 before Nov 24. Keep the queue at least 3 weeks ahead.
- **TikTok / LinkedIn video:** not set up. The same MP4 works on both if Zain wants them later (LinkedIn: post the video
  natively with the LinkedIn-style caption; TikTok would need its own account, which Zain creates).

### Keep everything in sync
- **One topic, one destination.** Each short points to the page that matches it: a guide (`/blog/...`), a tool
  (`/tools/...`), the product's group in `/shop/` or a service page (`/services/`, `/bookkeeping-cleanup/`, `/book/`).
  UTMs: `utm_source=instagram|youtube|pinterest&utm_medium=video&utm_campaign=<slug>` (the renderer writes them). When
  `mfa-advisory.com/start` is live (branch `start-hub`, waiting for Zain), shorts with no product match point there.
- **Same words everywhere.** Use the Pinterest RESEARCH.md phrase as the hook or Pinterest title (e.g. "tax write offs for
  hairstylist", "mileage log for taxes", "month end close checklist"), the same phrase as the product's Etsy title lead
  and, where the Ads agent bids on it, the same search term (`sync` block in the spec records product id, Etsy phrase,
  Ads keywords, blog and matching pin ids).
- **Same story everywhere.** Reuse a Pinterest story pin's angle for its short (p15 "Dana's bank said..." ↔ month-end
  close), so a viewer who sees both recognises the brand.
- **Etsy:** shorts never create Etsy listings. Each new listing costs $0.20 and renews at $0.20; don't flood the shop to
  match a video. Never put the site or a discount for buying elsewhere in an Etsy listing.
- **Fiverr:** never send people from Fiverr off-platform (no site links, emails or "link in bio" in Fiverr messages,
  gigs or deliveries). Shorts may mention Fiverr reviews only as proof, never as a contact route.
- After a short goes live, add a row to `social/log.json` with `"format": "short"` and the platforms it went to.

## Comment-keyword replies
Instagram auto-DMs need a tool such as ManyChat (not set up yet). Until then Zain's helper replies to "TRACKER", "GUIDE"
etc. by hand with the link in `00_POST-NOTES.md`. For shorts, the exact DM reply text is in each `00_SHORT-NOTES.md`
("Comment keyword" line).
