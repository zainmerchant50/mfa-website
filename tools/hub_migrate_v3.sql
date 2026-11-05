-- MFA Hub v3 migration (run once on D1 "mfa-hub"): outbound links + per-post stats link.
CREATE TABLE IF NOT EXISTS links (key TEXT PRIMARY KEY, label TEXT NOT NULL, url TEXT, updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')));
ALTER TABLE calendar_items ADD COLUMN stats_link TEXT;
INSERT OR REPLACE INTO links (key, label, url) VALUES
  ('Google Ads', 'Google Ads', 'https://ads.google.com/aw/campaigns?ocid=8595837773'),
  ('Pinterest Ads', 'Pinterest Ads', 'https://ads.pinterest.com/advertiser/549770934097/'),
  ('Pinterest', 'Pinterest profile', 'https://www.pinterest.com/mfaadvisory/_created/'),
  ('Meta', 'Meta Business Suite', 'https://business.facebook.com/latest/insights?asset_id=1357885654083102&business_id=1485123785998879'),
  ('LinkedIn', 'LinkedIn analytics', 'https://www.linkedin.com/company/108306962/admin/analytics/updates/'),
  ('TikTok', 'TikTok Studio', 'https://www.tiktok.com/tiktokstudio/analytics'),
  ('YouTube Shorts', 'YouTube Studio', 'https://studio.youtube.com/channel/UCLNPu802SdUCkrjLeIqgM_g/analytics'),
  ('Fiverr Ads', 'Fiverr Ads', 'https://www.fiverr.com/users/zainmerchant50/fiverr_ads'),
  ('Fiverr', 'Fiverr', 'https://www.fiverr.com/users/zainmerchant50/fiverr_ads'),
  ('Etsy Ads', 'Etsy stats', 'https://www.etsy.com/your/shops/me/stats'),
  ('Etsy', 'Etsy stats', 'https://www.etsy.com/your/shops/me/stats'),
  ('Gumroad', 'Gumroad analytics', 'https://app.gumroad.com/analytics'),
  ('Upwork', 'Upwork', 'https://www.upwork.com/'),
  ('MailerLite', 'MailerLite campaigns', 'https://dashboard.mailerlite.com/campaigns'),
  ('Subscribers', 'MailerLite subscribers', 'https://dashboard.mailerlite.com/subscribers'),
  ('QuickBooks', 'QuickBooks banking', 'https://qbo.intuit.com/app/banking'),
  ('Blog', 'Blog', 'https://mfa-advisory.com/blog/'),
  ('Site', 'mfa-advisory.com', 'https://mfa-advisory.com/'),
  ('Gmail', 'Gmail', 'https://mail.google.com/mail/u/0/');
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/201157566380639539/report' WHERE platform = 'Newsletter' AND instr(link, 'year-end-tax-planning') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/201167845274420627/report' WHERE platform = 'Newsletter' AND instr(link, '2027-tax-calendar') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/201193059382200077/report' WHERE platform = 'Newsletter' AND instr(link, 'anchor') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/201369743198782994/report' WHERE platform = 'Newsletter' AND instr(link, 'salt-cap') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/201774394670843190/report' WHERE platform = 'Newsletter' AND instr(link, 'adoption') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/201871888966747677/report' WHERE platform = 'Newsletter' AND instr(link, 'form-1065') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/201894244728702828/report' WHERE platform = 'Newsletter' AND instr(link, 'form-1120s') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/201977110181447210/report' WHERE platform = 'Newsletter' AND instr(link, 'which-tax-form') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/202413565836002843/report' WHERE platform = 'Newsletter' AND instr(link, 'llc-taxed-as-s-corp') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/202788499881985025/report' WHERE platform = 'Newsletter' AND instr(link, 'hiring-overseas') > 0;
UPDATE calendar_items SET stats_link = 'https://dashboard.mailerlite.com/campaigns/202786739306103810/report' WHERE platform = 'Newsletter' AND instr(link, 'small-business-tax-write-offs') > 0;
