-- MFA Hub v5 migration (run once on D1 "mfa-hub"): Finance confidence + auto-post time.
-- confidence: 'high' | 'med' | 'low', set by Finance on every finance_questions row (rules in tools/hub_sync.md). NULL = not rated (older rows).
-- auto_posted_at: ISO time Finance posted a High row in QuickBooks on its own; NULL unless Finance auto-posted it.
-- Check first: PRAGMA table_info(finance_questions) must not list confidence / auto_posted_at.
ALTER TABLE finance_questions ADD COLUMN confidence TEXT CHECK (confidence IS NULL OR confidence IN ('high','med','low'));
ALTER TABLE finance_questions ADD COLUMN auto_posted_at TEXT;
