// MFA Hub: Cloudflare Access JWT verification (RS256, WebCrypto, no dependencies).
// Settings come from Pages env vars only:
//   ACCESS_TEAM_DOMAIN  e.g. "super-voice-466f" or "super-voice-466f.cloudflareaccess.com"
//   ACCESS_AUD          the Access application's AUD tag
//   HUB_ALLOWED_EMAIL   the one email allowed in (zainmerchant@mfa-advisory.com)
// Anything missing or unexpected -> not ok (fail closed).

const LEEWAY = 60; // seconds of clock skew allowed
const certCache = new Map(); // team host -> { keys, fetchedAt }

export function teamHost(v) {
  const s = String(v || "").trim().toLowerCase().replace(/^https?:\/\//, "").replace(/\/.*$/, "");
  const name = s.endsWith(".cloudflareaccess.com") ? s.slice(0, -".cloudflareaccess.com".length) : s;
  return /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(name) ? `${name}.cloudflareaccess.com` : null;
}

function b64urlBytes(s) {
  if (typeof s !== "string" || !/^[A-Za-z0-9_-]*$/.test(s)) throw new Error("bad b64url");
  const b = atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4));
  const out = new Uint8Array(b.length);
  for (let i = 0; i < b.length; i++) out[i] = b.charCodeAt(i);
  return out;
}
const b64urlJson = (s) => JSON.parse(new TextDecoder().decode(b64urlBytes(s)));

async function defaultFetchCerts(host) {
  const r = await fetch(`https://${host}/cdn-cgi/access/certs`, { cf: { cacheTtl: 300 } });
  if (!r.ok) throw new Error("certs " + r.status);
  return r.json();
}

async function getKeys(host, fetchCerts, force) {
  const c = certCache.get(host);
  const now = Date.now();
  if (c && !force && now - c.fetchedAt < 3600e3) return c.keys;
  if (c && force && now - c.fetchedAt < 60e3) return c.keys; // refetch at most once a minute
  const j = await fetchCerts(host);
  const keys = Array.isArray(j && j.keys) ? j.keys.filter((k) => k && k.kty === "RSA" && k.kid && k.n && k.e) : [];
  certCache.set(host, { keys, fetchedAt: now });
  return keys;
}

export function _clearCertCache() { certCache.clear(); }

export async function verifyAccessJwt(token, env, opts = {}) {
  const fail = (reason) => ({ ok: false, reason });
  try {
    const host = teamHost(env.ACCESS_TEAM_DOMAIN);
    const aud = String(env.ACCESS_AUD || "").trim();
    const allowed = String(env.HUB_ALLOWED_EMAIL || "").trim().toLowerCase();
    if (!host || !/^[a-f0-9]{32,128}$/i.test(aud) || !/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/.test(allowed)) return fail("not configured");
    if (typeof token !== "string" || token.length > 8192) return fail("no token");
    const parts = token.split(".");
    if (parts.length !== 3 || !parts[0] || !parts[1] || !parts[2]) return fail("malformed");
    const header = b64urlJson(parts[0]);
    const payload = b64urlJson(parts[1]);
    if (!header || header.alg !== "RS256" || typeof header.kid !== "string") return fail("bad header");

    const fetchCerts = opts.fetchCerts || defaultFetchCerts;
    let keys = await getKeys(host, fetchCerts, false);
    let jwk = keys.find((k) => k.kid === header.kid);
    if (!jwk) { keys = await getKeys(host, fetchCerts, true); jwk = keys.find((k) => k.kid === header.kid); }
    if (!jwk) return fail("unknown kid");

    const key = await crypto.subtle.importKey("jwk", { kty: "RSA", n: jwk.n, e: jwk.e, alg: "RS256", ext: true },
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    const sigOk = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64urlBytes(parts[2]),
      new TextEncoder().encode(parts[0] + "." + parts[1]));
    if (!sigOk) return fail("bad signature");

    const now = Math.floor((opts.now || Date.now()) / 1000);
    if (!payload || typeof payload !== "object") return fail("bad payload");
    if (payload.iss !== `https://${host}`) return fail("bad iss");
    const auds = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
    if (!auds.includes(aud)) return fail("bad aud");
    if (typeof payload.exp !== "number" || payload.exp + LEEWAY < now) return fail("expired");
    if (typeof payload.nbf === "number" && payload.nbf - LEEWAY > now) return fail("not yet valid");
    if (typeof payload.iat === "number" && payload.iat - LEEWAY > now) return fail("issued in future");
    if (payload.type !== undefined && payload.type !== "app") return fail("bad type");
    const email = String(payload.email || "").trim().toLowerCase();
    if (!email || email !== allowed) return fail("email not allowed");
    return { ok: true, email, payload };
  } catch (e) {
    return fail("error");
  }
}
