# Shorts ideas backlog (tips that help today, then a soft CTA)

Created 2026-10-24 by the Social/Shorts agent on Zain's direction (2026-10-24): "Going forward the video reels, shorts,
pinterest etc should all be tips and tricks for small sized businesses/individuals so they are encouraged and then want to
follow and then buy our digital products. It should be real helpful practical stuff."

How to use this file
- Take the next idea from the top of the **Backlog** that isn't marked made, and that doesn't repeat a topic shorted in the
  last 3 weeks (see `social/log.json` and the specs folder).
- **Every figure is re-verified on the primary source on the day you render**, even if it is listed as verified below.
  "Verify" = open the page yourself, read the number, put the URL and date in the spec's `sources`. If it can't be
  confirmed, cut it from the short.
- Mix: about 4 pure tips for every 1 product-led short. A pure tip still ends on a soft CTA (tool, guide or the product
  that matches), but the product never gets its own beat. Product-led shorts use a `product` beat (only `live` products in
  `catalog/products.json`).
- Series (put the series name in the hook sub or the label so people recognise it and follow):
  **1-minute bookkeeping fix** · **Tax myth vs fact** · **Gig worker money tip** · **Seller money tip** · **Owner pay 101**.
- CTA destinations: site tools in `/tools/`, guides in `/blog/`, products in `/shop/#kit` or `/shop/#calc`, services in
  `/services/`, `/bookkeeping-cleanup/`, `/llc-formation/`, `/book/`.

## Backlog (ranked)

Rank = how often the question shows up (signal below) x how practical the fix is in 20 seconds x whether we have a
matching destination. Signal: **H** = many separate threads across 3+ communities and a Pinterest autocomplete phrase;
**M** = several threads in 1-2 communities; **L** = a few threads or seasonal.

| # | Status | Series | Hook (≤ 7 words on screen) | The tip in beats | Facts to verify (primary source) | CTA destination |
|---|---|---|---|---|---|---|
| 1 | made 2026-10-24 | Gig worker money tip | Paid on a *1099?* | story: no tax withheld → 15.3% SE tax + income tax → separate TAXES account → move a set % per payout → pay estimates during the year | 15.3% and $400 (irs.gov SE tax page) | /tools/1099-tax-calculator/ (product 08 for the full planner) |
| 2 | made 2026-10-24 | Tax myth vs fact | No 1099? Still *taxable.* | myth/fact rows → $400 SE threshold → log every payment, keep invoice, check against 1099s | all income reportable without a 1099 (irs.gov 1099-K FAQ, IR-2023-35); $400 (irs.gov SE tax page) | /shop/#kit, 1099 Income Tracker (10) |
| 3 | made 2026-10-24 | 1-minute bookkeeping fix | Personal buy on the *business card?* | story → don't delete → recategorize as owner's draw (S corp differs) → add note → IRS: personal expenses not deductible | irs.gov income/expenses FAQ (personal expenses, separate accounts) | /shop/#kit, Bookkeeping Cleanup Checklist (03) |
| 4 | made 2026-10-24 | 1-minute bookkeeping fix | How long to keep *receipts?* | story → 3 / 6 / 7 / 4+ years / indefinitely → photo same day, name it, note business reason | irs.gov "How long should I keep records?" | /shop/#kit, Business Expense Tracker (12) |
| 5 | made 2026-10-24 (product-led) | Seller money tip | Selling on *Etsy?* | $20,000 + 200 transactions (states lower) → myth/fact: still taxable, 1099-K is gross → track fees, shipping, COGS → product | irs.gov 1099-K FAQ; Etsy help article on 1099-K (state limits) | /shop/#kit, Online Seller Bookkeeping Sheet (22) |
| 6 | idea | Gig worker money tip | Which miles *count?* | commute vs business miles → first pickup / between orders → log start and end odometer | IRS Pub 463 (commuting rule); 2026 mileage rates (IRS notice) | /tools/mileage-deduction-calculator/, Mileage Log (14) |
| 7 | idea | Owner pay 101 | How do I *pay myself?* (LLC) | single-member LLC: owner's draw, not payroll → S corp: salary + distributions → draws aren't deductible | irs.gov single-member LLC page; S corp reasonable compensation page | /tools/s-corp-tax-savings-calculator/ |
| 8 | idea | 1-minute bookkeeping fix | Bank and books *don't match?* | 3 causes: missing transactions, duplicates, wrong opening balance → reconcile monthly | none (practice) | /shop/#kit, Month-End Close (18) or /bookkeeping-cleanup/ |
| 9 | idea | Tax myth vs fact | "It's a *write-off*, so it's on the house" | a deduction lowers taxable income, not the bill dollar for dollar → example at a stated bracket | 2026 brackets (Rev. Proc. 2025-32) | /tools/is-it-deductible/ |
| 10 | idea | Gig worker money tip | Missed a *quarterly payment?* | pay now, not in April → penalty grows with time → safe-harbor idea | due dates (Form 1040-ES 2026 PDF); penalty basics (irs.gov underpayment penalty page) | /tools/quarterly-estimated-tax-calculator/ |
| 11 | idea | Owner pay 101 | Do you need a *business account?* | single account = mixed records → open one → pay yourself by transfer | irs.gov FAQ (separate accounts) | /llc-formation/ or Bookkeeping Spreadsheet (11) |
| 12 | idea | Seller money tip | Count your *inventory* Dec 31 | why COGS needs a year-end count → 3-step count → keep the sheet | IRS Pub 334 / Schedule C Part III instructions | /shop/#kit, Reseller Year-End Kit (32) |
| 13 | idea | Tax myth vs fact | "I'll just *form an LLC*" | LLC alone doesn't change tax → default classification → when an election matters | irs.gov LLC classification page | /llc-formation/ |
| 14 | idea | 1-minute bookkeeping fix | Your *phone bill* write-off | business-use % → keep a sample month → don't claim 100% | irs.gov mixed-use guidance (vehicle example; phones under general rule) | /tools/is-it-deductible/, Tax Write Offs Tracker (13) |
| 15 | idea | Gig worker money tip | Home office, the *simple way* | $5 per sq ft, up to 300 sq ft → regular and exclusive use → renters qualify too | irs.gov simplified option page | /tools/home-office-deduction-calculator/ |
| 16 | idea | Owner pay 101 | Hiring help? *W-9 first* | get the W-9 before you pay → $2,000 1099-NEC rule for 2026 payments → keep it on file | 1099-NEC threshold (irs.gov / OBBB notice); Form W-9 instructions | /tools/do-i-need-to-send-a-1099/, W-9 email template |
| 17 | idea | Tax myth vs fact | Venmo for *birthday money?* | personal gifts and reimbursements aren't business income → mark them personal in the app | irs.gov 1099-K FAQ (personal payments) | blog 1099 guide |
| 18 | idea | Seller money tip | Who pays *sales tax* on Etsy? | marketplace collects in most states → you still track it → direct-site sales differ | state marketplace-facilitator rules (NJ Treasury page); Etsy help | /blog/nj-sales-tax-st50-filing-guide/ |
| 19 | idea | 1-minute bookkeeping fix | Profit but *no cash?* | timing: receivables, inventory, loan principal → 13-week cash view | none (practice) | /shop/#calc, Budget + 13-Week Cash Flow (31) |
| 20 | idea | Owner pay 101 | Price it with *margin*, not markup | markup vs margin with one example → find your floor price | none (math) | /tools/profit-margin-calculator/ |
| 21 | idea | Gig worker money tip | W-2 job *plus* a side hustle? | raise W-4 withholding instead of estimates → one form, no quarterly dates | irs.gov W-4 / Tax Withholding Estimator page | /tools/paycheck-tax-calculator/ |
| 22 | idea | Tax myth vs fact | "Hobby income isn't taxed" | hobby income is reported → hobby expenses generally not deductible → signs of a business | irs.gov hobby vs business page | blog Schedule C guide |
| 23 | idea | 1-minute bookkeeping fix | Set up your *chart of accounts* | 5 buckets → match Schedule C lines → stop "uncategorized" | Schedule C line list (IRS) | /shop/#kit, QuickBooks Chart of Accounts pack (23) |
| 24 | idea | Owner pay 101 | Buying equipment *before Dec 31?* | deduction ≠ cash back → Section 179 / bonus basics → buy only what you need | 2026 Section 179 limit (irs.gov / Rev. Proc.) | /blog/section-179-bonus-depreciation-2026/ |
| 25 | idea | Gig worker money tip | Health insurance when *self-employed* | self-employed health insurance deduction basics → who qualifies | irs.gov Form 7206 instructions | content only (CTA /book/) |
| 26 | idea | Tax myth vs fact | "Owe the IRS? You must *pay it all*" | payment plans exist → file on time even if you can't pay | irs.gov payment plans page | content only (CTA /book/) |
| 27 | idea | Seller money tip | Etsy fees are a *write-off* | listing, transaction, processing and ad fees → find them in the monthly statement | Schedule C instructions (ordinary and necessary) | Online Seller Bookkeeping Sheet (22) |
| 28 | idea | 1-minute bookkeeping fix | Tax-season *document checklist* | the 8 papers to gather in January → where each comes from | IRS form list (W-2, 1099s, 1098) | /shop/#kit, 2026 Personal Tax Organizer (29) |
| 29 | idea | Owner pay 101 | Is it time for an *S corp?* (salary angle) | rough profit level where it's worth a look → costs → run the calculator | SE tax (irs.gov); reasonable comp (irs.gov) | /tools/s-corp-tax-savings-calculator/ (already shorted 2026-10-24: wait 3 weeks) |
| 30 | idea | Seller money tip | Reselling *used stuff* online? | selling personal items at a loss vs reselling for profit → keep purchase receipts | irs.gov 1099-K FAQ (personal items sold at a loss) | Reseller Year-End Kit (32) |

## Research summary (2026-10-24)

**Method and a limit to know about.** Zain asked for Reddit research. From this agent's sandbox, Reddit could not be read:
reddit.com is refused by the network proxy (HTTP 403), the fetch tool refuses reddit URLs, and the web search tool returns no
reddit.com results (a domain filter on reddit.com is rejected). So the question list below comes from the public Q&A
communities that could be read: **TurboTax Community** (ttlc.intuit.com), **QuickBooks Community**, **Etsy Community and
Etsy Help**, **Upwork Community**, **eBay Community**, **TheTaxBook forum**, plus MFA's Pinterest autocomplete research
(`/home/claude/mfa-hub/pinterest/RESEARCH.md`, 2026-10-23). These cover the same audiences as the subreddits Zain named.
To add a Reddit pass later, run it from a session that can open reddit.com (for example Claude in Chrome on the PC when it
is not busy) and append findings here. No posts were quoted and no users are named.

Frequency signal is rough: how many separate threads the searches surfaced for the question, across how many communities,
plus whether Pinterest suggests the phrase (A/B from RESEARCH.md).

### Individuals and side hustlers
| Question / pain point | Signal | Maps to |
|---|---|---|
| "Do I have to report income under $600 / with no 1099?" | H | 1099 Income Tracker (10); idea 2 |
| "How much should I set aside for taxes?" | H | /tools/1099-tax-calculator/, product 08; idea 1 |
| "I owe and can't pay the full amount" (payment plans) | M | content only; idea 26 |
| "What documents do I need to file?" (tax document checklist) | H (Pinterest A) | Personal Tax Organizer (29), bundle (33); idea 28 |
| "Do I need to pay quarterly? What if I missed one?" | H | /tools/quarterly-estimated-tax-calculator/; idea 10 |
| Home office deduction as a renter, simplified method | M | /tools/home-office-deduction-calculator/; idea 15 |
| Phone and internet: what % can I deduct? | M | /tools/is-it-deductible/, Tax Write Offs Tracker (13); idea 14 |
| Self-employed health insurance; SEP vs Solo 401(k) | M | content only; idea 25 |
| How long to keep receipts; are bank statements enough? | M | Business Expense Tracker (12); idea 4 |
| W-2 job plus side income: withholding vs estimates | M | /tools/paycheck-tax-calculator/, product 07; idea 21 |
| Hobby or business? | L | content only; idea 22 |

### 1099 contractors and gig workers
| Question / pain point | Signal | Maps to |
|---|---|---|
| Standard mileage vs actual expenses | H | /tools/mileage-deduction-calculator/, Mileage Log (14), Driver Tracker (28) |
| Which miles count (commute, first pickup, between orders) | H | same; idea 6 |
| Platform 1099 doesn't match what hit my bank (gross vs net, fees) | M | Driver Tracker (28) |
| Phone, data, hot bags, car washes: deductible? | M | Driver Tracker (28), /tools/is-it-deductible/ |
| Self-employment tax surprise (15.3%) | H | /tools/1099-tax-calculator/; idea 1 |
| Client wants a W-9: sole proprietor or LLC? Do I need an LLC? | M | /llc-formation/; idea 13 |
| Didn't get a 1099 at all | H | 1099 Income Tracker (10); idea 2 |
| Got a 1099-K from PayPal/Venmo for personal payments | M | content only; idea 17 |
| Booth rent, tools and classes for stylists | M (Pinterest A) | Hair Stylist Tracker (30b); shorted 2026-10-24 |
| Quarterly due dates | H | /tools/tax-deadlines-2027/ |

### Small business owners
| Question / pain point | Signal | Maps to |
|---|---|---|
| How do I pay myself from my LLC? (owner's draw vs salary) | H | /tools/s-corp-tax-savings-calculator/, Bookkeeping Spreadsheet (11); idea 7 |
| Personal purchase on the business card: how to record it | H | Bookkeeping Cleanup (03); idea 3 |
| Bank balance doesn't match QuickBooks / reconciliation off | H | Month-End Close (18), /bookkeeping-cleanup/; idea 8 |
| Months behind on bookkeeping: how to catch up | H | Bookkeeping Cleanup (03), /bookkeeping-cleanup/ service |
| When does an S corp make sense; reasonable salary | M | S Corp calculator (19); shorted 2026-10-24 |
| Do I need to send a 1099 to this contractor? ($2,000 for 2026 payments) | H | /tools/do-i-need-to-send-a-1099/, 1099 Kit (01); shorted 2026-10-24 |
| Do I need a separate business bank account? | H | Bookkeeping Spreadsheet (11); idea 11 |
| Chart of accounts setup in QuickBooks | M (Pinterest B) | QuickBooks COA pack (23); idea 23 |
| Profitable on paper, no cash | M | Budget + 13-Week Cash Flow (31); idea 19 |
| Pricing: margin vs markup, break-even | M | /tools/profit-margin-calculator/, /tools/break-even-calculator/; idea 20 |
| What to do before Dec 31 | H (seasonal) | Year-End Checklist (17); /blog/year-end-tax-planning-2026-key-dates/ |
| Buy equipment before year end to cut tax? | M | /blog/section-179-bonus-depreciation-2026/; idea 24 |
| Which tax form does my LLC file? | M | /blog/which-tax-form-llc-corporation/ |

### Etsy and online sellers
| Question / pain point | Signal | Maps to |
|---|---|---|
| Will I get a 1099-K? What's the threshold now? | H | Online Seller Bookkeeping Sheet (22); idea 5 |
| My 1099-K is higher than what I made (gross vs net) | H | same; idea 5 |
| Do I collect or pay sales tax on Etsy sales? | H | /blog/nj-sales-tax-st50-filing-guide/; idea 18 |
| Cost of goods sold, year-end inventory count | M | Reseller Year-End Kit (32); idea 12 |
| Are Etsy fees and shipping supplies deductible? | M | Online Seller Bookkeeping Sheet (22); idea 27 |
| Do I need an LLC to sell on Etsy? | M | /llc-formation/ |
| Selling used personal items: taxable? | M | idea 30 |

### Sources read (2026-10-24)
Community threads (topics only, not quoted):
- TurboTax Community: [income under $600](https://ttlc.intuit.com/questions/3197785-do-i-have-to-report-income-under-600),
  [no 1099 received](https://ttlc.intuit.com/community/taxes/discussion/no-1099-form/00/1281664),
  [% to set aside as a contractor](https://ttlc.intuit.com/community/get-your-taxes-done-using-turbotax-6/as-an-independent-contractor-about-how-much-percentage-wise-should-i-be-setting-aside-to-cover-taxes-191416),
  [what an Uber driver can deduct](https://ttlc.intuit.com/community/taxes/discussion/what-can-an-uber-driver-deduct/00/755781),
  [cell phone use for Uber](https://ttlc.intuit.com/community/self-employed-27/figuring-out-my-cell-phone-usage-for-my-uber-business-997910),
  [home office](https://ttlc.intuit.com/community/business-taxes/discussion/home-office/00/3208446),
  [payment plan](https://ttlc.intuit.com/community/taxes/discussion/payment-plan/00/2656034),
  [S corp owner pay](https://ttlc.intuit.com/community/get-your-taxes-done-using-turbotax-6/s-corp-owner-pay-297102),
  [to LLC or not](https://ttlc.intuit.com/community/business-farm-10/to-llc-or-not-to-llc-831488),
  [COGS with no inventory](https://ttlc.intuit.com/community/deductions-credits-9/deducting-costs-of-goods-no-inventory-756759),
  [SE health insurance and IRA](https://ttlc.intuit.com/community/deductions-credits-9/self-employed-health-insurance-deduction-disappears-with-larger-ira-contribution-743758)
- QuickBooks Community: [personal expense on a business card](https://quickbooks.intuit.com/community/reports-and-accounting-5/how-do-i-handle-a-personal-expense-on-a-business-credit-card-59363),
  [categorize a personal purchase](https://quickbooks.intuit.com/community/reports-and-accounting-5/how-do-i-categorize-a-personal-purchase-on-a-business-credit-card-64713),
  [bank and books not matching](https://quickbooks.intuit.com/community/banking-4/quickbooks-and-bank-balance-not-matching-32520),
  [beginning balance off](https://quickbooks.intuit.com/learn-support/en-us/banking/beginning-bank-balance/00/260102)
- Etsy: [1099-K question](https://community.etsy.com/t5/Direct-Checkout/1099-K-Question/m-p/42681751/highlight/true),
  [tax help](https://community.etsy.com/t5/Etsy-Success/Tax-Help-Please-How-Does-it-Work/m-p/119236063),
  [Etsy Help: 1099-K](https://help.etsy.com/hc/articles/360000336447)
- Upwork Community: [W-9 legal name of business](https://community.upwork.com/t5/Freelancers/Tax-Information-gt-W-9-gt-Legal-Name-of-Business/td-p/770394)
- eBay Community: [cost of goods purchased earlier](https://community.ebay.com/t5/Selling/How-to-List-Cost-of-Goods-Purchased-Previously/td-p/33677788)
- TheTaxBook forum: [deductions for Uber drivers](https://forum.thetaxbook.com/forum/discussion-forums/main-forum-tax-discussion/28459-deductions-for-uber-drivers)

Primary sources checked for the first five tip shorts (2026-10-24):
- [IRS: Self-employment tax](https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-and-medicare-taxes) (15.3%, $400; updated 27-Jun-2026)
- [IRS: Form 1099-K FAQs, general information](https://www.irs.gov/newsroom/form-1099-k-faqs-general-information) ($20,000 / 200; all income taxable; gross amount; updated 03-Apr-2026)
- [IRS IR-2023-35: report all income](https://irs.gov/newsroom/tax-time-guide-irs-reminder-to-report-all-income-gig-economy-and-service-industry-digital-or-foreign-assets-and-sources)
- [IRS: How long should I keep records?](https://irs.gov/businesses/small-businesses-self-employed/how-long-should-i-keep-records) (updated 30-Jun-2026)
- [IRS FAQ: income and expenses](https://irs.gov/faqs/small-business-self-employed-other-business/income-expenses/income-expenses-1) (updated 30-Sep-2026)
- [Etsy Help: Form 1099-K](https://help.etsy.com/hc/articles/360000336447) (state thresholds)
