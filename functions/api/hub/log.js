// GET /api/hub/log?agent=<name>&limit=<1-200>  -> newest live-log lines (the hub polls this every 60 s).
import { json, authed } from "../../_shared/hub_api.js";

export async function onRequestGet(ctx) {
  if (!authed(ctx)) return json({ ok: false, error: "forbidden" }, 403);
  const db = ctx.env.HUB_DB;
  if (!db) return json({ ok: false, error: "database not bound" }, 503);
  const u = new URL(ctx.request.url);
  const agent = (u.searchParams.get("agent") || "").slice(0, 60);
  const limit = Math.min(200, Math.max(1, parseInt(u.searchParams.get("limit") || "100", 10) || 100));
  const q = agent
    ? db.prepare("SELECT id, ts, agent, action, detail, link FROM log WHERE agent = ?1 ORDER BY ts DESC, id DESC LIMIT ?2").bind(agent, limit)
    : db.prepare("SELECT id, ts, agent, action, detail, link FROM log ORDER BY ts DESC, id DESC LIMIT ?1").bind(limit);
  const rows = (await q.all()).results || [];
  const agents = ((await db.prepare("SELECT agent, COUNT(*) n FROM log GROUP BY agent ORDER BY agent").all()).results || []);
  return json({ ok: true, now: new Date().toISOString(), rows, agents });
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
