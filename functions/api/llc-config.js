// GET /api/llc-config -> tells the LLC page whether card checkout is switched on.
// Keys live only in Cloudflare Pages env vars (set by Zain): STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY.
export async function onRequestGet({ env }) {
  const pk = env.STRIPE_PUBLISHABLE_KEY || "";
  const on = !!(env.STRIPE_SECRET_KEY && pk);
  return Response.json({ enabled: on, pk: on ? pk : null, mode: pk.startsWith("pk_test") ? "test" : "live" },
    { headers: { "Cache-Control": "no-store" } });
}

