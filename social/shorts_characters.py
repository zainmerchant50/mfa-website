#!/usr/bin/env python3
"""MFA shorts characters: original flat-vector animated characters for social/shorts.py.

Every character is drawn in code with cairo (vector, anti-aliased, transparent background), in MFA's palette:
navy #10233F, gold #B08D3F, cream, plus one soft accent per niche. No text in the art, no outside images.

  artist         at an easel; the brush paints a landscape stroke by stroke (one-shot 2.5 s), then idle dabs + blink
  student        F-1 student with backpack at a laptop; a form fills in and checks pop (2.5 s), then typing + head tilt
  worker         H-1B professional with laptop bag + suitcase; calendar pages flip, office windows light up
  owner          shop owner behind a counter; a receipt prints and coins drop into a jar
  driver         rideshare / delivery car; route draws on a map card, odometer rolls, wheels and road move
  mascot-thumbs  Ledger, a small ledger-book mascot: thumbs up         (one-shot 1.3 s, then idle)
  mascot-hmm     ... thinking (hand on chin, thought dots)
  mascot-wow     ... surprised (hop, wide eyes, burst)

API (used by shorts.py through Track):
  render(name, t, w, h, alpha=1.0, backdrop=True) -> PIL RGBA image (w x h), character fitted bottom-centre
  CHARACTERS[name].render(t, w, h)                -> same, per character
  Track(spec["character"], scenes)                -> places the character in a short: large in the hook, small in a
                                                     corner on later beats whose text leaves the corner clear
CLI:
  python3 social/shorts_characters.py preview OUT_DIR [names...]   1080x1920 MP4 per character (navy background)
  python3 social/shorts_characters.py sheet OUT_DIR                characters-sheet.jpg (frames at 0/0.8/1.6/2.4/3.2 s)
  python3 social/shorts_characters.py frame NAME T OUT.png [W H]   one frame
  python3 social/shorts_characters.py bench                        render speed per character

Needs pycairo (pip install pycairo --break-system-packages), Pillow, numpy, ffmpeg for previews.
"""
import io
import math
import subprocess
import sys
from pathlib import Path

import cairo
from PIL import Image

TAU = 2 * math.pi
FW, FH, FPS = 1080, 1920, 30

# ------------------------------------------------------------------------------------------------ colour
_cache = {}


def col(h, a=1.0):
    if isinstance(h, tuple):
        return h if len(h) == 4 else (*h, a)
    k = (h, a)
    if k not in _cache:
        s = h.lstrip("#")
        _cache[k] = (int(s[0:2], 16) / 255, int(s[2:4], 16) / 255, int(s[4:6], 16) / 255, a)
    return _cache[k]


def mix(a, b, k):
    a, b = col(a), col(b)
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(4))


def dk(h, k=0.14):
    return mix(h, "#000000", k)


def lt(h, k=0.14):
    return mix(h, "#FFFFFF", k)


NAVY, GOLD, GOLD_L, GOLD_P = "#10233F", "#B08D3F", "#D8B769", "#E2C98F"
CREAM, PAPER, WHITE, INK = "#F1EEE6", "#FBF8F1", "#FDFDFC", "#16202F"
TEAL, TEAL_D, PLUM, BURG, SLATE = "#3E8C86", "#2E6E68", "#8E4F6E", "#8C3B4A", "#3B5578"
WOOD, WOOD_D = "#A9803F", "#7A5A2B"
BLUSH = "#E0786F"


# ------------------------------------------------------------------------------------------------ timing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def seg(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def lerp(a, b, k):
    return a + (b - a) * k


def e_out(x):
    return 1 - (1 - x) ** 3


def e_inout(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def e_back(x, s=1.70158):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def smooth01(x):
    return x * x * (3 - 2 * x)


def blink(t, phase=0.0):
    """Eye openness 0..1: a quick blink roughly every 3-4 s at irregular intervals."""
    o = 1.0
    for per, ph in ((3.7, 0.0), (5.3, 1.9)):
        x = (t + phase + ph) % per
        if x < 0.16:
            o = min(o, abs(x - 0.08) / 0.08)
    return o


# ------------------------------------------------------------------------------------------------ drawing primitives
def src(c, h, a=1.0):
    c.set_source_rgba(*col(h, a))


def fill(c, h, a=1.0, keep=False):
    src(c, h, a)
    c.fill_preserve() if keep else c.fill()


def stroke(c, h, w, a=1.0, cap=cairo.LINE_CAP_ROUND, keep=False):
    src(c, h, a)
    c.set_line_width(w)
    c.set_line_cap(cap)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.stroke_preserve() if keep else c.stroke()


def rrect(c, x, y, w, h, r):
    r = max(0.0, min(r, w / 2, h / 2))
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()


def ell(c, cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    if rx <= 0 or ry <= 0:
        return
    c.save()
    c.translate(cx, cy)
    c.scale(rx, ry)
    c.new_sub_path()
    c.arc(0, 0, 1, 0, TAU)
    c.restore()


def poly(c, pts, close=True):
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    if close:
        c.close_path()


def catmull(pts, closed=False, n=10):
    """Smooth sample points through pts (Catmull-Rom)."""
    out = []
    m = len(pts)
    rng = range(m if closed else m - 1)
    for i in rng:
        p0 = pts[(i - 1) % m] if (closed or i > 0) else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if (closed or i + 2 < m) else pts[-1]
        for j in range(n):
            u = j / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u3) for k in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def blob(c, pts):
    """Closed smooth shape through pts."""
    poly(c, catmull(pts, closed=True, n=8))


def cumlen(pts):
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return L


def prefix(pts, L, frac):
    """Points of the polyline up to frac of its length, and the end point."""
    target = clamp(frac) * L[-1]
    out = [pts[0]]
    for i in range(1, len(pts)):
        if L[i] <= target:
            out.append(pts[i])
        else:
            k = (target - L[i - 1]) / max(1e-9, L[i] - L[i - 1])
            p = (lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k))
            out.append(p)
            return out, p
    return out, pts[-1]


def circle_pts(cx, cy, r, turns=1.0, a0=-math.pi / 2, n=40):
    return [(cx + r * math.cos(a0 + TAU * turns * i / n), cy + r * math.sin(a0 + TAU * turns * i / n)) for i in range(n + 1)]


def ik(s, t, l1, l2, bend=1):
    dx, dy = t[0] - s[0], t[1] - s[1]
    d = clamp(math.hypot(dx, dy), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    a = math.atan2(dy, dx)
    A = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    if bend == 0:  # pick the elbow that hangs lower (natural for most poses)
        e1 = (s[0] + l1 * math.cos(a + A), s[1] + l1 * math.sin(a + A))
        e2 = (s[0] + l1 * math.cos(a - A), s[1] + l1 * math.sin(a - A))
        return (e1 if e1[1] >= e2[1] else e2), (s[0] + d * math.cos(a), s[1] + d * math.sin(a))
    ang = a + bend * A
    return (s[0] + l1 * math.cos(ang), s[1] + l1 * math.sin(ang)), (s[0] + d * math.cos(a), s[1] + d * math.sin(a))


def shadow(c, cx, cy, rx, ry=None, a=0.28):
    ry = ry or rx * 0.12
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0, 0.02, 0.05, 0.1, a)
    g.add_color_stop_rgba(0.65, 0.02, 0.05, 0.1, a * 0.75)
    g.add_color_stop_rgba(1, 0.02, 0.05, 0.1, 0)
    c.save()
    c.translate(cx, cy)
    c.scale(rx, ry)
    c.arc(0, 0, 1, 0, TAU)
    c.set_source(g)
    c.fill()
    c.restore()


def sparkle(c, x, y, r, h=GOLD_L, a=1.0, rot=0.0):
    """Four-point star."""
    if r <= 0.5:
        return
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.move_to(0, -r)
    for k in range(4):
        a1 = -math.pi / 2 + k * math.pi / 2
        c.curve_to(0.12 * r * math.cos(a1 + 0.6), 0.12 * r * math.sin(a1 + 0.6), 0.12 * r * math.cos(a1 + 0.97),
                   0.12 * r * math.sin(a1 + 0.97), r * math.cos(a1 + math.pi / 2), r * math.sin(a1 + math.pi / 2))
    c.close_path()
    fill(c, h, a)
    c.restore()


def check_mark(c, x, y, s, h=WHITE, w=None, frac=1.0):
    pts = [(x - 0.5 * s, y + 0.02 * s), (x - 0.15 * s, y + 0.36 * s), (x + 0.52 * s, y - 0.34 * s)]
    p, _ = prefix(pts, cumlen(pts), frac)
    if len(p) > 1:
        poly(c, p, close=False)
        stroke(c, h, w or s * 0.24)


# ------------------------------------------------------------------------------------------------ people
class Look(dict):
    __getattr__ = dict.get


def legs(c, k, cx, hip, gy, spread=34, face=0.0, w=46, step=0.0):
    for side in (-1, 1):
        x0 = cx + side * 27
        x1 = cx + side * spread + (step * side)
        c.move_to(x0, hip - 10)
        c.line_to(x1, gy - 16)
        stroke(c, k.bottom if side < 0 else lt(k.bottom, 0.06), w, cap=cairo.LINE_CAP_BUTT)
        ell(c, x1 + face * 12, gy - 11, 31, 14)
        fill(c, k.shoe)
        ell(c, x1 + face * 12, gy - 4, 30, 5)
        fill(c, dk(k.shoe, 0.18))


def torso_path(c, cx, sh, hip, wsh=74, whip=58):
    c.move_to(cx - wsh + 22, sh)
    c.curve_to(cx - wsh - 2, sh, cx - wsh - 4, sh + 22, cx - wsh, sh + 40)
    c.line_to(cx - whip, hip)
    c.curve_to(cx - whip + 10, hip + 8, cx + whip - 10, hip + 8, cx + whip, hip)
    c.line_to(cx + wsh, sh + 40)
    c.curve_to(cx + wsh + 4, sh + 22, cx + wsh + 2, sh, cx + wsh - 22, sh)
    c.close_path()


def torso(c, k, cx, sh, hip, face=0.0, breathe=0.0):
    sh = sh - breathe
    # neck
    rrect(c, cx + face * 8 - 15, sh - 30, 30, 40, 10)
    fill(c, k.skin_d)
    torso_path(c, cx, sh, hip)
    c.save()
    c.clip_preserve()
    fill(c, k.top)
    # far-side shade
    side = -1 if face >= 0 else 1
    rrect(c, cx + side * 74 - (26 if side > 0 else 0) - (0 if side > 0 else 0), sh, 26, hip - sh + 20, 0)
    fill(c, dk(k.top, 0.13))
    cx2 = cx + face * 8
    if k.collar == "v":
        poly(c, [(cx2 - 22, sh - 2), (cx2 + 22, sh - 2), (cx2, sh + 34)])
        fill(c, k.skin_d)
    elif k.collar == "hoodie":
        ell(c, cx2, sh + 2, 40, 16)
        fill(c, dk(k.top, 0.2))
        ell(c, cx2, sh - 2, 22, 10)
        fill(c, k.skin_d)
        for s2 in (-1, 1):
            c.move_to(cx2 + s2 * 13, sh + 12)
            c.line_to(cx2 + s2 * 15, sh + 58)
            stroke(c, CREAM, 4)
        rrect(c, cx2 - 46, hip - 70, 92, 46, 12)
        stroke(c, dk(k.top, 0.18), 4)
    elif k.collar == "blazer":
        poly(c, [(cx2 - 24, sh - 2), (cx2 + 24, sh - 2), (cx2, sh + 66)])
        fill(c, k.shirt)
        poly(c, [(cx2 - 8, sh + 4), (cx2 + 8, sh + 4), (cx2, sh + 20)])
        fill(c, k.skin_d)
        for s2 in (-1, 1):
            poly(c, [(cx2 + s2 * 24, sh - 2), (cx2 + s2 * 40, sh + 6), (cx2 + s2 * 22, sh + 46), (cx2 + s2 * 34, sh + 52),
                     (cx2 + s2 * 2, sh + 96)])
            fill(c, dk(k.top, 0.18))
        ell(c, cx2 + 3, sh + 120, 4.5)
        fill(c, GOLD_L)
    else:
        ell(c, cx2, sh - 2, 24, 13)
        fill(c, k.skin_d)
    if k.apron:
        poly(c, [(cx2 - 40, sh + 54), (cx2 + 40, sh + 54), (cx2 + 54, hip + 60), (cx2 - 54, hip + 60)])
        fill(c, k.apron)
        rrect(c, cx2 - 30, hip - 40, 60, 34, 8)
        stroke(c, dk(k.apron, 0.2), 3.5)
        for s2 in (-1, 1):
            c.move_to(cx2 + s2 * 38, sh + 56)
            c.line_to(cx2 + s2 * 22, sh - 2)
            stroke(c, dk(k.apron, 0.12), 6)
        for (dx, dy, h, r) in k.get("splats", []):
            ell(c, cx2 + dx, sh + dy, r)
            fill(c, h)
    c.restore()
    c.new_path()


def arm(c, k, s, t, bend=1, l1=88, l2=84, short=False, hand=True, sleeve=None, w=30):
    e, h = ik(s, t, l1, l2, bend)
    sleeve = sleeve or k.top
    # soft shadow under the arm so it separates from the body
    c.save()
    c.translate(3, 5)
    poly(c, [s, e, h], close=False)
    stroke(c, "#000000", w + 2, a=0.16)
    c.restore()
    if short:
        poly(c, [s, e, h], close=False)
        stroke(c, k.skin, w - 4)
        m = (lerp(s[0], e[0], 0.55), lerp(s[1], e[1], 0.55))
        poly(c, [s, m], close=False)
        stroke(c, sleeve, w + 4)
    else:
        cuff = (lerp(e[0], h[0], 0.8), lerp(e[1], h[1], 0.8))
        poly(c, [e, h], close=False)
        stroke(c, k.skin, w - 6)
        poly(c, [s, e, cuff], close=False)
        stroke(c, sleeve, w)
    if hand:
        ell(c, h[0], h[1], 15.5)
        fill(c, k.skin)
    return e, h


def hair_back(c, k, fx):
    st = k.hair_style
    if st == "bun":
        ell(c, -6 + fx * 0.3, -72, 27, 25)
        fill(c, k.hair)
        rrect(c, -22 + fx * 0.3, -54, 32, 9, 4)
        fill(c, k.accent or GOLD)
        c.save()
        c.rectangle(-80, -100, 160, 104)
        c.clip()
        ell(c, 0, -6, 56, 60)
        fill(c, k.hair)
        c.restore()
    elif st == "bob":
        rrect(c, -64 + fx * 0.2, -66, 128, 124, 54)
        fill(c, k.hair)
    elif st == "curly":
        for (x, y, r) in ((-48, -26, 20), (-40, -50, 22), (-18, -64, 23), (10, -66, 23), (36, -54, 22), (50, -30, 19),
                          (-54, -4, 15), (54, -6, 14)):
            ell(c, x + fx * 0.2, y, r)
        fill(c, k.hair)
    elif st == "wavy":
        for (x, y, r) in ((-40, -36, 22), (-16, -54, 25), (12, -58, 25), (38, -44, 22)):
            ell(c, x + fx * 0.3, y, r)
        fill(c, k.hair)
        c.save()
        c.rectangle(-80, -100, 160, 100)
        c.clip()
        ell(c, 0, -6, 55, 58)
        fill(c, k.hair)
        c.restore()
    else:  # short
        c.save()
        c.rectangle(-80, -100, 160, 96)
        c.clip()
        ell(c, 0, -8, 55, 57)
        fill(c, k.hair)
        c.restore()


def hair_front(c, k, fx):
    st = k.hair_style
    c.save()
    ell(c, 0, 0, 53, 58)
    c.clip()
    if st == "bun":
        line = [(60, 4), (44, -22), (14, -30), (-16, -26), (-44, -10), (-60, 16)]
    elif st == "bob":
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.rectangle(-70, -80, 140, 160)
        blob(c, [(p[0] + fx * 0.7, p[1]) for p in
                 [(-38, -6), (-10, -18), (22, -28), (42, -10), (44, 20), (32, 50), (0, 62), (-32, 50), (-44, 20)]])
        fill(c, k.hair)
        c.restore()
        return
    elif st == "curly":
        line = [(60, 0), (46, -26), (24, -32), (0, -26), (-24, -32), (-46, -26), (-60, 0)]
    elif st == "wavy":
        line = [(60, -2), (42, -20), (20, -18), (4, -30), (-22, -28), (-44, -14), (-60, 6)]
    else:
        line = [(60, 12), (48, 8), (46, -14), (24, -34), (-4, -38), (-30, -32), (-46, -14), (-48, 8), (-60, 12)]
    pts = [(x + fx * 0.5, y) for x, y in line]
    poly(c, catmull(pts, n=6) + [(-70, -90), (70, -90)])
    fill(c, k.hair)
    if st == "curly":
        for x in (-40, -20, 0, 20, 40):
            ell(c, x + fx * 0.5, -30 + abs(x) * 0.12, 13)
        fill(c, k.hair)
    c.restore()
    # a soft highlight on the hair
    if st in ("short", "wavy", "bun", "bob"):
        c.save()
        c.move_to(-20 + fx * 0.3, -50)
        c.curve_to(-6 + fx * 0.3, -58, 14 + fx * 0.3, -58, 26 + fx * 0.3, -50)
        stroke(c, lt(k.hair, 0.22), 5, a=0.8)
        c.restore()


def head(c, k, x, y, tilt=0.0, face=0.0, eye=1.0, mouth="smile", gaze=(0.0, 0.0), brow=0.0, beard=False):
    """Head centred at (x, y): about 106 x 116 units. face -1..1 turns it (3/4 view), eye = openness."""
    c.save()
    c.translate(x, y + 58)
    c.rotate(tilt)
    c.translate(0, -58)
    fx = face * 13
    hair_back(c, k, fx)
    for side in (-1, 1):
        if side * face > 0.35:
            continue
        ex = side * 50 + face * 14
        ell(c, ex, 8, 11, 14)
        fill(c, k.skin_d)
        ell(c, ex - side * 2, 8, 6, 8)
        fill(c, dk(k.skin_d, 0.1))
    # face with a crescent shade on the far side
    ell(c, 0, 0, 53, 58)
    c.save()
    c.clip_preserve()
    fill(c, k.skin_d)
    ell(c, 5 + face * 4, -3, 51, 57)
    fill(c, k.skin)
    c.restore()
    c.new_path()
    if beard:
        c.save()
        ell(c, 0, 0, 53, 58)
        c.clip()
        c.rectangle(-70, 16, 140, 70)
        c.clip()
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.rectangle(-70, 16, 140, 70)
        ell(c, fx, 14, 41, 25)
        fill(c, k.hair)
        rrect(c, fx - 17, 24, 34, 9, 4.5)
        fill(c, k.hair)
        c.restore()
    hair_front(c, k, fx)
    # cheeks
    for side in (-1, 1):
        ell(c, fx + side * 31 * (0.85 if side * face < 0 else 1), 25, 10, 6)
        fill(c, BLUSH, 0.22)
    # eyes
    gx, gy = gaze
    for side in (-1, 1):
        sx = 0.82 if side * face < 0 else 1.0
        ex, ey = fx + side * 19 * sx + gx, 5 + gy
        if eye > 0.25:
            ell(c, ex, ey, 6.2 * sx, 8 * eye)
            fill(c, INK)
            ell(c, ex + 1.8, ey - 2.6 * eye, 1.9, 1.9 * eye)
            fill(c, WHITE)
        else:
            c.move_to(ex - 6, ey + 1)
            c.curve_to(ex - 2, ey + 4, ex + 2, ey + 4, ex + 6, ey + 1)
            stroke(c, INK, 3.4)
    # brows
    for side in (-1, 1):
        sx = 0.82 if side * face < 0 else 1.0
        bx = fx + side * 20 * sx
        lift = brow * (1.4 if side > 0 else 0.6)
        c.move_to(bx - 9, -12 - lift + side * 1)
        c.curve_to(bx - 4, -16 - lift, bx + 4, -16 - lift, bx + 9, -12 - lift - side * 1)
        stroke(c, dk(k.hair, 0.05), 4.6)
    # nose
    c.move_to(fx * 1.25 + 1, 12)
    c.curve_to(fx * 1.25 + 5, 18, fx * 1.25 + 2, 21, fx * 1.25 - 2, 20)
    stroke(c, k.skin_d, 3.6)
    # mouth
    mx = fx * 1.05
    if mouth == "grin":
        c.move_to(mx - 13, 30)
        c.curve_to(mx - 8, 44, mx + 8, 44, mx + 13, 30)
        c.close_path()
        fill(c, "#5A2430")
        c.rectangle(mx - 10, 30, 20, 4)
        fill(c, WHITE)
    elif mouth == "o":
        ell(c, mx, 36, 6, 8)
        fill(c, "#5A2430")
    elif mouth == "flat":
        c.move_to(mx - 8, 35)
        c.line_to(mx + 8, 33)
        stroke(c, INK, 3.6)
    else:
        c.move_to(mx - 11, 32)
        c.curve_to(mx - 5, 39, mx + 5, 39, mx + 11, 32)
        stroke(c, INK, 3.8)
    if k.glasses:
        for side in (-1, 1):
            sx = 0.82 if side * face < 0 else 1.0
            ex = fx + side * 19 * sx
            rrect(c, ex - 15 * sx, -6, 30 * sx, 23, 9)
            stroke(c, k.glasses, 3.4)
        c.move_to(fx - 5, 2)
        c.line_to(fx + 5, 2)
        stroke(c, k.glasses, 3.2)
    c.restore()


# ------------------------------------------------------------------------------------------------ base class
class Character:
    name = ""
    W, H = 900, 900          # design units; the character is fitted into any box, bottom-centred
    intro = 2.5              # length of the one-shot; after that the idle loop runs forever
    disc = (450, 520, 360)   # backdrop disc (x, y, r) in design units, or None

    def draw(self, c, t):
        raise NotImplementedError

    def backdrop(self, c, t):
        if not self.disc:
            return
        x, y, r = self.disc
        ell(c, x, y, r)
        fill(c, WHITE, 0.055)
        # slow gold arc around the disc
        c.save()
        c.translate(x, y)
        c.rotate(t * 0.12)
        c.arc(0, 0, r + 16, 0.15, 1.35)
        stroke(c, GOLD, 3, a=0.55)
        c.arc(0, 0, r + 16, math.pi + 0.15, math.pi + 0.75)
        stroke(c, GOLD, 3, a=0.35)
        c.restore()

    def render(self, t, w, h, alpha=1.0, backdrop=True, pop=True):
        w, h = max(1, int(round(w))), max(1, int(round(h)))
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        c = cairo.Context(surf)
        s = min(w / self.W, h / self.H)
        c.translate((w - self.W * s) / 2, h - self.H * s)
        c.scale(s, s)
        a = alpha
        if pop:  # quick settle-in at the start (still visible on frame 0)
            k = seg(t, 0, 0.45)
            sc = lerp(0.9, 1.0, e_back(k, 2.2))
            c.translate(self.W / 2, self.H)
            c.scale(sc, sc)
            c.translate(-self.W / 2, -self.H)
        c.push_group()
        if backdrop:
            self.backdrop(c, t)
        self.draw(c, t)
        c.pop_group_to_source()
        c.paint_with_alpha(clamp(a))
        surf.flush()
        return Image.frombuffer("RGBA", (w, h), bytes(surf.get_data()), "raw", "BGRa", surf.get_stride(), 1)


# ------------------------------------------------------------------------------------------------ 1. artist
class Artist(Character):
    name = "artist"
    look = Look(skin="#7A4B2E", skin_d="#663C23", hair="#1D1716", hair_style="bun", accent=GOLD_L, top="#E9E2D3",
                bottom="#2F4A6B", shoe="#E8E2D4", collar="round", apron="#C99A48",
                splats=[(-22, 92, TEAL, 6), (18, 130, PLUM, 5), (-8, 160, "#2E6E68", 4)])
    CX0, CY0, CW, CH = 435, 352, 220, 250   # painting area on the canvas

    def __init__(self):
        L = []

        def region_rect(c):
            c.rectangle(0, 0, self.CW, self.CH)

        def region_circle(x, y, r):
            return lambda c: ell(c, x, y, r)

        def far_hill(c):
            c.move_to(0, 136)
            c.curve_to(50, 100, 110, 106, 140, 122)
            c.curve_to(170, 136, 200, 118, 220, 110)
            c.line_to(220, 250)
            c.line_to(0, 250)
            c.close_path()

        def near_hill(c):
            c.move_to(0, 194)
            c.curve_to(60, 168, 130, 166, 220, 200)
            c.line_to(220, 250)
            c.line_to(0, 250)
            c.close_path()

        def zig(p):
            return catmull(p, n=8)
        # (kind, region, colour, sweep points, width)
        L.append(("fill", region_rect, "#CFE4E1", zig([(40, 30), (180, 30), (42, 76), (180, 90), (40, 128), (178, 140)]), 84))
        L.append(("fill", region_circle(160, 58, 24), "#E7B85A", circle_pts(160, 58, 9, 1.15, n=30), 34))
        L.append(("fill", far_hill, "#7FB2A8", zig([(40, 132), (180, 126), (42, 176), (180, 176), (40, 222), (180, 228)]), 86))
        L.append(("fill", near_hill, "#2E6E68", zig([(40, 204), (180, 210), (42, 236), (180, 238)]), 70))
        L.append(("line", None, "#4A3426", [(58, 222), (58, 168)], 9))
        L.append(("fill", region_circle(58, 150, 28), PLUM, circle_pts(58, 150, 11, 1.1, n=30), 40))
        L.append(("line", None, NAVY, [(98, 40), (105, 46), (112, 40)], 3.6))
        L.append(("line", None, NAVY, [(120, 28), (126, 33), (132, 28)], 3.2))
        # schedule: duration weighted by length^0.6, small lifts between layers
        t0, t1, gap = 0.18, 2.45, 0.07
        lens = [cumlen(x[3]) for x in L]
        wts = [max(0.12, Lc[-1] ** 0.6) for Lc in lens]
        avail = t1 - t0 - gap * (len(L) - 1)
        tt = t0
        self.layers = []
        for x, Lc, wt in zip(L, lens, wts):
            d = avail * wt / sum(wts)
            self.layers.append(dict(kind=x[0], region=x[1], col=x[2], pts=x[3], L=Lc, w=x[4], s=tt, e=tt + d))
            tt += d + gap
        self.done = tt - gap

    def tip(self, t):
        """Brush tip position in painting coordinates and the paint colour on it."""
        Ls = self.layers
        if t <= Ls[0]["s"]:
            p0 = Ls[0]["pts"][0]
            return (p0[0] + 30 * (1 - seg(t, 0, Ls[0]["s"])), p0[1] - 20 * (1 - seg(t, 0, Ls[0]["s"]))), Ls[0]["col"]
        for i, l in enumerate(Ls):
            if t <= l["e"]:
                if t >= l["s"]:
                    _, p = prefix(l["pts"], l["L"], smooth01(seg(t, l["s"], l["e"])))
                    return p, l["col"]
                prev = Ls[i - 1]
                k = e_inout(seg(t, prev["e"], l["s"]))
                a, b = prev["pts"][-1], l["pts"][0]
                return (lerp(a[0], b[0], k), lerp(a[1], b[1], k) - 14 * math.sin(math.pi * k)), l["col"]
        # idle: small dabs near the bottom right corner (signing the piece)
        u = t - self.done
        k = e_inout(seg(u, 0, 0.5))
        a = Ls[-1]["pts"][-1]
        base = (lerp(a[0], 168, k), lerp(a[1], 222, k))
        bob = seg(u, 0.4, 0.8)
        return (base[0] + bob * 7 * math.sin(u * 2.6), base[1] + bob * (4 * math.sin(u * 5.2) - 3)), "#8E4F6E"

    def painting(self, c, t):
        c.save()
        c.translate(self.CX0, self.CY0)
        c.rectangle(0, 0, self.CW, self.CH)
        c.clip()
        for l in self.layers:
            if t < l["s"]:
                break
            p = smooth01(seg(t, l["s"], l["e"]))
            if l["kind"] == "fill":
                c.save()
                l["region"](c)
                c.clip()
                if p >= 1:
                    c.paint() if False else None
                    l["region"](c)
                    fill(c, l["col"])
                else:
                    pts, _ = prefix(l["pts"], l["L"], p)
                    if len(pts) > 1:
                        poly(c, pts, close=False)
                        stroke(c, l["col"], l["w"])
                c.restore()
            else:
                pts, _ = prefix(l["pts"], l["L"], p)
                if len(pts) > 1:
                    poly(c, pts, close=False)
                    stroke(c, l["col"], l["w"])
        c.restore()

    def draw(self, c, t):
        k = self.look
        gy = 850
        shadow(c, 470, gy - 4, 260, 22)
        # easel (behind the artist)
        ex, top = 545, 300
        c.move_to(ex, top)
        c.line_to(ex, gy - 6)
        stroke(c, WOOD_D, 13)
        for dx in (-96, 96):
            c.move_to(ex, top - 10)
            c.line_to(ex + dx, gy - 4)
            stroke(c, WOOD, 16)
        c.move_to(ex - 74, 700)
        c.line_to(ex + 74, 700)
        stroke(c, WOOD_D, 9)
        rrect(c, ex - 12, top - 34, 24, 40, 6)
        fill(c, WOOD)
        # canvas board with depth and drop shadow
        x0, y0 = self.CX0, self.CY0
        rrect(c, x0 + 10, y0 + 12, self.CW, self.CH, 4)
        fill(c, "#000000", 0.25)
        rrect(c, x0 + self.CW - 2, y0 + 4, 9, self.CH, 2)
        fill(c, "#D9D1BF")
        rrect(c, x0, y0, self.CW, self.CH, 3)
        fill(c, PAPER)
        self.painting(c, t)
        rrect(c, x0 - 22, y0 + self.CH - 2, self.CW + 44, 20, 6)
        fill(c, WOOD)
        rrect(c, x0 - 22, y0 + self.CH + 12, self.CW + 44, 6, 3)
        fill(c, WOOD_D)
        # artist
        cx, hip = 342, 650
        breathe = 2.2 * math.sin(t * 2.1)
        sh = 465
        legs(c, k, cx, hip, gy, face=0.6)
        torso(c, k, cx, sh, hip, face=0.5, breathe=breathe)
        (tx, ty), paint = self.tip(t)
        tip = (self.CX0 + tx, self.CY0 + ty)
        anc = (cx + 58 - 150, sh + 28 + 150)
        vx, vy = tip[0] - anc[0], tip[1] - anc[1]
        ang = math.atan2(vy, vx)
        bl = 105
        hand = (tip[0] - bl * math.cos(ang), tip[1] - bl * math.sin(ang))
        look_x = clamp((tip[0] - 540) / 120, -1, 1)
        head(c, k, cx + 8, sh - 74 - breathe, tilt=0.05 + 0.03 * math.sin(t * 1.3), face=0.62, eye=blink(t, 0.4),
             mouth="smile", gaze=(3 + 2 * look_x, 1 + (tip[1] - 470) / 90))
        # palette in the rear hand
        ps = (cx - 58, sh + 28 - breathe)
        ph = (cx - 26, 606)
        arm(c, k, ps, ph, bend=-1, short=True, hand=False)
        c.save()
        c.translate(ph[0] - 6, ph[1] - 4)
        c.rotate(-0.22)
        blob(c, [(-62, -8), (-40, -32), (10, -36), (58, -22), (66, 4), (40, 30), (-20, 34), (-58, 20)])
        fill(c, "#E9DCC0")
        ell(c, 8, 4, 10, 8)
        fill(c, "#C9B892")
        for (dx, dy, h) in ((-40, -10, TEAL), (-18, -22, "#E7B85A"), (12, -24, PLUM), (38, -12, BURG), (44, 12, "#CFE4E1")):
            ell(c, dx, dy, 9, 7.5)
            fill(c, h)
        c.restore()
        ell(c, ph[0], ph[1], 15.5)
        fill(c, k.skin)
        # brush arm (front)
        s2 = (cx + 58, sh + 28 - breathe)
        e, hnd = ik(s2, hand, 92, 88, 0)
        arm(c, k, s2, hand, bend=0, l1=92, l2=88, short=True, hand=False)
        # brush: handle, ferrule, tip in the current paint colour
        d = (math.cos(ang), math.sin(ang))
        c.move_to(hnd[0] - d[0] * 26, hnd[1] - d[1] * 26)
        c.line_to(hnd[0] + d[0] * 74, hnd[1] + d[1] * 74)
        stroke(c, NAVY, 8)
        c.move_to(hnd[0] + d[0] * 72, hnd[1] + d[1] * 72)
        c.line_to(hnd[0] + d[0] * 88, hnd[1] + d[1] * 88)
        stroke(c, "#C9CED6", 9, cap=cairo.LINE_CAP_BUTT)
        c.move_to(hnd[0] + d[0] * 87, hnd[1] + d[1] * 87)
        c.line_to(tip[0], tip[1])
        stroke(c, paint, 7)
        ell(c, hnd[0], hnd[1], 15.5)
        fill(c, k.skin)


# ------------------------------------------------------------------------------------------------ 2. F-1 student
class Student(Character):
    name = "student"
    look = Look(skin="#C68E62", skin_d="#AE774F", hair="#1C1B22", hair_style="wavy", top=TEAL, bottom="#4F6A92",
                shoe="#F1EEE6", collar="hoodie", glasses="#1B2433")
    SX, SY, SW, SH = 492, 377, 256, 186   # display area

    def screen(self, c, t):
        x, y = self.SX, self.SY
        c.save()
        c.translate(x, y)
        rrect(c, 0, 0, self.SW, self.SH, 6)
        c.clip()
        c.rectangle(0, 0, self.SW, self.SH)
        fill(c, PAPER)
        c.rectangle(0, 0, self.SW, 26)
        fill(c, NAVY)
        for i in range(3):
            ell(c, 14 + i * 13, 13, 4)
            fill(c, GOLD_L if i == 0 else CREAM, 0.9 if i == 0 else 0.45)
        # avatar + title bars
        ell(c, 26, 50, 13)
        fill(c, GOLD_P)
        ell(c, 26, 46, 5)
        fill(c, GOLD)
        ell(c, 26, 60, 9, 6)
        fill(c, GOLD)
        rrect(c, 48, 41, 92, 9, 4)
        fill(c, "#C9C3B5")
        rrect(c, 48, 55, 60, 7, 3.5)
        fill(c, "#DDD8CC")
        rows = [(80, 118), (110, 86), (140, 132)]
        for i, (ry, target) in enumerate(rows):
            a = 0.25 + i * 0.5
            p = e_out(seg(t, a, a + 0.42))
            rrect(c, 14, ry - 4, 36, 8, 4)
            fill(c, "#C9C3B5")
            rrect(c, 58, ry - 10, 158, 21, 6)
            fill(c, WHITE)
            rrect(c, 58, ry - 10, 158, 21, 6)
            stroke(c, GOLD if 0 < p < 1 else "#D9D3C6", 2.4 if 0 < p < 1 else 2)
            if p > 0:
                # typed "characters" as short bars
                xx, end = 64, 64 + target * p
                j = 0
                while xx < end:
                    wd = min([14, 9, 18, 11, 7, 15][(i * 3 + j) % 6], end - xx)
                    rrect(c, xx, ry - 3, wd, 7, 3)
                    fill(c, NAVY, 0.72)
                    xx += wd + 4
                    j += 1
                if p < 1 and (t * 3) % 1 < 0.6:
                    c.rectangle(end + 3, ry - 6, 2.4, 13)
                    fill(c, NAVY)
            k = seg(t, a + 0.42, a + 0.72)
            if k > 0:
                r = 9.5 * e_back(k, 2.6)
                ell(c, 234, ry + 0.5, r)
                fill(c, TEAL)
                check_mark(c, 234, ry + 0.5, 10, WHITE, 2.8, frac=seg(k, 0.3, 1))
        # submit button turns gold
        k = seg(t, 1.85, 2.15)
        rrect(c, 58, 160, 100, 20, 10)
        fill(c, mix("#D9D3C6", GOLD, e_out(k)))
        rrect(c, 84, 167, 48, 6, 3)
        fill(c, WHITE, 0.8)
        c.restore()

    def draw(self, c, t):
        k = self.look
        gy = 850
        shadow(c, 470, gy - 4, 290, 22)
        # desk
        dx0, dx1, dtop = 400, 800, 598
        for lx in (dx0 + 26, dx1 - 44):
            rrect(c, lx, dtop + 16, 18, gy - dtop - 20, 5)
            fill(c, WOOD_D)
        # student (behind the desk front)
        cx, hip, sh = 300, 650, 465
        breathe = 2.0 * math.sin(t * 2.0)
        # backpack behind
        rrect(c, cx - 112, sh + 14 - breathe, 70, 168, 26)
        fill(c, PLUM)
        rrect(c, cx - 118, sh + 96 - breathe, 52, 70, 16)
        fill(c, dk(PLUM, 0.15))
        legs(c, k, cx, hip, gy, face=0.5)
        torso(c, k, cx, sh, hip, face=0.45, breathe=breathe)
        # straps
        for (x0, x1) in ((cx - 44, cx - 40), (cx + 40, cx + 46)):
            c.move_to(x0, sh - 2 - breathe)
            c.curve_to(x0 + 4, sh + 50, x1, sh + 90, x1, sh + 150)
            stroke(c, dk(PLUM, 0.1), 11)
        tilt = 0.06 * math.sin(t * 1.1) + 0.04 * seg(t, 2.2, 2.6)
        done = seg(t, 2.1, 2.4)
        head(c, k, cx + 10, sh - 74 - breathe, tilt=tilt, face=0.55, eye=blink(t, 1.1),
             mouth="grin" if done > 0.5 and t < 3.6 else "smile", gaze=(4, 3), brow=3 * done)
        # rear hand on the strap
        arm(c, k, (cx - 58, sh + 28 - breathe), (cx - 30, sh + 98), bend=-1)
        # laptop
        rrect(c, 482, 366, 276, 212, 14)
        fill(c, "#2A3A55")
        rrect(c, 482, 366, 276, 212, 14)
        stroke(c, "#4A5D7D", 3)
        self.screen(c, t)
        # desk top
        rrect(c, dx0, dtop, dx1 - dx0, 22, 8)
        fill(c, "#D9C7A3")
        rrect(c, dx0, dtop + 14, dx1 - dx0, 8, 4)
        fill(c, "#BFA97F")
        # laptop base
        poly(c, [(456, 596), (784, 596), (770, 578), (470, 578)])
        fill(c, "#C9CED6")
        rrect(c, 586, 581, 68, 6, 3)
        fill(c, "#A9B0BC")
        # typing hand (front)
        typing = t > 0.2 and (t < 1.8 or t > 2.6)
        tap = (math.sin(t * 17) * 4 if typing else 0)
        hx = 510 + 26 * (0.5 + 0.5 * math.sin(t * 2.3)) if typing else 520
        arm(c, k, (cx + 58, sh + 28 - breathe), (hx, 572 + tap), bend=1, l1=96, l2=92)
        # success badge
        b = seg(t, 2.15, 2.55)
        if b > 0:
            r = 34 * e_back(b, 2.4) * (1 + 0.04 * math.sin(max(0, t - 2.6) * 3))
            bx, by = 752, 372
            for i in range(8):
                a = i * TAU / 8 + 0.2
                k2 = seg(t, 2.25, 2.85)
                if 0 < k2 < 1:
                    r0, r1 = 40 + 30 * e_out(k2), 46 + 44 * e_out(k2)
                    c.move_to(bx + r0 * math.cos(a), by + r0 * math.sin(a))
                    c.line_to(bx + r1 * math.cos(a), by + r1 * math.sin(a))
                    stroke(c, GOLD_L, 5, a=1 - k2)
            ell(c, bx, by, r + 5)
            fill(c, PAPER)
            ell(c, bx, by, r)
            fill(c, GOLD)
            check_mark(c, bx, by, r * 0.9, WHITE, r * 0.22, frac=seg(b, 0.35, 1))


# ------------------------------------------------------------------------------------------------ 3. H-1B worker
class Worker(Character):
    name = "worker"
    look = Look(skin="#E0AC86", skin_d="#C9926C", hair="#3A2318", hair_style="bob", top="#6F3E5E", shirt=CREAM,
                bottom="#3A3F4B", shoe="#5A2C38", collar="blazer")
    WIN = [(c_, r_) for r_ in range(7) for c_ in range(3)]

    def building(self, c, t):
        # back tower
        rrect(c, 640, 330, 150, 520, 6)
        fill(c, "#1F3658")
        for r_ in range(9):
            for c_ in range(3):
                rrect(c, 656 + c_ * 44, 352 + r_ * 52, 30, 30, 4)
                fill(c, "#2B4770")
        # front tower
        x0, y0 = 520, 250
        rrect(c, x0, y0, 220, 600, 8)
        fill(c, "#2C4B73")
        c.rectangle(x0, y0, 220, 18)
        fill(c, "#3B5E8A")
        rrect(c, x0 + 90, y0 - 40, 40, 44, 4)
        fill(c, "#2C4B73")
        for i, (c_, r_) in enumerate(self.WIN):
            wx, wy = x0 + 22 + c_ * 66, y0 + 42 + r_ * 70
            # windows light up bottom-up during the intro, then twinkle a little
            order = (6 - r_) * 3 + c_
            on = seg(t, 0.35 + order * 0.08, 0.55 + order * 0.08)
            if t > 3:
                h = (math.sin(i * 12.9898 + math.floor((t - 3) / 1.7 + i * 0.37) * 78.233) * 43758.5453) % 1
                on *= 0.55 + 0.45 * (h > 0.25)
            rrect(c, wx, wy, 44, 46, 5)
            fill(c, mix("#3E5F88", GOLD_P, on * 0.92))
        rrect(c, x0 + 80, 790, 60, 60, 4)
        fill(c, "#1A2E4D")

    def calendar(self, c, t):
        x, y, w, h = 70, 120, 210, 190
        bob = 5 * math.sin(t * 1.6)
        c.save()
        c.translate(0, bob)
        c.save()
        c.translate(x + w / 2, y + h / 2)
        c.rotate(-0.06)
        c.translate(-(x + w / 2), -(y + h / 2))
        rrect(c, x + 8, y + 12, w, h, 16)
        fill(c, "#000000", 0.25)
        flips = [0.25, 0.75, 1.25]
        nflip = sum(1 for f in flips if t >= f + 0.42)

        def page(px, py, idx, mark):
            rrect(c, px, py, w, h, 16)
            fill(c, PAPER)
            c.save()
            rrect(c, px, py, w, h, 16)
            c.clip()
            c.rectangle(px, py, w, 44)
            fill(c, [GOLD, TEAL, PLUM, BURG][idx % 4])
            c.restore()
            for r_ in range(4):
                for c_ in range(5):
                    rrect(c, px + 18 + c_ * 36, py + 60 + r_ * 30, 26, 20, 5)
                    fill(c, "#E6E0D2")
            if mark is not None:
                c_, r_ = mark
                cx_, cy_ = px + 31 + c_ * 36, py + 70 + r_ * 30
                rrect(c, cx_ - 13, cy_ - 10, 26, 20, 5)
                fill(c, GOLD_P)
        marks = [(1, 0), (3, 1), (0, 2), (2, 2)]
        # page under the one flipping
        under = min(nflip + 1, 3)
        page(x, y, under, marks[under] if under < 3 else None)
        if under == 3:
            k = seg(t, 1.75, 2.3)
            cx_, cy_ = x + 31 + 2 * 36, y + 70 + 2 * 30
            if k > 0:
                c.arc(cx_, cy_, 21, -math.pi / 2, -math.pi / 2 + TAU * e_out(k))
                stroke(c, GOLD, 5)
                check_mark(c, cx_, cy_ + 1, 13, NAVY, 3.6, frac=seg(t, 2.1, 2.45))
        # the flipping page rotates up around the top edge
        if nflip < 3:
            f0 = flips[nflip]
            p = e_inout(seg(t, f0, f0 + 0.42))
            sy = math.cos(math.pi * p)
            c.save()
            c.translate(0, y)
            c.scale(1, sy if sy > 0.02 else (0.02 if sy > -0.02 else sy * 0.32))
            c.translate(0, -y)
            if sy > 0:
                page(x, y, nflip, marks[nflip])
            else:
                rrect(c, x, y, w, h, 16)
                fill(c, "#E2DACA", 1 - 0.6 * (-sy))
            c.restore()
        # rings
        for rx in (x + 52, x + w - 52):
            rrect(c, rx - 6, y - 14, 12, 30, 6)
            fill(c, NAVY)
            rrect(c, rx - 6, y - 14, 12, 30, 6)
            stroke(c, GOLD_L, 2.5)
        c.restore()
        c.restore()

    def draw(self, c, t):
        k = self.look
        gy = 850
        self.building(c, t)
        shadow(c, 430, gy - 4, 300, 22)
        self.calendar(c, t)
        cx, hip, sh = 300, 650, 465
        sway = math.sin(t * 1.2)
        breathe = 2.0 * math.sin(t * 2.0)
        # laptop bag behind the hip on the rear side
        legs(c, k, cx, hip, gy, face=0.3)
        torso(c, k, cx, sh, hip, face=0.25, breathe=breathe)
        c.move_to(cx + 50, sh + 4 - breathe)
        c.line_to(cx - 64, hip - 34)
        stroke(c, "#5B4129", 10)
        head(c, k, cx + 4, sh - 74 - breathe, tilt=0.04 * sway, face=0.3, eye=blink(t, 2.2), mouth="smile",
             gaze=(2, 0))
        # suitcase
        s_x, s_y = 470, 690
        rrect(c, s_x + 30, s_y - 104, 10, 110, 4)
        fill(c, "#8F97A6")
        rrect(c, s_x + 70, s_y - 104, 10, 110, 4)
        fill(c, "#8F97A6")
        rrect(c, s_x + 22, s_y - 118, 66, 20, 9)
        fill(c, "#5C6575")
        rrect(c, s_x, s_y, 110, 140, 18)
        fill(c, TEAL)
        rrect(c, s_x, s_y, 110, 140, 18)
        c.save()
        c.clip()
        c.rectangle(s_x, s_y, 18, 140)
        fill(c, TEAL_D)
        c.restore()
        for sx in (s_x + 34, s_x + 74):
            c.rectangle(sx - 5, s_y, 10, 140)
            fill(c, GOLD_L)
        for wx in (s_x + 22, s_x + 88):
            ell(c, wx, s_y + 146, 9)
            fill(c, INK)
        # rear arm holding the bag strap low
        arm(c, k, (cx - 58, sh + 28 - breathe), (cx - 70, hip - 30), bend=-1)
        rrect(c, cx - 120, hip - 46, 100, 74, 14)
        fill(c, "#8A6A3E")
        rrect(c, cx - 120, hip - 46, 100, 30, 12)
        fill(c, "#6E5230")
        rrect(c, cx - 76, hip - 22, 14, 10, 3)
        fill(c, GOLD_L)
        ell(c, cx - 70, hip - 30, 15.5)
        fill(c, k.skin)
        # front arm on the suitcase handle
        arm(c, k, (cx + 58, sh + 28 - breathe), (s_x + 55, s_y - 106), bend=1)
        # travel sparkle once the date is set
        sp = seg(t, 2.25, 2.7)
        if sp > 0:
            sparkle(c, 300, 128 + 5 * math.sin(t * 1.6), 18 * e_back(min(1, sp * 1.2)) * (1 - 0.25 * seg(t, 2.7, 3.2)),
                    GOLD_L, rot=0.3 * t)


# ------------------------------------------------------------------------------------------------ 4. small business owner
class Owner(Character):
    name = "owner"
    look = Look(skin="#B5774C", skin_d="#9C6440", hair="#2A211C", hair_style="short", top="#E9DFC9",
                bottom="#3A3F4B", shoe="#5A2C38", collar="round", apron=BURG)
    DROPS = [0.45, 0.85, 1.25, 1.65, 2.05]
    PILE = [(-22, 0), (10, -2), (-4, -11), (24, -12), (-20, -20), (8, -24), (-6, -33), (20, -34)]

    def coins_landed(self, t):
        n = sum(1 for d in self.DROPS if t >= d + 0.5)
        return min(n, len(self.PILE))

    def draw(self, c, t):
        k = self.look
        gy = 850
        shadow(c, 450, gy - 4, 330, 24)
        # awning
        ax0, ax1, ay = 130, 770, 150
        rrect(c, ax0 - 16, ay - 18, ax1 - ax0 + 32, 20, 8)
        fill(c, WOOD_D)
        n = 8
        sw = (ax1 - ax0) / n
        sag = 3 * math.sin(t * 1.4)
        for i in range(n):
            x = ax0 + i * sw
            c.move_to(x, ay)
            c.line_to(x + sw, ay)
            c.line_to(x + sw, ay + 70 + sag)
            c.arc_negative(x + sw / 2, ay + 70 + sag, sw / 2, 0, math.pi)
            c.close_path()
            fill(c, GOLD if i % 2 == 0 else CREAM)
        c.rectangle(ax0, ay + 62, ax1 - ax0, 6)
        fill(c, "#000000", 0.08)
        # shelf behind
        rrect(c, 170, 336, 560, 12, 5)
        fill(c, WOOD_D)
        for (x, w, h, col_) in ((190, 40, 60, TEAL), (238, 34, 46, GOLD_L), (280, 46, 70, PLUM),
                                (600, 44, 54, TEAL_D), (652, 30, 66, BURG), (690, 30, 40, GOLD_L)):
            rrect(c, x, 336 - h, w, h, 8)
            fill(c, col_)
            rrect(c, x + 6, 336 - h + 10, w - 12, 10, 4)
            fill(c, WHITE, 0.35)
        # owner
        cx, sh, hip = 450, 450, 640
        breathe = 2.0 * math.sin(t * 2.0)
        torso(c, k, cx, sh, hip, face=0.0, breathe=breathe)
        nod = 0.05 * math.sin(t * 1.3) + 0.06 * math.sin(math.pi * seg(t, 2.3, 2.8))
        land = self.coins_landed(t)
        head(c, k, cx, sh - 74 - breathe, tilt=nod * 0.6, face=0.05, eye=blink(t, 0.7),
             mouth="grin" if 2.4 < t < 3.4 else "smile", gaze=(4 * seg(t, 0.3, 0.6) - 8 * seg(t, 1.6, 2.0), 4),
             beard=True)
        # arms: left presses the register, right rests by the jar
        press = 6 * max(0.0, math.sin(t * 9)) if 0.25 < t < 0.8 else 0
        arm(c, k, (cx - 58, sh + 28 - breathe), (300, 560 + press), bend=-1, short=True)
        arm(c, k, (cx + 58, sh + 28 - breathe), (568, 590), bend=1, short=True)
        # register
        rx = 190
        poly(c, [(rx, 600), (rx + 150, 600), (rx + 140, 520), (rx + 10, 520)])
        fill(c, SLATE)
        rrect(c, rx + 6, 506, 138, 20, 6)
        fill(c, dk(SLATE, 0.2))
        for r_ in range(2):
            for c_ in range(4):
                rrect(c, rx + 30 + c_ * 24, 545 + r_ * 22, 16, 12, 3)
                fill(c, CREAM if (r_, c_) != (1, 3) else GOLD_L)
        # receipt printing upward out of the slot
        slot = (rx + 44, 508)
        ln = 180 * e_out(seg(t, 0.3, 1.9)) + 3 * math.sin(t * 2) * seg(t, 1.9, 2.2)
        if ln > 1:
            px, pw = slot[0], 62
            top = slot[1] - ln
            c.move_to(px, slot[1])
            c.line_to(px, top + 6)
            for j in range(7):
                c.line_to(px + pw * (j + 0.5) / 7, top + (0 if j % 2 == 0 else 6))
            c.line_to(px + pw, top + 6)
            c.line_to(px + pw, slot[1])
            c.close_path()
            fill(c, WHITE)
            for j in range(12):
                yy = top + 20 + j * 14
                if yy > slot[1] - 8:
                    break
                wl = [44, 30, 38, 24, 40, 34, 28, 42, 36, 26, 40, 30][j]
                last = j == 0 and ln > 170
                rrect(c, px + 9, yy, wl if not last else 44, 5 if not last else 7, 2.5)
                fill(c, GOLD if last else "#B9B3A6")
        rrect(c, slot[0] - 6, slot[1] - 4, 74, 9, 4)
        fill(c, INK)
        # coin jar (back layer)
        jx, jy, jw, jh = 560, 470, 100, 124
        rrect(c, jx, jy, jw, jh, 20)
        fill(c, "#CFE4E1", 0.18)
        base_y = jy + jh - 14
        for i in range(self.coins_landed(t)):
            dx, dy = self.PILE[i]
            ell(c, jx + jw / 2 + dx, base_y + dy, 18, 7)
            fill(c, GOLD)
            ell(c, jx + jw / 2 + dx, base_y + dy - 2, 16, 5.5)
            fill(c, GOLD_L)
        # falling coins (spinning)
        drops = list(self.DROPS)
        if t > 2.6:
            u = t - 2.6
            drops.append(2.6 + math.floor(u / 2.4) * 2.4 + 0.4)
        for i, d in enumerate(drops):
            u = t - d
            if not 0 <= u < 0.5:
                continue
            land_y = base_y + self.PILE[min(i, len(self.PILE) - 1)][1] - 4
            y = lerp(300, land_y, (u / 0.5) ** 2)
            x = jx + jw / 2 + self.PILE[min(i, len(self.PILE) - 1)][0] * (u / 0.5)
            sx = abs(math.cos(u * 14)) * 0.85 + 0.15
            ell(c, x, y, 17 * sx, 17)
            fill(c, GOLD)
            ell(c, x, y, 12 * sx, 12)
            fill(c, GOLD_L)
        for d in drops:
            u = t - d - 0.5
            if 0 <= u < 0.35:
                sparkle(c, jx + jw - 6, jy + 30, 14 * math.sin(math.pi * u / 0.35), GOLD_L, rot=u * 3)
        # jar front: rim + glass highlight
        rrect(c, jx, jy, jw, jh, 20)
        stroke(c, WHITE, 4, a=0.55)
        rrect(c, jx - 8, jy - 12, jw + 16, 18, 8)
        fill(c, "#C9CED6")
        rrect(c, jx + 12, jy + 18, 8, 60, 4)
        fill(c, WHITE, 0.45)
        # counter (in front)
        rrect(c, 130, 596, 640, 26, 10)
        fill(c, "#E9DFC9")
        rrect(c, 150, 618, 600, gy - 618, 10)
        fill(c, TEAL_D)
        for i in range(3):
            rrect(c, 178 + i * 190, 650, 164, 170, 12)
            stroke(c, lt(TEAL_D, 0.12), 4)
        rrect(c, 150, 618, 600, 12, 0)
        fill(c, "#000000", 0.15)


# ------------------------------------------------------------------------------------------------ 5. gig driver
DIGITS = {
    0: [("ell",)],
    1: [[(6, 7), (12, 0), (12, 32)]],
    2: [[(1, 8), (4, 1), (11, 0), (17, 3), (18, 9), (15, 15), (1, 32), (19, 32)]],
    3: [[(2, 3), (9, 0), (16, 2), (17, 8), (14, 13), (8, 15)], [(8, 15), (15, 17), (18, 23), (16, 30), (9, 32), (1, 29)]],
    4: [[(14, 32), (14, 0), (1, 22), (19, 22)]],
    5: [[(17, 0), (4, 0), (2, 14), (9, 12), (15, 14), (18, 21), (16, 29), (9, 32), (2, 29)]],
    6: [[(15, 1), (8, 3), (3, 11), (1, 21), (3, 29), (10, 32), (16, 29), (18, 22), (15, 16), (9, 15), (3, 18), (1, 22)]],
    7: [[(1, 0), (19, 0), (7, 32)]],
    8: [("e8",)],
    9: [[(18, 10), (15, 15), (9, 17), (3, 14), (1, 8), (4, 2), (10, 0), (16, 2), (18, 9), (17, 20), (13, 28), (5, 32)]],
}


def digit(c, d, x, y, s, h, w):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for part in DIGITS[d]:
        if part == ("ell",):
            ell(c, 10, 16, 8.5, 15)
        elif part == ("e8",):
            ell(c, 10, 8, 7, 7.5)
            ell(c, 10, 24, 8.5, 8)
        else:
            poly(c, catmull(part, n=4) if len(part) > 3 else part, close=False)
    c.restore()
    stroke(c, h, w)


class Driver(Character):
    name = "driver"
    W, H = 1000, 780
    disc = (500, 470, 330)
    look = Look(skin="#6B4430", skin_d="#583624", hair="#17120F", hair_style="curly", top=GOLD, bottom=NAVY,
                shoe=CREAM)
    ROUTE = [(30, 150), (30, 104), (92, 104), (92, 60), (170, 60), (170, 120), (236, 120), (236, 46)]

    def mapcard(self, c, t):
        x, y, w, h = 650, 60, 290, 210
        c.save()
        c.translate(0, 3 * math.sin(t * 1.5 + 1))
        rrect(c, x + 8, y + 12, w, h, 20)
        fill(c, "#000000", 0.25)
        rrect(c, x, y, w, h, 20)
        fill(c, PAPER)
        c.save()
        rrect(c, x, y, w, h, 20)
        c.clip()
        c.translate(x + 12, y + 18)
        blob(c, [(150, -30), (200, 20), (280, 30), (300, -30)])
        fill(c, "#CFE4E1")
        for xs in (30, 92, 170, 236):
            c.move_to(xs, -20)
            c.line_to(xs, 200)
        for ys in (46, 60, 104, 120, 150):
            c.move_to(-20, ys)
            c.line_to(300, ys)
        stroke(c, "#E6E0D2", 9)
        for (bx, by, bw, bh) in ((44, 72, 34, 22), (106, 74, 50, 36), (186, 134, 36, 50), (44, 162, 120, 30)):
            rrect(c, bx, by, bw, bh, 5)
            fill(c, "#EEE8DC")
        L = cumlen(self.ROUTE)
        p = e_inout(seg(t, 0.35, 2.25))
        if p > 0:
            pts, end = prefix(self.ROUTE, L, p)
            poly(c, self.ROUTE, close=False)
            c.set_dash([2, 10])
            stroke(c, TEAL, 5, a=0.35)
            c.set_dash([])
            poly(c, pts, close=False)
            stroke(c, TEAL, 7)
        else:
            end = self.ROUTE[0]
        ell(c, self.ROUTE[0][0], self.ROUTE[0][1], 8)
        fill(c, NAVY)
        # destination pin
        dx, dy = self.ROUTE[-1]
        bounce = -abs(math.sin(max(0, t - 2.25) * 3.2)) * 6 * seg(t, 2.25, 2.4)
        c.save()
        c.translate(dx, dy - 4 + bounce)
        c.move_to(0, 0)
        c.curve_to(-6, -10, -16, -18, -16, -28)
        c.arc(0, -28, 16, math.pi, TAU)
        c.curve_to(16, -18, 6, -10, 0, 0)
        c.close_path()
        fill(c, BURG)
        ell(c, 0, -28, 6)
        fill(c, PAPER)
        c.restore()
        if t > 2.25:
            u = (t - 2.25) % 1.6
            c.arc(dx, dy, 6 + 26 * e_out(u / 1.6), 0, TAU)
            stroke(c, BURG, 3, a=0.6 * (1 - u / 1.6))
        if p < 1 or t < 2.4:
            ell(c, end[0], end[1], 11)
            fill(c, WHITE)
            ell(c, end[0], end[1], 7.5)
            fill(c, GOLD)
        c.restore()
        c.restore()

    def odometer(self, c, t):
        x, y = 60, 90
        n = 6
        cw, ch, gap = 40, 62, 8
        w = n * cw + (n - 1) * gap + 28
        c.save()
        c.translate(0, 3 * math.sin(t * 1.5))
        rrect(c, x + 8, y + 12, w, ch + 28, 18)
        fill(c, "#000000", 0.25)
        rrect(c, x, y, w, ch + 28, 18)
        fill(c, "#0A1526")
        rrect(c, x, y, w, ch + 28, 18)
        stroke(c, GOLD, 3)
        # value: 4,817.x miles rolling; fast during the intro then slow
        v = 4817.0 + 9.0 * e_inout(seg(t, 0.3, 2.3)) + max(0.0, t - 2.3) * 0.6
        for i in range(n):
            px = x + 14 + i * (cw + gap)
            py = y + 14
            last = i == n - 1
            rrect(c, px, py, cw, ch, 7)
            fill(c, GOLD if last else "#1C2B44")
            place = 10 ** (n - 2 - i)  # last window = tenths
            val = v / place
            dgt = int(math.floor(val)) % 10
            frac = val - math.floor(val)
            # roll: units-of-this-place only move while the lower places are carrying
            if not last:
                lower = (v % place) / place if place >= 1 else 0
                frac = clamp((lower - 0.9) / 0.1) if place >= 1 else frac
            c.save()
            rrect(c, px, py, cw, ch, 7)
            c.clip()
            for j, dd in ((0, dgt), (1, (dgt + 1) % 10)):
                oy = py + 15 + (j - frac) * ch
                digit(c, dd, px + 10, oy, 1.0, NAVY if last else CREAM, 4.4)
            g = cairo.LinearGradient(0, py, 0, py + ch)
            g.add_color_stop_rgba(0, 0, 0, 0, 0.35)
            g.add_color_stop_rgba(0.3, 0, 0, 0, 0)
            g.add_color_stop_rgba(0.7, 0, 0, 0, 0)
            g.add_color_stop_rgba(1, 0, 0, 0, 0.35)
            c.rectangle(px, py, cw, ch)
            c.set_source(g)
            c.fill()
            c.restore()
        c.restore()

    def scenery(self, c, t):
        speed = 260.0
        c.push_group()
        # far skyline (slow)
        off = (t * speed * 0.25) % 400
        for i in range(-1, 4):
            bx = i * 400 - off
            for (dx, w, h) in ((0, 70, 120), (80, 50, 170), (140, 90, 90), (250, 60, 140), (320, 70, 100)):
                rrect(c, bx + dx, 640 - h, w, h + 4, 6)
                fill(c, "#1E3657")
        # trees (mid)
        off = (t * speed * 0.6) % 260
        for i in range(-1, 6):
            tx = i * 260 - off + 40
            c.rectangle(tx - 4, 590, 8, 52)
            fill(c, "#1B2F4D")
            ell(c, tx, 580, 30, 36)
            fill(c, "#2A5A63")
        # road
        c.rectangle(0, 640, self.W, 70)
        fill(c, "#22395A")
        c.rectangle(0, 640, self.W, 4)
        fill(c, GOLD, 0.6)
        off = (t * speed) % 110
        for i in range(-1, 11):
            rrect(c, i * 110 - off, 672, 60, 7, 3.5)
            fill(c, CREAM, 0.75)
        c.pop_group_to_source()
        g = cairo.LinearGradient(0, 0, self.W, 0)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(0.12, 0, 0, 0, 1)
        g.add_color_stop_rgba(0.88, 0, 0, 0, 1)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        c.mask(g)

    def car(self, c, t):
        k = self.look
        bob = 2.2 * math.sin(t * 9) + 1.2 * math.sin(t * 5.3)
        cx = 470
        c.save()
        c.translate(0, bob * 0.5)
        shadow(c, cx, 652, 230, 12, a=0.4)
        # speed lines
        for i, (yy, ln) in enumerate(((560, 70), (590, 110), (620, 60))):
            u = (t * 2.2 + i * 0.37) % 1
            x0 = cx - 250 - u * 120
            c.move_to(x0, yy)
            c.line_to(x0 + ln, yy)
            stroke(c, CREAM, 5, a=0.5 * math.sin(math.pi * u))
        c.translate(0, bob)
        # body
        body = [(cx - 205, 620), (cx - 212, 560), (cx - 190, 520), (cx - 120, 470), (cx + 20, 466), (cx + 80, 500),
                (cx + 190, 520), (cx + 222, 556), (cx + 220, 616)]
        poly(c, catmull(body, n=6))
        c.line_to(cx + 220, 626)
        c.line_to(cx - 205, 626)
        c.close_path()
        fill(c, TEAL)
        c.save()
        poly(c, catmull(body, n=6))
        c.line_to(cx + 220, 626)
        c.line_to(cx - 205, 626)
        c.close_path()
        c.clip()
        c.rectangle(cx - 240, 588, 480, 50)
        fill(c, TEAL_D)
        c.rectangle(cx - 240, 584, 480, 5)
        fill(c, GOLD_L, 0.9)
        c.restore()
        # windows
        win = [(cx - 160, 530), (cx - 112, 488), (cx + 12, 486), (cx + 62, 516), (cx + 66, 530)]
        poly(c, win)
        fill(c, "#D7E6E3")
        c.save()
        poly(c, win)
        c.clip()
        # driver inside
        dk_ = self.look
        tilt = 0.05 * math.sin(t * 1.4)
        c.save()
        c.translate(cx - 6, 566)
        c.scale(0.62, 0.62)
        rrect(c, -62, -8, 124, 100, 34)
        fill(c, dk_.top)
        head(c, dk_, 4, -100, tilt=tilt, face=0.8, eye=blink(t, 0.3), mouth="smile", gaze=(4, 0))
        c.restore()
        poly(c, [(cx - 50, 470), (cx - 34, 470), (cx - 50, 560), (cx - 66, 560)])
        fill(c, TEAL_D)
        c.move_to(cx - 100, 520)
        c.line_to(cx - 40, 470)
        stroke(c, WHITE, 6, a=0.45)
        c.restore()
        # steering wheel hint and arm
        c.move_to(cx + 30, 556)
        c.line_to(cx + 52, 534)
        stroke(c, INK, 7)
        # door line, handle, lights
        c.move_to(cx - 44, 536)
        c.line_to(cx - 48, 616)
        stroke(c, TEAL_D, 3)
        rrect(c, cx - 30, 552, 26, 7, 3.5)
        fill(c, TEAL_D)
        rrect(c, cx + 196, 540, 26, 18, 8)
        fill(c, GOLD_P)
        rrect(c, cx - 214, 548, 14, 26, 6)
        fill(c, BURG)
        # roof sign with a pin (no text)
        rrect(c, cx - 70, 446, 90, 24, 10)
        fill(c, GOLD)
        c.save()
        c.translate(cx - 25, 466)
        c.scale(0.45, 0.45)
        c.move_to(0, 0)
        c.curve_to(-6, -10, -16, -18, -16, -28)
        c.arc(0, -28, 16, math.pi, TAU)
        c.curve_to(16, -18, 6, -10, 0, 0)
        c.close_path()
        fill(c, NAVY)
        c.restore()
        # wheels
        ang = t * 260 / 34
        for wx in (cx - 130, cx + 140):
            ell(c, wx, 620, 44)
            fill(c, NAVY)
            ell(c, wx, 624, 36)
            fill(c, "#0E1626")
            ell(c, wx, 624, 18)
            fill(c, "#C9CED6")
            for i in range(5):
                a = ang + i * TAU / 5
                c.move_to(wx + 5 * math.cos(a), 624 + 5 * math.sin(a))
                c.line_to(wx + 16 * math.cos(a), 624 + 16 * math.sin(a))
            stroke(c, "#8F97A6", 4)
            ell(c, wx, 624, 5)
            fill(c, NAVY)
        c.restore()

    def draw(self, c, t):
        self.scenery(c, t)
        self.car(c, t)
        self.odometer(c, t)
        self.mapcard(c, t)


# ------------------------------------------------------------------------------------------------ 6. mascot (Ledger)
class Mascot(Character):
    """Ledger: a small, friendly ledger book. Reactions: thumbs, hmm, wow."""
    W, H = 440, 500
    disc = (220, 290, 190)
    intro = 1.3
    COVER, SPINE, LIMB = GOLD, "#8E6F2E", "#5E4720"

    def __init__(self, mood):
        self.mood = mood
        self.name = "mascot-" + mood

    def draw(self, c, t):
        m = self.mood
        gy = 470
        cx = 220
        idle = max(0.0, t - self.intro)
        bob = 4 * math.sin(t * 2.4)
        jump = squash = 0.0
        lean = 0.0
        if m == "wow":
            k = seg(t, 0.0, 0.18)
            j = seg(t, 0.18, 0.62)
            squash = 0.1 * math.sin(math.pi * k) - 0.06 * math.sin(math.pi * seg(t, 0.62, 0.8))
            jump = 46 * math.sin(math.pi * j)
            bob *= seg(t, 0.8, 1.2)
            if idle > 0:
                lean = 0.025 * math.sin(idle * 9) * max(0, 1 - idle * 0.8)
        elif m == "thumbs":
            lean = 0.06 * e_out(seg(t, 0.1, 0.5)) - 0.02 * math.sin(math.pi * seg(t, 0.5, 0.9))
        else:
            lean = -0.07 * e_out(seg(t, 0.1, 0.6)) + 0.015 * math.sin(idle * 1.5)
        shadow(c, cx, gy - 2, 110 - jump * 0.6, 12, a=0.32)
        # legs + shoes
        ly = gy - 12
        top_y = 150 - bob - jump
        bot = 420 - bob * 0.5 - jump
        for side in (-1, 1):
            c.move_to(cx + side * 40, bot - 6)
            c.line_to(cx + side * 44, ly - jump)
            stroke(c, self.LIMB, 13)
            ell(c, cx + side * 50, ly + 2 - jump, 26, 12)
            fill(c, CREAM)
        c.save()
        c.translate(cx, bot)
        c.rotate(lean)
        c.scale(1 + squash, 1 - squash)
        c.translate(-cx, -bot)
        x0, w = cx - 110, 220
        y0, h = top_y, bot - top_y
        # back cover + page block (depth)
        rrect(c, x0 + 14, y0 + 10, w, h, 24)
        fill(c, dk(self.COVER, 0.3))
        rrect(c, x0 + 10, y0 + 6, w - 4, h - 6, 20)
        fill(c, PAPER)
        for i in range(5):
            c.move_to(x0 + w + 2, y0 + 26 + i * (h - 50) / 4)
            c.line_to(x0 + w + 10, y0 + 26 + i * (h - 50) / 4)
        stroke(c, "#D9D1BF", 2)
        # front cover
        rrect(c, x0, y0, w, h, 24)
        fill(c, self.COVER)
        c.save()
        rrect(c, x0, y0, w, h, 24)
        c.clip()
        c.rectangle(x0, y0, 40, h)
        fill(c, self.SPINE)
        for yy in (y0 + 34, y0 + h - 40):
            c.rectangle(x0, yy, 40, 6)
            fill(c, GOLD_L)
        c.rectangle(x0 + 40, y0, 6, h)
        fill(c, "#000000", 0.12)
        c.restore()
        # ribbon bookmark
        c.move_to(x0 + w - 60, y0 + h - 4)
        c.line_to(x0 + w - 60, y0 + h + 30 + 3 * math.sin(t * 3))
        c.line_to(x0 + w - 52, y0 + h + 22 + 3 * math.sin(t * 3))
        c.line_to(x0 + w - 44, y0 + h + 30 + 3 * math.sin(t * 3))
        c.line_to(x0 + w - 44, y0 + h - 4)
        c.close_path()
        fill(c, BURG)
        # face
        fx = x0 + 40 + (w - 40) / 2
        fy = y0 + h * 0.4
        op = blink(t, 0.9)
        eye_s = 1.0
        gaze = (3, 0)
        if m == "wow":
            eye_s = 1 + 0.25 * e_back(seg(t, 0.1, 0.4))
            gaze = (0, -1)
        if m == "hmm":
            gaze = (-5 * e_out(seg(t, 0.2, 0.6)), -7 * e_out(seg(t, 0.2, 0.6)))
        wink = m == "thumbs" and 0.45 < t < 1.0
        for side in (-1, 1):
            ex = fx + side * 36
            if wink and side > 0:
                c.move_to(ex - 13, fy + 2)
                c.curve_to(ex - 5, fy - 8, ex + 5, fy - 8, ex + 13, fy + 2)
                stroke(c, INK, 5)
                continue
            ell(c, ex, fy, 20 * eye_s, 24 * eye_s * max(op, 0.08))
            fill(c, WHITE)
            if op > 0.3:
                pr = 10 if m != "wow" else 7.5
                ell(c, ex + gaze[0], fy + gaze[1] + 2, pr, pr * op)
                fill(c, INK)
                ell(c, ex + gaze[0] + 3, fy + gaze[1] - 2, 3, 3 * op)
                fill(c, WHITE)
            # brows
            lift = 0
            if m == "hmm":
                lift = (10 if side > 0 else -2) * e_out(seg(t, 0.2, 0.6))
            if m == "wow":
                lift = 10 * e_out(seg(t, 0.1, 0.4))
            c.move_to(ex - 13, fy - 34 - lift + (side * 2 if m == "hmm" else 0))
            c.curve_to(ex - 5, fy - 40 - lift, ex + 5, fy - 40 - lift, ex + 13, fy - 34 - lift)
            stroke(c, self.LIMB, 6)
        for side in (-1, 1):
            ell(c, fx + side * 58, fy + 28, 13, 8)
            fill(c, BLUSH, 0.35)
        my = fy + 44
        if m == "wow":
            o = seg(t, 0.1, 0.35)
            ell(c, fx, my + 2, 10 + 4 * o, 13 + 6 * o - 4 * seg(idle, 0, 1))
            fill(c, "#5A2430")
        elif m == "hmm":
            c.move_to(fx - 14, my + 2)
            c.curve_to(fx - 4, my - 2, fx + 6, my + 6, fx + 16, my)
            stroke(c, INK, 5)
        else:
            k = e_out(seg(t, 0.15, 0.45))
            c.move_to(fx - 22, my - 4)
            c.curve_to(fx - 12, my + 10 + 8 * k, fx + 12, my + 10 + 8 * k, fx + 22, my - 4)
            if k > 0.3:
                c.close_path()
                fill(c, "#5A2430")
            else:
                stroke(c, INK, 5)
        # emblem: three short ledger rules
        for i in range(3):
            rrect(c, fx - 30, y0 + h - 70 + i * 14, 60 - i * 14, 6, 3)
            fill(c, PAPER, 0.75)
        # arms
        shy = y0 + h * 0.58
        lsh, rsh = (x0 + 4, shy), (x0 + w - 4, shy)
        if m == "thumbs":
            k = e_back(seg(t, 0.1, 0.5), 2.0)
            rh = (lerp(x0 + w + 40, x0 + w + 70, k), lerp(shy + 70, y0 + 40, k) + 3 * math.sin(idle * 4))
            lh = (x0 - 40, shy + 70)
        elif m == "hmm":
            k = e_out(seg(t, 0.1, 0.55))
            rh = (lerp(x0 + w + 40, fx + 30, k), lerp(shy + 70, my + 24, k))
            lh = (lerp(x0 - 40, x0 - 30, k), lerp(shy + 70, shy + 40, k))
        else:
            k = e_back(seg(t, 0.12, 0.45), 2.0)
            rh = (lerp(x0 + w + 40, x0 + w + 70, k), lerp(shy + 70, y0 - 10, k))
            lh = (lerp(x0 - 40, x0 - 70, k), lerp(shy + 70, y0 - 10, k))
        for s_, hnd, side in ((lsh, lh, -1), (rsh, rh, 1)):
            mid = ((s_[0] + hnd[0]) / 2 + side * 16, (s_[1] + hnd[1]) / 2 + 10)
            poly(c, catmull([s_, mid, hnd], n=6), close=False)
            stroke(c, self.LIMB, 13)
        for hnd, side in ((lh, -1), (rh, 1)):
            ell(c, hnd[0], hnd[1], 17)
            fill(c, CREAM)
            if m == "thumbs" and side > 0 and k > 0.5:
                rrect(c, hnd[0] - 7.5, hnd[1] - 42, 15, 32, 7.5)
                fill(c, CREAM)
        c.restore()
        # extras
        if m == "thumbs":
            sp = seg(t, 0.4, 0.7)
            if sp > 0:
                r = 22 * e_back(sp, 2.5) * (0.85 + 0.15 * math.sin(idle * 3))
                sparkle(c, x0 + w + 112, y0 + 10 - bob, r, GOLD_L, rot=0.4 * t)
                sparkle(c, x0 + w + 44, y0 - 40 - bob, r * 0.55, CREAM, rot=-0.3 * t)
        elif m == "hmm":
            for i, (dx, dy, r) in enumerate(((x0 + w + 20, y0 - 6, 9), (x0 + w + 44, y0 - 40, 13), (x0 + w + 78, y0 - 82, 19))):
                k2 = e_back(seg(t, 0.45 + i * 0.22, 0.7 + i * 0.22), 2.2)
                pulse = 1 + 0.12 * math.sin(idle * 4 - i * 1.1) * seg(idle, 0, 0.3)
                if k2 > 0:
                    ell(c, dx, dy - bob, r * k2 * pulse)
                    fill(c, CREAM, 0.92)
        else:
            b = seg(t, 0.35, 0.95)
            if 0 < b < 1:
                for i in range(7):
                    a = -math.pi / 2 + (i - 3) * 0.42
                    r0, r1 = 150 + 30 * e_out(b), 170 + 60 * e_out(b)
                    ox, oy = cx, y0 + 90 - jump * 0.3
                    c.move_to(ox + r0 * math.cos(a), oy + r0 * math.sin(a))
                    c.line_to(ox + r1 * math.cos(a), oy + r1 * math.sin(a))
                    stroke(c, GOLD_L, 7, a=1 - b)


# ------------------------------------------------------------------------------------------------ registry + API
CHARACTERS = {ch.name: ch for ch in (Artist(), Student(), Worker(), Owner(), Driver(),
                                     Mascot("thumbs"), Mascot("hmm"), Mascot("wow"))}
ALIASES = {"f1": "student", "f-1": "student", "h1b": "worker", "h-1b": "worker", "shop": "owner", "gig": "driver",
           "mascot": "mascot-thumbs"}


def get(name):
    n = ALIASES.get(name, name)
    if n not in CHARACTERS:
        raise KeyError(f"unknown character {name!r}; one of: {', '.join(CHARACTERS)}")
    return CHARACTERS[n]


def render(name, t, w, h, alpha=1.0, backdrop=True, pop=True):
    return get(name).render(t, w, h, alpha=alpha, backdrop=backdrop, pop=pop)


# ------------------------------------------------------------------------------------------------ placement in a short
SAFE_L, SAFE_R, TEXT_TOP, TEXT_BOT = 96, FW - 126, 400, 1490   # shorts.py scene box (text area)
FEATURE_H = 0.28    # share of frame height in the hook (24-40 %)
CORNER_H = 0.15     # share of frame height in a corner (12-18 %)
GAP = 24            # space between the hook text and the character


def box_for(name, where):
    ch = get(name)
    if where == "corner":
        h = round(FH * CORNER_H)
        w = round(h * ch.W / ch.H)
        return (SAFE_L, TEXT_BOT - h, w, h)
    h = round(FH * FEATURE_H)
    w = min(SAFE_R - SAFE_L, round(h * ch.W / ch.H))
    x = SAFE_L + ((SAFE_R - SAFE_L) - w) // 2
    y = TEXT_BOT - h + 6 if where == "lower" else TEXT_TOP
    return (x, y, w, h)


CORNER_MIN = 0.105  # below this share of frame height the corner character is skipped for that scene
CHECK_JS = r"""
function charfree(B,m){  // per scene: true when nothing in the settled scene comes within m px of box B=[x,y,w,h]
  const out=[];
  document.querySelectorAll('.scene').forEach((s,i)=>{
    const b=+s.dataset.e,last=s.dataset.last==='1';
    seek(last?TOTAL-0.05:b-0.3);
    let ok=true;
    s.querySelectorAll('*').forEach(el=>{const r=el.getBoundingClientRect();
      if(r.width===0||r.height===0) return;
      if(r.right>B[0]-m&&r.left<B[0]+B[2]+m&&r.bottom>B[1]-m&&r.top<B[1]+B[3]+m) ok=false;});
    out.push(ok);
  });
  seek(0);
  return out;
}
function charroom(X0,X1,m){  // per scene: lowest bottom edge of anything in the settled scene within columns X0..X1
  const out=[];
  document.querySelectorAll('.scene').forEach((s,i)=>{
    const b=+s.dataset.e,last=s.dataset.last==='1';
    seek(last?TOTAL-0.05:b-0.3);
    let low=0;
    s.querySelectorAll('*').forEach(el=>{const r=el.getBoundingClientRect();
      if(r.width===0||r.height===0) return;
      if(r.right>X0-m&&r.left<X1+m) low=Math.max(low,r.bottom);});
    out.push(low);
  });
  seek(0);
  return out;
}
"""


class Track:
    """Where and when a character appears in a short.

    spec["character"] = {"name": "artist", "scene": "hook" | "none", "position": "lower" | "upper",
                         "corner_after": true, "corner": "self" | "mascot-thumbs" | ...}
    The hook shows `name` large (its one-shot plays from t=0). With corner_after the character (or `corner`) then
    sits small in the bottom-left corner of every later scene that leaves room under its text: 15 % of the frame
    height when there is room, down to 10.5 %, otherwise it steps out for that scene. It never covers text.
    """

    def __init__(self, cfg, scenes):
        if isinstance(cfg, str):
            cfg = {"name": cfg}
        self.cfg = cfg
        self.name = get(cfg.get("name", "")).name
        self.featured = cfg.get("scene", "hook") == "hook"
        self.position = cfg.get("position", "lower")
        if self.position not in ("lower", "upper"):
            raise SystemExit(f"character.position must be lower or upper, not {self.position!r}")
        corner = cfg.get("corner", "self")
        self.corner_name = self.name if corner == "self" else get(corner).name
        self.corner_on = bool(cfg.get("corner_after", not self.featured))
        self.scenes = scenes
        self.fbox = box_for(self.name, self.position)
        self.cmax = box_for(self.corner_name, "corner")
        self.boxes = [None] * len(scenes)   # corner box per scene (None = no room)

    # -- page hooks
    def inject(self, html):
        """Extra CSS (hook text moves clear of the character) and the room-check functions."""
        css = ""
        if self.featured:
            x, y, w, h = self.fbox
            if self.position == "lower":
                css = f".scene.t-hook{{bottom:{FH - (y - GAP)}px}}"
            else:
                css = f".scene.t-hook{{top:{y + h + GAP}px}}"
            css += ".big.hook{font-size:108px}.t-hook .sub{font-size:38px}"
        return html.replace("</style>", css + "</style>", 1).replace("</script>", CHECK_JS + "</script>", 1)

    def check(self, pg):
        """Run after set_content: measures the room under each scene's text; returns layout problems."""
        bad = []
        x, _, w, _ = self.cmax
        lows = pg.evaluate("([a,b,m])=>charroom(a,b,m)", [x, x + w, 12])
        ch = get(self.corner_name)
        for i, low in enumerate(lows):
            if i == 0 and self.featured:
                continue
            h = int(min(self.cmax[3], TEXT_BOT - max(low, TEXT_TOP) - 18))
            if h >= FH * CORNER_MIN:
                self.boxes[i] = (SAFE_L, TEXT_BOT - h, round(h * ch.W / ch.H), h)
        if self.featured and not pg.evaluate("([B,m])=>charfree(B,m)", [list(self.fbox), 8])[0]:
            bad.append("character: hook text runs into the character box (shorten the hook or sub)")
        return bad

    # -- per frame
    def state(self, t):
        """[(name, character time, (x, y, w, h), alpha)] for frame time t."""
        sc, bx = self.scenes, self.boxes
        hook_end = sc[0]["e"]
        on = [self.corner_on and b is not None for b in bx]
        fly = self.featured and len(sc) > 1 and on[1] and self.corner_name == self.name
        if self.featured and t < hook_end + (0.25 if fly else 0):
            if fly:
                k = e_inout(seg(t, hook_end - 0.35, hook_end + 0.25))
                return [(self.name, t, tuple(lerp(a, b, k) for a, b in zip(self.fbox, bx[1])), 1.0)]
            a = 1 - seg(t, hook_end - 0.22, hook_end)
            return [(self.name, t, self.fbox, a)] if a > 0 else []
        if not self.corner_on:
            return []
        for i in range(len(sc) - 1, 0, -1):
            s, e = sc[i]["s"], sc[i]["e"]
            last = i == len(sc) - 1
            if t < s - 0.3 or (t >= e and not last) or not on[i]:
                continue
            prev_on = on[i - 1] if i > 1 else fly
            next_on = (not last) and on[i + 1]
            a = 1.0
            if not prev_on:
                a *= seg(t, s - 0.3, s - 0.02)
            if not next_on and not last:
                a *= 1 - seg(t, e - 0.22, e)
            b = bx[i]
            if prev_on and i > 1 and bx[i - 1] != b:  # resize smoothly between scenes
                k = e_inout(seg(t, s - 0.3, s + 0.1))
                b = tuple(lerp(p, q, k) for p, q in zip(bx[i - 1], b))
            run = i  # a different corner character (a mascot reaction) restarts when it reappears
            while run > 1 and on[run - 1]:
                run -= 1
            ct = t if self.corner_name == self.name else max(0.0, t - (sc[run]["s"] - 0.3))
            if a > 0:
                return [(self.corner_name, ct, b, a)]
            return []
        return []

    def composite(self, data, t):
        """Paste the character onto a screenshot (JPEG or PNG bytes); returns bytes in the same format."""
        st = self.state(t)
        if not st:
            return data
        im = Image.open(io.BytesIO(data))
        fmt = im.format
        im = im.convert("RGB")
        for name, ct, (x, y, w, h), a in st:
            lay = render(name, ct, w, h, alpha=a)
            im.paste(lay, (int(round(x)), int(round(y))), lay)
        buf = io.BytesIO()
        if fmt == "JPEG":
            im.save(buf, "JPEG", quality=94)
        else:
            im.save(buf, "PNG", compress_level=1)
        return buf.getvalue()


# ------------------------------------------------------------------------------------------------ previews
def navy_bg():
    import numpy as np
    y = np.linspace(0, 1, FH)[:, None]
    x = np.linspace(0, 1, FW)[None, :]
    top, mid, bot = np.array([11, 26, 51]), np.array([16, 35, 63]), np.array([33, 58, 92])
    k = np.clip(y * 0.75 + x * 0.25, 0, 1)[..., None]
    a = np.where(k < 0.5, top + (mid - top) * (k / 0.5), mid + (bot - mid) * ((k - 0.5) / 0.5))
    return Image.fromarray(a.astype("uint8"), "RGB")


def preview(name, out_dir, secs=6.5):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    bg = navy_bg()
    mp4 = out_dir / f"character-{name}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(mp4)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    mascots = ["mascot-thumbs", "mascot-hmm", "mascot-wow"]
    for i in range(int(secs * FPS)):
        t = i / FPS
        fr = bg.copy()
        if name == "mascot":
            per = secs / 3
            j = min(2, int(t // per))
            u = t - j * per
            x, y, w, h = box_for(mascots[j], "lower")
            fr.paste(lay := render(mascots[j], u, w, h, alpha=seg(u, 0, 0.2) if j else 1), (x, y), lay)
            if j < 2 and u > per - 0.2:
                pass
        else:
            fb, cb = box_for(name, "lower"), box_for(name, "corner")
            k = e_inout(seg(t, 4.0, 4.6))
            b = tuple(int(round(lerp(a, b_, k))) for a, b_ in zip(fb, cb))
            lay = render(name, t, b[2], b[3])
            fr.paste(lay, (b[0], b[1]), lay)
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    return mp4


def sheet(out_dir, times=(0, 0.8, 1.6, 2.4, 3.2)):
    from PIL import ImageDraw, ImageFont
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(CHARACTERS)
    cw, chh, lab, pad = 330, 330, 210, 14
    W = lab + len(times) * (cw + pad) + pad
    H = 70 + len(names) * (chh + pad) + pad
    im = Image.new("RGB", (W, H), (16, 35, 63))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24)
        fs = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 20)
    except OSError:
        f = fs = ImageFont.load_default()
    for j, t in enumerate(times):
        d.text((lab + pad + j * (cw + pad) + 8, 26), f"{t:.1f} s", fill=(216, 183, 105), font=fs)
    for i, n in enumerate(names):
        y = 70 + i * (chh + pad)
        d.text((24, y + chh // 2 - 14), n, fill=(241, 238, 230), font=f)
        ch = CHARACTERS[n]
        for j, t in enumerate(times):
            x = lab + pad + j * (cw + pad)
            d.rounded_rectangle((x, y, x + cw, y + chh), 14, fill=(22, 43, 74))
            w = cw - 20
            h = min(chh - 20, round(w * ch.H / ch.W))
            lay = ch.render(t, w, h)
            im.paste(lay, (x + 10, y + chh - 10 - h), lay)
    p = out_dir / "characters-sheet.jpg"
    im.save(p, quality=90)
    return p


def bench():
    import time
    for n, ch in CHARACTERS.items():
        for where in ("lower", "corner"):
            _, _, w, h = box_for(n, where)
            t0 = time.time()
            for i in range(60):
                ch.render(i / 30, w, h)
            print(f"{n:14s} {where:6s} {w}x{h}: {(time.time() - t0) / 60 * 1000:5.1f} ms/frame")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd = argv[0]
    if cmd == "preview":
        out = argv[1]
        names = argv[2:] or ["artist", "student", "worker", "owner", "driver", "mascot"]
        for n in names:
            print(preview(n, out))
    elif cmd == "sheet":
        print(sheet(argv[1]))
    elif cmd == "frame":
        name, t, out = argv[1], float(argv[2]), argv[3]
        w, h = (int(argv[4]), int(argv[5])) if len(argv) > 5 else (900, 900)
        render(name, t, w, h).save(out)
        print(out)
    elif cmd == "bench":
        bench()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
