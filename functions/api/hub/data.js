// GET /api/hub/data?page=home|board|calendar|ads|finance  -> the rows a Hub page shows, plus its comments.
import { json, authed, PAGES } from "../../_shared/hub_api.js";

const parse = (s) => { try { return JSON.parse(s || "{}"); } catch (e) { return {}; } };

export async function onRequestGet(ctx) {
  if (!authed(ctx)) return json({ ok: false, error: "forbidden" }, 403);
  const db = ctx.env.HUB_DB;
  if (!db) return json({ ok: false, error: "database not bound" }, 503);
  const page = new URL(ctx.request.url).searchParams.get("page");
  if (!PAGES.includes(page)) return json({ ok: false, error: "unknown page" }, 400);

  const all = async (sql, ...args) => (await db.prepare(sql).bind(...args).all()).results || [];
  const out = { ok: true, page, now: new Date().toISOString() };

  if (page === "home") {
    const one = async (sql) => (await db.prepare(sql).first()) || {};
    out.counts = {
      finance_open: (await one("SELECT COUNT(*) n FROM finance_questions WHERE status = 'open'")).n || 0,
      comments_new: (await one("SELECT COUNT(*) n FROM comments WHERE status = 'new'")).n || 0,
      comments_done: (await one("SELECT COUNT(*) n FROM comments WHERE status = 'done'")).n || 0,
      agents_blocked: (await one("SELECT COUNT(*) n FROM board_items WHERE kind = 'agent' AND status = 'Blocked'")).n || 0,
      ideas_new: (await one("SELECT COUNT(*) n FROM board_items WHERE kind = 'idea' AND status = 'new'")).n || 0,
      calendar_next7: (await one("SELECT COUNT(*) n FROM calendar_items WHERE date BETWEEN date('now','-5 hours') AND date('now','-5 hours','+7 days')")).n || 0,
      ads_latest: (await one("SELECT MAX(date) d FROM ads_metrics WHERE window_days = 1")).d || null,
    };
    out.replies = await all("SELECT id, created_at, page, item_ref, body, status, agent_note FROM comments WHERE agent_note IS NOT NULL ORDER BY id DESC LIMIT 10");
  } else if (page === "board") {
    const rows = await all("SELECT id, kind, ref, agent, title, status, at, data, updated_at FROM board_items WHERE kind <> 'activity' OR at >= datetime('now','-30 days') ORDER BY kind, at DESC LIMIT 1500");
    out.items = rows.map((r) => ({ ...r, data: parse(r.data) }));
  } else if (page === "calendar") {
    out.items = await all("SELECT * FROM calendar_items WHERE date >= date('now','-75 days') ORDER BY date, time LIMIT 2000");
  } else if (page === "ads") {
    out.rows = await all("SELECT date, platform, campaign, window_days, impressions, clicks, spend, conversions, source, updated_at FROM ads_metrics WHERE date >= date('now','-60 days') ORDER BY date DESC, platform LIMIT 3000");
  } else if (page === "finance") {
    out.items = await all("SELECT id, created_at, question, suggested_answer, status, zain_answer, answered_at, agent_note FROM finance_questions " +
      "ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'new' THEN 1 WHEN 'seen' THEN 2 ELSE 3 END, created_at DESC LIMIT 1000");
  }
  out.comments = await all("SELECT id, created_at, item_ref, body, status, agent_note FROM comments WHERE page = ?1 ORDER BY id DESC LIMIT 1000", page);
  return json(out);
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
