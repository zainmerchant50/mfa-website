// POST /api/hub/comment  {page, item_ref, body, kind?: 'comment'|'question'}  -> saves a comment for the agents (status 'new').
import { guardPost, json, readJson, cleanText, logStmt, PAGES, REF_RE } from "../../_shared/hub_api.js";

export async function onRequestPost(ctx) {
  const bad = await guardPost(ctx);
  if (bad) return bad;
  let b;
  try { b = await readJson(ctx.request); } catch (e) { return json({ ok: false, error: "bad request" }, 400); }
  const page = PAGES.includes(b.page) ? b.page : null;
  const ref = typeof b.item_ref === "string" && REF_RE.test(b.item_ref) ? b.item_ref : null;
  const body = cleanText(b.body, 4000);
  const kind = b.kind === "question" ? "question" : "comment";
  if (!page || !ref || !body) return json({ ok: false, error: "page, item_ref and a comment (max 4000 characters) are required" }, 400);
  const db = ctx.env.HUB_DB;
  const row = await db.prepare(
    "INSERT INTO comments (page, item_ref, body, kind) VALUES (?1, ?2, ?3, ?4) RETURNING id, created_at, status"
  ).bind(page, ref, body, kind).first();
  await logStmt(db, kind, `${page} · ${ref}: ${body.slice(0, 160)}`).run();
  return json({ ok: true, comment: { ...row, page, item_ref: ref, body, kind, agent_note: null } });
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
