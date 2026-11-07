# TikTok audit: @mfa.advisory (2026-11-06)

Read-only audit of TikTok Studio (Windows PC Chrome, signed in as mfa.advisory) on Nov 6, 2026 around 10:45 PM ET, plus the repo specs (`social/shorts.py`, `social/shorts/specs/`, `social/README.md`, `social/log.json`) and the standing rules in the project's sessions-chat (rule 20: TikTok is faceless, renderer title cards and characters, AI money scenarios). Nothing was posted, edited or changed.

## 1. Numbers rundown

The first post went up Oct 30, so the 7-day, 28-day and 60-day windows show the same totals (TikTok Studio gives no prior-period comparison yet, shown as "--").

| Metric | Last 7 days | Last 28 days | Last 60 days |
|---|---|---|---|
| Video views | 300 | 300 | 300 |
| Impressions | not shown by TikTok Studio | n/a | n/a |
| Total viewers / new viewers | 262 / 262 (28d Viewers tab) | 262 / 262 | n/a |
| Profile views | 3 | 3 | 3 |
| Likes | 4 (per-video rows add to 5) | 4 | 4 |
| Comments | 1 | 1 | 1 |
| Shares | 0 | 0 | 0 |
| Followers | 1 total, net 0 gained in 28d | same | same |
| Link / website clicks | not available: the bio has no clickable link | n/a | n/a |
| Est. rewards | $0.00 | $0.00 | $0.00 |

Daily trend (7-day chart, Oct 30 to Nov 5): about 60 views on Oct 30, about 25 on Oct 31, about 50 on Nov 1, a peak of about 95 on Nov 2, about 55 on Nov 3, then close to zero on Nov 4 and Nov 5.

**Traffic source (account):** For You 98.3%, Search 1.3%, Personal profile 0.4%, Following 0%, Sound 0%.
**Search queries that found us:** "selling art", "taxes on commission", "when do commission money get taxed" (a third each). Search is already sending a few viewers to keyword-led captions.

**Audience (Viewers tab, 28d):** United States 87.7%, Canada 3.4%, Brazil, UK and Puerto Rico 1.5% each. Age 25-34 50.1%, 18-24 25.6%, 35-44 13.7%, 45-54 6.5%, 55+ 4.1%. Male 74%, female 25%. The audience is the right country and age, so **geography is not the problem**.

## 2. Per video

20 posts in Studio: 11 published (Oct 30 to Nov 6), 9 scheduled (Nov 7 to 15). Sound on all: "original sound - mfa.advisory" (the synthesised music bed from `shorts.py`, no voiceover). No "not eligible for For You" or limited-distribution banner was shown anywhere on the web (Studio rows, post analytics, public video page, system notifications). The web does not always show that flag; see "Needs Zain".

| Posted (ET) | Video (hook / caption lead) | Length | Views | Avg watch | Watched full | Likes / comments / shares / saves | Hashtags |
|---|---|---|---|---|---|---|---|
| Oct 30, 7 PM | iPad, paint, shipping: what counts? (art business costs) | 0:27 | 86 | 3.1 s | 4.6% | 1 / 0 / 0 / 0 | #arttok #artbusiness #artist #sellingart #taxtok |
| Oct 31, 12 PM | Selling art: hobby or business? | 0:28 | **0** | n/a | n/a | 0 | #artbusiness #sellingart #artist #taxtips #taxtok |
| Oct 31, 7 PM | Paid for commissions? Set this aside | 0:28 | 54 | 2.3 s | 0% | 2 / 0 / 0 / 1 | #arttok #artbusiness #artist #sellingart #taxtok |
| Nov 1, 12 PM | 3 tax write-offs artists forget | 0:25 | **0** | n/a | n/a | 0 | #taxwriteoffs #artist #taxtok |
| Nov 1, 7 PM | Do artists need an LLC? | 0:29 | 100 | 2.44 s | 1% | 0 / 0 / 0 / 0 | #arttok #artbusiness #artist #sellingart #taxtok |
| Nov 2, 12 PM | Month-end close in 10 steps | 0:25 | **0** | n/a | n/a | 0 | #bookkeeping #smallbusiness #accounting #taxtok |
| Nov 2, 7 PM | Selling at an art fair? Sales tax | 0:26 | 59 | 2.44 s | 0% | 2 / 0 / 0 / 1 | #arttok #artbusiness #artist #sellingart #taxtok |
| Nov 3, 7 PM | ChatGPT said deductible. The rule had changed. | 0:21 | **0** | n/a | n/a | 0 | none |
| Nov 4, 7 PM | You pasted your W-2 into ChatGPT | 0:27 | **0** | n/a | n/a | 0 | none |
| Nov 5, 7 PM | The app scanned your receipt. The IRS wants more. | 0:21 | **0** | n/a | n/a | 0 | none |
| Nov 6, 7 PM | 1099s: the new $2,000 rule | 0:27 | **0** (about 4 h old) | n/a | n/a | 0 | none |

Retention, every video with views: TikTok says "Most viewers stopped watching at 0:01". First-second and 2-second view rates are not shown on these posts (the curve needs more data). The LLC video, the only one past 100 views, got 100% of its views from For You.

Scheduled: Nov 7 hire your kids (7 PM, no hashtags), Nov 8 hair stylist write-offs, Nov 9 S corp, Nov 10 14-day rental, Nov 11 monthly books, Nov 12 artist write-offs (all 7 PM, 5 tags each), Nov 13 IP PIN, Nov 14 AI-made art sales, Nov 15 holiday side gig (5 PM, 5 tags each).

**Upload pattern (decoded from the video IDs):** the four posts that got views were all uploaded together on Oct 30 around 12:20 PM ET for 7 PM slots. The three noon posts were uploaded in a second batch about 4:50 PM ET the same day, and the AI-in-tax set on Nov 3 around 12:10 AM ET. **Every post outside that first batch has 0 views.**

## 3. What the videos look like

Checked on the public pages and in the editor preview (LLC, ChatGPT, art fair, month-end, profile grid), compared with `social/shorts.py` and the specs:

- **Hook (0-2 s):** a static title card: a thin Cormorant Garamond serif headline (one gold italic word) on a dark navy-to-colour gradient, a small Inter sub-line, a small cartoon character, an "ARTISTS · LLC"-style label and a segmented progress bar. Words pop in, but nothing in the frame moves the way a person, a hand or a real object would. In the feed it looks like a slide or an ad.
- **On-screen text:** heavy. 5-7 scenes in 21-29 s, including rows, notes and lists with small text (for example a three-row table plus a footnote in 6.8 s). It cannot be read at feed speed. "Facts checked <date>" and the domain sit on every frame.
- **Voice vs music:** no voiceover (`shorts.py`: "There is no voiceover"). The sound is a synthesised soft bed labelled "original sound". No trending or commercial-library sound.
- **Length:** 21-29 s. Viewers leave at about 2.3-3.1 s, so 90% of every video goes unseen.
- **Captions:** the art set starts with a keyword question, which is good, and search found two of them. The AI set (Nov 3 onward) has no hashtags and a long first line. Captions link to plain-text URLs (mfa-advisory.com/artists), which cannot be tapped on TikTok and carry no UTM.
- **CTA:** an end card reading "Comment *WORD*" plus a URL pill. Almost nobody reaches it (0-4.6% finish), and the whole account has had 1 comment.
- **Sameness:** every video is the same template, fonts and layout, and 6 of the first 8 used the same artist character, link and 5 hashtags. TikTok's For You standards make unoriginal content ineligible when it is "uploaded without any new or creative edits" or carries someone else's watermark. Our videos are original renders without watermarks, so that rule should not apply to them. Still, a run of near-identical slide-style clips with no human element and only a music bed is the kind of low-signal content that gets very little test distribution.
- **Account:** it appears to be a **personal/creator account**. The profile shows no business category, and Studio shows Monetization and "Est. rewards", which is the creator view. Bio: "Tax & bookkeeping tips for small business owners. Book a call: mfa-advisory.com". The domain is **plain text, not a link**. A personal account only gets a clickable bio link at 1,000 followers. A Business account can add a website straight away.
- **Website:** mfa-advisory.com, /artists/, /quarterly-estimated-taxes/, /blog/year-end-tax-planning-2026-key-dates/ and /book/ all return 200.
- **Disclosure:** "Disclose post content > Your brand" is off on the posts checked. TikTok's For You standards list "marketing content that is not disclosed" as ineligible.

## 4. Diagnosis (in order of impact)

1. **Seven of the 11 posts got no distribution at all (0 views).** This is the biggest single problem. Every post since Nov 3 is at 0, while four posts from one upload batch got 54-100 each. A public post with exactly 0 views after 1-4 days usually means it is held: stuck in review, not eligible for For You, or the account was given a very small test pool after its first posts tested badly. The web shows no reason, so it has to be checked in the TikTok app (see "Needs Zain"). Things that likely contributed: posting twice a day from a 1-week-old account with 1 follower, a second batch of near-identical template videos uploaded the same day, and very weak early signals (point 2).
2. **The hook loses people in the first second.** Average watch is 2.3-3.1 s on 21-29 s videos, 0-4.6% watch to the end, and the drop-off is at 0:01 every time. On TikTok, that score decides whether a video gets a second, larger test. The opening frame is a small serif title on a dark card with a cartoon. It has no face, no voice, no movement and no pattern break, and it reads like an ad.
3. **Too long and too dense for the watch time we get.** 5-7 text scenes in about 27 s. Viewers would need to read tables at feed speed. Nobody reaches the tip or the CTA, which is why there are 0 shares, 1 comment and 0 follows.
4. **One repeated format and a mismatched audience signal.** Same template, same character and the same art tags, so TikTok sees one narrow, repetitive pattern. #arttok and #artist put the videos in front of people who want art, not tax help. Meanwhile the search terms prove intent ("taxes on commission").
5. **No route to clicks.** The bio URL can't be tapped, captions have non-clickable URLs without UTMs, and "Comment WORD" only works if someone replies with a DM. Clicks from TikTok are effectively zero and can't be measured.
6. **Search keywords are inconsistent.** The art captions start with a searchable question, and search found them. The AI-in-tax captions (Nov 3+) have no hashtags and bury the keyword. On-screen hook text does not use the words people type ("1099", "self employed tax", "LLC taxes").
7. **Smaller factors:** posting time keeps changing (12 PM and 7 PM, now 5 PM from Nov 13; Nov 7-12 are still at 7 PM). Data is too thin to pick a best hour yet. Audience country and age are fine (87.7% US, 25-34 the largest group).

## 5. Hashtags: needed?

Yes, but they matter less than keywords. TikTok allows 5 hashtags at most (since Aug 2025, per the skill's platform limits). They help TikTok put the video in a topic. The caption's first line, the on-screen hook and the spoken words matter more for search. Use **3-5 per post: 1 broad topic tag + 1-2 niche tags + 1 audience tag**, and put the search phrase itself in the first caption line, in the hook text and in the voiceover.

Recommended sets (pick one row per post):

| Topic | Tags |
|---|---|
| 1099 / gig / side income | #1099 #selfemployed #sidehustle #taxtok |
| Estimated taxes | #estimatedtaxes #selfemployed #1099 #taxtips |
| Late returns | #taxes #irs #taxtips #taxtok |
| LLC / S corp | #llc #smallbusinesstips #businessowner #taxtok |
| Bookkeeping | #bookkeeping #smallbusiness #smallbusinesstips #accountingtok |
| F-1 / OPT students | #f1visa #internationalstudents #studentsinusa #taxtips |
| Etsy / online sellers | #etsyseller #onlineseller #1099k #taxtips |
| Artists (keep, but swap #arttok/#artist) | #artbusiness #sellingart #selfemployed #taxtips |

Rules: no hashtag-only captions; no 5-tag block that repeats across every post; and the caption leads with the searchable phrase. For example: "1099 taxes for side hustles: what to do before January".

## 6. Video changes (format and spec)

**Top 3**
1. **Rebuild the first 2 seconds.** On screen at frame 0 and spoken at the same time: a 2-line hook of at most 8 words in **bold sans-serif** with an outline, large, in the upper third. Movement from frame 0: a hand pointing at a real form on screen, a zoom into an irs.gov page, or a face. Drop the serif title-card look, the small sub-line and the cartoon from the opening. The tracked goal is average watch above 6 s and the 0:01 drop-off gone.
2. **Shorter, one idea per video: 8-15 s to start (up to 20 s only for a 3-step fix).** One problem, one fix, at most 3 short on-screen lines per beat, no tables and no footnotes. Move "Facts checked" and the sources to the caption. Let the end loop back to the hook so replays count.
3. **Add a voice, and some human presence.** A voiceover reads the hook and the steps: Zain, or a consistent AI voice if he wants to stay faceless. TikTok indexes spoken words for search, and voice holds attention far better than a music bed. Ideally 1 in 3 videos uses Zain's face or hands, for example green-screen over an irs.gov page or a screen recording of a real form. That needs Zain because rule 20 says faceless.

**Also**
- Post **1 a day at most**, at one fixed time (5 PM ET, as already agreed), and stop the 12 PM second slot. Don't upload a second batch of near-duplicates on the same day.
- Rotate 4-5 visual formats so the feed isn't one template: green-screen explainer, screen-recording walkthrough, "reply to comment" video, myth vs fact split screen, b-roll with text.
- **Series** people can follow, named in the hook and the caption: "1-minute bookkeeping fix", "Tax myth vs fact", "Gig worker money tip", "F-1 tax check", "LLC 101". Number the episodes (Part 1, Part 2), because numbered series bring people back through the profile.
- Sound: if the account stays personal, a trending sound at low volume under the voice. If it switches to Business, use the Commercial Music Library.
- CTA: spoken, one line, about 1 s ("Full checklist: link in bio"). Keep "Comment WORD" only on posts where someone will actually reply.
- Turn on "Your brand" disclosure for posts that promote our products or services.
- Specs: add a `tiktok` captions block to `shorts.py` (caption ≤ 150 characters before "more", keyword first, 3-5 tags, a 5-tag lint) and a `--voiceover` option. Lower the duration floor from 12 s to 8 s for TikTok cuts.

**5 example hook lines** (on screen + spoken; no prices, MFA copy rules applied):
1. 1099s: "Getting a 1099 in January? Do this before it shows up."
2. Late returns: "Didn't file last year? Not filing costs more than not paying."
3. F-1 students: "F-1 student with zero income? You still have a form to file."
4. LLCs: "Your LLC didn't lower your taxes. Here's what it really does."
5. Bookkeeping: "We ask every new client one question. Most can't answer it."

Check each figure on its primary source before rendering, as usual. Hook 2 rests on IRS failure-to-file vs failure-to-pay penalties, and hook 3 on Form 8843.

## 7. Needs Zain

- **Check the 0-view posts in the TikTok app** (phone): open each 0-view post and look for "Not eligible for the For You feed" / "Under review", and check Settings > Account > Account status for any restriction. If a post shows a flag, appeal it there. Don't re-upload the same file; if needed, recut it with a new hook.
- **Switch to a Business account?** (Settings > Account > Switch to Business Account, category Accounting/Financial services.) Gains: a clickable website in the bio now, plus business analytics. Costs: only the Commercial Music Library (no mainstream trending songs) and no Creator Rewards (which needs 10k followers anyway). Recommendation: switch, because clicks to the site are the goal. Zain's call.
- **Face/voice:** approve a voiceover (his voice or an AI voice) and some on-camera or hands-on-screen videos. This changes rule 20 (faceless).
- **Bio link:** after the switch, use a UTM'd link (for example `mfa-advisory.com/?utm_source=tiktok&utm_medium=social`) or a short TikTok landing page, so clicks can be counted.
- **Schedule:** Nov 7-12 are still at 7 PM (the agreed time is 5 PM). Changing the times means editing scheduled posts, which this read-only audit did not do.

## Sources

- TikTok Studio (Analytics: Overview, Content, Viewers, Followers; Posts; per-post analytics; post editor view), read 2026-11-06.
- Repo: `social/shorts.py` (format, "no voiceover"), `social/shorts/specs/*.json`, `social/README.md`, `social/log.json`; `.projdocs/sessions-chat.md` rules 17 and 20.
- Repo skill: `.claude/skills/social/SKILL.md`, `references/platforms.md`, `references/platform-limits.md` (TikTok max 5 hashtags since Aug 2025), `references/short-form-video.md`.
- [TikTok For You feed Eligibility Standards](https://www.tiktok.com/community-guidelines/en/fyf-standards/?amp=&cgversion=2024H1update&lang=en) (unoriginal content, undisclosed marketing).
- [PiunikaWeb: TikTok videos stuck in review, 0 views (Jan 2026)](https://piunikaweb.com/2026/01/26/tiktok-videos-stuck-review-0-views/) (0 views usually means a held post).
- [Postiz: Why is my TikTok not getting views? A diagnostic guide](https://postiz.com/blog/why-is-my-tiktok-not-getting-views)
- [OpenClip: TikTok slideshow unoriginal content flag](https://openclip.app/guides/tiktok-slideshow-unoriginal-content-flag)
- [Metadata Reactor: TikTok SEO guide 2026](https://metadatareactor.com/blog/tiktok-seo-complete-guide/)
