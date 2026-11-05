// POST /api/hub/finance-answer  {id, answer}  -> kept for v1 pages; same as /api/hub/answer with kind 'finance'.
import { guardPost, json, readJson, cleanText, REF_RE } from "../../_shared/hub_api.js";
import { saveAnswer } from "./answer.js";

export async function onRequestPost(ctx) {
  const bad = await guardPost(ctx);
  if (bad) return bad;
  let b;
  try { b = await readJson(ctx.request); } catch (e) { return json({ ok: false, error: "bad request" }, 400); }
  const id = typeof b.id === "string" && REF_RE.test(b.id) ? b.id : null;
  const answer = cleanText(b.answer, 2000);
  if (!id || !answer) return json({ ok: false, error: "id and an answer (max 2000 characters) are required" }, 400);
  return saveAnswer(ctx, "finance", id, answer);
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
