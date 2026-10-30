#!/usr/bin/env python3
"""MFA thumbnail / cover renderer for every vertical video (YouTube Shorts, Instagram Reels, TikTok, Facebook Reels,
Pinterest video pins). Hub, 2026-10-30, after Zain flagged Shorts tiles showing "Comment LLC" / "?" end frames.

Usage:
  python3 social/thumbs.py social/shorts/specs/<spec>.json [more specs...] OUT_DIR
Writes OUT_DIR/<slug>-thumb.jpg (1080x1920, < 2 MB) and OUT_DIR/<slug>-thumb-grid.jpg (the 3:4 crop that the
Instagram / TikTok profile grids show, for checking). shorts.py uses cover() for <slug>-cover.jpg.

Spec field (optional, preferred):  "thumb": {"title": "Do artists need an *LLC*?", "sub": "What it changes for taxes"}
  title: the topic in 3-7 plain words, readable on a phone grid (*word* = gold italic). Never "Comment WORD", never
  a bare "?" and never the end card. sub: 2-6 words of context. Falls back to hook.text / hook.sub.
Rules (checked): title <= 7 words / 44 chars, sub <= 48 chars, no banned words, no prices ($ + digits is allowed
only for tax thresholds, e.g. "$2,000 rule"), everything inside the 3:4 centre crop (y 240-1680).
"""
import base64
import html
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render as R  # noqa: E402

W, H = 1080, 1920
CROP = (240, 1680)  # 3:4 centre crop used by Instagram/TikTok grids
PRICE = re.compile(r"\$\s?\d[\d,]*(\.\d+)?\s*(/|per\b|a month|monthly|flat|fee)", re.I)


def texts(p):
    t = p.get("thumb") or {}
    title = t.get("title") or p["hook"]["text"]
    sub = t.get("sub") if "sub" in t else p["hook"].get("sub", "")
    return title, sub or ""


def lint(p):
    title, sub = texts(p)
    plain = re.sub(r"\*", "", title)
    errs = []
    if len(plain.split()) > 7 or len(plain) > 44:
        errs.append(f"thumb title too long ({len(plain.split())} words / {len(plain)} chars): {plain!r}")
    if len(sub) > 48:
        errs.append(f"thumb sub too long ({len(sub)} chars)")
    low = (plain + " " + sub).lower()
    if re.search(r"\bcomment\b", low) or plain.strip() in {"?", ""}:
        errs.append("thumb must name the topic (no 'Comment WORD', no bare '?')")
    for b in R.BANNED:
        if re.search(b, low, re.I):
            errs.append(f"banned wording: {b}")
    if PRICE.search(plain + " " + sub):
        errs.append("no prices on social covers")
    return errs


def char_b64(p):
    ch = (p.get("character") or {}).get("name")
    if not ch:
        return None
    import shorts_characters as SC  # pycairo
    im = SC.render(ch, 3.2, 640, 640, pop=False)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def page(p):
    title, sub = texts(p)
    mid, deep = R.ACCENTS.get(p.get("accent", "slate"), R.ACCENTS["slate"])
    logo = R.b64(HERE / "assets" / "mfa-logo-white.png")
    ch = char_b64(p)
    n = len(re.sub(r"\*", "", title))
    size = 150 if n <= 18 else 132 if n <= 26 else 116 if n <= 34 else 102
    char_html = f'<img class="ch" src="data:image/png;base64,{ch}"/>' if ch else '<div class="noch"></div>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{R.font_css()}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px}}
body{{background:radial-gradient(120% 80% at 80% 15%,{mid} 0%,transparent 60%),linear-gradient(165deg,#0f1c33 0%,{deep} 100%);
  color:#fff;font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.in{{position:absolute;left:90px;right:90px;top:{CROP[0] + 40}px;bottom:{H - CROP[1] + 40}px;display:flex;flex-direction:column}}
.hd{{display:flex;justify-content:space-between;align-items:center}}
.hd img{{height:78px}}
.lab{{font-weight:600;font-size:30px;letter-spacing:.2em;text-transform:uppercase;color:#d9b75f}}
.rule{{height:4px;background:#c9a24a;width:150px;margin:44px 0 0}}
h1{{font-family:'Cormorant Garamond',serif;font-variant-numeric:lining-nums;font-weight:500;font-size:{size}px;line-height:1.02;margin-top:40px;letter-spacing:-.01em}}
h1 em{{color:#e6c477;font-style:italic}}
.sub{{font-size:50px;line-height:1.25;color:rgba(255,255,255,.92);margin-top:34px;font-weight:500}}
.ch{{width:560px;height:560px;align-self:center;margin-top:auto}}
.noch{{margin-top:auto}}
.ft{{border-top:2px solid rgba(201,162,74,.6);padding-top:22px;display:flex;justify-content:space-between;font-size:30px;color:#e6c477;letter-spacing:.08em;font-weight:500}}
</style></head><body><div class="in">
<div class="hd"><img src="data:image/png;base64,{logo}"/><div class="lab">{html.escape(p.get("label", ""))}</div></div>
<div class="rule"></div>
<h1>{R.rich(title)}</h1>
{f'<div class="sub">{html.escape(sub)}</div>' if sub else ''}
{char_html}
<div class="ft"><span>Tax · Bookkeeping</span><span>mfa-advisory.com</span></div>
</div></body></html>"""


def cover(p, pw_browser=None):
    """JPEG bytes of the 1080x1920 thumbnail. Raises SystemExit on lint errors or overflow."""
    errs = lint(p)
    if errs:
        sys.exit("THUMB REJECTED (" + p.get("slug", "?") + ")\n- " + "\n- ".join(errs))
    from playwright.sync_api import sync_playwright
    own = pw_browser is None
    ctx = sync_playwright().start() if own else None
    br = ctx.chromium.launch() if own else pw_browser
    pg = br.new_page(viewport={"width": W, "height": H})
    pg.route("http*://**", lambda r: r.abort())
    pg.set_content(page(p), wait_until="load")
    pg.evaluate("document.fonts.ready")
    over = pg.evaluate("""()=>{const r=document.querySelector('.in').getBoundingClientRect();
      return [...document.querySelectorAll('.in *')].filter(e=>{const b=e.getBoundingClientRect();
      return b.bottom>r.bottom+1||b.right>r.right+1||b.top<r.top-1}).map(e=>e.className||e.tagName)}""")
    gap = pg.evaluate("""()=>{const s=document.querySelector('.sub')||document.querySelector('h1');
      const c=document.querySelector('.ch,.noch');return c.getBoundingClientRect().top-s.getBoundingClientRect().bottom}""")
    if over or gap < 20:
        sys.exit(f"THUMB LAYOUT OVERFLOW ({p.get('slug')}): {over} gap={gap:.0f}px; shorten title/sub")
    jpg = pg.screenshot(type="jpeg", quality=90)
    pg.close()
    if own:
        br.close()
        ctx.stop()
    return jpg


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    out = Path(args[-1])
    out.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for s in args[:-1]:
            p = json.loads(Path(s).read_text(encoding="utf-8"))
            jpg = cover(p, br)
            (out / f"{p['slug']}-thumb.jpg").write_bytes(jpg)
            Image.open(io.BytesIO(jpg)).crop((0, CROP[0], W, CROP[1])).save(out / f"{p['slug']}-thumb-grid.jpg", quality=85)
            print(out / f"{p['slug']}-thumb.jpg")
        br.close()


if __name__ == "__main__":
    main()
