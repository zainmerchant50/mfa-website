// MFA Hub links: safe outbound URLs, platform deep links, hash routes. No DOM here (unit-tested in tools/test_hub.mjs).
(function (root) {
  "use strict";
  // Hosts we expect to link to. Other https links still work but show their host so nothing is hidden.
  var KNOWN = ["google.com", "pinterest.com", "facebook.com", "instagram.com", "linkedin.com", "tiktok.com", "youtube.com", "youtu.be",
    "fiverr.com", "etsy.com", "gumroad.com", "mailerlite.com", "intuit.com", "mfa-advisory.com", "typefully.com", "upwork.com", "claude.ai"];

  function parse(u) { try { return new URL(u); } catch (e) { return null; } }
  // https only, no credentials, no whitespace/quotes/angle brackets/backslashes, max 2000 chars.
  function safeUrl(u) {
    if (typeof u !== "string" || !u || u.length > 2000 || /[\s"'<>\\`]/.test(u)) return null;
    var x = parse(u); if (!x || x.protocol !== "https:" || x.username || x.password || !x.hostname) return null;
    return x.href;
  }
  function host(u) { var x = parse(u); return x ? x.hostname.toLowerCase() : ""; }
  function known(u) { var h = host(u); return KNOWN.some(function (a) { return h === a || h.slice(-(a.length + 1)) === "." + a; }); }

  var DEF = {
    "Google Ads": ["Google Ads", "https://ads.google.com/aw/campaigns?ocid=8595837773"],
    "Pinterest Ads": ["Pinterest Ads", "https://ads.pinterest.com/advertiser/549770934097/"],
    "Pinterest": ["Pinterest profile", "https://www.pinterest.com/mfaadvisory/_created/"],
    "Meta": ["Meta Business Suite", "https://business.facebook.com/latest/insights?asset_id=1357885654083102&business_id=1485123785998879"],
    "LinkedIn": ["LinkedIn analytics", "https://www.linkedin.com/company/108306962/admin/analytics/updates/"],
    "TikTok": ["TikTok Studio", "https://www.tiktok.com/tiktokstudio/analytics"],
    "YouTube Shorts": ["YouTube Studio", "https://studio.youtube.com/channel/UCLNPu802SdUCkrjLeIqgM_g/analytics"],
    "Fiverr Ads": ["Fiverr Ads", "https://www.fiverr.com/users/zainmerchant50/fiverr_ads"],
    "Fiverr": ["Fiverr", "https://www.fiverr.com/users/zainmerchant50/fiverr_ads"],
    "Etsy Ads": ["Etsy stats", "https://www.etsy.com/your/shops/me/stats"],
    "Etsy": ["Etsy stats", "https://www.etsy.com/your/shops/me/stats"],
    "Gumroad": ["Gumroad analytics", "https://app.gumroad.com/analytics"],
    "Upwork": ["Upwork", "https://www.upwork.com/"],
    "MailerLite": ["MailerLite sent campaigns", "https://dashboard.mailerlite.com/campaigns/status/sent"],
    "Subscribers": ["MailerLite subscribers", "https://dashboard.mailerlite.com/subscribers"],
    "QuickBooks": ["QuickBooks banking", "https://qbo.intuit.com/app/banking"],
    "Blog": ["Blog", "https://mfa-advisory.com/blog/"],
    "Site": ["mfa-advisory.com", "https://mfa-advisory.com/"],
    "Gmail": ["Gmail", "https://mail.google.com/mail/u/0/"]
  };
  var ALIAS = { Instagram: "Meta", Facebook: "Meta", "Instagram+Facebook": "Meta", "IG/FB": "Meta", Newsletter: "MailerLite", NL: "MailerLite",
    LI: "LinkedIn", TT: "TikTok", YT: "YouTube Shorts", Pin: "Pinterest", "Website form": "Gmail" };
  var AGENT = { Ads: "Google Ads", Pinterest: "Pinterest Ads", Social: "Meta", Store: "Etsy", Finance: "QuickBooks", TaxSavings: "QuickBooks",
    Site: "Site", Blog: "Blog", Freelance: "Fiverr", "Lead Engine": "Gmail", Growth: "Site" };
  var DOCS = {
    Ads: "claude/site/claude-ads-playbook.md", "Google Ads": "claude/site/claude-ads-playbook.md",
    Pinterest: "claude/site/pinterest-audience-plan.md", "Pinterest Ads": "claude/site/pinterest-audience-plan.md",
    Social: "claude/site/social-plan-nov.md", Meta: "claude/site/social-plan-nov.md", LinkedIn: "claude/site/social-plan-nov.md",
    TikTok: "claude/site/social-plan-nov.md", "YouTube Shorts": "claude/site/social-plan-nov.md",
    Store: "claude/store/daily-stats.md", Etsy: "claude/store/daily-stats.md", "Etsy Ads": "claude/store/daily-stats.md", Gumroad: "claude/store/daily-stats.md",
    Finance: "claude/finance/review-board.md", QuickBooks: "claude/finance/review-board.md", TaxSavings: "claude/finance/tax-savings.md",
    Site: "claude/site/agent-inventory.md", Blog: "claude/blog/agent-inventory.md", MailerLite: "claude/blog/agent-inventory.md",
    Freelance: "claude/site/freelance-status.md", Fiverr: "claude/site/freelance-status.md", "Fiverr Ads": "claude/site/freelance-status.md",
    "Lead Engine": "claude/site/lead-response-process.md", Gmail: "claude/site/lead-response-process.md",
    Growth: "claude/site/monetization-plan-nov.md", Hub: "tools/hub_sync.md"
  };

  // D1 rows {key, label, url} override the defaults (only when the URL is safe).
  function index(rows) { var m = {}; (rows || []).forEach(function (r) { if (r && r.key) m[r.key] = r; }); return m; }
  function pick(L, key) {
    var r = L && L[key]; if (r && safeUrl(r.url)) return { label: r.label || key, url: safeUrl(r.url) };
    var d = DEF[key]; return d ? { label: d[0], url: d[1] } : null;
  }
  function canon(name) { return ALIAS[name] || name; }
  function platformLink(name, L) { if (!name) return null; return pick(L, name) || pick(L, canon(name)); }
  function campaignLink(platform, campaign, L) { return (campaign && pick(L, "campaign:" + platform + ":" + campaign)) || platformLink(platform, L); }
  function agentLink(agent, L) { return pick(L, "agent:" + agent) || (AGENT[agent] ? platformLink(AGENT[agent], L) : null); }
  function doc(name, L) { var r = L && L["doc:" + name]; return (r && r.label) || DOCS[name] || DOCS[canon(name)] || null; }

  function slug(s) { return String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
  // "google" matches "Google Ads"; exact slug wins.
  function matchSlug(want, names) {
    var w = slug(want); if (!w) return null; var ex = null, pre = null;
    (names || []).forEach(function (n) { var s = slug(n); if (s === w) ex = ex || n; else if (s.indexOf(w + "-") === 0 || s.indexOf(w) === 0) pre = pre || n; });
    return ex || pre;
  }

  function parseHash(h) {
    var out = {}; String(h || "").replace(/^#/, "").split("&").forEach(function (kv) {
      var i = kv.indexOf("="); if (i < 1) return; var k = kv.slice(0, i), v;
      if (!/^[a-z]{1,12}$/.test(k)) return;
      try { v = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, " ")); } catch (e) { return; }
      if (v.length && v.length <= 200) out[k] = v;
    });
    return out;
  }
  function qs(p) {
    return Object.keys(p || {}).filter(function (k) { return /^[a-z]{1,12}$/.test(k) && p[k] !== null && p[k] !== undefined && p[k] !== ""; })
      .map(function (k) { return k + "=" + encodeURIComponent(String(p[k])); }).join("&");
  }
  var PAGES = ["home", "board", "calendar", "ads", "finance", "leads", "tasks", "log"];
  function route(page, p) { if (PAGES.indexOf(page) < 0) page = "home"; var q = qs(p); return "/hub/" + (page === "home" ? "" : page + "/") + (q ? "#" + q : ""); }

  // Where a comment's item_ref lives in the hub.
  function refHref(page, ref) {
    ref = String(ref || "");
    var m = /^agent:(.+)$/.exec(ref); if (m) return route("board", { agent: m[1] });
    if (/^(idea|activity):/.test(ref)) return route("board");
    if (/^need:/.test(ref)) return route("home");
    m = /^platform:(.+)$/.exec(ref); if (m) return route("ads", { platform: slug(m[1]), range: "7d" });
    m = /^lead:(.+)$/.exec(ref); if (m) return route("leads", { lead: m[1] });
    if (/^request:/.test(ref)) return route("tasks");
    if (ref === "finance:general") return route("finance");
    if (page === "finance") return route("finance", { q: ref });
    if (page === "calendar") return route("calendar", { item: ref });
    return route(page);
  }
  // Gmail search by first name only, in the URL fragment (never sent to a server, no full email).
  function gmailSearch(firstName) {
    var n = String(firstName || "").replace(/[^A-Za-zÀ-ɏ' -]/g, "").trim().slice(0, 40);
    return n ? "https://mail.google.com/mail/u/0/#search/" + encodeURIComponent('"' + n + '"') : DEF.Gmail[1];
  }

  root.HubLinks = { safeUrl: safeUrl, known: known, host: host, index: index, platformLink: platformLink, campaignLink: campaignLink, agentLink: agentLink,
    doc: doc, slug: slug, matchSlug: matchSlug, parseHash: parseHash, qs: qs, route: route, refHref: refHref, gmailSearch: gmailSearch, DEF: DEF };
})(typeof window !== "undefined" ? window : globalThis);
