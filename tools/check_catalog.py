#!/usr/bin/env python3
"""Checks catalog/products.json and the built /shop/ page against each other (offline).

Run before every push that touches products:  python3 tools/check_catalog.py
Exit code 1 on any problem. Live Gumroad/Etsy prices are compared by the daily
"MFA shop price check" scheduled task (WebFetch), since this container can't reach gumroad.com.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cat = json.loads((ROOT / "catalog" / "products.json").read_text(encoding="utf-8"))
shop = (ROOT / "site" / "shop" / "index.html").read_text(encoding="utf-8")
errs = []
PRICE = re.compile(r"^\d+(\.\d{2})?$")
ids, slugs = set(), set()

for p in cat["products"]:
    pid = p.get("id")
    tag = f'{pid} {p.get("name")}'
    if pid in ids:
        errs.append(f"{tag}: duplicate id")
    ids.add(pid)
    text = json.dumps(p, ensure_ascii=False)
    if re.search(r"\bfree\b", text, re.I):
        errs.append(f'{tag}: contains the word "free"')
    if re.search(r"\bCPA firm\b", text):
        errs.append(f'{tag}: says "CPA firm"')
    if p["status"] not in ("live", "planned", "draft", "retired"):
        errs.append(f'{tag}: unknown status {p["status"]}')
    g = p["gumroad"]
    if p["status"] == "live":
        if not p.get("slug") or p["slug"] in slugs:
            errs.append(f"{tag}: missing or duplicate slug")
        slugs.add(p.get("slug"))
        if not g.get("url") or not str(g.get("price") or "").strip():
            errs.append(f"{tag}: live product needs a Gumroad url and price")
            continue
        if not PRICE.match(str(g["price"])):
            errs.append(f'{tag}: bad price format {g["price"]}')
        if not g["url"].endswith("/l/" + p["slug"]):
            errs.append(f"{tag}: Gumroad url doesn't match slug")
        if not p["shop"].get("blurb"):
            errs.append(f"{tag}: missing shop blurb")
        # the built page must show this product's link and price
        e0 = p.get("etsy") or {}
        buy_url = e0["url"] if e0.get("allowed") and e0.get("url") else g["url"]
        if f'href="{buy_url}"' not in shop:
            errs.append(f"{tag}: /shop/ is missing its Buy link (rebuild: python3 tools/build_resources.py)")
        if f'>${g["price"]}<' not in shop:
            errs.append(f'{tag}: /shop/ does not show ${g["price"]} (rebuild)')
    e = p.get("etsy") or {}
    if e.get("allowed") and e.get("sale") is not None and g.get("price") and float(e["sale"]) != float(g["price"]):
        errs.append(f'{tag}: Etsy sale price {e["sale"]} != Gumroad price {g["price"]}')

live_links = set(re.findall(r'href="(https://(?:mfaadvisory\.gumroad\.com/l|www\.etsy\.com/listing)/[^"]+)"', shop))
cat_links = {p["gumroad"]["url"] for p in cat["products"] if p["status"] == "live"} | \
            {p["etsy"]["url"] for p in cat["products"] if p["status"] == "live" and (p.get("etsy") or {}).get("url")}
for extra in sorted(live_links - cat_links):
    errs.append(f"/shop/ links to {extra}, which isn't a live catalog product")

live = sum(1 for p in cat["products"] if p["status"] == "live")
if errs:
    print("CATALOG CHECK FAILED\n- " + "\n- ".join(errs))
    sys.exit(1)
print(f"catalog OK: {live} live, {len(cat['products']) - live} not live; /shop/ matches")
