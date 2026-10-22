#!/usr/bin/env python3
"""Checks the built site (site/) for SEO and AI-discovery problems. Offline, standard library only.

Run after every build:   python3 tools/check_seo.py
Optional vocabulary check of every JSON-LD type and property against schema.org (needs schema-dts, which
ships schema.org as TypeScript):   npm pack schema-dts && tar xzf schema-dts-*.tgz
                                   python3 tools/check_seo.py --vocab package/dist/schema.d.ts

Per indexable page: one <title> (<= 60 chars) and unique; one meta description (<= 155 chars) and unique; exactly one canonical,
https://mfa-advisory.com/... (no www), listed in sitemap.xml; exactly one <h1>; Open Graph and Twitter tags; every JSON-LD block
parses; @id references resolve inside the page; no ratings/reviews markup; img alt present.
Site files: sitemap.xml, robots.txt (all search/assistant bots allowed), llms.txt links, catalog.json, and the MFA project rules
(no "free", "CPA firm" or "certified" in machine-readable output, no street address).
Exit code 1 on any error.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BASE = "https://mfa-advisory.com"
errs, warns = [], []
BOTS = ["Googlebot", "Bingbot", "Applebot", "OAI-SearchBot", "ChatGPT-User", "GPTBot", "Claude-SearchBot", "Claude-User", "ClaudeBot",
        "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "DuckAssistBot"]


def E(p, m):
    errs.append(f"{p}: {m}")


def vocab_from_dts(path):
    """{type: (parents, props)} parsed from schema-dts' schema.d.ts."""
    txt = Path(path).read_text(encoding="utf-8")
    types = {}
    for m in re.finditer(r"^(?:export )?interface (\w+?)(?:Base|Leaf) extends ([^{]+) \{\n(.*?)^\}", txt, re.S | re.M):
        name, parents, body = m.group(1), [x.strip() for x in m.group(2).split(",")], m.group(3)
        t = types.setdefault(name, [set(), set()])
        t[0].update(re.sub(r"(Base|Leaf)$", "", x) for x in parents if re.fullmatch(r"\w+", x))
        t[1].update(re.findall(r'^\s+"(\w+)"\??:', body, re.M))
    return types


def allowed_props(types, t, seen=None):
    seen = seen or set()
    if t in seen or t not in types:
        return set()
    seen.add(t)
    out = set(types[t][1])
    for p in types[t][0]:
        out |= allowed_props(types, p, seen)
    return out


def walk(x, fn, path=""):
    if isinstance(x, dict):
        fn(x, path)
        for k, v in x.items():
            walk(v, fn, f"{path}/{k}")
    elif isinstance(x, list):
        for v in x:
            walk(v, fn, path)


def check_ld(rel, blocks, vocab):
    defined, refs, typed = {}, [], {}
    for b in blocks:
        try:
            j = json.loads(b)
        except Exception as e:
            E(rel, f"JSON-LD does not parse: {e}")
            continue
        if j.get("@context") != "https://schema.org":
            E(rel, "JSON-LD @context is not https://schema.org")

        def visit(n, path):
            t = n.get("@type")
            if t in ("AggregateRating", "Review", "Rating") or "aggregateRating" in n or "review" in n:
                E(rel, "ratings/reviews markup is not allowed (nothing is published to support it)")
            if "@id" in n:
                if len(n) == 1:
                    refs.append(n["@id"])
                else:
                    if n["@id"] in defined and defined[n["@id"]] != t and path.count("/") <= 2:
                        E(rel, f"@id {n['@id']} defined with two types ({defined[n['@id']]}, {t})")
                    defined.setdefault(n["@id"], t)
            if vocab and isinstance(t, str):
                if t not in vocab:
                    E(rel, f"unknown schema.org type {t}")
                else:
                    ok = allowed_props(vocab, t) | {"Thing"}
                    for k in n:
                        if not k.startswith("@") and k not in ok:
                            E(rel, f"property {k} is not valid on {t}")
        walk(j, visit)
    for r in refs:
        if r not in defined:
            E(rel, f"@id reference {r} is not defined on the page")
    return defined


def main():
    vocab = None
    if "--vocab" in sys.argv:
        vocab = vocab_from_dts(sys.argv[sys.argv.index("--vocab") + 1])
        print(f"schema.org vocabulary loaded: {len(vocab)} types")
    sm = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    smurls = re.findall(r"<loc>(.*?)</loc>", sm)
    if len(smurls) != len(set(smurls)):
        E("sitemap.xml", "duplicate URLs")
    titles, descs, indexable = {}, {}, []
    for p in sorted(SITE.rglob("*.html")):
        rel = "/" + str(p.relative_to(SITE))
        s = p.read_text(encoding="utf-8")
        noindex = bool(re.search(r'<meta[^>]+name="robots"[^>]+noindex', s))
        if p.name == "404.html":
            continue
        t = re.findall(r"<title>(.*?)</title>", s, re.S)
        if len(t) != 1:
            E(rel, f"{len(t)} <title> tags")
            continue
        title = html.unescape(t[0]).strip()
        d = re.findall(r'<meta name="description" content="(.*?)"', s, re.S)
        desc = html.unescape(d[0]).strip() if d else ""
        can = re.findall(r'<link rel="canonical" href="(.*?)"', s)
        robots = re.findall(r'<meta name="robots"', s)
        if len(robots) > 1:
            E(rel, "more than one robots meta tag")
        if noindex:
            continue
        indexable.append(rel)
        if len(title) > 60:
            E(rel, f"title is {len(title)} chars (max 60): {title}")
        if len(d) != 1 or not 50 <= len(desc) <= 155:
            E(rel, f"meta description missing/duplicated or {len(desc)} chars (50-155)")
        titles.setdefault(title, []).append(rel)
        descs.setdefault(desc, []).append(rel)
        if len(can) != 1:
            E(rel, f"{len(can)} canonical tags")
        else:
            c = can[0]
            if not c.startswith(BASE + "/"):
                E(rel, f"canonical not on the apex https domain: {c}")
            if c not in smurls:
                E(rel, f"canonical {c} is not in sitemap.xml")
        h1 = len(re.findall(r"<h1[\s>]", s))
        if h1 != 1:
            E(rel, f"{h1} <h1> tags")
        for k in ("og:title", "og:description", "og:url", "og:image", "og:type"):
            if f'property="{k}"' not in s:
                E(rel, f"missing {k}")
        for k in ("twitter:card", "twitter:title", "twitter:description"):
            if f'name="{k}"' not in s:
                E(rel, f"missing {k}")
        if f'property="og:url" content="{can[0] if can else ""}"' not in s:
            E(rel, "og:url differs from canonical")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
        if not blocks:
            E(rel, "no JSON-LD")
        defined = check_ld(rel, blocks, vocab)
        if blocks and "https://mfa-advisory.com/#organization" not in defined:
            E(rel, "JSON-LD graph does not define the organization")
        if blocks and not any(v == "BreadcrumbList" for v in defined.values()) and not any('"BreadcrumbList"' in b for b in blocks) and rel != "/index.html":
            warns.append(f"{rel}: no BreadcrumbList")
        for img in re.findall(r"<img\b[^>]*>", s):
            if "alt=" not in img:
                E(rel, f"<img> without alt: {img[:80]}")
        low = html.unescape(re.sub(r"<[^>]+>", " ", s)).lower()
        if re.search(r"\b\d{1,5} [a-z0-9 ]+ (street|st\.|avenue|ave\.|road|rd\.|boulevard|blvd)\b[^.]{0,30}princeton", low):
            E(rel, "looks like a street address")
        for banned in (r"\bcpa firm\b", r"\bcertified (?:public|accountant|quickbooks)", r"\bfree\b"):
            if re.search(banned, f"{title} {desc}".lower()):
                E(rel, f"banned wording in title/description ({banned})")
    for k, v in titles.items():
        if len(v) > 1:
            E(", ".join(v), f"duplicate title: {k}")
    for k, v in descs.items():
        if len(v) > 1:
            E(", ".join(v), f"duplicate description: {k}")
    # sitemap
    for u in smurls:
        path = u[len(BASE):]
        f = SITE / path.lstrip("/") / "index.html" if path.endswith("/") else SITE / path.lstrip("/")
        if not f.exists():
            E("sitemap.xml", f"{u} has no file")
        elif "/" + str(f.relative_to(SITE)) not in indexable:
            E("sitemap.xml", f"{u} is noindex or not indexable")
    for rel in indexable:
        u = BASE + (rel[: -len("index.html")] if rel.endswith("/index.html") else rel)
        if u not in smurls:
            E("sitemap.xml", f"indexable page {u} is missing")
    if not re.search(r"<lastmod>\d{4}-\d\d-\d\d</lastmod>", sm):
        E("sitemap.xml", "no lastmod dates")
    # robots
    rb = (SITE / "robots.txt").read_text(encoding="utf-8")
    for b in BOTS:
        if not re.search(rf"User-agent: {re.escape(b)}\nAllow: /\n", rb):
            E("robots.txt", f"{b} is not explicitly allowed")
    if re.search(r"^Disallow:\s*(?!/cdn-cgi/\s*$)\S", rb, re.M):  # /cdn-cgi/ (Cloudflare internals) is the only allowed Disallow
        E("robots.txt", "has a Disallow rule")
    if f"Sitemap: {BASE}/sitemap.xml" not in rb:
        E("robots.txt", "no Sitemap line")
    # llms files
    for name in ("llms.txt", "llms-full.txt"):
        txt = (SITE / name).read_text(encoding="utf-8")
        if not txt.startswith("# "):
            E(name, "must start with an H1")
        for u in set(re.findall(r"\]\((https://mfa-advisory\.com[^)\s]*)\)", txt)):
            path = u[len(BASE):].split("#")[0]
            f = SITE / path.lstrip("/") / "index.html" if path.endswith("/") else SITE / path.lstrip("/")
            if path not in ("", "/") and not f.exists():
                E(name, f"link {u} has no file")
        for banned in (r"\bfree\b", r"\bcpa firm\b", r"\bcertified\b", r"spring st"):
            if re.search(banned, txt, re.I):
                E(name, f"banned wording {banned}")
    cat = (SITE / "catalog.json").read_text(encoding="utf-8")
    try:
        cj = json.loads(cat)
        check_ld("catalog.json", [json.dumps(cj)], vocab)
    except Exception as e:
        E("catalog.json", f"does not parse: {e}")
    for banned in (r"\bfree\b", r"\bcpa firm\b", r"\bcertified\b"):
        if re.search(banned, cat, re.I):
            E("catalog.json", f"banned wording {banned}")
    for w in warns:
        print("warn:", w)
    if errs:
        print("SEO CHECK FAILED\n- " + "\n- ".join(errs))
        sys.exit(1)
    print(f"seo OK: {len(indexable)} indexable pages, {len(smurls)} sitemap URLs, titles/descriptions unique and within limits")


if __name__ == "__main__":
    main()
