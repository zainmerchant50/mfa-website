#!/usr/bin/env python3
"""Shared SEO and AI-discovery layer for mfa-advisory.com (Site session, branch draft/seo-ai).

One place for everything that tells search engines, AI assistants and shopping/research agents who MFA is:

  * schema.org JSON-LD building blocks (Organization/AccountingService, WebSite, Person, WebPage, BreadcrumbList,
    Service/Offer with the public prices, Product for the shop) used by every page builder;
  * the files at the site root that machines read: sitemap.xml, robots.txt, llms.txt, llms-full.txt, catalog.json.

Rules this module enforces (they come from the MFA project rules and from Google's structured-data policies):
  * only facts that are already on the site: no reviews, ratings, awards, founding years or credentials that aren't published;
  * public prices only: LLC formation $150 / $249 / $649 + state fee, add-ons, bookkeeping from $199/month,
    quarterly estimate service $199/year, everything else "quoted up front";
  * no street address anywhere (Princeton, New Jersey only); never "CPA firm", never "certified", never the word "free".

Standard library only. Called from build_blog.py (the last step of a build), build_landing.py and the builders in tools/.
"""
import html as _html
import json
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BASE = "https://mfa-advisory.com"
ORG_ID = BASE + "/#organization"
SITE_ID = BASE + "/#website"
PERSON_ID = BASE + "/authors/zain-merchant/#person"
LOGO = BASE + "/apple-touch-icon.png"
NAME = "Merchant Financial Advisory LLC"
SHORT = "Merchant Financial Advisory"
PHONE_DISPLAY = "(347) 205-4468"
PHONE_E164 = "+13472054468"
EMAIL = "info@mfa-advisory.com"
BOOK = BASE + "/book/"
GUMROAD_STORE = "https://mfaadvisory.gumroad.com/"
LINKEDIN_CO = "https://www.linkedin.com/company/mfa-advisory"
LINKEDIN_ZAIN = "https://www.linkedin.com/in/zainmerchant50"
UPWORK = "https://www.upwork.com/freelancers/zainmerchant50"
FIVERR = "https://www.fiverr.com/zainmerchant50"
INSTAGRAM = "https://www.instagram.com/mfa_advisory/"
GBP = "https://maps.google.com/?cid=17671016441974338457"  # Google Business Profile (verified Oct 2026)
FACEBOOK = "https://www.facebook.com/profile.php?id=61596160376520"
YOUTUBE = "https://www.youtube.com/channel/UCLNPu802SdUCkrjLeIqgM_g"
TIKTOK = "https://www.tiktok.com/@mfa.advisory"
PINTEREST = "https://www.pinterest.com/mfaadvisory/"
YELP = "https://www.yelp.com/biz/merchant-financial-advisory-princeton"
# Public social profiles, in the order shown in the site footer. Hub, 2026-10-30.
SOCIAL = [("LinkedIn", LINKEDIN_CO), ("Instagram", INSTAGRAM), ("Facebook", FACEBOOK), ("YouTube", YOUTUBE),
          ("TikTok", TIKTOK), ("Pinterest", PINTEREST), ("Google", GBP), ("Yelp", YELP)]
SAME_AS = [GBP, LINKEDIN_CO, INSTAGRAM, FACEBOOK, YOUTUBE, TIKTOK, PINTEREST, YELP, UPWORK, FIVERR, GUMROAD_STORE]
TOPICS = ["Tax preparation", "Tax planning", "Bookkeeping", "Accrual accounting", "Financial reporting", "QuickBooks Online", "QuickBooks Desktop", "Xero", "Sage", "Wave Accounting", "FreshBooks",
          "Fractional CFO services", "LLC formation", "S corporation elections", "Form 1099 reporting", "IRS filing deadlines",
          "New Jersey taxes", "New York taxes", "Small business accounting"]
ORG_DESC = ("Accounting, bookkeeping, tax preparation and advisory firm in Princeton, New Jersey for small and mid-sized businesses "
            "and individuals in New Jersey, New York City and nationwide, with LLC formation in all 50 states and a shop of "
            "digital tax and bookkeeping tools. Founded by Zain Merchant, ACCA, formerly of PwC.")
HOURS_NOTE = "Replies to inquiries within one business day."
PERSON_DESC = ("Zain Merchant, ACCA, is the founder and principal of Merchant Financial Advisory in Princeton, New Jersey. "
               "Before starting MFA he worked at PwC in New York on audit, SOX and internal-controls engagements.")


# ----------------------------------------------------------------------------------------------- JSON-LD plumbing
def dumps(ld, ascii_only=True):
    """Compact JSON for a <script type=application/ld+json> block ('</' escaped so it can't close the tag)."""
    return json.dumps(ld, ensure_ascii=ascii_only, separators=(",", ":")).replace("</", "<\\/")


def script(ld, ascii_only=True):
    return f'<script type="application/ld+json">{dumps(ld, ascii_only)}</script>'


def plain(t):
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or ""))).strip()


def address():
    # City and state only. MFA publishes no street address (see docs/seo-ai-report.md for the SEO trade-off).
    return {"@type": "PostalAddress", "addressLocality": "Princeton", "addressRegion": "NJ", "addressCountry": "US"}


def area_served():
    # Princeton and Mercer County come first: the home base named on /princeton-nj/ ("Mercer County, including Princeton ...").
    nj = {"@type": "State", "name": "New Jersey"}
    return [{"@type": "City", "name": "Princeton", "containedInPlace": {"@type": "AdministrativeArea", "name": "Mercer County", "containedInPlace": nj}},
            {"@type": "AdministrativeArea", "name": "Mercer County", "containedInPlace": nj},
            nj, {"@type": "State", "name": "New York"},
            {"@type": "City", "name": "New York", "containedInPlace": {"@type": "State", "name": "New York"}},
            {"@type": "Country", "name": "United States"}]


STATE_NAMES = {"CA": "California", "CT": "Connecticut", "MD": "Maryland", "NY": "New York", "OR": "Oregon"}


def states_excluded(codes):
    """schema.org States for Offer.ineligibleRegion (states where MFA doesn't prepare state returns)."""
    return [{"@type": "State", "name": STATE_NAMES[c], "containedInPlace": {"@type": "Country", "name": "United States"}} for c in codes]


def person():
    """Zain Merchant. Only published facts: title, ACCA, firm, profile links (same as /authors/zain-merchant/)."""
    return {"@type": "Person", "@id": PERSON_ID, "name": "Zain Merchant", "honorificSuffix": "ACCA",
            "jobTitle": "Founder & Principal", "url": BASE + "/authors/zain-merchant/",
            "image": LOGO, "sameAs": [LINKEDIN_ZAIN, UPWORK, FIVERR],
            "worksFor": {"@id": ORG_ID},
            # Same facts as the visible bio on /authors/zain-merchant/ (ACCA, founder, formerly PwC New York).
            "description": PERSON_DESC,
            "memberOf": {"@type": "Organization", "name": "ACCA", "url": "https://www.accaglobal.com/"},
            "knowsAbout": ["Tax preparation", "Tax planning", "Accrual accounting", "Bookkeeping", "QuickBooks Online",
                           "Form 1099 reporting", "Financial reporting", "Internal controls", "Audit support"],
            "address": address()}


def website():
    return {"@type": "WebSite", "@id": SITE_ID, "url": BASE + "/", "name": SHORT, "alternateName": "MFA",
            "inLanguage": "en-US", "publisher": {"@id": ORG_ID}}


def org(full=False, areas=None, offers=None):
    """The firm as an AccountingService (a schema.org LocalBusiness subtype). `full` adds the offer catalog with public prices."""
    o = {"@type": "AccountingService", "@id": ORG_ID, "name": NAME, "legalName": NAME, "alternateName": ["MFA", SHORT],
         "url": BASE + "/", "logo": {"@type": "ImageObject", "url": LOGO, "width": 180, "height": 180}, "image": LOGO,
         "email": EMAIL, "telephone": PHONE_E164, "address": address(),
         "areaServed": areas or area_served(), "sameAs": SAME_AS, "founder": {"@id": PERSON_ID}}
    if full:
        o.update({
            "description": ORG_DESC, "knowsAbout": TOPICS, "knowsLanguage": ["en", "hi", "ur"],
            "priceRange": "From $150",
            "foundingDate": "2025-07",
            # Same hours as the Google Business Profile. Change both together.
            "openingHoursSpecification": [
                {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": "09:00", "closes": "18:00"},
                {"@type": "OpeningHoursSpecification", "dayOfWeek": "Saturday", "opens": "10:00", "closes": "13:00"}],
            "currenciesAccepted": "USD",
            "contactPoint": [{"@type": "ContactPoint", "contactType": "customer service", "telephone": PHONE_E164, "email": EMAIL,
                              "availableLanguage": ["English", "Hindi", "Urdu"], "areaServed": "US"}],
            "potentialAction": {"@type": "ReserveAction", "name": "Book a 30-minute consultation",
                                "target": {"@type": "EntryPoint", "urlTemplate": BOOK, "actionPlatform": "https://schema.org/DesktopWebPlatform"}},
            "hasOfferCatalog": {"@type": "OfferCatalog", "name": "MFA services and public prices",
                                "itemListElement": offers if offers is not None else offer_list()}})
    return o


def crumbs(items):
    """items = [(name, url), ...] from Home down to the current page."""
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(items, 1)]}


def webpage(url, name, desc, kind="WebPage", modified=None, image=None, extra=None):
    w = {"@type": kind, "@id": url + "#webpage", "url": url, "name": name, "description": desc, "inLanguage": "en-US",
         "isPartOf": {"@id": SITE_ID}, "about": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID}}
    if modified:
        w["dateModified"] = modified
    if image:
        w["primaryImageOfPage"] = {"@type": "ImageObject", "url": image}
    w.update(extra or {})
    return w


def _defines(x, ident):
    if isinstance(x, dict):
        return (x.get("@id") == ident and len(x) > 1) or any(_defines(v, ident) for v in x.values())
    if isinstance(x, list):
        return any(_defines(v, ident) for v in x)
    return False


def graph(url, name, desc, *nodes, crumb=None, kind="WebPage", full_org=False, areas=None, modified=None, extra=None):
    """A complete @graph for one page: firm, website, the page itself, breadcrumb, plus the page-specific `nodes`.
    The founder (Person) is added unless a page-specific node already defines him, so every @id reference resolves on the page."""
    g = [org(full_org, areas), website(), webpage(url, name, desc, kind, modified, extra=extra)]
    if not _defines(list(nodes), PERSON_ID):
        g.append(person())
    if crumb:
        bc = crumbs(crumb)
        bc["@id"] = url + "#breadcrumb"
        g[2]["breadcrumb"] = {"@id": bc["@id"]}
        g.append(bc)
    g += [n for n in nodes if n]
    return {"@context": "https://schema.org", "@graph": g}


# ----------------------------------------------------------------------------------------------- public prices / services
def _offer(name, price, desc, unit=None, url=None, includes=None):
    o = {"@type": "Offer", "name": name, "priceCurrency": "USD", "description": desc,
         "itemOffered": {"@type": "Service", "name": name, "provider": {"@id": ORG_ID}}}
    if price is not None:
        o["price"] = str(price)
        if unit:
            o["priceSpecification"] = {"@type": "UnitPriceSpecification", "price": str(price), "priceCurrency": "USD",
                                       "unitCode": unit[0], "unitText": unit[1]}
    if url:
        o["url"] = url
        o["itemOffered"]["url"] = url
    return o


def llc_packages():
    import build_llc as L
    out = []
    for p in L.PACKAGES:
        out.append(_offer(f"LLC formation: {p['name']}", p["price"],
                          "Plus the state filing fee at cost, paid once. One-time price; it does not renew. " + plain(p["lead"]),
                          url=BASE + "/llc-formation/#packages"))
    return out


def llc_addons():
    import build_llc as L
    A, M = L.ADDONS, L.MONTHLY
    return [
        _offer("Monthly bookkeeping", M["price"], f"Starting price per month for {M['scope']}. Month to month; larger books are quoted up front.",
               unit=("MON", "month"), url=BASE + "/llc-formation/#monthly"),
        _offer(A["quarterly"]["name"], A["quarterly"]["price"], "Price for the year: four federal and state estimate calculations with due dates.",
               unit=("ANN", "year"), url=BASE + "/services/#tax-planning"),
        _offer(A["f1099"]["name"], A["f1099"]["per"], f"${A['f1099']['per']} per form, ${A['f1099']['min']} minimum.", url=BASE + "/llc-formation/#start"),
        _offer(A["salestax"]["name"], A["salestax"]["price"], "Included in the Complete Launch package.", url=BASE + "/llc-formation/#start"),
        _offer(A["scorp"]["name"], A["scorp"]["price"], "S corporation election (Form 2553). Included in the Complete Launch package.", url=BASE + "/llc-formation/#start"),
    ]


def llc_addon_catalog():
    """Add-ons and monthly bookkeeping as a separate OfferCatalog node (the page's cart sells them)."""
    return [{"@type": "OfferCatalog", "@id": BASE + "/llc-formation/#addons", "name": "LLC formation add-ons and monthly bookkeeping",
             "itemListElement": llc_addons()}]


def quoted_offers():
    q = "Quoted up front before any work starts."
    return [_offer("Tax preparation and filing", None, q + " Individual and business returns, federal and state.", url=BASE + "/services/#tax-preparation"),
            _offer("Bookkeeping cleanup and catch-up", None, q + " Fixed quote after a review of a sample of your accounts.", url=BASE + "/bookkeeping-cleanup/"),
            _offer("Fractional CFO", None, "Monthly retainer, quoted up front.", url=BASE + "/services/#fractional-cfo")]


def offer_list():
    import build_intl
    return llc_packages() + llc_addons() + quoted_offers() + build_intl.offers()


def service_nodes():
    """One Service per entry on /services/, with its public price (or 'quoted up front')."""
    import build_services as S
    out = []
    for sid, name, lead, items, price, _links in S.SERVICES:
        n = plain(name)
        node = {"@type": "Service", "@id": f"{BASE}/services/#{sid}", "name": n, "url": f"{BASE}/services/#{sid}",
                "serviceType": n, "description": plain(lead) + " " + plain(price), "provider": {"@id": ORG_ID},
                "areaServed": area_served(), "termsOfService": BASE + "/terms"}
        if sid == "bookkeeping":
            node["offers"] = [_offer("Monthly bookkeeping", 199, "Starting price per month for one bank account, one card and up to 100 transactions a month.", unit=("MON", "month"))]
        elif sid == "business-advisory":
            node["offers"] = llc_packages()
        else:
            node["offers"] = [_offer(n, None, plain(price))]
        out.append(node)
    return out


def llc_service(url, state=None):
    """LLC formation Service (all 50 states and DC) or its state-specific variant."""
    import build_llc as L
    name = f"LLC formation in {state}" if state else "LLC formation"
    areas = ([{"@type": "State", "name": state}] if state else [{"@type": "State", "name": L.STATES[c]["name"]} for c in L.ORDER])
    return {"@type": "Service", "@id": url + "#service", "name": name, "serviceType": "LLC formation and business setup", "url": url,
            "provider": {"@id": ORG_ID}, "areaServed": areas,
            "description": "State filing, EIN and operating agreement template from $150 plus the state fee, paid once; tax classification review, state tax registration and QuickBooks setup in Business Setup.",
            "offers": llc_packages()}


# ----------------------------------------------------------------------------------------------- shop (Gumroad) products
def buy_link(p):
    """Where Buy sends the visitor: the Etsy listing when there is one (Zain 2026-10-22: Etsy's checkout is better),
    otherwise Gumroad. Returns (url, "etsy"|"gumroad")."""
    e = p.get("etsy") or {}
    if e.get("allowed") and e.get("url"):
        return e["url"], "etsy"  # Etsy-only products (Gumroad not created yet) also land here
    return p["gumroad"]["url"], "gumroad"


def live_products():
    cat = json.loads((ROOT / "catalog" / "products.json").read_text(encoding="utf-8"))
    groups = {g["id"]: g["name"] for g in cat["groups"]}
    out = []
    for p in cat["products"]:
        if p["status"] != "live" or not (p["gumroad"].get("url") or (p.get("etsy") or {}).get("url")):
            continue
        s = p["shop"]
        url, via = buy_link(p)
        out.append({"slug": p["slug"], "name": p["name"], "price": p["gumroad"]["price"], "url": url, "via": via,
                    "gumroad_url": p["gumroad"].get("url"),
                    "blurb": s["blurb"], "format": s["format"], "group": groups.get(s["group"], s["group"]),
                    "related": s.get("related")})
    return out


def product_node(p):
    seller = {"@id": ORG_ID}
    return {"@type": "Product", "@id": p["url"] + "#product", "name": p["name"], "description": p["blurb"], "sku": p["slug"],
            "url": p["url"], "image": f"{BASE}/shop/img/{p['slug']}.webp", "category": p["group"],
            "brand": {"@type": "Brand", "name": SHORT},
            "additionalProperty": [{"@type": "PropertyValue", "name": "Format", "value": p["format"]},
                                   {"@type": "PropertyValue", "name": "Delivery", "value": "Instant download after checkout"}],
            "offers": {"@type": "Offer", "price": p["price"], "priceCurrency": "USD", "availability": "https://schema.org/InStock",
                       "url": p["url"], "seller": seller, "itemCondition": "https://schema.org/NewCondition",
                       "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": "US",
                                                   "returnPolicyCategory": "https://schema.org/MerchantReturnNotPermitted"},
                       # Digital download: no physical shipping; delivered by email/download right after checkout.
                       "shippingDetails": {"@type": "OfferShippingDetails",
                                           "shippingRate": {"@type": "MonetaryAmount", "value": 0, "currency": "USD"},
                                           "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "US"},
                                           "deliveryTime": {"@type": "ShippingDeliveryTime",
                                                            "handlingTime": {"@type": "QuantitativeValue", "minValue": 0, "maxValue": 0, "unitCode": "DAY"},
                                                            "transitTime": {"@type": "QuantitativeValue", "minValue": 0, "maxValue": 0, "unitCode": "DAY"}}}}}


# ----------------------------------------------------------------------------------------------- related links (internal linking)
# Tool slug -> (services anchor ids, shop product slugs, blog slugs). Rendered as a small "Related" strip on each tool page.
RELATED = {
    "do-i-need-to-send-a-1099": (["tax-preparation"], ["1099-kit"], ["form-1099-preparation-guide-2026"]),
    "1099-contractor-tracker": (["tax-preparation"], ["1099-kit"], ["form-1099-preparation-guide-2026"]),
    "w-9-request-email-template": (["tax-preparation"], ["1099-kit"], ["form-1099-preparation-guide-2026"]),
    "1099-tax-calculator": (["tax-planning"], ["1099-self-employed-tax-calculator-2026"], ["year-end-tax-planning-2026-key-dates"]),
    "quarterly-estimated-tax-calculator": (["tax-planning"], ["1099-self-employed-tax-calculator-2026"], ["2027-tax-calendar"]),
    "s-corp-tax-savings-calculator": (["tax-planning"], ["s-corp-vs-llc-savings-calculator"], ["form-1120s-s-corp-guide"]),
    "paycheck-tax-calculator": (["tax-preparation"], ["salary-paycheck-tax-calculator-2026"], ["year-end-tax-planning-2026-key-dates"]),
    "home-office-deduction-calculator": (["tax-preparation"], ["small-business-year-end-tax-checklist"], ["year-end-tax-planning-2026-key-dates"]),
    "mileage-deduction-calculator": (["tax-preparation"], ["small-business-year-end-tax-checklist"], ["year-end-tax-planning-2026-key-dates"]),
    "break-even-calculator": (["fractional-cfo", "financial-reporting"], [], []),
    "profit-margin-calculator": (["fractional-cfo", "financial-reporting"], [], []),
    "tax-deadlines-2027": (["tax-preparation"], ["small-business-year-end-tax-checklist"], ["2027-tax-calendar"]),
    "is-it-deductible": (["tax-preparation", "tax-planning"], ["small-business-year-end-tax-checklist"], ["section-179-bonus-depreciation-2026", "year-end-tax-planning-2026-key-dates"]),
}


# Tool slug -> audience pages to link from the tool's "Related on MFA" strip (internal links, 2026-10-25).
_ART, _INTL = ("/artists/", "Taxes for artists & creatives"), ("/international-students/", "International student tax filing")
RELATED_PAGES = {
    "is-it-deductible": [_ART], "home-office-deduction-calculator": [_ART], "mileage-deduction-calculator": [_ART],
    "1099-tax-calculator": [_ART], "quarterly-estimated-tax-calculator": [_ART], "s-corp-tax-savings-calculator": [_ART],
    "paycheck-tax-calculator": [_INTL], "tax-deadlines-2027": [_INTL, _ART],
}


def related_html(slug):
    if slug not in RELATED:
        return ""
    import build_services as S
    svc, prods, posts = RELATED[slug]
    names = {sid: plain(n) for sid, n, *_ in S.SERVICES}
    pn = {p["slug"]: p["name"] for p in live_products()}
    titles = {}
    ovr = json.loads((ROOT / "tools" / "seo_overrides.json").read_text(encoding="utf-8"))
    for f in (ROOT / "content" / "posts").glob("*.html"):
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->", f.read_text(encoding="utf-8"), re.S)
        if m:
            meta = json.loads(m.group(1))
            titles[meta["slug"]] = re.sub(r"\s*\|\s*MFA( Insights)?$", "", ovr.get(meta["slug"], {}).get("title", meta["title"]))
    links = [(f"/services/#{s}", names[s]) for s in svc if s in names]
    links += RELATED_PAGES.get(slug, [])
    links += [("/shop/", pn[p]) for p in prods if p in pn]
    links += [(f"/blog/{b}/", titles[b]) for b in posts if b in titles]
    if not links:
        return ""
    li = "".join(f'<a href="{u}">{_html.escape(t)}</a>' for u, t in links)
    return (f'<nav class="relnav" aria-label="Related on MFA"><div class="wrap"><span>Related on MFA</span>{li}</div></nav>')


# ----------------------------------------------------------------------------------------------- last-modified dates
def _git(*args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def lastmod(path):
    """Date a file last changed: its last commit date, or today if it has uncommitted changes (or no git history)."""
    rel = str(Path(path).resolve().relative_to(ROOT))
    if _git("status", "--porcelain", "--", rel):
        return date.today().isoformat()
    d = _git("log", "-1", "--format=%cs", "--", rel)
    return d or date.today().isoformat()


# ----------------------------------------------------------------------------------------------- page discovery / sitemap
def discover_pages():
    """Every indexable page under site/: (canonical url, lastmod, path). Pages marked noindex or without a canonical are skipped."""
    out = []
    for p in sorted(SITE.rglob("*.html")):
        s = p.read_text(encoding="utf-8")
        if re.search(r'<meta[^>]+name="robots"[^>]+noindex', s) or p.name == "404.html":
            continue
        m = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        if not m or not m.group(1).startswith(BASE):
            continue
        out.append((m.group(1), p))
    return out


def build_sitemap(posts):
    pm = {f"{BASE}/blog/{p['slug']}/": p.get("updated", p["date"]) for p in posts}
    rows = []
    for url, p in discover_pages():
        rows.append((url, pm.get(url) or lastmod(p)))
    if posts:   # the blog index and author page change when a post is published
        pm_latest = max(p.get("updated", p["date"]) for p in posts)
        rows = [(u, pm_latest if u in (BASE + "/blog/", BASE + "/authors/zain-merchant/") else d) for u, d in rows]

    def key(r):
        path = r[0][len(BASE):]
        top = ["/", "/services/", "/llc-formation/", "/shop/", "/resources/", "/blog/"]
        return (top.index(path) if path in top else len(top), path.count("/"), path)
    rows.sort(key=key)
    body = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in rows)
    (SITE / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>', encoding="utf-8")
    return [u for u, _ in rows]


# ----------------------------------------------------------------------------------------------- robots.txt
def build_robots():
    """Allow every search and assistant crawler. Sources for the user-agent names are in docs/seo-ai-report.md."""
    groups = [
        ("Search engines (Google, Bing and Apple power most AI answers: ChatGPT search and Copilot use Bing's index, AI Overviews and AI Mode use Google's)",
         ["Googlebot", "Bingbot", "Applebot"]),
        ("AI search crawlers: pages are indexed so assistants can cite and link to MFA",
         ["OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "DuckAssistBot"]),
        ("Fetches made on a person's behalf when they ask an assistant about a page (some of these ignore robots.txt by design)",
         ["ChatGPT-User", "Claude-User", "Perplexity-User"]),
        ("Training-use controls. They do not affect search visibility; change to Disallow to opt out of model training",
         ["GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended"]),
    ]
    out = ["# mfa-advisory.com robots.txt (generated by tools/seo.py)", "# Everything public is open to all crawlers. Machine-readable summaries:",
           f"#   {BASE}/llms.txt   {BASE}/llms-full.txt   {BASE}/catalog.json", "", "User-agent: *", "Allow: /", "Disallow: /cdn-cgi/", ""]
    for note, bots in groups:
        out.append(f"# {note}")
        for b in bots:
            out += [f"User-agent: {b}", "Allow: /", "Disallow: /cdn-cgi/", ""]
    out.append(f"Sitemap: {BASE}/sitemap.xml")
    (SITE / "robots.txt").write_text("\n".join(out) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------------------------- llms.txt / llms-full.txt
def _tools():
    """(title, url, description) for every built tool page."""
    rows = []
    for p in sorted((SITE / "tools").glob("*/index.html")):
        s = p.read_text(encoding="utf-8")
        t = _html.unescape(re.search(r"<title>(.*?)</title>", s, re.S).group(1))
        d = _html.unescape(re.search(r'<meta name="description" content="(.*?)"', s, re.S).group(1))
        rows.append((re.sub(r"\s*\|\s*MFA$", "", t), f"{BASE}/tools/{p.parent.name}/", d))
    return rows


def _deductible(full_text):
    """Every Is It Deductible? entry as plain text (tools/build_deductible.py owns the wording)."""
    import build_deductible as D
    return D.llms_lines(full_text)


def _pricing_lines():
    import build_llc as L
    lines = [f"- LLC formation, {p['name']}: ${p['price']} plus the state filing fee (paid once, does not renew). {plain(p['lead'])}" for p in L.PACKAGES]
    A, M = L.ADDONS, L.MONTHLY
    lines += [f"- Monthly bookkeeping: from ${M['price']}/month for {M['scope']}. Month to month; larger books are quoted up front. Software: QuickBooks (Online and Desktop), Xero, Sage, Wave and FreshBooks.",
              f"- Quarterly estimated tax service: ${A['quarterly']['price']} for the year (four federal and state estimate calculations with due dates).",
              f"- 1099 preparation and e-filing: ${A['f1099']['per']} per form, ${A['f1099']['min']} minimum.",
              f"- Sales tax registration: ${A['salestax']['price']} (included in Complete Launch). S corporation election (Form 2553): ${A['scorp']['price']} (included in Complete Launch).",
              "- Bookkeeping cleanup and catch-up: fixed quote after a review of a sample of your accounts (https://mfa-advisory.com/bookkeeping-cleanup/).",
              "- International students and H-1B workers (https://mfa-advisory.com/international-students/): Form 8843 only (no US income) $25; "
              "student package (Form 1040-NR + Form 8843 + tax treaty check) $99 federal, $129 with one state return; Social Security and Medicare "
              "refund claim (Forms 843 + 8316) $49; wrong-form fix $129; first-year H-1B dual-status return $249; H-1B and other US tax residents file Form 1040 at standard tax return pricing. "
              "State returns for every state except Connecticut, Maryland and Oregon.",
              "- Artists and creatives (https://mfa-advisory.com/artists/): self-employed artist tax returns (Form 1040 with Schedule C) quoted up front; "
              "bookkeeping, LLC formation and quarterly estimates at the prices above. State returns for every state except Connecticut, Maryland and Oregon.",
              "- Tax preparation, tax planning, financial reporting, fractional CFO, audit support and technical accounting: quoted up front before any work starts."]
    import build_offers as O
    lines += [f"- {v['name']}: ${v['price']}" + (" per form/person" if 'min' in v else "") + f", pay online at {BASE}{v['page']}" for v in O.SERVICES.values()]
    return lines


def build_llms(posts):
    products = live_products()
    L = [
        "# Merchant Financial Advisory LLC (MFA)",
        "",
        "> Accounting, bookkeeping, tax preparation and advisory firm in Princeton, New Jersey. Serves small and mid-sized businesses and "
        "individuals in New Jersey, New York City and nationwide, forms LLCs in all 50 states, and sells digital tax and bookkeeping tools. "
        "Founded by Zain Merchant, ACCA, formerly of PwC.",
        "",
        f"Contact: {EMAIL}, {PHONE_DISPLAY}. Location: Princeton, New Jersey (no public street address; work is done remotely by video, phone and secure upload). "
        "Languages: English, Hindi, Urdu. Book a 30-minute consultation: " + BOOK + ". " + HOURS_NOTE,
        "",
        "Not a law firm. MFA does not perform audits or issue audit, review or compilation reports. Content on the site is general information, not tax, legal or financial advice.",
        "",
        "## Services and public prices",
        f"- [Services]({BASE}/services/): tax preparation, tax planning, bookkeeping (QuickBooks, Xero, Sage, Wave and FreshBooks), financial reporting, fractional CFO, audit support, technical accounting, business advisory",
        f"- [LLC formation in all 50 states]({BASE}/llc-formation/): $150 / $249 / $649 plus the state fee, paid once; state-by-state fees and rules",
        f"- [Bookkeeping cleanup and catch-up]({BASE}/bookkeeping-cleanup/): fixed quote request",
        f"- [International students and H-1B workers]({BASE}/international-students/): international student tax filing; Form 8843 $25, Form 1040-NR student package $99 ($129 with one state), Social Security and Medicare (FICA) refund claim $49, wrong-form fix (1040 filed instead of 1040-NR) $129, first-year H-1B dual-status return $249, tax treaty check; other H-1B returns at standard Form 1040 pricing",
        f"- [Year-end tax planning session]({BASE}/year-end-tax-planning/): 60 minutes before Dec 31 plus a written action list, $99, pay online",
        f"- [1099-NEC filing]({BASE}/1099-filing/): W-9s, IRS e-filing and contractor copies; $20 per form early-bird through Dec 15, 2026, then $25 (3-form minimum)",
        f"- [S corp election for 2027]({BASE}/s-corp-election/): savings check, Form 2553, reasonable salary and payroll plan, $299",
        f"- [Quarterly estimated taxes]({BASE}/quarterly-estimated-taxes/): federal and state payments worked out, $199 for 2027 or $59 for the next payment",
        f"- [LLC annual report filing]({BASE}/llc-annual-report/): $39 plus the state fee at cost; annual report fees and due dates for all 50 states and DC",
        f"- [Late 2025 tax return filing]({BASE}/late-tax-return/): missed the October 15 deadline or never filed; Form 1040 $249, with Schedule C $399, add a state $49",
        f"- [Taxes for artists and creatives]({BASE}/artists/): Schedule C tax returns (quoted up front), bookkeeping for artists from $199/month, LLC formation from $150 plus state fee, quarterly estimates $199/year; tax deductions for artists, Etsy 1099-K, self-employment tax, do artists need an LLC",
        f"- [Machine-readable catalog]({BASE}/catalog.json): all services, prices, tools and products as schema.org JSON",
        "",
        "## Local pages",
        f"- [Princeton, NJ]({BASE}/princeton-nj/): bookkeeping, accounting and tax preparation for Princeton and Mercer County",
        f"- [Bookkeeping in Princeton, NJ]({BASE}/bookkeeping/princeton-nj/): monthly bookkeeping from $199/month in QuickBooks, Xero, Sage, Wave and FreshBooks, flat monthly or hourly, cleanup quoted up front",
        f"- [Union City, NJ]({BASE}/union-city-nj/): bookkeeping, accounting and tax preparation for Union City and Hudson County",
        f"- [New York, NY]({BASE}/new-york-ny/): bookkeeping, accounting and tax preparation for the five boroughs",
        "",
        "## Tools (online calculators and checkers)",
        f"- [Resources hub]({BASE}/resources/): all tools, calendars, templates and guides",
    ] + [f"- [{t}]({u}): {d}" for t, u, d in _tools()] + [
        "",
        "## Is It Deductible? (2026 business expense deductions, one line per expense)",
        f"- [Is it tax deductible? 2026 business write-off finder]({BASE}/tools/is-it-deductible/): search {len(_deductible(False))} common business expenses; verdict, rule, limits, records to keep and the IRS source for each",
        f"- [Dataset (JSON)]({BASE}/tools/is-it-deductible/deductions.json): the same entries as structured data. Cite with a link to the page.",
    ] + _deductible(False) + [
        "",
        "## Shop (digital downloads, checkout by Gumroad)",
        f"- [MFA shop]({BASE}/shop/): spreadsheets, checklists and kits, instant download, all sales final",
    ] + [f"- [{p['name']}]({p['url']}): ${p['price']}. {p['blurb']}" for p in products] + [
        "",
        "## About",
        f"- [Zain Merchant, ACCA]({BASE}/authors/zain-merchant/): founder and principal, author of MFA Insights",
        f"- [Disclaimer]({BASE}/disclaimer), [Privacy]({BASE}/privacy), [Terms]({BASE}/terms)",
        "",
        "## MFA Insights (articles on IRS, New Jersey and New York tax rules and deadlines)",
        f"- [MFA Insights blog]({BASE}/blog/): all articles; [newsletter]({BASE}/newsletter/); [RSS feed]({BASE}/blog/feed.xml)",
    ] + [f"- [{p['title']}]({BASE}/blog/{p['slug']}/): {p['description']}" for p in posts] + [
        "",
        "## Optional",
        f"- [Full details for assistants]({BASE}/llms-full.txt): services, prices, LLC packages and state fees, products, FAQs",
        f"- [Sitemap]({BASE}/sitemap.xml)",
    ]
    (SITE / "llms.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


def _faq_home():
    s = (SITE / "index.html").read_text(encoding="utf-8")
    return home_faq(s)


def home_faq(s):
    out = []
    for m in re.finditer(r'<div class="faq-i">\s*<button class="faq-q"[^>]*>(.*?)<span class="faq-pm".*?<div class="faq-a">\s*<p>(.*?)</p>', s, re.S):
        out.append((plain(m.group(1)), plain(m.group(2))))
    return out


def build_llms_full(posts):
    import build_llc as LC
    import build_services as S
    products = live_products()
    today = date.today().strftime("%B %-d, %Y")
    o = [f"# Merchant Financial Advisory LLC (MFA): full details for AI assistants and agents", "",
         f"Generated {today} from the live site sources. Prices shown here are the public prices on mfa-advisory.com; anything marked "
         "\"quoted\" is priced up front after a conversation. Prefer the linked pages for the latest wording.", "",
         "## Who MFA is", "",
         "- Name: Merchant Financial Advisory LLC (MFA), a New Jersey accounting, bookkeeping, tax preparation and advisory firm.",
         "- Founder and principal: Zain Merchant, ACCA, formerly of PwC (Big Four) in New York. Profile: " + BASE + "/authors/zain-merchant/",
         "- Location: Princeton, New Jersey. No public street address; clients are served remotely by video call, phone and secure document upload.",
         "- Serves: small and mid-sized businesses, freelancers and households in New Jersey, New York City and across the United States. LLC formation in all 50 states and DC.",
         f"- Contact: {EMAIL}, {PHONE_DISPLAY}. Book a 30-minute consultation: {BOOK}. {HOURS_NOTE}",
         "- Languages: English, Hindi, Urdu.",
         "- Engagements that require a licensed CPA are handled together with partner CPAs. MFA is not a law firm and does not perform audits or issue audit, review or compilation reports.",
         "", "## Services (" + BASE + "/services/)", ""]
    for sid, name, lead, items, price, _l in S.SERVICES:
        o.append(f"### {plain(name)}")
        o.append(f"{plain(lead)} Pricing: {plain(price)}")
        o += [f"- {plain(i)}" for i in items]
        o.append(f"Page: {BASE}/services/#{sid}")
        o.append("")
    o += ["## Public prices", ""] + _pricing_lines() + [""]
    o += ["## LLC formation packages (" + BASE + "/llc-formation/)", ""]
    for p in LC.PACKAGES:
        o.append(f"### {p['name']}: ${p['price']} plus state fee")
        o += [f"- {plain(i)}" for i in p["items"]]
        o.append("")
    o += ["## LLC state filing fees (checked " + LC.CHECKED + "; each state page lists its sources)", "",
          "| State | State filing fee | Page |", "|---|---|---|"]
    for c in LC.ORDER:
        s = LC.STATES[c]
        fee = LC.v(s, "filing_fee")
        o.append(f"| {s['name']} | {('$' + format(fee, ',')) if isinstance(fee, (int, float)) else 'confirmed at quote'} | {BASE}/llc-formation/{c.lower()}/ |")
    o += ["", "## Online tools", ""] + [f"- {t}: {d} {u}" for t, u, d in _tools()] + ["", "## Shop products (checkout by Gumroad; instant download; all sales final)", ""]
    for g in dict.fromkeys(p["group"] for p in products):
        o.append(f"### {g}")
        o += [f"- {p['name']}: ${p['price']}, {p['format']}. {p['blurb']} Buy: {p['url']}" for p in products if p["group"] == g]
        o.append("")
    o += ["## Is It Deductible? 2026 business expense deductions (" + BASE + "/tools/is-it-deductible/)", "",
          "Educational information only, not tax, legal or accounting advice. Written for sole proprietors and single-member LLCs filing Schedule C. "
          "Dataset: " + BASE + "/tools/is-it-deductible/deductions.json (cite with a link to the page).", ""] + _deductible(True)
    o += ["## Frequently asked questions", ""]
    for q, a in _faq_home():
        o += [f"**{q}**", a, ""]
    o += ["## Articles (MFA Insights)", ""] + [f"- {p['title']} ({p['date']}): {p['description']} {BASE}/blog/{p['slug']}/" for p in posts]
    o += ["", "## Sources and disclaimers", "",
          "Every article and tool lists its official IRS and state sources and the date its facts were checked. Content is general information, not tax, legal or financial advice."]
    (SITE / "llms-full.txt").write_text("\n".join(o) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------------------------- catalog.json (agent-readable)
def audience_services():
    """Service nodes for the audience pages (/international-students/, /artists/), same as each page's own JSON-LD."""
    import build_intl
    import build_artists
    return [build_intl.service_node(), build_artists.service_node()]


def build_catalog(posts):
    """schema.org DataFeed at /catalog.json: the firm, every service with its public price, tools and shop products."""
    tools = [{"@type": "WebApplication", "name": t, "url": u, "description": d, "applicationCategory": "BusinessApplication",
              "operatingSystem": "Any",
              "provider": {"@id": ORG_ID}} for t, u, d in _tools()]
    feed = {"@context": "https://schema.org", "@type": "DataFeed", "@id": BASE + "/catalog.json",
            "name": "Merchant Financial Advisory: services, public prices, tools and products",
            "description": "Machine-readable list of what MFA offers and what is publicly priced. Services marked 'quoted up front' have no public price.",
            "url": BASE + "/catalog.json", "dateModified": date.today().isoformat(), "inLanguage": "en-US",
            "provider": org(True), "creator": person(),
            "dataFeedElement": [{"@type": "DataFeedItem", "dateModified": date.today().isoformat(), "item": i}
                                for i in service_nodes() + [llc_service(BASE + "/llc-formation/")] + audience_services()
                                + [product_node(p) for p in live_products()] + tools]}
    (SITE / "catalog.json").write_text(json.dumps(feed, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------------------------- home page (hand-edited file): keep its JSON-LD in sync
HOME_MARK = ("<!--seo:jsonld-->", "<!--/seo:jsonld-->")


def patch_home():
    """Rewrites the structured data in site/index.html between markers (first run wraps the existing block). Body copy is untouched."""
    path = SITE / "index.html"
    s = path.read_text(encoding="utf-8")
    faq = home_faq(s)
    url = BASE + "/"
    ld = graph(url, "Merchant Financial Advisory | Accounting & Tax, Princeton NJ",
               plain(re.search(r'<meta name="description" content="(.*?)"', s, re.S).group(1)),
               {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
                   {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]} if faq else None,
               kind="WebPage", full_org=True,
               extra={"mainEntity": {"@id": ORG_ID}, "primaryImageOfPage": {"@type": "ImageObject", "url": LOGO}})
    block = HOME_MARK[0] + script(ld) + HOME_MARK[1]
    if HOME_MARK[0] in s:
        s = re.sub(re.escape(HOME_MARK[0]) + r".*?" + re.escape(HOME_MARK[1]), lambda m: block, s, count=1, flags=re.S)
    else:
        s, n = re.subn(r'<script type="application/ld\+json">.*?</script>', lambda m: block, s, count=1, flags=re.S)
        assert n == 1, "home JSON-LD block not found"
    path.write_text(s, encoding="utf-8")



# ----------------------------------------------------------------------------------------------- page decorations
# One place for two things every builder would otherwise have to repeat (run from build_all, so every build_blog.py run
# re-applies them; they sit between markers, so re-running is idempotent and other builders' output is never edited
# anywhere else):
#   1. <meta name="keywords"> from the page's real topics (Google ignores it; Bing and some assistants read it; harmless).
#   2. A "Guides on this topic" strip right after <main> on service, local and LLC pages, linking each to its best guides
#      (service pages -> top guides; blog posts -> service pages is done in build_blog.py).
# check_seo.py fails if a mapped page loses its strip, so a builder run on its own is caught before a push.
KW_MARK = ("<!--seo:kw-->", "<!--/seo:kw-->")
GUIDES_MARK = ("<!--seo:guides-->", "<!--/seo:guides-->")

PAGE_KEYWORDS = {
    "/": ["accountant Princeton NJ", "bookkeeping services New Jersey", "tax preparation NJ and NYC", "small business accounting",
          "QuickBooks bookkeeping", "LLC formation", "fractional CFO"],
    "/services/": ["small business accounting services", "tax preparation services", "tax planning", "monthly bookkeeping",
                   "financial reporting", "fractional CFO", "audit support", "NJ and NYC accountant"],
    "/llc-formation/": ["LLC formation service", "form an LLC", "LLC cost by state", "EIN and operating agreement",
                        "single-member LLC", "LLC filing fees 2026"],
    "/bookkeeping-cleanup/": ["bookkeeping cleanup", "catch-up bookkeeping", "behind on bookkeeping", "QuickBooks cleanup",
                              "reconcile bank accounts", "fixed quote bookkeeping"],
    "/1099-filing/": ["1099 filing service", "1099-NEC filing", "1099-MISC filing", "W-9 collection", "1099 deadline 2027",
                      "file 1099s for contractors"],
    "/late-tax-return/": ["late tax return", "file 2025 taxes late", "missed October 15 deadline", "unfiled tax return",
                          "late filing penalty", "Form 1040 late filing"],
    "/quarterly-estimated-taxes/": ["quarterly estimated taxes", "estimated tax payments", "1040-ES", "self-employed taxes",
                                    "estimated tax due dates 2026", "safe harbor"],
    "/s-corp-election/": ["S corp election", "Form 2553", "LLC taxed as S corp", "reasonable salary", "S corp deadline 2027"],
    "/year-end-tax-planning/": ["year-end tax planning", "tax planning session", "reduce taxes before December 31",
                                "small business tax deductions", "2026 tax planning"],
    "/llc-annual-report/": ["LLC annual report filing", "annual report deadline", "state annual report fee",
                            "keep LLC in good standing"],
    "/international-students/": ["international student tax filing", "Form 8843", "1040-NR", "F-1 student taxes",
                                 "H-1B tax return", "nonresident alien tax"],
    "/artists/": ["artist taxes", "1099-K for artists", "Schedule C for artists", "art fair sales tax", "creative business deductions"],
    "/princeton-nj/": ["accountant Princeton NJ", "bookkeeping Princeton NJ", "tax preparation Princeton NJ", "Mercer County accountant",
                       "small business accountant Princeton"],
    "/union-city-nj/": ["accountant Union City NJ", "bookkeeping Union City NJ", "tax preparation Union City NJ",
                        "Hudson County accountant", "small business accountant Union City"],
    "/new-york-ny/": ["accountant New York NY", "bookkeeping NYC", "tax preparation New York City", "NYC small business accountant",
                      "New York tax preparer"],
    "/bookkeeping/princeton-nj/": ["bookkeeping Princeton NJ", "monthly bookkeeping", "QuickBooks bookkeeper Princeton",
                                   "small business bookkeeping NJ"],
    "/shop/": ["tax calculator spreadsheet", "bookkeeping checklist", "1099 kit", "small business tax templates",
               "AI prompts for bookkeeping", "tax organizer 2026"],
    "/resources/": ["small business tax calculators", "1099 checker", "tax deadlines 2027", "bookkeeping templates",
                    "LLC fees by state", "tax tools"],
    "/blog/": ["small business tax tips", "tax deadlines 2026", "QuickBooks tips", "accrual accounting", "New Jersey taxes",
               "New York taxes"],
    "/book/": ["book a tax consultation", "accountant consultation", "bookkeeping consultation", "Princeton NJ accountant"],
    "/newsletter/": ["tax newsletter", "tax deadline reminders", "small business tax updates", "QuickBooks tips email"],
    "/authors/zain-merchant/": ["Zain Merchant ACCA", "accountant Princeton NJ", "MFA founder", "tax and accounting articles"],
    "/privacy": ["privacy policy", "Merchant Financial Advisory"],
    "/terms": ["terms of service", "Merchant Financial Advisory"],
    "/disclaimer": ["disclaimer", "not tax advice", "Merchant Financial Advisory"],
    "/tools/1099-contractor-tracker/": ["1099 contractor tracker", "who needs a 1099-NEC", "1099 threshold 2026", "contractor payments log"],
    "/tools/1099-tax-calculator/": ["1099 tax calculator", "self-employment tax calculator", "how much to set aside for taxes 1099",
                                    "1099 taxes NJ NY"],
    "/tools/break-even-calculator/": ["break-even calculator", "break-even point", "fixed and variable costs", "small business pricing"],
    "/tools/do-i-need-to-send-a-1099/": ["do I need to send a 1099", "1099-NEC rules 2026", "1099 threshold", "1099 for LLC"],
    "/tools/home-office-deduction-calculator/": ["home office deduction calculator", "simplified home office deduction",
                                                 "Form 8829", "home office deduction 2026"],
    "/tools/is-it-deductible/": ["is it tax deductible", "small business tax write-offs", "business expense deductions",
                                 "deductible expenses list"],
    "/tools/mileage-deduction-calculator/": ["mileage deduction calculator", "IRS standard mileage rate 2026", "business mileage log",
                                             "car expense deduction"],
    "/tools/paycheck-tax-calculator/": ["paycheck tax calculator", "take-home pay calculator", "FICA withholding",
                                        "NJ paycheck calculator", "NY paycheck calculator"],
    "/tools/profit-margin-calculator/": ["profit margin calculator", "markup calculator", "gross margin", "pricing calculator"],
    "/tools/quarterly-estimated-tax-calculator/": ["quarterly estimated tax calculator", "estimated tax payments 2026",
                                                   "1040-ES calculator", "NJ estimated tax", "NY estimated tax"],
    "/tools/s-corp-tax-savings-calculator/": ["S corp tax savings calculator", "is an S corp worth it", "S corp vs LLC",
                                              "reasonable salary S corp"],
    "/tools/tax-deadlines-2027/": ["2027 tax deadlines", "business tax deadlines by entity", "NJ tax deadlines 2027",
                                   "NY tax deadlines 2027"],
    "/tools/w-9-request-email-template/": ["W-9 request email template", "request a W-9 from a vendor", "W-9 form 2026",
                                           "1099 vendor onboarding"],
}

_LLC_GUIDES = ["which-tax-form-llc-corporation", "schedule-c-guide-single-member-llc", "llc-taxed-as-s-corp-guide"]
PAGE_GUIDES = {
    "/services/": ["2027-tax-calendar", "which-tax-form-llc-corporation", "small-business-tax-write-offs-2026", "form-1099-preparation-guide-2026"],
    "/1099-filing/": ["form-1099-preparation-guide-2026", "1099-income-filing-threshold", "hiring-overseas-contractors-taxes-w8ben"],
    "/late-tax-return/": ["filing-taxes-late-2025-return", "october-15-2026-tax-extension-deadline"],
    "/llc-formation/": _LLC_GUIDES,
    "/quarterly-estimated-taxes/": ["2027-tax-calendar", "1099-income-filing-threshold", "social-security-wage-base-2027-self-employed"],
    "/s-corp-election/": ["llc-taxed-as-s-corp-guide", "form-1120s-s-corp-guide", "social-security-wage-base-2027-self-employed"],
    "/year-end-tax-planning/": ["year-end-tax-planning-2026-key-dates", "section-179-bonus-depreciation-2026", "small-business-tax-write-offs-2026"],
    "/llc-annual-report/": ["which-tax-form-llc-corporation", "form-1065-guide-llc"],
    "/bookkeeping-cleanup/": ["small-business-tax-write-offs-2026", "schedule-c-guide-single-member-llc", "ai-in-accounting-and-tax-2026"],
    "/international-students/": ["filing-taxes-late-2025-return", "2027-tax-calendar"],
    "/artists/": ["small-business-tax-write-offs-2026", "schedule-c-guide-single-member-llc", "1099-income-filing-threshold"],
    "/princeton-nj/": ["nj-property-tax-relief-anchor-stay-nj-2026", "nj-sales-tax-st50-filing-guide", "salt-cap-2026-nj-ny-pte-tax", "2027-tax-calendar"],
    "/union-city-nj/": ["nj-property-tax-relief-anchor-stay-nj-2026", "nj-sales-tax-st50-filing-guide", "salt-cap-2026-nj-ny-pte-tax", "2027-tax-calendar"],
    "/new-york-ny/": ["salt-cap-2026-nj-ny-pte-tax", "2027-tax-calendar", "which-tax-form-llc-corporation"],
}


def _state_name(s):
    m = re.search(r"<h1[^>]*>How much does an LLC cost in ([^<?]+)\?</h1>", s)
    return _html.unescape(m.group(1)).strip() if m else None


def page_keywords(path, s):
    if path in PAGE_KEYWORDS:
        return PAGE_KEYWORDS[path]
    if re.fullmatch(r"/llc-formation/[a-z]{2}/", path):
        st = _state_name(s)
        if st:
            return [f"{st} LLC cost", f"form an LLC in {st}", f"{st} LLC filing fee", f"{st} LLC requirements", "LLC formation service"]
    return None


def page_guides(path):
    if path in PAGE_GUIDES:
        return PAGE_GUIDES[path]
    if re.fullmatch(r"/llc-formation/[a-z]{2}/", path):
        return _LLC_GUIDES
    return None


def _guide_titles(posts):
    ovr = json.loads((ROOT / "tools" / "seo_overrides.json").read_text(encoding="utf-8"))
    return {p["slug"]: re.sub(r"\s*\|\s*MFA( Insights)?$", "", ovr.get(p["slug"], {}).get("title") or p.get("seoTitle") or p["title"])
            for p in posts}


GUIDES_CSS = ("<style>.mfa-guides{border-top:1px solid rgba(21,21,21,.1);background:#F5F4EF;padding:22px 0}"
              ".mfa-guides .mg-in{max-width:1120px;margin:0 auto;padding:0 20px;display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px}"
              ".mfa-guides .mg-k{font:700 10px/1.4 Inter,system-ui,sans-serif;letter-spacing:.22em;text-transform:uppercase;color:#B08D3F;margin-right:6px}"
              ".mfa-guides a{font:500 .86rem/1.3 Inter,system-ui,sans-serif;padding:7px 13px;border:1px solid #B08D3F;border-radius:999px;"
              "background:#FDFDFC;color:#10233F;text-decoration:none;transition:background .3s,color .3s,transform .3s}"
              ".mfa-guides a:hover,.mfa-guides a:focus-visible{background:#B08D3F;color:#fff;transform:translateY(-1px)}"
              "@media (prefers-reduced-motion:reduce){.mfa-guides a{transition:none}.mfa-guides a:hover{transform:none}}</style>")


def guides_html(slugs, titles):
    links = [(f"/blog/{g}/", titles[g]) for g in slugs if g in titles]
    if not links:
        return ""
    li = "".join(f'<a href="{u}">{_html.escape(t)}</a>' for u, t in links)
    return (f'{GUIDES_CSS}<nav class="mfa-guides" aria-label="Guides on this topic"><div class="mg-in">'
            f'<span class="mg-k">Guides on this topic</span>{li}</div></nav>')


def _set_block(s, mark, block, anchor_re, before=True):
    """Replace the marked block, or insert it at the anchor (before/after the last match). Returns the new text."""
    full = mark[0] + block + mark[1] if block else ""
    if mark[0] in s:
        return re.sub(re.escape(mark[0]) + r".*?" + re.escape(mark[1]), lambda m: full, s, count=1, flags=re.S)
    if not block:
        return s
    ms = list(re.finditer(anchor_re, s, re.S))
    if not ms:
        return s
    m = ms[-1]
    i = m.start() if before else m.end()
    return s[:i] + full + s[i:]


def decorate_pages(posts):
    titles = _guide_titles(posts)
    n = 0
    for url, f in discover_pages():
        path = url[len(BASE):]
        if path.startswith("/blog/") and path != "/blog/":
            continue   # posts get keywords and tags from build_blog.py
        s = f.read_text(encoding="utf-8")
        t = s
        kws = page_keywords(path, s)
        has_own = re.search(r'<meta name="keywords"', re.sub(re.escape(KW_MARK[0]) + r".*?" + re.escape(KW_MARK[1]), "", s, flags=re.S))
        if kws and not has_own:
            t = _set_block(t, KW_MARK, f'<meta name="keywords" content="{_html.escape(", ".join(kws))}"/>',
                           r'<meta name="description" content="[^"]*"\s*/?>', before=False)
        g = page_guides(path)
        if g:
            t = _set_block(t, GUIDES_MARK, guides_html(g, titles), r"</main>", before=False)
        if t != s:
            f.write_text(t, encoding="utf-8")
            n += 1
    return n


# ----------------------------------------------------------------------------------------------- everything
def build_all(posts):
    patch_home()
    decorate_pages(posts)
    build_robots()
    build_llms(posts)
    build_llms_full(posts)
    build_catalog(posts)
    return build_sitemap(posts)   # last: it reads the finished pages
