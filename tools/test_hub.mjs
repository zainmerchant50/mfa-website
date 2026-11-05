// Local tests for the MFA Hub gate and API (run: node tools/test_hub.mjs). Uses a generated RSA key, no network.
import { verifyAccessJwt, _clearCertCache } from "../functions/_shared/hub_auth.js";
import { onRequest as middleware, hubPathCheck } from "../functions/_middleware.js";
import { onRequestPost as commentPost } from "../functions/api/hub/comment.js";
import { onRequestPost as financePost } from "../functions/api/hub/finance-answer.js";
import { onRequestGet as dataGet } from "../functions/api/hub/data.js";

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
function fakeDb() {
  const log = [];
  return { log, prepare(sql) { return { bind(...a) { return { async first() { log.push([sql, a]); if (sql.startsWith("UPDATE")) return a[0] === "missing" ? null : { id: a[0], status: "new", zain_answer: a[1], answered_at: "2026-11-05T00:00:00Z" }; return { id: 1, created_at: "2026-11-05T00:00:00Z", status: "new" }; }, async all() { log.push([sql, a]); return { results: [] }; } }; }, async first() { return { n: 0 }; } }; } };
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
await t("finance answer: accepted and sets status new", async () => { const { ctx, db } = apiCtx(FU, { body: { id: "1843-20260917-9b0678", answer: "Business · Advisory/Consulting Income" } }); const r = await financePost(ctx); eq(r.status, 200); eq((await r.json()).question.status, "new"); eq(db.log[0][0].includes("status = 'new'"), true); });
await t("finance answer: cross-origin rejected", async () => { const { ctx, db } = apiCtx(FU, { body: { id: "x1", answer: "y" }, origin: "https://evil.example" }); eq((await financePost(ctx)).status, 403); eq(db.log.length, 0); });
await t("finance answer: unknown id -> 404", async () => { const { ctx } = apiCtx(FU, { body: { id: "missing", answer: "y" } }); eq((await financePost(ctx)).status, 404); });
await t("data: no Access identity -> 403", async () => { const r = await dataGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/data?page=board"), env: { HUB_DB: fakeDb() }, data: {} }); eq(r.status, 403); });
await t("data: unknown page -> 400", async () => { const r = await dataGet({ request: new Request("https://hub.mfa-advisory.com/api/hub/data?page=x"), env: { HUB_DB: fakeDb() }, data: { hubEmail: EMAIL } }); eq(r.status, 400); });

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
