#!/usr/bin/env python3
"""Builds the Is It Deductible? tool (/tools/is-it-deductible/). Site session owns this file.

Called from tools/build_resources.py (build()). Every rule, figure and source lives in data/deductions.json
(checked on irs.gov or in the Code/Regs; see meta.checked). Redesigned 2026-10-23 for business owners rather than
accountants ("Can I write this off?"): search, everyday tap cards, and answers that lead with Yes / Partly / Usually not,
then the why, what to keep as proof and a common mistake. Form and line detail sits in a small "For your accountant" fold.

Every answer is server-rendered (crawlable, readable without JavaScript); site/resources/deductible.js adds search and
the answer sheet. Figures shared with other tools (mileage, home office) are cross-checked against
data/tax-figures-2026.json at build time.
"""
import hashlib
import json
import re
from datetime import date
from pathlib import Path

import build_blog as B
import seo
import ui_kit
from build_resources import BASE, EXTRA_CSS, NOTE, OG, SITE, clean_ld, cta, esc, write

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "deductions.json").read_text(encoding="utf-8"))
FIG = json.loads((ROOT / "data" / "tax-figures-2026.json").read_text(encoding="utf-8"))
SLUG = "is-it-deductible"
URL = f"{BASE}/tools/{SLUG}/"
JSON_URL = URL + "deductions.json"   # the dataset, published next to the page (data/deductions.json + license note)
PAGE_MODIFIED = "2026-10-23"         # page/markup last changed (facts: meta.checked; review: meta.last_reviewed)
LICENSE_NOTE = ("© Merchant Financial Advisory LLC. You may quote or reuse this data if you cite it with a link to "
                + URL + ". Educational information only, not tax, legal or accounting advice.")
V = lambda f: hashlib.md5((SITE / "resources" / f).read_bytes()).hexdigest()[:10]
GENERAL = "General information, not tax advice."

# The owner-facing answer (entry["answer"]); the technical verdict stays in the dataset and the accountant fold.
ANSWERS = {
    "yes": {"label": "Yes", "line": "It counts as a business expense when it's a normal, needed cost of running your business."},
    "partly": {"label": "Partly", "line": "Some of it counts: the business share, a percentage like half, or up to a limit."},
    "no": {"label": "Usually not", "line": "It generally doesn't count as a business expense, with only narrow exceptions."},
}
TECH = {"deductible": "Deductible", "partly": "Partly deductible", "depends": "Depends on the facts", "not": "Not deductible"}
TOOL_NAMES = {
    "/tools/home-office-deduction-calculator/": "Home office deduction calculator",
    "/tools/mileage-deduction-calculator/": "Mileage deduction calculator",
    "/tools/do-i-need-to-send-a-1099/": "Do I need to send a 1099?",
    "/tools/1099-contractor-tracker/": "1099 contractor tracker",
    "/tools/w-9-request-email-template/": "W-9 request email templates",
    "/tools/1099-tax-calculator/": "1099 tax calculator",
    "/tools/quarterly-estimated-tax-calculator/": "Quarterly estimated tax calculator",
    "/tools/paycheck-tax-calculator/": "Paycheck tax calculator",
    "/tools/s-corp-tax-savings-calculator/": "S corp tax savings calculator",
    "/llc-formation/": "LLC formation: NJ & NY fees",
}
# Everyday tap cards: (label, entry slug, icon override)
EVERYDAY = [("Car", "mileage", None), ("Phone", "cell-phone", None), ("Home office", "home-office", None),
            ("Meals with clients", "meals", None), ("Travel", "business-travel", None), ("Gym", "gym", None),
            ("Clothes", "uniforms", None), ("Software and apps", "software-subscriptions", None), ("Courses", "business-education", None),
            ("Gifts for clients", "client-gifts", None), ("Laptop", "computer", None), ("Internet", "internet", None),
            ("Health insurance", "self-employed-health-insurance", None), ("Ads", "advertising", None),
            ("Freelancers", "contractors", None), ("Parking tickets", "fines-penalties", "ticket")]
# Plain-English names for the dataset's categories
GROUPS = {"home": "Home and workspace", "vehicle": "Car and travel", "meals": "Food and entertaining",
          "tech": "Phone, internet and software", "equip": "Equipment and bigger buys", "people": "Paying people",
          "insurance": "Insurance and health", "retire": "Saving for retirement", "pro": "Accountants, lawyers and dues",
          "marketing": "Marketing and gifts", "education": "Courses and learning", "banking": "Bank fees, loans and unpaid bills",
          "startup": "Starting a business", "inventory": "Products and shipping", "taxes": "Taxes and licenses",
          "not": "Things that usually don't count"}

ICONS = {  # 24px line icons (stroke = currentColor)
    "home": '<path d="M3.5 11 12 4l8.5 7"/><path d="M5.5 9.5V20h13V9.5M10 20v-5h4v5"/>',
    "building": '<path d="M5 21V4.5h9V21M14 9h5v12M3 21h18M8 8h3M8 11.5h3M8 15h3M16.5 12.5h0M16.5 16h0"/>',
    "desk": '<path d="M3 10h18M5 10v9M19 10v9M13.5 14h5.5"/><rect x="8" y="3.5" width="7" height="4.5" rx="1"/><path d="M11.5 8v2"/>',
    "bolt": '<path d="M13 2.5 5 13.5h6l-1 8 8-11h-6z"/>',
    "pencil": '<path d="M4 20l1-4.5L15.5 5a2.1 2.1 0 0 1 3 3L8 18.5zM13.5 7l3 3"/>',
    "shirt": '<path d="M8.5 3.5 4 6l-1.5 4.5 3 1.2v8.8h13v-8.8l3-1.2L20 6l-4.5-2.5c-.6 1.6-2 2.5-3.5 2.5s-2.9-.9-3.5-2.5z"/>',
    "car": '<path d="M5 16.5h14M6.5 16.5V19M17.5 16.5V19M4 16.5l1.6-5.2A2 2 0 0 1 7.5 10h9a2 2 0 0 1 1.9 1.3l1.6 5.2"/><circle cx="8" cy="14" r=".6"/><circle cx="16" cy="14" r=".6"/>',
    "fuel": '<path d="M4.5 20.5V5A1.5 1.5 0 0 1 6 3.5h7A1.5 1.5 0 0 1 14.5 5v15.5M3 20.5h13M7 7.5h5M14.5 10h2a1.5 1.5 0 0 1 1.5 1.5V16a1.5 1.5 0 0 0 3 0V8.5L18.5 6"/>',
    "parking": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M10 16.5v-9h3a2.5 2.5 0 0 1 0 5h-3"/>',
    "plane": '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
    "meal": '<path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M16 3c-1.7 0-3 2-3 5s1.3 4 3 4v9"/>',
    "ticket": '<path d="M3.5 8V6.5h17V8a2.5 2.5 0 0 0 0 5v4.5h-17V13a2.5 2.5 0 0 0 0-5z"/><path d="M14.5 7v1.5M14.5 11v2M14.5 15.5V17"/>',
    "party": '<path d="M12 3c3 0 5 2.4 5 5.5S14.5 15 12 15 7 11.6 7 8.5 9 3 12 3z"/><path d="m11 15-.8 1.6h3.6L13 15M12 16.6c0 2-2 2.4-2 4.4"/>',
    "coffee": '<path d="M4.5 9h12v5a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5zM16.5 10.5H18a2.5 2.5 0 0 1 0 5h-2M8 3.5c-.6.9.6 1.6 0 2.5M12 3.5c-.6.9.6 1.6 0 2.5"/>',
    "phone": '<rect x="6.5" y="2.5" width="11" height="19" rx="2.5"/><path d="M10.5 18.5h3"/>',
    "wifi": '<path d="M2.5 9a14 14 0 0 1 19 0M5.5 12.3a9.5 9.5 0 0 1 13 0M8.6 15.5a5 5 0 0 1 6.8 0"/><circle cx="12" cy="19" r=".8"/>',
    "app": '<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="3.5"/>',
    "laptop": '<rect x="4.5" y="5" width="15" height="10" rx="1.5"/><path d="M2.5 19h19"/>',
    "chair": '<path d="M7 3.5h10l-1 8H8zM6 11.5h12M8.5 11.5 7 20.5M15.5 11.5l1.5 9M12 11.5v6"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "tag": '<path d="M3.5 12.2V4.5a1 1 0 0 1 1-1h7.7l8.3 8.3a1.4 1.4 0 0 1 0 2l-6.4 6.4a1.4 1.4 0 0 1-2 0z"/><circle cx="8" cy="8" r="1.4"/>',
    "tool": '<path d="M14.5 6.5a4 4 0 0 0-5.3 5.3L4 17l3 3 5.2-5.2a4 4 0 0 0 5.3-5.3l-2.4 2.4-2.6-.4-.4-2.6z"/>',
    "hammer": '<path d="M13.5 9.5 4 19l1.5 1.5 9.5-9.5M11 5.5l2.5-2.5 2.5 1 4.5 4.5-2 2-2-1-1.5 1.5-3-3z"/>',
    "handshake": '<rect x="3" y="7.5" width="18" height="12.5" rx="2"/><path d="M8.5 7.5v-2A1.5 1.5 0 0 1 10 4h4a1.5 1.5 0 0 1 1.5 1.5v2M3 13h18M11 13v1.5h2V13"/>',
    "cash": '<rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M6 9.5v5M18 9.5v5"/>',
    "receipt": '<path d="M6 3h12v18l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4L6 21z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
    "heart": '<path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7a4.3 4.3 0 0 1 7.5 2.8C19.5 15.4 12 20 12 20z"/>',
    "award": '<circle cx="12" cy="9" r="5.5"/><path d="M8.5 13.3 7 21l5-2.8 5 2.8-1.5-7.7"/>',
    "umbrella": '<path d="M3 12a9 9 0 0 1 18 0zM12 12v6.5a2 2 0 0 1-4 0"/>',
    "health": '<rect x="3.5" y="3.5" width="17" height="17" rx="4"/><path d="M12 8v8M8 12h8"/>',
    "shield": '<path d="M12 3 4.5 6v5.5c0 4.4 3.1 8.1 7.5 9.5 4.4-1.4 7.5-5.1 7.5-9.5V6z"/><path d="m9 12 2 2 4-4"/>',
    "piggy": '<path d="M5 11a6 5 0 0 1 11-2.8L19 7v4l1.5 1v3H18a6 5 0 0 1-2.5 2.2V20h-3v-2.1a7 6 0 0 1-2 0V20h-3v-3A5 5 0 0 1 5 11z"/><circle cx="15" cy="11" r=".6"/>',
    "scale": '<path d="M12 4v16M5 8h14M5 8l-2.5 6a3 3 0 0 0 5 0zM19 8l-2.5 6a3 3 0 0 0 5 0zM8 20h8"/>',
    "calc": '<rect x="5" y="2.5" width="14" height="19" rx="2.5"/><path d="M8.5 6.5h7M8.5 11h1M12 11h1M15.5 11h0M8.5 14.5h1M12 14.5h1M15.5 14.5v3M8.5 18h1M12 18h1"/>',
    "badge": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2.2"/><path d="M5.8 16a3.5 3.5 0 0 1 6.4 0M14.5 10h4M14.5 13.5h3"/>',
    "megaphone": '<path d="M4 10v4h3l7 4V6L7 10zM17 9.5a3.5 3.5 0 0 1 0 5M7 14l1.2 5h2.3l-.9-4.2"/>',
    "gift": '<rect x="3.5" y="8.5" width="17" height="4" rx="1"/><path d="M5 12.5v8h14v-8M12 8.5v12M12 8.5C10.5 5 7 4.5 7 6.6S10 8.5 12 8.5zM12 8.5c1.5-3.5 5-4 5-1.9S14 8.5 12 8.5z"/>',
    "pen": '<path d="M18.5 3.5a2 2 0 0 1 2 2L9 17l-4 1.5L6.5 14.5z"/><path d="M15.5 6.5l2 2"/>',
    "book": '<path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5zM12 6.5v13"/>',
    "card": '<rect x="2.5" y="5.5" width="19" height="13" rx="2"/><path d="M2.5 10h19M6 14.5h4"/>',
    "percent": '<circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/><path d="M19 5 5 19"/>',
    "invoice": '<path d="M6 2.5h9l4 4v15H6z"/><path d="M15 2.5v4h4M9 11h7M9 14.5h7M9 18h4"/>',
    "rocket": '<path d="M12 15c-1.5-1.5-2.5-3.5-2-6.5C10.5 6 12.5 4 16 3.5c.5 3.5-1.5 5.5-4 6.5M9.5 14.5 7 17M8 12.5H5l2.5-3h3M11.5 16v3l3-2.5v-3"/><circle cx="14.5" cy="8" r="1"/>',
    "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "box": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/>',
    "truck": '<path d="M2.5 6.5h11v10h-11zM13.5 10h4l3 3.2v3.3h-7"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    "gov": '<path d="M4 20h16M5.5 20v-8M9.5 20v-8M14.5 20v-8M18.5 20v-8M3.5 12h17M6 12a6 6 0 0 1 12 0M12 6V3.5"/>',
    "cert": '<rect x="3.5" y="4" width="17" height="12.5" rx="1.5"/><path d="M7 8h10M7 11h6"/><circle cx="16" cy="16.5" r="2.5"/><path d="m14.8 18.6-.8 2.9 2-1 2 1-.8-2.9"/>',
    "train": '<rect x="5.5" y="3" width="13" height="14" rx="3"/><path d="M5.5 10.5h13M8.5 14h0M15.5 14h0M8 17l-2 4M16 17l2 4"/>',
    "warn": '<path d="M12 3.5 2.5 20h19z"/><path d="M12 10v4.5M12 17.2v.3"/>',
    "flag": '<path d="M5 21V4M5 4.5h11l-2 3.5 2 3.5H5"/>',
    "golf": '<path d="M8 19.5V3.5l8 3.5-8 3.5"/><path d="M3.5 20.5c1.5-.7 3-1 4.5-1s3 .3 4.5 1"/>',
    "cart": '<path d="M3 4h2.5l2.2 11h10.6l2-8H6.5"/><circle cx="9" cy="19.5" r="1.4"/><circle cx="17" cy="19.5" r="1.4"/>',
    "hands": '<path d="M12 11.5s-4-2.4-4-5.2A2.2 2.2 0 0 1 12 5a2.2 2.2 0 0 1 4 1.3c0 2.8-4 5.2-4 5.2z"/><path d="M3 15.5h3.5L10 17h4a1.5 1.5 0 0 1 0 3H9.5M14 20h1.5l5-3a1.4 1.4 0 0 0-1.5-2.4l-3.5 2M3 14v7"/>',
    "gym": '<path d="M7.5 12h9M4.5 8.5v7M7.5 6.5v11M16.5 6.5v11M19.5 8.5v7M2.5 12h2M19.5 12h2"/>',
    "people": '<circle cx="9" cy="8.5" r="3"/><path d="M3.5 19a5.5 5.5 0 0 1 11 0"/><circle cx="17" cy="9.5" r="2.4"/><path d="M15.5 14.4A4.5 4.5 0 0 1 21 19"/>',
    "cap": '<path d="m2.5 9 9.5-4.5L21.5 9 12 13.5z"/><path d="M6.5 11v4.5c1.6 1.4 3.5 2 5.5 2s3.9-.6 5.5-2V11M21.5 9v5"/>',
    "bank": '<path d="M3 9.5 12 4l9 5.5M4.5 10v8M9 10v8M15 10v8M19.5 10v8M3 20h18"/>',
    "ban": '<circle cx="12" cy="12" r="8.5"/><path d="m6 6 12 12"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.8v.2"/>',
    "chev": '<path d="m9 6 6 6-6 6"/>',
    "a-yes": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "a-partly": '<circle cx="12" cy="12" r="7.5"/><path d="M12 4.5a7.5 7.5 0 0 1 0 15z" fill="currentColor"/>',
    "a-no": '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
}
CAT_ICON = {"home": "home", "vehicle": "car", "meals": "meal", "tech": "phone", "equip": "tool", "people": "people", "insurance": "shield",
            "retire": "piggy", "pro": "scale", "marketing": "megaphone", "education": "cap", "banking": "bank", "startup": "rocket",
            "inventory": "box", "taxes": "receipt", "not": "ban"}
svg = lambda k, w=1.7: (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{w}" stroke-linecap="round" '
                        f'stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[k]}</svg>')


def nice(d):
    """Oct. 21, 2026 (AP-style month abbreviations)."""
    d = date.fromisoformat(d[:10])
    m = {3: "March", 4: "April", 5: "May", 6: "June", 7: "July"}.get(d.month) or d.strftime("%b") + "."
    return f"{'Sept.' if d.month == 9 else m} {d.day}, {d.year}"


def check_data():
    """Fail the build if the data drifts from the shared figures or breaks the project rules."""
    E = DATA["entries"]
    by = {e["slug"]: e for e in E}
    m = FIG["mileage"]
    for k in ("business_rate_2026_jan_jun", "business_rate_2026_jul_dec"):
        assert f'{m[k]["value"] * 100:g} cents' in by["mileage"]["limits"], f"mileage entry doesn't match tax-figures-2026.json {k}"
        assert f'{m[k]["value"] * 100:g} cents' in by["mileage"]["plain"], f"mileage plain wording doesn't match tax-figures-2026.json {k}"
    h = FIG["home_office_simplified"]
    lim = by["home-office"]["limits"]
    assert f'${h["rate_per_sq_ft"]["value"]} per square foot' in lim and f'{h["max_sq_ft"]["value"]} square feet' in lim and f'${h["max_deduction"]["value"]:,}' in lim, \
        "home office entry doesn't match tax-figures-2026.json"
    assert f'${h["rate_per_sq_ft"]["value"]} per square foot, up to {h["max_sq_ft"]["value"]} square feet' in by["home-office"]["plain"], "home office plain wording drifted"
    txt = json.dumps(DATA, ensure_ascii=False).lower()
    assert " free " not in txt.replace('"', " ") and "cpa firm" not in txt and "mfasite" not in txt, "banned wording in deductions.json"
    cats = {c["id"] for c in DATA["meta"]["categories"]}
    for e in E:
        for u in [e["source_url"]] + [a["url"] for a in e.get("also", [])]:
            assert u.startswith(("https://www.irs.gov/", "https://www.law.cornell.edu/")), f'{e["slug"]}: source must be irs.gov or the Code/Regs ({u})'
        for u in e.get("tools", []):
            assert u in TOOL_NAMES and (SITE / u.strip("/") / "index.html").exists(), f'{e["slug"]}: unknown tool link {u}'
        assert e.get("answer") in ANSWERS, f'{e["slug"]}: answer must be yes|partly|no'
        assert e.get("plain") and e.get("mistake") and e.get("keep"), f'{e["slug"]}: plain, keep and mistake are required'
        assert e.get("icon") in ICONS, f'{e["slug"]}: unknown icon {e.get("icon")}'
        assert e["category"] in cats and e["category"] in GROUPS, f'{e["slug"]}: unknown category'
    for _, s, ic in EVERYDAY:
        assert s in by and (ic is None or ic in ICONS), f"everyday card points at unknown entry {s}"
    gym = by.get("gym")
    assert gym and gym["answer"] == "no", "gym and health club dues must read as personal / not deductible"
    for c in DATA["meta"]["categories"]:
        assert c["count"] == sum(1 for e in E if e["category"] == c["id"]), f'category count out of date: {c["id"]}'
    assert 50 <= len(E) <= 60, f"{len(E)} entries (expected 50-60)"


def first_sentence(t):
    return t.split(". ")[0].rstrip(".") + "."


def verdict_big(e):
    """Technical verdict for machine-readable output: '50% deductible', 'Partly deductible', 'Not deductible' ..."""
    if e["verdict"] == "not":
        return "Not deductible"
    if e["percent"] is not None:
        return f'{e["percent"]}% deductible'
    return {"deductible": "Deductible", "partly": "Partly deductible", "depends": "It depends"}[e["verdict"]]


def why(e):
    """The plain explanation without a leading 'Yes.' / 'No.' / 'Partly.' that would only repeat the answer badge."""
    t = re.sub(r"^(?:Yes|No|Partly|Half)[.:]\s+", "", e["plain"].strip())
    return t[0].upper() + t[1:]


def qualifier(e):
    """A short extra under the answer when one clear percentage applies."""
    p = e["percent"]
    return "Counts at half (50%)" if p == 50 else (f"Counts at {p}%" if p not in (None, 0, 100) else "")


def pill(e, big=False):
    a = e["answer"]
    return (f'<span class="vb a-{a}{" big" if big else ""}">{svg("a-" + a, 2.4 if a != "partly" else 1.8)}'
            f'<span>{esc(ANSWERS[a]["label"])}</span></span>')


def answer_body(e):
    """The complete answer for one expense. Server-rendered in the list; the JS answer sheet shows a copy of it."""
    src = (f'<li><a href="{esc(e["source_url"])}" target="_blank" rel="noopener">{esc(e["source_title"])}</a></li>' +
           "".join(f'<li><a href="{esc(a["url"])}" target="_blank" rel="noopener">{esc(a["title"])}</a></li>' for a in e.get("also", [])))
    tools = "".join(f'<li><a href="{u}">{esc(TOOL_NAMES[u])}</a></li>' for u in e.get("tools", []))
    q = qualifier(e)
    keep = "".join(f"<li>{esc(k)}</li>" for k in e["keep"])
    return (f'<div class="ans">'
            f'<p class="lead">{pill(e, True)}{f"<span class=q>{esc(q)}</span>" if q else ""}</p>'
            f'<p class="why">{esc(why(e))}</p>'
            + (f'<p class="eg"><b>For example:</b> {esc(e["example"])}</p>' if e.get("example") else "") +
            f'<div class="blk proof"><span class="bi">{svg("receipt")}</span><div><p class="bh">What to keep as proof</p><ul>{keep}</ul></div></div>'
            f'<div class="blk oops"><span class="bi">{svg("warn")}</span><div><p class="bh">Common mistake</p><p>{esc(e["mistake"])}</p></div></div>'
            f'<details class="acct"><summary>For your accountant</summary><div class="acct-in">'
            f'<dl><dt>Technical answer</dt><dd>{esc(TECH[e["verdict"]])}</dd>'
            f'<dt>The rule</dt><dd>{esc(e["rule"])}</dd><dt>Limits</dt><dd>{esc(e["limits"])}</dd>'
            f'<dt>Records</dt><dd>{esc(e["records"])}</dd><dt>Who it applies to</dt><dd>{esc(e["applies_to"])}</dd></dl>'
            f'<p class="ah">Official sources</p><ul class="srcs">{src}</ul>'
            + (f'<p class="ah">Related MFA tools</p><ul class="srcs">{tools}</ul>' if tools else "") +
            f'</div></details>'
            f'<p class="foot">{svg("info")}<span>{GENERAL} <a href="/book/" data-conv="book">Not sure about yours? Talk it through with us.</a></span></p>'
            f'</div>')


def row(e):
    """One expense in the browse list: a disclosure that holds the full answer (works without JS)."""
    return (f'<details class="ex" id="{e["slug"]}" data-slug="{e["slug"]}"><summary>'
            f'<span class="ic">{svg(e["icon"])}</span><h4 class="nm">{esc(e["name"])}</h4>{pill(e)}'
            f'<span class="go">{svg("chev", 2)}</span></summary>{answer_body(e)}</details>')


FAQ = [
    ("What makes a business expense deductible?",
     "The general test: the cost is ordinary (common in your line of work) and necessary (helpful for your business). Personal, living and family costs aren't "
     "deductible, and when something is used for both business and personal purposes, only the business share counts. Some expenses also have their "
     "own limits, such as the 50% limit on business meals and the $25 limit on gifts."),
    ("What can I write off if I'm self-employed?",
     "The normal, needed costs of running your business, reported on Schedule C. Common write-offs include software and supplies, "
     "advertising, payments to contractors, business insurance, business travel, a qualifying home office and the business share of your "
     "phone, internet and car. Self-employed people can also deduct half of their self-employment tax, self-employed health insurance "
     "premiums if they qualify, and contributions to a SEP IRA or solo 401(k); those are claimed on Form 1040 rather than Schedule C."),
    ("Can I write off my gym membership?",
     "Generally no. Gym, health club and fitness memberships are personal expenses, and dues to athletic and other social or recreational clubs "
     "aren't deductible even if you meet clients there."),
    ("Can I deduct 100% of business meals in 2026?",
     "Usually not. Business meals with clients and meals while traveling are generally 50% deductible (80% for workers under Department of "
     "Transportation hours-of-service limits). Holiday parties and similar events mainly for employees are fully deductible. Starting in 2026, food "
     "and drinks an employer provides to employees at work, such as office snacks or on-site meals for the employer's convenience, are no longer deductible."),
    ("What expenses are never deductible as business expenses?",
     "Commuting between home and your regular workplace, fines and penalties paid to a government (including parking tickets and tax "
     "penalties), political contributions and most lobbying, dues for social, athletic and similar clubs, entertainment such as game "
     "tickets and golf, and personal, living and family expenses. A sole proprietor's charitable donations aren't a business expense "
     "either, though they may be deductible on your personal return: on Schedule A if you itemize, or, starting in 2026, up to $1,000 of cash gifts "
     "($2,000 married filing jointly) if you don't."),
    ("What records do I need to keep?",
     "Keep receipts, canceled checks and other documents that support each deduction. For travel, meals, gifts and car use, also record the amount, "
     "date, place, business purpose and business relationship, and keep receipts for lodging and anything $75 or more. Keep records at least until the "
     "period to assess tax runs out, generally 3 years after you file, and employment tax records for at least 4 years."),
    ("Should I deduct equipment all at once or depreciate it?",
     "You often have a choice. Items of $2,500 or less per invoice or item can be deducted under the de minimis safe harbor election. Larger purchases "
     "can be expensed under Section 179 (up to $2,560,000 for tax years beginning in 2026) or with 100% bonus depreciation for property acquired after "
     "Jan. 19, 2025, or depreciated over several years. The best choice depends on your income this year and in later years, so it's worth running the numbers."),
    ("Does this tool apply to my W-2 job?",
     "It's written for self-employed people and small businesses. W-2 employees generally can't deduct unreimbursed job costs such as car expenses "
     "or a home office."),
    ("How current is this information?",
     f"Every entry was checked against IRS publications, instructions and the Internal Revenue Code (most recently on {nice(DATA['meta']['checked'])}), and "
     "uses 2026 figures where the IRS has published them. Where a 2026 edition isn't out yet, the latest edition is cited with its year. IRS Publication "
     "535 (Business Expenses) has been discontinued; its topics now live in Publication 334 and the Schedule C instructions."),
]


def all_sources():
    seen = {}
    for e in DATA["entries"]:
        for t, u in [(e["source_title"], e["source_url"])] + [(a["title"], a["url"]) for a in e.get("also", [])]:
            seen.setdefault(u, t)
    return seen


def sources_list():
    seen = all_sources()
    groups = [("IRS publications and instructions", lambda u: "/publications/" in u or "/instructions/" in u or "/pub/irs-pdf/" in u),
              ("Other IRS guidance", lambda u: u.startswith("https://www.irs.gov/")),
              ("Internal Revenue Code and Treasury Regulations", lambda u: True)]
    out, used = [], set()
    for name, test in groups:
        rows = sorted(((t, u) for u, t in seen.items() if u not in used and test(u)), key=lambda r: r[0])
        used |= {u for _, u in rows}
        if rows:
            out.append(f'<h3>{esc(name)}</h3><ul>' + "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in rows) + "</ul>")
    return "".join(out), len(seen)


def structured_data(title, desc, n):
    """WebPage (reviewedBy, citations) + WebApplication + Dataset + FAQPage + ItemList + BreadcrumbList, one @graph."""
    meta, E = DATA["meta"], DATA["entries"]
    pubs = [{"@type": "CreativeWork", "@id": u, "name": t, "url": u,
             "publisher": {"@type": "GovernmentOrganization", "name": "Internal Revenue Service", "url": "https://www.irs.gov/"}}
            for u, t in sorted(all_sources().items(), key=lambda r: r[1])
            if u.startswith("https://www.irs.gov/") and ("/publications/" in u or "/instructions/" in u or "/pub/irs-pdf/" in u)]
    app = {"@type": "WebApplication", "@id": URL + "#app", "name": "Tax Write-Offs for Small Business: Is It Deductible?", "url": URL,
           "description": desc, "applicationCategory": "FinanceApplication", "applicationSubCategory": "Tax deduction lookup",
           "operatingSystem": "Any", "browserRequirements": "Works in any modern browser; search uses JavaScript",
           "inLanguage": "en-US", "publisher": {"@id": seo.ORG_ID}, "creator": {"@id": seo.ORG_ID},
           "featureList": [f"Search {n} common business expenses in everyday words",
                           "Tap everyday categories such as car, phone, home office, meals, travel and gym",
                           "A plain answer (yes, partly or usually not), what to keep as proof, a common mistake and the IRS source for each expense"],
           "isBasedOn": {"@id": URL + "#dataset"}}
    dataset = {"@type": "Dataset", "@id": URL + "#dataset", "name": f"Is It Deductible? {meta['tax_year']} business expense deductions",
               "description": (f"{n} common small business expenses with a plain-English answer (yes, partly, usually not), the technical verdict, "
                               f"the percentage where one applies, the rule, limits, records to keep, a common mistake and who it applies to, each sourced "
                               f"to IRS publications, instructions or the Internal Revenue Code. Facts checked {nice(meta['checked'])}."),
               "url": URL, "sameAs": JSON_URL, "inLanguage": "en-US",
               "keywords": ["tax deductions", "business expenses", "self-employed", "Schedule C", "write-offs", str(meta["tax_year"])],
               "temporalCoverage": str(meta["tax_year"]), "spatialCoverage": {"@type": "Country", "name": "United States"},
               "dateModified": PAGE_MODIFIED, "creator": {"@id": seo.ORG_ID}, "publisher": {"@id": seo.ORG_ID},
               "copyrightHolder": {"@id": seo.ORG_ID}, "copyrightNotice": LICENSE_NOTE,
               "license": {"@type": "CreativeWork", "name": "Copyright Merchant Financial Advisory LLC; reuse with attribution (cite with a link)", "url": URL},
               "contributor": {"@id": seo.PERSON_ID}, "citation": [{"@id": c["@id"]} for c in pubs],
               "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": JSON_URL}}
    faq = {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    items = {"@type": "ItemList", "@id": URL + "#expenses", "name": f"{n} business expenses and whether they're deductible in {meta['tax_year']}",
             "numberOfItems": n, "itemListOrder": "https://schema.org/ItemListUnordered", "itemListElement": [
                 {"@type": "ListItem", "position": i, "url": f"{URL}#{e['slug']}", "name": f"{e['name']}: {ANSWERS[e['answer']]['label']}",
                  "description": why(e)} for i, e in enumerate(E, 1)]}
    ld = seo.graph(URL, title.replace(" | MFA", ""), desc, app, dataset, faq, items,
                   crumb=[("Home", BASE + "/"), ("Resources", BASE + "/resources/"), ("Is it tax deductible?", URL)],
                   modified=PAGE_MODIFIED,
                   extra={"mainEntity": {"@id": URL + "#app"}, "hasPart": [{"@id": URL + "#expenses"}, {"@id": URL + "#faq"}],
                          "reviewedBy": {"@id": seo.PERSON_ID}, "lastReviewed": meta["last_reviewed"], "citation": pubs,
                          "keywords": "tax write offs for small business, is it tax deductible, can I write this off, business expense deductions 2026, what can I write off self-employed"})
    return clean_ld(ld)


def write_json():
    """Publishes the dataset at /tools/is-it-deductible/deductions.json (same content as data/deductions.json, plus where it lives and the license)."""
    out = {"meta": {**{k: v for k, v in DATA["meta"].items() if k != "owner"}, "url": JSON_URL, "page": URL, "page_modified": PAGE_MODIFIED, "license": LICENSE_NOTE,
                    "publisher": seo.NAME}, "entries": DATA["entries"]}
    path = SITE / "tools" / SLUG / "deductions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def llms_lines(full_text=False):
    """Plain-text summary of every entry for llms.txt (one line each) and llms-full.txt (rule, limits, records, source). Used by tools/seo.py."""
    E = DATA["entries"]
    if not full_text:
        return [f"- [{e['name']}]({URL}#{e['slug']}): {ANSWERS[e['answer']]['label']}. {why(e)}" for e in E]
    o = []
    for e in E:
        o += [f"### {e['name']}: {ANSWERS[e['answer']]['label']} ({verdict_big(e)})", f"In plain English: {why(e)}",
              f"Keep as proof: {'; '.join(e['keep'])}", f"Common mistake: {e['mistake']}",
              f"Rule: {e['rule']}", f"Limits: {e['limits']}", f"Records to keep: {e['records']}",
              f"Applies to: {e['applies_to']}", f"Source: {e['source_title']} {e['source_url']}"]
        o += [f"Also: {a['title']} {a['url']}" for a in e.get("also", [])]
        o += [f"Page: {URL}#{e['slug']}", ""]
    return o


# Email capture (Hub, 2026-10-30, Zain): visitors leave with the checklist PDF, MFA keeps the lead.
# MailerLite form 202772412124628516 (single opt-in) → group "Write-off checklist" → automation emails the PDF.
CK_ENDPOINT = "https://assets.mailerlite.com/jsonp/2707043/forms/202772412124628516/subscribe"
CK_PDF = "/downloads/write-off-checklist-2026.pdf"


def checklist_box():
    n = len(DATA["entries"])
    css = ("<style>.ck-box{max-width:820px;margin:8px auto 40px}.ck-f{display:grid;gap:12px}"
           ".ck-f .nl-row{display:grid;grid-template-columns:1fr 1.4fr;gap:12px}"
           ".ck-f label{display:grid;gap:5px;font-size:.78rem;font-weight:600}"
           ".ck-f input{font:inherit;font-size:.95rem;padding:11px 13px;border:1px solid rgba(21,21,21,.18);border-radius:9px;background:#fff;color:#151515;width:100%}"
           ".ck-f .btn{justify-self:start;cursor:pointer;border:0;padding:14px 26px;background:var(--gold-b,#E2C98F);color:var(--navy,#13213A)}"
           ".ck-done a{color:var(--gold-b,#E2C98F);text-decoration:underline}"
           "@media (max-width:560px){.ck-f .nl-row{grid-template-columns:1fr}.ck-f .btn{justify-self:stretch;justify-content:center}}</style>")
    form = f"""<div class="wrap ck-box" id="checklist"><section class="nl-box" aria-label="Email me the write-off checklist">
  <span class="eyebrow">Keep this handy</span>
  <h2>Email me the {n}-expense write-off checklist</h2>
  <p>A printable PDF of every expense on this page: Yes, Partly or Usually not, plus the proof to keep for each one. Tick off what you spent this year and hand it to whoever does your taxes.</p>
  <form class="ck-f" novalidate>
  <div class="nl-row"><label>First name<input name="name" autocomplete="given-name"/></label><label>Email<input name="email" type="email" autocomplete="email" required/></label></div>
  <input class="ask-hp" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px"/>
  <button class="btn" type="submit">Email me the checklist</button>
  <p class="nl-fine">One email with the PDF now, then occasional tax-deadline reminders. Unsubscribe in one click. We never sell or share your address. <a href="/privacy.html">Privacy Policy</a>.</p>
  <p class="nl-st" role="status" aria-live="polite"></p>
  </form>
  <p class="nl-done ck-done" hidden>Sent. Check your inbox in a minute (and your promotions or spam folder). You can also <a href="{CK_PDF}" target="_blank" rel="noopener">open the checklist now</a>.</p>
</section></div>"""
    js = """<script>(function(){var f=document.querySelector('form.ck-f');if(!f)return;var b=f.querySelector('button'),l=b.textContent,st=f.querySelector('.nl-st'),ok=document.querySelector('.ck-done');
function done(){b.disabled=false;b.textContent=l;st.textContent='';f.hidden=true;ok.hidden=false;
try{if(window.gtag)gtag('event','generate_lead',{method:'write_off_checklist',page_path:location.pathname});}catch(e){}}
function fail(){b.disabled=false;b.textContent=l;st.textContent='Couldn\\u2019t send. Please email %(email)s with the word CHECKLIST.';}
f.addEventListener('submit',function(e){e.preventDefault();if(f._honey.value)return;if(!f.checkValidity()){f.reportValidity();return;}
b.disabled=true;b.textContent='Sending\\u2026';var m=new URLSearchParams();m.append('fields[email]',f.email.value.trim());
if(f.name.value)m.append('fields[name]',f.name.value.trim());m.append('ml-submit','1');m.append('anticsrf','true');
fetch('%(ml)s',{method:'POST',headers:{'Accept':'application/json'},body:m}).then(function(r){return r.json();})
.then(function(j){if(j&&j.success===false)throw 0;done();})
.catch(function(){fetch('%(ml)s',{method:'POST',mode:'no-cors',body:m}).then(done).catch(fail);});});})();</script>""" % {"ml": CK_ENDPOINT, "email": B.EMAIL}
    return css + form + js


def build():
    check_data()
    meta, E = DATA["meta"], DATA["entries"]
    by = {e["slug"]: e for e in E}
    checked = nice(meta["checked"])
    reviewed = nice(meta["last_reviewed"])
    n = len(E)
    title = "Tax Write-Offs for Small Business: Is It Deductible? | MFA"
    desc = (f"Tax write-offs for small business, 2026: search {n} everyday expenses for a plain answer, "
            "what proof to keep and the mistake to avoid.")
    assert len(title) <= 60 and len(desc) <= 155, (len(title), len(desc))

    tiles = "".join(
        f'<li><a class="tile" href="#{s}" data-open="{s}"><span class="ic">{svg(ic or by[s]["icon"])}</span>'
        f'<span class="tt"><span class="tl">{esc(label)}</span>{pill(by[s])}</span></a></li>' for label, s, ic in EVERYDAY)
    pk = by["meals"]
    peek = (f'<div class="dd-peek" aria-hidden="true"><div class="pk-card pk-back"></div><div class="pk-card">'
            f'<div class="pk-hd"><span class="ic">{svg(pk["icon"])}</span><b>{esc(pk["name"])}</b></div>'
            f'<p class="lead">{pill(pk, True)}<span class="q">{esc(qualifier(pk))}</span></p><p class="why">{esc(why(pk))}</p>'
            f'<div class="blk oops"><span class="bi">{svg("warn")}</span><div><p class="bh">Common mistake</p><p>{esc(pk["mistake"])}</p></div></div>'
            f'</div></div>')
    hero = f"""<header class="dd-hero"><div class="wrap"><div class="dd-hgrid"><div class="dd-htext">
  <div class="crumbs"><a href="/">Home</a> / <a href="/resources/">Resources</a> / Is it tax deductible?</div>
  <h1><span class="h1-kw">Tax write-offs for small business:</span> Is it deductible?</h1>
  <p class="dek">Can I write this off? Search or tap something your business spends money on. You'll get a straight answer for the {meta["tax_year"]} tax year, what to keep as proof and the mistake people make most.</p>
  <div class="dd-find" role="search">
    <label class="sr" for="dd-q">Search an expense</label>
    <div class="dd-sbox">{svg("search", 2)}<input type="search" id="dd-q" placeholder="Try “car”, “phone bill” or “gym”" autocomplete="off" spellcheck="false" aria-controls="dd-res" aria-describedby="dd-gen"/><button type="button" class="dd-clear" id="dd-clear" aria-label="Clear search" hidden>{svg("a-no", 2)}</button></div>
    <div class="dd-res" id="dd-res" hidden><p class="dd-count" id="dd-count" role="status" aria-live="polite"></p><ul id="dd-hits"></ul></div>
  </div>
  <p class="gen" id="dd-gen">{svg("info")}<span><strong>{GENERAL}</strong> Answers are written for small business owners and the self-employed.</span></p>
</div>{peek}</div></div></header>"""

    groups = []
    for c in meta["categories"]:
        rows = [e for e in E if e["category"] == c["id"]]
        if not rows:
            continue
        groups.append(f'<details class="grp" data-cat="{c["id"]}"><summary><span class="gi">{svg(CAT_ICON[c["id"]])}</span>'
                      f'<h3>{esc(GROUPS[c["id"]])}</h3><span class="gc">{len(rows)}</span><span class="go">{svg("chev", 2)}</span></summary>'
                      f'<div class="grp-in">{"".join(row(e) for e in rows)}</div></details>')
    legend = "".join(f'<li>{pill({"answer": k})}<span>{esc(v["line"])}</span></li>' for k, v in ANSWERS.items())
    main = f"""<main class="dd-main" id="dd-main">
<section class="dd-every wrap" aria-labelledby="dd-every-h">
  <h2 id="dd-every-h">Tap something you spend on</h2>
  <ul class="tiles">{tiles}</ul>
</section>
<section class="dd-all wrap" id="expenses" aria-labelledby="dd-all-h">
  <div class="dd-all-hd"><h2 id="dd-all-h">Everything else, by topic</h2><p>{n} expenses in all. Open a topic, then tap an expense for the full answer.</p></div>
  <div class="grps">{"".join(groups)}</div>
  <ul class="legend" aria-label="What the answers mean">{legend}</ul>
</section>
</main>"""

    src_html, n_src = sources_list()
    faq = ui_kit.faq_accordion([(esc(q), esc(a)) for q, a in FAQ])
    info = f"""<div class="tinfo dd-info"><article class="article">
<h2>How the answers work</h2>
<p>Each answer starts with <strong>Yes</strong>, <strong>Partly</strong> or <strong>Usually not</strong>, then says why in a sentence or two, what to keep as proof and the mistake people make most. The exact rule, limits, form references and the official source sit under “For your accountant” in every answer.</p>
<p>Answers are written for sole proprietors and single-member LLCs, and most apply the same way to partnerships and corporations. Figures are for the {meta["tax_year"]} tax year where the IRS has published them. To see what a deduction is worth, try the <a href="/tools/home-office-deduction-calculator/">home office calculator</a>, the <a href="/tools/mileage-deduction-calculator/">mileage calculator</a> or the <a href="/tools/1099-tax-calculator/">1099 tax calculator</a>.</p>
<p class="rev">Reviewed by <a href="/authors/zain-merchant/">Zain Merchant, ACCA</a> on {reviewed}. Facts last checked {checked}.</p>
<p>Building something with this? The full list is published as a dataset at <a href="/tools/{SLUG}/deductions.json">deductions.json</a>. Cite it with a link to this page.</p>
<section class="faqs" id="faqs"><h2>FAQs</h2>{faq}</section>
<section class="sources dd-src-g"><h2>Official sources</h2><p>All {n_src} sources used on this page. IRS Publication 535 (Business Expenses) has been discontinued, so it isn't cited.</p>{src_html}
<p class="disclaimer">{GENERAL} Tax rules change and depend on your facts, so check with a qualified tax professional before you file. Reviewed by <a href="/authors/zain-merchant/">Zain Merchant, ACCA</a>, {reviewed}. Facts checked against the sources above as of {checked}. {esc(NOTE)}</p></section>
</article></div>"""

    sheet = (f'<dialog class="dd-sheet" id="dd-sheet" aria-labelledby="dd-st"><div class="sh-hd"><span class="ic" id="dd-sic"></span>'
             f'<h2 id="dd-st"></h2><button type="button" class="sh-x" id="dd-sx" aria-label="Close">{svg("a-no", 2)}</button></div>'
             f'<div class="sh-bd" id="dd-sb"></div></dialog>')

    # Search index only: everything a reader sees is in the HTML above.
    payload = {"entries": [{"slug": e["slug"], "name": e["name"], "aliases": e["aliases"], "answer": e["answer"],
                            "group": GROUPS[e["category"]]} for e in E],
               "labels": {k: v["label"] for k, v in ANSWERS.items()}}
    data_tag = '<script type="application/json" id="dd-data">' + json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/") + "</script>"

    ld = structured_data(title, desc, n)
    extra = ('<script>document.documentElement.classList.add("dd-js")</script>' + EXTRA_CSS +
             f'<link rel="stylesheet" href="/resources/deductible.css?v={V("deductible.css")}"/>' +
             f'<link rel="alternate" type="application/json" href="/tools/{SLUG}/deductions.json" title="Is It Deductible? dataset"/>' + seo.script(ld))
    nl = checklist_box()
    body = (hero + main + nl + info + sheet + data_tag +
            f'<script src="/resources/deductible.js?v={V("deductible.js")}" defer></script>' +
            cta("Not sure what you can write off?", "We can go through your expenses with you and set up your books so write-offs are tracked all year. Book a 30-minute consultation when it suits you."))
    html = f'{B.head(title, desc, URL, OG, extra)}\n<body class="dd-page">{B.nav("res")}\n{body}\n{B.FOOT}</body></html>'
    ids = re.findall(r'\sid="([^"]+)"', html)
    dup = {x for x in ids if ids.count(x) > 1}
    assert not dup, f"duplicate ids on the page: {sorted(dup)}"
    low = re.sub(r"<[^>]+>", " ", html).lower()
    assert not re.search(r"\bfree\b", low) and "mfasite" not in html.lower() and "cpa firm" not in low, "banned wording on the page"
    write_json()
    return write(f"tools/{SLUG}", html)


if __name__ == "__main__":
    print(build())
