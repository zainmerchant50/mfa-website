// GET /api/hub/data?page=home|board|calendar|ads|finance|leads|tasks|log  -> the rows a Hub page shows, plus its comments.
import { json, authed, PAGES, parseSuggestions } from "../../_shared/hub_api.js";

const parse = (s) => { try { return JSON.parse(s || "{}"); } catch (e) { return {}; } };
const sugg = (rows) => rows.map((r) => ({ ...r, suggestions: parseSuggestions(r.suggestions) }));

const Q = {
  kpis: "SELECT key, label, value, unit, as_of, source, note FROM kpis ORDER BY key",
  leads: "SELECT id, received_at, first_name, email_domain, topic, source, status, reminder_at, note, updated_at FROM leads ORDER BY received_at DESC LIMIT 500",
  ads: "SELECT date, platform, campaign, window_days, impressions, clicks, spend, conversions, source, updated_at FROM ads_metrics WHERE date >= date('now','-60 days') ORDER BY date DESC, platform LIMIT 3000",
  needs: "SELECT id, created_at, source, agent, title, detail, ref, suggestions, status, answer, answered_at, agent_note FROM needs WHERE status <> 'done' OR answered_at >= datetime('now','-3 days') ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'new' THEN 1 WHEN 'seen' THEN 2 ELSE 3 END, created_at DESC LIMIT 300",
  finance: "SELECT id, created_at, question, suggested_answer, suggestions, status, zain_answer, answered_at, agent_note, kind, confidence, auto_posted_at FROM finance_questions ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'new' THEN 1 WHEN 'seen' THEN 2 ELSE 3 END, created_at DESC, id LIMIT 1000",
  financeOpen: "SELECT id, created_at, question, suggested_answer, suggestions, status, zain_answer, answered_at, agent_note, kind, confidence, auto_posted_at FROM finance_questions WHERE status IN ('open','new','seen') ORDER BY CASE status WHEN 'open' THEN 0 ELSE 1 END, id LIMIT 500",
  agents: "SELECT id, ref, agent, title, status, at, data, updated_at FROM board_items WHERE kind = 'agent' ORDER BY agent",
  ideas: "SELECT id, ref, agent, title, status, at, data, updated_at FROM board_items WHERE kind = 'idea' ORDER BY at DESC LIMIT 500",
  activity: "SELECT id, ref, agent, title, at FROM board_items WHERE kind = 'activity' AND at >= datetime('now','-62 days') ORDER BY at DESC LIMIT 1000",
  topPosts: "SELECT id, date, platform, title, impressions, clicks, engagements, leads, link FROM calendar_items WHERE impressions IS NOT NULL AND date >= date('now','-31 days') ORDER BY impressions DESC LIMIT 500",
  calSince: "SELECT MIN(date) AS min_date FROM calendar_items",
  logRecent: "SELECT id, ts, agent, action, detail, link FROM log WHERE ts >= datetime('now','-62 days') ORDER BY ts DESC, id DESC LIMIT 3000",
  logMin: "SELECT MIN(ts) AS min_ts FROM log",
  calendar: "SELECT * FROM calendar_items WHERE date >= date('now','-90 days') ORDER BY date, time LIMIT 3000",
  log: "SELECT id, ts, agent, action, detail, link FROM log ORDER BY ts DESC, id DESC LIMIT 100",
  requests: "SELECT id, created_at, area, body, status, agent_note, updated_at FROM requests ORDER BY CASE status WHEN 'done' THEN 1 ELSE 0 END, id DESC LIMIT 500",
  allComments: "SELECT id, created_at, page, item_ref, body, kind, status, agent_note FROM comments ORDER BY id DESC LIMIT 500",
  links: "SELECT key, label, url FROM links ORDER BY key LIMIT 500",
};

export async function onRequestGet(ctx) {
  if (!authed(ctx)) return json({ ok: false, error: "forbidden" }, 403);
  const db = ctx.env.HUB_DB;
  if (!db) return json({ ok: false, error: "database not bound" }, 503);
  const page = new URL(ctx.request.url).searchParams.get("page");
  if (!PAGES.includes(page)) return json({ ok: false, error: "unknown page" }, 400);

  const want = {
    home: ["kpis", "leads", "ads", "needs", "financeOpen", "agents", "topPosts", "calSince", "log", "requests", "links"],
    board: ["agents", "ideas", "activity", "needs", "logRecent", "logMin", "links"],
    calendar: ["calendar", "calSince", "links"],
    ads: ["ads", "kpis", "links"],
    finance: ["finance", "needs", "links"],
    leads: ["leads", "links"],
    tasks: ["requests", "allComments", "needs", "links"],
    log: ["log"],
  }[page];
  const stmts = want.map((k) => db.prepare(Q[k]));
  stmts.push(db.prepare("SELECT id, created_at, item_ref, body, kind, status, agent_note FROM comments WHERE page = ?1 ORDER BY id DESC LIMIT 1000").bind(page));
  const res = await db.batch(stmts);
  const out = { ok: true, page, now: new Date().toISOString() };
  want.forEach((k, i) => { out[k] = res[i].results || []; });
  out.comments = res[res.length - 1].results || [];
  if (out.agents) out.agents = out.agents.map((r) => ({ ...r, data: parse(r.data) }));
  if (out.ideas) out.ideas = out.ideas.map((r) => ({ ...r, data: parse(r.data) }));
  for (const k of ["needs", "finance", "financeOpen"]) if (out[k]) out[k] = sugg(out[k]);
  return json(out);
}

export function onRequest() {
  return json({ ok: false, error: "method not allowed" }, 405);
}
