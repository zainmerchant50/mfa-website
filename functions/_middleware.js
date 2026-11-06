// Site-wide Pages middleware. Only job: keep the private MFA Hub private.
// - Any request on hub.mfa-advisory.com, and any /hub* or /api/hub* path on any host, needs a valid
//   Cloudflare Access JWT (Cf-Access-Jwt-Assertion) for HUB_ALLOWED_EMAIL. See functions/_shared/hub_auth.js.
// - Without one: 404 (the normal site 404 page) on public hosts, 403 on the hub host. Fails closed.
// - Every other request on the public site passes straight through untouched.
import { verifyAccessJwt } from "./_shared/hub_auth.js";

const HUB_HOST = "hub.mfa-advisory.com";
const PRIVATE = {
  "X-Robots-Tag": "noindex, nofollow, noarchive, nosnippet",
  "Cache-Control": "no-store, private, max-age=0",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
  "X-Content-Type-Options": "nosniff",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
};
const CSP = "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; " +
  "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; " +
  "base-uri 'none'; form-action 'self'; object-src 'none'";

// Normalised path used only for the "is this private?" decision (decoded, lower-case, single slashes).
export function hubPathCheck(pathname) {
  let p;
  try { p = decodeURIComponent(pathname); } catch (e) { return true; } // undecodable -> treat as private
  p = p.toLowerCase().replace(/\\/g, "/").replace(/\/+/g, "/");
  return p.startsWith("/hub") || p.startsWith("/api/hub");
}

function withHeaders(res, extra) {
  const r = new Response(res.body, res);
  for (const [k, v] of Object.entries({ ...PRIVATE, ...extra })) r.headers.set(k, v);
  r.headers.delete("ETag");
  r.headers.delete("Last-Modified");
  return r;
}

async function deny(ctx, onHubHost) {
  if (onHubHost) {
    return new Response("Forbidden", { status: 403, headers: { ...PRIVATE, "Content-Type": "text/plain; charset=utf-8" } });
  }
  // Look exactly like any other missing page on the public site.
  try {
    const nf = await ctx.env.ASSETS.fetch(new Request(new URL("/__no-such-page__/", ctx.request.url)));
    const body = nf.status === 404 ? await nf.text() : "Not found";
    return new Response(body, { status: 404, headers: { ...PRIVATE, "Content-Type": nf.headers.get("Content-Type") || "text/html; charset=utf-8" } });
  } catch (e) {
    return new Response("Not found", { status: 404, headers: { ...PRIVATE, "Content-Type": "text/plain; charset=utf-8" } });
  }
}

// Junk probes (Cloudflare AI Crawl Control, Nov 2026: ~1k 4xx a week, mostly these): the old WordPress site's URLs
// (incl. a WordPress MCP endpoint, /wp-json/wp/v2/wpmcp/streamable, that some assistant client still polls), PHP
// scanners, dotfile and path-traversal probes, and the old theme's demo pages. They get a tiny, cacheable 410 Gone so
// crawlers drop them for good. Nothing is blocked: every real page and file is untouched. Never matches /.well-known/.
const JUNK = new RegExp([
  "^/(?:wp-[a-z]+|wp|wordpress|xmlrpc)(?:[/.]|$)",        // WordPress: wp-json, wp-admin, wp-login.php, wp-content, /wp/, xmlrpc.php
  "\\.php\\d?(?:/|$)",                                    // no PHP on this site
  "/\\.(?!well-known(?:/|$))[^/]+",                       // dotfiles and dot-dirs: /.env, /.git/, /.aws/credentials
  "(?:^|/)\\.\\.(?:/|$)|%2e%2e|/proc/self/|^/cgi-bin/",  // path traversal and server probes
  "^/(?:portfolio|header)/",                              // old WordPress theme demo pages (pre-Oct 2026)
].join("|"), "i");

export function junkPath(pathname) {
  return JUNK.test(pathname);
}

const GONE_HEADERS = {
  "Content-Type": "text/plain; charset=utf-8",
  "Cache-Control": "public, max-age=86400",
  "X-Robots-Tag": "noindex",
};

export async function onRequest(ctx) {
  const { request, env } = ctx;
  const url = new URL(request.url);
  const onHubHost = url.hostname.toLowerCase() === HUB_HOST;
  if (!onHubHost && junkPath(url.pathname)) {
    return new Response(request.method === "HEAD" ? null : "410 Gone: this URL is not part of mfa-advisory.com.\n", { status: 410, headers: GONE_HEADERS });
  }
  if (!onHubHost && !hubPathCheck(url.pathname)) return ctx.next(); // public site: untouched

  try {
    const res = await verifyAccessJwt(request.headers.get("Cf-Access-Jwt-Assertion"), env);
    if (!res.ok) return deny(ctx, onHubHost);
    ctx.data.hubEmail = res.email;
    if (onHubHost && (url.pathname === "/" || url.pathname === "")) {
      return new Response(null, { status: 302, headers: { ...PRIVATE, Location: "/hub/" } });
    }
    const out = await ctx.next();
    const ct = out.headers.get("Content-Type") || "";
    return withHeaders(out, ct.includes("text/html") ? { "Content-Security-Policy": CSP } : {});
  } catch (e) {
    return deny(ctx, onHubHost);
  }
}
