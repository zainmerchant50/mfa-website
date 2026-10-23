// Cloudflare Pages Function — one-click unsubscribe for the MFA Lead Engine.
// Install at:  functions/u/[[path]].js  in the mfa-website repo.
// Bindings:    KV namespace UNSUB, secret UNSUBSCRIBE_SECRET  (see README.md)

const PAGE = (title, body) => `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title>
<style>body{font:16px/1.5 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:480px;margin:12vh auto;padding:0 20px;color:#1f2937}
button{font:inherit;padding:10px 18px;border:0;border-radius:8px;background:#1d4ed8;color:#fff;cursor:pointer}
small{color:#6b7280}</style></head><body>${body}</body></html>`;

function tokenFromPath(url) {
  const parts = new URL(url).pathname.split("/").filter(Boolean); // ["u", "<token>"]
  return parts.length >= 2 && parts[0] === "u" ? parts[1] : null;
}

function looksLikeToken(t) {
  return typeof t === "string" && /^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$/.test(t);
}

async function record(env, token, request) {
  const ts = Math.floor(Date.now() / 1000);
  const key = `unsub:${ts}:${token.slice(0, 24)}`;
  const value = JSON.stringify({
    token,
    ts,
    ua: (request.headers.get("user-agent") || "").slice(0, 200),
    ip: request.headers.get("cf-connecting-ip") || "",
  });
  await env.UNSUB.put(key, value, { expirationTtl: 60 * 60 * 24 * 400 }); // keep ~13 months
  return ts;
}

export async function onRequestPost({ request, env }) {
  const token = tokenFromPath(request.url);
  if (!looksLikeToken(token)) return new Response("bad request", { status: 400 });
  if (!env.UNSUB) return new Response("not configured", { status: 503 });
  await record(env, token, request);
  const accept = request.headers.get("accept") || "";
  if (accept.includes("text/html")) {
    return new Response(PAGE("Unsubscribed", `<h2>You're unsubscribed.</h2>
<p>You won't receive further emails from Merchant Financial Advisory.</p>`),
      { headers: { "content-type": "text/html; charset=utf-8" } });
  }
  return new Response("unsubscribed", { status: 200 });
}

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const parts = url.pathname.split("/").filter(Boolean);

  // Public liveness probe: GET /u/health → "ok" only when KV and the secret are configured.
  if (parts[1] === "health") {
    const ready = !!(env.UNSUB && env.UNSUBSCRIBE_SECRET);
    return new Response(ready ? "ok" : "not configured", {
      status: ready ? 200 : 503, headers: { "cache-control": "no-store", "content-type": "text/plain" } });
  }

  // Lead-engine sync:  GET /u/list?after=<ts>  with Bearer secret
  // (also the engine's SAFETY LOCK health check: after=<far future> → 200 [] proves URL + KV + secret)
  if (parts[1] === "list") {
    if (!env.UNSUB) return new Response("not configured", { status: 503 });
    const auth = request.headers.get("authorization") || "";
    if (!env.UNSUBSCRIBE_SECRET || auth !== `Bearer ${env.UNSUBSCRIBE_SECRET}`) {
      return new Response("unauthorized", { status: 401 });
    }
    const after = parseInt(url.searchParams.get("after") || "0", 10) || 0;
    const out = [];
    let cursor;
    do {
      const page = await env.UNSUB.list({ prefix: "unsub:", cursor });
      for (const k of page.keys) {
        const ts = parseInt(k.name.split(":")[1], 10);
        if (ts > after) {
          const v = await env.UNSUB.get(k.name);
          if (v) out.push(JSON.parse(v));
        }
      }
      cursor = page.list_complete ? undefined : page.cursor;
    } while (cursor);
    out.sort((a, b) => a.ts - b.ts);
    return new Response(JSON.stringify(out), {
      headers: { "content-type": "application/json", "cache-control": "no-store" } });
  }

  // Human visit from the footer link: confirm with a button. GET never unsubscribes (Google's rule).
  const token = tokenFromPath(request.url);
  if (!looksLikeToken(token)) return new Response("not found", { status: 404 });
  return new Response(PAGE("Unsubscribe", `<h2>Unsubscribe from Merchant Financial Advisory emails?</h2>
<form method="post"><button type="submit">Yes, unsubscribe me</button></form>
<p><small>Or simply reply STOP to any of our emails.</small></p>`),
    { headers: { "content-type": "text/html; charset=utf-8" } });
}
