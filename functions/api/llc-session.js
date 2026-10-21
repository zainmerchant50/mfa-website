// GET /api/llc-session?session_id=cs_... -> safe summary for the thank-you page.
import { stripe } from "../_shared/stripe.js";
export async function onRequestGet({ request, env }) {
  const id = new URL(request.url).searchParams.get("session_id") || "";
  if (!env.STRIPE_SECRET_KEY || !/^cs_[A-Za-z0-9_]+$/.test(id)) return Response.json({ error: "bad_request" }, { status: 400 });
  try {
    const s = await stripe(env, "GET", "checkout/sessions/" + id);
    const m = s.metadata || {};
    return Response.json({ status: s.status, paid: s.payment_status === "paid", amount: (s.amount_total || 0) / 100,
      email: s.customer_details && s.customer_details.email, name: m.name, state: m.state, package: m.package,
      llc_name: m.llc_name, activity: m.activity, monthly_bookkeeping: m.monthly_bookkeeping, state_fee_confirmed: m.state_fee_confirmed },
      { headers: { "Cache-Control": "no-store" } });
  } catch (e) { return Response.json({ error: "stripe" }, { status: 502 }); }
}
