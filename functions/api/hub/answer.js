// POST /api/hub/answer {kind: 'finance'|'need', id, answer}  -> saves Zain's answer (chip or typed), status 'new'.
// POST /api/hub/answer {kind, id, undo: true}               -> takes it back if no agent has picked it up and
//                                                              it was given in the last 60 seconds.
import { guardPost, json, readJson, cleanText, logStmt, REF_RE } from "../../_shared/hub_api.js";

// extra: columns only finance_questions has (v5), returned with the saved row
const T = { finance: { table: "finance_questions", col: "zain_answer", label: "finance", extra: ", confidence, auto_posted_at" }, need: { table: "needs", col: "answer", label: "needs-you", extra: "" } };

export async function saveAnswer(ctx, kind, id, answer) {
  const t = T[kind];
  const db = ctx.env.HUB_DB;
  const row = await db.prepare(
    `UPDATE ${t.table} SET ${t.col} = ?2, answered_at = strftime('%Y-%m-%dT%H:%M:%SZ','now'), status = 'new', agent_note = NULL ` +
    `WHERE id = ?1 RETURNING id, status, ${t.col} AS answer, answered_at${t.extra}`
  ).bind(id, answer).first();
  if (!row) return json({ ok: false, error: "item not found" }, 404);
  await logStmt(db, "answered", `${t.label} ${id}: ${answer.slice(0, 200)}`).run();
  return json({ ok: true, item: row });
}

export async function onRequestPost(ctx) {
  const bad = await guardPost(ctx);
  if (bad) return bad;
  let b;
  try { b = await readJson(ctx.request); } catch (e) { return json({ ok: false, error: "bad request" }, 400); }
  const kind = Object.prototype.hasOwnProperty.call(T, b.kind) ? b.kind : null;
  const id = typeof b.id === "string" && REF_RE.test(b.id) ? b.id : null;
  if (!kind || !id) return json({ ok: false, error: "kind and id are required" }, 400);
  if (b.undo === true) {
    const t = T[kind];
    const db = ctx.env.HUB_DB;
    const row = await db.prepare(
      `UPDATE ${t.table} SET ${t.col} = NULL, answered_at = NULL, status = 'open' ` +
      `WHERE id = ?1 AND status = 'new' AND answered_at >= strftime('%Y-%m-%dT%H:%M:%SZ','now','-60 seconds') RETURNING id, status${t.extra}`
    ).bind(id).first();
    if (!row) return json({ ok: false, error: "too late to undo (an agent may have it already)" }, 409);
    await logStmt(db, "undo", `${t.label} ${id}: answer taken back`).run();
    return json({ ok: true, item: row });
  }
  const answer = cleanText(b.answer, 2000);
  if (!answer) return json({ ok: false, error: "an answer (max 2000 characters) is required" }, 400);
  return saveAnswer(ctx, kind, id, answer);
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
