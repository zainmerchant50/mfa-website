# Pinterest bulk upload (CSV)

Where: Pinterest Business, Settings, Import content, Bulk create Pins, Upload .csv file
(https://www.pinterest.com/settings/bulk-create-pins/). Organic Pins only: no ads, no spend.

Template: `docs/pinterest-bulk-upload-template.csv` (10 Pins drafted 2026-11-04 from the top performers: the
"Is it deductible?" write-offs and the 1099 checklist). **Uploaded 2026-11-04 (Zain's yes, 23:16 ET)**, scheduled
Nov 7-16 at 8:30 PM ET. Pinterest skipped the Nov 8 row because its image repeated the Nov 7 row's; it was re-sent
with a different image in `docs/pinterest-bulk-upload-fix-2026-11-08.csv`.

## Column format

Header row, exactly in this order (Pinterest's sample file):

| Column | Required | What goes in it |
|---|---|---|
| Title | yes | Up to 100 characters. Keyword first ("Is Mileage Deductible?"). |
| Media URL | yes | Public URL of the image file itself (.jpg or .png), on mfa-advisory.com. 2:3 or 4:5 vertical works best. |
| Pinterest board | yes | Board name exactly as it appears on the profile. `Board/Section` for a section. A name that doesn't exist creates a new board, so copy it. |
| Thumbnail | video only | Leave blank for image Pins. |
| Description | no | Up to 500 characters. Plain sentences plus the search phrase. |
| Link | no | Destination URL with UTM (below). |
| Publish date | no | `YYYY-MM-DDTHH:MM:SS` in **UTC**. Blank publishes right away. A malformed date fails that row. |
| Keywords | no | Comma-separated search terms, inside quotes. |

Up to 200 rows per file. Save as CSV (UTF-8). Wrap any field that contains a comma in double quotes.

Current boards: Self-Employed & 1099 Taxes; Tax Write Offs & Deductions for Small Business; Tax Forms Explained for
Small Business; Tax Prep Checklist & Tax Season Organization; Small Business Bookkeeping Templates & Tips; Business
Expense Tracker & Budget Templates; Bookkeeping for Hair Stylists, Realtors & More; LLC Checklist & Starting a Business;
MFA Tax Guides (blog RSS auto-pins); Social (Instagram auto-pins).

## Rules

- **No prices and no percentages** in titles or descriptions (no "$", no "%", no "50 percent"). Images may show figures.
- Never the word "free" (also not "tax-free"). Never call MFA a CPA firm or Zain a CPA. No street address.
- **Every Link carries UTM:** `?utm_source=pinterest&utm_medium=social&utm_campaign=bulk_pins&utm_content=<short-id>`
  (put any `#anchor` after the UTM). Catalog product Pins use `utm_medium=catalog` and are made by the catalog feed, not here.
- **Spacing: one Pin per day at 8:30 PM ET.** In UTC that is 01:30 the next day while Eastern is on standard time
  (Nov to mid-March), 00:30 during daylight time. Example: 8:30 PM ET on Nov 7, 2026 = `2026-11-08T01:30:00`.
- Before uploading, check each row against Pins already on the profile so nothing posts twice, and confirm every Media
  URL and Link opens (200). **Use a different Media URL on every row:** Pinterest silently drops a row whose image
  repeats another row's.
- Links stay on mfa-advisory.com (claimed domain). Amazon Associates links live only on /picks/, never in Pins.

## Upload steps (when Zain says go)

1. Re-date the rows so the first Pin lands on the next free 8:30 PM ET slot.
2. Settings, Import content, Bulk create Pins, Upload .csv file, choose the file.
3. Pinterest emails a summary; rows with errors are listed there. Fix and re-upload only those rows.
4. Log the batch in claude/sessions-chat.md.
