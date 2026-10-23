#!/usr/bin/env python3
"""Build Abiha's "Ready to post" email from a post JSON (Social agent / Hub).

Usage: python3 social/email.py social/posts/<date>-<slug>.json "<exact reply text from 00_POST-NOTES.md>" [--note "<one line>"]
Writes /tmp/abiha-email/{subject.txt,body.html,body.txt} for the Gmail send tool (htmlBody + body).

Images must already be live at https://mfa-advisory.com/ready/<date>/<slug>-INSTAGRAM.jpg and -LINKEDIN.jpg
(made by: python3 social/email.py --images <json> <rendered folder>, then commit + push site/ready/).
Layout: each caption sits alone in its own box so Abiha can long-press > Select all > Copy on her phone
and paste straight into LinkedIn / Instagram. Never the word "free"; never "CPA"."""
import html
import json
import sys
from datetime import date
from pathlib import Path

SITE = "https://mfa-advisory.com"
OUT = Path("/tmp/abiha-email")


def images(post_json, rendered):
    from PIL import Image
    p = json.load(open(post_json))
    d = Path(__file__).resolve().parent.parent / "site" / "ready" / p["date"]
    d.mkdir(parents=True, exist_ok=True)
    for kind in ("INSTAGRAM", "LINKEDIN"):
        src = next(Path(rendered).glob(f"*_{kind}.png"))
        Image.open(src).convert("RGB").save(d / f"{p['slug']}-{kind}.jpg", "JPEG", quality=92, optimize=True, progressive=True)
    print(d)


def box(label, text, accent):
    t = html.escape(text.strip()).replace("\n", "<br>")
    return (f'<p style="margin:22px 0 6px;font:600 13px Arial,sans-serif;letter-spacing:.06em;color:{accent};text-transform:uppercase">{label}</p>'
            f'<div style="border:2px solid {accent};border-radius:10px;padding:14px 16px;background:#ffffff;'
            f'font:15px/1.5 Arial,sans-serif;color:#111">{t}</div>')


def build(post_json, reply, note=""):
    p = json.load(open(post_json))
    d = date.fromisoformat(p["date"])
    day = d.strftime("%a %b ") + str(d.day)
    title = p["slug"].replace("-", " ")
    word = p["cta_word"]
    t = p.get("post_times", {})
    li_t, ig_t = t.get("linkedin", "8:00 AM ET"), t.get("instagram", "12:00 PM ET")
    img = {k: f"{SITE}/ready/{p['date']}/{p['slug']}-{k}.jpg" for k in ("INSTAGRAM", "LINKEDIN")}
    subject = f"Ready to post: {day} - {title} (LinkedIn + Instagram)"

    def img_block(k, name):
        return (f'<p style="margin:6px 0"><a href="{img[k]}" style="color:#7a1f2b;font-weight:600">Download the {name} image (full size)</a></p>'
                f'<img src="{img[k]}" alt="{name} image" width="260" style="width:260px;max-width:100%;border-radius:8px;border:1px solid #ddd">')

    h = f"""<div style="max-width:620px;font:15px/1.55 Arial,sans-serif;color:#111">
<p>Hi Abiha,</p>
<p>{day}'s posts are ready and final. Nothing needs editing.{(' ' + html.escape(note)) if note else ''}</p>
<p style="margin:16px 0 4px"><b>1. LinkedIn, {day}, {li_t}</b><br>Save the LinkedIn image, then copy the LinkedIn caption box below and paste it as is.</p>
{img_block("LINKEDIN", "LinkedIn")}
{box("LinkedIn caption (copy everything in this box)", p["li_caption"], "#0a66c2")}
<p style="margin:26px 0 4px"><b>2. Instagram, {day}, {ig_t}</b><br>Save the Instagram image (keep the 4:5 crop), then copy the Instagram caption box below.</p>
{img_block("INSTAGRAM", "Instagram")}
{box("Instagram caption (copy everything in this box)", p["ig_caption"], "#c13584")}
<p style="margin:26px 0 4px"><b>3. Comments during the day</b><br>When someone comments <b>{html.escape(word)}</b>, send this (Instagram: as a DM; LinkedIn: as a reply to their comment):</p>
{box("Reply to send", reply, "#555555")}
<p style="margin:24px 0 0">Thanks,<br>Zain</p></div>"""

    txt = (f"Hi Abiha,\n\n{day}'s posts are ready and final. Nothing needs editing.{(' ' + note) if note else ''}\n\n"
           f"1. LinkedIn, {day}, {li_t}\nImage: {img['LINKEDIN']}\n\n----- LINKEDIN CAPTION (copy from here) -----\n{p['li_caption'].strip()}\n----- END -----\n\n"
           f"2. Instagram, {day}, {ig_t}\nImage (keep the 4:5 crop): {img['INSTAGRAM']}\n\n----- INSTAGRAM CAPTION (copy from here) -----\n{p['ig_caption'].strip()}\n----- END -----\n\n"
           f"3. When someone comments {word}, send this (Instagram: DM; LinkedIn: comment reply):\n{reply}\n\nThanks,\nZain\n")
    import re
    assert not re.search(r"\bfree\b", txt, re.I) and not re.search(r"\bCPA\b", txt), "banned word"
    OUT.mkdir(exist_ok=True)
    (OUT / "subject.txt").write_text(subject)
    (OUT / "body.html").write_text(h)
    (OUT / "body.txt").write_text(txt)
    print(subject)
    print(img["INSTAGRAM"], img["LINKEDIN"], sep="\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--images":
        images(a[1], a[2])
    else:
        note = a[a.index("--note") + 1] if "--note" in a else ""
        build(a[0], a[1], note)
