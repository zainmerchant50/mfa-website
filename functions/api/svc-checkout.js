// POST /api/svc-checkout -> embedded Stripe Checkout Session for a fixed-price service (tools/build_offers.py SERVICES).
// The price list is generated server-side (../_shared/service-pricing.js); the browser only sends the service id and quantity.
import PRICES from "../_shared/service-pricing.js";
import { stripe } from "../_shared/stripe.js";

const EMAIL = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;
const clip = (s, n = 400) => String(s == null ? "" : s).trim().slice(0, n);

export function buildOrder(body) {
  const b = body || {};
  const svc = PRICES[clip(b.service, 40)];
  const errs = [];
  if (!svc) return { errs: ["service"] };
  if (clip(b.name).length < 2) errs.push("name");
  if (!EMAIL.test(clip(b.email, 200))) errs.push("email");
  let qty = 1;
  if (svc.per) {
    qty = parseInt(b.extra, 10);
    if (!Number.isFinite(qty)) qty = svc.min;
    qty = Math.max(svc.min, Math.min(svc.max, qty));
  }
  return { svc, qty, total: svc.amount * qty, errs };
}

export async function onRequestPost({ request, env }) {
  if (!env.STRIPE_SECRET_KEY) return Response.json({ error: "payments_off" }, { status: 424 });
  let body;
  try { body = await request.json(); } catch { return Response.json({ error: "bad_json" }, { status: 400 }); }
  const { svc, qty, total, errs } = buildOrder(body);
  if (errs.length) return Response.json({ error: "invalid", fields: errs }, { status: 422 });
  const origin = new URL(request.url).origin;
  const meta = { service_id: clip(body.service, 40), service: svc.name.slice(0, 450), qty: String(qty),
    name: clip(body.name, 200), phone: clip(body.phone, 40), extra: clip(body.extra, 200), notes: clip(body.notes, 480) };
  const params = {
    mode: "payment", ui_mode: "embedded", submit_type: "pay",
    return_url: `${origin}/checkout/thanks/?session_id={CHECKOUT_SESSION_ID}`,
    customer_email: clip(body.email, 200), billing_address_collection: "auto", metadata: meta,
    custom_text: { submit: { message: "If we review your details and can't take on the work, we refund you in full. We reply within 1-3 business days." } },
    line_items: { 0: { quantity: qty, price_data: { currency: "usd", unit_amount: svc.amount, product_data: { name: svc.name } } } },
    payment_intent_data: { description: `MFA: ${svc.name} x${qty} / ${meta.name}`.slice(0, 990), metadata: meta },
  };
  try {
    const s = await stripe(env, "POST", "checkout/sessions", params);
    return Response.json({ clientSecret: s.client_secret, total: total / 100 });
  } catch (e) {
    return Response.json({ error: "stripe", message: String(e.message || e) }, { status: 424 });
  }
}
