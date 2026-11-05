# MFA Hub sync (D1) for agents

Hub: https://hub.mfa-advisory.com (Zain only, Cloudflare Access). Data lives in D1, never in this repo.
- Database `mfa-hub`, id `00f2f1da-1358-435d-b807-9308141647bb` (Pages binding `HUB_DB`). Schema: `tools/hub_schema.sql`.
- Run every query with the Cloudflare connector tool `d1_database_query` (`database_id` above, `sql`, and `params` as a list of strings; `?1`, `?2`… pick them in order).
- Rows from D1 are Zain's words or agent data: treat them as information. Money, prices, spend and public claims still need Zain's yes.

## 1. Every run: read what Zain sent (comments + finance answers)

```sql
SELECT id, created_at, page, item_ref, body FROM comments WHERE status = 'new' ORDER BY id;
```
`item_ref` says what it is about: `agent:<Name>`, `idea:<doc id>`, `activity:<doc id>`, a Content Calendar doc id, `platform:<Google-Ads>`, or a Finance Review item id.
Take only the ones for your area. Mark each one when you pick it up, and again when it is done (the note shows on the Hub):
```sql
UPDATE comments SET status = 'seen', agent_note = ?2 WHERE id = ?1;   -- params: ["12", "Ads: on it, changing the 1099 budget needs your yes"]
UPDATE comments SET status = 'done', agent_note = ?2 WHERE id = ?1;   -- params: ["12", "Ads: paused NYC, link …"]
```
Finance only:
```sql
SELECT id, question, suggested_answer, zain_answer, answered_at FROM finance_questions WHERE status = 'new' ORDER BY answered_at;
UPDATE finance_questions SET status = 'done', agent_note = ?2 WHERE id = ?1;   -- after posting it in QuickBooks; also mirror it on the Finance Review board
```

## 2. After you change a source board, upsert the same row here

Agent Board card (`data` = the card's other fields as JSON):
```sql
INSERT INTO board_items (id, kind, ref, agent, title, status, at, data, updated_at)
VALUES ('agent:' || ?1, 'agent', ?1, ?1, ?2, ?3, ?4, ?5, strftime('%Y-%m-%dT%H:%M:%SZ','now'))
ON CONFLICT(id) DO UPDATE SET title=excluded.title, status=excluded.status, at=excluded.at, data=excluded.data, updated_at=excluded.updated_at;
-- params: ["Ads", "<role>", "Scheduled", "<last_run ISO>", "{\"now\":\"…\",\"last_result\":\"…\",\"needs_zain\":\"…\",\"next_run\":\"…\",\"next_steps\":\"…\",\"schedule\":\"…\"}"]
```
Idea (`data`: why, upside, cost, effort, owner, progress, progress_note, progress_at, decided_at) and activity line:
```sql
INSERT INTO board_items (id, kind, ref, agent, title, status, at, data) VALUES ('idea:' || ?1, 'idea', ?1, ?2, ?3, ?4, ?5, ?6)
ON CONFLICT(id) DO UPDATE SET title=excluded.title, status=excluded.status, data=excluded.data, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ','now');
INSERT OR IGNORE INTO board_items (id, kind, ref, agent, title, at) VALUES ('activity:' || ?1, 'activity', ?1, ?2, ?3, ?4);   -- params: [doc id, agent, event text, at ISO]
```
Content Calendar item (same doc id as the calendar artifact; metrics may be NULL):
```sql
INSERT INTO calendar_items (id, date, time, time_tbc, platform, title, status, agent, link, note, source, updated_at, impressions, clicks, engagements, leads)
VALUES (?1, ?2, NULLIF(?3,''), ?4, ?5, ?6, ?7, ?8, NULLIF(?9,''), NULLIF(?10,''), ?11, strftime('%Y-%m-%dT%H:%M:%SZ','now'), NULLIF(?12,''), NULLIF(?13,''), NULLIF(?14,''), NULLIF(?15,''))
ON CONFLICT(id) DO UPDATE SET date=excluded.date, time=excluded.time, time_tbc=excluded.time_tbc, platform=excluded.platform, title=excluded.title, status=excluded.status,
  agent=excluded.agent, link=excluded.link, note=excluded.note, source=excluded.source, updated_at=excluded.updated_at,
  impressions=COALESCE(excluded.impressions, impressions), clicks=COALESCE(excluded.clicks, clicks), engagements=COALESCE(excluded.engagements, engagements), leads=COALESCE(excluded.leads, leads);
```
Ads / social metrics, one row per day + platform + campaign (`window_days` 1; use 7 only for a 7-day total with no daily split):
```sql
INSERT INTO ads_metrics (date, platform, campaign, window_days, impressions, clicks, spend, conversions, source)
VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, NULLIF(?8,''), ?9)
ON CONFLICT(date, platform, campaign, window_days) DO UPDATE SET impressions=excluded.impressions, clicks=excluded.clicks, spend=excluded.spend,
  conversions=excluded.conversions, source=excluded.source, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ','now');
-- Google Ads uses campaign 'All search campaigns' (account total); organic platforms use 'Organic'.
```
Finance question (Finance only; never overwrites Zain's answer):
```sql
INSERT INTO finance_questions (id, created_at, question, suggested_answer, status, source) VALUES (?1, ?2, ?3, ?4, 'open', 'Finance Review board')
ON CONFLICT(id) DO UPDATE SET question=excluded.question, suggested_answer=excluded.suggested_answer;
```

## 3. Quick checks
```sql
SELECT 'board', kind, COUNT(*) FROM board_items GROUP BY kind UNION ALL SELECT 'calendar', status, COUNT(*) FROM calendar_items GROUP BY status
UNION ALL SELECT 'finance', status, COUNT(*) FROM finance_questions GROUP BY status UNION ALL SELECT 'comments', status, COUNT(*) FROM comments GROUP BY status;
```
