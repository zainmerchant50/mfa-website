/* Is It Deductible? (/tools/is-it-deductible/). Site session owns this file.
   Reads the entries from #dd-data (built from data/deductions.json by tools/build_deductible.py). No tax figures live here. */
(function () {
  var d = document, root = d.documentElement;
  var DATA = JSON.parse(d.getElementById('dd-data').textContent);
  var E = DATA.entries, BY = {}, CATS = {};
  E.forEach(function (e, i) { e._i = i; BY[e.slug] = e; });
  DATA.categories.forEach(function (c) { CATS[c.id] = c; });
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var q = d.getElementById('dd-q'), clr = d.getElementById('dd-clear-q'), list = d.getElementById('dd-list'),
    empty = d.getElementById('dd-empty'), count = d.getElementById('dd-count'), resH = d.getElementById('dd-res-h'),
    showAll = d.getElementById('dd-all'), catBtns = [].slice.call(d.querySelectorAll('.dd-cat')),
    cards = {}, cat = '';
  [].slice.call(list.querySelectorAll('.dd-item')).forEach(function (a) { cards[a.getAttribute('data-slug')] = a; });
  if (window.matchMedia && matchMedia('(max-width: 480px)').matches) q.setAttribute('placeholder', 'Try meals, laptop, phone');

  /* ---------- search: name + aliases ---------- */
  function words(s) { return s.toLowerCase().replace(/[^a-z0-9%$&]+/g, ' ').trim().split(' ').filter(Boolean); }
  E.forEach(function (e) {
    e._phr = [e.name.toLowerCase()].concat(e.aliases.map(function (a) { return a.toLowerCase(); }));
    e._w = {}; e._phr.forEach(function (p) { words(p).forEach(function (w) { e._w[w] = 1; }); });
    e._nw = words(e.name);
  });
  function match(e, toks, mode) {
    return toks.every(function (t) {
      if (mode === 'whole') return !!e._w[t] || !!e._w[t.replace(/s$/, '')] || !!e._w[t + 's'];
      for (var w in e._w) if (w.indexOf(t) === 0) return true;
      return false;
    });
  }
  function score(e, qs, toks) {
    var s = 0;
    if (e._phr.indexOf(qs) > -1) s += 5;
    if (e.name.toLowerCase().indexOf(qs) === 0) s += 2;
    toks.forEach(function (t) { if (e._nw.indexOf(t) > -1) s += 1; });
    return s;
  }
  function search(qs) {
    var toks = words(qs);
    if (!toks.length) return null;
    var pool = E.filter(function (e) { return !cat || e.category === cat; });
    var hits = pool.filter(function (e) { return match(e, toks, 'whole'); });
    if (!hits.length) hits = pool.filter(function (e) { return match(e, toks, 'prefix'); });
    var nq = toks.join(' ');
    return hits.map(function (e) { return [score(e, nq, toks), e]; })
      .sort(function (a, b) { return b[0] - a[0] || a[1]._i - b[1]._i; }).map(function (x) { return x[1]; });
  }

  var timer;
  function run(fromUser) {
    var qs = (q.value || '').trim(), res = search(qs), shown;
    clr.hidden = !qs;
    if (res === null) shown = E.filter(function (e) { return !cat || e.category === cat; });
    else shown = res;
    var on = {};
    shown.forEach(function (e, i) { on[e.slug] = 1; var c = cards[e.slug]; list.appendChild(c); c.style.animationDelay = still ? '0ms' : Math.min(i, 8) * 35 + 'ms'; });
    E.forEach(function (e) { var c = cards[e.slug], vis = !!on[e.slug]; if (c.hidden === vis) { c.hidden = !vis; if (vis && !still) { c.style.animation = 'none'; c.offsetHeight; c.style.animation = ''; } } });
    empty.hidden = shown.length > 0;
    d.getElementById('dd-empty-q').textContent = qs;
    var label = cat ? CATS[cat].name : (qs ? 'Results' : 'All expenses');
    resH.textContent = label;
    count.textContent = shown.length === 1 ? '1 expense' : shown.length + ' expenses';
    showAll.hidden = !cat && !qs;
    if (fromUser && qs && window.gtag) { clearTimeout(timer); timer = setTimeout(function () { try { gtag('event', 'deduction_search', { search_term: qs.slice(0, 60), results: shown.length }); } catch (x) {} }, 1200); }
  }
  q.addEventListener('input', function () { run(true); });
  q.addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter') { ev.preventDefault(); var first = list.querySelector('.dd-item:not([hidden])'); if (first) first.focus(); }
  });
  clr.addEventListener('click', function () { q.value = ''; run(); q.focus(); });
  [].slice.call(d.querySelectorAll('.dd-chip')).forEach(function (b) {
    b.addEventListener('click', function () { q.value = b.getAttribute('data-q'); run(true);
      d.getElementById('dd-results').scrollIntoView({ behavior: still ? 'auto' : 'smooth', block: 'start' }); });
  });
  function setCat(id) {
    cat = id;
    catBtns.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-cat') === cat ? 'true' : 'false'); });
    run();
  }
  catBtns.forEach(function (b) {
    b.addEventListener('click', function () { var id = b.getAttribute('data-cat'); setCat(cat === id ? '' : id);
      if (cat) d.getElementById('dd-results').scrollIntoView({ behavior: still ? 'auto' : 'smooth', block: 'start' }); });
  });
  showAll.addEventListener('click', function () { q.value = ''; setCat(''); });

  /* ---------- popup ---------- */
  var modal = d.getElementById('dd-modal'), sheet = d.getElementById('dd-sheet'), body = d.getElementById('dd-mbody'),
    closeBtn = d.getElementById('dd-close'), back = d.getElementById('dd-back'), lastFocus = null, current = null, hideT;
  var VERB = DATA.verdicts;
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function ring(p) {
    var C = 2 * Math.PI * 40, off = C * (1 - p / 100);
    return '<div class="dd-ring" role="img" aria-label="' + p + ' percent deductible"><svg viewBox="0 0 92 92" aria-hidden="true">' +
      '<circle class="trk" cx="46" cy="46" r="40" fill="none" stroke-width="9"/>' +
      '<circle class="val" cx="46" cy="46" r="40" fill="none" stroke-width="9" stroke-linecap="round" stroke-dasharray="' + C.toFixed(2) +
      '" stroke-dashoffset="' + (still ? off : C).toFixed(2) + '" data-off="' + off.toFixed(2) + '"/></svg><b>' + p + '%</b></div>';
  }
  function render(e) {
    var v = VERB[e.verdict];
    var vis = e.percent !== null && e.percent !== undefined ? ring(e.percent) : '<span class="dd-ico" aria-hidden="true">' + DATA.icons[e.verdict] + '</span>';
    var src = '<li>Source: <a href="' + esc(e.source_url) + '" target="_blank" rel="noopener">' + esc(e.source_title) + '</a></li>' +
      (e.also || []).map(function (s) { return '<li>Also: <a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.title) + '</a></li>'; }).join('');
    var tools = (e.tools || []).map(function (u) { return DATA.tools[u] ? '<a href="' + esc(u) + '">' + esc(DATA.tools[u]) + '</a>' : ''; }).join('');
    return '<span class="eb">' + esc(CATS[e.category].name) + '</span><h2 id="dd-mtitle">' + esc(e.name) + '</h2>' +
      '<div class="dd-v v-' + e.verdict + '">' + vis + '<div><span class="dd-badge">' + esc(v.label) + '</span><div class="big">' +
      esc(e.percent !== null && e.percent !== undefined ? (e.verdict === 'not' ? 'Not deductible' : e.percent + '% deductible') : v.big) + '</div><p>' + esc(v.line) + '</p></div></div>' +
      '<section class="dd-sec"><h3>The rule</h3><p>' + esc(e.rule) + '</p></section>' +
      '<section class="dd-sec"><h3>Limits</h3><p>' + esc(e.limits) + '</p></section>' +
      '<section class="dd-sec"><h3>Records to keep</h3><p>' + esc(e.records) + '</p></section>' +
      '<section class="dd-sec"><h3>Who it applies to</h3><p>' + esc(e.applies_to) + '</p></section>' +
      '<section class="dd-sec"><h3>Official sources</h3><ul>' + src + '</ul><p class="ck">Facts checked ' + esc(DATA.checked_label) + '.</p></section>' +
      (tools ? '<section class="dd-sec"><h3>Related MFA tools</h3><div class="dd-tools">' + tools + '</div></section>' : '') +
      '<p class="dd-mnote">' + esc(DATA.short_disclaimer) + '</p>' +
      '<div class="dd-acts"><a class="dd-btn gold" href="/#book" data-conv="book">Need help? Book a consultation</a>' +
      '<button type="button" class="dd-btn line" id="dd-copy">Copy link</button></div>';
  }
  function focusables() {
    return [].slice.call(sheet.querySelectorAll('a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])')).filter(function (el) { return el.offsetParent !== null || el === closeBtn; });
  }
  function open(slug, opts) {
    var e = BY[slug]; if (!e) return;
    clearTimeout(hideT);
    if (!current) lastFocus = (opts && opts.from) || d.activeElement;
    current = slug;
    body.innerHTML = render(e);
    sheet.scrollTop = 0;
    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');
    root.classList.add('dd-lock');
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      modal.classList.add('open');
      closeBtn.focus({ preventScroll: true });
      var v = body.querySelector('.dd-ring .val'); if (v) v.setAttribute('stroke-dashoffset', v.getAttribute('data-off'));
    }); });
    if (location.hash !== '#' + slug) history.replaceState(null, '', '#' + slug);
    var cp = d.getElementById('dd-copy');
    cp.addEventListener('click', function () {
      var u = location.origin + location.pathname + '#' + slug;
      var done = function () { cp.textContent = 'Link copied'; setTimeout(function () { cp.textContent = 'Copy link'; }, 1800); };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(u).then(done, function () {}); else done();
    });
    if (window.gtag) try { gtag('event', 'deduction_view', { item: slug, verdict: e.verdict }); } catch (x) {}
  }
  function close() {
    if (!current) return;
    current = null;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    root.classList.remove('dd-lock');
    hideT = setTimeout(function () { modal.hidden = true; body.innerHTML = ''; }, still ? 0 : 420);
    if (location.hash) history.replaceState(null, '', location.pathname + location.search);
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  list.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('.dd-item'); if (!a) return;
    ev.preventDefault(); open(a.getAttribute('data-slug'), { from: a });
  });
  closeBtn.addEventListener('click', close);
  back.addEventListener('click', close);
  d.addEventListener('keydown', function (ev) {
    if (!current) return;
    if (ev.key === 'Escape') { ev.preventDefault(); close(); return; }
    if (ev.key === 'Tab') {
      var f = focusables(); if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (ev.shiftKey && (d.activeElement === first || !sheet.contains(d.activeElement))) { ev.preventDefault(); last.focus(); }
      else if (!ev.shiftKey && (d.activeElement === last || !sheet.contains(d.activeElement))) { ev.preventDefault(); first.focus(); }
    }
  });
  function fromHash() {
    var h = decodeURIComponent(location.hash.replace(/^#/, ''));
    if (h && BY[h]) { if (current !== h) open(h); }
    else if (current && !h) close();
  }
  window.addEventListener('hashchange', fromHash);
  run();
  fromHash();
})();
