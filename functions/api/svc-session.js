// GET /api/svc-session?session_id=cs_... -> safe summary for /checkout/thanks/.
import { stripe } from "../_shared/stripe.js";
export async function onRequestGet({ request, env }) {
  const id = new URL(request.url).searchParams.get("session_id") || "";
  if (!env.STRIPE_SECRET_KEY || !/^cs_[A-Za-z0-9_]+$/.test(id)) return Response.json({ error: "bad_request" }, { status: 400 });
  try {
    const s = await stripe(env, "GET", "checkout/sessions/" + id);
    const m = s.metadata || {};
    if (!m.service_id) return Response.json({ error: "not_found" }, { status: 404 });
    return Response.json({ status: s.status, paid: s.payment_status === "paid", amount: (s.amount_total || 0) / 100,
      email: s.customer_details && s.customer_details.email, name: m.name, phone: m.phone, service: m.service, qty: m.qty,
      extra: m.extra, notes: m.notes }, { headers: { "Cache-Control": "no-store" } });
  } catch (e) { return Response.json({ error: "stripe" }, { status: 424 }); }
}
