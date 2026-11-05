-- MFA Hub v2 migration (run once on D1 "mfa-hub"). tools/hub_schema.sql is the full current schema.
ALTER TABLE finance_questions ADD COLUMN suggestions TEXT NOT NULL DEFAULT '[]';
CREATE TABLE IF NOT EXISTS needs (
  id TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  source TEXT NOT NULL, agent TEXT, title TEXT NOT NULL, detail TEXT, ref TEXT,
  suggestions TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','new','seen','done')),
  answer TEXT, answered_at TEXT, agent_note TEXT);
CREATE INDEX IF NOT EXISTS needs_status ON needs(status);
CREATE TABLE IF NOT EXISTS log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  agent TEXT NOT NULL, action TEXT NOT NULL, detail TEXT, link TEXT);
CREATE INDEX IF NOT EXISTS log_ts ON log(ts DESC);
CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  area TEXT NOT NULL DEFAULT 'general', body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','seen','in_progress','done')),
  agent_note TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY, received_at TEXT NOT NULL, first_name TEXT, email_domain TEXT, topic TEXT, source TEXT,
  status TEXT NOT NULL DEFAULT 'new', reminder_at TEXT, note TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS kpis (key TEXT PRIMARY KEY, label TEXT NOT NULL, value REAL, unit TEXT, as_of TEXT, source TEXT, note TEXT);
CREATE TABLE comments_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  page TEXT NOT NULL CHECK (page IN ('home','board','calendar','ads','finance','leads','tasks','log')),
  item_ref TEXT NOT NULL, body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','seen','done')), agent_note TEXT);
INSERT INTO comments_v2 SELECT id, created_at, page, item_ref, body, status, agent_note FROM comments;
DROP TABLE comments;
ALTER TABLE comments_v2 RENAME TO comments;
CREATE INDEX IF NOT EXISTS comments_status ON comments(status, created_at);
ALTER TABLE comments ADD COLUMN kind TEXT NOT NULL DEFAULT 'comment';
ALTER TABLE calendar_items ADD COLUMN metrics_at TEXT;
