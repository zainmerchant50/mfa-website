import { readFileSync } from "node:fs";
import vm from "node:vm";
// Local tests for the MFA Hub gate and API (run: node tools/test_hub.mjs). Uses a generated RSA key, no network.
import { verifyAccessJwt, _clearCertCache } from "../functions/_shared/hub_auth.js";
import { onRequest as middleware, hubPathCheck, junkPath } from "../functions/_middleware.js";
import { readdirSync, statSync } from "node:fs";
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
await t("junkPath: probes get 410, never a real site file", async () => {
  for (const p of ["/wp-json/wp/v2/wpmcp/streamable", "/wp-login.php", "/xmlrpc.php", "/wp-admin/", "/wp/", "/wordpress/", "/wp-sitemap.xml", "/.env", "/.env.backup", "/.git/config", "/.aws/credentials", "/public../.env", "/x1x1.php", "/proc/self/environ", "/api/w/a/../../etc", "/portfolio/business-growth/", "/header/sticky-header/"]) eq(junkPath(p), true, p);
  for (const p of ["/", "/blog/", "/.well-known/security.txt", "/llc-formation/pa/", "/tools/is-it-deductible/deductions.json", "/privacy", "/hub/", "/api/llc-config", "/u/abc.def", "/wpm/"]) eq(junkPath(p), false, p);
  const walk = (d) => readdirSync(d).flatMap((n) => statSync(d + "/" + n).isDirectory() ? walk(d + "/" + n) : [d + "/" + n]);
  const root = new URL("../site", import.meta.url).pathname;
  for (const f of walk(root)) { const p = f.slice(root.length); if (junkPath(p)) throw new Error("real file matched: " + p); }
});
await t("junk probe answered 410 without touching assets", async () => { const r = await run("https://mfa-advisory.com/wp-json/wp/v2/wpmcp/streamable"); eq(r.res.status, 410); eq(r.called, false); eq(r.res.headers.get("X-Robots-Tag"), "noindex"); });
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
    if (pg === "board") { eq(Array.isArray(j.logRecent), true, "board logRecent"); eq(Array.isArray(j.logMin), true, "board logMin"); }
    if (pg === "finance") eq(Array.isArray(j.needs), true, "finance needs");
  }
});
await t("hub_links.js is behind the gate (404 public, 403 hub host without Access)", async () => {
  eq((await run("https://mfa-advisory.com/hub/hub_links.js")).res.status, 404); eq((await run("https://hub.mfa-advisory.com/hub/hub_links.js")).res.status, 403);
});

// ---------- v4: ranges + finance kinds ----------
const day = (t, n) => HL.addDays(t, n);
const T0 = "2026-11-05";
const mk = (platform, from, to, o = {}) => { const out = []; for (let d = from; d <= to; d = day(d, 1)) out.push({ date: d, platform, campaign: "c", window_days: 1, impressions: 10, clicks: 1, spend: 2, conversions: 0, ...o }); return out; };
await t("ranges: windows and coverage", async () => {
  const w = HL.win(T0, 7); eq(w.from, "2026-10-30"); eq(w.to, T0); eq(w.pFrom, "2026-10-23"); eq(w.pTo, "2026-10-29");
  const w30 = HL.win(T0, 30); eq(w30.from, "2026-10-07"); eq(w30.pTo, "2026-10-06");
  eq(HL.rangeKey("30d"), "30d"); eq(HL.rangeKey("14d"), "7d"); eq(HL.rangeKey(undefined), "7d"); eq(HL.rangeKey("today"), "today");
  eq(HL.covered("2026-10-08", "2026-10-07"), true); eq(HL.covered("2026-10-09", "2026-10-07"), false); eq(HL.covered(null, "2026-10-07"), false);
});
await t("ranges: 30d is n/a until daily rows cover it (no partial totals)", async () => {
  const rows = mk("Google Ads", "2026-10-13", "2026-11-04");   // 23 days, like D1 today
  const P30 = HL.adsModel(rows, 30, T0)["Google Ads"]; eq(P30.s, null); eq(P30.naKind, "build"); eq(/n\/a until data builds \(23 of 30 days/.test(P30.na), true, P30.na);
  const P7 = HL.adsModel(rows, 7, T0)["Google Ads"]; eq(P7.s.i, 60); eq(P7.s.s, 12); eq(P7.p.i, 70);   // 6 days (today not pulled) + full prior week
  const full = HL.adsModel(mk("Google Ads", "2026-09-01", "2026-11-04"), 30, T0)["Google Ads"]; eq(full.s.i, 290); eq(full.p.i, 300);
  const td = HL.adsModel(rows, 1, T0)["Google Ads"]; eq(td.s, null); eq(td.na, "today: not pulled yet"); eq(td.p.i, 10);
});
await t("ranges: window-only platforms are 'not reported', never summed into another length", async () => {
  const rows = [{ date: "2026-11-04", platform: "Fiverr Ads", campaign: "All gigs", window_days: 30, impressions: 649, clicks: 6, spend: 11.6, conversions: 2 },
    { date: "2026-11-04", platform: "Pinterest Ads", campaign: "All", window_days: 7, impressions: 5086, clicks: 74, spend: 23.81, conversions: 0 }];
  const P7 = HL.adsModel(rows, 7, T0); eq(P7["Fiverr Ads"].s, null); eq(P7["Fiverr Ads"].naKind, "nr"); eq(P7["Pinterest Ads"].s.i, 5086);
  const P30 = HL.adsModel(rows, 30, T0); eq(P30["Fiverr Ads"].s.i, 649); eq(P30["Pinterest Ads"].s, null); eq(P30["Pinterest Ads"].naKind, "nr");
});
await t("finance: transaction parser and kind", async () => {
  const a = HL.parseTxn("State of New Jersey: $146.00 spend on 2026-04-22, BofA Checking ••1843 (bank text: New Jersey) Note: NJ fee or personal?");
  eq(a.payee, "State of New Jersey"); eq(a.amount, 146); eq(a.dir, "spend"); eq(a.date, "2026-04-22"); eq(a.account, "BofA Checking ••1843"); eq(a.note, "NJ fee or personal?");
  const b = HL.parseTxn("Mohammed Zain Merchant: +$1,838.83 deposit on 2026-11-02, BofA Checking ••1843 (bank text: Mobile Transfer Chk) Note: transfer in");
  eq(b.amount, 1838.83); eq(b.dir, "deposit"); eq(b.payee, "Mohammed Zain Merchant");
  eq(HL.parseTxn("Should MFA use a calendar fiscal year?"), null);
  eq(HL.financeKind({ question: "Create a Loan from owner account?" }), "other"); eq(HL.financeKind({ question: a ? "Tous Les Jours: $46.00 spend on 2026-11-02, Card ••1234" : "" }), "txn");
  eq(HL.financeKind({ kind: "other", question: "Tous Les Jours: $46.00 spend on 2026-11-02, Card ••1234" }), "other"); eq(HL.financeKind({ kind: "bogus", question: "x" }), "other");
});

// ---------- Board text formatter + one-tap answers ----------
const flat = (segs) => segs.map((s) => (s.b ? `[${s.t}]` : s.t)).join("");
await t("text: '; ' chains and sentences become one bullet per line, headline first", async () => {
  const b = HL.rich("Waiting on Zain to approve the budget; spend is $12.50/day, up 25% vs Nov 3. Also needs the banner copy before 2026-11-10.", { head: true });
  eq(b[0].type, "h"); eq(flat(b[0].segs), "Waiting on Zain to approve the budget");
  eq(b[1].type, "ul"); eq(b[1].items.length, 2);
  eq(flat(b[1].items[0]), "spend is [$12.50]/day, up [25%] vs [Nov 3].");
  eq(flat(b[1].items[1]), "Also needs the banner copy before [2026-11-10].");
  eq(HL.rich("Short detail line.")[0].type, "p"); eq(HL.rich("").length, 0); eq(HL.rich(null).length, 0);
});
await t("text: labels, **bold**, '- ' bullets; URLs, long IDs and form names stay plain", async () => {
  eq(flat(HL.rich("Why: W-9 missing for 1099-NEC")[0].segs), "[Why:] W-9 missing for [1099]-NEC");
  const m = HL.rich("**Raise budget to $18**\n- CTR 4.2%\n- 12 leads in 7 days, e.g. at 9:10 AM");
  eq(flat(m[0].segs), "[Raise budget to $18]"); eq(m[0].segs[0].k, "md"); eq(m[1].type, "ul");
  eq(flat(m[1].items[0]), "CTR [4.2%]"); eq(flat(m[1].items[1]), "[12] leads in [7] days, e.g. at [9:10 AM]");
  eq(flat(HL.rich("see https://ads.google.com/x?ocid=123&u=45 and ID 23019283746501928374650192837465")[0].segs), "see https://ads.google.com/x?ocid=123&u=45 and ID 23019283746501928374650192837465");
  eq(flat(HL.rich("Waiting on Zain to approve https://a.com/x: it is long")[0].segs).startsWith("[Waiting"), false); // no label past 25 chars
});
await t("text: markup stays literal text (the page sets textContent only)", async () => {
  const b = HL.rich('<img src=x onerror=alert(1)> costs $5; <script>x</script>');
  const all = JSON.stringify(b);
  eq(all.includes("<img src=x onerror=alert("), true); eq(all.includes("<script>x</script>"), true);
  eq(b.every((x) => (x.segs || x.items.flat()).every((s) => typeof s.t === "string" && Object.keys(s).every((k) => ["t", "b", "k"].includes(k)))), true);
  const hubJs = readFileSync(new URL("../site/hub/hub.js", import.meta.url), "utf8");
  eq(/innerHTML|outerHTML|insertAdjacentHTML|document\.write/.test(hubJs), false, "hub.js must not write HTML strings");
});
await t("answers: agent chips win, else defaults by type", async () => {
  eq(JSON.stringify(HL.suggestionsFor("Approve the new ad copy?", [])), JSON.stringify(["Yes, go ahead", "No", "Hold for now"]));
  eq(JSON.stringify(HL.suggestionsFor("**Approve** raising the budget?", null)), JSON.stringify(["Yes, go ahead", "No", "Hold for now"]));
  eq(JSON.stringify(HL.suggestionsFor("Should the blog cover OPT taxes?")), JSON.stringify(["Yes", "No", "Tell me more"]));
  eq(JSON.stringify(HL.suggestionsFor("Approve it?", ["Keep it", " ", 5, "Pause it"])), JSON.stringify(["Keep it", "Pause it"]));
  const hub = readFileSync(new URL("../site/hub/hub.js", import.meta.url), "utf8") + readFileSync(new URL("../site/hub/hub_links.js", import.meta.url), "utf8");
  eq(/["'][^"'\n]*\bfree\b[^"'\n]*["']/i.test(hub), false, "no 'free' in hub UI strings");
});
await t("answers: wait age labels and urgency", async () => {
  const now = Date.parse("2026-11-06T12:00:00Z");
  eq(HL.waitAge("2026-11-06T11:30:00Z", now).label, "<1h waiting"); eq(HL.waitAge("2026-11-06T07:00:00Z", now).label, "5h waiting");
  const d3 = HL.waitAge("2026-11-03T12:00:00Z", now); eq(d3.label, "3d waiting"); eq(d3.level, "bad");
  eq(HL.waitAge("2026-11-05T06:00:00Z", now).level, "warn"); eq(HL.waitAge("", now), null); eq(HL.waitAge("nope", now), null);
  eq(HL.urgent("Deadline is today"), true); eq(HL.urgent("Approve the photos?", "Why: Monday push"), false);
});

// ---------- v5: Finance confidence + auto-posted (helpers, API columns, and the real hub.js render on a small fake DOM) ----------
await t("confidence: badge per level, nothing when unrated, aliases and junk", async () => {
  eq(HL.confBadge({ confidence: "high" }).cls, "conf conf-high"); eq(HL.confBadge({ confidence: "high" }).label, "High");
  eq(HL.confBadge({ confidence: "med" }).label, "Med"); eq(HL.confBadge({ confidence: "Medium" }).level, "med"); eq(HL.confBadge({ confidence: "LOW" }).cls, "conf conf-low");
  for (const x of [{}, { confidence: null }, { confidence: "" }, { confidence: "sure" }, null]) eq(HL.confBadge(x), null, JSON.stringify(x));
  eq(HL.confKey("low"), "low"); eq(HL.confKey("x<y"), ""); eq(HL.confKey(undefined), "");
});
await t("confidence: Low (and unrated) sort first, chip counts and filter", async () => {
  const L = [{ id: "h", confidence: "high" }, { id: "m", confidence: "med" }, { id: "n" }, { id: "l", confidence: "low" }];
  eq(L.slice().sort((a, b) => HL.confRank(a) - HL.confRank(b)).map((x) => x.id).join(""), "nlmh");
  const c = HL.confChips(L, "med"); eq(c.map((x) => x.label + x.n).join(" "), "All4 High1 Med1 Low1"); eq(c.filter((x) => x.on).map((x) => x.key).join(), "med");
  eq(HL.confChips(L, "").filter((x) => x.on)[0].label, "All");
  eq(L.filter((x) => HL.confMatch(x, "low")).map((x) => x.id).join(), "l"); eq(L.filter((x) => HL.confMatch(x, "")).length, 4); eq(L.filter((x) => HL.confMatch(x, "bogus")).length, 4);
});
await t("auto-posted: label, undo state, status filter keeps 14 days of auto-posts with open", async () => {
  const now = Date.parse("2026-11-06T18:00:00Z");
  const ap = HL.autoPosted({ auto_posted_at: "2026-11-06T15:00:00Z", status: "done" }); eq(ap.label, "Auto-posted Nov 6"); eq(ap.undone, false); eq(ap.undo, "Undo auto-post");
  eq(HL.autoPosted({ auto_posted_at: "2026-11-06T15:00:00Z", status: "new", zain_answer: "Undo auto-post" }).undone, true);
  eq(HL.autoPosted({ status: "open" }), null); eq(HL.autoPosted({ auto_posted_at: "nope" }), null);
  eq(HL.finStatus({ auto_posted_at: "2026-11-06T15:00:00Z", status: "done" }), "auto-posted"); eq(HL.finStatus({ status: "open" }), "open");
  eq(HL.finStatus({ auto_posted_at: "2026-11-06T15:00:00Z", status: "new", zain_answer: "Undo auto-post" }), "new");
  eq(HL.finStatusMatch({ auto_posted_at: "2026-11-01T15:00:00Z", status: "done" }, "open", now), true);
  eq(HL.finStatusMatch({ auto_posted_at: "2026-10-01T15:00:00Z", status: "done" }, "open", now), false);
  eq(HL.finStatusMatch({ auto_posted_at: "2026-10-01T15:00:00Z", status: "done" }, "auto-posted", now), true);
  eq(HL.finStatusMatch({ status: "done" }, "open", now), false); eq(HL.finStatusMatch({ status: "done" }, "", now), true);
});
await t("API v5: finance rows carry confidence + auto_posted_at; answer returns them for finance only", async () => {
  for (const pg of ["home", "finance"]) {
    const db = fakeDb(); await dataGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/data?page=" + pg), env: { HUB_DB: db }, data: { hubEmail: EMAIL } });
    const q = db.log.filter((x) => x[0].includes("FROM finance_questions")); eq(q.length > 0, true, pg);
    for (const x of q) eq(x[0].includes("confidence, auto_posted_at"), true, pg);
  }
  const a = apiCtx(AU, { body: { kind: "finance", id: "f1", answer: "Undo auto-post" } }); eq((await answerPost(a.ctx)).status, 200); eq(a.db.log[0][0].includes("answered_at, confidence, auto_posted_at"), true);
  const b = apiCtx(AU, { body: { kind: "need", id: "n1", answer: "Yes" } }); eq((await answerPost(b.ctx)).status, 200); eq(b.db.log[0][0].includes("confidence"), false);
  const c = apiCtx(AU, { body: { kind: "finance", id: "f1", undo: true } }); eq((await answerPost(c.ctx)).status, 200); eq(c.db.log[0][0].includes("RETURNING id, status, confidence, auto_posted_at"), true);
  const sch = readFileSync(new URL("./hub_schema.sql", import.meta.url), "utf8"), mig = readFileSync(new URL("./hub_migrate_v5.sql", import.meta.url), "utf8");
  for (const s of [sch, mig]) { eq(s.includes("confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high','med','low'))"), true); eq(s.includes("auto_posted_at TEXT"), true); }
});

// A small fake DOM: enough of document/window for hub.js to draw a page from mock /api/hub data (text only, like the real page).
function fakeDom() {
  class N {
    constructor(tag) { this.tagName = tag ? tag.toUpperCase() : null; this.childNodes = []; this.parentNode = null; this.attrs = {}; this.listeners = {}; this.style = { setProperty() {} }; this.hidden = false; this.disabled = false; this.value = ""; this._cls = new Set(); this._text = ""; }
    get className() { return [...this._cls].join(" "); } set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); }
    get classList() { const s = this._cls; return { add: (...c) => c.forEach((x) => s.add(x)), remove: (...c) => c.forEach((x) => s.delete(x)), contains: (c) => s.has(c), toggle: (c, on) => { const v = on === undefined ? !s.has(c) : !!on; if (v) s.add(c); else s.delete(c); return v; } }; }
    get id() { return this.attrs.id || ""; } set id(v) { this.attrs.id = v; }
    get firstChild() { return this.childNodes[0] || null; } get lastChild() { return this.childNodes[this.childNodes.length - 1] || null; }
    get nextSibling() { const p = this.parentNode; return p ? p.childNodes[p.childNodes.indexOf(this) + 1] || null : null; }
    get textContent() { return this.tagName ? this.childNodes.map((c) => c.textContent).join("") : this._text; }
    set textContent(v) { if (!this.tagName) { this._text = String(v); return; } this.childNodes.forEach((c) => { c.parentNode = null; }); this.childNodes = []; if (v !== "") this.appendChild(new N(null))._text = String(v); }
    appendChild(c) { if (c.parentNode) c.parentNode.removeChild(c); c.parentNode = this; this.childNodes.push(c); return c; }
    removeChild(c) { const i = this.childNodes.indexOf(c); if (i >= 0) this.childNodes.splice(i, 1); c.parentNode = null; return c; }
    insertBefore(c, ref) { if (!ref) return this.appendChild(c); if (c.parentNode) c.parentNode.removeChild(c); c.parentNode = this; this.childNodes.splice(this.childNodes.indexOf(ref), 0, c); return c; }
    setAttribute(k, v) { if (k === "class") this.className = v; else this.attrs[k] = String(v); } getAttribute(k) { return k === "class" ? this.className : this.attrs[k] === undefined ? null : this.attrs[k]; }
    addEventListener(e, f) { (this.listeners[e] = this.listeners[e] || []).push(f); }
    dispatch(e, ev = {}) { (this.listeners[e] || []).forEach((f) => f({ preventDefault() {}, key: "", ...ev })); }
    click() { if (!this.disabled) this.dispatch("click"); }
    focus() {} scrollIntoView() {} getBoundingClientRect() { return { top: 0, left: 0, width: 0, height: 0 }; }
    get offsetHeight() { return 0; } get scrollHeight() { return 0; } get clientHeight() { return 0; }
    get options() { return this.childNodes; }
    matches(sel) { return sel.split(",").some((s) => matchChain(this, s.trim().split(/\s+/))); }
    closest(sel) { let n = this; while (n && n.tagName) { if (n.matches(sel)) return n; n = n.parentNode; } return null; }
    querySelectorAll(sel) { const out = []; const walk = (n) => n.childNodes.forEach((c) => { if (c.tagName) { if (c.matches(sel)) out.push(c); walk(c); } }); walk(this); return out; }
    querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
  }
  const one = (n, s) => { const m = /^([a-z0-9]*)((?:\.[\w-]+)*)(?:\[([\w-]+)="([^"]*)"\])?$/i.exec(s); if (!m) throw new Error("selector " + s);
    return (!m[1] || n.tagName === m[1].toUpperCase()) && (m[2] ? m[2].slice(1).split(".") : []).every((c) => n._cls.has(c)) && (!m[3] || n.getAttribute(m[3]) === m[4]); };
  const matchChain = (n, parts) => { if (!one(n, parts[parts.length - 1])) return false; let rest = parts.slice(0, -1), p = n.parentNode; while (rest.length && p && p.tagName) { if (one(p, rest[rest.length - 1])) rest = rest.slice(0, -1); p = p.parentNode; } return !rest.length; };
  const html = new N("html"), body = html.appendChild(new N("body"));
  const document = { body, documentElement: html, createElement: (t) => new N(t), createElementNS: (ns, t) => new N(t), createTextNode: (t) => { const x = new N(null); x._text = String(t); return x; },
    getElementById: (id) => findId(body, id), querySelector: (s) => body.querySelector(s) };
  const findId = (n, id) => { for (const c of n.childNodes) { if (!c.tagName) continue; if (c.attrs.id === id) return c; const f = findId(c, id); if (f) return f; } return null; };
  function Option(text, value) { const o = new N("option"); o.textContent = text; o.value = value; return o; }
  return { N, document, body, Option };
}
// a hub page shell like tools/build_hub.py: sections with .pn-h h2 + #<id>Sub
function hubPage(page, mock, hash = "") {
  mock = JSON.parse(JSON.stringify(mock)); // hub.js updates the items it renders; every page gets its own copy
  const D = fakeDom(), { document, body, N } = D, main = new N("main"), mk = (tag, cls, id, parent) => { const n = new N(tag); if (cls) n.className = cls; if (id) n.id = id; (parent || main).appendChild(n); return n; };
  body.setAttribute("data-page", page); mk("span", "hub-status", "hubStatus", body); main.className = "hub-main"; body.appendChild(main);
  mk("div", "rbar", "rbar"); mk("div", "kpis", "kpis");
  const pn = (id) => { const s = mk("section", "pn"), h = mk("div", "pn-h", null, s); mk("h2", null, null, h); mk("span", "sub", id + "Sub", h); return mk("div", "pn-b", id, s); };
  if (page === "finance") { pn("finAsk"); mk("div", null, "finFilter").hidden = true; mk("div", "confwrap", "finConf").hidden = true; pn("finTxn"); pn("finOther"); }
  if (page === "board") { pn("agents"); pn("needs"); pn("ideas"); pn("activity"); }
  const posts = [], location = { hash, reload() {} };
  const fetch = async (url, o = {}) => {
    const u = String(url), json = (j) => ({ ok: true, status: 200, json: async () => j });
    if (o.method === "POST") { const b = JSON.parse(o.body); posts.push([u, b]); return json({ ok: true, item: { id: b.id, status: b.undo ? "open" : "new", answer: b.answer || null, answered_at: new Date().toISOString() } }); }
    const pg = /page=(\w+)/.exec(u); return json({ ok: true, page: pg && pg[1], links: [], comments: [], ...(mock[pg && pg[1]] || {}) });
  };
  const win = { document, location, fetch, Node: N, Option: D.Option, URL, encodeURIComponent, decodeURIComponent, setTimeout, clearTimeout, setInterval: () => 0, clearInterval() {}, innerWidth: 1440, innerHeight: 900, scrollY: 0,
    matchMedia: () => ({ matches: true }), addEventListener() {}, console };
  win.window = win; win.globalThis = win; vm.createContext(win);
  vm.runInContext(readFileSync(new URL("../site/hub/hub_links.js", import.meta.url), "utf8"), win);
  vm.runInContext(readFileSync(new URL("../site/hub/hub.js", import.meta.url), "utf8"), win);
  const $ = (id) => document.getElementById(id);
  return { $, posts, location, settle: async () => { for (let i = 0; i < 20; i++) await new Promise((r) => setImmediate(r)); } };
}
const apAt = new Date(Date.now() - 2 * 864e5).toISOString();
const apLabel = "Auto-posted " + new Date(apAt).toLocaleDateString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric" });
const FQ = (id, payee, date, conf, o = {}) => ({ id, created_at: "2026-11-05T12:00:00Z", question: `${payee}: $46.00 spend on ${date}, Card ••1234 (bank text: ${payee}) Note: business or personal?`, suggested_answer: "Business · Meals", suggestions: ["Business · Meals", "Personal"], status: "open", zain_answer: null, answered_at: null, agent_note: null, kind: "txn", confidence: conf, auto_posted_at: null, ...o });
const FIN = [FQ("t-low", "Tous Les Jours", "2026-11-02", "low"), FQ("t-med", "Staples", "2026-10-30", "med"), FQ("t-none", "Wawa", "2026-10-15", null),
  FQ("t-ap", "Adobe", "2026-11-03", "high", { status: "done", auto_posted_at: apAt, suggested_answer: "Business · Software", agent_note: "Rule: decisions.md, Adobe = Software" }),
  FQ("t-old-ap", "Zoom", "2026-09-03", "high", { status: "done", auto_posted_at: "2026-09-04T12:00:00Z" }),
  { ...FQ("o-high", "x", "2026-11-01", "high"), kind: "other", question: "Match the Upwork payout to INV-1042?", suggestions: ["Yes, match it", "No"] },
  { ...FQ("o-low", "x", "2026-11-01", "low"), kind: "other", question: "Create a Loan from owner account?", suggestions: ["Yes", "No"] }];
const rowsOf = (host) => host.querySelectorAll("tbody tr").filter((r) => !r._cls.has("total"));
await t("render: Finance page shows a colored badge per rated item and nothing for unrated", async () => {
  const P = hubPage("finance", { finance: { finance: FIN, needs: [] } }); await P.settle();
  const tx = P.$("finTxn"), rows = rowsOf(tx);
  eq(rows.length, 4, "open + recent auto-post (the 60-day-old auto-post is out of the default view)");
  const badge = (r) => { const b = r.querySelector("span.conf"); return b ? b.className + "=" + b.textContent : "-"; };
  eq(rows.map(badge).join(" | "), "- | conf conf-low=Low | conf conf-med=Med | conf conf-high=High", "Low/unrated first, then Med, then High");
  eq(rows[0].textContent.includes("Wawa"), true); eq(rows[1].textContent.includes("Tous Les Jours"), true);
  const oth = P.$("finOther"); eq(oth.querySelectorAll("span.conf").map((b) => b.textContent).join(","), "Low,High", "other questions: Low first");
});
await t("render: All / High / Med / Low chip row with counts; #conf=low shows only Low", async () => {
  const P = hubPage("finance", { finance: { finance: FIN, needs: [] } }); await P.settle();
  const bar = P.$("finConf"); eq(bar.hidden, false);
  const chips = bar.querySelectorAll("button.chip"); eq(chips.map((c) => c.textContent).join(" "), "All6 High2 Med1 Low2");
  eq(chips[0].getAttribute("aria-pressed"), "true"); chips[3].click(); eq(P.location.hash, "conf=low");
  const L = hubPage("finance", { finance: { finance: FIN, needs: [] } }, "#conf=low"); await L.settle();
  eq(L.$("finConf").querySelector('button[aria-pressed="true"]').textContent, "Low2");
  eq(rowsOf(L.$("finTxn")).map((r) => r.querySelector("span.conf").textContent).join(), "Low"); eq(L.$("finOther").querySelectorAll("span.conf").map((b) => b.textContent).join(), "Low");
  const E = hubPage("finance", { finance: { finance: FIN, needs: [] } }, "#conf=med"); await E.settle(); eq(E.$("finOther").textContent.includes("No Med confidence questions here."), true);
});
await t("render: auto-posted rows show 'Auto-posted <date>' muted, one Undo? chip that sends 'Undo auto-post'", async () => {
  const P = hubPage("finance", { finance: { finance: FIN, needs: [] } }); await P.settle();
  const row = rowsOf(P.$("finTxn")).filter((r) => r.textContent.includes("Adobe"))[0], ans = row.querySelector("div.ans");
  eq(ans._cls.has("ap"), true); eq(ans.querySelector("div.ap-l").textContent, apLabel);
  const chips = ans.querySelectorAll("button.chip"); eq(chips.length, 1); eq(chips[0].textContent, "Undo?"); eq(chips[0]._cls.has("ghost"), true);
  eq(ans.querySelector("div.note").textContent, "Agent: Rule: decisions.md, Adobe = Software");
  chips[0].click(); await P.settle();
  eq(P.posts.length, 1); eq(P.posts[0][0], "/api/hub/answer"); eq(JSON.stringify(P.posts[0][1]), JSON.stringify({ kind: "finance", id: "t-ap", answer: "Undo auto-post" }));
  eq(ans.textContent.includes("Sent ✓ Undo auto-post"), true);
  const open = rowsOf(P.$("finTxn")).filter((r) => r.textContent.includes("Staples"))[0].querySelector("div.ans");
  eq(open._cls.has("ap"), false); eq(open.querySelectorAll("button.chip").map((c) => c.textContent).join(), "Business · Meals,Personal", "normal rows keep their one-tap chips");
  const U = hubPage("finance", { finance: { finance: FIN.map((f) => f.id === "t-ap" ? { ...f, status: "new", zain_answer: "Undo auto-post" } : f), needs: [] } }, "#status=new"); await U.settle();
  const ua = rowsOf(U.$("finTxn")).filter((r) => r.textContent.includes("Adobe"))[0];
  eq(ua ? ua.querySelector("div.ap-l").textContent : "", apLabel + " · undo asked"); eq(ua.querySelectorAll("button.chip").length, 0);
  const S = hubPage("finance", { finance: { finance: FIN, needs: [] } }, "#status=auto-posted"); await S.settle();
  eq(rowsOf(S.$("finTxn")).map((r) => /Adobe|Zoom/.exec(r.textContent)[0]).sort().join(), "Adobe,Zoom", "status=auto-posted lists every auto-post");
});
await t("render: Board finance cards get badges, the chip row, Low first, and quick Undo? on auto-posts", async () => {
  const fo = FIN.filter((f) => f.id !== "t-old-ap").map((f) => f.id === "t-ap" ? { ...f, status: "seen" } : f);
  const P = hubPage("board", { board: { agents: [], ideas: [], activity: [], logRecent: [], logMin: [], needs: [{ id: "n1", created_at: "2026-11-05T12:00:00Z", source: "agent", agent: "Ads", title: "Approve the new ad copy?", detail: "", suggestions: [], status: "open" }] }, home: { financeOpen: fo }, calendar: { calendar: [] } });
  await P.settle();
  const nh = P.$("needs"), cards = nh.querySelectorAll("article.card");
  eq(cards.length, 7, "1 agent approval + 6 finance cards");
  eq(nh.querySelector("div.confbar").querySelectorAll("button.chip").map((c) => c.textContent).join(" "), "All7 High2 Med1 Low2");
  const lv = cards.map((c) => { const b = c.querySelector("span.conf"); return b ? b.textContent : "-"; });
  eq(lv.indexOf("Med") > lv.lastIndexOf("Low"), true, lv.join()); eq(lv.indexOf("High") > lv.indexOf("Med"), true, lv.join());
  const ap = cards.filter((c) => c.textContent.includes("Adobe"))[0]; eq(ap.querySelector("div.ap-l").textContent, apLabel); eq(ap.querySelectorAll("button.chip").map((c) => c.textContent).join(), "Undo?");
  const L = hubPage("board", { board: { agents: [], ideas: [], activity: [], logRecent: [], logMin: [], needs: [] }, home: { financeOpen: fo }, calendar: { calendar: [] } }, "#conf=high"); await L.settle();
  eq(L.$("needs").querySelectorAll("article.card").map((c) => c.querySelector("span.conf").textContent).join(), "High,High");
});

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
