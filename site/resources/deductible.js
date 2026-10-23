/* Is It Deductible? (/tools/is-it-deductible/). Site session owns this file.
   Every answer is already in the HTML (tools/build_deductible.py). This script adds: search (name, everyday words and topic
   from #dd-data) with a results list, and the answer sheet (a native <dialog>) that shows a copy of an answer when a card,
   a result or a list row is tapped, or when the page opens with #slug. No tax figures live here. */
(function () {
  var d = document, W = window;
  var $ = function (id) { return d.getElementById(id); };
  var DATA = JSON.parse($('dd-data').textContent), E = DATA.entries, BY = {};
  E.forEach(function (e, i) {
    e._i = i; BY[e.slug] = e;
    e._n = e.name.toLowerCase();
    e._a = e.aliases.map(function (a) { return a.toLowerCase(); });
    e._w = (e._n + ' ' + e._a.join(' ') + ' ' + e.group.toLowerCase()).replace(/[^a-z0-9%$&]+/g, ' ').trim().split(' ');
  });
  var q = $('dd-q'), clr = $('dd-clear'), res = $('dd-res'), hits = $('dd-hits'), count = $('dd-count');
  var sheet = $('dd-sheet'), sb = $('dd-sb'), st = $('dd-st'), sic = $('dd-sic'), back = null;
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };

  /* ---------- search ---------- */
  function stem(t) { return t.length > 3 && /s$/.test(t) && !/ss$/.test(t) ? t.slice(0, -1) : t; }
  function score(e, s, toks) {
    if (e._n === s || e._a.indexOf(s) > -1) return 100;
    if (e._n.indexOf(s) === 0 || e._a.some(function (a) { return a.indexOf(s) === 0; })) return 80;
    var all = toks.every(function (t) { return e._w.some(function (w) { return w.indexOf(t) === 0; }); });
    if (!all) return 0;
    return e._w.slice(0, e._n.split(' ').length).some(function (w) { return w.indexOf(toks[0]) === 0; }) ? 60 : 40;
  }
  function search() {
    var s = q.value.toLowerCase().replace(/[^a-z0-9%$&' ]+/g, ' ').replace(/\s+/g, ' ').trim();
    clr.hidden = !q.value;
    if (!s) { res.hidden = true; hits.innerHTML = ''; return; }
    var toks = s.replace(/'/g, '').split(' ').map(stem);
    var found = E.map(function (e) { return { e: e, s: score(e, s, toks) }; })
      .filter(function (r) { return r.s > 0; })
      .sort(function (a, b) { return b.s - a.s || a.e._i - b.e._i; }).slice(0, 8);
    hits.innerHTML = found.map(function (r) {
      var e = r.e, row = $(e.slug), ic = row ? row.querySelector('.ic').innerHTML : '', pill = row ? row.querySelector('summary .vb').outerHTML : '';
      return '<li><button type="button" class="hit" data-open="' + e.slug + '"><span class="ic">' + ic + '</span><span class="t"><b>' + esc(e.name) +
        '</b><small>' + esc(e.group) + '</small></span>' + pill + '</button></li>';
    }).join('');
    count.innerHTML = found.length
      ? found.length + (found.length === 1 ? ' match' : ' matches') + '. Tap one for the full answer.'
      : 'Nothing matches “' + esc(q.value.trim()) + '” yet. Try a simpler word, like “car” or “phone”, or <a href="/book/" data-conv="book">ask us about it</a>.';
    res.hidden = false;
  }
  if (q) {
    q.addEventListener('input', search);
    q.addEventListener('keydown', function (ev) {
      var first = hits.querySelector('.hit');
      if (ev.key === 'ArrowDown' && first) { ev.preventDefault(); first.focus(); }
      else if (ev.key === 'Enter' && first) { ev.preventDefault(); open(first.getAttribute('data-open'), q); }
      else if (ev.key === 'Escape') { q.value = ''; search(); }
    });
    hits.addEventListener('keydown', function (ev) {
      var b = [].slice.call(hits.querySelectorAll('.hit')), i = b.indexOf(d.activeElement);
      if (ev.key === 'ArrowDown' && i < b.length - 1) { ev.preventDefault(); b[i + 1].focus(); }
      else if (ev.key === 'ArrowUp') { ev.preventDefault(); (i > 0 ? b[i - 1] : q).focus(); }
      else if (ev.key === 'Escape') { q.focus(); }
    });
    clr.addEventListener('click', function () { q.value = ''; search(); q.focus(); });
    d.addEventListener('click', function (ev) {
      if (!res.hidden && !ev.target.closest('.dd-find') && !ev.target.closest('#dd-sheet')) res.hidden = true;
    });
    q.addEventListener('focus', function () { if (q.value.trim()) res.hidden = false; });
  }

  /* ---------- the answer sheet ---------- */
  var canModal = sheet && typeof sheet.showModal === 'function';
  function open(slug, from) {
    var row = $(slug);
    if (!BY[slug] || !row) return;
    if (!canModal) {  // older browsers: open the row in the list instead
      var g = row.closest('.grp'); if (g) g.open = true;
      row.open = true; row.scrollIntoView({ block: 'start' }); return;
    }
    back = from || d.activeElement;
    st.textContent = BY[slug].name;
    sic.className = 'ic'; sic.innerHTML = row.querySelector('.ic').innerHTML;
    sb.innerHTML = ''; sb.appendChild(row.querySelector('.ans').cloneNode(true));
    sb.scrollTop = 0;
    if (!sheet.open) sheet.showModal();
    d.documentElement.classList.add('dd-lock');
    if (history.replaceState) history.replaceState(null, '', '#' + slug);
  }
  function closed() {
    d.documentElement.classList.remove('dd-lock');
    if (history.replaceState && location.hash) history.replaceState(null, '', location.pathname + location.search);
    if (back && back.focus) back.focus();
    back = null;
  }
  if (sheet) {
    sheet.addEventListener('close', closed);
    $('dd-sx').addEventListener('click', function () { sheet.close(); });
    sheet.addEventListener('click', function (ev) { if (ev.target === sheet) sheet.close(); });  // tap on the backdrop
  }
  d.addEventListener('click', function (ev) {
    var t = ev.target.closest('[data-open]');
    if (t) { ev.preventDefault(); open(t.getAttribute('data-open'), t); return; }
    var s = ev.target.closest('.ex > summary');
    if (s && canModal) { ev.preventDefault(); open(s.parentNode.id, s); }
  });
  function fromHash() {
    var h = decodeURIComponent(location.hash.slice(1));
    if (h && BY[h]) open(h, null);
  }
  W.addEventListener('hashchange', fromHash);
  fromHash();
})();
