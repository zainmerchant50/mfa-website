-- MFA Hub v6 migration (run once on D1 "mfa-hub"): operations deadlines for the Today page (Zain 2026-11-16: "focus is on operations").
-- One row per dated operational item: lead follow-ups, client deadlines, ad-test end dates, PR deadlines, sprint verdicts, filing dates.
-- due = YYYY-MM-DD (ET). area = Leads|Clients|Ads|Content|PR|Store|Freelance|Ops|Tax. owner = agent name or "Zain".
CREATE TABLE IF NOT EXISTS deadlines (
  id TEXT PRIMARY KEY, due TEXT NOT NULL, title TEXT NOT NULL, area TEXT, owner TEXT,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','done','dropped')),
  link TEXT, note TEXT, updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')));
CREATE INDEX IF NOT EXISTS deadlines_due ON deadlines(due);
