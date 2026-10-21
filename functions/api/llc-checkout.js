// POST /api/llc-checkout -> creates a Stripe Checkout Session (embedded) for an LLC formation order.
// The amount is always computed here from the published prices (never trusted from the browser).
import PRICING from "../_shared/llc-pricing.js";
import { stripe } from "../_shared/stripe.js";

const EMAIL = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;
const clip = (s, n = 400) => String(s || "").trim().slice(0, n);

export function buildOrder(body) {
  const pkg = PRICING.packages[body.package];
  const st = PRICING.states[String(body.state || "").toUpperCase()];
  const errs = [];
  if (clip(body.name).length < 2) errs.push("name");
  if (!EMAIL.test(clip(body.email))) errs.push("email");
  if (!pkg) errs.push("package");
  if (!st) errs.push("state");
  if (clip(body.llc_name).length < 2) errs.push("llc_name");
  if (clip(body.activity).length < 2) errs.push("activity");
  if (errs.length) return { errs };
  const lines = [{ name: `${pkg.name} (MFA LLC formation package)`, amount: pkg.price * 100 }];
  if (st.fee != null) lines.push({ name: `${st.name} state filing fee (paid to the state at cost)`, amount: Math.round(st.fee * 100) });
  if (st.extra) lines.push({ name: `${st.name} fees also due at formation (paid to the state at cost)`, amount: Math.round(st.extra * 100) });
  if (st.pub_fee) lines.push({ name: `${st.name} Certificate of Publication fee (paid to the state at cost)`, amount: Math.round(st.pub_fee * 100) });
  const total = lines.reduce((a, l) => a + l.amount, 0);
  return { pkg, st, lines, total, feeKnown: st.fee != null };
}

export async function onRequestPost({ request, env }) {
  if (!env.STRIPE_SECRET_KEY) return Response.json({ error: "payments_off" }, { status: 503 });
  let body;
  try { body = await request.json(); } catch { return Response.json({ error: "bad_json" }, { status: 400 }); }
  const o = buildOrder(body);
  if (o.errs) return Response.json({ error: "invalid", fields: o.errs }, { status: 422 });
  const origin = new URL(request.url).origin;
  const meta = {
    name: clip(body.name, 200), phone: clip(body.phone, 40), state: o.st.code, package: body.package,
    llc_name: clip(body.llc_name, 200), backup_name: clip(body.backup_name, 200), owners: clip(body.owners, 40),
    managed_by: clip(body.managed_by, 80), activity: clip(body.activity, 400), will_hire: body.will_hire ? "yes" : "no",
    sells_taxable: body.sells_taxable ? "yes" : "no", has_agent: body.has_agent ? "yes" : "no",
    s_corp_interest: body.s_corp_interest ? "yes" : "no", monthly_bookkeeping: body.monthly_bookkeeping ? "yes" : "no",
    notes: clip(body.notes, 480), state_fee_confirmed: o.feeKnown ? "yes" : "no (charge separately at cost)",
  };
  const params = {
    mode: "payment", ui_mode: "embedded",
    return_url: `${origin}/llc-formation/thanks/?session_id={CHECKOUT_SESSION_ID}`,
    customer_email: clip(body.email, 200),
    billing_address_collection: "auto",
    submit_type: "pay",
    metadata: meta,
    payment_intent_data: { description: `LLC formation: ${o.pkg.name} / ${o.st.name} / ${meta.llc_name}`, metadata: meta },
    custom_text: { submit: { message: "If we can't file your LLC (for example, the name isn't available), we refund you in full. State fees can't be refunded once the state accepts the filing." } },
    line_items: Object.fromEntries(o.lines.map((l, i) => [i, { quantity: 1, price_data: { currency: "usd", unit_amount: l.amount, product_data: { name: l.name } } }])),
  };
  try {
    const s = await stripe(env, "POST", "checkout/sessions", params);
    return Response.json({ clientSecret: s.client_secret, total: o.total / 100, lines: o.lines, feeKnown: o.feeKnown });
  } catch (e) {
    return Response.json({ error: "stripe", message: String(e.message || e) }, { status: 502 });
  }
}
