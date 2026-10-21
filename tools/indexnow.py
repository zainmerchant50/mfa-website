#!/usr/bin/env python3
"""Tells Bing (and every other IndexNow search engine) which MFA URLs are new or changed.

ChatGPT search, Microsoft Copilot and Bing all draw on Bing's index, so a fast Bing crawl is how new pages reach them sooner.
IndexNow is a public protocol (https://www.indexnow.org/documentation): the key file below must be live at
https://mfa-advisory.com/<key>.txt first (it ships in site/ and goes live when main is deployed).

    python3 tools/indexnow.py            # dry run: prints the URLs it would send
    python3 tools/indexnow.py --send     # sends every URL in sitemap.xml
    python3 tools/indexnow.py --send https://mfa-advisory.com/shop/ https://mfa-advisory.com/services/   # just these

Run it after a deploy that adds or changes pages. Standard library only. Bing Webmaster Tools verification is still needed
to see indexing and the AI Performance report, but IndexNow itself needs no account.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
HOST = "mfa-advisory.com"
KEYS = [p for p in SITE.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem)]


def main():
    if len(KEYS) != 1:
        sys.exit("expected exactly one IndexNow key file (32 hex characters + .txt) in site/")
    key = KEYS[0].stem
    assert KEYS[0].read_text().strip() == key
    args = [a for a in sys.argv[1:] if a != "--send"]
    urls = args or re.findall(r"<loc>(.*?)</loc>", (SITE / "sitemap.xml").read_text(encoding="utf-8"))
    body = {"host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt", "urlList": urls}
    print(f"{len(urls)} URLs, key file https://{HOST}/{key}.txt")
    if "--send" not in sys.argv:
        print("\n".join(urls[:5]), "...", sep="\n")
        print("dry run: add --send to submit")
        return
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("IndexNow response:", r.status)   # 200 or 202 = accepted


if __name__ == "__main__":
    main()
