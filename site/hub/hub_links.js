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

  // ---------- ranges (Today / 7d / 30d) ----------
  var RANGE = { today: 1, "7d": 7, "30d": 30 };
  function rangeKey(r) { return RANGE[r] ? r : "7d"; }
  function addDays(ymd, n) { var d = new Date(ymd + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  // current window ends today (ET date t); prior window is the same length right before it
  function win(t, n) { return { n: n, from: addDays(t, -(n - 1)), to: t, pFrom: addDays(t, -(2 * n - 1)), pTo: addDays(t, -n) }; }
  // a window is covered when its data starts by its 2nd day (today may not be pulled yet)
  function covered(since, from) { return !!since && since <= addDays(from, 1); }
  function distinct(list, k) { var o = {}; list.forEach(function (r) { o[r[k]] = 1; }); return Object.keys(o).length; }

  // ads/social rows -> per platform {today, s (window), p (prior), na, naKind}. naKind 'build' = not enough daily rows yet
  // (the number would be wrong), 'nr' = the platform doesn't report at this length (left out of totals, said so).
  function adsModel(rows, n, t) {
    var W = win(t, n), P = {}, need = n === 1 ? 1 : n - 1, lab = n === 1 ? "today" : n + "d";
    (rows || []).forEach(function (r) {
      var p = P[r.platform] = P[r.platform] || { name: r.platform, paid: /Ads$/.test(r.platform), daily: [], win: [], latest: null, since: null };
      if (r.window_days === 1) { p.daily.push(r); if (!p.since || r.date < p.since) p.since = r.date; } else p.win.push(r);
      if (!p.latest || r.date > p.latest) p.latest = r.date;
    });
    function sum(list) { return list.reduce(function (s, r) { s.i += r.impressions || 0; s.c += r.clicks || 0; s.s += r.spend || 0; s.v += r.conversions || 0; s.n++; return s; }, { i: 0, c: 0, s: 0, v: 0, n: 0 }); }
    function wrow(p, len, a, b) { var w = p.win.filter(function (r) { return r.window_days === len && r.date >= a && r.date <= b; }).sort(function (x, y) { return y.date.localeCompare(x.date); })[0]; return w ? sum([w]) : null; }
    Object.keys(P).forEach(function (k) {
      var p = P[k], inW = function (a, b) { return p.daily.filter(function (r) { return r.date >= a && r.date <= b; }); };
      p.today = sum(inW(t, t)); p.na = ""; p.naKind = ""; p.note = "";
      var dc = inW(W.from, W.to), dp = inW(W.pFrom, W.pTo), wr;
      if (dc.length && distinct(dc, "date") >= need) p.s = sum(dc);
      else if (n > 1 && (wr = wrow(p, n, addDays(t, -2), t))) { p.s = wr; p.note = n + "-day total from the platform"; }
      else {
        p.s = null;
        if (p.daily.length) { p.naKind = "build"; p.na = n === 1 ? "today: not pulled yet" : lab + ": n/a until data builds (" + distinct(dc, "date") + " of " + n + " days in D1)"; }
        else if (p.win.length) { var lens = p.win.map(function (r) { return r.window_days; }).filter(function (x, i, a) { return a.indexOf(x) === i; }).join("/"); p.naKind = "nr"; p.na = lab + ": n/a (platform gives " + lens + "-day totals only)"; }
        else { p.naKind = "build"; p.na = lab + ": no data yet"; }
      }
      if (dp.length && distinct(dp, "date") >= need) p.p = sum(dp);
      else if (n > 1 && (wr = wrow(p, n, addDays(W.pTo, -2), W.pTo))) p.p = wr;
      else p.p = null;
    });
    return P;
  }

  // ---------- finance question kinds ----------
  // "<payee>: $46.00 spend on 2026-11-02, BofA Checking ••1843 (bank text: …) Note: …"
  var TXN = /^(.{1,80}?):\s*([+-]?)\$([\d,]+(?:\.\d{2})?)\s*(spend|deposit|charge|payment|refund|credit|debit|transfer)?\s*on\s*(\d{4}-\d{2}-\d{2}),\s*([^(]*?••\s?\d{4}|[^,(]{2,40})/i;
  function parseTxn(q) {
    var m = TXN.exec(String(q || "")); if (!m) return null;
    var note = /\bNote:\s*([\s\S]*)$/.exec(q), dir = (m[4] || "").toLowerCase();
    if (m[2] === "+" && !dir) dir = "deposit";
    return { payee: m[1].trim(), amount: Number(m[3].replace(/,/g, "")), dir: dir, date: m[5], account: m[6].trim(), note: note ? note[1].trim() : "" };
  }
  function financeKind(f) { if (f && (f.kind === "txn" || f.kind === "other")) return f.kind; return f && parseTxn(f.question) ? "txn" : "other"; }

  // ---------- readable text (Board cards) ----------
  // rich(text, {head}) -> blocks [{type:"h"|"p", segs} | {type:"ul", items:[segs]}], segs = [{t, b, k}].
  // Output is plain strings only; the page puts them on screen with textContent, so markup in agent text stays literal.
  // One point per line: "- " lines are bullets; a line with several sentences or "; " parts becomes a bullet list.
  // Bold: a short leading label ("Why:"), **markdown bold**, money, %, counts, dates and times (not numbers inside URLs or long IDs).
  var ABBR = /(?:\be\.g|\bi\.e|\bvs|\betc|\bapprox|\bMrs?|\bMs|\bDr|\bSt|\bNo|\bU\.S|\bInc|\bJan|\bFeb|\bMar|\bApr|\bJun|\bJul|\bAug|\bSept?|\bOct|\bNov|\bDec)\.$/i;
  var TOK = new RegExp([
    "https?:\\/\\/\\S+",
    "\\*\\*[^*\\n]+?\\*\\*",
    "[+-]?\\$\\d[\\d,]*(?:\\.\\d+)?(?:\\s?[kKmM]\\b)?",
    "\\b\\d{4}-\\d{2}-\\d{2}\\b",
    "\\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\\.? \\d{1,2}(?:st|nd|rd|th)?(?:, \\d{4})?\\b",
    "\\b\\d{1,2}:\\d{2}(?:\\s?[AaPp][Mm]\\b)?",
    "\\b\\d{1,2}\\/\\d{1,2}(?:\\/\\d{2,4})?\\b",
    "\\b\\d[\\d,]{0,8}(?:\\.\\d+)?(?!\\d)%?"
  ].join("|"), "g");
  var LABEL = /^([A-Za-z][A-Za-z0-9 '’&\/()+.-]{0,23}):\s+(?=\S)/;
  function inline(s) {
    var out = [], last = 0, m, lab = LABEL.exec(s);
    if (lab) { out.push({ t: lab[1] + ":", b: true, k: "label" }, { t: " ", b: false }); s = s.slice(lab[0].length); }
    TOK.lastIndex = 0;
    while ((m = TOK.exec(s))) {
      var x = m[0], i = m.index;
      if (/^https?:/i.test(x)) continue; // URLs stay plain
      if (/^[\d,.]+%?$/.test(x) && /[A-Za-z]-$/.test(s.slice(Math.max(0, i - 2), i))) continue; // form names: W-9, 1099-NEC's tail
      if (i > last) out.push({ t: s.slice(last, i), b: false });
      if (x.slice(0, 2) === "**") out.push({ t: x.slice(2, -2), b: true, k: "md" }); else out.push({ t: x, b: true, k: "num" });
      last = i + x.length;
    }
    if (last < s.length) out.push({ t: s.slice(last), b: false });
    return out;
  }
  function pieces(line) {
    var out = [];
    line.split(/;\s+/).forEach(function (part) {
      var acc = [];
      part.replace(/([.!?])\s+(?=["“(]?[A-Z0-9$*])/g, "$1\u0001").split("\u0001").forEach(function (x) {
        if (acc.length && ABBR.test(acc[acc.length - 1])) acc[acc.length - 1] += " " + x; else acc.push(x);
      });
      acc.forEach(function (x) { x = x.replace(/[;,]\s*$/, "").trim(); if (x) out.push(x); });
    });
    return out;
  }
  function rich(text, o) {
    o = o || {}; var blocks = [], ul = null;
    String(text === null || text === undefined ? "" : text).replace(/\r/g, "").split("\n").forEach(function (line) {
      line = line.trim(); if (!line) { ul = null; return; }
      var bm = /^(?:[-*•–]|\d{1,2}[.)])\s+(.+)$/.exec(line);
      if (bm) { if (!ul) { ul = { type: "ul", items: [] }; blocks.push(ul); } ul.items.push(inline(bm[1].trim())); return; }
      var ps = pieces(line); if (!ps.length) return;
      if (o.head && !blocks.length) { blocks.push({ type: "h", segs: inline(ps.shift()) }); ul = null; if (!ps.length) return; }
      if (ps.length === 1) { blocks.push({ type: "p", segs: inline(ps[0]) }); ul = null; return; }
      ul = { type: "ul", items: ps.map(inline) }; blocks.push(ul); ul = null;
    });
    return blocks;
  }
  // one-tap answers for a Needs-you item: the agent's own chips, else defaults by type
  function suggestionsFor(title, list) {
    var s = (Array.isArray(list) ? list : []).filter(function (x) { return typeof x === "string" && x.trim(); });
    if (s.length) return s;
    var t = String(title || "").trim();
    if (/^(approve|ok(ay)? to|go ahead|sign off|green.?light)\b/i.test(t) || /\bapprov(e|al)\b/i.test(t)) return ["Yes, go ahead", "No", "Hold for now"];
    return ["Yes", "No", "Tell me more"];
  }
  // "3d waiting" (bad after 2 days) from an ISO time; null when the time is missing or bad
  function waitAge(iso, now) {
    var t = new Date(iso).getTime(); if (!iso || isNaN(t)) return null;
    var h = Math.max(0, ((now === undefined ? Date.now() : now) - t) / 36e5);
    return { h: h, label: (h < 1 ? "<1h" : h < 24 ? Math.floor(h) + "h" : Math.floor(h / 24) + "d") + " waiting", level: h >= 48 ? "bad" : h >= 24 ? "warn" : "ok" };
  }
  function urgent(title, detail) { return /\b(urgent|asap|today|tonight|deadline|overdue|expir\w*|blocked|due)\b/i.test(String(title || "") + " " + String(detail || "")); }

  root.HubLinks = { safeUrl: safeUrl, known: known, host: host, index: index, platformLink: platformLink, campaignLink: campaignLink, agentLink: agentLink,
    doc: doc, slug: slug, matchSlug: matchSlug, parseHash: parseHash, qs: qs, route: route, refHref: refHref, gmailSearch: gmailSearch, DEF: DEF,
    RANGE: RANGE, rangeKey: rangeKey, addDays: addDays, win: win, covered: covered, adsModel: adsModel, parseTxn: parseTxn, financeKind: financeKind,
    rich: rich, suggestionsFor: suggestionsFor, waitAge: waitAge, urgent: urgent };
})(typeof window !== "undefined" ? window : globalThis);
