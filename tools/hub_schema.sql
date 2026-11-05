-- MFA Hub (D1 database "mfa-hub", binding HUB_DB). Private data lives only in D1, never in the repo.
CREATE TABLE IF NOT EXISTS board_items (
  id TEXT PRIMARY KEY,            -- "<kind>:<ref>", e.g. agent:Hub, idea:20261103-0915-referral, activity:20261104T091900-Hub
  kind TEXT NOT NULL CHECK (kind IN ('agent','idea','activity')),
  ref TEXT NOT NULL,              -- doc id on the Agent Board artifact
  agent TEXT,                     -- agent name (agent rows: the agent itself)
  title TEXT,                     -- agent: role · idea: title · activity: event text
  status TEXT,                    -- agent: Working|Scheduled|Blocked|Idle · idea: new|approved|declined|done
  at TEXT,                        -- ISO time (agent: last_run, idea: at, activity: at)
  data TEXT NOT NULL DEFAULT '{}',-- the full source document as JSON
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS board_kind_at ON board_items(kind, at DESC);

CREATE TABLE IF NOT EXISTS calendar_items (
  id TEXT PRIMARY KEY,            -- Content Calendar doc id
  date TEXT NOT NULL,             -- YYYY-MM-DD (ET)
  time TEXT,                      -- HH:MM ET or NULL
  time_tbc INTEGER NOT NULL DEFAULT 0,
  platform TEXT,
  title TEXT,
  status TEXT,                    -- scheduled|published|...
  agent TEXT,
  link TEXT,
  note TEXT,
  source TEXT,
  updated_at TEXT,
  impressions INTEGER,
  clicks INTEGER,
  engagements INTEGER,
  leads INTEGER
);
CREATE INDEX IF NOT EXISTS cal_date ON calendar_items(date);

CREATE TABLE IF NOT EXISTS ads_metrics (
  date TEXT NOT NULL,             -- YYYY-MM-DD (last day of the window)
  platform TEXT NOT NULL,         -- Google Ads, Pinterest Ads, Instagram, ...
  campaign TEXT NOT NULL DEFAULT 'All',
  window_days INTEGER NOT NULL DEFAULT 1,  -- 1 = one day; 7 = a 7-day total ending on date
  impressions INTEGER, clicks INTEGER, spend REAL, conversions INTEGER,
  source TEXT,
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  PRIMARY KEY (date, platform, campaign, window_days)
);

CREATE TABLE IF NOT EXISTS finance_questions (
  id TEXT PRIMARY KEY,            -- Finance Review item id
  created_at TEXT NOT NULL,
  question TEXT NOT NULL,
  suggested_answer TEXT,
  status TEXT NOT NULL DEFAULT 'open',  -- open (waiting on Zain) | new (Zain answered in the Hub) | seen | done | answered/posted (from the Finance Review board)
  zain_answer TEXT,
  answered_at TEXT,
  agent_note TEXT,
  source TEXT,
  data TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS fin_status ON finance_questions(status);

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  page TEXT NOT NULL CHECK (page IN ('home','board','calendar','ads','finance')),
  item_ref TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','seen','done')),
  agent_note TEXT
);
CREATE INDEX IF NOT EXISTS comments_status ON comments(status, created_at);
