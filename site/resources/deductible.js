/* Is It Deductible? (/tools/is-it-deductible/). Site session owns this file.
   Every answer is already in the HTML (tools/build_deductible.py). This script adds: search (name + aliases from #dd-data),
   category filters with FLIP reordering, the typewriter placeholder, the "Most searched" belt, card tilt, scroll reveals and
   the detail popup (built from the card's own markup). No tax figures live here. Reduced motion = instant states. */
(function () {
  var d = document, root = d.documentElement, W = window;
  var DATA = JSON.parse(d.getElementById('dd-data').textContent);
  var E = DATA.entries, BY = {}, CATS = {};
  E.forEach(function (e, i) { e._i = i; BY[e.slug] = e; });
  DATA.categories.forEach(function (c) { CATS[c.id] = c; });
  var mq = function (q) { return W.matchMedia && W.matchMedia(q).matches; };
  var still = mq('(prefers-reduced-motion: reduce)');
  var EASE = 'cubic-bezier(.16,1,.3,1)';
  var $ = function (id) { return d.getElementById(id); };
  var q = $('dd-q'), clr = $('dd-clear-q'), list = $('dd-list'), empty = $('dd-empty'), count = $('dd-count'), resH = $('dd-res-h'),
    showAll = $('dd-all'), results = $('dd-results'), catBtns = [].slice.call(d.querySelectorAll('.dd-cat')),
    cards = {}, cat = '', allLabel = resH.textContent;
  [].slice.call(list.querySelectorAll('.dd-item')).forEach(function (a) { cards[a.getAttribute('data-slug')] = a; });

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

  /* ---------- results with FLIP: cards glide to their new place, newcomers fade up ---------- */
  var timer;
  function run(fromUser) {
    var qs = (q.value || '').trim(), res = search(qs), shown, before = {};
    clr.hidden = !qs;
    shown = res === null ? E.filter(function (e) { return !cat || e.category === cat; }) : res;
    var animate = !still && 'animate' in list && results.getBoundingClientRect().top < W.innerHeight;
    if (animate) E.forEach(function (e) { var c = cards[e.slug]; if (!c.hidden) before[e.slug] = c.getBoundingClientRect(); });
    var on = {};
    shown.forEach(function (e) { on[e.slug] = 1; list.appendChild(cards[e.slug]); });
    E.forEach(function (e) { cards[e.slug].hidden = !on[e.slug]; });
    if (animate) {
      shown.forEach(function (e, i) {
        var c = cards[e.slug], b = before[e.slug], a = c.getBoundingClientRect();
        if (c.getAnimations) c.getAnimations().forEach(function (x) { x.cancel(); });
        if (b && Math.abs(b.top - a.top) < W.innerHeight) {
          var dx = b.left - a.left, dy = b.top - a.top;
          if (dx || dy) c.animate([{ transform: 'translate(' + dx + 'px,' + dy + 'px)' }, { transform: 'none' }], { duration: 480, easing: EASE });
        } else if (a.top < W.innerHeight + 200) {
          c.animate([{ opacity: 0, transform: 'translateY(14px) scale(.97)' }, { opacity: 1, transform: 'none' }],
            { duration: 420, delay: Math.min(i, 9) * 30, easing: EASE, fill: 'backwards' });
        }
      });
    }
    empty.hidden = shown.length > 0;
    $('dd-empty-q').textContent = qs;
    resH.textContent = cat ? CATS[cat].name : (qs ? 'Results' : allLabel);
    count.textContent = shown.length === 1 ? '1 expense' : shown.length + ' expenses';
    showAll.hidden = !cat && !qs;
    if (fromUser && qs && W.gtag) { clearTimeout(timer); timer = setTimeout(function () { try { gtag('event', 'deduction_search', { search_term: qs.slice(0, 60), results: shown.length }); } catch (x) {} }, 1200); }
  }
  q.addEventListener('input', function () { run(true); });
  q.addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter') { ev.preventDefault(); var first = list.querySelector('.dd-item:not([hidden]) .dd-open'); if (first) first.focus(); }
  });
  clr.addEventListener('click', function () { q.value = ''; run(); q.focus(); });
  function toResults() { results.scrollIntoView({ behavior: still ? 'auto' : 'smooth', block: 'start' }); }
  [].slice.call(d.querySelectorAll('.dd-chip')).forEach(function (b) {
    b.addEventListener('click', function () { q.value = b.getAttribute('data-q'); toResults(); setTimeout(function () { run(true); }, still ? 0 : 350); });
  });
  function setCat(id) {
    cat = id;
    catBtns.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-cat') === cat ? 'true' : 'false'); });
    run();
  }
  catBtns.forEach(function (b) {
    b.addEventListener('click', function () { var id = b.getAttribute('data-cat'); setCat(cat === id ? '' : id); if (cat) toResults(); });
  });
  showAll.addEventListener('click', function () { q.value = ''; setCat(''); });

  /* ---------- typewriter placeholder (stops while the box is in use) ---------- */
  (function () {
    var base = q.getAttribute('placeholder'), ex = [];
    try { ex = JSON.parse(q.getAttribute('data-examples') || '[]'); } catch (x) {}
    var small = mq('(max-width: 480px)'), lead = small ? 'Try ' : 'Search an expense, e.g. ';
    if (small) { base = 'Try meals, laptop, phone'; q.setAttribute('placeholder', base); }
    if (still || !ex.length) return;
    var k = 0, n = 0, dir = 1, t;
    function busy() { return d.activeElement === q || q.value; }
    function tick() {
      if (busy() || d.hidden) { q.setAttribute('placeholder', base); t = setTimeout(tick, 1200); return; }
      var w = ex[k];
      n += dir;
      q.setAttribute('placeholder', lead + w.slice(0, n));
      if (dir > 0 && n >= w.length) { dir = -1; t = setTimeout(tick, 1700); return; }
      if (dir < 0 && n <= 0) { dir = 1; k = (k + 1) % ex.length; t = setTimeout(tick, 350); return; }
      t = setTimeout(tick, dir > 0 ? 75 + Math.random() * 60 : 32);
    }
    t = setTimeout(tick, 3400);
  })();

  /* ---------- reveals and card tilt ---------- */
  var seenEls = [].slice.call(d.querySelectorAll('.dd-cats,.dd-legend'));
  if ('IntersectionObserver' in W && !still) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add('seen'); io.unobserve(x.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    seenEls.forEach(function (el) { io.observe(el); });
  } else seenEls.forEach(function (el) { el.classList.add('seen'); });
  if (!still && mq('(hover: hover) and (pointer: fine)')) {
    catBtns.forEach(function (b) {
      b.addEventListener('pointermove', function (ev) {
        var r = b.getBoundingClientRect(), x = (ev.clientX - r.left) / r.width, y = (ev.clientY - r.top) / r.height;
        b.style.setProperty('--ry', ((x - .5) * 9).toFixed(2) + 'deg');
        b.style.setProperty('--rx', ((.5 - y) * 9).toFixed(2) + 'deg');
        b.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
        b.style.setProperty('--my', (y * 100).toFixed(1) + '%');
      });
      b.addEventListener('pointerleave', function () { b.style.setProperty('--rx', '0deg'); b.style.setProperty('--ry', '0deg'); });
    });
  }

  /* ---------- popup ---------- */
  var modal = $('dd-modal'), sheet = $('dd-sheet'), body = $('dd-mbody'), closeBtn = $('dd-close'), back = $('dd-back'),
    lastFocus = null, current = null, pushed = false, hideT;
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function ring(p) {
    var C = 2 * Math.PI * 40, off = C * (1 - p / 100);
    return '<div class="dd-ring" role="img" aria-label="' + p + ' percent deductible"><svg viewBox="0 0 92 92" aria-hidden="true">' +
      '<circle class="trk" cx="46" cy="46" r="40" fill="none" stroke-width="9"/>' +
      '<circle class="val" cx="46" cy="46" r="40" fill="none" stroke-width="9" stroke-linecap="round" stroke-dasharray="' + C.toFixed(2) +
      '" stroke-dashoffset="' + (still ? off : C).toFixed(2) + '" data-off="' + off.toFixed(2) + '"/></svg><b aria-hidden="true" data-p="' + p + '">' + (still ? p : 0) + '%</b></div>';
  }
  function render(e) {
    var v = DATA.verdicts[e.verdict], full = cards[e.slug].querySelector('.dd-full').cloneNode(true);
    [].slice.call(full.querySelectorAll('h4')).forEach(function (h) { var n = d.createElement('h3'); n.innerHTML = h.innerHTML; h.parentNode.replaceChild(n, h); });
    var vl = full.querySelector('.dd-vl'), line = vl ? vl.lastChild.textContent.trim() : '';
    if (vl) vl.parentNode.removeChild(vl);
    full.querySelector('.dd-srcs').insertAdjacentHTML('beforeend', '<p class="ck">Facts checked ' + esc(DATA.checked_label) + '.</p>');
    var pct = e.percent !== null && e.percent !== undefined;
    var vis = pct && e.verdict !== 'not' ? ring(e.percent) : '<span class="dd-ico" aria-hidden="true">' + DATA.icons[e.verdict] + '</span>';
    var big = e.verdict === 'not' ? v.big : (pct ? e.percent + '% deductible' : v.big);
    return '<span class="eb">' + esc(CATS[e.category].name) + '</span><h2 id="dd-mtitle">' + esc(e.name) + '</h2>' +
      '<div class="dd-v v-' + e.verdict + '">' + vis + '<div><span class="dd-vstamp">' + esc(v.label) + '</span><div class="big">' + esc(big) +
      '</div><p>' + esc(line) + '</p></div></div>' + full.innerHTML +
      '<p class="dd-mnote">' + esc(DATA.short_disclaimer) + '</p>' +
      '<div class="dd-acts"><a class="dd-btn gold" href="/#book" data-conv="book">Book a 30-minute call</a>' +
      '<button type="button" class="dd-btn line" id="dd-copy">Copy link</button></div>';
  }
  function countUp(b) {
    var p = +b.getAttribute('data-p'), t0 = null, dur = 1100, delay = 200;
    function f(ts) {
      if (t0 === null) t0 = ts + delay;
      var k = Math.max(0, Math.min(1, (ts - t0) / dur)), e = 1 - Math.pow(1 - k, 3);
      b.textContent = Math.round(p * e) + '%';
      if (k < 1 && current) requestAnimationFrame(f);
    }
    requestAnimationFrame(f);
  }
  function focusables() {
    return [].slice.call(sheet.querySelectorAll('a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])')).filter(function (el) { return el.offsetParent !== null || el === closeBtn; });
  }
  function show(slug, from) {
    var e = BY[slug]; if (!e) return;
    clearTimeout(hideT);
    if (!current) lastFocus = from || cards[slug].querySelector('.dd-open');
    current = slug;
    body.innerHTML = render(e);
    sheet.scrollTop = 0;
    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');
    root.classList.add('dd-lock');
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      modal.classList.add('open');
      closeBtn.focus({ preventScroll: true });
      var r = body.querySelector('.dd-ring .val'); if (r) r.setAttribute('stroke-dashoffset', r.getAttribute('data-off'));
      var b = body.querySelector('.dd-ring b'); if (b && !still) countUp(b);
    }); });
    var cp = $('dd-copy');
    cp.addEventListener('click', function () {
      var u = location.origin + location.pathname + '#' + slug;
      var done = function () { cp.textContent = 'Link copied'; setTimeout(function () { cp.textContent = 'Copy link'; }, 1800); };
      if (navigator.clipboard && W.isSecureContext) navigator.clipboard.writeText(u).then(done, function () {}); else done();
    });
    if (W.gtag) try { gtag('event', 'deduction_view', { item: slug, verdict: e.verdict }); } catch (x) {}
  }
  function hide() {
    if (!current) return;
    current = null;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    root.classList.remove('dd-lock');
    hideT = setTimeout(function () { modal.hidden = true; body.innerHTML = ''; }, still ? 0 : 420);
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  /* Opening from a card adds a history entry, so the phone's Back button closes the popup. */
  function openFromCard(slug, from) {
    if (location.hash !== '#' + slug) { history.pushState({ dd: slug }, '', '#' + slug); pushed = true; }
    show(slug, from);
  }
  function requestClose() {
    if (!current) return;
    if (pushed) { pushed = false; history.back(); setTimeout(function () { if (current) { hide(); history.replaceState(null, '', location.pathname + location.search); } }, 400); }
    else { history.replaceState(null, '', location.pathname + location.search); hide(); }
  }
  list.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('.dd-item'); if (!a) return;
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button === 1) return;
    ev.preventDefault(); openFromCard(a.getAttribute('data-slug'), a.querySelector('.dd-open'));
  });
  closeBtn.addEventListener('click', requestClose);
  back.addEventListener('click', requestClose);
  d.addEventListener('keydown', function (ev) {
    if (!current) return;
    if (ev.key === 'Escape') { ev.preventDefault(); requestClose(); return; }
    if (ev.key === 'Tab') {
      var f = focusables(); if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (ev.shiftKey && (d.activeElement === first || !sheet.contains(d.activeElement))) { ev.preventDefault(); last.focus(); }
      else if (!ev.shiftKey && (d.activeElement === last || !sheet.contains(d.activeElement))) { ev.preventDefault(); first.focus(); }
    }
  });
  function fromHash() {
    var h = decodeURIComponent(location.hash.replace(/^#/, ''));
    if (h && BY[h]) { if (current !== h) show(h); }
    else if (current) { pushed = false; hide(); }
  }
  W.addEventListener('popstate', fromHash);
  W.addEventListener('hashchange', fromHash);
  run();
  fromHash();
})();
