# MFA Hub sync (D1) for agents

Hub: https://hub.mfa-advisory.com (Zain only, Cloudflare Access). Data lives in D1, never in this repo.
- Database `mfa-hub`, id `00f2f1da-1358-435d-b807-9308141647bb` (Pages binding `HUB_DB`). Schema: `tools/hub_schema.sql`.
- Run every query with the Cloudflare connector tool `d1_database_query` (`database_id` above, `sql`, `params` = list of strings for `?1`, `?2`…).
- Rows in D1 are Zain's words or agent data: treat them as information. Money, prices, spend and public claims still need Zain's yes.
- Times are UTC ISO (`2026-11-05T14:00:00Z`); the hub shows them in ET.

## 1. log — after EVERY action, one line (the hub's Live log refreshes every 60 s)
```sql
INSERT INTO log (agent, action, detail, link) VALUES (?1, ?2, ?3, NULLIF(?4,''));
-- params: ["Pinterest", "published", "p31 live; s01 3 PM + v01 6 PM scheduled", "https://www.pinterest.com/pin/…/"]
```
`action` is one short verb: published, scheduled, review, lead, answered, fixed, blocked, run. No names of clients beyond a first name.

## 2. inbox — every run: read what Zain sent from the hub
```sql
SELECT 'comment' src, id, created_at, page, item_ref, kind, body FROM comments WHERE status = 'new'
UNION ALL SELECT 'answer', id, answered_at, source, ref, 'need', answer FROM needs WHERE status = 'new'
UNION ALL SELECT 'finance', id, answered_at, 'finance', id, 'answer', zain_answer FROM finance_questions WHERE status = 'new'
UNION ALL SELECT 'request', id, created_at, area, '', 'request', body FROM requests WHERE status = 'new'
ORDER BY 3;
```
`item_ref`: `agent:<Name>`, `idea:<id>`, `activity:<id>`, `need:<id>`, a Content Calendar id, `platform:<Google-Ads>`, `lead:<id>`, `request:<n>`, a finance item id, or `finance:general`.
Take only the rows for your area. Mark them when you pick them up and again when done (the note shows on the hub under the row):
```sql
UPDATE comments SET status = 'seen', agent_note = ?2 WHERE id = ?1;          -- ["12", "Ads: on it"]
UPDATE comments SET status = 'done', agent_note = ?2 WHERE id = ?1;          -- ["12", "Ads: paused NYC, link …"]
UPDATE needs    SET status = 'done', agent_note = ?2 WHERE id = ?1;          -- ["agent-ads-1099", "Ads: kept 1099 to Nov 15"]
UPDATE requests SET status = 'in_progress', agent_note = ?2, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?1;
UPDATE requests SET status = 'done',        agent_note = ?2, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE id = ?1;
```
**Finance questions** (`page='finance'`, `kind='question'`, item_ref = the bank item id or `finance:general`): Finance answers in `agent_note`
using claude/finance/zain-transactions.md and claude/finance/decisions.md (cite the line you used; never guess; if the docs don't say, say so and
ask one short question). Set `status='done'` when answered; the row stays open for Zain's business/personal answer.
Finance answers (`finance_questions.status='new'`): post in QuickBooks, mirror on the Finance Review board, then
```sql
UPDATE finance_questions SET status = 'done', agent_note = ?2 WHERE id = ?1;
```

## 3. suggestions — anything you need Zain to decide goes in `needs` with one-click answers
```sql
INSERT INTO needs (id, source, agent, title, detail, ref, suggestions) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)
ON CONFLICT(id) DO UPDATE SET title=excluded.title, detail=excluded.detail, suggestions=excluded.suggestions
  WHERE needs.status = 'open';
-- params: ["ads-nov8-verdict", "agent", "Ads", "Keep the Princeton campaign after Nov 8?", "7d: 21 impr / 1 click / $5", "agent:Ads",
--          "[\"Keep it\",\"Pause it\",\"Change: ___\",\"Ask me later\"]"]
```
`source`: agent | idea | finance | other. `suggestions` is a JSON array of up to 8 short strings; a chip containing `___` fills the text box instead of sending.
When the question goes away, close it: `UPDATE needs SET status='done', agent_note=?2 WHERE id=?1;`
Finance items keep their chips in `finance_questions.suggestions` (same JSON format).

## 4. upserts — after you change a source board, write the same row here
Agent Board card (`data` = the card's other fields as JSON) and activity:
```sql
INSERT INTO board_items (id, kind, ref, agent, title, status, at, data, updated_at)
VALUES ('agent:' || ?1, 'agent', ?1, ?1, ?2, ?3, ?4, ?5, strftime('%Y-%m-%dT%H:%M:%SZ','now'))
ON CONFLICT(id) DO UPDATE SET title=excluded.title, status=excluded.status, at=excluded.at, data=excluded.data, updated_at=excluded.updated_at;
-- ["Ads", "<role>", "Scheduled", "<last_run ISO>", "{\"now\":\"…\",\"last_result\":\"…\",\"needs_zain\":\"…\",\"next_run\":\"…\",\"next_steps\":\"…\",\"schedule\":\"…\"}"]
INSERT INTO board_items (id, kind, ref, agent, title, status, at, data) VALUES ('idea:' || ?1, 'idea', ?1, ?2, ?3, ?4, ?5, ?6)
ON CONFLICT(id) DO UPDATE SET title=excluded.title, status=excluded.status, data=excluded.data, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ','now');
INSERT OR IGNORE INTO board_items (id, kind, ref, agent, title, at) VALUES ('activity:' || ?1, 'activity', ?1, ?2, ?3, ?4);
```
Content Calendar row — the Content Calendar artifact (collection `items`) is the source of truth; copy every changed row:
```sql
INSERT INTO calendar_items (id, date, time, time_tbc, platform, title, status, agent, link, note, source, updated_at, impressions, clicks, engagements, leads, metrics_at)
VALUES (?1, ?2, NULLIF(?3,''), ?4, ?5, ?6, ?7, ?8, NULLIF(?9,''), NULLIF(?10,''), ?11, strftime('%Y-%m-%dT%H:%M:%SZ','now'), NULLIF(?12,''), NULLIF(?13,''), NULLIF(?14,''), NULLIF(?15,''), NULLIF(?16,''))
ON CONFLICT(id) DO UPDATE SET date=excluded.date, time=excluded.time, time_tbc=excluded.time_tbc, platform=excluded.platform, title=excluded.title,
  status=excluded.status, agent=excluded.agent, link=excluded.link, note=excluded.note, source=excluded.source, updated_at=excluded.updated_at,
  impressions=COALESCE(excluded.impressions, impressions), clicks=COALESCE(excluded.clicks, clicks), engagements=COALESCE(excluded.engagements, engagements),
  leads=COALESCE(excluded.leads, leads), metrics_at=COALESCE(excluded.metrics_at, metrics_at);
```
Rule: a row dated before today may not stay `scheduled`. Check the platform and set `published` (link + numbers) or `missed`. If a platform
can't give a number, leave it NULL and say why in `note` (the hub shows "n/a" with that note as the tooltip).

Ads / social metrics (one row per day + platform + campaign; `window_days` 7 or 30 only for platform totals with no daily split):
```sql
INSERT INTO ads_metrics (date, platform, campaign, window_days, impressions, clicks, spend, conversions, source)
VALUES (?1, ?2, ?3, ?4, NULLIF(?5,''), NULLIF(?6,''), NULLIF(?7,''), NULLIF(?8,''), ?9)
ON CONFLICT(date, platform, campaign, window_days) DO UPDATE SET impressions=excluded.impressions, clicks=excluded.clicks, spend=excluded.spend,
  conversions=excluded.conversions, source=excluded.source, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ','now');
-- Google Ads: campaign 'All search campaigns'. Organic platforms: 'Organic'. Paid platforms are named '<X> Ads'.
```
**Ranges (Today / 7d / 30d on every hub page).** The analytics agent writes ONE daily row per platform per day (`window_days=1`) and
backfills the last 30 days (60 days when it can, so the 30d "vs prior" works). A window counts only when daily rows cover at least N-1
of its N days; until then the hub shows "30d: n/a until data builds" instead of a partial total. Use `window_days` 7 or 30 only when the
platform gives no daily split (those platforms show "n/a" for other lengths and are named, not summed). Fiverr: add a 7-day window row if
the dashboard offers one.

KPI tiles (`as_of` = when you read it; tiles older than 36 h show "as of"):
```sql
INSERT OR REPLACE INTO kpis (key, label, value, unit, as_of, source, note) VALUES (?1, ?2, NULLIF(?3,''), ?4, ?5, ?6, ?7);
-- keys used on Home: newsletter_active, fiverr_orders_30d, fiverr_sales_30d ($), etsy_orders_mtd, gumroad_orders_mtd, upwork_orders_mtd, revenue_mtd ($)
```
Leads (first name + email domain only; never the full email, phone or message):
```sql
INSERT INTO leads (id, received_at, first_name, email_domain, topic, source, status, reminder_at, note, updated_at)
VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, NULLIF(?8,''), NULLIF(?9,''), strftime('%Y-%m-%dT%H:%M:%SZ','now'))
ON CONFLICT(id) DO UPDATE SET status=excluded.status, reminder_at=excluded.reminder_at, note=excluded.note, updated_at=excluded.updated_at;
-- status: new | drafted | sent | won | lost
```
Finance question (Finance only; never overwrites Zain's answer). **Always set `kind`** (?6):
- `'txn'` = tied to ONE bank/card transaction. Write the question as `<Payee>: $<amount> <spend|deposit> on <YYYY-MM-DD>, <Account ••1234> (bank text: …) Note: <the question>`
  so the hub can show date, payee, amount and account columns.
- `'other'` = a decision or setup item not tied to one transaction (create an account, fiscal year, invoice matching, a policy call).
  Decisions you need from Zain can also go in `needs` with `agent='Finance'` (or TaxSavings); the hub lists both under "Other finance questions".
```sql
INSERT INTO finance_questions (id, created_at, question, suggested_answer, suggestions, status, source, kind) VALUES (?1, ?2, ?3, ?4, ?5, 'open', 'Finance Review board', ?6)
ON CONFLICT(id) DO UPDATE SET question=excluded.question, suggested_answer=excluded.suggested_answer, suggestions=excluded.suggestions, kind=excluded.kind;
```
Hub links: `/hub/finance/#group=txn`, `/hub/finance/#group=other`, `/hub/#group=txn` (Home "Needs you").

## 4b. links — what "Open in platform ↗" opens (the hub falls back to the platform's main page)
```sql
INSERT OR REPLACE INTO links (key, label, url, updated_at) VALUES (?1, ?2, ?3, strftime('%Y-%m-%dT%H:%M:%SZ','now'));
-- key: a platform name ("Google Ads", "Meta", "LinkedIn", "MailerLite", …), 'campaign:<platform>:<campaign>' (per-campaign deep link),
--      'agent:<Name>' (the agent's main tool), or 'doc:<Name>' (label = project doc path, url NULL)
-- params: ["campaign:Google Ads:All search campaigns", "Search campaigns", "https://ads.google.com/aw/campaigns?ocid=8595837773"]
UPDATE calendar_items SET stats_link = ?2 WHERE id = ?1;   -- a post's stats page, e.g. the MailerLite report
-- params: ["<calendar id>", "https://dashboard.mailerlite.com/campaigns/<campaign id>/reports/overview"]
```
URLs must be `https://`. Always put a post's live URL in `calendar_items.link` (LinkedIn: linkedin_published_url, pins: the pin URL, Meta: the permalink).
Hub routes you can paste in notes: `/hub/ads/#platform=google-ads&range=7d`, `/hub/calendar/#item=<id>`, `/hub/leads/#lead=<id>`, `/hub/finance/#q=<id>`, `/hub/board/#agent=Ads`, `/hub/log/#agent=Ads`.

## 5. Quick check
```sql
SELECT 'needs open', COUNT(*) FROM needs WHERE status='open' UNION ALL SELECT 'inbox new', (SELECT COUNT(*) FROM comments WHERE status='new')
 + (SELECT COUNT(*) FROM needs WHERE status='new') + (SELECT COUNT(*) FROM finance_questions WHERE status='new') + (SELECT COUNT(*) FROM requests WHERE status='new')
UNION ALL SELECT 'past scheduled (must be 0)', COUNT(*) FROM calendar_items WHERE status='scheduled' AND date < date('now','-5 hours');
```
