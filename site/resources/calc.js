/* MFA tax calculators (tools/build_calculators.py). Site session owns this file.
 * Every tax figure comes from the page's embedded JSON (#calc-data), which the build reads from
 * data/tax-figures-2026.json and data/tax-calendar-2027.json. No tax numbers are hard-coded here.
 * Vanilla JS, no libraries. Nothing typed on these pages is sent anywhere. */
(function () {
  'use strict';
  var MFA = window.MFA = { pages: {} };
  var D = null;

  /* ---------- small helpers ---------- */
  function $(id) { return document.getElementById(id); }
  function num(id) { var e = $(id); if (!e) return 0; var v = parseFloat(e.value); return isFinite(v) && v > 0 ? v : 0; }
  function blank(id) { var e = $(id); return !e || String(e.value).trim() === ''; }
  function sel(id) { var e = $(id); return e ? e.value : ''; }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function money(n, cents) {
    n = Number(n) || 0;
    var r = cents ? Math.round(Math.abs(n) * 100) / 100 : Math.round(Math.abs(n));
    var s = r.toLocaleString('en-US', { minimumFractionDigits: cents ? 2 : 0, maximumFractionDigits: cents ? 2 : 0 });
    return (n < 0 && r !== 0 ? '-' : '') + '$' + s;
  }
  function pct(x, d) { return (+(x * 100).toFixed(d == null ? 3 : d)) + '%'; }
  function setText(id, t) { var e = $(id); if (e) e.textContent = t; }
  function setMoney(id, n, cents) { var e = $(id); if (!e) return; e.textContent = money(n, cents); e.setAttribute('data-v', String(n)); }
  function dash(ids) { ids.forEach(function (i) { var e = $(i); if (e) { e.textContent = '\u2014'; e.removeAttribute('data-v'); } }); }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function todayISO() { var d = new Date(); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function isoDate(s) { return new Date(s + 'T00:00:00Z'); }
  function fmtDate(s, opt) {
    return isoDate(s).toLocaleDateString('en-US', Object.assign({ timeZone: 'UTC', month: 'long', day: 'numeric', year: 'numeric' }, opt || {}));
  }
  function daysUntil(s) {
    var t = todayISO();
    return Math.round((isoDate(s) - isoDate(t)) / 86400000);
  }
  function wire(run) {
    document.addEventListener('input', run);
    document.addEventListener('change', run);
    run();
  }
  /* breakdown table: rows = [label, amountText, how, cls] */
  function renderRows(id, rows) {
    var tb = $(id); if (!tb) return;
    tb.innerHTML = rows.map(function (r) {
      return '<tr' + (r[3] ? ' class="' + r[3] + '"' : '') + '><td>' + esc(r[0]) + (r[2] ? '<small>' + esc(r[2]) + '</small>' : '') +
        '</td><td class="num">' + esc(r[1]) + '</td></tr>';
    }).join('');
  }
  function showIf(id, on) { var e = $(id); if (e) e.hidden = !on; }

  /* ---------- tax engine ---------- */
  function findBracket(tbl, x) {
    for (var i = 0; i < tbl.length; i++) {
      var b = tbl[i];
      if (x > b.over && (b.not_over === null || x <= b.not_over)) return b;
    }
    return tbl[tbl.length - 1];
  }
  function bracketTax(tbl, x) { if (x <= 0) return 0; var b = findBracket(tbl, x); return b.base_tax + b.rate * (x - b.over); }
  function subtractTax(tbl, x) { if (x <= 0) return 0; var b = findBracket(tbl, x); return Math.max(0, x * b.rate - b.subtract); }
  function njTable(st) { return D.nj.brackets[(st === 'single' || st === 'married_separate') ? 'single_or_married_separate' : 'married_joint_hoh_surviving_spouse']; }
  function nyKey(st) { return st === 'married_joint' ? 'married_joint' : (st === 'head_of_household' ? 'head_of_household' : 'single_or_married_separate'); }
  var STATUS_LABEL = { single: 'Single', married_joint: 'Married filing jointly', married_separate: 'Married filing separately', head_of_household: 'Head of household' };

  /* Self-employment tax. net = profit; w2 = this person's W-2 wages (they use up Social Security wage base). */
  function seTax(net, w2, status) {
    var F = D.fed, ne = net * F.factor;
    var r = { ne: ne, applies: ne >= F.se_min, room: Math.max(0, F.wage_base - w2), ssBase: 0, ss: 0, med: 0, core: 0, addl: 0, total: 0, half: 0, thr: F.addl_thr[status] };
    if (!r.applies) return r;
    r.ssBase = Math.min(ne, r.room);
    r.ss = F.ss_rate * r.ssBase;
    r.med = F.med_rate * ne;
    r.core = r.ss + r.med;
    r.addl = F.addl_rate * Math.max(0, w2 + ne - r.thr);
    r.total = r.core + r.addl;
    r.half = F.half_share * r.core;
    return r;
  }
  function fedIncome(agi, status, extra) {
    var std = D.fed.std[status], ti = Math.max(0, agi - std - (extra || 0));
    return { std: std, ti: ti, tax: bracketTax(D.fed.brackets[status], ti) };
  }
  /* State income tax estimate. p: {state, status, net, w2, other, flat, stEx}; agi = federal AGI. */
  function stateTax(p, agi) {
    var ex = p.stEx || 0, o;
    if (p.state === 'NJ') {
      var inc = Math.max(0, p.net + p.w2 + p.other - ex);
      return { tax: subtractTax(njTable(p.status), inc), city: 0, base: inc, name: 'New Jersey', how: 'NJ rate schedule on ' + money(inc) + ' of income (NJ has no standard deduction and does not allow the self-employment tax deduction)' };
    }
    if (p.state === 'NY' || p.state === 'NYC') {
      var ti = Math.max(0, agi - D.ny.std[p.status] - ex);
      var nys = bracketTax(D.ny.brackets[nyKey(p.status)], ti);
      var nyc = p.state === 'NYC' ? bracketTax(D.nyc.brackets[nyKey(p.status)], ti) : 0;
      return { tax: nys + nyc, state: nys, city: nyc, base: ti, name: p.state === 'NYC' ? 'New York State and City' : 'New York State',
        how: 'NY taxable income ' + money(ti) + ' (federal AGI minus the ' + money(D.ny.std[p.status]) + ' NY standard deduction)' + (p.state === 'NYC' ? '; state ' + money(nys) + ' + city ' + money(nyc) : '') };
    }
    var b = Math.max(0, agi - ex);
    o = b * (p.flat || 0) / 100;
    return { tax: o, city: 0, base: b, name: 'Your state', how: (p.flat || 0) + '% of ' + money(b) + ' (federal AGI less any deductions you entered)' };
  }
  function estimate(p) {
    var s = seTax(p.net, p.w2, p.status);
    var agi = p.net + p.w2 + p.other - s.half;
    var f = fedIncome(agi, p.status);
    var st = stateTax(p, agi);
    return { se: s, agi: agi, fed: f, st: st, fedTotal: s.total + f.tax, total: s.total + f.tax + st.tax };
  }
  function seRows(e, p, cents) {
    var F = D.fed, s = e.se, m = function (n) { return money(n, cents); };
    return [
      ['Net self-employment profit', m(p.net), 'What you expect to earn after business expenses'],
      ['Net earnings subject to SE tax', m(s.ne), pct(F.factor, 2) + ' of profit' + (s.applies ? '' : '. Under ' + money(F.se_min) + ', so no SE tax')],
      ['Social Security (' + pct(F.ss_rate, 1) + ')', m(s.ss), s.applies ? 'On ' + m(s.ssBase) + ' of earnings; the ' + money(F.wage_base) + ' wage base leaves ' + m(s.room) + (p.w2 ? ' after your ' + m(p.w2) + ' of W-2 wages' : '') : ''],
      ['Medicare (' + pct(F.med_rate, 1) + ')', m(s.med), s.applies ? 'On all ' + m(s.ne) + ' of net earnings' : ''],
      ['Additional Medicare (' + pct(F.addl_rate, 1) + ')', m(s.addl), 'On wages plus SE earnings over ' + money(s.thr) + ' for your filing status'],
      ['Self-employment tax', m(s.total), 'Social Security + Medicare + Additional Medicare', 'tot']
    ];
  }

  /* ---------- .ics + download helpers ---------- */
  function icsText(t) { return String(t).replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n'); }
  function icsFold(line) {
    var enc = new TextEncoder(), out = [], cur = '', len = 0;
    for (var ch of line) {
      var n = enc.encode(ch).length;
      if (len + n > 73) { out.push(cur); cur = ''; len = 0; }
      cur += ch; len += n;
    }
    out.push(cur);
    return out.join('\r\n ');
  }
  function addDays(iso, n) { var d = isoDate(iso); d.setUTCDate(d.getUTCDate() + n); return d.getUTCFullYear() + pad(d.getUTCMonth() + 1) + pad(d.getUTCDate()); }
  /* events: [{uid, date:'YYYY-MM-DD', title, note}] -> all-day events with a 7-day reminder */
  MFA.ics = function (events, name) {
    var now = new Date(), stamp = now.getUTCFullYear() + pad(now.getUTCMonth() + 1) + pad(now.getUTCDate()) + 'T' + pad(now.getUTCHours()) + pad(now.getUTCMinutes()) + pad(now.getUTCSeconds()) + 'Z';
    var L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Merchant Financial Advisory//MFA Tax Tools//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
      'X-WR-CALNAME:' + icsText(name || 'MFA tax deadlines'), 'X-WR-TIMEZONE:America/New_York'];
    events.forEach(function (e) {
      L.push('BEGIN:VEVENT', 'UID:' + e.uid, 'DTSTAMP:' + stamp, 'DTSTART;VALUE=DATE:' + e.date.replace(/-/g, ''), 'DTEND;VALUE=DATE:' + addDays(e.date, 1),
        'SUMMARY:' + icsText(e.title),
        'DESCRIPTION:' + icsText((e.note ? e.note + '\n\n' : '') + 'General information, not tax advice. Merchant Financial Advisory, mfa-advisory.com'),
        'URL:' + (e.url || 'https://mfa-advisory.com/resources/'), 'TRANSP:TRANSPARENT',
        'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + icsText(e.title), 'TRIGGER:-P7D', 'END:VALARM', 'END:VEVENT');
    });
    L.push('END:VCALENDAR');
    return L.map(icsFold).join('\r\n') + '\r\n';
  };
  MFA.download = function (filename, text, mime) {
    var blob = new Blob([text], { type: mime || 'text/plain' });
    if (window.navigator && navigator.msSaveBlob) { navigator.msSaveBlob(blob, filename); return; }
    var a = document.createElement('a'), url = URL.createObjectURL(blob);
    a.href = url; a.download = filename; a.style.display = 'none';
    document.body.appendChild(a); a.click();
    setTimeout(function () { document.body.removeChild(a); URL.revokeObjectURL(url); }, 500);
  };
  function gcalLink(e) {
    return 'https://calendar.google.com/calendar/render?action=TEMPLATE&text=' + encodeURIComponent(e.title) +
      '&dates=' + e.date.replace(/-/g, '') + '/' + addDays(e.date, 1) + '&details=' + encodeURIComponent((e.note ? e.note + '\n\n' : '') + 'General information, not tax advice. mfa-advisory.com');
  }

  MFA.init = function (name) {
    var el = $('calc-data');
    D = JSON.parse(el.textContent);
    MFA.pages[name]();
  };

  /* =====================================================================
   * 1. Quarterly estimated tax calculator
   * ===================================================================== */
  MFA.pages.quarterly = function () {
    function run() {
      showIf('q-flat-wrap', sel('q-state') === 'OTHER');
      var p = { net: num('q-net'), w2: num('q-w2'), other: num('q-other'), status: sel('q-status'), state: sel('q-state'), flat: num('q-flat'), stEx: num('q-stex') };
      var fedWh = num('q-fedwh'), stWh = num('q-stwh'), paidF = num('q-paidf'), paidS = num('q-paids');
      var outs = ['k-total', 'k-fedq', 'k-stq', 'k-totq'];
      if (!p.net && !p.w2 && !p.other) {
        dash(outs); setText('rsub', 'Enter your expected 2026 profit to see your payments.');
        renderRows('math', [['Enter your numbers above', '\u2014', 'Each step of the calculation will show here.']]);
        $('dues').innerHTML = ''; $('safe').innerHTML = ''; setText('rnote', ''); setText('left', '');
        return;
      }
      var e = estimate(p), F = D.fed;
      var fedDue = Math.max(0, e.fedTotal - fedWh);
      var stDue = Math.max(0, e.st.tax - stWh);
      var totDue = fedDue + stDue;
      setMoney('k-total', e.total);
      setMoney('k-fedq', fedDue / 4); setMoney('k-stq', stDue / 4); setMoney('k-totq', totDue / 4);
      setText('rsub', 'Based on ' + money(p.net) + ' of expected profit for 2026. ' + (totDue > 0 ? 'Pay ' + money(totDue / 4) + ' each quarter.' : 'You may not owe estimated tax.'));

      /* schedule */
      var today = todayISO(), rows = '', ord = ['1st', '2nd', '3rd', '4th'];
      F.due.forEach(function (d, i) {
        var past = d < today, dd = daysUntil(d);
        rows += '<tr><td>' + esc(fmtDate(d, { month: 'short' })) + '<small>' + ord[i] + ' payment \u00b7 ' + (past ? 'date has passed' : (dd === 0 ? 'due today' : 'in ' + dd + ' days')) + '</small></td>' +
          '<td class="num">' + money(fedDue / 4) + '</td><td class="num">' + money(stDue / 4) + '</td><td class="num">' + money(totDue / 4) + '</td></tr>';
      });
      rows += '<tr class="tot"><td>Total</td><td class="num">' + money(fedDue) + '</td><td class="num">' + money(stDue) + '</td><td class="num">' + money(totDue) + '</td></tr>';
      $('dues').innerHTML = rows;

      /* where you stand */
      var leftF = Math.max(0, fedDue - paidF), leftS = Math.max(0, stDue - paidS), nextD = null;
      for (var i = 0; i < F.due.length; i++) { if (F.due[i] >= today) { nextD = F.due[i]; break; } }
      if (paidF || paidS) {
        setText('left', 'After the payments you entered, about ' + money(leftF) + ' federal and ' + money(leftS) + ' state remain' +
          (nextD ? '. Next due date: ' + fmtDate(nextD) + '.' : '. All four 2026 dates have passed, so pay the rest as soon as you can; a late-payment penalty may apply.'));
      } else {
        setText('left', nextD ? 'Next due date: ' + fmtDate(nextD) + '. If you have already made 2026 payments, enter them above to see what is left.' : 'All four 2026 due dates have passed. Pay what you owe as soon as you can; a late-payment penalty may apply.');
      }

      /* notes: thresholds */
      var notes = [];
      if (e.fedTotal - fedWh < F.est_threshold) notes.push('Your federal balance after withholding is under ' + money(F.est_threshold) + ', so federal estimated payments are generally not required.');
      var stThr = p.state === 'NJ' ? D.nj.threshold : (p.state === 'NY' || p.state === 'NYC' ? D.ny.threshold : 0);
      if (stThr && stDue > 0 && stDue < stThr) notes.push('Your state balance is under ' + money(stThr) + ', the level where ' + (p.state === 'NJ' ? 'New Jersey' : 'New York') + ' estimates may be needed.');
      if (p.state === 'NY' || p.state === 'NYC') notes.push(D.ny.note);
      if (p.state === 'NJ') notes.push(D.nj.due_note);
      setText('rnote', '');
      $('qnotes').innerHTML = notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('');

      /* safe harbor */
      var S = F.safe, priorTax = num('q-prior'), hasPrior = !blank('q-prior') && priorTax > 0, priorAgi = num('q-prioragi');
      var hiThr = p.status === 'married_separate' ? S.high_income_agi_over_mfs : S.high_income_agi_over;
      var priorPct = priorAgi > hiThr ? S.prior_year_pct_high_income : S.prior_year_pct;
      var optA = Math.max(0, S.current_year_pct * e.fedTotal - fedWh);
      var sh = '<h3>Federal safe harbor</h3><p>You avoid the underpayment penalty if your withholding and estimated payments add up to the <b>smaller</b> of ' + pct(S.current_year_pct, 0) + ' of this year\u2019s tax or ' +
        pct(S.prior_year_pct, 0) + ' of last year\u2019s tax (' + pct(S.prior_year_pct_high_income, 0) + ' if last year\u2019s AGI was over ' + money(hiThr) + ').</p>' +
        '<table class="tbl ctbl"><thead><tr><th>Option</th><th class="num">Per quarter</th></tr></thead><tbody>' +
        '<tr><td>' + pct(S.current_year_pct, 0) + ' of this year\u2019s estimated tax<small>' + money(S.current_year_pct * e.fedTotal) + ' minus ' + money(fedWh) + ' withheld = ' + money(optA) + ' for the year</small></td><td class="num">' + money(optA / 4) + '</td></tr>';
      var best = optA;
      if (hasPrior) {
        var optB = Math.max(0, priorPct * priorTax - fedWh);
        best = Math.min(optA, optB);
        sh += '<tr><td>' + pct(priorPct, 0) + ' of last year\u2019s tax<small>' + money(priorTax) + ' \u00d7 ' + pct(priorPct, 0) + ' = ' + money(priorPct * priorTax) + ', minus ' + money(fedWh) + ' withheld = ' + money(optB) + ' for the year' +
          (blank('q-prioragi') ? '. Last year\u2019s AGI not entered, so ' + pct(S.prior_year_pct, 0) + ' is assumed' : '') + '</small></td><td class="num">' + money(optB / 4) + '</td></tr>';
      }
      sh += '<tr class="tot"><td>Smallest safe-harbor payment' + (hasPrior ? '' : '<small>Enter last year\u2019s total tax to compare the second option</small>') + '</td><td class="num">' + money(best / 4) + '</td></tr></tbody></table>' +
        '<p class="hintp">Safe harbor protects you from the penalty, but you still owe the full tax when you file. Paying the lower amount just moves the balance to April.</p>';
      $('safe').innerHTML = sh;
      setMoney('k-safeq', best / 4);

      /* math */
      var rowsM = seRows(e, p);
      rowsM.push(
        ['Half of SE tax (deduction)', money(-e.se.half), pct(D.fed.half_share, 0) + ' of Social Security + Medicare. It lowers income, not SE tax'],
        ['Adjusted gross income (AGI)', money(e.agi), 'Profit + W-2 wages + other income \u2212 half of SE tax'],
        ['Standard deduction', money(-e.fed.std), STATUS_LABEL[p.status] + '. Itemizing could be higher'],
        ['Federal taxable income', money(e.fed.ti), 'Qualified business income (QBI) deduction not included'],
        ['Federal income tax', money(e.fed.tax), '2026 brackets for your filing status', 'tot'],
        ['State income tax (' + e.st.name + ')', money(e.st.tax), e.st.how],
        ['Total estimated 2026 tax', money(e.total), 'SE tax + federal income tax + state income tax', 'tot'],
        ['Less: tax already withheld', money(-(fedWh + stWh)), 'Federal ' + money(fedWh) + ' + state ' + money(stWh)],
        ['Left to pay through estimates', money(totDue), 'Divided by 4 = ' + money(totDue / 4) + ' per payment', 'tot']
      );
      renderRows('math', rowsM);
    }
    wire(run);
  };

  /* =====================================================================
   * 2. 1099 tax calculator
   * ===================================================================== */
  MFA.pages.t1099 = function () {
    function run() {
      showIf('t-flat-wrap', sel('t-state') === 'OTHER');
      var inc = num('t-inc'), exp = num('t-exp');
      var p = { net: Math.max(0, inc - exp), w2: 0, other: 0, status: sel('t-status'), state: sel('t-state'), flat: num('t-flat'), stEx: 0 };
      var outs = ['k-net', 'k-total', 'k-set', 'k-eff', 'k-se', 'k-inc'];
      if (!inc) {
        dash(outs); setText('rsub', 'Enter your 1099 income to see what to set aside.');
        renderRows('math', [['Enter your numbers above', '\u2014', 'Each step of the calculation will show here.']]);
        return;
      }
      var e = estimate(p);
      setMoney('k-net', p.net); setMoney('k-total', e.total); setMoney('k-se', e.se.total); setMoney('k-inc', e.fed.tax + e.st.tax);
      var setAside = e.total / inc, eff = p.net > 0 ? e.total / p.net : 0;
      setText('k-set', pct(setAside, 1)); $('k-set').setAttribute('data-v', String(setAside));
      setText('k-eff', pct(eff, 1)); $('k-eff').setAttribute('data-v', String(eff));
      setText('rsub', 'Set aside about ' + pct(setAside, 0) + ' of every payment you receive.');
      var rows = seRows(e, p);
      rows.unshift(['1099 income', money(inc), 'Total received from clients for the year'], ['Less: business expenses', money(-Math.min(exp, inc)), 'Costs of doing the work']);
      rows.push(
        ['Half of SE tax (deduction)', money(-e.se.half), 'Lowers income, not SE tax'],
        ['Adjusted gross income (AGI)', money(e.agi), 'Profit \u2212 half of SE tax'],
        ['Standard deduction', money(-e.fed.std), STATUS_LABEL[p.status]],
        ['Federal taxable income', money(e.fed.ti), 'Qualified business income (QBI) deduction not included'],
        ['Federal income tax', money(e.fed.tax), '2026 brackets for your filing status', 'tot'],
        ['State income tax (' + e.st.name + ')', money(e.st.tax), e.st.how],
        ['Total estimated tax', money(e.total), 'SE tax + federal + state', 'tot'],
        ['Share of every payment to set aside', pct(setAside, 1), 'Total tax \u00f7 ' + money(inc) + ' of 1099 income'],
        ['Effective rate on profit', pct(eff, 1), 'Total tax \u00f7 ' + money(p.net) + ' of profit']
      );
      renderRows('math', rows);
    }
    wire(run);
  };

  /* =====================================================================
   * 3. S corp savings calculator
   * ===================================================================== */
  MFA.pages.scorp = function () {
    var F, ficaSS, ficaMed;
    function llcTax(profit) { return seTax(profit, 0, 'single'); }
    function payroll(sal) {
      var thr = F.addl_thr.single;
      var ss = ficaSS * Math.min(sal, F.wage_base), med = ficaMed * sal;
      var addl = F.addl_rate * Math.max(0, sal - thr);
      return { ssEe: ss, ssEr: ss, medEe: med, medEr: med, addl: addl, ee: ss + med + addl, er: ss + med, total: 2 * (ss + med) + addl };
    }
    function breakEven(sal, costs) {
      var f = function (P) { return llcTax(P).total - payroll(sal).total - costs; };
      var lo = sal, hi = Math.max(sal, 1000) * 2;
      if (f(lo) >= 0) return lo;
      var n = 0;
      while (f(hi) < 0 && n < 60) { hi *= 2; n++; }
      if (f(hi) < 0) return null;
      for (var i = 0; i < 80; i++) { var mid = (lo + hi) / 2; if (f(mid) < 0) lo = mid; else hi = mid; }
      return hi;
    }
    function run() {
      F = D.fed; ficaSS = F.ss_rate / 2; ficaMed = F.med_rate / 2;
      var P = num('s-profit'), S = num('s-salary'), c1 = num('s-cost1'), c2 = num('s-cost2'), costs = c1 + c2, state = sel('s-state');
      var notes = { NJ: D.notes.NJ, NY: D.notes.NY, OTHER: D.notes.OTHER };
      setText('s-statenote', notes[state] || '');
      var outs = ['k-llc', 'k-scorp', 'k-save', 'k-be'];
      if (!P) {
        dash(outs); setText('rsub', 'Enter your net profit to compare.');
        $('verdict').className = 'verdict'; $('verdict').innerHTML = '<span class="vk">Start here</span><h3>Enter your profit and salary.</h3><p>We compare self-employment tax as an LLC with payroll taxes as an S corporation, after the extra costs of running one.</p>';
        renderRows('math', [['Enter your numbers above', '\u2014', 'Each step of the comparison will show here.']]);
        return;
      }
      var L = llcTax(P), R = payroll(S), save = L.total - R.total - costs, be = breakEven(S, costs);
      setMoney('k-llc', L.total); setMoney('k-scorp', R.total); setMoney('k-save', save);
      if (be === null) setText('k-be', 'Not reached'); else setMoney('k-be', be);
      var v = $('verdict'), msg;
      if (S > P) {
        v.className = 'verdict'; msg = ['Check your salary', 'Salary can\u2019t be more than the business earns', 'Your salary is higher than your profit. Lower the salary or raise the profit to compare.'];
      } else if (save > 0) {
        v.className = 'verdict yes'; msg = ['Estimated savings', 'An S corp could save about ' + money(save) + ' a year', 'Payroll taxes on a ' + money(S) + ' salary come to ' + money(R.total) + ', versus ' + money(L.total) + ' of self-employment tax, and that is after ' + money(costs) + ' of extra costs.'];
      } else {
        v.className = 'verdict'; msg = ['Estimated result', 'An S corp probably wouldn\u2019t save tax at this profit', 'After ' + money(costs) + ' of extra costs, the S corp comes out ' + money(-save) + ' worse on these taxes' + (be ? '. The break-even profit for this salary is about ' + money(be) + '.' : '.')];
      }
      v.innerHTML = '<span class="vk">' + esc(msg[0]) + '</span><h3>' + esc(msg[1]) + '</h3><p>' + esc(msg[2]) + '</p>';
      setText('rsub', S > P ? 'Salary is higher than profit.' : 'Salary is ' + pct(P > 0 ? S / P : 0, 0) + ' of your profit.');
      var rows = [
        ['As an LLC (sole proprietor or single-member)', '', '', 'sec'],
        ['Net profit', money(P), 'All of it is subject to self-employment tax'],
        ['Net earnings subject to SE tax', money(L.ne), pct(F.factor, 2) + ' of profit'],
        ['Social Security (' + pct(F.ss_rate, 1) + ')', money(L.ss), 'On the first ' + money(L.ssBase) + ' (wage base ' + money(F.wage_base) + ')'],
        ['Medicare (' + pct(F.med_rate, 1) + ')', money(L.med), 'On all net earnings'],
        ['Additional Medicare (' + pct(F.addl_rate, 1) + ')', money(L.addl), 'Over ' + money(F.addl_thr.single) + ' (single filer, no other wages assumed)'],
        ['SE tax as an LLC', money(L.total), '', 'tot'],
        ['As an S corporation', '', '', 'sec'],
        ['Salary you pay yourself', money(S), 'Subject to payroll taxes'],
        ['Employee share: Social Security + Medicare', money(R.ee - R.addl), pct(ficaSS, 1) + ' + ' + pct(ficaMed, 1) + ' withheld from your pay'],
        ['Employer share: Social Security + Medicare', money(R.er), 'The S corp pays the same amount on top of your salary'],
        ['Additional Medicare (' + pct(F.addl_rate, 1) + ')', money(R.addl), 'On salary over ' + money(F.addl_thr.single)],
        ['Payroll taxes as an S corp', money(R.total), '', 'tot'],
        ['Extra annual S corp costs', money(costs), 'Payroll service ' + money(c1) + ' + return prep and bookkeeping ' + money(c2) + ' (your assumptions)'],
        ['Profit paid out as distributions', money(Math.max(0, P - S - R.er)), 'Profit minus salary minus the employer payroll tax. Not subject to SE or payroll tax'],
        ['Annual savings after costs', money(save), 'SE tax as LLC \u2212 payroll taxes as S corp \u2212 extra costs', 'tot'],
        ['Break-even profit', be === null ? 'Not reached' : money(be), 'Profit at which the savings equal the extra costs, for this salary and these costs']
      ];
      renderRows('math', rows);
    }
    wire(run);
  };

  /* =====================================================================
   * 5. Paycheck tax calculator
   * ===================================================================== */
  MFA.pages.paycheck = function () {
    function run() {
      var F = D.fed, ssRate = F.ss_rate / 2, medRate = F.med_rate / 2;
      var n = parseFloat(sel('p-freq')) || 26, gross = num('p-gross'), status = sel('p-status'), state = sel('p-state');
      var k401 = num('p-k401') * n, s125 = num('p-s125') * n;
      var outs = ['k-net', 'k-gross', 'k-tax', 'k-rate'];
      if (!gross) {
        dash(outs); setText('rsub', 'Enter your annual salary to see take-home pay.');
        $('pmath').innerHTML = '<tr><td colspan="3">Enter your numbers above to see each step.</td></tr>';
        return;
      }
      var ficaW = Math.max(0, gross - s125);
      var ss = ssRate * Math.min(ficaW, F.wage_base), med = medRate * ficaW, addl = F.addl_rate * Math.max(0, ficaW - F.addl_thr.single);
      var fedTI = Math.max(0, gross - k401 - s125 - F.std[status]);
      var fedTax = bracketTax(F.brackets[status], fedTI);
      var stTax = 0, stNote = 'No state income tax included';
      if (state === 'NJ') {
        var njInc = Math.max(0, gross - k401 - s125);
        stTax = subtractTax(njTable(status), njInc);
        stNote = 'NJ rate schedule on ' + money(njInc) + ' (401(k) deferrals excluded; NJ has no standard deduction; 403(b)/457 deferrals are taxable in NJ)';
      } else if (state === 'NY' || state === 'NYC') {
        var nyTI = Math.max(0, gross - k401 - s125 - D.ny.std[status]);
        var nys = bracketTax(D.ny.brackets[nyKey(status)], nyTI), nyc = state === 'NYC' ? bracketTax(D.nyc.brackets[nyKey(status)], nyTI) : 0;
        stTax = nys + nyc;
        stNote = 'NY taxable income ' + money(nyTI) + (state === 'NYC' ? '; state ' + money(nys) + ' + city ' + money(nyc) : '') + '. Estimate: ' + D.ny.note;
      }
      var taxes = fedTax + ss + med + addl + stTax, net = gross - k401 - s125 - taxes;
      var c = function (x) { return money(x / n, true); }, a = function (x) { return money(x, false); };
      setMoney('k-net', net / n, true); setMoney('k-gross', gross / n, true); setMoney('k-tax', taxes / n, true);
      setText('k-rate', pct(taxes / gross, 1)); $('k-rate').setAttribute('data-v', String(taxes / gross));
      setText('rsub', 'Estimated take-home of ' + money(net / n, true) + ' per paycheck (' + n + ' paychecks a year).');
      var rows = [
        ['Gross pay', c(gross), a(gross), 'Annual salary \u00f7 ' + n + ' paychecks', ''],
        ['Pre-tax retirement (401(k))', c(-k401), a(-k401), 'Lowers federal, NJ and NY income tax, not Social Security or Medicare', ''],
        ['Pre-tax health (Section 125)', c(-s125), a(-s125), 'Lowers income tax and payroll taxes', ''],
        ['Federal income tax', c(-fedTax), a(-fedTax), 'On ' + money(fedTI) + ' of taxable income after the ' + money(F.std[status]) + ' standard deduction', ''],
        ['Social Security (' + pct(ssRate, 1) + ')', c(-ss), a(-ss), 'On wages up to the ' + money(F.wage_base) + ' wage base', ''],
        ['Medicare (' + pct(medRate, 2) + ')', c(-med), a(-med), 'On all wages', ''],
        ['Additional Medicare (' + pct(F.addl_rate, 1) + ')', c(-addl), a(-addl), 'On wages over ' + money(F.addl_thr.single) + ' (what employers withhold)', ''],
        [state === 'NJ' ? 'New Jersey income tax' : (state === 'NYC' ? 'New York State and City income tax' : (state === 'NY' ? 'New York State income tax' : 'State income tax')), c(-stTax), a(-stTax), stNote, ''],
        ['Take-home pay', c(net), a(net), 'Gross pay minus deductions and taxes', 'tot']
      ];
      $('pmath').innerHTML = rows.map(function (r) {
        return '<tr' + (r[4] ? ' class="' + r[4] + '"' : '') + '><td>' + esc(r[0]) + '<small>' + esc(r[3]) + '</small></td><td class="num">' + esc(r[1]) + '</td><td class="num">' + esc(r[2]) + '</td></tr>';
      }).join('');
    }
    wire(run);
  };

  /* =====================================================================
   * 6. Home office deduction calculator
   * ===================================================================== */
  MFA.pages.homeoffice = function () {
    var H = null;
    function run() {
      H = D.home;
      var home = num('h-home'), office = num('h-office');
      var fields = ['h-rent', 'h-mint', 'h-tax', 'h-ins', 'h-util', 'h-rep', 'h-dep', 'h-other'];
      var indirect = 0; fields.forEach(function (f) { indirect += num(f); });
      var direct = num('h-direct'), limitSet = !blank('h-limit'), limit = num('h-limit');
      var outs = ['k-simple', 'k-regular', 'k-best', 'k-pct'];
      if (!office) {
        dash(outs); setText('rsub', 'Enter your office size to compare the two methods.');
        renderRows('math', [['Enter your numbers above', '\u2014', 'Each step of the calculation will show here.']]);
        $('verdict').className = 'verdict'; $('verdict').innerHTML = '<span class="vk">Start here</span><h3>Enter your square footage.</h3><p>We compare the simplified method with the regular method side by side.</p>';
        return;
      }
      var simpSq = Math.min(office, H.max_sqft), simple = simpSq * H.rate;
      var share = home > 0 ? Math.min(1, office / home) : 0;
      var regular = indirect * share + direct;
      var simpleL = limitSet ? Math.min(simple, limit) : simple, regularL = limitSet ? Math.min(regular, limit) : regular;
      setMoney('k-simple', simpleL); setMoney('k-regular', regularL);
      setText('k-pct', home > 0 ? pct(share, 1) : '\u2014');
      var better = regularL > simpleL ? 'regular' : 'simple';
      var diff = Math.abs(regularL - simpleL);
      setText('k-best', regularL === simpleL ? 'Same' : (better === 'regular' ? 'Regular' : 'Simplified'));
      var v = $('verdict');
      if (home <= 0) {
        v.className = 'verdict'; v.innerHTML = '<span class="vk">Almost there</span><h3>Add your home\u2019s total square feet.</h3><p>The regular method needs it to work out your business-use percentage. The simplified method is shown now.</p>';
      } else if (regularL === simpleL) {
        v.className = 'verdict'; v.innerHTML = '<span class="vk">Result</span><h3>Both methods give ' + esc(money(simpleL)) + '</h3><p>The simplified method is much less paperwork.</p>';
      } else {
        v.className = 'verdict yes';
        v.innerHTML = '<span class="vk">Result</span><h3>' + (better === 'regular' ? 'The regular method is higher by ' : 'The simplified method is higher by ') + esc(money(diff)) + '</h3><p>' +
          (better === 'regular' ? 'You would deduct ' + esc(money(regularL)) + ' instead of ' + esc(money(simpleL)) + ', but you need to track and keep records of your actual home expenses.' : 'You would deduct ' + esc(money(simpleL)) + ' with far less record keeping than the regular method\u2019s ' + esc(money(regularL)) + '.') + '</p>';
      }
      setText('rsub', 'Office is ' + (home > 0 ? pct(share, 1) + ' of your home.' : 'size entered.'));
      var rows = [
        ['Simplified method', '', '', 'sec'],
        ['Square feet counted', simpSq + ' sq ft', 'Your office, up to ' + H.max_sqft + ' sq ft'],
        ['Rate per square foot', money(H.rate), 'IRS simplified rate'],
        ['Simplified deduction', money(simple), simpSq + ' \u00d7 ' + money(H.rate) + (office > H.max_sqft ? '. Capped at ' + money(H.max_deduction) : ''), 'tot'],
        ['Regular method', '', '', 'sec'],
        ['Business-use percentage', home > 0 ? pct(share, 2) : '\u2014', office + ' sq ft \u00f7 ' + (home || '?') + ' sq ft'],
        ['Shared home expenses', money(indirect), 'Rent, mortgage interest, property tax, insurance, utilities, repairs, depreciation and other'],
        ['Business share of those', money(indirect * share), money(indirect) + ' \u00d7 ' + (home > 0 ? pct(share, 2) : '\u2014')],
        ['Direct office expenses', money(direct), 'Costs only for the office, deducted in full'],
        ['Regular deduction', money(regular), '', 'tot']
      ];
      if (limitSet) rows.push(['Income limit', money(limit), 'The deduction can\u2019t exceed ' + money(limit) + '. ' + D.home.limit_note], ['Deduction after the income limit', 'Simplified ' + money(simpleL) + ' \u00b7 Regular ' + money(regularL), '', 'tot']);
      renderRows('math', rows);
    }
    wire(run);
  };

  /* =====================================================================
   * 7. Mileage deduction calculator
   * ===================================================================== */
  MFA.pages.mileage = function () {
    function run() {
      var M = D.mileage, m1 = num('m-h1'), m2 = num('m-h2'), park = num('m-park');
      var d1 = m1 * M.r1, d2 = m2 * M.r2, tot = d1 + d2 + park;
      if (!m1 && !m2 && !park) {
        dash(['k-total', 'k-miles', 'k-h1', 'k-h2']); setText('rsub', 'Enter your business miles to see the deduction.');
        renderRows('math', [['Enter your miles above', '\u2014', 'Each step of the calculation will show here.']]); return;
      }
      setMoney('k-total', tot, true); setMoney('k-h1', d1, true); setMoney('k-h2', d2, true);
      setText('k-miles', (m1 + m2).toLocaleString('en-US')); $('k-miles').setAttribute('data-v', String(m1 + m2));
      setText('rsub', (m1 + m2).toLocaleString('en-US') + ' business miles' + (park ? ' plus ' + money(park, true) + ' of parking and tolls' : '') + '.');
      renderRows('math', [
        ['Jan. 1 \u2013 June 30', money(d1, true), m1.toLocaleString('en-US') + ' miles \u00d7 ' + +(M.r1 * 100).toFixed(3) + ' cents'],
        ['July 1 \u2013 Dec. 31', money(d2, true), m2.toLocaleString('en-US') + ' miles \u00d7 ' + +(M.r2 * 100).toFixed(3) + ' cents'],
        ['Parking and tolls', money(park, true), 'Deductible in addition to the standard mileage rate'],
        ['Total mileage deduction', money(tot, true), 'Reported on Schedule C if you are self-employed', 'tot']
      ]);
    }
    wire(run);
  };

  /* =====================================================================
   * 4. 1099 contractor tracker
   * ===================================================================== */
  MFA.pages.tracker = function () {
    var KEY = 'mfa-1099-tracker-v1', YEAR = String(D.year), TH = D.threshold;
    var S = { vendors: [], payments: [] }, persisted = true, editing = null;
    var ents = {}, meths = {};
    D.entities.forEach(function (e) { ents[e.id] = e; });
    D.methods.forEach(function (m) { meths[m.id] = m; });

    function load() {
      try { var t = window.localStorage.getItem(KEY); if (t) { var o = JSON.parse(t); if (o && Array.isArray(o.vendors) && Array.isArray(o.payments)) S = o; } }
      catch (e) { persisted = false; }
    }
    function save() {
      try { window.localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { persisted = false; }
      storageNote();
    }
    function storageNote() {
      var n = $('st-note'); if (!n) return;
      n.hidden = persisted;
      if (!persisted) n.textContent = 'Your browser is blocking local storage, so this list will be lost when you close the page. Use Export CSV to keep a copy.';
    }
    function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
    function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
    function vendorById(id) { for (var i = 0; i < S.vendors.length; i++) if (S.vendors[i].id === id) return S.vendors[i]; return null; }
    function totals(v) {
      var rep = 0, exc = 0;   /* cents, so 1,999.99 + 0.01 is exactly 2,000.00 */
      S.payments.forEach(function (p) {
        if (p.vendor !== v.id || String(p.date).slice(0, 4) !== YEAR) return;
        if (meths[p.method] && meths[p.method].reportable) rep += Math.round(p.amount * 100); else exc += Math.round(p.amount * 100);
      });
      return { rep: rep / 100, exc: exc / 100 };
    }
    function flag(v, t) {
      var e = ents[v.entity] || ents.indiv;
      if (e.foreign) return { k: 'none', txt: 'Usually no 1099 (foreign payee, Form W-8)' };
      if (e.exempt) return { k: 'none', txt: 'No 1099 (tax-exempt or government)' };
      if (e.corp && !v.lm) return { k: 'none', txt: 'No 1099 (corporation)' };
      if (t.rep >= TH) return { k: 'need', txt: '1099-NEC needed' };
      var left = Math.round((TH - t.rep) * 100) / 100;
      return { k: 'under', txt: 'Under ' + money(TH) + ': ' + money(left, left % 1 !== 0) + ' to go' };
    }
    function msg(id, text, bad) { var m = $(id); if (!m) return; m.textContent = text; m.className = 'tmsg' + (bad ? ' bad' : ''); }

    function render() {
      /* vendor select */
      var ps = $('p-vendor'), cur = ps.value;
      ps.innerHTML = '';
      var o0 = el('option', '', S.vendors.length ? 'Choose a vendor' : 'Add a vendor first'); o0.value = ''; ps.appendChild(o0);
      S.vendors.slice().sort(function (a, b) { return a.name.localeCompare(b.name); }).forEach(function (v) { var o = el('option', '', v.name); o.value = v.id; ps.appendChild(o); });
      ps.value = cur && vendorById(cur) ? cur : '';

      var vl = $('vlist'); vl.innerHTML = '';
      var needed = 0, missing = 0, repAll = 0;
      var sorted = S.vendors.slice().sort(function (a, b) { return a.name.localeCompare(b.name); });
      if (!sorted.length) vl.appendChild(el('p', 'empty', 'No vendors yet. Add the people and businesses you pay.'));
      sorted.forEach(function (v) {
        var t = totals(v), f = flag(v, t), e = ents[v.entity] || ents.indiv;
        if (f.k === 'need') needed++;
        var hasW9 = v.tin === 'Y';
        var paid = t.rep + t.exc > 0;
        if (!hasW9 && (f.k === 'need' || f.k === 'under') && paid) missing++;
        if (f.k !== 'none') repAll += t.rep;
        var row = el('div', 'vrow ' + f.k);
        var top = el('div', 'vtop'); top.appendChild(el('b', '', v.name)); top.appendChild(el('span', 'fchip ' + f.k, f.txt)); row.appendChild(top);
        row.appendChild(el('div', 'vmeta', e.label + (v.lm ? ' \u00b7 attorney' : '') + ' \u00b7 ' + (hasW9 ? 'Taxpayer ID on file' + (v.w9 ? ' (W-9 dated ' + fmtDate(v.w9, { month: 'short' }) + ')' : '') : 'Taxpayer ID not on file')));
        var nums = el('div', 'vnums');
        var a = el('span', '', f.k === 'none' ? 'Paid by check, ACH or similar (no 1099): ' : 'Counts toward 1099: '); a.appendChild(el('b', '', money(t.rep, true))); nums.appendChild(a);
        var b = el('span', '', 'Card or processor (1099-K): '); b.appendChild(el('b', '', money(t.exc, true))); nums.appendChild(b);
        row.appendChild(nums);
        if (!hasW9 && f.k !== 'none' && paid) row.appendChild(el('div', 'vwarn', 'No taxpayer ID on file. Request a W-9 before you pay again; without one you may have to withhold tax from payments.'));
        var act = el('div', 'vact');
        var be = el('button', 'mini', 'Edit'); be.type = 'button'; be.setAttribute('data-act', 'edit'); be.setAttribute('data-id', v.id); act.appendChild(be);
        var bd = el('button', 'mini', 'Delete'); bd.type = 'button'; bd.setAttribute('data-act', 'delvendor'); bd.setAttribute('data-id', v.id); act.appendChild(bd);
        row.appendChild(act);
        vl.appendChild(row);
      });
      var pl = $('plist'); pl.innerHTML = '';
      var pays = S.payments.slice().sort(function (a, b) { return a.date < b.date ? 1 : (a.date > b.date ? -1 : 0); });
      if (!pays.length) pl.appendChild(el('p', 'empty', 'No payments logged yet.'));
      pays.forEach(function (p) {
        var v = vendorById(p.vendor), m = meths[p.method] || { label: p.method, reportable: true };
        var r = el('div', 'prow');
        r.appendChild(el('span', 'pd', fmtDate(p.date, { month: 'short' })));
        r.appendChild(el('span', 'pv', v ? v.name : '(deleted vendor)'));
        r.appendChild(el('b', 'pa', money(p.amount, true)));
        r.appendChild(el('span', 'pm' + (m.reportable ? '' : ' ex'), m.label + (m.reportable ? '' : ' \u00b7 not counted')));
        var x = el('button', 'mini', 'Remove'); x.type = 'button'; x.setAttribute('data-act', 'delpay'); x.setAttribute('data-id', p.id); r.appendChild(x);
        pl.appendChild(r);
      });
      setText('s-vendors', String(S.vendors.length)); setText('s-needed', String(needed)); setText('s-missing', String(missing));
      setText('s-total', money(repAll, true));
      $('s-needed').setAttribute('data-v', String(needed));
      $('s-total').setAttribute('data-v', String(repAll));
      var dd = daysUntil(D.deadline.date);
      setText('s-deadline', fmtDate(D.deadline.date, { weekday: 'long' }) + (dd >= 0 ? ' (' + dd + ' days away)' : ' (date has passed)'));
    }

    /* ----- vendor form ----- */
    function clearVendorForm() {
      $('v-name').value = ''; $('v-tin').value = 'N'; $('v-w9').value = ''; $('v-entity').value = 'indiv'; $('v-lm').checked = false;
      editing = null; $('v-add').textContent = 'Add vendor'; $('v-cancel').hidden = true;
    }
    function addVendor() {
      var name = $('v-name').value.trim().slice(0, 80);
      if (!name) { msg('v-msg', 'Enter the vendor\u2019s name.', true); return; }
      var rec = { id: editing || uid(), name: name, tin: $('v-tin').value, w9: $('v-w9').value, entity: $('v-entity').value, lm: $('v-lm').checked };
      if (editing) { var o = vendorById(editing); Object.keys(rec).forEach(function (k) { o[k] = rec[k]; }); msg('v-msg', 'Saved changes to ' + name + '.'); }
      else {
        var dup = S.vendors.some(function (v) { return v.name.toLowerCase() === name.toLowerCase(); });
        if (dup) { msg('v-msg', 'A vendor with that name already exists.', true); return; }
        S.vendors.push(rec); msg('v-msg', 'Added ' + name + '.');
      }
      clearVendorForm(); save(); render();
    }
    function addPayment() {
      var vid = $('p-vendor').value, date = $('p-date').value, amt = parseFloat($('p-amount').value), method = $('p-method').value;
      if (!vid) { msg('p-msg', 'Choose a vendor.', true); return; }
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) { msg('p-msg', 'Enter the payment date.', true); return; }
      if (!isFinite(amt) || amt <= 0) { msg('p-msg', 'Enter an amount greater than zero.', true); return; }
      S.payments.push({ id: uid(), vendor: vid, date: date, amount: Math.round(amt * 100) / 100, method: method });
      $('p-amount').value = '';
      msg('p-msg', 'Logged ' + money(amt, true) + ' for ' + vendorById(vid).name + '.');
      save(); render();
    }

    /* ----- CSV ----- */
    function csvCell(s) {
      s = String(s == null ? '' : s);
      if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
      return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }
    var HEAD = ['vendor', 'taxpayer_id_on_file', 'w9_date', 'entity_type', 'attorney', 'payment_date', 'amount', 'payment_method'];
    function exportCSV() {
      var lines = [HEAD.join(',')];
      S.vendors.forEach(function (v) {
        var pays = S.payments.filter(function (p) { return p.vendor === v.id; }).sort(function (a, b) { return a.date < b.date ? -1 : 1; });
        var base = [v.name, v.tin, v.w9, v.entity, v.lm ? 'Y' : 'N'];
        if (!pays.length) lines.push(base.concat(['', '', '']).map(csvCell).join(','));
        pays.forEach(function (p) { lines.push(base.concat([p.date, p.amount.toFixed(2), p.method]).map(csvCell).join(',')); });
      });
      MFA.download('mfa-1099-contractor-tracker-' + YEAR + '.csv', lines.join('\r\n') + '\r\n', 'text/csv');
    }
    function parseCSV(t) {
      var rows = [], row = [], cur = '', q = false, i = 0;
      t = t.replace(/^\uFEFF/, '');
      for (; i < t.length; i++) {
        var c = t[i];
        if (q) { if (c === '"') { if (t[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
        else if (c === '"') q = true;
        else if (c === ',') { row.push(cur); cur = ''; }
        else if (c === '\n' || c === '\r') { if (c === '\r' && t[i + 1] === '\n') i++; row.push(cur); rows.push(row); row = []; cur = ''; }
        else cur += c;
      }
      if (cur !== '' || row.length) { row.push(cur); rows.push(row); }
      return rows.filter(function (r) { return r.some(function (x) { return String(x).trim() !== ''; }); });
    }
    function unq(s) { s = String(s).trim(); return /^'[=+\-@\t\r]/.test(s) ? s.slice(1) : s; }
    function importCSV(text) {
      var rows = parseCSV(text);
      if (!rows.length) { msg('io-msg', 'That file is empty.', true); return; }
      var head = rows[0].map(function (h) { return String(h).trim().toLowerCase(); }), ix = {};
      HEAD.forEach(function (h) { ix[h] = head.indexOf(h); });
      if (ix.vendor < 0) { msg('io-msg', 'This doesn\u2019t look like an export from this tool (no \u201cvendor\u201d column).', true); return; }
      var addedV = 0, addedP = 0, skipped = 0;
      var get = function (r, k) { return ix[k] >= 0 && r[ix[k]] != null ? unq(r[ix[k]]) : ''; };
      var entByLabel = {}; D.entities.forEach(function (e) { entByLabel[e.label.toLowerCase()] = e.id; });
      rows.slice(1).forEach(function (r) {
        var name = get(r, 'vendor').slice(0, 80); if (!name) { skipped++; return; }
        var v = S.vendors.filter(function (x) { return x.name.toLowerCase() === name.toLowerCase(); })[0];
        if (!v) {
          var en = get(r, 'entity_type'); en = ents[en] ? en : (entByLabel[en.toLowerCase()] || 'indiv');
          var w9 = get(r, 'w9_date');
          v = { id: uid(), name: name, tin: get(r, 'taxpayer_id_on_file').toUpperCase() === 'Y' ? 'Y' : 'N', w9: /^\d{4}-\d{2}-\d{2}$/.test(w9) ? w9 : '', entity: en, lm: get(r, 'attorney').toUpperCase() === 'Y' };
          S.vendors.push(v); addedV++;
        }
        var d = get(r, 'payment_date'), a = parseFloat(get(r, 'amount')), m = get(r, 'payment_method');
        if (!d && !get(r, 'amount')) return;
        if (!/^\d{4}-\d{2}-\d{2}$/.test(d) || !isFinite(a) || a <= 0 || !meths[m]) { skipped++; return; }
        a = Math.round(a * 100) / 100;
        var dupe = S.payments.some(function (p) { return p.vendor === v.id && p.date === d && p.amount === a && p.method === m; });
        if (dupe) return;
        S.payments.push({ id: uid(), vendor: v.id, date: d, amount: a, method: m }); addedP++;
      });
      save(); render();
      msg('io-msg', 'Imported ' + addedV + ' new vendor' + (addedV === 1 ? '' : 's') + ' and ' + addedP + ' payment' + (addedP === 1 ? '' : 's') + (skipped ? '; skipped ' + skipped + ' row' + (skipped === 1 ? '' : 's') + ' that could not be read' : '') + '.', skipped > 0 && !addedV && !addedP);
    }

    /* ----- events ----- */
    $('v-add').addEventListener('click', addVendor);
    $('v-cancel').addEventListener('click', function () { clearVendorForm(); msg('v-msg', ''); });
    $('p-add').addEventListener('click', addPayment);
    $('b-export').addEventListener('click', exportCSV);
    $('f-import').addEventListener('change', function (e) {
      var f = e.target.files && e.target.files[0]; if (!f) return;
      var rd = new FileReader(); rd.onload = function () { importCSV(String(rd.result)); e.target.value = ''; };
      rd.readAsText(f);
    });
    $('b-clear').addEventListener('click', function () {
      if (!window.confirm('Delete every vendor and payment from this browser? Export a CSV first if you want a copy.')) return;
      S = { vendors: [], payments: [] }; clearVendorForm(); save(); render(); msg('io-msg', 'All data removed from this browser.');
    });
    $('s-cal').addEventListener('click', function () {
      MFA.download('1099-nec-deadline-' + D.deadline.date + '.ics', MFA.ics([{ uid: 'mfa-1099-nec-' + D.deadline.date + '@mfa-advisory.com', date: D.deadline.date, title: 'Send and file 1099-NECs (2026 payments)', note: D.deadline.what, url: D.page_url }], 'MFA 1099 deadline'), 'text/calendar');
    });
    document.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('button[data-act]'); if (!b) return;
      var id = b.getAttribute('data-id'), act = b.getAttribute('data-act');
      if (act === 'edit') {
        var v = vendorById(id); if (!v) return;
        editing = id; $('v-name').value = v.name; $('v-tin').value = v.tin; $('v-w9').value = v.w9 || ''; $('v-entity').value = v.entity; $('v-lm').checked = !!v.lm;
        $('v-add').textContent = 'Save changes'; $('v-cancel').hidden = false; $('v-name').focus(); $('v-name').scrollIntoView({ block: 'center' });
      } else if (act === 'delvendor') {
        var vv = vendorById(id); if (!vv) return;
        if (!window.confirm('Delete ' + vv.name + ' and all of their payments?')) return;
        S.vendors = S.vendors.filter(function (x) { return x.id !== id; }); S.payments = S.payments.filter(function (p) { return p.vendor !== id; });
        if (editing === id) clearVendorForm();
        save(); render();
      } else if (act === 'delpay') {
        S.payments = S.payments.filter(function (p) { return p.id !== id; }); save(); render();
      }
    });
    $('p-date').value = todayISO().slice(0, 4) === YEAR ? todayISO() : YEAR + '-12-31';
    load(); storageNote(); render();
    MFA.trackerState = function () { return S; };
  };

  /* =====================================================================
   * 8. Tax deadlines
   * ===================================================================== */
  MFA.pages.deadlines = function () {
    var cur = [];
    function build() {
      var ent = sel('d-entity'), juris = {};
      ['federal', 'NJ', 'NY'].forEach(function (j) { var c = $('d-j-' + j); juris[j] = c ? c.checked : true; });
      var list = (D.cal[ent] || []).filter(function (e) { return juris[e.jurisdiction]; });
      list = list.slice().sort(function (a, b) { return a.date < b.date ? -1 : (a.date > b.date ? 1 : (a.jurisdiction < b.jurisdiction ? -1 : 1)); });
      return list.map(function (e, i) {
        return { date: e.date, form: e.form, what: e.what, j: e.jurisdiction, note: e.note || '', src: e.source_url,
          title: (e.jurisdiction === 'federal' ? 'IRS' : e.jurisdiction) + ': ' + e.form + ' \u2013 ' + e.what, uid: 'mfa-deadline-' + ent + '-' + e.date + '-' + i + '@mfa-advisory.com', url: D.page_url };
      });
    }
    function run() {
      var ent = sel('d-entity'), info = D.entities.filter(function (x) { return x.id === ent; })[0];
      setText('d-desc', info ? info.desc : '');
      cur = build();
      var today = todayISO(), out = '', lastM = '';
      cur.forEach(function (e, i) {
        var m = fmtDate(e.date, { day: undefined, month: 'long' });
        if (m !== lastM) { out += '<h3 class="dmonth">' + esc(m) + '</h3>'; lastM = m; }
        var past = e.date < today;
        out += '<div class="drow' + (past ? ' past' : '') + '"><div class="dd"><b>' + esc(isoDate(e.date).toLocaleDateString('en-US', { timeZone: 'UTC', day: 'numeric' })) + '</b><span>' + esc(isoDate(e.date).toLocaleDateString('en-US', { timeZone: 'UTC', weekday: 'short' })) + '</span></div>' +
          '<div class="dc"><div class="dt"><b>' + esc(e.form) + '</b><span class="jb j-' + esc(e.j) + '">' + esc(e.j === 'federal' ? 'Federal' : e.j) + '</span>' + (past ? '<span class="jb j-past">Passed</span>' : '') + '</div>' +
          '<p>' + esc(e.what) + '</p>' + (e.note ? '<p class="dn">' + esc(e.note) + '</p>' : '') +
          '<div class="dlinks"><button type="button" class="mini" data-i="' + i + '">Add to calendar (.ics)</button><a class="mini" href="' + esc(gcalLink(e)) + '" target="_blank" rel="noopener">Google Calendar</a><a class="mini" href="' + esc(e.src) + '" target="_blank" rel="noopener">Source</a></div></div></div>';
      });
      $('dlist').innerHTML = out || '<p class="empty">No dates for this combination. Turn on another jurisdiction.</p>';
      setText('d-count', cur.length + ' deadline' + (cur.length === 1 ? '' : 's'));
      $('d-all').disabled = !cur.length;
      $('d-all').textContent = 'Add all ' + cur.length + ' to calendar (.ics)';
      setText('d-next', (function () { for (var i = 0; i < cur.length; i++) if (cur[i].date >= today) return 'Next: ' + fmtDate(cur[i].date, { weekday: 'long' }) + ' \u2013 ' + cur[i].form; return ''; })());
    }
    $('dlist').addEventListener('click', function (ev) {
      var b = ev.target.closest && ev.target.closest('button[data-i]'); if (!b) return;
      var e = cur[+b.getAttribute('data-i')]; if (!e) return;
      MFA.download('mfa-deadline-' + e.date + '.ics', MFA.ics([e], 'MFA tax deadline'), 'text/calendar');
    });
    $('d-all').addEventListener('click', function () {
      var name = sel('d-entity');
      MFA.download('mfa-2027-tax-deadlines-' + name + '.ics', MFA.ics(cur, 'MFA 2027 tax deadlines'), 'text/calendar');
    });
    wire(run);
  };
})();
