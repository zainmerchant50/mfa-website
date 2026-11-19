#!/usr/bin/env python3
"""MFA shorts renderer: vertical 1080x1920 MP4 for Instagram Reels, YouTube Shorts and Pinterest video pins.

Usage:
  python3 social/shorts.py social/shorts/specs/<date>-<slug>.json OUT_DIR            # MP4 + cover + captions
  python3 social/shorts.py <spec> OUT_DIR --frames 0,1,3,6,10,end                     # also save check frames (PNG)
  python3 social/shorts.py <spec> OUT_DIR --frames-only 0,1,3,end                     # frames only, no video (fast)
  python3 social/shorts.py <spec> OUT_DIR --no-music                                  # silent video

What it makes (OUT_DIR):
  <slug>.mp4            H.264 High, yuv420p, 30 fps, AAC 160k, faststart; 12-30 s, must be <= 50 MB
  <slug>-cover.jpg      1080x1920 cover (the hook frame) for Instagram / Pinterest / YouTube
  INSTAGRAM.txt         Reel caption (+ hashtags, comment keyword, "link in bio")
  YOUTUBE.txt           Shorts title (<= 70 chars) + description with the UTM link
  PINTEREST.txt         video pin title, description, destination URL (UTM), alt text, board
  00_SHORT-NOTES.md     duration, beats, destination, sync (blog/product/ads/Etsy), sources

Look: MFA navy -> accent gradient with grain, gold hairlines, white MFA logo, Cormorant Garamond headlines,
Inter body (fonts and logo bundled in social/, no network). All text stays inside the platform-safe box:
top 250 px and bottom 350 px are kept clear of content (Reels/Shorts/Pinterest UI), sides 96/126 px.
The hook is fully on screen at frame 0. Every beat animates in (word pop, slide, wipe, count-up), a segmented
gold progress bar runs along the top of the safe area, and a soft music bed is synthesised (no samples, no
copyrighted audio). There is no voiceover: the on-screen text is the burned-in caption, so the video works muted.

Spec JSON (see social/shorts/specs/ for real ones):
  date, slug (kebab), title, type (product|value|service), accent (burgundy|amber|teal|plum|forest|slate),
  theme? (paper|neon|vice; omit for the classic navy look: rotate themes so the feed does not repeat),
  label (top-right, short), checked ("October 24, 2026"),
  link {path, anchor?, label}  -> destination page on mfa-advisory.com (UTMs are added per platform),
  hook {text, sub?}  (text supports *accent* = gold italic),
  beats [ {type: story|question|list|stat|values|rows|product|text, ...fields below, dur?} ],
  cta {big? (default "Comment *WORD*"), url, sub?},  captions.dm_reply? (default: thanks + link label + Instagram UTM link)
  captions {comment_word, instagram, hashtags[5-10], youtube_hashtags[3-5 incl #shorts]?, youtube_title (<=70), youtube_description,
            pinterest_title (<=100), pinterest_description (<=500), pinterest_alt, pinterest_board},
  sync {product_id?, etsy_title_phrase?, ads_keywords[], blog?, pin_ids[]}, sources [{fact, url}]
  character? {name: artist|student|worker|owner|driver|mascot-thumbs|mascot-hmm|mascot-wow, scene: hook|none,
              position: lower|upper, corner_after: bool, corner: self|mascot-...}   animated character, drawn by
              social/shorts_characters.py (needs pycairo): large under/over the hook text, then small in the
              bottom-left corner on later scenes whose text leaves that corner clear
Beat fields:
  story    {lines[], kicker?}                         lines slide in one by one (invented first names only)
  question {text}                                     big centred question
  list     {kicker?, items[{t, s?}], start? (number of the first item)}
  stat     {kicker?, value, sub?, from?, count?{to, pre, suf, dec}, note?}
  values   {kicker?, items[{v, l}], note?}            two or three figures side by side
  rows     {kicker?, items[{l, r, ok}], note?}        verdict rows (ok true = gold badge)
  product  {image, kicker?, text, sub?}               image path relative to the repo root
  text     {kicker?, text, sub?}
Rules enforced here: never "free", never a CPA claim, no street address, no clickable-link claims in the video,
no refund/savings promises, 12-30 s, caption length limits. Fix the spec and re-run when it refuses.
"""
import hashlib
import html
import io
import json
import math
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import render as R  # noqa: E402  (fonts, accents, rich(), banned list)

W, H, FPS = 1080, 1920, 30
SAFE = dict(top=250, bottom=H - 350, left=60, right=W - 60)  # nothing may cross these lines
SITE = "https://mfa-advisory.com"
EXTRA_BANNED = [
    r"\bguarantee", r"\brefund", r"\bsave(s)? you\b", r"\byou('ll| will) save\b", r"\bsavings of \$",
    r"\bclick\b", r"\btap (the|this) link\b", r"\bswipe up\b", r"\blink below\b", r"\bIRS logo\b",
    r"\bCPA\b(?! candidate)",
]
STYLE_BANNED = ["here's why", "here's the thing", "unlock", "game changer", "leverage", "navigate", "dive into",
                "thrilled", "excited", "revolutionary", "cutting edge", "transform", "seamless", "robust", "empower",
                "elevate", "let's be honest", "the truth is"]


# ----------------------------------------------------------------------------------------------- checks
def lint(p):
    errs = []
    video_text = json.dumps({k: p.get(k) for k in ("hook", "beats", "cta")}, ensure_ascii=False)
    all_text = json.dumps(p, ensure_ascii=False)
    for b in R.BANNED:
        if re.search(b, all_text, re.I):
            errs.append(f"banned phrase: {b}")
    for b in EXTRA_BANNED:
        hay = video_text if b in (r"\bclick\b", r"\btap (the|this) link\b", r"\bswipe up\b", r"\blink below\b") else all_text
        # source URLs and titles may legitimately contain words like "refund"; check copy only
        hay = re.sub(r'"(url|fact)": "[^"]*"', "", hay)
        if re.search(b, hay, re.I):
            errs.append(f"not allowed: {b}")
    low = all_text.lower()
    errs += [f"style word: {w}" for w in STYLE_BANNED if w in low]
    if re.search(r"\d+\s+\w+\s+(Street|St\.|Avenue|Ave\.|Road|Rd\.|Suite)\b", all_text):
        errs.append("looks like a street address")
    for k in ("date", "slug", "title", "type", "label", "checked", "link", "hook", "beats", "cta", "captions", "sources"):
        if not p.get(k):
            errs.append(f"missing field: {k}")
    if errs:
        return errs
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", p["slug"]):
        errs.append("slug must be kebab-case")
    if not 3 <= len(p["beats"]) <= 7:
        errs.append("beats: 3-7 (plus hook and CTA = 5-9 scenes)")
    c = p["captions"]
    for k in ("comment_word", "instagram", "hashtags", "youtube_title", "youtube_description",
              "pinterest_title", "pinterest_description", "pinterest_alt", "pinterest_board"):
        if not c.get(k):
            errs.append(f"captions.{k} missing")
    if errs:
        return errs
    if len(c["youtube_title"]) > 70:
        errs.append(f"youtube_title is {len(c['youtube_title'])} chars (max 70)")
    if len(c["pinterest_title"]) > 100:
        errs.append(f"pinterest_title is {len(c['pinterest_title'])} chars (max 100)")
    if len(pinterest_description(p)) > 500:
        errs.append(f"pinterest description is {len(pinterest_description(p))} chars (max 500)")
    if "#" in c["pinterest_description"]:
        errs.append("no hashtags in the Pinterest description")
    if not 5 <= len(c["hashtags"]) <= 10:
        errs.append("instagram: 5-10 hashtags (broad + niche; see README hashtag sets)")
    yh = c.get("youtube_hashtags")
    if yh is not None and (not 3 <= len(yh) <= 5 or "#shorts" not in [t.lower() for t in yh]):
        errs.append("youtube_hashtags: 3-5 tags including #shorts")
    if not p["link"]["path"].startswith("/"):
        errs.append("link.path must start with /")
    return errs


# ----------------------------------------------------------------------------------------------- links + captions
def utm(p, source):
    lk = p["link"]
    # niche lanes (niche-views-plan.md §6): utm_campaign=<lane>, utm_content=<slug>
    camp = f"{p['lane']}&utm_content={p['slug']}" if p.get("lane") else p["slug"]
    url = f"{SITE}{lk['path']}?utm_source={source}&utm_medium=video&utm_campaign={camp}"
    return url + (f"#{lk['anchor']}" if lk.get("anchor") else "")


def plain_link(p):
    return "mfa-advisory.com" + p["link"]["path"].rstrip("/")


DISCLAIMER = "General information, not tax advice."
CODE_LINE = "Use code MFASITE10 for 10% off on Etsy or Gumroad."


def instagram_caption(p):
    c = p["captions"]
    parts = [c["instagram"].strip(), "",
             f"Comment {c['comment_word']} and we'll DM you the link. Or visit {plain_link(p)}."]
    if p["type"] == "product":
        parts.append(CODE_LINE)
    parts += ["", DISCLAIMER + " Names in our stories are made up.", "", " ".join(c["hashtags"])]
    return "\n".join(parts)


def youtube_text(p):
    c = p["captions"]
    desc = [f"{p['link']['label']}: {utm(p, 'youtube')}", "", c["youtube_description"].strip()]
    if p["type"] == "product":
        desc.append(CODE_LINE)
    desc += ["", "Merchant Financial Advisory: bookkeeping, tax and advisory for small businesses. Book a call: "
             f"{SITE}/book/?utm_source=youtube&utm_medium=video&utm_campaign={p['slug']}",
             "", DISCLAIMER + " Names in our stories are made up.", "",
             " ".join(c.get("youtube_hashtags") or ["#Shorts", "#SmallBusiness", "#Taxes"])]
    return (f"TITLE ({len(c['youtube_title'])}/70)\n{c['youtube_title']}\n\nDESCRIPTION\n" + "\n".join(desc)
            + f"\n\nPINNED COMMENT\n{p['link']['label']}: {utm(p, 'youtube')}\n")


def dm_reply(p):
    """Exact text to send people who comment the keyword on Instagram (manual DM until ManyChat exists)."""
    c = p["captions"]
    return c.get("dm_reply") or (f"Thanks for commenting {c['comment_word']}! {p['link']['label']}: {utm(p, 'instagram')} "
                                 f"(General information, not tax advice.)")


def pinterest_description(p):
    return p["captions"]["pinterest_description"].strip() + " " + DISCLAIMER


def pinterest_text(p):
    c = p["captions"]
    return (f"TITLE ({len(c['pinterest_title'])}/100)\n{c['pinterest_title']}\n\n"
            f"DESCRIPTION ({len(pinterest_description(p))}/500, no hashtags)\n{pinterest_description(p)}\n\n"
            f"DESTINATION URL\n{utm(p, 'pinterest')}\n\nALT TEXT\n{c['pinterest_alt']}\n\n"
            f"BOARD\n{c['pinterest_board']}\n\nCOVER\n{p['slug']}-cover.jpg (or pick the hook frame at 0 s)\n")


# ----------------------------------------------------------------------------------------------- timeline
def words(s):
    return len(re.sub(r"[*]", "", s).split())


def beat_duration(b):
    if b.get("dur"):
        return float(b["dur"])
    t = b["type"]
    if t == "story":
        return 0.7 + sum(0.45 + words(x) / 4.6 for x in b["lines"])
    if t == "list":
        return 0.9 + sum(0.95 + words(i["t"] + " " + i.get("s", "")) / 7.0 for i in b["items"])
    if t == "rows":
        return 1.2 + 1.3 * len(b["items"]) + (words(b.get("note", "")) / 4.5)
    if t == "question":
        return max(2.0, 0.8 + words(b["text"]) / 3.0)
    if t == "product":
        return 3.0
    if t in ("stat", "values"):
        return 2.2 + words(b.get("sub", "") + " " + b.get("note", "")) / 4.8
    return max(2.2, 0.8 + words(b.get("text", "") + " " + b.get("sub", "")) / 3.6)


def timeline(p):
    scenes = [dict(type="hook", **p["hook"], dur=p["hook"].get("dur") or max(1.8, 0.8 + words(p["hook"]["text"] + " " + p["hook"].get("sub", "")) / 6.0))]
    scenes += [dict(b, dur=beat_duration(b)) for b in p["beats"]]
    scenes.append(dict(type="cta", **p["cta"], dur=p["cta"].get("dur", 3.2)))
    t = 0.0
    for s in scenes:
        s["s"], s["e"] = round(t, 3), round(t + s["dur"], 3)
        t = s["e"]
    return scenes, round(t, 3)


# ----------------------------------------------------------------------------------------------- HTML
def rich_words(text, t0, step=0.07, anim="pop", cls="w"):
    """Split into word spans (keeps *accent* runs) so each word can pop in."""
    toks = []  # (word, accent, glue-to-previous)
    for part in re.split(r"(\*[^*]+\*)", text):
        if not part:
            continue
        acc = len(part) > 1 and part[0] == "*" and part[-1] == "*"
        body = part[1:-1] if acc else part
        for j, w in enumerate(body.split()):
            toks.append((w, acc, j == 0 and bool(toks) and not part[0].isspace() and not acc))
    inners = []
    for w, acc, glue in toks:
        inner = f"<em>{html.escape(w)}</em>" if acc else html.escape(w)
        if glue and inners:
            inners[-1] += inner  # punctuation after an accent stays with its word (no line break before it)
        else:
            inners.append(inner)
    return " ".join(f'<span class="{cls}" data-a="{anim}" data-t="{t0 + i * step:.3f}" data-d=".42">{x}</span>'
                    for i, x in enumerate(inners))


def rr(text):
    """render.rich() plus: hyphenated words (W-9, 1099-NEC, Form 1120-S) never break at the hyphen."""
    return re.sub(r"(?<![<\w/-])([\w$.,]+(?:-[\w$.,]+)+)", r'<span class="nw">\1</span>', R.rich(text))


def img_b64(path):
    import base64
    from PIL import Image
    im = Image.open(REPO / path).convert("RGB")
    if im.width > 1200:
        im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def grain_b64():
    import base64
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(7)
    a = rng.integers(0, 255, (256, 256), dtype=np.uint8)
    im = Image.fromarray(a, "L").convert("RGBA")
    im.putalpha(Image.fromarray((np.full((256, 256), 26)).astype("uint8"), "L"))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def kick(k, t0):
    return f'<div class="kick" data-a="up" data-t="{t0:.3f}">{html.escape(k)}</div>' if k else ""


def fit(s, steps, lead):
    """Squeeze the stagger when a beat has a fixed dur, so the last item is on screen for at least 1.2 s."""
    room = s["dur"] - lead - 1.2
    natural = sum(steps[:-1]) if len(steps) > 1 else 0
    return 1.0 if natural <= room or natural == 0 else max(0.3, room / natural)


def scene_html(s, i, n):
    a, ty = s["s"], s["type"]
    last = "1" if i == n - 1 else "0"
    h = []
    if ty == "hook":
        h.append(f'<div class="hookwrap" data-a="zoom" data-t="0" data-d=".55">'
                 f'<div class="big hook">{rich_words(s["text"], -1.0, 0)}</div>'
                 '<div class="bar" data-a="wipe" data-t="0.15" data-d=".5"></div>'
                 + (f'<div class="sub">{rr(s["sub"])}</div>' if s.get("sub") else "") + '</div>')
    elif ty == "story":
        h.append(kick(s.get("kicker"), a))
        t = a + 0.05
        for line in s["lines"]:
            h.append(f'<div class="line" data-a="left" data-t="{t:.3f}" data-d=".45">{rr(line)}</div>')
            t += (0.45 + words(line) / 4.6) * fit(s, [0.45 + words(x) / 4.6 for x in s["lines"]], 0.05)
    elif ty == "question":
        h.append('<div class="qmark" data-a="pop" data-t="%.3f" data-d=".5">?</div>' % a)
        h.append(f'<div class="big q">{rich_words(s["text"], a + 0.12, 0.09)}</div>')
    elif ty == "list":
        h.append(kick(s.get("kicker"), a))
        t, n0 = a + 0.3, int(s.get("start", 1))
        for j, it in enumerate(s["items"]):
            sub = f'<span>{rr(it["s"])}</span>' if it.get("s") else ""
            h.append(f'<div class="item" data-a="up" data-t="{t:.3f}" data-d=".45"><b class="n">{n0 + j:02d}</b>'
                     f'<div><strong>{rr(it["t"])}</strong>{sub}</div></div>')
            t += (0.95 + words(it["t"] + " " + it.get("s", "")) / 7.0) * fit(
                s, [0.95 + words(x["t"] + " " + x.get("s", "")) / 7.0 for x in s["items"]], 0.3)
        if len(s["items"]) > 4:
            h[0] = h[0].replace('class="kick"', 'class="kick tight"') if h[0] else h[0]
    elif ty == "stat":
        h.append(kick(s.get("kicker"), a))
        if s.get("from"):
            h.append(f'<div class="from" data-a="fade" data-t="{a + .1:.3f}"><s>{html.escape(s["from"])}</s></div>')
        cnt = s.get("count")
        data = ""
        if cnt:
            data = (f' data-count="{cnt["to"]}" data-pre="{html.escape(cnt.get("pre", ""))}" data-suf="{html.escape(cnt.get("suf", ""))}"'
                    f' data-dec="{cnt.get("dec", 0)}" data-ct="{a + .25:.3f}" data-cd="1.1"')
        h.append(f'<div class="stat" data-a="pop" data-t="{a + (.45 if s.get("from") else .2):.3f}" data-d=".55"{data}>{rr(s["value"])}</div>')
        if s.get("sub"):
            h.append(f'<div class="sub c" data-a="up" data-t="{a + .8:.3f}">{rr(s["sub"])}</div>')
        if s.get("note"):
            h.append(f'<div class="note c" data-a="up" data-t="{a + 1.3:.3f}">{rr(s["note"])}</div>')
    elif ty == "values":
        h.append(kick(s.get("kicker"), a))
        cells = "".join(f'<div class="val" data-a="pop" data-t="{a + .25 + j * .45:.3f}" data-d=".5"><b>{rr(v["v"])}</b>'
                        f'<span>{rr(v["l"])}</span></div>' for j, v in enumerate(s["items"]))
        h.append(f'<div class="vals">{cells}</div>')
        if s.get("note"):
            h.append(f'<div class="note c" data-a="up" data-t="{a + .4 + len(s["items"]) * .45:.3f}">{rr(s["note"])}</div>')
    elif ty == "rows":
        h.append(kick(s.get("kicker"), a))
        t = a + 0.3
        for it in s["items"]:
            badge = "yes" if it.get("ok") else "no"
            h.append(f'<div class="row" data-a="left" data-t="{t:.3f}"><span>{rr(it["l"])}</span>'
                     f'<i class="{badge}" data-a="pop" data-t="{t + .45:.3f}">{html.escape(it["r"])}</i></div>')
            t += 1.3 * fit(s, [1.3] * len(s["items"]), 0.3)
        if s.get("note"):
            h.append(f'<div class="note" data-a="up" data-t="{t:.3f}">{rr(s["note"])}</div>')
    elif ty == "product":
        h.append(kick(s.get("kicker"), a))
        h.append(f'<div class="shot" data-a="up" data-t="{a + .1:.3f}" data-d=".6"><img data-a="kb" data-t="{a:.3f}" '
                 f'data-d="{s["dur"]:.3f}" src="data:image/jpeg;base64,{img_b64(s["image"])}"/></div>')
        h.append(f'<div class="ptitle">{rich_words(s["text"], a + .5, .06, "up")}</div>')
        if s.get("sub"):
            h.append(f'<div class="sub" data-a="up" data-t="{a + 1.1:.3f}">{rr(s["sub"])}</div>')
    elif ty == "text":
        h.append(kick(s.get("kicker"), a))
        h.append(f'<div class="big">{rich_words(s["text"], a + .1, .08)}</div>')
        if s.get("sub"):
            h.append(f'<div class="sub" data-a="up" data-t="{a + .7:.3f}">{rr(s["sub"])}</div>')
    elif ty == "cta":
        h.append(f'<div class="big cta">{rich_words(s.get("big", "Link in *bio*"), a + .05, .1)}</div>')
        cls = "url sm" if len(s["url"]) > 26 else "url"  # long page paths (e.g. /international-students) get a smaller pill
        h.append(f'<div class="{cls}" data-a="pop" data-t="{a + .45:.3f}" data-d=".5">{html.escape(s["url"])}</div>')
        if s.get("sub"):
            h.append(f'<div class="sub c" data-a="up" data-t="{a + .8:.3f}">{rr(s["sub"])}</div>')
        h.append(f'<div class="disc" data-a="fade" data-t="{a + 1.0:.3f}">{html.escape(s.get("disc", ""))}</div>')
    else:
        raise SystemExit(f"unknown beat type: {ty}")
    return (f'<section class="scene t-{ty}" data-s="{s["s"]}" data-e="{s["e"]}" data-last="{last}">'
            + "\n".join(x for x in h if x) + "</section>")



THEMES = {  # optional spec "theme": restyles the whole reel (Hub, Nov 3: rotate looks so feeds don't repeat)
    "paper": """
body{color:#10233F;background:linear-gradient(170deg,#FBF8F1 0%,#F4EEE2 60%,#EADFCB 100%)}
#glow{background:radial-gradient(circle,rgba(176,141,63,.18) 0%,transparent 65%)}
#grain{mix-blend-mode:multiply;opacity:.25}
.hd img{filter:brightness(0) saturate(100%) invert(12%) sepia(36%) saturate(1500%) hue-rotate(190deg) brightness(92%)}
.lab,.kick,.qmark,.item .n,.handle{color:#8A2E2E} em{color:#8A2E2E}
.seg{background:rgba(16,35,63,.15)} .seg i{background:#8A2E2E}
.handle{border-top-color:rgba(138,46,46,.45)} .handle span:first-child{color:#5b6475}
.sub{color:#1d2b44} .note,.item span,.disc{color:#4a5468} .from{color:#7b8496}
.stat,.big{color:#10233F} .bar{background:#8A2E2E}
.line,.item,.val,.row{background:rgba(255,255,255,.72);border-color:rgba(16,35,63,.18);box-shadow:0 10px 30px rgba(16,35,63,.08)}
.line{border-left-color:#8A2E2E} .val span{color:#8A2E2E}
.row i.yes{background:#10233F;color:#FBF8F1} .row i.no{border-color:#7b8496;color:#4a5468}
.url{background:#10233F;color:#FBF8F1}
""",
    "vice": """
body{background:linear-gradient(172deg,#1c0638 0%,#4a1170 30%,#a8237f 58%,#ee4a7c 78%,#ff9447 94%,#ffc15e 100%)}
#glow{background:radial-gradient(circle,rgba(255,193,94,.45) 0%,rgba(238,74,124,.18) 42%,transparent 70%)}
.big,.stat,.val b,.ptitle,.from,.item .n{font-family:Inter,sans-serif;font-weight:900;font-style:italic;letter-spacing:-.02em;text-transform:uppercase;text-shadow:5px 5px 0 #1c0638}
.big{font-size:100px} .big.hook{font-size:112px} .stat{font-size:200px}
em{font-style:italic;color:#29f0dc;text-shadow:5px 5px 0 #1c0638,0 0 30px rgba(41,240,220,.5)}
.lab,.kick,.qmark,.item .n,.handle{color:#29f0dc} .seg i{background:#29f0dc} .bar{background:#ff5c9e}
.line,.item,.val,.row{background:rgba(28,6,56,.62);border-color:rgba(41,240,220,.6)}
.line{border-left-color:#ff5c9e} .val span{color:#29f0dc}
.row i.yes{background:#29f0dc;color:#1c0638} .row i.no{border-color:#ff5c9e;color:#ffd3e3}
.url{background:#29f0dc;color:#1c0638}
.handle{border-top-color:rgba(41,240,220,.5)}
body::after{content:"";position:absolute;left:0;right:0;bottom:0;height:400px;background:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDgwIiBoZWlnaHQ9IjQ2MCIgdmlld0JveD0iMCAwIDEwODAgNDYwIj4KPGRlZnM+PGxpbmVhckdyYWRpZW50IGlkPSJzIiB4MT0iMCIgeTE9IjAiIHgyPSIwIiB5Mj0iMSI+PHN0b3Agb2Zmc2V0PSIwIiBzdG9wLWNvbG9yPSIjZmZkMzZlIi8+PHN0b3Agb2Zmc2V0PSIuNTUiIHN0b3AtY29sb3I9IiNmZjdhNTkiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiNlMjNlODYiLz48L2xpbmVhckdyYWRpZW50Pgo8bGluZWFyR3JhZGllbnQgaWQ9InIiIHgxPSIwIiB5MT0iMCIgeDI9IjAiIHkyPSIxIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiMyYTBhNGYiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiMxMjAyMWYiLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz4KPGNpcmNsZSBjeD0iNTQwIiBjeT0iMjUwIiByPSIyMzAiIGZpbGw9InVybCgjcykiIG9wYWNpdHk9Ii45NSIvPjxyZWN0IHg9IjMwMCIgeT0iMTUwIiB3aWR0aD0iNDgwIiBoZWlnaHQ9IjQiIGZpbGw9IiM0YTExNzAiLz48cmVjdCB4PSIzMDAiIHk9IjE3NCIgd2lkdGg9IjQ4MCIgaGVpZ2h0PSI2IiBmaWxsPSIjNGExMTcwIi8+PHJlY3QgeD0iMzAwIiB5PSIxOTgiIHdpZHRoPSI0ODAiIGhlaWdodD0iOCIgZmlsbD0iIzRhMTE3MCIvPjxyZWN0IHg9IjMwMCIgeT0iMjIyIiB3aWR0aD0iNDgwIiBoZWlnaHQ9IjEwIiBmaWxsPSIjNGExMTcwIi8+PHJlY3QgeD0iMzAwIiB5PSIyNDYiIHdpZHRoPSI0ODAiIGhlaWdodD0iMTIiIGZpbGw9IiM0YTExNzAiLz48cmVjdCB4PSIzMDAiIHk9IjI3MCIgd2lkdGg9IjQ4MCIgaGVpZ2h0PSIxNCIgZmlsbD0iIzRhMTE3MCIvPjxyZWN0IHg9IjMwMCIgeT0iMjk0IiB3aWR0aD0iNDgwIiBoZWlnaHQ9IjE2IiBmaWxsPSIjNGExMTcwIi8+CjxyZWN0IHg9IjAiIHk9IjI4MCIgd2lkdGg9IjcyIiBoZWlnaHQ9IjE4MCIgZmlsbD0iIzJhMGE0ZiIvPjxyZWN0IHg9IjI0IiB5PSIyOTQiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjQwIiB5PSIyOTQiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjgiIHk9IjMzOCIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iODIiIHk9IjI3NiIgd2lkdGg9IjcwIiBoZWlnaHQ9IjE4NCIgZmlsbD0iIzJhMGE0ZiIvPjxyZWN0IHg9IjkwIiB5PSIyOTAiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjEzOCIgeT0iMjkwIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI5MCIgeT0iMzM0IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIxNTUiIHk9IjIyNiIgd2lkdGg9IjQ4IiBoZWlnaHQ9IjIzNCIgZmlsbD0iIzJhMGE0ZiIvPjxyZWN0IHg9IjE2MyIgeT0iMjQwIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIxNzkiIHk9IjI0MCIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iMTc5IiB5PSIzMDYiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjIxMyIgeT0iMjA4IiB3aWR0aD0iMzciIGhlaWdodD0iMjUyIiBmaWxsPSIjMmEwYTRmIi8+PHJlY3QgeD0iMjIxIiB5PSIyMjIiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjIzNyIgeT0iMjQ0IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIyMjEiIHk9IjI4OCIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iMjIxIiB5PSIzMTAiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjIzNyIgeT0iMzMyIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIyNTUiIHk9IjI5NyIgd2lkdGg9IjgwIiBoZWlnaHQ9IjE2MyIgZmlsbD0iIzJhMGE0ZiIvPjxyZWN0IHg9IjI2MyIgeT0iMzExIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIyNzkiIHk9IjMxMSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iMzQxIiB5PSIxNzUiIHdpZHRoPSI0NCIgaGVpZ2h0PSIyODUiIGZpbGw9IiMyYTBhNGYiLz48cmVjdCB4PSIzNDkiIHk9IjE4OSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iMzY1IiB5PSIyMzMiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjM5MyIgeT0iMTQ1IiB3aWR0aD0iNDEiIGhlaWdodD0iMzE1IiBmaWxsPSIjMmEwYTRmIi8+PHJlY3QgeD0iNDAxIiB5PSIyMDMiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjQwMSIgeT0iMjI1IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI0MDEiIHk9IjI0NyIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNDQzIiB5PSIxNzciIHdpZHRoPSI0NSIgaGVpZ2h0PSIyODMiIGZpbGw9IiMyYTBhNGYiLz48cmVjdCB4PSI0NTEiIHk9IjM0NSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNDkwIiB5PSIxNjIiIHdpZHRoPSI0NyIgaGVpZ2h0PSIyOTgiIGZpbGw9IiMyYTBhNGYiLz48cmVjdCB4PSI1MTQiIHk9IjE3NiIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNDk4IiB5PSIyNDIiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjUxNCIgeT0iMjQyIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI1MTQiIHk9IjMzMCIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNTQ0IiB5PSIxNjMiIHdpZHRoPSI0NSIgaGVpZ2h0PSIyOTciIGZpbGw9IiMyYTBhNGYiLz48cmVjdCB4PSI1NjgiIHk9IjE3NyIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNTUyIiB5PSIyMjEiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjU2OCIgeT0iMjQzIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI1NTIiIHk9IjI2NSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNTUyIiB5PSIzMDkiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjU1MiIgeT0iMzMxIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI1OTgiIHk9IjEzOSIgd2lkdGg9IjY3IiBoZWlnaHQ9IjMyMSIgZmlsbD0iIzJhMGE0ZiIvPjxyZWN0IHg9IjYzOCIgeT0iMTUzIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI2MjIiIHk9IjIxOSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNjU0IiB5PSIyMTkiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjYwNiIgeT0iMjQxIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI2MjIiIHk9IjI2MyIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNjU0IiB5PSIyNjMiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjY1NCIgeT0iMjg1IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI2NTQiIHk9IjMwNyIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNjM4IiB5PSIzMjkiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjY3MyIgeT0iMTgxIiB3aWR0aD0iNzEiIGhlaWdodD0iMjc5IiBmaWxsPSIjMmEwYTRmIi8+PHJlY3QgeD0iNzEzIiB5PSIxOTUiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjY5NyIgeT0iMjE3IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI3MjkiIHk9IjIxNyIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNzI5IiB5PSIyNjEiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjY4MSIgeT0iMzA1IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI3MTMiIHk9IjMyNyIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNzEzIiB5PSIzNDkiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjcyOSIgeT0iMzQ5IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI3NTQiIHk9IjIzMSIgd2lkdGg9IjU5IiBoZWlnaHQ9IjIyOSIgZmlsbD0iIzJhMGE0ZiIvPjxyZWN0IHg9Ijc5NCIgeT0iMjQ1IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI3OTQiIHk9IjI2NyIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNzYyIiB5PSIyODkiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9Ijc5NCIgeT0iMjg5IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI3NzgiIHk9IjMxMSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iNzYyIiB5PSIzMzMiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjgxOCIgeT0iMjI1IiB3aWR0aD0iNzIiIGhlaWdodD0iMjM1IiBmaWxsPSIjMmEwYTRmIi8+PHJlY3QgeD0iODI2IiB5PSIyMzkiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9Ijg0MiIgeT0iMjM5IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI4NzQiIHk9IjIzOSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iODI2IiB5PSIyODMiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9Ijg1OCIgeT0iMjgzIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI4NzQiIHk9IjMwNSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iODI2IiB5PSIzMjciIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9Ijg0MiIgeT0iMzQ5IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI4NTgiIHk9IjM0OSIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iODk3IiB5PSIyNzciIHdpZHRoPSI2OSIgaGVpZ2h0PSIxODMiIGZpbGw9IiMyYTBhNGYiLz48cmVjdCB4PSI5MDUiIHk9IjMxMyIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iOTY4IiB5PSIyMTQiIHdpZHRoPSIzNiIgaGVpZ2h0PSIyNDYiIGZpbGw9IiMyYTBhNGYiLz48cmVjdCB4PSI5NzYiIHk9IjIyOCIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iOTkyIiB5PSIyMjgiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9Ijk5MiIgeT0iMjUwIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSI5OTIiIHk9IjI3MiIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iOTc2IiB5PSIyOTQiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9Ijk3NiIgeT0iMzE2IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIxMDE0IiB5PSIxNzgiIHdpZHRoPSI3NiIgaGVpZ2h0PSIyODIiIGZpbGw9IiMyYTBhNGYiLz48cmVjdCB4PSIxMDM4IiB5PSIxOTIiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjEwNzAiIHk9IjE5MiIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iMTAzOCIgeT0iMjE0IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIxMDU0IiB5PSIyMTQiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjEwNzAiIHk9IjIxNCIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iMTAzOCIgeT0iMjM2IiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIxMDU0IiB5PSIyMzYiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjEwNzAiIHk9IjIzNiIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+PHJlY3QgeD0iMTA1NCIgeT0iMjgwIiB3aWR0aD0iNiIgaGVpZ2h0PSI5IiBmaWxsPSIjMjlmMGRjIiBvcGFjaXR5PSIuNTUiLz48cmVjdCB4PSIxMDIyIiB5PSIzMjQiIHdpZHRoPSI2IiBoZWlnaHQ9IjkiIGZpbGw9IiMyOWYwZGMiIG9wYWNpdHk9Ii41NSIvPjxyZWN0IHg9IjEwNTQiIHk9IjM0NiIgd2lkdGg9IjYiIGhlaWdodD0iOSIgZmlsbD0iIzI5ZjBkYyIgb3BhY2l0eT0iLjU1Ii8+CjxyZWN0IHg9IjAiIHk9IjM1MiIgd2lkdGg9IjEwODAiIGhlaWdodD0iMTA4IiBmaWxsPSJ1cmwoI3IpIi8+CjxwYXRoIGQ9Ik01NDAgMzUyIEw0NzAgNDYwIE01NDAgMzUyIEw2MTAgNDYwIiBzdHJva2U9IiMyOWYwZGMiIHN0cm9rZS13aWR0aD0iMyIgb3BhY2l0eT0iLjUiLz4KPGxpbmUgeDE9IjAiIHkxPSIzNTIiIHgyPSIxMDgwIiB5Mj0iMzUyIiBzdHJva2U9IiNmZjVjOWUiIHN0cm9rZS13aWR0aD0iMyIgb3BhY2l0eT0iLjgiLz4KPGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoNzAsNDYwKSBzY2FsZSgxLjA1LDEuMDUpIiBmaWxsPSIjMWEwNTMzIj4KPHBhdGggZD0iTS02IDAgQy0yIC0xMzIuMCA4IC0yNDcuNSAxNCAtMzMwIEwyMiAtMzMwIEMxNCAtMjM3LjYgNiAtMTMyLjAgNiAwIFoiLz4KPGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTgsLTMzMCkiPgo8cGF0aCBkPSJNMCAwIEM0MCAtMzAgOTAgLTIwIDEyMCAxMCBDODUgLTUgNDUgLTUgMCAwWiIvPjxwYXRoIGQ9Ik0wIDAgQy00MCAtMzAgLTk1IC0xOCAtMTI1IDEyIEMtODggLTQgLTQ1IC02IDAgMFoiLz4KPHBhdGggZD0iTTAgMCBDMjUgLTQ1IDcwIC03MCAxMTAgLTYwIEM3NSAtNTAgNDAgLTM1IDAgMFoiLz48cGF0aCBkPSJNMCAwIEMtMjUgLTQ1IC03MiAtNjggLTExMiAtNTggQy03NiAtNDggLTQwIC0zNCAwIDBaIi8+CjxwYXRoIGQ9Ik0wIDAgQzEwIC01MCA1IC05MCAtMTUgLTExMCBDMiAtODAgNCAtNDUgMCAwWiIvPjxwYXRoIGQ9Ik0wIDAgQzUwIDUgODUgMzUgOTUgNzAgQzcyIDQ1IDQwIDIyIDAgMFoiLz48cGF0aCBkPSJNMCAwIEMtNTAgNiAtODUgMzggLTkyIDcyIEMtNzAgNDYgLTQwIDI0IDAgMFoiLz48L2c+PC9nPjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKDE5MCw0NjApIHNjYWxlKC0wLjg1LDAuODUpIiBmaWxsPSIjMWEwNTMzIj4KPHBhdGggZD0iTS02IDAgQy0yIC0xMDAuMCA4IC0xODcuNSAxNCAtMjUwIEwyMiAtMjUwIEMxNCAtMTgwLjAgNiAtMTAwLjAgNiAwIFoiLz4KPGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTgsLTI1MCkiPgo8cGF0aCBkPSJNMCAwIEM0MCAtMzAgOTAgLTIwIDEyMCAxMCBDODUgLTUgNDUgLTUgMCAwWiIvPjxwYXRoIGQ9Ik0wIDAgQy00MCAtMzAgLTk1IC0xOCAtMTI1IDEyIEMtODggLTQgLTQ1IC02IDAgMFoiLz4KPHBhdGggZD0iTTAgMCBDMjUgLTQ1IDcwIC03MCAxMTAgLTYwIEM3NSAtNTAgNDAgLTM1IDAgMFoiLz48cGF0aCBkPSJNMCAwIEMtMjUgLTQ1IC03MiAtNjggLTExMiAtNTggQy03NiAtNDggLTQwIC0zNCAwIDBaIi8+CjxwYXRoIGQ9Ik0wIDAgQzEwIC01MCA1IC05MCAtMTUgLTExMCBDMiAtODAgNCAtNDUgMCAwWiIvPjxwYXRoIGQ9Ik0wIDAgQzUwIDUgODUgMzUgOTUgNzAgQzcyIDQ1IDQwIDIyIDAgMFoiLz48cGF0aCBkPSJNMCAwIEMtNTAgNiAtODUgMzggLTkyIDcyIEMtNzAgNDYgLTQwIDI0IDAgMFoiLz48L2c+PC9nPjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKDkzMCw0NjApIHNjYWxlKC0xLDEpIiBmaWxsPSIjMWEwNTMzIj4KPHBhdGggZD0iTS02IDAgQy0yIC0xMjQuMCA4IC0yMzIuNSAxNCAtMzEwIEwyMiAtMzEwIEMxNCAtMjIzLjIgNiAtMTI0LjAgNiAwIFoiLz4KPGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTgsLTMxMCkiPgo8cGF0aCBkPSJNMCAwIEM0MCAtMzAgOTAgLTIwIDEyMCAxMCBDODUgLTUgNDUgLTUgMCAwWiIvPjxwYXRoIGQ9Ik0wIDAgQy00MCAtMzAgLTk1IC0xOCAtMTI1IDEyIEMtODggLTQgLTQ1IC02IDAgMFoiLz4KPHBhdGggZD0iTTAgMCBDMjUgLTQ1IDcwIC03MCAxMTAgLTYwIEM3NSAtNTAgNDAgLTM1IDAgMFoiLz48cGF0aCBkPSJNMCAwIEMtMjUgLTQ1IC03MiAtNjggLTExMiAtNTggQy03NiAtNDggLTQwIC0zNCAwIDBaIi8+CjxwYXRoIGQ9Ik0wIDAgQzEwIC01MCA1IC05MCAtMTUgLTExMCBDMiAtODAgNCAtNDUgMCAwWiIvPjxwYXRoIGQ9Ik0wIDAgQzUwIDUgODUgMzUgOTUgNzAgQzcyIDQ1IDQwIDIyIDAgMFoiLz48cGF0aCBkPSJNMCAwIEMtNTAgNiAtODUgMzggLTkyIDcyIEMtNzAgNDYgLTQwIDI0IDAgMFoiLz48L2c+PC9nPjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKDEwMjAsNDYwKSBzY2FsZSgwLjgsMC44KSIgZmlsbD0iIzFhMDUzMyI+CjxwYXRoIGQ9Ik0tNiAwIEMtMiAtOTIuMCA4IC0xNzIuNSAxNCAtMjMwIEwyMiAtMjMwIEMxNCAtMTY1LjYgNiAtOTIuMCA2IDAgWiIvPgo8ZyB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxOCwtMjMwKSI+CjxwYXRoIGQ9Ik0wIDAgQzQwIC0zMCA5MCAtMjAgMTIwIDEwIEM4NSAtNSA0NSAtNSAwIDBaIi8+PHBhdGggZD0iTTAgMCBDLTQwIC0zMCAtOTUgLTE4IC0xMjUgMTIgQy04OCAtNCAtNDUgLTYgMCAwWiIvPgo8cGF0aCBkPSJNMCAwIEMyNSAtNDUgNzAgLTcwIDExMCAtNjAgQzc1IC01MCA0MCAtMzUgMCAwWiIvPjxwYXRoIGQ9Ik0wIDAgQy0yNSAtNDUgLTcyIC02OCAtMTEyIC01OCBDLTc2IC00OCAtNDAgLTM0IDAgMFoiLz4KPHBhdGggZD0iTTAgMCBDMTAgLTUwIDUgLTkwIC0xNSAtMTEwIEMyIC04MCA0IC00NSAwIDBaIi8+PHBhdGggZD0iTTAgMCBDNTAgNSA4NSAzNSA5NSA3MCBDNzIgNDUgNDAgMjIgMCAwWiIvPjxwYXRoIGQ9Ik0wIDAgQy01MCA2IC04NSAzOCAtOTIgNzIgQy03MCA0NiAtNDAgMjQgMCAwWiIvPjwvZz48L2c+Cjwvc3ZnPg==) center bottom/1080px 400px no-repeat;pointer-events:none}
.handle{top:1470px}
""",
    "neon": """
body{background:linear-gradient(165deg,#05070d 0%,#0a0f1f 55%,#101a33 100%)}
#glow{background:radial-gradient(circle,rgba(62,230,193,.28) 0%,rgba(62,230,193,.08) 40%,transparent 68%)}
.big,.stat,.val b,.ptitle,.from,.item .n{font-family:Inter,sans-serif;font-weight:800;letter-spacing:-.02em}
.big{font-size:104px} .big.hook{font-size:116px} .stat{font-size:220px}
em{font-style:normal;color:#3EE6C1}
.lab,.kick,.qmark,.item .n,.handle{color:#3EE6C1} .seg i{background:#3EE6C1} .bar{background:#FF5C8A}
.line,.item,.val,.row{background:rgba(255,255,255,.05);border-color:rgba(62,230,193,.45)}
.line{border-left-color:#FF5C8A} .val span{color:#3EE6C1}
.row i.yes{background:#3EE6C1;color:#05070d} .url{background:#3EE6C1;color:#05070d}
.handle{border-top-color:rgba(62,230,193,.4)}
""",
}


def page(p, scenes, total):
    mid, deep = R.ACCENTS.get(p.get("accent", "slate"), R.ACCENTS["slate"])
    logo = R.b64(HERE / "assets" / "mfa-logo-white.png")
    segs = "".join(f'<div class="seg" data-s="{s["s"]}" data-e="{s["e"]}"><i></i></div>' for s in scenes)
    body = "\n".join(scene_html(s, i, len(scenes)) for i, s in enumerate(scenes))
    L, Rm, TOP, BOT = 96, 126, 400, H - 1490
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{R.font_css()}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{position:relative;color:#FDFDFC;font-family:Inter,sans-serif;font-variant-numeric:lining-nums;
background:linear-gradient(160deg,#0b1a33 0%,#10233F 34%,{mid} 78%,{deep} 100%)}}
#glow{{position:absolute;width:1500px;height:1500px;left:-210px;top:-200px;border-radius:50%;
background:radial-gradient(circle,{mid}cc 0%,{mid}55 35%,transparent 68%);will-change:transform}}
#grain{{position:absolute;inset:0;background-image:url(data:image/png;base64,{grain_b64()});mix-blend-mode:overlay;opacity:.55}}
.hd{{position:absolute;left:{L}px;right:{Rm}px;top:262px;display:flex;justify-content:space-between;align-items:center}}
.hd img{{height:62px}}
.lab{{color:#B08D3F;font-weight:600;font-size:24px;letter-spacing:.18em;text-transform:uppercase}}
.prog{{position:absolute;left:{L}px;right:{Rm}px;top:350px;display:flex;gap:8px}}
.seg{{flex:1;height:6px;border-radius:3px;background:rgba(255,255,255,.2);overflow:hidden}}
.seg i{{display:block;height:100%;width:0;background:#D8B769}}
.handle{{position:absolute;left:{L}px;right:{Rm}px;top:1500px;display:flex;justify-content:space-between;
font-size:26px;letter-spacing:.12em;color:#D8B769;font-weight:500;border-top:1px solid rgba(176,141,63,.55);padding-top:16px}}
.handle span:first-child{{color:#BDB7A8;letter-spacing:.04em;font-weight:400}}
.scene{{position:absolute;left:{L}px;right:{Rm}px;top:{TOP}px;bottom:{BOT}px;display:none;flex-direction:column;
justify-content:center;gap:30px}}
[data-a]{{will-change:transform,opacity}}
.w{{display:inline-block}}
span.nw{{white-space:nowrap;display:inline!important;margin:0!important;padding:0!important;font-size:inherit!important;color:inherit!important}}
em{{font-style:italic;color:#E2C98F}}
.kick{{color:#D8B769;font-weight:600;font-size:30px;letter-spacing:.18em;text-transform:uppercase}}
.big{{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:112px;line-height:1.04;text-wrap:balance}}
.big.hook{{font-size:128px;line-height:1.0}}
.hookwrap{{display:flex;flex-direction:column;gap:34px;transform-origin:left center}}
.bar{{width:220px;height:5px;background:#B08D3F;border-radius:3px}}
.sub{{font-size:42px;line-height:1.35;color:#F1EEE6;text-wrap:balance}}
.c{{text-align:center}}
.note{{font-size:34px;line-height:1.4;color:#D9D4C7;text-wrap:balance}}
.line{{font-size:54px;line-height:1.28;font-weight:500;background:rgba(10,18,36,.42);border-left:6px solid #B08D3F;
border-radius:14px;padding:24px 30px;text-wrap:balance}}
.t-question{{align-items:center;text-align:center}}
.qmark{{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:260px;line-height:.8;color:#D8B769}}
.big.q{{font-style:italic;font-weight:400;font-size:108px}}
.t-list{{gap:20px}}
.item{{display:flex;gap:26px;align-items:flex-start;background:rgba(10,18,36,.42);border:1px solid rgba(176,141,63,.5);
border-radius:16px;padding:22px 28px}}
.item .n{{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:64px;line-height:.95;color:#D8B769;min-width:70px}}
.item strong{{display:block;font-weight:600;font-size:44px;line-height:1.2;text-wrap:balance}}
.item span{{display:block;font-size:32px;line-height:1.38;color:#D9D4C7;margin-top:6px;text-wrap:pretty}}
.t-list .item:nth-last-child(n+6), .t-list .item:nth-last-child(n+6) ~ .item{{padding:16px 26px}}
.t-stat{{align-items:center;text-align:center}}
.from{{font-family:'Cormorant Garamond',serif;font-size:120px;color:#BDB7A8;line-height:1}}
.from s{{text-decoration-thickness:6px;text-decoration-color:#B08D3F}}
.stat{{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:250px;line-height:.95;color:#FDFDFC}}
.t-values .kick,.t-values .note{{text-align:center}}
.vals{{display:flex;gap:28px;justify-content:center}}
.val{{flex:1;text-align:center;background:rgba(10,18,36,.42);border:1px solid rgba(176,141,63,.55);border-radius:20px;padding:34px 16px}}
.val b{{display:block;font-family:'Cormorant Garamond',serif;font-weight:500;font-size:150px;line-height:1}}
.val span{{display:block;margin-top:14px;font-size:34px;color:#E2C98F;font-weight:500}}
.row{{display:flex;justify-content:space-between;align-items:center;gap:20px;background:rgba(10,18,36,.42);
border:1px solid rgba(176,141,63,.5);border-radius:16px;padding:26px 28px;font-size:44px;font-weight:500}}
.row i{{font-style:normal;font-weight:600;font-size:34px;letter-spacing:.04em;padding:12px 22px;border-radius:40px;white-space:nowrap}}
.row i.yes{{background:#B08D3F;color:#10233F}} .row i.no{{border:2px solid #BDB7A8;color:#E8E4DA}}
.shot{{border-radius:22px;overflow:hidden;border:2px solid rgba(176,141,63,.75);box-shadow:0 30px 70px rgba(0,0,0,.5)}}
.shot img{{display:block;width:100%;transform-origin:center 40%}}
.ptitle{{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:80px;line-height:1.05;text-wrap:balance}}
.t-cta{{align-items:center;text-align:center;gap:38px}}
.big.cta{{font-size:150px}}
.url{{background:#B08D3F;color:#10233F;font-weight:600;font-size:50px;letter-spacing:.02em;border-radius:60px;padding:24px 48px}}
.url.sm{{font-size:32px;padding:22px 32px;white-space:nowrap}}
.disc{{font-size:26px;color:#BDB7A8;line-height:1.4;text-wrap:balance}}
{THEMES.get(p.get("theme", ""), "")}
</style></head><body>
<div id="glow"></div><div id="grain"></div>
<div class="hd"><img src="data:image/png;base64,{logo}"/><div class="lab">{html.escape(p["label"])}</div></div>
<div class="prog">{segs}</div>
{body}
<div class="handle"><span>{html.escape("Facts checked " + p["checked"])}</span><span>mfa-advisory.com</span></div>
<script>
const E={{c:x=>1-Math.pow(1-x,3),b:x=>{{const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)}}}};
const C=x=>Math.max(0,Math.min(1,x));
const TOTAL={total};
function fmt(v,dec){{return v.toLocaleString('en-US',{{minimumFractionDigits:dec,maximumFractionDigits:dec}})}}
const PRE=0.3, OUT=0.22;  // crossfade: the next scene starts entering PRE s before the cut while this one fades over OUT s
function seek(t){{
  document.querySelectorAll('.scene').forEach((s,i)=>{{
    const a=+s.dataset.s,b=+s.dataset.e,last=s.dataset.last==='1',pre=i?PRE:0,tt=t+pre;
    if(t<a-pre-1e-6||(!last&&t>=b)){{s.style.display='none';return}}
    s.style.display='flex';
    const o=last?0:C((t-(b-OUT))/OUT);
    s.style.opacity=1-o; s.style.transform='translateY('+(-46*E.c(o))+'px)';
    s.querySelectorAll('[data-a]').forEach(el=>{{
      const t0=+el.dataset.t,d=+(el.dataset.d||0.45),p=C((tt-t0)/d),k=el.dataset.a;
      if(k==='pop'){{const e=E.b(p);el.style.opacity=C(p*2.6);el.style.transform='scale('+(0.55+0.45*e)+')'}}
      else if(k==='up'){{const e=E.c(p);el.style.opacity=C(p*1.4);el.style.transform='translateY('+(56*(1-e))+'px)'}}
      else if(k==='left'){{const e=E.c(p);el.style.opacity=C(p*1.4);el.style.transform='translateX('+(-90*(1-e))+'px)'}}
      else if(k==='fade'){{el.style.opacity=p}}
      else if(k==='wipe'){{el.style.clipPath='inset(0 '+(100*(1-E.c(p)))+'% 0 0)'}}
      else if(k==='zoom'){{el.style.transform='scale('+(1.07-0.07*E.c(p))+')'}}
      else if(k==='kb'){{el.style.transform='scale('+(1.0+0.09*C((tt-t0)/d))+')'}}
      if(el.dataset.count){{const q=E.c(C((tt-(+el.dataset.ct))/(+el.dataset.cd)));
        el.textContent=el.dataset.pre+fmt((+el.dataset.count)*q,+el.dataset.dec)+el.dataset.suf}}
    }});
  }});
  document.querySelectorAll('.seg').forEach(g=>{{const a=+g.dataset.s,b=+g.dataset.e;
    g.firstChild.style.width=(100*C((t-a)/(b-a)))+'%'}});
  const gx=Math.sin(t*0.35)*120, gy=Math.cos(t*0.27)*160+t*6;
  document.getElementById('glow').style.transform='translate('+gx+'px,'+gy+'px)';
}}
function check(S){{  // every visible element of every scene inside the safe box once it has settled
  const bad=[];
  document.querySelectorAll('.scene').forEach((s,i)=>{{
    const b=+s.dataset.e, last=s.dataset.last==='1';
    seek(last?TOTAL-0.05:b-0.3);
    if(s.scrollHeight>s.clientHeight+2) bad.push('scene '+i+' content taller than the safe area');
    s.querySelectorAll('*').forEach(el=>{{const r=el.getBoundingClientRect();
      if(r.width===0||el.tagName==='IMG') return;
      if(r.top<S.top||r.bottom>S.bottom||r.left<S.left||r.right>S.right)
        bad.push('scene '+i+' '+el.className+' "'+(el.textContent||'').slice(0,40)+'" at '+[r.left,r.top,r.right,r.bottom].map(Math.round));
      if(!el.classList.contains('shot')&&el.scrollWidth>el.clientWidth+2&&getComputedStyle(el).overflow!=='visible') bad.push('scene '+i+' text clipped: '+el.className);
    }});
  }});
  return bad;
}}
function coverage(T){{  // frames where no text or image is at least 40% visible (an empty background between scenes)
  const low=[];
  for(let i=0;i<Math.round(T*30);i++){{const t=i/30; seek(t); let m=0;
    document.querySelectorAll('.scene').forEach(s=>{{if(s.style.display==='none') return;
      s.querySelectorAll('*').forEach(el=>{{
        if(el.tagName!=='IMG'&&(el.children.length||!(el.textContent||'').trim())) return;
        let o=1,x=el; while(x){{const v=x.style.opacity; if(v!=='') o*=parseFloat(v); if(x===s) break; x=x.parentElement}}
        m=Math.max(m,o)}})}});
    if(m<0.4) low.push(t.toFixed(2)+' s ('+m.toFixed(2)+')')}}
  return low;
}}
seek(0);
</script></body></html>"""


# ----------------------------------------------------------------------------------------------- music
def music(path, total, cuts, seed_text):
    """Soft procedural bed: warm pad + bass + quiet plucked arpeggio + light pulse; a soft whoosh into each cut."""
    import numpy as np
    from scipy.signal import butter, lfilter
    sr = 44100
    n = int(sr * total)
    t = np.arange(n) / sr
    rng = np.random.default_rng(int(hashlib.md5(seed_text.encode()).hexdigest()[:8], 16))
    progs = [[(53, 57, 60, 64), (57, 60, 64, 67), (50, 53, 57, 60), (55, 59, 62, 67)],   # Fmaj7 Am7 Dm7 G
             [(48, 52, 55, 59), (57, 60, 64, 67), (53, 57, 60, 64), (55, 59, 62, 65)],   # Cmaj7 Am7 Fmaj7 G7
             [(50, 53, 57, 60), (55, 59, 62, 65), (48, 52, 55, 59), (57, 60, 64, 67)]]   # Dm7 G7 Cmaj7 Am7
    prog = progs[rng.integers(len(progs))]
    bpm = 88 + int(rng.integers(0, 9))
    beat = 60 / bpm
    bar = 4 * beat
    f = lambda m: 440 * 2 ** ((m - 69) / 12)  # noqa: E731
    L = np.zeros(n)
    Rr = np.zeros(n)
    nb = int(math.ceil(total / bar)) + 1
    for k in range(nb):
        ch = prog[k % len(prog)]
        s0 = int(k * bar * sr)
        if s0 >= n:
            break
        ln = int((bar + 1.0) * sr)
        tt = np.arange(ln) / sr
        env = np.minimum(1, tt / 0.5) * np.minimum(1, np.maximum(0, (bar + 1.0 - tt) / 1.0))
        for m in ch:
            for det, side in ((-0.004, 0), (0.004, 1)):
                w = np.sin(2 * np.pi * f(m) * (1 + det) * tt) + 0.18 * np.sin(4 * np.pi * f(m) * (1 + det) * tt)
                seg = 0.055 * env * w
                e = min(n, s0 + ln)
                (L if side == 0 else Rr)[s0:e] += seg[:e - s0]
        # bass: root, an octave down
        bw = 0.16 * env * np.sin(2 * np.pi * f(ch[0] - 12) * tt)
        e = min(n, s0 + ln)
        L[s0:e] += bw[:e - s0]
        Rr[s0:e] += bw[:e - s0]
        # arpeggio: eighth notes over the chord, an octave up
        for j in range(8):
            a0 = s0 + int(j * beat / 2 * sr)
            if a0 >= n:
                break
            m = ch[[0, 1, 2, 3, 2, 1, 2, 3][j]] + 12
            al = int(0.6 * sr)
            ta = np.arange(al) / sr
            pl = (np.sin(2 * np.pi * f(m) * ta) + 0.25 * np.sin(4 * np.pi * f(m) * ta)) * np.exp(-ta * 7) * np.minimum(1, ta / 0.004)
            e = min(n, a0 + al)
            pan = 0.35 + 0.3 * (j % 2)
            L[a0:e] += 0.05 * (1 - pan) * pl[:e - a0]
            Rr[a0:e] += 0.05 * pan * pl[:e - a0]
        # soft pulse on beats 1 and 3
        for j in (0, 2):
            k0 = s0 + int(j * beat * sr)
            if k0 >= n:
                break
            kl = int(0.22 * sr)
            tk = np.arange(kl) / sr
            kk = 0.22 * np.sin(2 * np.pi * (48 * tk + 70 * (1 - np.exp(-tk * 30)) / 30)) * np.exp(-tk * 14)
            e = min(n, k0 + kl)
            L[k0:e] += kk[:e - k0]
            Rr[k0:e] += kk[:e - k0]
    # gentle low-pass on the whole bed
    b, a = butter(2, 3800 / (sr / 2))
    L, Rr = lfilter(b, a, L), lfilter(b, a, Rr)
    # whoosh into each cut: band-limited noise swelling for 0.35 s
    bb, ba = butter(2, [500 / (sr / 2), 4000 / (sr / 2)], btype="band")
    for c in cuts:
        w0, w1 = int((c - 0.35) * sr), int((c + 0.08) * sr)
        if w0 < 0 or w1 > n:
            continue
        nz = lfilter(bb, ba, rng.standard_normal(w1 - w0))
        env = np.sin(np.linspace(0, np.pi, w1 - w0)) ** 2
        L[w0:w1] += 0.05 * env * nz
        Rr[w0:w1] += 0.05 * env * nz
    st = np.stack([L, Rr], 1)
    st /= max(1e-9, np.abs(st).max())
    st *= 0.42  # about -7.5 dBFS peak: a bed, not a song
    fade_in = np.minimum(1, t / 0.08)
    fade_out = np.minimum(1, np.maximum(0, (total - t) / 1.2))
    st *= (fade_in * fade_out)[:, None]
    pcm = (st * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


# ----------------------------------------------------------------------------------------------- main
def parse_times(arg, total):
    out = []
    for x in arg.split(","):
        x = x.strip()
        out.append(total - 0.05 if x == "end" else min(float(x), total - 0.05))
    return out


def on_screen(s):
    """One-line summary of what a scene shows (for 00_SHORT-NOTES.md)."""
    bits = [s.get("kicker"), s.get("from") and f"~~{s['from']}~~", s.get("big"), s.get("text"), s.get("value"), s.get("url")]
    bits += s.get("lines", [])
    for it in s.get("items", []):
        bits.append(" ".join(x for x in (it.get("t"), it.get("v"), it.get("l"), it.get("r")) if x))
    bits += [s.get("sub"), s.get("note")]
    return " / ".join(str(b).replace("*", "").replace("|", "/") for b in bits if b)


def notes_md(p, scenes, total, size_mb):
    c = p["captions"]
    sy = p.get("sync", {})
    rows = "\n".join(f"| {i} | {s['s']:.1f}-{s['e']:.1f} s | {s['type']} | {on_screen(s)} |" for i, s in enumerate(scenes))
    src = "\n".join(f"| {x['fact']} | {x['url']} |" for x in p["sources"])
    return f"""# Short: {p['title']}

- Date made: {p['date']} · Facts checked {p['checked']} · Type: {p['type']}
- File: `{p['slug']}.mp4`, 1080x1920, 30 fps, H.264 + AAC, {total:.1f} s, {size_mb:.1f} MB. Cover: `{p['slug']}-cover.jpg`.
- Music: procedural bed made by social/shorts.py (no copyrighted audio). Platforms may also let you add a trending sound; keep it quiet.
- Destination: {p['link']['label']} → `{SITE}{p['link']['path']}`
  - Instagram (link in bio): `{utm(p, 'instagram')}`
  - YouTube: `{utm(p, 'youtube')}`
  - Pinterest: `{utm(p, 'pinterest')}`
- Comment keyword: **{c['comment_word']}** (end card says "Comment {c['comment_word']}"). DM reply to copy-paste:
  > {dm_reply(p)}
- End card by platform: Instagram Reel = comment keyword, DM the reply above; YouTube Short = UTM link is the first
  line of the description and the pinned comment; Pinterest video pin = the pin links to the page (PINTEREST.txt).
- Sync: product {sy.get('product_id', '-')} · Etsy title phrase "{sy.get('etsy_title_phrase', '-')}" · Ads keywords {', '.join(sy.get('ads_keywords', [])) or '-'} · blog {sy.get('blog', '-')} · Pinterest pins {', '.join(sy.get('pin_ids', [])) or '-'}
- Not posted anywhere yet. Zain reviews the first batch.

## Beats
| # | Time | Type | On screen |
|---|---|---|---|
{rows}

## Sources
| Fact | Source |
|---|---|
{src}
"""


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    spec, out = Path(args[0]), Path(args[1])
    p = json.loads(spec.read_text(encoding="utf-8"))
    p.setdefault("cta", {}).setdefault("disc", f"{DISCLAIMER} Names in our stories are made up.")
    p["cta"].setdefault("big", f"Comment *{p.get('captions', {}).get('comment_word', '')}*")  # Instagram comment-to-DM
    errs = lint(p)
    if errs:
        sys.exit("SHORT REJECTED\n- " + "\n- ".join(errs))
    scenes, total = timeline(p)
    track = None
    if p.get("character"):
        import shorts_characters as SC  # noqa: E402  (pycairo; only loaded when a spec asks for a character)
        track = SC.Track(p["character"], scenes)
    if not 12 <= total <= 30 and "--force" not in args:
        sys.exit(f"DURATION {total:.1f} s is outside 12-30 s: trim or add beats (or set dur on beats)")
    frames_arg = args[args.index("--frames") + 1] if "--frames" in args else None
    only = args[args.index("--frames-only") + 1] if "--frames-only" in args else None
    out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.route("http*://**", lambda r: r.abort())  # everything is inlined; never touch the network
        doc = page(p, scenes, total)
        pg.set_content(track.inject(doc) if track else doc, wait_until="load")
        pg.evaluate("document.fonts.ready")
        bad = pg.evaluate("S=>check(S)", SAFE)
        bad += ["near-empty frame at " + x for x in pg.evaluate(f"coverage({total})")]
        if track:
            bad += track.check(pg)  # hook text clear of the character; notes which scenes leave the corner free
        snap = (lambda tt, **kw: track.composite(pg.screenshot(**kw), tt)) if track else (lambda tt, **kw: pg.screenshot(**kw))
        if bad and "--force" not in args:
            sys.exit("LAYOUT CHECK FAILED (safe area / empty frames) in " + str(spec) + "\n- " + "\n- ".join(bad[:20]))
        for arg in (frames_arg, only):
            if arg:
                fd = out / "frames"
                fd.mkdir(exist_ok=True)
                for tt in parse_times(arg, total):
                    pg.evaluate(f"seek({tt})")
                    (fd / f"{p['slug']}-{tt:05.2f}s.png").write_bytes(snap(tt))
        if only:
            br.close()
            print(out / "frames")
            return
        # cover/thumbnail: dedicated title card from social/thumbs.py (Hub 2026-10-30: platforms otherwise pick
        # an end-card frame like "Comment LLC"). Upload it as the YouTube thumbnail and the IG/TikTok/FB cover.
        import thumbs  # noqa: E402
        (out / f"{p['slug']}-cover.jpg").write_bytes(thumbs.cover(p, br))
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "bed.wav"
            if "--no-music" not in args:
                music(wav, total, [s["s"] for s in scenes[1:]], p["slug"])
            mp4 = out / f"{p['slug']}.mp4"
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-"]
            if wav.exists():
                cmd += ["-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest"]
            cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high", "-level", "4.1",
                    "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-r", str(FPS), "-g", str(FPS * 2), "-movflags", "+faststart", str(mp4)]
            ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            nfr = int(round(total * FPS))
            for i in range(nfr):
                pg.evaluate(f"seek({i / FPS})")
                ff.stdin.write(snap(i / FPS, type="jpeg", quality=93))
            ff.stdin.close()
            if ff.wait() != 0:
                sys.exit("ffmpeg failed")
        br.close()
    size_mb = mp4.stat().st_size / 1e6
    if size_mb > 50:
        sys.exit(f"{mp4} is {size_mb:.1f} MB (> 50 MB): raise -crf")
    (out / "INSTAGRAM.txt").write_text(instagram_caption(p) + "\n", encoding="utf-8")
    (out / "YOUTUBE.txt").write_text(youtube_text(p), encoding="utf-8")
    (out / "PINTEREST.txt").write_text(pinterest_text(p), encoding="utf-8")
    (out / "00_SHORT-NOTES.md").write_text(notes_md(p, scenes, total, size_mb), encoding="utf-8")
    print(f"{mp4}  {total:.1f} s  {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
