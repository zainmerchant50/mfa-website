// Helpers for /api/hub/* (MFA Hub). The site middleware has already verified the Access JWT and
// set ctx.data.hubEmail; every handler checks it again so a routing mistake can't open the API.
export const PAGES = ["home", "board", "calendar", "ads", "finance", "leads", "tasks", "log"];

export function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store, private, max-age=0", "X-Robots-Tag": "noindex, nofollow" },
  });
}

export function authed(ctx) {
  return typeof ctx.data?.hubEmail === "string" && ctx.data.hubEmail.length > 3;
}

// CSRF: the browser must say this POST comes from this same origin, as JSON, with our header.
export function sameOrigin(request) {
  const url = new URL(request.url);
  const origin = request.headers.get("Origin");
  if (!origin || origin !== url.origin) return false;
  const sfs = request.headers.get("Sec-Fetch-Site");
  if (sfs && sfs !== "same-origin") return false;
  const ct = (request.headers.get("Content-Type") || "").toLowerCase();
  if (!ct.startsWith("application/json")) return false;
  if (request.headers.get("X-MFA-Hub") !== "1") return false;
  return true;
}

export async function readJson(request, maxBytes = 16384) {
  const len = Number(request.headers.get("Content-Length") || 0);
  if (len > maxBytes) throw new Error("too large");
  const t = await request.text();
  if (t.length > maxBytes) throw new Error("too large");
  const j = JSON.parse(t);
  if (!j || typeof j !== "object" || Array.isArray(j)) throw new Error("bad body");
  return j;
}

export function cleanText(v, max) {
  if (typeof v !== "string") return null;
  const s = v.replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "").trim();
  return s && s.length <= max ? s : null;
}

export const REF_RE = /^[A-Za-z0-9_:.\-+@~]{1,200}$/;

// JSON array of short strings from D1 -> safe array (max 8 items, 120 chars each).
export function parseSuggestions(s) {
  try {
    const a = JSON.parse(s || "[]");
    return Array.isArray(a) ? a.filter((x) => typeof x === "string" && x.trim() && x.length <= 120).slice(0, 8) : [];
  } catch (e) { return []; }
}

// One live-log line for something Zain did in the hub (agents write their own lines straight to D1).
export function logStmt(db, action, detail, link = null) {
  return db.prepare("INSERT INTO log (agent, action, detail, link) VALUES ('Zain (hub)', ?1, ?2, ?3)")
    .bind(String(action).slice(0, 80), String(detail || "").slice(0, 400), link);
}

export async function guardPost(ctx) {
  if (!authed(ctx)) return json({ ok: false, error: "forbidden" }, 403);
  if (!sameOrigin(ctx.request)) return json({ ok: false, error: "cross-origin request refused" }, 403);
  if (!ctx.env.HUB_DB) return json({ ok: false, error: "database not bound" }, 503);
  return null;
}
