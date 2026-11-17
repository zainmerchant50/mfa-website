#!/usr/bin/env python3
"""Niche calculators (Site, 2026-11-17). Zain: "Add the website features you recommended above" (niche-growth-plan #2).

  /tools/no-tax-on-tips-calculator/      booth renters, stylists, barbers, servers (Schedule 1-A, Part II)
  /tools/airbnb-host-tax-checker/        short-term rental hosts (Topic 415 14-day rule, Pub 527 Schedule C vs E)
  /tools/rental-depreciation-calculator/ landlords (Pub 527: 27.5 years, mid-month convention, land excluded)

Each page ends with the shared "Get my price" box (tools/lead_box.py), which emails the visitor's results with the request.
Every rule below was read on irs.gov on CHECKED (2026-11-16/17): Schedule 1-A lines 1-13 (f1040s1a.pdf), the OBBBA
deductions page, the tipped occupations list, Topic 415 and Pub 527. Logic lives in site/resources/calc.js (MFA.pages.tips,
.airbnb, .deprec). Registered in build_calculators.py (reg + RELATED). Never "free", never "CPA", no prices.
"""
import build_calculators as C
import lead_box

CHECKED = "2026-11-17"
S_1A = ("IRS: Schedule 1-A (Form 1040), Additional Deductions", "https://www.irs.gov/pub/irs-pdf/f1040s1a.pdf")
S_OBBBA = ("IRS: One, Big, Beautiful Bill Act deductions for working Americans and seniors",
           "https://www.irs.gov/newsroom/one-big-beautiful-bill-act-tax-deductions-for-working-americans-and-seniors")
S_TIPLIST = ("IRS: Occupations that customarily and regularly received tips",
             "https://www.irs.gov/forms-pubs/occupations-that-customarily-and-regularly-received-tips-on-or-before-dec-31-2024")
S_415 = ("IRS: Topic 415, Renting residential and vacation property", "https://www.irs.gov/taxtopics/tc415")
S_527 = ("IRS: Publication 527, Residential Rental Property", "https://www.irs.gov/publications/p527")
S_554 = ("IRS: Topic 554, Self-employment tax", "https://www.irs.gov/taxtopics/tc554")

TIPS = {"cap": 25000, "th_single": 150000, "th_joint": 300000, "step": 1000, "cut": 100}
RATES = [("0.10", "10%"), ("0.12", "12%"), ("0.22", "22%"), ("0.24", "24%"), ("0.32", "32%"), ("0.35", "35%"), ("0.37", "37%")]
MONTHS = [(str(i), m) for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                             "September", "October", "November", "December"], 1)]


def build_tips():
    slug = "no-tax-on-tips-calculator"
    f = C.Facts()
    grid = ('<div class="tcard"><h2>Your tips and income</h2><p class="sub">For tax years 2025 through 2028. Nothing you type leaves your browser.</p>'
            f'<p class="factline">Rules checked {C.day(CHECKED)} on irs.gov</p>' +
            C.select("t-status", "Filing status", [("single", "Single, head of household or surviving spouse"), ("joint", "Married filing jointly"),
                                                   ("separate", "Married filing separately")]) +
            C.select("t-occ", "Is your job on the IRS tipped occupations list?", [("yes", "Yes (for example barber, stylist, nail tech, server, bartender)"),
                                                                                  ("unsure", "Not sure"), ("no", "No")],
                     "Barbers, hairstylists and cosmetologists (603), manicurists (605), lash and brow techs (606) and makeup artists (607) are on it") +
            C.money("t-w2", "Tips on your W-2 or Form 4137", "Box 7 of your W-2, plus tips you reported on Form 4137", "6,000") +
            C.money("t-se", "Tips earned as a self-employed person", "Booth renters: cash, card and app tips from your own clients", "8,000") +
            C.money("t-np", "Net profit of that self-employed business", "Schedule C profit after expenses. Self-employed tips count only up to this amount", "30,000") +
            C.money("t-magi", "Modified adjusted gross income (MAGI)", "Usually your AGI. Phase-out starts at $150,000 ($300,000 joint)", "62,000") +
            C.select("t-rate", "Your top federal tax bracket (for the savings estimate)", RATES, "", "0.12") + "</div>")
    kp = (C.kpi("k-ded", "Tips deduction", "wide gold") + C.kpi("k-save", "Rough federal income tax saved") +
          C.kpi("k-qual", "Qualified tips counted") + C.kpi("k-cut", "Phase-out reduction"))
    res = C.result_card("Your estimate", kp, cta_label="Have us check your tips")
    below = C.math_card(sub="Follows Schedule 1-A, Part II, lines 1 to 13. Nothing is rounded until the end.")
    info = """<h2>How much of my tips can I deduct?</h2>
<p><strong>Up to $25,000 of qualified tips a year, for 2025 through 2028.</strong> The deduction drops by $100 for every full $1,000 of modified AGI over $150,000 ($300,000 if married filing jointly). You can take it whether or not you itemize. Married couples must file jointly, and you need a valid Social Security number.</p>
<h2>Who counts as a tipped worker?</h2>
<ul><li><strong>Your job must be on the IRS list</strong> of occupations that customarily received tips before 2025. Barbers, hairstylists, cosmetologists, nail techs, lash and brow techs and makeup artists are on it.</li>
<li><strong>Employees:</strong> tips on your W-2 (box 7) and tips you reported on Form 4137 count.</li>
<li><strong>Self-employed and booth renters:</strong> tips count too, but only up to the net profit of the business the tips came from. Some self-employed service businesses are excluded.</li>
<li><strong>Tips must be voluntary.</strong> A required service charge is not a tip.</li></ul>
<h2>What the deduction does not do</h2>
<p>It lowers your federal income tax only. Social Security and Medicare tax (self-employment tax if you rent a booth) still apply to every tip, and state rules can differ. Booth renter? See <a href="/booth-renters/">booth renter taxes</a> for the full picture.</p>"""
    lead = lead_box.lead_box("No tax on tips", "calc-tips", "Want your tips deduction done right?",
                             "We prepare returns for stylists, barbers, nail techs and other tipped workers, employee or booth renter.",
                             [("tax-return", "Tax return with the tips deduction"), ("booth-renter", "Booth renter taxes and quarterly estimates"),
                              ("bookkeeping", "Monthly bookkeeping"), ("question", "A quick question first")],
                             ["A fixed quote before any work starts", "Tips, booth rent and self-employment tax handled together"], calc=True)
    return C.build_page(slug, "No Tax on Tips Calculator (2025–2028 Deduction)",
                        "Estimate the no tax on tips deduction: up to $25,000 of qualified tips, the $150,000 phase-out and the rules for booth renters.",
                        "No tax on tips", "No tax on tips calculator",
                        "Estimate the qualified tips deduction for 2025 to 2028, for employees and booth renters.",
                        grid + res, below, info, {"tips": TIPS}, "tips", f, "Tipped worker or booth renter?",
                        "We file returns for stylists, barbers and nail techs, including the tips deduction. Book a 30-minute consultation.",
                        extra_src=[S_1A, S_OBBBA, S_TIPLIST, S_554], extra_checked=[CHECKED], lead=lead)


def build_airbnb():
    slug = "airbnb-host-tax-checker"
    f = C.Facts()
    grid = ('<div class="tcard"><h2>Your rental year</h2><p class="sub">One property at a time. Nothing you type leaves your browser.</p>'
            f'<p class="factline">Rules checked {C.day(CHECKED)} on irs.gov</p>' +
            C.numf("a-rent", "Days rented at a fair price", "Nights guests paid market rate. Nights rented to family below market count as personal days", "120") +
            C.numf("a-pers", "Days of personal use", "Nights you, family or friends stayed, or it was rented below market", "10") +
            C.money("a-inc", "Rental income for the year", "Optional. Gross payouts before platform fees", "24,000") +
            C.money("a-exp", "Total expenses for the property", "Optional. Mortgage interest, taxes, cleaning, supplies, utilities, insurance", "15,000") +
            C.select("a-svc", "Do you provide hotel-style services?", [("no", "No, guests get the space (basic cleaning between stays is fine)"),
                                                                        ("yes", "Yes, regular cleaning during stays, fresh linens, meals or concierge")],
                     "Substantial services, like a hotel, move the income to Schedule C") + "</div>")
    kp = (C.kpi("k-form", "Where it goes", "wide gold") + C.kpi("k-home", "Used as a home?") +
          C.kpi("k-share", "Rental share of expenses") + C.kpi("k-ded", "Expenses you can deduct"))
    res = C.result_card("Your answer", kp, cta_label="Have us review your rental")
    below = C.math_card(sub="Follows IRS Topic 415 and Publication 527. Check the result against your own records.", title="How we got there")
    info = """<h2>Do I have to report Airbnb income?</h2>
<p><strong>Usually yes.</strong> The one exception: if the place is also your home and you rent it for fewer than 15 days in the year, you don't report the rental income and you don't deduct rental expenses (IRS Topic 415). From 15 rental days on, the income is reported and expenses are split between rental and personal days.</p>
<h2>When does the IRS treat a rental as my home?</h2>
<p>When your personal days are more than the greater of 14 days or 10% of the days it was rented at a fair price. A home that is also rented can still deduct its rental share of expenses, but those expenses can't create a rental loss.</p>
<h2>Schedule C or Schedule E for a short-term rental?</h2>
<table class="tbl ctbl"><thead><tr><th>You provide</th><th>Form</th><th>Self-employment tax</th></tr></thead><tbody>
<tr><td>The space, with cleaning between guests</td><td>Schedule E</td><td>No</td></tr>
<tr><td>Hotel-style services during stays: regular cleaning, linen changes, maid service, meals</td><td>Schedule C</td><td>Usually yes</td></tr></tbody></table>
<p>Owning a long-term rental too? See <a href="/rental-property-taxes/">rental property taxes</a>, and work out the building's yearly write-off with the <a href="/tools/rental-depreciation-calculator/">rental depreciation calculator</a>.</p>"""
    lead = lead_box.lead_box("Airbnb host taxes", "calc-airbnb", "Want a host who knows Airbnb taxes on your return?",
                             "We prepare returns for short-term rental hosts and landlords in NJ, NY and across the US.",
                             [("tax-return", "Tax return for my rental"), ("bookkeeping", "Monthly rental bookkeeping"),
                              ("cleanup", "Catch-up on past years"), ("question", "A quick question first")],
                             ["A fixed quote before any work starts", "Schedule C or E decided with you, not guessed"], calc=True)
    return C.build_page(slug, "Airbnb Host Tax Checker: 14-Day Rule, Schedule C or E",
                        "Check how the IRS treats your Airbnb or short-term rental: the 14-day rule, personal-use days, Schedule C or E, and the share of expenses you can deduct.",
                        "Airbnb host taxes", "Airbnb host tax checker",
                        "Enter rental and personal days to see the 14-day rule, the right schedule and your deductible share.",
                        grid + res, below, info, {"page": "airbnb"}, "airbnb", f, "Hosting on Airbnb or Vrbo?",
                        "We sort out the 14-day rule, the right schedule and depreciation for hosts. Book a 30-minute consultation.",
                        extra_src=[S_415, S_527, S_554], extra_checked=[CHECKED], lead=lead)


def build_deprec():
    slug = "rental-depreciation-calculator"
    f = C.Facts()
    grid = ('<div class="tcard"><h2>Your rental property</h2><p class="sub">Residential rental buildings only. Nothing you type leaves your browser.</p>'
            f'<p class="factline">Rules checked {C.day(CHECKED)} on irs.gov</p>' +
            C.money("d-price", "Purchase price plus closing costs", "Include settlement costs that add to basis, like title fees and transfer taxes", "400,000") +
            C.money("d-land", "Value of the land", "Land never depreciates. Your property tax bill often splits land and building", "100,000") +
            C.money("d-imp", "Improvements before renting", "Optional. A new roof or kitchen before the first tenant", "0") +
            C.select("d-month", "Month it was ready and available to rent", MONTHS, "Depreciation starts when it is placed in service, not when the first tenant moves in", "1") +
            C.numf("d-year", "Year it was placed in service", "", "2026", "2026") + "</div>")
    kp = (C.kpi("k-y1", "First-year depreciation", "wide gold") + C.kpi("k-full", "Each full year") +
          C.kpi("k-basis", "Depreciable basis") + C.kpi("k-end", "Last year of depreciation"))
    res = C.result_card("Your depreciation", kp, cta_label="Have us set up your depreciation")
    head = '<thead><tr><th>Year</th><th class="num">Depreciation</th></tr></thead>'
    below = C.math_card(sub="Straight line over 27.5 years with the mid-month convention (Publication 527). IRS tables round each year to three decimals, so your return can differ by a few dollars.",
                        head=head, title="Your depreciation schedule")
    info = """<h2>How is rental property depreciation calculated?</h2>
<p><strong>Divide the building's basis by 27.5 to get each full year's depreciation.</strong> Basis is what you paid plus certain closing costs and improvements, minus the value of the land. The first and last years are partial: the mid-month convention treats the property as placed in service in the middle of its first month.</p>
<ul><li><strong>Land is never depreciated.</strong> Split the price between land and building, for example with your property tax assessment.</li>
<li><strong>It starts when the rental is ready and available,</strong> even if the first tenant arrives later.</li>
<li><strong>Improvements are depreciated, repairs are deducted.</strong> A new roof or addition starts its own 27.5-year schedule. Read <a href="/blog/rental-property-repairs-vs-improvements-2026/">repairs vs improvements</a>.</li>
<li><strong>Allowed or allowable.</strong> When you sell, the IRS treats depreciation you could have taken as taken, so claim it every year.</li></ul>
<p>Short-term rental? Check the 14-day rule first with the <a href="/tools/airbnb-host-tax-checker/">Airbnb host tax checker</a>. Full service details: <a href="/rental-property-taxes/">rental property taxes</a>.</p>"""
    lead = lead_box.lead_box("Rental depreciation", "calc-deprec", "Want your rental depreciation set up right?",
                             "We set up depreciation schedules and prepare Schedule E returns for landlords and hosts.",
                             [("tax-return", "Tax return for my rental"), ("catch-up", "Missed depreciation in past years"),
                              ("bookkeeping", "Monthly rental bookkeeping"), ("question", "A quick question first")],
                             ["A fixed quote before any work starts", "Land, improvements and past years checked"], calc=True)
    return C.build_page(slug, "Rental Property Depreciation Calculator (27.5 Years)",
                        "Calculate rental property depreciation over 27.5 years: depreciable basis without the land, the mid-month first year and a year-by-year schedule.",
                        "Rental depreciation", "Rental property depreciation calculator",
                        "Your yearly write-off for a residential rental: 27.5 years, mid-month first year, land taken out.",
                        grid + res, below, info, {"page": "deprec"}, "deprec", f, "Own a rental property?",
                        "We set up depreciation and file Schedule E for landlords. Book a 30-minute consultation.",
                        extra_src=[S_527], extra_checked=[CHECKED], lead=lead)


def build_all():
    return [build_tips(), build_airbnb(), build_deprec()]
