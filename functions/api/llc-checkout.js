// POST /api/llc-checkout -> creates an embedded Stripe Checkout Session for an LLC formation order.
// The cart on the page and this function use the SAME pricing code (site/resources/llc-order.js) and the
// same generated price list, and the amount is always recomputed here (the browser's numbers are never trusted).
// One-time items (package, state fees, one-time add-ons) are charged today. Monthly bookkeeping, if chosen,
// becomes a Stripe subscription whose first charge is 30 days after checkout.
import PRICING from "../_shared/llc-pricing.js";
import { selectionFromForm, computeOrder } from "../../site/resources/llc-order.js";
import { stripe } from "../_shared/stripe.js";

const EMAIL = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;
const clip = (s, n = 400) => String(s || "").trim().slice(0, n);

export function buildOrder(body) {
  const sel = selectionFromForm(body || {});
  const o = computeOrder(PRICING, sel);
  const errs = [];
  if (clip(body.name).length < 2) errs.push("name");
  if (!EMAIL.test(clip(body.email))) errs.push("email");
  if (!o.pkg) errs.push("package");
  if (!o.st) errs.push("state");
  if (clip(body.llc_name).length < 2) errs.push("llc_name");
  if (clip(body.activity).length < 2) errs.push("activity");
  if (sel.bk.on && o.bk && o.bk.incomplete) errs.push("bk_accounts");
  return { sel, o, errs };
}

export async function onRequestPost({ request, env }) {
  if (!env.STRIPE_SECRET_KEY) return Response.json({ error: "payments_off" }, { status: 424 });
  let body;
  try { body = await request.json(); } catch { return Response.json({ error: "bad_json" }, { status: 400 }); }
  const { sel, o, errs } = buildOrder(body);
  if (errs.length) return Response.json({ error: "invalid", fields: errs }, { status: 422 });
  const origin = new URL(request.url).origin;
  const addons = [
    ...o.today.filter((l) => !["pkg", "fee", "extra", "pub"].includes(l.key)).map((l) => l.name),
    ...o.recurring.map((l) => l.name + " $" + l.amount / 100 + "/mo"),
    ...(o.bk && o.bk.quote ? ["Monthly bookkeeping: QUOTE NEEDED (" + sel.bk.accounts + " accounts, " + sel.bk.volume + " txns)"] : []),
  ].join("; ");
  const meta = {
    name: clip(body.name, 200), phone: clip(body.phone, 40), state: o.st.code, package: sel.package,
    llc_name: clip(body.llc_name, 200), backup_name: clip(body.backup_name, 200), owners: clip(body.owners, 40),
    managed_by: clip(body.managed_by, 80), activity: clip(body.activity, 400), will_hire: body.will_hire ? "yes" : "no",
    sells_taxable: body.sells_taxable ? "yes" : "no", has_agent: body.has_agent ? "yes" : "no",
    s_corp_interest: body.s_corp_interest ? "yes" : "no", addons: clip(addons, 480) || "none",
    monthly_bookkeeping: o.recurring.length ? "subscription" : (o.bk && o.bk.quote ? "quote" : "no"),
    notes: clip(body.notes, 480), state_fee_confirmed: o.st.fee != null ? "yes" : "no (charge separately at cost)",
  };
  const items = [...o.today, ...o.recurring];
  const sub = o.recurring.length > 0;
  const params = {
    mode: sub ? "subscription" : "payment", ui_mode: "embedded",
    return_url: `${origin}/llc-formation/thanks/?session_id={CHECKOUT_SESSION_ID}`,
    customer_email: clip(body.email, 200),
    billing_address_collection: "auto",
    metadata: meta,
    custom_text: { submit: { message: "If we can't file your LLC (for example, the name isn't available), we refund you in full. State fees can't be refunded once the state accepts the filing." + (sub ? " Monthly bookkeeping starts 30 days after today; cancel anytime." : "") } },
    line_items: Object.fromEntries(items.map((l, i) => [i, { quantity: 1, price_data: {
      currency: "usd", unit_amount: l.amount, product_data: { name: l.name },
      ...(l.interval ? { recurring: { interval: l.interval } } : {}) } }])),
  };
  if (sub) params.subscription_data = { trial_period_days: o.recurring[0].trial_days, description: `MFA monthly bookkeeping for ${meta.llc_name}`, metadata: meta };
  else { params.submit_type = "pay"; params.payment_intent_data = { description: `LLC formation: ${o.pkg.name} / ${o.st.name} / ${meta.llc_name}`, metadata: meta }; }
  try {
    const s = await stripe(env, "POST", "checkout/sessions", params);
    return Response.json({ clientSecret: s.client_secret, total: o.total / 100, recurring: o.recurring.map((l) => ({ name: l.name, amount: l.amount / 100 })), lines: o.today, feeKnown: o.st.fee != null });
  } catch (e) {
    return Response.json({ error: "stripe", message: String(e.message || e) }, { status: 424 });
  }
}
