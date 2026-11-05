import { readFileSync } from "node:fs";
import vm from "node:vm";
// Local tests for the MFA Hub gate and API (run: node tools/test_hub.mjs). Uses a generated RSA key, no network.
import { verifyAccessJwt, _clearCertCache } from "../functions/_shared/hub_auth.js";
import { onRequest as middleware, hubPathCheck } from "../functions/_middleware.js";
import { onRequestPost as commentPost } from "../functions/api/hub/comment.js";
import { onRequestPost as financePost } from "../functions/api/hub/finance-answer.js";
import { onRequestGet as dataGet } from "../functions/api/hub/data.js";
import { onRequestPost as answerPost } from "../functions/api/hub/answer.js";
import { onRequestPost as requestPost } from "../functions/api/hub/request.js";
import { onRequestGet as logGet } from "../functions/api/hub/log.js";

let pass = 0, fail = 0;
const t = async (name, fn) => { try { await fn(); pass++; console.log("ok   ", name); } catch (e) { fail++; console.log("FAIL ", name, "-", e.message); } };
const eq = (a, b, m) => { if (a !== b) throw new Error(`${m || ""} expected ${JSON.stringify(b)} got ${JSON.stringify(a)}`); };

const TEAM = "super-voice-466f", HOST = `${TEAM}.cloudflareaccess.com`;
const AUD = "a".repeat(64), EMAIL = "zainmerchant@mfa-advisory.com";
const ENV = { ACCESS_TEAM_DOMAIN: TEAM, ACCESS_AUD: AUD, HUB_ALLOWED_EMAIL: EMAIL };

const b64u = (buf) => Buffer.from(buf).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const gen = () => crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"]);
const good = await gen(), evil = await gen();
const goodJwk = { ...(await crypto.subtle.exportKey("jwk", good.publicKey)), kid: "k1" };
const certs = { keys: [{ kid: "k1", kty: "RSA", alg: "RS256", use: "sig", e: goodJwk.e, n: goodJwk.n }] };
const fetchCerts = async (host) => { if (host !== HOST) throw new Error("wrong host " + host); return certs; };
globalThis.fetch = async (url) => { if (String(url) === `https://${HOST}/cdn-cgi/access/certs`) return new Response(JSON.stringify(certs)); throw new Error("unexpected fetch " + url); };

const now = Math.floor(Date.now() / 1000);
async function sign(payload, { key = good.privateKey, header = { alg: "RS256", kid: "k1", typ: "JWT" } } = {}) {
  const h = b64u(JSON.stringify(header)), p = b64u(JSON.stringify(payload));
  const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(h + "." + p));
  return h + "." + p + "." + b64u(sig);
}
const base = () => ({ aud: [AUD], email: EMAIL, exp: now + 3600, iat: now - 10, nbf: now - 10, iss: `https://${HOST}`, type: "app", sub: "u1" });
const V = (tok, env = ENV) => verifyAccessJwt(tok, env, { fetchCerts });

await t("valid token accepted", async () => { const r = await V(await sign(base())); eq(r.ok, true, r.reason); });
await t("email compare is case-insensitive", async () => { const r = await V(await sign({ ...base(), email: "ZainMerchant@MFA-Advisory.com" })); eq(r.ok, true); });
await t("team domain may be the full host", async () => { const r = await V(await sign(base()), { ...ENV, ACCESS_TEAM_DOMAIN: HOST }); eq(r.ok, true); });
await t("forged signature (other key) rejected", async () => { eq((await V(await sign(base(), { key: evil.privateKey }))).reason, "bad signature"); });
await t("tampered payload rejected", async () => { const tok = (await sign(base())).split("."); tok[1] = b64u(JSON.stringify({ ...base(), email: "attacker@example.com" })); eq((await V(tok.join("."))).ok, false); });
await t("expired token rejected", async () => { eq((await V(await sign({ ...base(), exp: now - 3600 }))).reason, "expired"); });
await t("not-yet-valid token rejected", async () => { eq((await V(await sign({ ...base(), nbf: now + 3600 }))).reason, "not yet valid"); });
await t("wrong aud rejected", async () => { eq((await V(await sign({ ...base(), aud: ["b".repeat(64)] }))).reason, "bad aud"); });
await t("wrong issuer rejected", async () => { eq((await V(await sign({ ...base(), iss: "https://evil.cloudflareaccess.com" }))).reason, "bad iss"); });
await t("other email rejected", async () => { eq((await V(await sign({ ...base(), email: "someone@mfa-advisory.com" }))).reason, "email not allowed"); });
await t("missing email rejected", async () => { const p = base(); delete p.email; eq((await V(await sign(p))).reason, "email not allowed"); });
await t("service-token style (type org) rejected", async () => { eq((await V(await sign({ ...base(), type: "org" }))).reason, "bad type"); });
await t("alg none rejected", async () => { const h = b64u(JSON.stringify({ alg: "none", kid: "k1" })), p = b64u(JSON.stringify(base())); eq((await V(h + "." + p + ".")).ok, false); });
await t("alg HS256 rejected", async () => { eq((await V(await sign(base(), { header: { alg: "HS256", kid: "k1" } }))).ok, false); });
await t("unknown kid rejected", async () => { _clearCertCache(); eq((await V(await sign(base(), { header: { alg: "RS256", kid: "zz" } }))).reason, "unknown kid"); });
await t("garbage token rejected", async () => { eq((await V("abc.def.ghi")).ok, false); eq((await V("")).ok, false); eq((await V(null)).ok, false); });
await t("missing env = fail closed", async () => { const tok = await sign(base()); eq((await V(tok, {})).reason, "not configured"); eq((await V(tok, { ...ENV, ACCESS_AUD: "" })).reason, "not configured"); eq((await V(tok, { ...ENV, ACCESS_TEAM_DOMAIN: "evil.com/x" })).reason, "not configured"); });

// ---------- middleware ----------
const ASSETS = { fetch: async (req) => new Response("<html>MFA 404 page</html>", { status: 404, headers: { "Content-Type": "text/html" } }) };
async function run(url, { jwt, env = ENV, method = "GET", headers = {} } = {}) {
  let called = false; const data = {};
  const h = new Headers(headers); if (jwt) h.set("Cf-Access-Jwt-Assertion", jwt);
  const res = await middleware({ request: new Request(url, { method, headers: h }), env: { ...env, ASSETS }, data,
    next: async () => { called = true; return new Response("<html>page</html>", { status: 200, headers: { "Content-Type": "text/html" } }); } });
  return { res, called, data };
}
_clearCertCache();
const JWT = await sign(base());
await t("public page passes through untouched", async () => { const r = await run("https://mfa-advisory.com/1099-filing/"); eq(r.called, true); eq(r.res.headers.get("X-Robots-Tag"), null); });
await t("public home + blog pass through", async () => { eq((await run("https://mfa-advisory.com/")).called, true); eq((await run("https://mfa-advisory.com/blog/")).called, true); });
for (const p of ["/hub", "/hub/", "/hub/finance/", "/hub/hub.js", "/api/hub/data?page=finance", "/HUB/", "/%68ub/", "//hub/", "/api/%68ub/comment", "/Api/Hub/data", "/hub%2F..%2F"]) {
  await t(`no JWT on public host ${p} -> 404, next not called`, async () => { const r = await run("https://mfa-advisory.com" + p); eq(r.res.status, 404); eq(r.called, false); eq(r.res.headers.get("Cache-Control").includes("no-store"), true); eq((await r.res.text()).includes("MFA 404 page"), true); });
}
await t("no JWT on pages.dev /hub -> 404", async () => { const r = await run("https://mfa-website-83y.pages.dev/hub/"); eq(r.res.status, 404); eq(r.called, false); });
await t("forged JWT on public host -> 404", async () => { const r = await run("https://mfa-advisory.com/hub/", { jwt: await sign(base(), { key: evil.privateKey }) }); eq(r.res.status, 404); eq(r.called, false); });
await t("expired JWT on hub host -> 403", async () => { const r = await run("https://hub.mfa-advisory.com/hub/", { jwt: await sign({ ...base(), exp: now - 100 }) }); eq(r.res.status, 403); eq(r.called, false); });
for (const p of ["/", "/hub/", "/blog/ui.css", "/api/llc-config", "/anything"]) {
  await t(`no JWT on hub host ${p} -> 403`, async () => { const r = await run("https://hub.mfa-advisory.com" + p); eq(r.res.status, 403); eq(r.called, false); });
}
await t("valid JWT: /hub/ served with private headers + CSP", async () => { const r = await run("https://hub.mfa-advisory.com/hub/", { jwt: JWT }); eq(r.res.status, 200); eq(r.called, true); eq(r.data.hubEmail, EMAIL); eq(r.res.headers.get("X-Robots-Tag").includes("noindex"), true); eq(r.res.headers.get("Cache-Control").includes("no-store"), true); eq(!!r.res.headers.get("Content-Security-Policy"), true); });
await t("valid JWT: hub host root redirects to /hub/", async () => { const r = await run("https://hub.mfa-advisory.com/", { jwt: JWT }); eq(r.res.status, 302); eq(r.res.headers.get("Location"), "/hub/"); });
await t("unconfigured env: valid-looking JWT still denied", async () => { const r = await run("https://mfa-advisory.com/hub/", { jwt: JWT, env: {} }); eq(r.res.status, 404); });
await t("hubPathCheck", async () => { eq(hubPathCheck("/blog/"), false); eq(hubPathCheck("/%E0%A4%A"), true); eq(hubPathCheck("/hub"), true); });

// ---------- API (CSRF + validation) with a fake D1 ----------
function fakeDb(opts = {}) {
  const log = [];
  const stmt = (sql, a = []) => ({
    sql, a,
    bind(...b) { return stmt(sql, b); },
    async first() {
      log.push([sql, a]);
      if (sql.startsWith("UPDATE")) {
        if (a[0] === "missing") return null;
        if (sql.includes("'-60 seconds'")) return opts.undoOk === false ? null : { id: a[0], status: "open" };
        return { id: a[0], status: "new", answer: a[1], zain_answer: a[1], answered_at: "2026-11-05T00:00:00Z" };
      }
      if (sql.startsWith("INSERT INTO requests")) return { id: 7, created_at: "2026-11-05T00:00:00Z", area: a[0], body: a[1], status: "new" };
      if (sql.startsWith("SELECT COUNT")) return { n: 0 };
      return { id: 1, created_at: "2026-11-05T00:00:00Z", status: "new" };
    },
    async run() { log.push([sql, a]); return { success: true }; },
    async all() { log.push([sql, a]); return { results: sql.includes("FROM log") && !sql.includes("GROUP") ? [{ id: 1, ts: "2026-11-05T00:00:00Z", agent: "Hub", action: "built", detail: "x" }] : [] }; },
  });
  return { log, prepare(sql) { return stmt(sql); }, async batch(list) { return Promise.all(list.map((x) => x.all())); } };
}
function apiCtx(url, { origin = "https://hub.mfa-advisory.com", ct = "application/json", body = {}, authedEmail = EMAIL, xh = "1", sfs } = {}) {
  const h = new Headers(); if (origin) h.set("Origin", origin); if (ct) h.set("Content-Type", ct); if (xh) h.set("X-MFA-Hub", xh); if (sfs) h.set("Sec-Fetch-Site", sfs);
  const db = fakeDb();
  return { db, ctx: { request: new Request(url, { method: "POST", headers: h, body: typeof body === "string" ? body : JSON.stringify(body) }), env: { HUB_DB: db }, data: authedEmail ? { hubEmail: authedEmail } : {} } };
}
const CU = "https://hub.mfa-advisory.com/api/hub/comment", FU = "https://hub.mfa-advisory.com/api/hub/finance-answer";
const okBody = { page: "board", item_ref: "agent:Hub", body: "Please pause Store." };
await t("comment: same-origin JSON accepted", async () => { const { ctx, db } = apiCtx(CU, { body: okBody, sfs: "same-origin" }); const r = await commentPost(ctx); eq(r.status, 200); eq(db.log[0][1][2], "Please pause Store."); });
await t("comment: cross-origin Origin rejected", async () => { const { ctx, db } = apiCtx(CU, { body: okBody, origin: "https://evil.example" }); eq((await commentPost(ctx)).status, 403); eq(db.log.length, 0); });
await t("comment: other MFA origin rejected", async () => { const { ctx } = apiCtx(CU, { body: okBody, origin: "https://mfa-advisory.com" }); eq((await commentPost(ctx)).status, 403); });
await t("comment: missing Origin rejected", async () => { const { ctx } = apiCtx(CU, { body: okBody, origin: null }); eq((await commentPost(ctx)).status, 403); });
await t("comment: Sec-Fetch-Site cross-site rejected", async () => { const { ctx } = apiCtx(CU, { body: okBody, sfs: "cross-site" }); eq((await commentPost(ctx)).status, 403); });
await t("comment: text/plain (form-style CSRF) rejected", async () => { const { ctx } = apiCtx(CU, { body: okBody, ct: "text/plain" }); eq((await commentPost(ctx)).status, 403); });
await t("comment: missing X-MFA-Hub header rejected", async () => { const { ctx } = apiCtx(CU, { body: okBody, xh: null }); eq((await commentPost(ctx)).status, 403); });
await t("comment: no Access identity rejected", async () => { const { ctx } = apiCtx(CU, { body: okBody, authedEmail: null }); eq((await commentPost(ctx)).status, 403); });
await t("comment: bad page / ref / empty body rejected", async () => {
  for (const b of [{ ...okBody, page: "x" }, { ...okBody, item_ref: "a b<script>" }, { ...okBody, body: "  " }, { ...okBody, body: "x".repeat(4001) }]) { const { ctx } = apiCtx(CU, { body: b }); eq((await commentPost(ctx)).status, 400); }
  const { ctx } = apiCtx(CU, { body: "not json" }); eq((await commentPost(ctx)).status, 400);
});
await t("finance answer: accepted and sets status new", async () => { const { ctx, db } = apiCtx(FU, { body: { id: "1843-20260917-9b0678", answer: "Business · Advisory/Consulting Income" } }); const r = await financePost(ctx); eq(r.status, 200); eq((await r.json()).item.status, "new"); eq(db.log[0][0].includes("status = 'new'"), true); });
await t("finance answer: cross-origin rejected", async () => { const { ctx, db } = apiCtx(FU, { body: { id: "x1", answer: "y" }, origin: "https://evil.example" }); eq((await financePost(ctx)).status, 403); eq(db.log.length, 0); });
await t("finance answer: unknown id -> 404", async () => { const { ctx } = apiCtx(FU, { body: { id: "missing", answer: "y" } }); eq((await financePost(ctx)).status, 404); });
await t("data: no Access identity -> 403", async () => { const r = await dataGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/data?page=board"), env: { HUB_DB: fakeDb() }, data: {} }); eq(r.status, 403); });
await t("data: unknown page -> 400", async () => { const r = await dataGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/data?page=x"), env: { HUB_DB: fakeDb() }, data: { hubEmail: EMAIL } }); eq(r.status, 400); });

// ---------- v2: chips (answer + undo), requests, log, data pages ----------
const AU = "https://hub.mfa-advisory.com/api/hub/answer", RU = "https://hub.mfa-advisory.com/api/hub/request";
await t("chip answer (need): same-origin accepted, status new, log line written", async () => {
  const { ctx, db } = apiCtx(AU, { body: { kind: "need", id: "need-ads-1099", answer: "Yes, keep 1099 to Nov 15" } });
  const r = await answerPost(ctx); eq(r.status, 200); const j = await r.json(); eq(j.item.status, "new");
  eq(db.log[0][0].includes("UPDATE needs"), true); eq(db.log[0][1][1], "Yes, keep 1099 to Nov 15"); eq(db.log.some((x) => x[0].startsWith("INSERT INTO log")), true);
});
await t("chip answer (finance) updates finance_questions", async () => { const { ctx, db } = apiCtx(AU, { body: { kind: "finance", id: "1843-20260422-5899cc", answer: "Personal · Owner's Draws" } }); eq((await answerPost(ctx)).status, 200); eq(db.log[0][0].includes("UPDATE finance_questions"), true); });
await t("chip answer: unknown kind / bad id / empty answer -> 400", async () => {
  for (const b of [{ kind: "comments", id: "x", answer: "y" }, { kind: "need", id: "a b", answer: "y" }, { kind: "need", id: "x", answer: " " }, { kind: "need; DROP", id: "x", answer: "y" }]) { const { ctx } = apiCtx(AU, { body: b }); eq((await answerPost(ctx)).status, 400); }
});
await t("chip answer: unknown id -> 404", async () => { const { ctx } = apiCtx(AU, { body: { kind: "need", id: "missing", answer: "y" } }); eq((await answerPost(ctx)).status, 404); });
await t("chip answer: cross-origin / no header / no identity -> 403, nothing written", async () => {
  for (const o of [{ origin: "https://evil.example" }, { xh: null }, { authedEmail: null }, { ct: "text/plain" }]) { const { ctx, db } = apiCtx(AU, { body: { kind: "need", id: "x", answer: "y" }, ...o }); eq((await answerPost(ctx)).status, 403); eq(db.log.length, 0); }
});
await t("undo within 60 s accepted (only status new)", async () => { const { ctx, db } = apiCtx(AU, { body: { kind: "need", id: "x1", undo: true } }); eq((await answerPost(ctx)).status, 200); eq(db.log[0][0].includes("status = 'new'"), true); eq(db.log[0][0].includes("'-60 seconds'"), true); });
await t("undo too late -> 409", async () => { const h = apiCtx(AU, { body: { kind: "need", id: "x1", undo: true } }); h.ctx.env.HUB_DB = fakeDb({ undoOk: false }); eq((await answerPost(h.ctx)).status, 409); });
await t("request: accepted, area defaults to general, cross-origin rejected", async () => {
  const a = apiCtx(RU, { body: { area: "bogus", body: "Make the calendar denser" } }); const r = await requestPost(a.ctx); eq(r.status, 200); eq((await r.json()).request.area, "general");
  const b = apiCtx(RU, { body: { area: "ads", body: "x" }, origin: "https://evil.example" }); eq((await requestPost(b.ctx)).status, 403);
  const c = apiCtx(RU, { body: { area: "ads", body: "" } }); eq((await requestPost(c.ctx)).status, 400);
});
await t("log GET: needs identity, returns rows, clamps limit, agent filter is bound not interpolated", async () => {
  eq((await logGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/log"), env: { HUB_DB: fakeDb() }, data: {} })).status, 403);
  const db = fakeDb(); const r = await logGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/log?limit=99999&agent=Ads%27%20OR%201%3D1"), env: { HUB_DB: db }, data: { hubEmail: EMAIL } });
  eq(r.status, 200); const j = await r.json(); eq(j.rows.length, 1); eq(db.log[0][1][1], 200); eq(db.log[0][1][0], "Ads' OR 1=1"); eq(db.log[0][0].includes("OR 1=1"), false);
});
await t("finance question comment: kind 'question' stored, unknown kind falls back to comment", async () => {
  const a = apiCtx(CU, { body: { page: "finance", item_ref: "1843-20260422-5899cc", body: "Was this the NJ LLC fee?", kind: "question" } }); eq((await commentPost(a.ctx)).status, 200); eq(a.db.log[0][1][3], "question");
  const b = apiCtx(CU, { body: { page: "finance", item_ref: "finance:general", body: "x", kind: "drop table" } }); eq((await commentPost(b.ctx)).status, 200); eq(b.db.log[0][1][3], "comment");
  const c = apiCtx(CU, { body: { page: "finance", item_ref: "finance:general", body: "x", kind: "question" }, origin: "https://evil.example" }); eq((await commentPost(c.ctx)).status, 403);
});
for (const pg of ["home", "board", "calendar", "ads", "finance", "leads", "tasks", "log"]) {
  await t(`data page ${pg} -> 200`, async () => { const r = await dataGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/data?page=" + pg), env: { HUB_DB: fakeDb() }, data: { hubEmail: EMAIL } }); eq(r.status, 200); });
}
await t("log/answer/request paths are behind the gate (404 public, 403 hub host)", async () => {
  for (const p of ["/api/hub/log", "/api/hub/answer", "/api/hub/request", "/hub/log/", "/hub/tasks/"]) { eq((await run("https://mfa-advisory.com" + p)).res.status, 404); eq((await run("https://hub.mfa-advisory.com" + p)).res.status, 403); }
});

// ---------- v3 links (site/hub/hub_links.js, loaded in a sandbox) ----------
const box = { URL, encodeURIComponent, decodeURIComponent }; box.globalThis = box; vm.createContext(box);
vm.runInContext(readFileSync(new URL("../site/hub/hub_links.js", import.meta.url), "utf8"), box);
const HL = box.HubLinks;
await t("links: only safe https URLs pass", async () => {
  for (const bad of ["javascript:alert(1)", "http://ads.google.com/", "data:text/html,x", "https://user:pw@ads.google.com/", "https://a.com/x y", "https://a.com/\"onmouseover", "//ads.google.com", "", null, 5, "https://a.com/<b>", "https://" + "a".repeat(2001)]) eq(HL.safeUrl(bad), null, String(bad));
  eq(HL.safeUrl("https://ads.google.com/aw/campaigns?ocid=8595837773"), "https://ads.google.com/aw/campaigns?ocid=8595837773");
  eq(HL.known("https://studio.youtube.com/x"), true); eq(HL.known("https://evil-google.com/x"), false); eq(HL.known("https://google.com.evil.io/"), false);
});
await t("links: platform deep links, aliases, D1 override, unsafe override ignored", async () => {
  eq(HL.platformLink("Google Ads").url, "https://ads.google.com/aw/campaigns?ocid=8595837773");
  eq(HL.platformLink("Instagram+Facebook").label, "Meta Business Suite"); eq(HL.platformLink("Newsletter").label, "MailerLite sent campaigns");
  const L = HL.index([{ key: "campaign:Google Ads:Princeton", label: "Princeton", url: "https://ads.google.com/aw/overview?campaignId=1" }, { key: "Etsy", label: "x", url: "javascript:alert(1)" }]);
  eq(HL.campaignLink("Google Ads", "Princeton", L).url, "https://ads.google.com/aw/overview?campaignId=1");
  eq(HL.campaignLink("Google Ads", "Other", L).label, "Google Ads");
  eq(HL.platformLink("Etsy", L).url, "https://www.etsy.com/your/shops/me/stats");
  eq(HL.agentLink("Ads").label, "Google Ads"); eq(HL.agentLink("Finance").label, "QuickBooks banking"); eq(HL.agentLink("Hub"), null);
  eq(HL.doc("Ads"), "claude/site/claude-ads-playbook.md");
  for (const k of Object.keys(HL.DEF)) eq(!!HL.safeUrl(HL.DEF[k][1]), true, k);
});
await t("links: hash routes round-trip and reject junk keys", async () => {
  eq(HL.route("ads", { platform: "google-ads", range: "7d" }), "/hub/ads/#platform=google-ads&range=7d");
  eq(HL.route("home"), "/hub/"); eq(HL.route("evil", { a: "x" }), "/hub/#a=x"); eq(HL.route("calendar", { item: "a b&c=d" }), "/hub/calendar/#item=a%20b%26c%3Dd");
  const h = HL.parseHash("#item=a%20b%26c%3Dd&range=7d&BAD=1&x%3Cy=2&empty=&q=%E0%A4"); eq(h.item, "a b&c=d"); eq(h.range, "7d"); eq(h.BAD, undefined); eq(h.empty, undefined); eq(h.q, undefined);
  eq(JSON.stringify(HL.parseHash("#needs")), "{}");
  eq(HL.matchSlug("google", ["Google Ads", "Pinterest Ads"]), "Google Ads"); eq(HL.matchSlug("pinterest", ["Pinterest", "Pinterest Ads"]), "Pinterest"); eq(HL.matchSlug("nope", ["Google Ads"]), null);
});
await t("links: comment refs map to hub pages; Gmail search uses the fragment and first name only", async () => {
  eq(HL.refHref("board", "agent:Ads"), "/hub/board/#agent=Ads"); eq(HL.refHref("ads", "platform:Google-Ads"), "/hub/ads/#platform=google-ads&range=7d");
  eq(HL.refHref("leads", "lead:l1"), "/hub/leads/#lead=l1"); eq(HL.refHref("finance", "1843-x"), "/hub/finance/#q=1843-x"); eq(HL.refHref("finance", "finance:general"), "/hub/finance/");
  eq(HL.refHref("calendar", "2026-11-04-li"), "/hub/calendar/#item=2026-11-04-li");
  const g = HL.gmailSearch("Benson <x@y.com>"); eq(g.startsWith("https://mail.google.com/mail/u/0/#search/"), true); eq(g.includes("?"), false); eq(g.includes("@"), false);
});
await t("data: every page returns the links table; board gets log lines", async () => {
  for (const pg of ["home", "board", "calendar", "ads", "finance", "leads", "tasks"]) {
    const db = fakeDb(); const r = await dataGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/data?page=" + pg), env: { HUB_DB: db }, data: { hubEmail: EMAIL } });
    const j = await r.json(); eq(Array.isArray(j.links), true, pg); eq(db.log.some((x) => x[0].includes("FROM links")), true, pg);
    if (pg === "board") eq(Array.isArray(j.log), true, "board log");
  }
});
await t("hub_links.js is behind the gate (404 public, 403 hub host without Access)", async () => {
  eq((await run("https://mfa-advisory.com/hub/hub_links.js")).res.status, 404); eq((await run("https://hub.mfa-advisory.com/hub/hub_links.js")).res.status, 403);
});

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
