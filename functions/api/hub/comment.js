// POST /api/hub/comment  {page, item_ref, body}  -> saves a comment for the agents (status 'new').
import { guardPost, json, readJson, cleanText, PAGES, REF_RE } from "../../_shared/hub_api.js";

export async function onRequestPost(ctx) {
  const bad = await guardPost(ctx);
  if (bad) return bad;
  let b;
  try { b = await readJson(ctx.request); } catch (e) { return json({ ok: false, error: "bad request" }, 400); }
  const page = PAGES.includes(b.page) ? b.page : null;
  const ref = typeof b.item_ref === "string" && REF_RE.test(b.item_ref) ? b.item_ref : null;
  const body = cleanText(b.body, 4000);
  if (!page || !ref || !body) return json({ ok: false, error: "page, item_ref and a comment (max 4000 characters) are required" }, 400);
  const row = await ctx.env.HUB_DB.prepare(
    "INSERT INTO comments (page, item_ref, body) VALUES (?1, ?2, ?3) RETURNING id, created_at, status"
  ).bind(page, ref, body).first();
  return json({ ok: true, comment: { ...row, page, item_ref: ref, body, agent_note: null } });
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
