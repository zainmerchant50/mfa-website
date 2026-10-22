#!/usr/bin/env python3
"""MFA social post renderer (Instagram 1080x1350 + LinkedIn 1200x1200).

Usage:  python3 social/render.py social/posts/2026-10-23-1099-tracker.json OUT_DIR

The post JSON (see social/README.md for every field) holds the copy; this file holds the look, which matches the
batches in iCloud "MFA/Social Media Management": navy-to-accent gradient with grain, gold hairlines, the white MFA
hexagon logo top-left, a gold letterspaced label top-right, Cormorant Garamond headlines, Inter body, and a footer
with info@mfa-advisory.com / mfa-advisory.com plus "General information, not tax advice. Facts checked <date>."

Writes into OUT_DIR:
  NN_<Slug>_INSTAGRAM.png, NN_<Slug>_LINKEDIN.png, NN_<Slug>_INSTAGRAM_caption.txt, NN_<Slug>_LINKEDIN_caption.txt
Needs: playwright (Chromium). Fonts and logo are bundled in social/, so no network is used.
"""
import base64
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCENTS = {  # (mid, deep) colors of the gradient wash; navy is always the start
    "burgundy": ("#6b2a2a", "#3a1414"),
    "amber": ("#7a4a1e", "#2c1a0c"),
    "teal": ("#1d5a5a", "#0b2626"),
    "plum": ("#4e2a5e", "#1e1026"),
    "forest": ("#2a5a3a", "#0e2416"),
    "slate": ("#3a4a66", "#141c2c"),
}
BANNED = [r"\bfree\b", r"\bCPA firm\b", r"\bwe are CPAs?\b", r"\bcertified public accountant", r"\baudit(s|ing)? (services|firm)\b"]


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def font_css():
    out = []
    for fam, f, w, st in [("Cormorant Garamond", "cormorant-garamond-latin-400-normal.woff2", 400, "normal"),
                          ("Cormorant Garamond", "cormorant-garamond-latin-400-italic.woff2", 400, "italic"),
                          ("Cormorant Garamond", "cormorant-garamond-latin-500-normal.woff2", 500, "normal"),
                          ("Cormorant Garamond", "cormorant-garamond-latin-500-italic.woff2", 500, "italic"),
                          ("Inter", "inter-latin-400-normal.woff2", 400, "normal"),
                          ("Inter", "inter-latin-500-normal.woff2", 500, "normal"),
                          ("Inter", "inter-latin-600-normal.woff2", 600, "normal")]:
        out.append(f"@font-face{{font-family:'{fam}';font-style:{st};font-weight:{w};"
                   f"src:url(data:font/woff2;base64,{b64(HERE / 'fonts' / f)}) format('woff2')}}")
    return "\n".join(out)


def rich(s):
    """Escape, then *word* -> gold italic (headline accent)."""
    s = html.escape(s)
    return re.sub(r"\*(.+?)\*", r'<em>\1</em>', s)


def body_html(p, mode):
    lay = p.get("layout", "hero")
    parts = []
    if lay == "hero":
        h = p["hero"]
        parts.append(f'<div class="rule"></div><div class="hero">{html.escape(h["value"])}</div><div class="rule"></div>'
                     f'<div class="cap">{html.escape(h.get("sub", ""))}</div>')
        parts += [f'<p class="txt">{rich(t)}</p>' for t in p.get("body", [])]
    elif lay == "list":
        items = "".join(f'<li><span class="n">{i:02d}</span><div><b>{rich(it["title"])}</b>'
                        f'{"<span>" + rich(it["text"]) + "</span>" if it.get("text") else ""}</div></li>'
                        for i, it in enumerate(p["items"], 1))
        parts.append(f'<ul class="list">{items}</ul>')
        parts += [f'<p class="txt sm">{rich(t)}</p>' for t in p.get("body", [])]
    elif lay == "product":
        pr = p["product"]
        img = HERE / "products" / pr["id"] / pr.get("image", "photo-3.jpg")
        if not img.exists():
            img = HERE / "products" / pr["id"] / "cover.jpg"
        if pr.get("crop"):  # [left, top, right, bottom] as fractions of the photo, to drop empty margins
            from PIL import Image
            import io
            im = Image.open(img).convert("RGB")
            w, h = im.size
            l, t, r, bt = pr["crop"]
            buf = io.BytesIO()
            im.crop((int(l * w), int(t * h), int(r * w), int(bt * h))).save(buf, "JPEG", quality=90)
            data = base64.b64encode(buf.getvalue()).decode()
        else:
            data = b64(img)
        feats = "".join(f"<li>{rich(f)}</li>" for f in pr.get("features", []))
        parts.append(f'<div class="shot"><img src="data:image/jpeg;base64,{data}"/></div>'
                     f'<ul class="feats">{feats}</ul>')
    if p.get("cta_word"):
        parts.append(f'<div class="cta"><span>Comment <b>{html.escape(p["cta_word"])}</b> for the link</span>'
                     f'<i>{html.escape(p.get("link", "mfa-advisory.com"))}</i></div>')
    return "\n".join(parts)


def page(p, W, H, mode):
    mid, deep = ACCENTS.get(p.get("accent", "burgundy"), ACCENTS["burgundy"])
    M = round(W * 0.083)
    s = min(W / 1080, H / 1350)  # type scale (LinkedIn square is shorter, so it scales by height)
    logo = b64(HERE / "assets" / "mfa-logo-white.png")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font_css()}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{position:relative;color:#FDFDFC;font-family:Inter,sans-serif;
background:radial-gradient(ellipse 70% 45% at 78% 30%,{mid}cc 0%,transparent 70%),
linear-gradient(152deg,#0b1a33 0%,#15284a 30%,{mid} 72%,{deep} 100%)}}
body:after{{content:"";position:absolute;inset:0;pointer-events:none;opacity:.22;mix-blend-mode:overlay;
background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")}}
.wrap{{position:absolute;inset:{M}px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.top img{{height:{round(105*s)}px}}
.lab{{color:#B08D3F;font-weight:600;font-size:{round(21*s)}px;letter-spacing:.17em;text-transform:uppercase}}
.hair{{flex-shrink:0;height:1px;background:#B08D3F;opacity:.75;margin:{round(36*s)}px 0 {round(40*s)}px}}
.kick{{color:#E2C98F;font-weight:600;font-size:{round(19*s)}px;letter-spacing:.2em;text-transform:uppercase;margin-bottom:{round(18*s)}px}}
h1{{font-family:'Cormorant Garamond',serif;font-weight:400;font-size:{round(p.get("headline_size", 76)*s)}px;line-height:1.08;text-wrap:balance}}
h1 em,.txt em,.list em,.feats em{{font-style:italic;color:#E2C98F}}
.main{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:{round(18*s)}px}}
.rule{{width:{round(180*s)}px;height:1px;background:#B08D3F;opacity:.7;align-self:center}}
.hero{{font-family:'Cormorant Garamond',serif;font-weight:500;font-size:{round(190*s)}px;line-height:1;text-align:center}}
.cap{{text-align:center;color:#E2C98F;font-weight:600;font-size:{round(21*s)}px;letter-spacing:.17em;text-transform:uppercase;margin-bottom:{round(14*s)}px}}
.txt{{font-size:{round(29*s)}px;line-height:1.45;color:#F1EEE6}}
.txt.sm{{font-size:{round(23*s)}px;color:#D9D4C7}}
.list{{list-style:none;display:flex;flex-direction:column;gap:{round(14*s)}px}}
.list li{{display:flex;gap:{round(22*s)}px;align-items:flex-start;background:rgba(10,18,36,.38);border:1px solid rgba(176,141,63,.45);
border-radius:{round(14*s)}px;padding:{round(18*s)}px {round(24*s)}px}}
.list .n{{font-family:'Cormorant Garamond',serif;font-size:{round(46*s)}px;line-height:1;color:#B08D3F;min-width:{round(54*s)}px}}
.list b{{display:block;font-weight:600;font-size:{round(26*s)}px;line-height:1.3}}
.list span{{display:block;font-size:{round(21*s)}px;line-height:1.4;color:#D9D4C7;margin-top:4px}}
.shot{{border-radius:{round(16*s)}px;overflow:hidden;border:1px solid rgba(176,141,63,.6);box-shadow:0 {round(24*s)}px {round(60*s)}px rgba(0,0,0,.45)}}
.shot img{{display:block;width:100%;max-height:{round((560 if mode == "ig" else 470)*s)}px;object-fit:cover;object-position:top}}
.feats{{list-style:none;display:flex;flex-wrap:wrap;gap:{round(10*s)}px {round(26*s)}px;font-size:{round(22*s)}px;color:#F1EEE6}}
.feats li:before{{content:"\\203A";color:#B08D3F;margin-right:10px;font-weight:600}}
.cta{{display:flex;justify-content:space-between;align-items:center;background:#B08D3F;color:#10233F;border-radius:{round(12*s)}px;
padding:{round(16*s)}px {round(24*s)}px;font-size:{round(24*s)}px}}
.cta b{{font-weight:600;letter-spacing:.08em}} .cta i{{font-style:normal;font-weight:600;font-size:{round(21*s)}px}}
.disc{{font-size:{round(17*s)}px;color:#BDB7A8;margin-top:{round(20*s)}px}}
.foot{{border-top:1px solid rgba(176,141,63,.75);margin-top:{round(22*s)}px;padding-top:{round(22*s)}px;display:flex;justify-content:space-between;
font-size:{round(24*s)}px;letter-spacing:.06em}}
.foot span:last-child{{color:#B08D3F;font-weight:500}}
</style></head><body><div class="wrap">
<div class="top"><img src="data:image/png;base64,{logo}"/><div class="lab">{html.escape(p["label"])}</div></div>
<div class="hair"></div>
{f'<div class="kick">{html.escape(p["kicker"])}</div>' if p.get("kicker") else ""}
<h1>{rich(p["headline"])}</h1>
<div class="main">{body_html(p, mode)}</div>
<div class="disc">General information, not tax advice. Facts checked {html.escape(p["checked"])}.</div>
<div class="foot"><span>info@mfa-advisory.com</span><span>mfa-advisory.com</span></div>
</div></body></html>"""


def lint(p):
    """Hard project rules: never "free", never CPA claims, no street address."""
    text = json.dumps(p, ensure_ascii=False)
    errs = [f"banned phrase matched: {b}" for b in BANNED if re.search(b, text, re.I)]
    if re.search(r"\d+\s+\w+\s+(Street|St\.|Avenue|Ave\.|Road|Rd\.|Suite)\b", text):
        errs.append("looks like a street address")
    for k in ("number", "slug", "label", "headline", "checked", "ig_caption", "li_caption", "sources"):
        if not p.get(k):
            errs.append(f"missing field: {k}")
    return errs


def main(spec, out):
    p = json.loads(Path(spec).read_text(encoding="utf-8"))
    errs = lint(p)
    if errs:
        sys.exit("POST REJECTED\n- " + "\n- ".join(errs))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    base = f'{int(p["number"]):02d}_{p["slug"]}'
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for mode, W, H, tag in (("ig", 1080, 1350, "INSTAGRAM"), ("li", 1200, 1200, "LINKEDIN")):
            pg = b.new_page(viewport={"width": W, "height": H})
            pg.set_content(page(p, W, H, mode), wait_until="load")
            pg.evaluate("document.fonts.ready")
            # overflow guard: the footer must sit inside the canvas
            over = pg.evaluate("(()=>{const f=document.querySelector('.foot').getBoundingClientRect();"
                               "const m=document.querySelector('.main');return f.bottom>innerHeight-20||m.scrollHeight>m.clientHeight+2})()")
            if over and "--force" not in sys.argv:
                sys.exit(f"LAYOUT OVERFLOW on {tag}: shorten the copy in {spec}")
            pg.screenshot(path=str(out / f"{base}_{tag}.png"))
        b.close()
    (out / f"{base}_INSTAGRAM_caption.txt").write_text(p["ig_caption"].strip() + "\n", encoding="utf-8")
    (out / f"{base}_LINKEDIN_caption.txt").write_text(p["li_caption"].strip() + "\n", encoding="utf-8")
    print(out / base)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
