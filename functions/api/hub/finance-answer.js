// POST /api/hub/finance-answer  {id, answer}  -> saves Zain's answer; status 'new' so Finance picks it up.
import { guardPost, json, readJson, cleanText, REF_RE } from "../../_shared/hub_api.js";

export async function onRequestPost(ctx) {
  const bad = await guardPost(ctx);
  if (bad) return bad;
  let b;
  try { b = await readJson(ctx.request); } catch (e) { return json({ ok: false, error: "bad request" }, 400); }
  const id = typeof b.id === "string" && REF_RE.test(b.id) ? b.id : null;
  const answer = cleanText(b.answer, 2000);
  if (!id || !answer) return json({ ok: false, error: "id and an answer (max 2000 characters) are required" }, 400);
  const row = await ctx.env.HUB_DB.prepare(
    "UPDATE finance_questions SET zain_answer = ?2, answered_at = strftime('%Y-%m-%dT%H:%M:%SZ','now'), status = 'new', agent_note = NULL " +
    "WHERE id = ?1 RETURNING id, status, zain_answer, answered_at"
  ).bind(id, answer).first();
  if (!row) return json({ ok: false, error: "question not found" }, 404);
  return json({ ok: true, question: row });
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
