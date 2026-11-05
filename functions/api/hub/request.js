// POST /api/hub/request {body, area}  -> a new task/request from Zain for the agents (status 'new').
import { guardPost, json, readJson, cleanText, logStmt } from "../../_shared/hub_api.js";

export const AREAS = ["general", "site", "blog", "social", "ads", "store", "finance", "leads", "freelance"];

export async function onRequestPost(ctx) {
  const bad = await guardPost(ctx);
  if (bad) return bad;
  let b;
  try { b = await readJson(ctx.request); } catch (e) { return json({ ok: false, error: "bad request" }, 400); }
  const area = AREAS.includes(b.area) ? b.area : "general";
  const body = cleanText(b.body, 4000);
  if (!body) return json({ ok: false, error: "a request (max 4000 characters) is required" }, 400);
  const db = ctx.env.HUB_DB;
  const row = await db.prepare("INSERT INTO requests (area, body) VALUES (?1, ?2) RETURNING id, created_at, area, body, status")
    .bind(area, body).first();
  await logStmt(db, "request", `#${row.id} (${area}): ${body.slice(0, 200)}`).run();
  return json({ ok: true, request: row });
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
