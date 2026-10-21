// GET /api/llc-config -> tells the LLC page whether card checkout is switched on.
// Keys live only in Cloudflare Pages env vars (set by Zain): STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY.
export async function onRequestGet({ env }) {
  const pk = env.STRIPE_PUBLISHABLE_KEY || "";
  const sk = env.STRIPE_SECRET_KEY || "";
  // Only switch checkout on when both keys look real (guards against a placeholder value).
  const on = /^sk_(live|test)_/.test(sk) && /^pk_(live|test)_/.test(pk) && sk.slice(3, 7) === pk.slice(3, 7);
  return Response.json({ enabled: on, pk: on ? pk : null, mode: pk.startsWith("pk_test") ? "test" : "live" },
    { headers: { "Cache-Control": "no-store" } });
}

