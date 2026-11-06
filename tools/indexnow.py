#!/usr/bin/env python3
"""Tells Bing (and every other IndexNow search engine: Yandex, Seznam, Naver...) which MFA URLs are new or changed.

ChatGPT search, Microsoft Copilot and Bing draw on Bing's index, so a fast Bing crawl is how new pages reach them sooner.
IndexNow is a public protocol (https://www.indexnow.org/documentation): the key file below must be live at
https://mfa-advisory.com/<key>.txt (it ships in site/ and is live since Oct 2026).

    python3 tools/indexnow.py                     # dry run: every URL in sitemap.xml
    python3 tools/indexnow.py --changed            # dry run: pages whose built files changed in the last commit
    python3 tools/indexnow.py --changed abc123     # ... changed since commit abc123 (e.g. the commit before a publish)
    python3 tools/indexnow.py --send --changed     # submit them (run AFTER the Cloudflare Pages deploy is live)
    python3 tools/indexnow.py --send --wait --changed   # first wait (up to 5 min) until the first URL answers 200 live
    python3 tools/indexnow.py --send https://mfa-advisory.com/shop/ https://mfa-advisory.com/services/   # just these

Blog task (tools/skills/mfa-contentcreator/SKILL.md): after pushing a post and seeing the Cloudflare Pages check go green, run
`python3 tools/indexnow.py --send --wait --changed <sha-before-the-post>`.
If this machine's network blocks api.indexnow.org (the cloud sandboxes do), the script prints one GET link per URL instead:
open them in a browser (Claude in Chrome); an empty page with HTTP 200 or 202 means accepted.

Only indexable pages are sent (those listed in sitemap.xml), plus sitemap.xml itself when it changed. Standard library only.
"""
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
HOST = "mfa-advisory.com"
BASE = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"
KEYS = [p for p in SITE.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem)]


def sitemap_urls():
    return re.findall(r"<loc>(.*?)</loc>", (SITE / "sitemap.xml").read_text(encoding="utf-8"))


def file_url(rel):
    """site-relative file path -> public URL (Cloudflare Pages: x/index.html -> /x/, privacy.html -> /privacy)."""
    if rel.endswith("index.html"):
        return f"{BASE}/{rel[: -len('index.html')]}"
    if rel.endswith(".html"):
        return f"{BASE}/{rel[: -len('.html')]}"
    return f"{BASE}/{rel}"


def changed_urls(since="HEAD~1"):
    out = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", since, "HEAD", "--", "site"],
                         capture_output=True, text=True, check=True).stdout.split()
    live = set(sitemap_urls())
    urls = []
    for f in out:
        u = file_url(f[len("site/"):])
        if u in live or f == "site/sitemap.xml":
            urls.append(u)
    return sorted(set(urls))


def wait_live(url, minutes=5):
    """True once url answers 200; False after `minutes`; None if this machine can't reach the site at all."""
    end = time.time() + minutes * 60
    while time.time() < end:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
                if r.status == 200:
                    return True
        except urllib.error.HTTPError:
            pass                      # reachable, not deployed yet (404) -> keep waiting
        except Exception:
            return None               # no route to the site from here (sandbox proxy)
        time.sleep(15)
    return False


def get_links(key, urls):
    return [f"{ENDPOINT}?url={urllib.parse.quote(u, safe='')}&key={key}" for u in urls]


def main():
    if len(KEYS) != 1:
        sys.exit("expected exactly one IndexNow key file (32 hex characters + .txt) in site/")
    key = KEYS[0].stem
    assert KEYS[0].read_text().strip() == key
    argv = sys.argv[1:]
    send, wait = "--send" in argv, "--wait" in argv
    argv = [a for a in argv if a not in ("--send", "--wait")]
    if "--changed" in argv:
        i = argv.index("--changed")
        since = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("http") else "HEAD~1"
        urls = changed_urls(since)
    else:
        urls = [a for a in argv if a.startswith("http")] or sitemap_urls()
    print(f"{len(urls)} URLs, key file {BASE}/{key}.txt")
    if not urls:
        return
    if not send:
        print("\n".join(urls[:20]) + ("\n..." if len(urls) > 20 else ""))
        print("dry run: add --send to submit")
        return
    if wait:
        live = wait_live(urls[0])
        if live is False:
            sys.exit(f"{urls[0]} is not live yet (no 200 after 5 minutes); nothing sent")
        if live is None:
            print(f"(can't reach {BASE} from here to confirm the deploy; check the Cloudflare Pages check-run instead)")
    body = {"host": HOST, "key": key, "keyLocation": f"{BASE}/{key}.txt", "urlList": urls[:10000]}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow response:", r.status, "(200 or 202 = accepted)")
    except urllib.error.HTTPError as e:
        sys.exit(f"IndexNow refused: HTTP {e.code} {e.reason} (400 bad request, 403 key not valid, 422 URL not on host, 429 too many)")
    except Exception as e:
        print(f"could not reach {ENDPOINT} from here ({e.__class__.__name__}). Open these in a browser instead:")
        print("\n".join(get_links(key, urls)))
        sys.exit(2)


if __name__ == "__main__":
    main()
