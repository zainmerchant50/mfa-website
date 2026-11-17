#!/usr/bin/env python3
"""/answers/ Q&A library (Site, 2026-11-17). Zain: "Add the website features you recommended above" (niche-growth-plan #1).

One short page per question people ask Copilot, Bing and Google in our niches (Bing grounding queries + Search Console,
claude/site/search-content-plan-2026-11-16.md). Built for AI answers: the question is the H1 and title, a 40-60 word direct
answer comes first, then a key-facts table, detail, links to the niche page and calculator, sources and the checked date,
with FAQPage schema. Every fact was read on irs.gov on CHECKED (see SOURCES per answer). Add a row to ANSWERS to add a page.
Never "free", never "CPA", no prices, no street address.
"""
import re
from datetime import date

import build_blog as B
import seo
import ui_kit
from build_resources import page, write, esc, BASE, cta

CHECKED = "2026-11-17"
I415 = ("IRS: Topic 415, Renting residential and vacation property", "https://www.irs.gov/taxtopics/tc415")
P527 = ("IRS: Publication 527, Residential Rental Property", "https://www.irs.gov/publications/p527")
T554 = ("IRS: Topic 554, Self-employment tax", "https://www.irs.gov/taxtopics/tc554")
P334 = ("IRS: Publication 334, Tax Guide for Small Business", "https://www.irs.gov/publications/p334")
OBBBA = ("IRS: One, Big, Beautiful Bill Act deductions for working Americans and seniors",
         "https://www.irs.gov/newsroom/one-big-beautiful-bill-act-tax-deductions-for-working-americans-and-seniors")
TIPLIST = ("IRS: Occupations that customarily and regularly received tips",
           "https://www.irs.gov/forms-pubs/occupations-that-customarily-and-regularly-received-tips-on-or-before-dec-31-2024")
S1A = ("IRS: Schedule 1-A (Form 1040), Additional Deductions", "https://www.irs.gov/pub/irs-pdf/f1040s1a.pdf")
ES = ("IRS: Form 1040-ES, Estimated Tax for Individuals (2026)", "https://www.irs.gov/pub/irs-pdf/f1040es.pdf")
T425 = ("IRS: Topic 425, Passive activities, losses and credits", "https://www.irs.gov/taxtopics/tc425")

I2553 = ("IRS: Instructions for Form 2553", "https://www.irs.gov/instructions/i2553")
SCOMP = ("IRS: S corporation compensation and medical insurance issues",
         "https://www.irs.gov/businesses/small-businesses-self-employed/s-corporation-compensation-and-medical-insurance-issues")
SCORP = ("IRS: S corporations", "https://www.irs.gov/businesses/small-businesses-self-employed/s-corporations")
K1099 = ("IRS: Form 1099-K threshold reverts to $20,000 (FAQs)",
         "https://www.irs.gov/newsroom/irs-issues-faqs-on-form-1099-k-threshold-under-the-one-big-beautiful-bill-dollar-limit-reverts-to-20000")
KUND = ("IRS: Understanding your Form 1099-K", "https://www.irs.gov/businesses/understanding-your-form-1099-k")
NJREM = ("NJ Division of Taxation: Remote sellers", "https://www.nj.gov/treasury/taxation/remotesellers.shtml")
I5472 = ("IRS: Instructions for Form 5472", "https://www.irs.gov/instructions/i5472")
BOI = ("FinCEN: Beneficial ownership information reporting", "https://www.fincen.gov/boi")
CAL27 = ("MFA: 2027 tax calendar (federal, NJ, NY)", "https://mfa-advisory.com/tools/2027-tax-calendar/")

LANES = [("booth", "Booth renters and beauty pros", "/booth-renters/", "Booth renter taxes"),
         ("airbnb", "Airbnb and short-term rental hosts", "/rental-property-taxes/", "Rental property taxes"),
         ("landlord", "Landlords and real estate investors", "/rental-property-taxes/", "Rental property taxes"),
         ("scorp", "S corp and LLC owners", "/s-corp-election/", "S corp election"),
         ("ecom", "Online sellers (Etsy, Shopify, Amazon)", "/bookkeeping-cleanup/", "Bookkeeping for online sellers"),
         ("foreign", "Foreign-owned US LLCs", "/llc-formation/", "LLC formation and compliance")]

# slug, lane, question, answer (40-60 words, plain text), facts [(k, v)], detail html, tool (href, label) or None, sources
ANSWERS = [
    ("do-booth-renters-pay-self-employment-tax", "booth", "Do salon booth renters pay self-employment tax?",
     "Yes. A booth renter runs their own business, so the profit goes on Schedule C and self-employment tax of 15.3% applies "
     "once net earnings are $400 or more. That is 12.4% for Social Security and 2.9% for Medicare. Nobody withholds it, "
     "so most booth renters pay quarterly estimated tax.",
     [("Forms", "Schedule C and Schedule SE with Form 1040"), ("Rate", "15.3% (12.4% Social Security + 2.9% Medicare)"),
      ("Applies from", "$400 of net earnings from self-employment"), ("Paid through", "Quarterly estimated payments (Form 1040-ES)")],
     "<p>Self-employment tax is figured on your <strong>profit</strong>, not your total sales, so every booth rent payment, supply order and "
     "license fee you record lowers it. The Social Security part stops at the yearly wage base; the Medicare part does not. "
     "You can deduct half of your self-employment tax when you figure your income tax.</p>",
     ("/tools/1099-tax-calculator/", "1099 tax calculator"), [T554, P334, ES]),
    ("is-booth-rent-tax-deductible", "booth", "Is booth rent tax deductible?",
     "Yes. If you rent a chair, booth or suite to run your own beauty business, the rent is a business expense you deduct on "
     "Schedule C. So are the supplies, tools, license renewals and education you pay for. Keep the lease or receipts, "
     "because the deduction lowers both income tax and self-employment tax.",
     [("Where it goes", "Schedule C, rent or lease line"), ("Also deductible", "Supplies, tools, licenses, education, booking apps"),
      ("Not deductible", "Personal haircuts, clothes you could wear anywhere"), ("Lowers", "Income tax and self-employment tax")],
     "<p>Booth rent paid to the salon owner is rent for business property. If you pay it weekly by app, download the yearly "
     "history so you can match it to your bank account. Mixed personal and business costs, like a phone, are deducted only for the business share.</p>",
     ("/tools/is-it-deductible/", "Is it deductible? checker"), [P334, T554]),
    ("do-hairstylists-qualify-for-no-tax-on-tips", "booth", "Do hairstylists qualify for no tax on tips?",
     "Yes. Barbers, hairstylists, cosmetologists, nail techs, lash and brow techs and makeup artists are on the IRS tipped "
     "occupations list. For 2025 through 2028 you can deduct up to $25,000 of qualified tips. The deduction shrinks above "
     "$150,000 of modified AGI ($300,000 joint). Booth renters qualify too, up to their net profit.",
     [("Years", "2025 through 2028"), ("Cap", "$25,000 of qualified tips a year"),
      ("Phase-out", "$100 less for each $1,000 of MAGI over $150,000 ($300,000 joint)"), ("Form", "Schedule 1-A, Part II"),
      ("Rules", "Valid SSN; married couples must file jointly")],
     "<p>The deduction lowers federal income tax only. Social Security and Medicare tax, or self-employment tax for booth renters, "
     "still applies to every tip. Some self-employed service businesses are excluded, and a required service charge is not a tip.</p>",
     ("/tools/no-tax-on-tips-calculator/", "No tax on tips calculator"), [OBBBA, TIPLIST, S1A]),
    ("estimated-tax-due-dates-2026", "booth", "When are 2026 estimated tax payments due?",
     "The four 2026 federal estimated tax payments are due April 15, June 15 and September 15, 2026, and January 15, 2027. "
     "Self-employed people, booth renters and landlords generally pay them if they expect to owe $1,000 or more for the year, "
     "because no employer withholds tax for them.",
     [("1st payment", "April 15, 2026"), ("2nd payment", "June 15, 2026"), ("3rd payment", "September 15, 2026"),
      ("4th payment", "January 15, 2027"), ("Form", "1040-ES (pay online with IRS Direct Pay or EFTPS)")],
     "<p>Each payment covers income earned in its period, so a slow first quarter can mean a smaller first payment. "
     "Paying too little, or late, can mean an underpayment penalty. New Jersey and New York use the same four dates for their own estimates.</p>",
     ("/tools/quarterly-estimated-tax-calculator/", "Quarterly estimated tax calculator"), [ES]),
    ("do-i-report-airbnb-income-under-15-days", "airbnb", "Do I report Airbnb income under 15 days?",
     "Not if the place is also your home. If you use a dwelling as a home and rent it for fewer than 15 days in the year, "
     "you don't report the rental income or deduct rental expenses. From 15 rental days on, you report all of it "
     "and split expenses between rental and personal use.",
     [("Rule", "Rented under 15 days and used as a home"), ("Income", "Not reported"), ("Rental expenses", "Not deducted"),
      ("Still deductible", "Mortgage interest and property taxes, if you itemize"), ("Source", "IRS Topic 415")],
     "<p>“Used as a home” means your personal days are more than the greater of 14 days or 10% of the days it was rented "
     "at a fair price. A property you never stay in doesn't get this rule: rent it even a few nights and the income is reported.</p>",
     ("/tools/airbnb-host-tax-checker/", "Airbnb host tax checker"), [I415, P527]),
    ("airbnb-income-schedule-c-or-schedule-e", "airbnb", "Is Airbnb income reported on Schedule C or Schedule E?",
     "Most hosts use Schedule E. If you provide substantial services mainly for guests' convenience, such as regular cleaning "
     "during stays, changing linens or maid service, the income goes on Schedule C instead, like a hotel. Schedule C income "
     "is usually also subject to 15.3% self-employment tax.",
     [("Space only, cleaning between guests", "Schedule E"), ("Hotel-style services during stays", "Schedule C"),
      ("Self-employment tax", "Usually only on Schedule C"), ("Source", "IRS Publication 527")],
     "<p>Utilities, trash collection and cleaning of common areas don't count as substantial services. "
     "The choice changes your tax, so decide it from what you actually provide, not from what the platform calls you.</p>",
     ("/tools/airbnb-host-tax-checker/", "Airbnb host tax checker"), [P527, T554]),
    ("airbnb-personal-use-days-limit", "airbnb", "How many personal days can an Airbnb host use?",
     "Up to 14 days or 10% of the days it was rented at a fair price, whichever is more. Go over that and the IRS treats the "
     "rental as your home: you still deduct the rental share of expenses, but they can't be more than your rental income, "
     "so the rental can't show a loss.",
     [("Limit", "Greater of 14 days or 10% of fair-rental days"), ("Counts as personal", "You, family, friends, below-market rentals"),
      ("Over the limit", "No rental loss allowed"), ("Source", "IRS Topic 415, Publication 527")],
     "<p>Example: rented 200 nights, personal limit 20 nights (10% of 200). Days spent mainly repairing or maintaining the "
     "property don't count as personal days.</p>",
     ("/tools/airbnb-host-tax-checker/", "Airbnb host tax checker"), [I415, P527]),
    ("how-many-years-to-depreciate-rental-property", "landlord", "How many years do you depreciate a rental property?",
     "27.5 years for a residential rental building, using the mid-month convention. Divide the building's basis by 27.5 for "
     "each full year; the first and last years are partial. Land is never depreciated, so take its value out of the price "
     "before you start.",
     [("Recovery period", "27.5 years (residential rental)"), ("Method", "Straight line, mid-month convention"),
      ("Not depreciated", "Land"), ("First year", "Partial, from the middle of the month placed in service"), ("Form", "Form 4562, then Schedule E")],
     "<p>Basis is usually the purchase price plus certain closing costs, minus land. Improvements, like a new roof, start their "
     "own 27.5-year schedule. When you sell, depreciation you took, or could have taken, is taxed back.</p>",
     ("/tools/rental-depreciation-calculator/", "Rental depreciation calculator"), [P527]),
    ("when-does-rental-property-depreciation-start", "landlord", "When does depreciation start on a rental property?",
     "When the property is placed in service, meaning ready and available to rent, not when the first tenant moves in. "
     "A house listed for rent in March starts depreciating in March even if it stays empty until June. Depreciation stops "
     "when you have recovered its cost or take it out of service.",
     [("Starts", "Ready and available for rent"), ("Not", "The first tenant's move-in date"),
      ("First-year amount", "Mid-month convention"), ("Stops", "Cost fully recovered, or retired from service")],
     "<p>Keep proof of the date: the listing, photos of the finished unit, or the agent's email. It sets every year of your schedule.</p>",
     ("/tools/rental-depreciation-calculator/", "Rental depreciation calculator"), [P527]),
    ("is-a-new-roof-on-a-rental-a-repair-or-improvement", "landlord", "Is a new roof on a rental a repair or improvement?",
     "A new roof is an improvement. You add it to the property's basis and depreciate it over 27.5 years. Fixing a leak or "
     "replacing a few shingles is a repair, deducted in the year you pay. Items costing $2,500 or less per invoice or item can be "
     "deducted under the de minimis safe harbor if you elect it.",
     [("Whole new roof", "Improvement, 27.5 years"), ("Patch or a few shingles", "Repair, deduct now"),
      ("De minimis safe harbor", "$2,500 per invoice or item, elected each year"), ("Source", "IRS Publication 527")],
     "<p>The test is whether the work betters, restores or adapts the property. Read the full guide: "
     "<a href=\"/blog/rental-property-repairs-vs-improvements-2026/\">rental property repairs vs improvements</a>.</p>",
     ("/tools/rental-depreciation-calculator/", "Rental depreciation calculator"), [P527]),
    ("can-a-rental-loss-offset-w2-income", "landlord", "Can a rental property loss offset my W-2 income?",
     "Up to $25,000 a year, if you actively participate in managing the rental. The allowance phases out as modified AGI "
     "goes from $100,000 to $150,000, and married couples filing separately get less. Losses you can't use carry forward "
     "to future years or until you sell.",
     [("Allowance", "Up to $25,000 a year"), ("Requires", "Active participation (approving tenants, setting rent, approving repairs)"),
      ("Phase-out", "MAGI $100,000 to $150,000"), ("Unused loss", "Carries forward"), ("Form", "Form 8582")],
     "<p>Real estate professionals follow different rules. A short-term rental with a short average stay may not count as a "
     "rental activity at all, so ask before counting on this allowance.</p>",
     None, [T425, P527]),
    ("is-a-security-deposit-taxable-income", "landlord", "Is a security deposit taxable rental income?",
     "Not when you get it, if you may have to return it. It becomes income in the year you keep any of it, for example for "
     "damage or unpaid rent. A deposit that will be used as the last month's rent is advance rent, which is income in the year "
     "you receive it.",
     [("Refundable deposit", "Not income when received"), ("Deposit you keep", "Income in the year you keep it"),
      ("Last month's rent paid upfront", "Advance rent, income when received"), ("Source", "IRS Publication 527")],
     "<p>Keep deposits in a separate account or ledger line so they don't get counted as rent by mistake.</p>",
     None, [P527]),
    ("s-corp-election-deadline-2027", "scorp", "When is the deadline to elect S corp status for 2027?",
     "For an LLC or corporation on the calendar year, file Form 2553 by March 15, 2027 for the election to start January 1, 2027. "
     "The rule is no more than 2 months and 15 days after the start of the tax year. File later and the election usually starts in 2028, "
     "unless you qualify for late-election relief.",
     [("Form", "2553, Election by a Small Business Corporation"), ("Deadline for 2027", "March 15, 2027"),
      ("Rule", "Within 2 months and 15 days of the tax year start"), ("Who signs", "Every shareholder (LLC members)"),
      ("Missed it", "Late-election relief may be available")],
     "<p>An LLC can elect S corp tax treatment without changing its state registration. Before you elect, compare the payroll tax "
     "you save with the extra cost of payroll and a separate Form 1120-S return.</p>",
     ("/tools/s-corp-tax-savings-calculator/", "S corp tax savings calculator"), [I2553, CAL27]),
    ("do-s-corp-owners-have-to-take-a-salary", "scorp", "Do S corp owners have to pay themselves a salary?",
     "Yes, if you work in the business. The IRS requires an S corporation to pay a shareholder who provides services reasonable "
     "compensation as W-2 wages before taking non-wage distributions. Wages carry Social Security and Medicare tax; distributions "
     "don't, which is where the savings come from and why the IRS watches salaries.",
     [("Rule", "Reasonable compensation before distributions"), ("Paid as", "W-2 wages through payroll"),
      ("Taxes on wages", "Social Security and Medicare, plus income tax withholding"), ("Distributions", "No payroll tax"),
      ("Risk", "IRS can reclassify distributions as wages")],
     "<p>Reasonable means what you'd pay someone else to do your job: think duties, hours and what similar businesses pay. "
     "Write down how you set the number and review it each year.</p>",
     ("/tools/s-corp-tax-savings-calculator/", "S corp tax savings calculator"), [SCOMP, SCORP]),
    ("when-is-form-1120-s-due-2027", "scorp", "When is the 2026 S corp return (Form 1120-S) due?",
     "March 15, 2027 for a calendar-year S corporation, together with a Schedule K-1 for each shareholder. Form 7004 extends the "
     "filing deadline six months, to September 15, 2027. The S corp itself usually pays no federal income tax; owners report "
     "their share of profit on their own returns.",
     [("Return", "Form 1120-S plus Schedules K-1"), ("Due", "March 15, 2027"), ("Extension", "Form 7004, to September 15, 2027"),
      ("Owners report", "K-1 income on their personal returns"), ("Partnerships (Form 1065)", "Same dates")],
     "<p>Owners can't file their personal return until they have their K-1, so filing the 1120-S on time keeps everyone's April "
     "deadline realistic. New Jersey and New York have their own S corp filings.</p>",
     ("/tools/2027-tax-calendar/", "2027 tax calendar"), [SCORP, CAL27]),
    ("is-my-1099-k-amount-my-income", "ecom", "Is the amount on my 1099-K my income?",
     "No. A 1099-K shows the gross payments processed for you, before platform fees, refunds, shipping and sales tax are taken out. "
     "You report your gross sales, then deduct fees, refunds and other costs as business expenses. Your payouts, which arrive net, "
     "won't match the form, and that's expected.",
     [("1099-K shows", "Gross payments, before fees and refunds"), ("Your payouts", "Net of fees and refunds"),
      ("You report", "Gross sales, then expenses and returns"), ("Where", "Schedule C for most sellers")],
     "<p>Book each payout as gross sales, then the fees and refunds as separate lines. That way your books tie to the 1099-K "
     "and to your bank deposits, and the IRS sees the same total it was sent.</p>",
     None, [KUND, K1099]),
    ("when-do-online-sellers-get-a-1099-k", "ecom", "When do online sellers get a 1099-K?",
     "Payment platforms and marketplaces such as Etsy, Shopify and Amazon must send a 1099-K when your payments for the year exceed "
     "$20,000 and you have more than 200 transactions, the threshold restored by the One Big Beautiful Bill Act. Below that you may "
     "get no form, but every sale is still income you report.",
     [("Threshold", "Over $20,000 and over 200 transactions"), ("Sent by", "Payment platforms and marketplaces"),
      ("No form?", "Sales are still taxable income"), ("Check", "Form totals against your own records")],
     "<p>If a 1099-K is wrong, for example personal transfers included, ask the issuer to correct it and keep records showing "
     "what the payments were.</p>",
     None, [K1099, KUND]),
    ("do-online-sellers-collect-nj-sales-tax", "ecom", "Do online sellers have to collect NJ sales tax?",
     "Yes, once your sales into New Jersey exceed $100,000 or reach 200 separate transactions in the current or prior year, you must "
     "register, collect and remit New Jersey sales tax. Sales through a marketplace like Etsy or Amazon are different: the marketplace "
     "collects and remits the tax for those.",
     [("Threshold", "Over $100,000 in sales or 200+ transactions into NJ"), ("Period", "Current or prior calendar year"),
      ("Marketplace sales", "The marketplace collects the tax"), ("Your own site", "You collect once over the threshold")],
     "<p>Selling through your own Shopify store and a marketplace? Track the two channels separately, because only your own-site "
     "sales are your responsibility. Other states have their own thresholds.</p>",
     None, [NJREM]),
    ("does-a-foreign-owned-llc-file-form-5472", "foreign", "Does a foreign-owned US LLC file Form 5472?",
     "Yes. A US single-member LLC owned by a foreign person files Form 5472 attached to a pro forma Form 1120 for any year it has "
     "reportable transactions with its owner, including money put in or taken out. The penalty for not filing is $25,000, plus more "
     "if it stays unfiled after an IRS notice.",
     [("Forms", "Form 5472 with a pro forma Form 1120"), ("Who", "Foreign-owned US single-member LLCs"),
      ("Reportable", "Transactions with the owner, including contributions and distributions"), ("Penalty", "$25,000 per form, more after 90 days"),
      ("Due", "With the pro forma 1120: April 15 for calendar-year; Form 7004 extends")],
     "<p>Only a few lines of the Form 1120 are filled in, but the LLC also needs an EIN and records of every transaction with the owner. "
     "Missing it is one of the costliest mistakes foreign founders make.</p>",
     None, [I5472]),
    ("does-a-foreign-owned-llc-file-a-boi-report", "foreign", "Does a foreign-owned US LLC file a BOI report?",
     "No, not under FinCEN's current rule. Companies formed in the United States are exempt from beneficial ownership information "
     "reporting, whoever owns them, so a US LLC with a foreign owner doesn't file. Only companies formed abroad and registered to do "
     "business in a US state still report.",
     [("US-formed LLC", "Exempt, even with a foreign owner"), ("Still report", "Foreign companies registered in a US state"),
      ("Rule", "FinCEN, finalized August 2026"), ("Still required", "IRS filings such as Form 5472")],
     "<p>BOI rules have changed several times since 2024. The IRS filings don't change with them, so a foreign-owned LLC still files "
     "Form 5472 every year it has transactions with its owner.</p>",
     None, [BOI, I5472]),
]


PRICE = {"scorp": "/s-corp-election/#prices", "ecom": "/bookkeeping-cleanup/#quote", "foreign": "/book/"}


def url(slug):
    return f"{BASE}/answers/{slug}/"


CSS = """<style>
.ans-main{padding:48px 0 24px}
.ans-lay{max-width:var(--maxw,1180px);margin:0 auto;padding:0 24px;display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:40px;align-items:start}
.ans-art{min-width:0;font-size:1.02rem;line-height:1.65;color:var(--ink)}
.ans-art h2{font-size:1.3rem;margin:34px 0 12px;color:var(--navy)}
.ans-art p{margin:0 0 14px}
.ans-box{background:#fff;border:1px solid rgba(176,141,63,.35);border-left:5px solid var(--gold,#b08d3f);border-radius:16px;padding:22px 24px;box-shadow:0 10px 30px rgba(15,35,64,.06)}
.ans-box .lbl{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:8px}
.ans-box p{margin:0;font-size:1.12rem;line-height:1.6}
.ans-facts{width:100%;border-collapse:separate;border-spacing:0;background:#fff;border:1px solid rgba(21,21,21,.1);border-radius:14px;overflow:hidden;font-size:.96rem}
.ans-facts th,.ans-facts td{text-align:left;padding:12px 16px;border-bottom:1px solid rgba(21,21,21,.08);vertical-align:top}
.ans-facts tr:last-child th,.ans-facts tr:last-child td{border-bottom:0}
.ans-facts th{width:36%;background:#faf8f3;color:var(--navy);font-weight:600}
.ans-art a{color:var(--navy);border-bottom:1px solid var(--gold)}
.ans-rel{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.ans-rel a{display:flex;justify-content:space-between;gap:12px;align-items:center;background:#fff;border:1px solid rgba(21,21,21,.1);border-radius:12px;padding:12px 16px;color:var(--navy);border-bottom-width:1px;font-weight:500;text-decoration:none}
.ans-rel a:hover{border-color:var(--gold)}
.ans-rel a::after{content:"\\2192";color:var(--gold)}
.ans-src{margin-top:30px;padding-top:18px;border-top:1px solid rgba(21,21,21,.1);font-size:.88rem;color:var(--muted)}
.ans-src h2{font-size:1rem;margin:0 0 8px}
.ans-src ul{margin:0 0 8px;padding-left:18px}
.ans-side{position:sticky;top:96px;display:grid;gap:16px}
.ans-card{background:var(--navy,#0f2340);color:#fff;border-radius:18px;padding:22px}
.ans-card .lbl{font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--gold)}
.ans-card h3{color:#fff;font-size:1.2rem;margin:8px 0 8px}
.ans-card p{color:rgba(255,255,255,.8);font-size:.92rem;margin:0 0 14px;font-weight:300}
.ans-card .btn{width:100%;justify-content:center;margin-top:8px}
.ans-card .btn-line{color:#fff;border-color:rgba(255,255,255,.4)}
.ans-tool{background:#fff;border:1px solid rgba(21,21,21,.1);border-radius:18px;padding:18px 20px}
.ans-tool .lbl{font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.ans-tool a{display:block;margin-top:6px;color:var(--navy);font-weight:600}
.ans-idx{max-width:var(--maxw,1180px);margin:0 auto;padding:40px 24px 10px}
.ans-jump{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 30px}
.ans-jump a{border:1px solid rgba(21,21,21,.14);border-radius:999px;padding:8px 14px;font-size:.88rem;color:var(--navy);background:#fff;text-decoration:none}
.ans-jump a:hover{border-color:var(--gold)}
.ans-lane{margin:0 0 40px;scroll-margin-top:96px}
.ans-lane-hd{display:flex;justify-content:space-between;align-items:baseline;gap:16px;border-bottom:1px solid rgba(21,21,21,.1);padding-bottom:10px;margin-bottom:16px}
.ans-lane-hd h2{font-size:1.35rem;margin:0;color:var(--navy)}
.ans-lane-hd a{font-size:.9rem;color:var(--navy);border-bottom:1px solid var(--gold);white-space:nowrap;text-decoration:none}
.ans-list{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.ans-list a{display:block;background:#fff;border:1px solid rgba(21,21,21,.1);border-radius:16px;padding:18px 20px;text-decoration:none;color:var(--ink);height:100%;transition:border-color .2s,box-shadow .2s}
.ans-list a:hover{border-color:var(--gold);box-shadow:0 8px 24px rgba(15,35,64,.08)}
.ans-list b{display:block;color:var(--navy);margin-bottom:6px;font-size:1.02rem}
.ans-list span{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;font-size:.9rem;color:var(--muted);font-weight:300;line-height:1.55}
@media(max-width:900px){.ans-lay{grid-template-columns:1fr;gap:28px}.ans-side{position:static}}
@media(max-width:720px){.ans-list{grid-template-columns:1fr}.ans-facts th{width:42%}.ans-lay,.ans-idx{padding-left:16px;padding-right:16px}.ans-main{padding-top:32px}.ans-lane-hd{flex-direction:column;gap:4px}}
</style>"""


def desc_of(answer):
    """First sentence(s) of the answer, trimmed to 155 characters for the meta description."""
    out = ""
    for s in re.split(r"(?<=\.)\s+", answer):
        if len(out) + len(s) + 1 > 155:
            break
        out = (out + " " + s).strip()
    return out if len(out) >= 50 else answer[:152].rsplit(" ", 1)[0] + "…"


def build_one(a, nice):
    slug, lane, q, ans, facts, detail, tool, srcs = a
    ln = next(x for x in LANES if x[0] == lane)
    u = url(slug)
    rows = "".join(f'<tr><th scope="row">{esc(k)}</th><td>{esc(v)}</td></tr>' for k, v in facts)
    src = "".join(f'<li><a href="{esc(s[1])}" target="_blank" rel="noopener">{esc(s[0])}</a></li>' for s in srcs)
    others = [x for x in ANSWERS if x[1] == lane and x[0] != slug][:4]
    more = "".join(f'<li><a href="/answers/{x[0]}/">{esc(x[2])}</a></li>' for x in others)
    tool_html = (f'<div class="ans-tool"><span class="lbl">Try it with your numbers</span><a href="{tool[0]}">{esc(tool[1])} →</a></div>' if tool else "")
    body = f'''{CSS}<header class="bhero"><div class="wrap"><span class="eyebrow">Tax answers · {esc(ln[1])}</span>
<h1>{esc(q)}</h1><p>Short answer first, checked against official sources on {nice}.</p></div></header>
<main class="ans-main"><div class="ans-lay"><article class="ans-art">
<div class="ans-box"><span class="lbl">Short answer</span><p>{esc(ans)}</p></div>
<h2>Key facts</h2><table class="ans-facts"><tbody>{rows}</tbody></table>
<h2>What else to know</h2>{detail}
<h2>Related questions</h2><ul class="ans-rel">{more}<li><a href="/answers/">All tax answers</a></li></ul>
<section class="ans-src"><h2>Sources</h2><ul>{src}</ul><p>Checked against the sources above on {nice}. General information, not tax advice for your situation.</p></section>
</article>
<aside class="ans-side"><div class="ans-card"><span class="lbl">{esc(ln[1])}</span><h3>Want this handled for you?</h3>
<p>Tell us what you need and we'll email a fixed quote within one business day.</p>
<a class="btn btn-gold" href="{PRICE.get(lane, ln[2] + '#get-price')}">Get my price</a><a class="btn btn-line" href="{ln[2]}">{esc(ln[3])}</a></div>{tool_html}</aside>
</div></main>
{cta("Want this applied to your return?", "Book a 30-minute call or phone <a href='tel:+13472054468' data-conv='call'>(347) 205-4468</a>. We quote before any work starts.")}'''
    d = desc_of(ans)
    faq = {"@type": "FAQPage", "@id": u + "#faq", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}]}
    ld = seo.graph(u, q, d, faq, crumb=[("Home", BASE + "/"), ("Tax answers", BASE + "/answers/"), (q, u)])
    return write(f"answers/{slug}", page(f"{q} | MFA", d, u, body, ld, active="res", keywords=[q.rstrip("?").lower(), ln[3].lower(), "tax answers"]))


def build_index(nice):
    u = BASE + "/answers/"
    jump, lanes = "", ""
    for key, name, href, label in LANES:
        lst = [a for a in ANSWERS if a[1] == key]
        if not lst:
            continue
        jump += f'<a href="#{key}">{esc(name)} ({len(lst)})</a>'
        items = "".join(f'<li><a href="/answers/{a[0]}/"><b>{esc(a[2])}</b><span>{esc(desc_of(a[3]))}</span></a></li>' for a in lst)
        lanes += (f'<section class="ans-lane" id="{key}" aria-labelledby="h-{key}"><div class="ans-lane-hd"><h2 id="h-{key}">{esc(name)}</h2>'
                  f'<a href="{href}">{esc(label)} →</a></div><ul class="ans-list">{items}</ul></section>')
    title = "Tax Answers for Small Business Owners & Investors | MFA"
    d = ("Short, sourced answers to the tax questions booth renters, Airbnb hosts, landlords, S corp owners, online sellers and foreign LLC owners ask most.")
    body = f'''{CSS}<header class="bhero"><div class="wrap"><span class="eyebrow">Tax answers</span>
<h1>Tax answers, <em>short and sourced.</em></h1><p>{len(ANSWERS)} questions our clients ask most. Each page gives the answer in a few sentences, then the key facts and the official source. Checked {nice}.</p></div></header>
<main><div class="ans-idx"><nav class="ans-jump" aria-label="Jump to a topic">{jump}</nav>{lanes}</div>
{cta("Have a question that isn't here?", "Book a 30-minute call or email us. We answer before we quote.")}
</main>'''
    items = [{"@type": "ListItem", "position": i + 1, "url": url(a[0]), "name": a[2]} for i, a in enumerate(ANSWERS)]
    ld = seo.graph(u, "Tax answers", d, {"@type": "ItemList", "@id": u + "#list", "itemListElement": items},
                   crumb=[("Home", BASE + "/"), ("Tax answers", u)], kind="CollectionPage")
    return write("answers", page(title, d, u, body, ld, active="res", keywords=["tax answers", "booth renter taxes", "Airbnb host taxes", "landlord taxes", "S corp questions", "1099-K", "Form 5472"]))


def build():
    nice = date.fromisoformat(CHECKED).strftime("%B %-d, %Y")
    for a in ANSWERS:
        n = len(a[3].split())
        assert 40 <= n <= 62, f"{a[0]}: answer is {n} words (want 40-60)"
    return [build_index(nice)] + [build_one(a, nice) for a in ANSWERS]


if __name__ == "__main__":
    print("\n".join(build()))
