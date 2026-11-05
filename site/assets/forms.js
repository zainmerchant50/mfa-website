/* MFA lead-form safety net (Hub, 2026-11-04). Loaded site-wide right after ads.js (see tools/ads.py TAG).
   Every lead form posts to FormSubmit (formsubmit.co/ajax/...). FormSubmit went down (503 / no response),
   so leads were lost. This wraps fetch: each FormSubmit send is ALSO saved to MailerLite
   (form 203186546079172505 -> group "Website leads (backup)", fields name, phone, lead_details).
   The form reports success as soon as EITHER service accepts it; FormSubmit keeps going in the
   background (keepalive) so the email notification still arrives when it is up.
   QA: send a test from every form type after any change (see claude/site/hub-qa-checklist.md). */
(function (w) {
  if (w.__mfaRelay || !w.fetch) return;
  w.__mfaRelay = 1;
  var ML = 'https://assets.mailerlite.com/jsonp/2707043/forms/203186546079172505/subscribe';
  var raw = w.fetch.bind(w);

  function details(fd) {
    var subj = '', out = [];
    fd.forEach(function (v, k) {
      if (typeof v !== 'string' || !v) return;
      if (k === '_subject') { subj = v; return; }
      if (/^_|^(your-)?(email|name|phone)$/.test(k)) return;
      out.push(k + ': ' + v.replace(/\s+/g, ' '));
    });
    return ((subj ? subj + ' | ' : '') + out.join(' | ')).slice(0, 1000);
  }

  function saveToMailerLite(fd) {
    var pick = function (re) { var v = ''; fd.forEach(function (x, k) { if (!v && typeof x === 'string' && x.trim() && re.test(k)) v = x.trim(); }); return v; };
    var em = String(fd.get('email') || fd.get('_replyto') || pick(/e-?mail/i) || '').trim();
    if (!/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(em)) return Promise.resolve(false);
    var m = new FormData();
    m.append('fields[email]', em);
    var n = fd.get('name') || pick(/(^|-)name$/i); if (n) m.append('fields[name]', String(n).trim());
    var p = fd.get('phone') || pick(/phone|tel/i); if (p) m.append('fields[phone]', String(p).trim());
    m.append('fields[lead_details]', details(fd) || ('page: ' + w.location.pathname));
    m.append('ml-submit', '1');
    m.append('anticsrf', 'true');
    return raw(ML, { method: 'POST', headers: { 'Accept': 'application/json' }, body: m })
      .then(function (r) {
        // A real answer from MailerLite: trust it (an error page is a failure, never a silent success).
        if (!r.ok) return false;
        return r.json().then(function (j) { return !!j && j.success === true; }, function () { return false; });
      }, function () {
        // Network/CORS block only: retry opaque (as the site's newsletter forms do).
        return raw(ML, { method: 'POST', mode: 'no-cors', body: m }).then(function () { return true; }, function () { return false; });
      });
  }

  // Lead tracking (Zain's yes, 2026-11-05): once a lead send is accepted (the form's thanks state), fire the
  // Google Ads "Submit lead form" conversion + GA4 generate_lead via window.mfaLead (ads.js; it skips internal/test
  // traffic and ignores a repeat within 5 s). Unsubscribes, blog questions and PAID notices are not leads.
  var NOT_LEAD = /^(newsletter unsubscribe|blog question|paid)/i;
  function trackLead(fd) {
    try {
      var subj = String(fd.get('_subject') || '');
      if (NOT_LEAD.test(subj) || typeof w.mfaLead !== 'function') return;
      var kind = (subj.split(':')[0] || 'lead').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'lead';
      w.mfaLead(kind, { page_path: w.location.pathname });
    } catch (e) { /* tracking must never break the form */ }
  }

  function reply(ok) {
    return new Response(JSON.stringify(ok ? { success: true } : { success: false, message: 'Send failed' }),
      { status: ok ? 200 : 502, headers: { 'Content-Type': 'application/json' } });
  }

  w.fetch = function (input, init) {
    try {
      var url = typeof input === 'string' ? input : (input && input.url) || '';
      if (url.indexOf('formsubmit.co/ajax/') !== -1 && init && init.body instanceof FormData) {
        var fd = init.body;
        var fs = raw(input, Object.assign({}, init, { keepalive: true }))
          .then(function (r) { return r.ok; }, function () { return false; });
        var ml = saveToMailerLite(fd);
        return new Promise(function (resolve) {
          var done = false, left = 2;
          function fin(ok) {
            if (done) return;
            if (ok) { done = true; trackLead(fd); resolve(reply(true)); }
            else if (--left === 0) { done = true; resolve(reply(false)); }
          }
          fs.then(fin); ml.then(fin);
          setTimeout(function () { if (!done) { done = true; resolve(reply(false)); } }, 15000);
        });
      }
    } catch (e) { /* fall through to the normal request */ }
    return raw(input, init);
  };
})(window);
