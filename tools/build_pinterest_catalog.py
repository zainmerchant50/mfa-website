#!/usr/bin/env python3
"""Pinterest Catalogs product feed (organic shoppable product Pins; no ads, no spend).

Writes site/feeds/pinterest-catalog.csv (and a matching RSS 2.0 / g: namespace pinterest-catalog.xml) from
catalog/products.json via seo.live_products(), the same LIVE list and prices /shop/ shows. Pinterest pulls the CSV
daily (Pinterest Business → Catalogs → data source, set up 2026-11-04 for Zain's "use whatever we can" request).

Rules: published prices only (never new ones); skip any product priced at 0; no "free"; links go to the product's card
on /shop/ (the claimed domain, where Pinterest checks the price) with utm_source=pinterest&utm_medium=catalog.
Images: site/feeds/img/<slug>.jpg, a JPEG copy of the /shop/ card image (site/shop/img/<slug>.webp). A product
without that image is left out until it has one.
Run after any catalog change: python3 tools/build_pinterest_catalog.py
"""
import csv
import html
import io
import re
from pathlib import Path

from PIL import Image

import seo

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = SITE / "feeds"
BASE = "https://mfa-advisory.com"
UTM = "utm_source=pinterest&utm_medium=catalog&utm_campaign=shop"
BRAND = "MFA"
# Google product taxonomy paths (Pinterest accepts the text path).
CAT_TEMPLATE = "Software > Digital Goods & Currency > Document Templates"
CAT_GUIDE = "Media > Books > E-books"
FIELDS = ["id", "title", "description", "link", "image_link", "price", "availability", "condition", "brand",
          "google_product_category", "product_type"]
BANNED = re.compile(r"\bfree\b|tax-free|\bCPA\b", re.I)


SKIPPED = []


def rows():
    out = []
    for p in seo.live_products():
        price = float(p["price"] or 0)
        if price <= 0:
            continue
        slug = p["slug"]
        if not (SITE / "shop" / "img" / f"{slug}.webp").exists():
            SKIPPED.append(slug)  # no picture on /shop/ yet: a product Pin needs one
            continue
        desc = f'{p["blurb"]} Format: {p["format"]}. Instant download after checkout.'
        row = {
            "id": slug,
            "title": p["name"][:500],
            "description": desc[:10000],
            "link": f"{BASE}/shop/?{UTM}&utm_content={slug}#{slug}",
            "image_link": f"{BASE}/feeds/img/{slug}.jpg",
            "price": f"{price:.2f} USD",
            "availability": "in stock",
            "condition": "new",
            "brand": BRAND,
            "google_product_category": CAT_GUIDE if p["group"] == "Tax mini-guides" else CAT_TEMPLATE,
            "product_type": f'Digital downloads > {p["group"]}',
        }
        for k in ("title", "description", "product_type"):
            if BANNED.search(row[k]):
                raise SystemExit(f"banned word in {slug} {k}: {row[k]}")
        out.append(row)
    return out


def images(items):
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    for r in items:
        src = SITE / "shop" / "img" / f'{r["id"]}.webp'
        dst = OUT / "img" / f'{r["id"]}.jpg'
        if not src.exists():
            raise SystemExit(f"missing shop image {src}")
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            continue
        im = Image.open(src).convert("RGB")
        im = im.resize((800, 800), Image.LANCZOS) if im.size[0] < 800 else im
        im.save(dst, "JPEG", quality=90, optimize=True)


def write_csv(items):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writeheader()
    w.writerows(items)
    (OUT / "pinterest-catalog.csv").write_text(buf.getvalue(), encoding="utf-8")


def write_xml(items):
    e = lambda s: html.escape(s, quote=False)
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel>',
             f"<title>MFA shop</title><link>{BASE}/shop/</link>",
             "<description>Tax calculators, bookkeeping checklists and tax guides from MFA.</description>"]
    for r in items:
        parts.append("<item>" + "".join(
            f"<g:{k}>{e(r[k])}</g:{k}>" if k not in ("title", "description", "link") else f"<{k}>{e(r[k])}</{k}>"
            for k in FIELDS) + "</item>")
    parts.append("</channel></rss>\n")
    (OUT / "pinterest-catalog.xml").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    items = rows()
    images(items)
    write_csv(items)
    write_xml(items)
    print(f"wrote site/feeds/pinterest-catalog.csv/.xml: {len(items)} products")
    if SKIPPED:
        print("skipped (no site/shop/img/<slug>.webp):", ", ".join(SKIPPED))
