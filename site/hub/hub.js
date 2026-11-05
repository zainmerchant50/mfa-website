/* MFA Hub v2 (private). All data comes from /api/hub/* and goes on the page with textContent / SVG attributes only. */
(function () {
  "use strict";
  var PAGE = document.body.getAttribute("data-page");
  var TZ = "America/New_York";
  var SVGNS = "http://www.w3.org/2000/svg";
  var COLORS = { "Google Ads": "#10233F", "Pinterest Ads": "#B08D3F", "Fiverr Ads": "#2f6f4e", "Etsy Ads": "#9a5d0c", Instagram: "#8a4f7d", Facebook: "#2c4f86", TikTok: "#151515", LinkedIn: "#1f6f9a", "YouTube Shorts": "#b3261e", Pinterest: "#D8B769" };
  var PALETTE = ["#10233F", "#B08D3F", "#2c4f86", "#2f6f4e", "#8a4f7d", "#b3261e", "#1f6f9a", "#9a5d0c", "#5b6573", "#D8B769"];
  var $ = function (id) { return document.getElementById(id); };

  // ---------- DOM helpers (text only) ----------
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined && text !== null) e.textContent = String(text); return e; }
  function add(p) { for (var i = 1; i < arguments.length; i++) { var k = arguments[i]; if (k === null || k === undefined || k === false) continue; p.appendChild(typeof k === "string" ? document.createTextNode(k) : k); } return p; }
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); return n; }
  function btn(cls, text, fn) { var b = el("button", cls, text); b.type = "button"; if (fn) b.addEventListener("click", fn); return b; }
  function svg(tag, attrs) { var e = document.createElementNS(SVGNS, tag); for (var k in attrs) if (attrs[k] !== undefined) e.setAttribute(k, String(attrs[k])); return e; }
  var HL = window.HubLinks, LINKS = {}, H = HL.parseHash(location.hash), DATA = null;
  // outbound: https only (HubLinks.safeUrl), new tab, no opener/referrer; an unexpected host is shown next to the label
  function link(url, label) { var u = HL.safeUrl(url); if (!u) return null; var a = el("a", "ext", (label || "open") + (HL.known(u) ? "" : " (" + HL.host(u) + ")")); a.href = u; a.target = "_blank"; a.rel = "noopener noreferrer"; return a; }
  function ext(lk, label) { return lk ? link(lk.url, (label || lk.label) + " ↗") : null; }
  // in-hub link (href always comes from HubLinks.route)
  function hl(text, href, cls) { var a = el("a", "dl" + (cls ? " " + cls : ""), text); a.href = href; return a; }
  function merge(a, b) { var o = {}, k; for (k in a) o[k] = a[k]; for (k in b) o[k] = b[k]; return o; }
  function setHash(p) { var q = HL.qs(p); if (q !== location.hash.replace(/^#/, "")) location.hash = q; }
  function pill(s) { return el("span", "pill " + String(s || "").replace(/[^A-Za-z_]/g, ""), String(s || "—").replace(/_/g, " ")); }
  function clip(text) { var d = el("div", "clip", text || ""); d.title = "Click to expand"; d.addEventListener("click", function () { d.classList.toggle("open"); }); return d; }

  // ---------- formatting ----------
  function ymdET(d) { return (d instanceof Date ? d : new Date(d)).toLocaleDateString("en-CA", { timeZone: TZ }); }
  function today() { return ymdET(new Date()); }
  function addDays(ymd, n) { var d = new Date(ymd + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  function fmtD(iso, time) {
    if (!iso) return "";
    var d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso + "T12:00:00Z" : iso);
    if (isNaN(d)) return String(iso);
    var o = { timeZone: /^\d{4}-\d{2}-\d{2}$/.test(iso) ? "UTC" : TZ, month: "short", day: "numeric" };
    if (time) { o.hour = "numeric"; o.minute = "2-digit"; }
    return d.toLocaleString("en-US", o);
  }
  function n0(v) { return v === null || v === undefined || v === "" || isNaN(v) ? "—" : Math.round(Number(v)).toLocaleString("en-US"); }
  function money(v) { return v === null || v === undefined || isNaN(v) ? "—" : "$" + Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function pct(a, b) { return b ? (100 * a / b).toFixed(1) + "%" : "—"; }
  function delta(cur, prev) {
    if (prev === null || prev === undefined || !isFinite(prev) || prev === 0 || cur === null) return null;
    var p = (cur - prev) / prev * 100; var s = el("span", p >= 0 ? "up" : "dn", (p >= 0 ? "▲" : "▼") + Math.abs(p).toFixed(0) + "%");
    s.title = "vs prior 7 days"; return s;
  }
  function isStale(asOf, hours) { if (!asOf) return true; var t = new Date(asOf).getTime(); return isNaN(t) || Date.now() - t > (hours || 36) * 3600e3; }

  // ---------- API ----------
  function getJSON(url) { return fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } }).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); }); }
  function post(path, body) {
    return fetch(path, { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-MFA-Hub": "1" }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || !j.ok) throw new Error(j.error || "HTTP " + r.status); return j; }); });
  }
  function status(t, err) { var s = $("hubStatus"); if (s) { s.textContent = t || ""; s.className = "hub-status" + (err ? " err" : ""); } }

  // ---------- comments / inline reply ----------
  var COMMENTS = {};
  function indexComments(list) { COMMENTS = {}; (list || []).forEach(function (c) { (COMMENTS[c.item_ref] = COMMENTS[c.item_ref] || []).push(c); }); }
  function lastNote(ref) { var l = COMMENTS[ref] || []; for (var i = 0; i < l.length; i++) if (l[i].agent_note) return l[i].agent_note; return null; }
  function commentBox(ref, kind, ph) {
    var box = el("div", "cbox"), ul = el("ul");
    (COMMENTS[ref] || []).slice().reverse().forEach(function (c) {
      var li = el("li"); add(li, pill(c.status), " " + fmtD(c.created_at, true) + " · " + c.body);
      if (c.agent_note) add(li, el("div", "note", "Agent: " + c.agent_note)); ul.appendChild(li);
    });
    var ta = el("textarea", "fld"); ta.maxLength = 4000; ta.rows = 2; ta.placeholder = ph || (kind === "question" ? "Ask Finance a question or leave a comment" : "Comment or instruction for the agents"); ta.setAttribute("aria-label", "Comment");
    var msg = el("span", ""), send = btn("btn-s", "Send", function () {
      var body = ta.value.trim(); if (!body) { msg.className = "err-msg"; msg.textContent = "Write something first."; return; }
      send.disabled = true; msg.className = "muted"; msg.textContent = "Sending…";
      post("/api/hub/comment", { page: PAGE, item_ref: ref, body: body, kind: kind || "comment" }).then(function (j) {
        (COMMENTS[ref] = COMMENTS[ref] || []).unshift(j.comment); var li = el("li"); add(li, pill("new"), " just now · " + body); ul.appendChild(li);
        ta.value = ""; msg.className = "ok-msg"; msg.textContent = "Sent ✓";
      }).catch(function (e) { msg.className = "err-msg"; msg.textContent = "Not sent (" + e.message + ")"; }).then(function () { send.disabled = false; });
    });
    add(box, ul.childNodes.length ? ul : null, ta, add(el("div", "row-acts"), send, msg));
    return box;
  }
  function replyCell(ref, colspan, o) {
    o = o || {};
    var n = (COMMENTS[ref] || []).length, td = el("td", "nw"), note = lastNote(ref), lab = o.label || "Reply";
    var b = btn("reply", n ? lab + " (" + n + ")" : lab);
    b.addEventListener("click", function () {
      var tr = td.parentNode, nx = tr.nextSibling;
      if (nx && nx.classList && nx.classList.contains("subrow")) { nx.parentNode.removeChild(nx); return; }
      var sub = el("tr", "subrow"), c = el("td"); c.colSpan = colspan; c.appendChild(commentBox(ref, o.kind)); sub.appendChild(c); tr.parentNode.insertBefore(sub, tr.nextSibling);
    });
    add(td, b);
    if (note) { if (o.marker) td.appendChild(el("span", "pill new", "💬 reply")); var nn = el("div", "note", "Agent: " + note); nn.title = note; td.appendChild(nn); }
    return td;
  }

  // ---------- one-click answers (chips + typed answer + 10 s undo) ----------
  function answerCell(kind, item) {
    var box = el("div", "ans");
    function render() {
      clear(box);
      if (item.status === "open") {
        var chips = el("div", "chips"), own = el("div", "own"), inp = el("input"); inp.type = "text"; inp.maxLength = 2000; inp.placeholder = "Your answer…"; inp.setAttribute("aria-label", "Your answer");
        (item.suggestions || []).forEach(function (s) {
          var fill = /_{3}/.test(s);
          chips.appendChild(btn("chip" + (fill ? " fill" : ""), fill ? s.replace(/\s*_{3,}\s*/, "…") : s, function () {
            if (fill) { inp.value = s.replace(/\s*_{3,}\s*/, " ").trimEnd() + " "; inp.focus(); return; }
            submit(s);
          }));
        });
        var go = btn("btn-s gold", "Send", function () { var v = inp.value.trim(); if (v) submit(v); else inp.focus(); });
        inp.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); go.click(); } });
        add(own, inp, go); add(box, chips.childNodes.length ? chips : null, own);
      } else {
        add(box, add(el("div"), pill(item.status), " ", el("b", null, item.answer || item.zain_answer || "")));
        if (item.answered_at) box.appendChild(el("div", "muted", "Answered " + fmtD(item.answered_at, true)));
        if (item.agent_note) box.appendChild(el("div", "note", "Agent: " + item.agent_note));
      }
    }
    function submit(answer) {
      Array.prototype.forEach.call(box.querySelectorAll("button,input"), function (x) { x.disabled = true; });
      post("/api/hub/answer", { kind: kind, id: item.id, answer: answer }).then(function (j) {
        item.status = j.item.status; item.answer = item.zain_answer = j.item.answer; item.answered_at = j.item.answered_at; item.agent_note = null;
        clear(box); var left = 10, msg = el("span", "ok-msg", "Sent ✓ " + answer), u = btn("btn-s line", "Undo (10)");
        var t = setInterval(function () { left--; u.textContent = "Undo (" + left + ")"; if (left <= 0) { clearInterval(t); render(); } }, 1000);
        u.addEventListener("click", function () {
          clearInterval(t); u.disabled = true;
          post("/api/hub/answer", { kind: kind, id: item.id, undo: true }).then(function () { item.status = "open"; item.answer = item.zain_answer = null; render(); })
            .catch(function (e) { render(); box.appendChild(el("div", "err-msg", "Undo failed: " + e.message)); });
        });
        add(box, msg, add(el("div", "row-acts"), u));
      }).catch(function (e) { render(); box.appendChild(el("div", "err-msg", "Not sent (" + e.message + ")")); });
    }
    render();
    return box;
  }

  // ---------- sortable, filterable table ----------
  // cfg: {cols:[{k,l,num,cls,get(r),cell(r)}], rows, ref(r), selects:[{k,l,get}], search:true, sort:{k,dir}, short, empty, total(rows)->[cells]}
  function table(host, cfg) {
    clear(host);
    var st = { k: (cfg.sort || {}).k, dir: (cfg.sort || {}).dir || "desc", q: "", sel: {} };
    var tb = el("div", "tb"), wrap = el("div", "tw" + (cfg.short ? " short" : "")), cnt = el("span", "cnt");
    if (cfg.search !== false) {
      var s = el("input"); s.type = "search"; s.placeholder = "Filter…"; s.setAttribute("aria-label", "Filter rows");
      s.addEventListener("input", function () { st.q = s.value.trim().toLowerCase(); draw(); }); tb.appendChild(s);
    }
    (cfg.selects || []).forEach(function (f) {
      var vals = {}; cfg.rows.forEach(function (r) { var v = f.get ? f.get(r) : r[f.k]; if (v !== null && v !== undefined && v !== "") vals[v] = 1; });
      var sel = el("select"); sel.setAttribute("aria-label", f.l); sel.appendChild(new Option(f.l + ": all", ""));
      Object.keys(vals).sort().forEach(function (v) { sel.appendChild(new Option(v, v)); });
      if (f.value) { sel.value = f.value; st.sel[f.l] = f.value; }
      sel.addEventListener("change", function () { st.sel[f.l] = sel.value; draw(); }); tb.appendChild(sel);
    });
    add(tb, cnt); add(host, tb, wrap);
    var colspan = cfg.cols.length + (cfg.ref ? 1 : 0);
    function val(c, r) { return c.get ? c.get(r) : r[c.k]; }
    function draw() {
      var rows = cfg.rows.filter(function (r) {
        for (var i = 0; i < (cfg.selects || []).length; i++) { var f = cfg.selects[i], want = st.sel[f.l]; if (want && String(f.get ? f.get(r) : r[f.k]) !== want) return false; }
        if (!st.q) return true;
        return cfg.cols.some(function (c) { var v = val(c, r); return v !== null && v !== undefined && String(v).toLowerCase().indexOf(st.q) >= 0; });
      });
      if (st.k) {
        var c = cfg.cols.filter(function (x) { return x.k === st.k; })[0];
        rows.sort(function (a, b) {
          var x = val(c, a), y = val(c, b), nx = x === null || x === undefined || x === "", ny = y === null || y === undefined || y === "";
          if (nx || ny) return nx === ny ? 0 : nx ? 1 : -1;
          var r = (typeof x === "number" && typeof y === "number") ? x - y : String(x).localeCompare(String(y));
          return st.dir === "asc" ? r : -r;
        });
      }
      cnt.textContent = rows.length + " of " + cfg.rows.length;
      var t = el("table", "dt"), th = el("thead"), hr = el("tr");
      cfg.cols.forEach(function (c) {
        var h = el("th", c.num ? "n" : "", c.l); if (st.k === c.k) h.setAttribute("data-dir", st.dir);
        h.addEventListener("click", function () { if (st.k === c.k) st.dir = st.dir === "asc" ? "desc" : "asc"; else { st.k = c.k; st.dir = c.num ? "desc" : "asc"; } draw(); });
        hr.appendChild(h);
      });
      if (cfg.ref) hr.appendChild(el("th", "", (cfg.reply && cfg.reply.head) || "Reply"));
      add(th, hr); var bd = el("tbody");
      rows.forEach(function (r) {
        var tr = el("tr");
        cfg.cols.forEach(function (c) {
          var td = el("td", (c.num ? "n " : "") + (c.cls || "")), v = c.cell ? c.cell(r) : val(c, r);
          if (v instanceof Node) td.appendChild(v); else td.textContent = v === null || v === undefined ? "" : (c.num && typeof v === "number" ? n0(v) : String(v));
          td.setAttribute("data-l", c.l); tr.appendChild(td);
        });
        if (cfg.ref) tr.appendChild(replyCell(cfg.ref(r), colspan, cfg.reply ? { label: cfg.reply.label, kind: cfg.reply.kind, marker: cfg.reply.marker && cfg.reply.marker(r) } : null));
        bd.appendChild(tr);
      });
      if (cfg.total && rows.length) { var tt = el("tr", "total"); cfg.total(rows).forEach(function (x, i) { var td = el("td", cfg.cols[i] && cfg.cols[i].num ? "n" : "", x); tt.appendChild(td); }); if (cfg.ref) tt.appendChild(el("td")); bd.appendChild(tt); }
      add(t, th, bd); clear(wrap).appendChild(t);
      if (!rows.length) wrap.appendChild(el("div", "empty", cfg.empty || "Nothing here yet."));
    }
    draw();
  }

  // ---------- charts (hand-made SVG) ----------
  function hbars(host, data, o) {
    o = o || {}; clear(host);
    if (!data.length) { host.appendChild(el("div", "empty", o.empty || "No data yet.")); return; }
    var W = 560, lw = o.labelW || 150, rh = 20, H = data.length * rh + 6, max = Math.max.apply(null, data.map(function (d) { return d.value || 0; })) || 1;
    var s = svg("svg", { viewBox: "0 0 " + W + " " + H, class: "ch", role: "img", "aria-label": o.title || "bar chart" });
    data.forEach(function (d, i) {
      var y = i * rh + 3, w = Math.max(1, (W - lw - 70) * (d.value || 0) / max);
      var lab = svg("text", { x: lw - 6, y: y + 13, "text-anchor": "end" }); lab.textContent = d.label.length > 24 ? d.label.slice(0, 23) + "…" : d.label;
      var r = svg("rect", { x: lw, y: y + 2, width: w, height: rh - 6, rx: 2, fill: d.color || o.color || "#10233F" });
      var tt = svg("title", {}); tt.textContent = d.label + ": " + (d.fmt || n0)(d.value); r.appendChild(tt);
      var v = svg("text", { x: lw + w + 5, y: y + 13, class: "v" }); v.textContent = (d.fmt || o.fmt || n0)(d.value);
      if (d.href) { var a = svg("a", { href: d.href, class: "lnk" }); add(a, svg("rect", { x: 0, y: y, width: W, height: rh, fill: "transparent" }), lab, r, v); s.appendChild(a); } else add(s, lab, r, v);
    });
    host.appendChild(s);
  }
  function pairBars(host, data, names, fmts) {
    clear(host);
    if (!data.length) { host.appendChild(el("div", "empty", "No paid data in the last 7 days.")); return; }
    var lg = el("div", "legend"); [0, 1].forEach(function (i) { var it = el("span"), sw = el("i"); sw.style.background = i ? "#B08D3F" : "#10233F"; add(it, sw, names[i]); lg.appendChild(it); });
    var W = 560, lw = 110, gh = 34, H = data.length * gh + 4, ma = Math.max.apply(null, data.map(function (d) { return d.a || 0; })) || 1, mb = Math.max.apply(null, data.map(function (d) { return d.b || 0; })) || 1;
    var s = svg("svg", { viewBox: "0 0 " + W + " " + H, class: "ch", role: "img", "aria-label": names.join(" vs ") });
    data.forEach(function (d, i) {
      var g = d.href ? svg("a", { href: d.href, class: "lnk" }) : s; if (g !== s) { s.appendChild(g); g.appendChild(svg("rect", { x: 0, y: i * gh + 2, width: W, height: gh - 2, fill: "transparent" })); }
      var y = i * gh + 3, lab = svg("text", { x: lw - 6, y: y + 18, "text-anchor": "end" }); lab.textContent = d.label; g.appendChild(lab);
      [[d.a, ma, "#10233F", fmts[0]], [d.b, mb, "#B08D3F", fmts[1]]].forEach(function (p, j) {
        var w = Math.max(1, (W - lw - 80) * (p[0] || 0) / p[1]), yy = y + j * 13 + 2;
        var r = svg("rect", { x: lw, y: yy, width: w, height: 11, rx: 2, fill: p[2] }), v = svg("text", { x: lw + w + 5, y: yy + 10, class: "v" });
        v.textContent = p[3](p[0]); add(g, r, v);
      });
    });
    add(host, lg, s);
  }
  // stacked columns: days [ymd], series [{name, color, vals:{ymd:value}}]
  function columns(host, days, series, o) {
    o = o || {}; clear(host);
    var totals = days.map(function (d) { return series.reduce(function (t, s) { return t + (s.vals[d] || 0); }, 0); });
    if (!totals.some(function (x) { return x > 0; })) { host.appendChild(el("div", "empty", o.empty || "No data in this window yet.")); return; }
    if (series.length > 1) { var lg = el("div", "legend"); series.forEach(function (s) { var it = el("span"), sw = el("i"); sw.style.background = s.color; add(it, sw, s.name); lg.appendChild(it); }); host.appendChild(lg); }
    var W = 560, H = o.h || 170, pl = 34, pb = 18, pt = 8, max = Math.max.apply(null, totals) || 1, cw = (W - pl - 4) / days.length;
    var s = svg("svg", { viewBox: "0 0 " + W + " " + H, class: "ch", role: "img", "aria-label": o.title || "column chart" });
    (max < 4 ? [0, 1] : [0, 0.5, 1]).forEach(function (f) {
      var y = pt + (H - pt - pb) * (1 - f); add(s, svg("line", { x1: pl, x2: W, y1: y, y2: y, stroke: "#e3e0d7" }));
      var t = svg("text", { x: pl - 4, y: y + 4, "text-anchor": "end" }); t.textContent = (o.fmt || n0)(max * f); s.appendChild(t);
    });
    days.forEach(function (d, i) {
      var x = pl + i * cw + cw * 0.15, w = cw * 0.7, y0 = H - pb;
      series.forEach(function (se) {
        var v = se.vals[d] || 0; if (!v) return; var h = (H - pt - pb) * v / max; y0 -= h;
        var r = svg("rect", { x: x, y: y0, width: w, height: h, fill: se.color }), tt = svg("title", {}); tt.textContent = fmtD(d) + " · " + se.name + ": " + (o.fmt || n0)(v); r.appendChild(tt);
        var hr = o.href && o.href(d, se.name); if (hr) { var a = svg("a", { href: hr, class: "lnk" }); a.appendChild(r); s.appendChild(a); } else s.appendChild(r);
      });
      if (days.length <= 16 || i % 2 === 0) { var lab = svg("text", { x: x + w / 2, y: H - 5, "text-anchor": "middle" }); lab.textContent = d.slice(5).replace("-", "/"); s.appendChild(lab); }
    });
    host.appendChild(s);
  }
  function spark(vals) {
    var W = 120, H = 18, max = Math.max.apply(null, vals.concat([1])), n = vals.length, s = svg("svg", { viewBox: "0 0 " + W + " " + H, class: "spark", "aria-hidden": "true", preserveAspectRatio: "none" });
    var pts = vals.map(function (v, i) { return (n > 1 ? i * W / (n - 1) : 0).toFixed(1) + "," + (H - 2 - (H - 4) * v / max).toFixed(1); }).join(" ");
    add(s, svg("polyline", { points: pts, fill: "none", stroke: "#B08D3F", "stroke-width": 1.5 })); return s;
  }
  function lastDays(n, end) { var e = end || today(), out = []; for (var i = n - 1; i >= 0; i--) out.push(addDays(e, -i)); return out; }

  // ---------- ads math ----------
  function adsModel(rows) {
    var t = today(), from7 = addDays(t, -6), pFrom = addDays(t, -13), pTo = addDays(t, -7), P = {};
    rows.forEach(function (r) {
      var p = P[r.platform] = P[r.platform] || { name: r.platform, paid: /Ads$/.test(r.platform), daily: [], win: [], latest: null };
      if (r.window_days === 1) { p.daily.push(r); if (!p.latest || r.date > p.latest) p.latest = r.date; } else p.win.push(r);
    });
    function sum(list) { return list.reduce(function (s, r) { s.i += r.impressions || 0; s.c += r.clicks || 0; s.s += r.spend || 0; s.v += r.conversions || 0; s.n++; return s; }, { i: 0, c: 0, s: 0, v: 0, n: 0 }); }
    function win(p, endFrom, endTo) { var w = p.win.filter(function (r) { return r.window_days === 7 && r.date >= endFrom && r.date <= endTo; }).sort(function (a, b) { return b.date.localeCompare(a.date); })[0]; return w ? sum([w]) : null; }
    Object.keys(P).forEach(function (k) {
      var p = P[k];
      p.today = sum(p.daily.filter(function (r) { return r.date === t; }));
      var d7 = p.daily.filter(function (r) { return r.date >= from7 && r.date <= t; }), dp = p.daily.filter(function (r) { return r.date >= pFrom && r.date <= pTo; });
      p.s7 = d7.length ? sum(d7) : win(p, addDays(t, -2), t); p.note = d7.length ? "" : (p.s7 ? "7-day total from the platform" : "");
      p.p7 = dp.length >= 5 ? sum(dp) : win(p, addDays(pTo, -2), pTo); // prior period counts only with full coverage
      var w30 = p.win.filter(function (r) { return r.window_days === 30; }).sort(function (a, b) { return b.date.localeCompare(a.date); })[0];
      if (!p.s7 && w30) { p.s30 = sum([w30]); p.note = "30-day total only"; p.latest = p.latest || w30.date; }
      if (!p.latest && p.win.length) p.latest = p.win.map(function (r) { return r.date; }).sort().pop();
    });
    return P;
  }

  // ---------- KPI tile ----------
  function kpi(host, label, value, sub, o) {
    o = o || {}; var u = o.ext ? HL.safeUrl(o.ext.url) : null, k = el(o.href || u ? "a" : "div", "kpi" + (o.stale ? " stale" : "") + (o.bad ? " bad" : "") + (u && !o.href ? " x" : ""));
    if (o.href) k.href = o.href; else if (u) { k.href = u; k.target = "_blank"; k.rel = "noopener noreferrer"; }
    var v = el("div", "v"); add(v, value instanceof Node ? value : String(value)); if (o.delta) { v.appendChild(document.createTextNode(" ")); v.appendChild(o.delta); }
    var s = el("span", "s"); add(s, sub || ""); if (o.stale) s.appendChild(el("span", "stale-tag", o.asOf ? "as of " + fmtD(o.asOf) : "stale"));
    k.title = (o.title || label) + (o.asOf ? " · as of " + fmtD(o.asOf, true) : "") + (o.href ? " · click for the detail" : u ? " · opens " + o.ext.label : "");
    add(k, el("span", "l", label), v, s); if (o.spark) k.appendChild(spark(o.spark)); host.appendChild(k);
  }
  function fit(w) {
    function go() { if (window.innerWidth < 700) { w.style.maxHeight = ""; return; } var top = w.getBoundingClientRect().top + window.scrollY; w.style.maxHeight = Math.max(320, window.innerHeight - top - 12) + "px"; }
    go(); if (!fit.on) { fit.on = true; window.addEventListener("resize", function () { var c = $("cal"); if (c) fit(c); }); }
  }
  function kmap(list) { var m = {}; (list || []).forEach(function (k) { m[k.key] = k; }); return m; }

  // ---------- shared tables ----------
  function needsRows(d) {
    var rows = (d.needs || []).map(function (n) { return { kind: "need", id: n.id, src: n.source, agent: n.agent || "", title: n.title, detail: n.detail, item: n, ts: n.created_at, status: n.status }; });
    (d.financeOpen || d.finance || []).forEach(function (f) { rows.push({ kind: "finance", id: f.id, src: "finance", agent: "Finance", title: f.question, detail: f.suggested_answer ? "Suggested: " + f.suggested_answer : "", item: f, ts: f.created_at, status: f.status }); });
    return rows;
  }
  function needsTable(host, d, o) {
    var rows = needsRows(d);
    table(host, {
      rows: rows, short: o && o.short, sort: { k: "o", dir: "asc" },
      selects: [{ l: "Source", k: "src" }, { l: "Status", k: "status", value: "open" }],
      cols: [
        { k: "o", l: "#", num: true, get: function (r) { return (r.status === "open" ? 0 : 1) * 1e6 + (r.kind === "finance" ? 1e5 : 0) + rows.indexOf(r); }, cell: function (r) { return String(rows.indexOf(r) + 1); } },
        { k: "src", l: "From", cls: "nw", cell: function (r) { var ref = r.item && r.item.ref, m = ref && /^agent:(.+)$/.exec(ref);
          return hl(r.agent || r.src, r.kind === "finance" ? HL.route("finance", { q: r.id }) : m ? HL.route("board", { agent: m[1] }) : r.agent ? HL.route("board", { agent: r.agent }) : ref ? HL.refHref("home", ref) : HL.route("board")); } },
        { k: "title", l: "Question / approval", cls: "w", cell: function (r) { var w = el("div"); add(w, clip(r.title)); if (r.detail) w.appendChild(el("div", "muted", r.detail)); return w; } },
        { k: "status", l: "Answer", cls: "ww", cell: function (r) { return answerCell(r.kind, r.item); } }
      ],
      ref: function (r) { return r.kind === "finance" ? r.id : "need:" + r.id; },
      empty: "Nothing is waiting on you."
    });
  }
  function logTable(host, rows, agentSel) {
    table(host, {
      rows: rows, short: true, sort: { k: "ts", dir: "desc" }, selects: agentSel === false ? [] : [{ l: "Agent", k: "agent" }],
      cols: [
        { k: "ts", l: "Time (ET)", cls: "nw", cell: function (r) { return fmtD(r.ts, true); } },
        { k: "agent", l: "Agent", cls: "nw", cell: function (r) { return hl(r.agent, HL.route("board", { agent: r.agent })); } }, { k: "action", l: "Action", cls: "nw" },
        { k: "detail", l: "Detail", cls: "w", cell: function (r) { var w = el("div"); add(w, clip(r.detail || "")); var a = link(r.link, "link"); if (a) w.appendChild(a); return w; } }
      ], empty: "No log lines yet."
    });
  }
  var POLL = null;
  function pollLog(host, filterSel) {
    function want() { return filterSel ? (H.agent || "") : ""; }
    function sync() { if (!filterSel) return; var w = want(); if (w && ![].some.call(filterSel.options, function (o) { return o.value === w; })) filterSel.appendChild(new Option(w, w)); filterSel.value = w; }
    function go() {
      var w = want(), a = w ? "&agent=" + encodeURIComponent(w) : "";
      getJSON("/api/hub/log?limit=100" + a).then(function (j) {
        if (filterSel && filterSel.options.length <= 2) (j.agents || []).forEach(function (x) { if (![].some.call(filterSel.options, function (o) { return o.value === x.agent; })) filterSel.appendChild(new Option(x.agent + " (" + x.n + ")", x.agent)); });
        sync(); logTable(host, j.rows || [], false); var u = $("logUpd"); if (u) u.textContent = "updated " + new Date().toLocaleTimeString("en-US", { timeZone: TZ, hour: "numeric", minute: "2-digit" });
      }).catch(function (e) { var u = $("logUpd"); if (u) u.textContent = "log refresh failed (" + e.message + ")"; });
    }
    sync(); go();
    if (!POLL) { POLL = setInterval(go, 60000); if (filterSel) filterSel.addEventListener("change", function () { setHash(filterSel.value ? { agent: filterSel.value } : {}); }); }
  }

  // ---------- detail panel (drill-down) ----------
  function detailHost() {
    var h = $("detail"); if (h) return h;
    h = el("section", "pn det"); h.id = "detail"; var m = document.querySelector(".hub-main"), k = $("kpis");
    if (k && k.parentNode === m) m.insertBefore(h, k.nextSibling); else m.insertBefore(h, m.firstChild); return h;
  }
  function hideDetail() { var h = $("detail"); if (h) { clear(h); h.hidden = true; } }
  // o: {title, sub, close: hash params after closing, fields: [[label, value|Node]], links: [Node], table: cfg, ref, refKind}
  function showDetail(o) {
    var h = clear(detailHost()); h.hidden = false;
    var hd = el("div", "pn-h"), acts = el("div", "acts");
    (o.links || []).forEach(function (a) { if (a) acts.appendChild(a); });
    acts.appendChild(btn("btn-s line", "Close ✕", function () { setHash(o.close || {}); }));
    add(hd, add(el("div"), el("h2", null, o.title), o.sub ? el("span", "sub", " " + o.sub) : null), acts); h.appendChild(hd);
    if (o.fields && o.fields.length) {
      var f = el("div", "fields"); o.fields.forEach(function (x) { if (x[1] === null || x[1] === undefined || x[1] === "") return; var c = el("div", "f"); add(c, el("span", "l", x[0]), x[1] instanceof Node ? x[1] : el("span", "v", String(x[1]))); f.appendChild(c); });
      h.appendChild(f);
    }
    if (o.table) { var tw = el("div"); h.appendChild(tw); table(tw, o.table); }
    if (o.ref) { var cb = el("div", "pn-b"); cb.appendChild(commentBox(o.ref, o.refKind || "comment", "Comment or ask about this")); h.appendChild(cb); }
    if (o.scroll !== false) try { h.scrollIntoView({ block: "nearest" }); } catch (e) { /* old browsers */ }
  }
  function docTag(name, short) { var d = HL.doc(name, LINKS); if (!d) return null; var s = el("span", "doc", short ? d.split("/").pop() : "Doc: " + d); s.title = "Project doc " + d + " (open it in the MFA project)"; return s; }
  // Review cell: hub detail + platform + project doc
  function reviewCell(hubHref, platformLk, docName) {
    var w = el("div", "rev"); add(w, hl("Review", hubHref), ext(platformLk, "Open"), docName ? docTag(docName, true) : null); return w;
  }
  function filterChip(text, clearHref) { var w = el("div", "fbar"); add(w, el("span", "fchip", text), hl("Show all", clearHref)); return w; }

  // ---------- pages ----------
  var R = {};
  R.home = function (d) {
    var K = kmap(d.kpis), t = today(), strip = clear($("kpis")), A = function (p) { return HL.route("ads", p); };
    var L = d.leads || [], ld = function (n) { var f = addDays(t, -(n - 1)); return L.filter(function (x) { return ymdET(x.received_at) >= f; }).length; };
    kpi(strip, "Leads today / 7d / 30d", L.filter(function (x) { return ymdET(x.received_at) === t; }).length + " / " + ld(7) + " / " + ld(30), "website forms (backup log)", { href: HL.route("leads", { range: "30d" }), spark: lastDays(14).map(function (dd) { return L.filter(function (x) { return ymdET(x.received_at) === dd; }).length; }) });
    var waiting = L.filter(function (x) { return x.status === "new" || x.status === "drafted"; }).length;
    kpi(strip, "Lead replies", waiting ? waiting + " waiting" : "all answered", L.filter(function (x) { return x.status === "sent"; }).length + " sent", { bad: waiting > 0, href: HL.route("leads", waiting ? { status: "waiting" } : {}) });
    var P = adsModel(d.ads || []), paid = Object.keys(P).filter(function (k) { return P[k].paid; }), org = Object.keys(P).filter(function (k) { return !P[k].paid; });
    var d14 = lastDays(14), dser = function (keys, m) { return d14.map(function (dd) { return keys.reduce(function (t2, k) { return t2 + P[k].daily.filter(function (r) { return r.date === dd; }).reduce(function (a, r) { return a + (r[m] || 0); }, 0); }, 0); }); };
    var spT = 0, sp7 = 0, i7 = 0, c7 = 0, pi = 0, pc = 0, ps = 0, parts = [];
    var pFull = true;
    paid.forEach(function (k) { var p = P[k]; spT += p.today.s; if (p.s7) { sp7 += p.s7.s; i7 += p.s7.i; c7 += p.s7.c; if (p.s7.s) parts.push(k.replace(" Ads", "") + " " + money(p.s7.s)); if (!p.p7) pFull = false; } if (p.p7) { pi += p.p7.i; pc += p.p7.c; ps += p.p7.s; } });
    if (!pFull) { pi = pc = ps = null; }
    kpi(strip, "Ad spend today", money(spT), paid.filter(function (k) { return P[k].today.s; }).map(function (k) { return k.replace(" Ads", "") + " " + money(P[k].today.s); }).join(" · ") || "no spend logged today", { href: A({ type: "Paid", range: "today" }) });
    kpi(strip, "Ad spend 7d", money(sp7), parts.join(" · "), { delta: delta(sp7, ps), spark: dser(paid, "spend"), href: A({ type: "Paid", range: "7d" }) });
    kpi(strip, "Paid impressions 7d", n0(i7), "all ad platforms", { delta: delta(i7, pi), spark: dser(paid, "impressions"), href: A({ type: "Paid", range: "7d" }) });
    kpi(strip, "Paid clicks 7d", n0(c7), "CTR " + pct(c7, i7), { delta: delta(c7, pc), spark: dser(paid, "clicks"), href: A({ type: "Paid", range: "7d" }) });
    kpi(strip, "CPC 7d", c7 ? money(sp7 / c7) : "—", pc ? "prior " + money(ps / pc) : "no full prior week yet", { delta: c7 && pc ? delta(sp7 / c7, ps / pc) : null, href: A({ type: "Paid", range: "7d" }) });
    var ov = 0, op = 0, oFull = true, latestOrg = null; org.forEach(function (k) { if (P[k].s7) { ov += P[k].s7.i; if (!P[k].p7) oFull = false; } if (P[k].p7) op += P[k].p7.i; if (!latestOrg || P[k].latest > latestOrg) latestOrg = P[k].latest; }); if (!oFull) op = null;
    kpi(strip, "Organic views 7d", n0(ov), org.length + " platforms" + (op === null ? " · no full prior week" : ""), { delta: delta(ov, op), stale: latestOrg && latestOrg < addDays(t, -1), asOf: latestOrg, spark: dser(org, "impressions"), href: A({ type: "Organic", range: "7d" }) });
    var KL = { newsletter_active: "Subscribers", fiverr_orders_30d: "Fiverr", fiverr_sales_30d: "Fiverr", etsy_orders_mtd: "Etsy", gumroad_orders_mtd: "Gumroad", upwork_orders_mtd: "Upwork", revenue_mtd: "QuickBooks" };
    [["newsletter_active", "Subscribers"], ["fiverr_orders_30d", "Fiverr orders 30d"], ["fiverr_sales_30d", "Fiverr sales 30d"], ["etsy_orders_mtd", "Etsy orders MTD"], ["gumroad_orders_mtd", "Gumroad orders MTD"], ["upwork_orders_mtd", "Upwork MTD"], ["revenue_mtd", "Revenue MTD"]].forEach(function (x) {
      var k = K[x[0]]; if (!k) return; kpi(strip, x[1], k.value === null ? "—" : (k.unit === "$" ? money(k.value) : n0(k.value)), k.note || k.source || "", { stale: isStale(k.as_of, 36), asOf: k.as_of, title: k.label, ext: HL.platformLink(KL[x[0]], LINKS) });
    });
    var fo = (d.financeOpen || []).filter(function (f) { return f.status === "open"; }).length;
    kpi(strip, "Finance questions", fo + " open", (d.financeOpen || []).length - fo + " answered, waiting for Finance", { bad: fo > 0, href: HL.route("finance", { status: "open" }) });
    var bl = (d.agents || []).filter(function (a) { return a.status === "Blocked"; });
    kpi(strip, "Blocked agents", String(bl.length), bl.map(function (a) { return a.agent; }).join(", ") || "none", { bad: bl.length > 0, href: HL.route("board", bl.length ? { status: "Blocked" } : {}) });
    kpi(strip, "Needs you", String(needsRows(d).filter(function (r) { return r.status === "open"; }).length), "questions and approvals below", { href: "#needs" });
    // charts: every bar opens its rows
    pairBars($("chSpend"), paid.filter(function (k) { return P[k].s7 && (P[k].s7.s || P[k].s7.c); }).map(function (k) { return { label: k.replace(" Ads", ""), a: P[k].s7.s, b: P[k].s7.c, href: A({ platform: HL.slug(k), range: "7d" }) }; }), ["Spend 7d", "Clicks 7d"], [money, n0]);
    hbars($("chImpr"), Object.keys(P).filter(function (k) { return P[k].s7 && P[k].s7.i; }).map(function (k) { return { label: k, value: P[k].s7.i, color: COLORS[k], href: A({ platform: HL.slug(k), range: "7d" }) }; }).sort(function (a, b) { return b.value - a.value; }), { labelW: 120 });
    hbars($("chTop"), (d.topPosts || []).map(function (p) { return { label: p.title + " · " + p.platform.replace("Instagram+Facebook", "IG/FB"), value: p.impressions, color: COLORS[p.platform] || "#B08D3F", href: HL.route("calendar", { item: p.id }) }; }), { labelW: 230, empty: "No post metrics yet." });
    var days = lastDays(30), lv = {}; L.forEach(function (x) { var k = ymdET(x.received_at); lv[k] = (lv[k] || 0) + 1; });
    columns($("chLeads"), days, [{ name: "Leads", color: "#B08D3F", vals: lv }], { h: 140, empty: "No leads in the last 30 days.", href: function (dd) { return lv[dd] ? HL.route("leads", { date: dd }) : null; } });
    needsTable($("needs"), d, { short: false });
    logTable($("log"), d.log || [], true); pollLog($("log"));
    tasksForm($("reqForm"));
  };

  R.board = function (d) {
    var ag = d.agents || [];
    table($("agents"), {
      rows: ag, sort: { k: "st", dir: "asc" }, selects: [{ l: "Status", k: "status", value: H.status || "" }],
      cols: [
        { k: "agent", l: "Agent", cls: "nw", cell: function (a) { return add(el("div"), hl(a.agent, HL.route("board", { agent: a.agent }), "b"), el("div", "muted", a.title || "")); } },
        { k: "st", l: "Status", get: function (a) { return { Blocked: 0, Working: 1, Scheduled: 2, Idle: 3 }[a.status] + ""; }, cell: function (a) { var w = el("div"); add(w, pill(a.status)); if (isStale(a.data.updated_at || a.at, 48)) w.appendChild(el("span", "stale-tag", "no update 48h")); return w; } },
        { k: "at", l: "Last run", cls: "nw", cell: function (a) { return hl(fmtD(a.at, true), HL.route("log", { agent: a.agent })); } },
        { k: "res", l: "Last result", cls: "w", get: function (a) { return a.data.last_result || ""; }, cell: function (a) { return clip(a.data.last_result || ""); } },
        { k: "next", l: "Next run", cls: "nw", get: function (a) { return a.data.next_run || ""; }, cell: function (a) { return fmtD(a.data.next_run, true); } },
        { k: "need", l: "Needs you / blocked by", cls: "w", get: function (a) { return a.data.needs_zain || ""; }, cell: function (a) { return clip(a.data.needs_zain || ""); } },
        { k: "sched", l: "Schedule", cls: "ww", get: function (a) { return a.data.schedule || ""; } },
        { k: "rev", l: "Review", cls: "nw", get: function () { return ""; }, cell: function (a) { return reviewCell(HL.route("board", { agent: a.agent }), HL.agentLink(a.agent, LINKS), a.agent); } }
      ], ref: function (a) { return a.id; }
    });
    needsTable($("needs"), { needs: d.needs || [] });
    var ideas = d.ideas || [];
    table($("ideas"), {
      rows: ideas, sort: { k: "at", dir: "desc" }, selects: [{ l: "Status", k: "status" }, { l: "Owner", get: function (i) { return i.data.owner || ""; } }],
      cols: [
        { k: "at", l: "Added", cls: "nw", cell: function (i) { return fmtD(i.at); } },
        { k: "status", l: "Status", cell: function (i) { return pill(i.status); } },
        { k: "title", l: "Idea", cls: "w", cell: function (i) { return clip(i.title); } },
        { k: "owner", l: "Owner", get: function (i) { return i.data.owner || ""; }, cell: function (i) { return i.data.owner ? hl(i.data.owner, HL.route("board", { agent: i.data.owner })) : ""; } },
        { k: "prog", l: "Progress", cls: "ww", get: function (i) { return (i.data.progress || "") + (i.data.progress_note ? ": " + i.data.progress_note : ""); }, cell: function (i) { return clip((i.data.progress ? i.data.progress.replace(/_/g, " ") + ": " : "") + (i.data.progress_note || "")); } },
        { k: "up", l: "Upside", cls: "ww", get: function (i) { return i.data.upside || ""; }, cell: function (i) { return clip(i.data.upside || ""); } }
      ], ref: function (i) { return i.id; }, empty: "No ideas synced yet. Agents add them with tools/hub_sync.md."
    });
    table($("activity"), {
      rows: d.activity || [], short: true, sort: { k: "at", dir: "desc" }, selects: [{ l: "Agent", k: "agent" }],
      cols: [{ k: "at", l: "Time", cls: "nw", cell: function (a) { return fmtD(a.at, true); } }, { k: "agent", l: "Agent", cls: "nw", cell: function (a) { return a.agent ? hl(a.agent, HL.route("board", { agent: a.agent })) : ""; } }, { k: "title", l: "What happened", cls: "w" }],
      ref: function (a) { return a.id; }
    });
    // agent drill-down: card, its log lines and activity, platform + doc
    var a = H.agent && ag.filter(function (x) { return x.agent === H.agent; })[0];
    if (!H.agent) { hideDetail(); return; }
    var runs = (d.log || []).filter(function (r) { return r.agent === H.agent; }).map(function (r) { return { ts: r.ts, what: r.action + ": " + (r.detail || ""), link: r.link }; })
      .concat((d.activity || []).filter(function (x) { return x.agent === H.agent; }).map(function (x) { return { ts: x.at, what: x.title || "", link: null }; }));
    showDetail({
      title: H.agent + (a ? " · " + (a.title || "") : ""), sub: a ? a.status : "not on the Agent Board", close: H.status ? { status: H.status } : {},
      links: [hl("All log lines", HL.route("log", { agent: H.agent })), ext(HL.agentLink(H.agent, LINKS), "Open " + ((HL.agentLink(H.agent, LINKS) || {}).label || "")), docTag(H.agent)],
      fields: a ? [["Status", a.status], ["Last run", fmtD(a.at, true)], ["Next run", fmtD(a.data.next_run, true)], ["Schedule", a.data.schedule], ["Doing now", a.data.now], ["Last result", a.data.last_result], ["Next steps", a.data.next_steps], ["Needs you", a.data.needs_zain]] : [],
      table: { rows: runs, short: true, search: true, sort: { k: "ts", dir: "desc" }, cols: [{ k: "ts", l: "When (ET)", cls: "nw", cell: function (r) { return fmtD(r.ts, true); } }, { k: "what", l: "Run / activity", cls: "w", cell: function (r) { var w = el("div"); add(w, clip(r.what)); var l = link(r.link, "link"); if (l) w.appendChild(l); return w; } }], empty: "No runs logged for this agent in the newest 100 log lines." },
      ref: a ? a.id : "agent:" + H.agent
    });
  };

  // ----- Calendar: one row per piece of content, one cell group per platform (matrix) -----
  var PCOLS = [["LI", "LinkedIn"], ["IG/FB", "Instagram + Facebook (Meta shows the Facebook copy's numbers)"], ["TT", "TikTok"], ["YT", "YouTube Shorts"], ["Pin", "Pinterest"], ["Blog", "Blog"], ["NL", "Newsletter"]];
  function pcol(p) { return { LinkedIn: "LI", "Instagram+Facebook": "IG/FB", Instagram: "IG/FB", Facebook: "IG/FB", TikTok: "TT", "YouTube Shorts": "YT", Pinterest: "Pin", Blog: "Blog", Newsletter: "NL" }[p] || p; }
  var STOP = { a: 1, an: 1, the: 1, for: 1, of: 1, in: 1, to: 1, and: 1, your: 1, you: 1, is: 1, on: 1, mfa: 1, insights: 1, reel: 1, image: 1, blog: 1, rerun: 1, re: 1, run: 1, post: 1, caption: 1, copy: 1, second: 1, what: 1, do: 1, does: 1, my: 1, it: 1, s: 1 };
  function ckey(i) {
    var t = String(i.title || "").toLowerCase();
    if (/not logged|caption not shown|^pin [a-z]\d+$/.test(t)) return "solo:" + i.id;
    var w = t.replace(/\(.*?\)/g, " ").replace(/^pin [a-z]\d+:\s*/, "").replace(/[^a-z0-9$]+/g, " ").split(" ").filter(function (x) { return x && !STOP[x]; });
    return w.length ? w.slice(0, 4).join(" ") : "solo:" + i.id;
  }
  var TOPICS = [["1099", /1099|contractor|w-9|w-8/], ["LLC / S corp", /llc|s corp|2553|1120|1065|annual report/], ["Artists & creators", /artist|art |commission|paint|creator/], ["Year-end", /dec 31|year-end|year end|before dec/], ["Estimates & deadlines", /estimate|quarterly|deadline|late|penalt|oct/], ["Students & visas", /opt|f-1|student|campus/], ["Drivers & mileage", /mileage|miles|driver|rideshare/], ["Deductions & credits", /deduct|write-off|credit|charit|salt|overtime|senior|gift/], ["AI & tools", /ai |chatgpt|calculator|tracker|bookkeeping app/]];
  function topic(t) { t = String(t || "").toLowerCase() + " "; for (var i = 0; i < TOPICS.length; i++) if (TOPICS[i][1].test(t)) return TOPICS[i][0]; return "Other"; }
  function cstat(i, t) { return i.status === "published" ? "published" : i.status === "missed" ? "missed" : (i.date < t ? "missed?" : "scheduled"); }
  var CS = { from: null, to: null, status: "all", plat: "", topic: "", q: "", sort: "date", dir: "desc", open: {} };
  var YMD = /^\d{4}-\d{2}-\d{2}$/;
  // calendar slicers live in the URL hash (back button + shareable links)
  function csFromHash(t) {
    CS.from = YMD.test(H.from || "") ? H.from : addDays(t, -21); CS.to = YMD.test(H.to || "") ? H.to : addDays(t, 14);
    CS.status = ["published", "scheduled", "missed"].indexOf(H.status) >= 0 ? H.status : "all";
    CS.plat = PCOLS.some(function (p) { return p[0] === H.plat; }) ? H.plat : "";
    CS.topic = H.topic || ""; CS.q = (H.q || "").toLowerCase();
    CS.sort = ["date", "title", "topic", "tot"].concat(PCOLS.map(function (p) { return p[0]; })).indexOf(H.sort) >= 0 ? H.sort : "date"; CS.dir = H.dir === "asc" ? "asc" : "desc";
  }
  function calSet(ch) { var n = merge(H, ch); delete n.item; if (ch.item) n.item = ch.item; setHash(n); }
  R.calendar = function (d) {
    var items = d.calendar || [], t = today();
    csFromHash(t);
    var groups = {};
    items.forEach(function (i) { var k = ckey(i), g = groups[k] = groups[k] || { key: k, items: [], cells: {} }; g.items.push(i); });
    Object.keys(groups).forEach(function (k) {
      var g = groups[k]; g.items.sort(function (a, b) { return (a.date + (a.time || "")).localeCompare(b.date + (b.time || "")); });
      var main = g.items.filter(function (i) { return !/not logged|caption not shown/i.test(i.title || ""); })[0] || g.items[0];
      g.date = g.items[0].date; g.title = main.title; g.topic = topic(g.items.map(function (i) { return i.title; }).join(" "));
      g.items.forEach(function (i) { var c = pcol(i.platform); (g.cells[c] = g.cells[c] || []).push(i); });
    });
    function inSlice(i) {
      if (i.date < CS.from || i.date > CS.to) return false;
      if (CS.plat && pcol(i.platform) !== CS.plat) return false;
      var s = cstat(i, t); if (CS.status !== "all" && s.replace("?", "") !== CS.status) return false;
      return true;
    }
    var rows = Object.keys(groups).map(function (k) {
      var g = groups[k], its = g.items.filter(inSlice); if (!its.length) return null;
      if (CS.topic && g.topic !== CS.topic) return null;
      if (CS.q && (g.title + " " + its.map(function (i) { return i.title + " " + i.platform; }).join(" ")).toLowerCase().indexOf(CS.q) < 0) return null;
      var r = { g: g, its: its, date: its[0].date, title: g.title, topic: g.topic, tot: { i: 0, c: 0, e: 0 }, by: {} };
      its.forEach(function (i) { var c = pcol(i.platform), b = r.by[c] = r.by[c] || { i: null, c: null, e: null, items: [] }; b.items.push(i);
        ["impressions", "clicks", "engagements"].forEach(function (m, j) { var kk = "ice"[j]; if (i[m] !== null && i[m] !== undefined) { b[kk] = (b[kk] || 0) + i[m]; r.tot[kk] += i[m]; } }); });
      return r;
    }).filter(Boolean);
    // KPI strip with sparklines (follows the slicers)
    var flat = []; rows.forEach(function (r) { flat = flat.concat(r.its); });
    var pub = flat.filter(function (i) { return i.status === "published"; }), days = lastDays(14, CS.to < t ? CS.to : t);
    function daily(m) { var o = days.map(function (dd) { return pub.filter(function (i) { return i.date === dd; }).reduce(function (s, i) { return s + (m ? (i[m] || 0) : 1); }, 0); }); return o; }
    function per(m, a, b) { return items.filter(function (i) { return i.status === "published" && i.date >= a && i.date <= b && (!CS.plat || pcol(i.platform) === CS.plat); }).reduce(function (s, i) { return s + (m ? (i[m] || 0) : 1); }, 0); }
    var t7 = addDays(t, -6), p0 = addDays(t, -13), p1 = addDays(t, -7), strip = clear($("kpis"));
    [["Published", null], ["Impressions", "impressions"], ["Clicks", "clicks"], ["Engagements", "engagements"], ["Leads", "leads"]].forEach(function (x) {
      var cur = per(x[1], t7, t), prev = per(x[1], p0, p1);
      kpi(strip, x[0] + " · last 7d", n0(cur), "prior 7d " + n0(prev), { delta: delta(cur, prev), spark: daily(x[1]), href: HL.route("calendar", { status: "published", from: t7, to: t, sort: x[1] ? "tot" : "date" }) });
    });
    kpi(strip, "Scheduled next 7d", String(items.filter(function (i) { return i.status === "scheduled" && i.date >= t && i.date <= addDays(t, 7); }).length), "in the queue", { href: HL.route("calendar", { status: "scheduled", from: t, to: addDays(t, 7), dir: "asc" }) });
    var miss = items.filter(function (i) { return cstat(i, t) !== "published" && cstat(i, t) !== "scheduled"; }).length;
    kpi(strip, "Missed / unconfirmed", String(miss), "past rows not published", { bad: miss > 0, href: HL.route("calendar", { status: "missed", from: addDays(t, -90), to: t }) });
    var nl = items.filter(function (i) { return /not logged/i.test(i.title || ""); }).length;
    kpi(strip, "Titles not logged", String(nl), "rows to fix", { bad: nl > 0, href: HL.route("calendar", { q: "not logged", from: addDays(t, -90), to: addDays(t, 30) }) });
    // slicers
    var sl = clear($("slicers"));
    function sel(label, opts, val, key) { var s = el("select", "fld"); s.setAttribute("aria-label", label); opts.forEach(function (o) { s.appendChild(new Option(o[1], o[0])); }); s.value = val; s.addEventListener("change", function () { var c = {}; c[key] = s.value; calSet(c); }); return s; }
    function date(label, val, key) { var i = el("input", "fld"); i.type = "date"; i.value = val; i.setAttribute("aria-label", label); i.addEventListener("change", function () { if (YMD.test(i.value)) { var c = {}; c[key] = i.value; calSet(c); } }); return i; }
    var q = el("input", "fld"); q.type = "search"; q.placeholder = "Search titles…"; q.value = CS.q; q.setAttribute("aria-label", "Search");
    q.value = H.q || ""; q.addEventListener("change", function () { calSet({ q: q.value.trim() }); });
    var st = el("div", "chips"); [["all", "All"], ["published", "Published"], ["scheduled", "Scheduled"], ["missed", "Missed"]].forEach(function (o) { var b = btn("chip", o[1], function () { calSet({ status: o[0] === "all" ? "" : o[0] }); }); b.setAttribute("aria-pressed", String(CS.status === o[0])); st.appendChild(b); });
    add(sl, st, sel("Platform", [["", "All platforms"]].concat(PCOLS.map(function (p) { return [p[0], p[0]]; })), CS.plat, "plat"),
      sel("Topic", [["", "All topics"]].concat(TOPICS.map(function (x) { return [x[0], x[0]]; })).concat([["Other", "Other"]]), CS.topic, "topic"),
      add(el("span", "muted"), "From "), date("From", CS.from, "from"), add(el("span", "muted"), " to "), date("To", CS.to, "to"), q,
      btn("btn-s line", "Reset", function () { CS.open = {}; setHash({}); }));
    var ob = el("span", "open-bar"); add(ob, el("span", "muted", "Open: "));
    [["LinkedIn", "LinkedIn"], ["Meta", "Meta"], ["TikTok", "TikTok"], ["YouTube Shorts", "YouTube"], ["Pinterest", "Pinterest"], ["Blog", "Blog"], ["MailerLite", "MailerLite"]].forEach(function (x) { var a = ext(HL.platformLink(x[0], LINKS), x[1]); if (a) ob.appendChild(a); });
    sl.appendChild(ob);
    // matrix
    var maxI = 1; rows.forEach(function (r) { PCOLS.forEach(function (p) { var b = r.by[p[0]]; if (b && b.i > maxI) maxI = b.i; }); });
    function sv(r, k) { if (k === "date") return r.date; if (k === "title") return r.title; if (k === "topic") return r.topic; if (k === "tot") return r.tot.i; var b = r.by[k]; return b ? (b.i === null ? -1 : b.i) : -2; }
    rows.sort(function (a, b) { var x = sv(a, CS.sort), y = sv(b, CS.sort), c = typeof x === "number" ? x - y : String(x).localeCompare(String(y)); return CS.dir === "asc" ? c : -c; });
    var tbl = el("table", "dt mx"), th = el("thead"), hr = el("tr");
    [["date", "Date"], ["title", "Content"], ["topic", "Topic"]].concat(PCOLS.map(function (p) { return [p[0], p[0], p[1]]; })).concat([["tot", "Total"]]).forEach(function (h) {
      var c = el("th", h[0] === "date" || h[0] === "title" || h[0] === "topic" ? "" : h[0] === "tot" ? "n" : "c", h[1]); if (h[2]) c.title = h[2] + " · impressions · clicks · engagements";
      if (CS.sort === h[0]) c.setAttribute("data-dir", CS.dir);
      c.addEventListener("click", function () { calSet(CS.sort === h[0] ? { sort: h[0], dir: CS.dir === "asc" ? "desc" : "asc" } : { sort: h[0], dir: h[0] === "title" || h[0] === "topic" ? "asc" : "desc" }); });
      hr.appendChild(c);
    });
    add(th, hr); var bd = el("tbody");
    function metric(b, k, its) {
      if (b[k] !== null) return n0(b[k]);
      var pubd = its.filter(function (i) { return i.status === "published"; });
      if (pubd.length && pubd.every(function (i) { return i.note || i.metrics_at; })) return "n/a";
      return "";
    }
    rows.forEach(function (r) {
      var tr = el("tr", "mrow"), open = !!CS.open[r.g.key];
      var t1 = el("td", "nw"); t1.textContent = fmtD(r.date); tr.appendChild(t1);
      var t2 = el("td", "w"), tb = btn("reply", (open ? "▾ " : "▸ ") + (r.title || ""), function () { CS.open[r.g.key] = !open; R.calendar(d); }); tb.title = "Show every post in this group"; t2.appendChild(tb); tr.appendChild(t2);
      tr.appendChild(el("td", "nw muted", r.topic));
      PCOLS.forEach(function (p) {
        var b = r.by[p[0]], td = el("td", "mc");
        if (b) {
          var sts = b.items.map(function (i) { return cstat(i, t); }), s = sts.indexOf("missed") >= 0 || sts.indexOf("missed?") >= 0 ? "missed" : sts.indexOf("scheduled") >= 0 && sts.indexOf("published") < 0 ? "scheduled" : "published";
          var dot = el("i", "dot " + s), m = el("span", "mono", [metric(b, "i", b.items), metric(b, "c", b.items), metric(b, "e", b.items)].join("·").replace(/^··$/, ""));
          var cl = hl("", "#" + HL.qs(merge(H, { item: b.items[0].id })), "cell"); add(cl, dot, m); td.appendChild(cl);
          if (H.item && b.items.some(function (i) { return i.id === H.item; })) td.classList.add("sel");
          if (b.i) td.style.background = "rgba(176,141,63," + (0.06 + 0.42 * b.i / maxI).toFixed(3) + ")";
          td.title = b.items.map(function (i) { return p[0] + " · " + fmtD(i.date) + (i.time && !i.time_tbc ? " " + i.time : "") + " · " + cstat(i, t) + "\n" + i.title + "\nimpr " + n0(i.impressions) + " · clicks " + n0(i.clicks) + " · eng " + n0(i.engagements) + (i.note ? "\n" + i.note : "") + (i.metrics_at ? "\nmetrics as of " + fmtD(i.metrics_at, true) : ""); }).join("\n\n");
        }
        tr.appendChild(td);
      });
      var hasM = r.its.some(function (i) { return i.impressions !== null && i.impressions !== undefined; });
      var tt = el("td", "n mono", hasM ? n0(r.tot.i) + "·" + n0(r.tot.c) + "·" + n0(r.tot.e) : ""); tr.appendChild(tt);
      bd.appendChild(tr);
      if (open) {
        var sub = el("tr", "subrow"), c = el("td"); c.colSpan = PCOLS.length + 4; var host = el("div"); c.appendChild(host); sub.appendChild(c); bd.appendChild(sub);
        table(host, { rows: r.g.items, search: false, sort: { k: "date", dir: "asc" },
          cols: [{ k: "date", l: "Date", cls: "nw", get: function (i) { return i.date + (i.time || ""); }, cell: function (i) { return fmtD(i.date) + (i.time && !i.time_tbc ? " " + i.time : " · TBC"); } },
            { k: "platform", l: "Platform", cls: "nw" }, { k: "title", l: "Title", cls: "w", cell: function (i) { var w = el("div"); add(w, i.title || ""); var a = link(i.link, "open"); if (a) { w.appendChild(document.createTextNode(" ")); w.appendChild(a); } if (i.note) w.appendChild(el("div", "muted", i.note)); return w; } },
            { k: "status", l: "Status", cell: function (i) { return pill(cstat(i, t).replace("?", "")); } }, { k: "impressions", l: "Impr", num: true }, { k: "clicks", l: "Clicks", num: true }, { k: "engagements", l: "Eng", num: true }, { k: "leads", l: "Leads", num: true }, { k: "agent", l: "Agent", cls: "nw" }],
          ref: function (i) { return i.id; } });
      }
    });
    var tot = { i: 0, c: 0, e: 0 }; rows.forEach(function (r) { tot.i += r.tot.i; tot.c += r.tot.c; tot.e += r.tot.e; });
    var tr2 = el("tr", "total"); add(tr2, el("td", "", "Total"), el("td", "", rows.length + " pieces · " + flat.length + " posts"), el("td"));
    PCOLS.forEach(function (p) { var s = { i: 0, c: 0, e: 0, n: 0 }; rows.forEach(function (r) { var b = r.by[p[0]]; if (b) { s.n++; s.i += b.i || 0; s.c += b.c || 0; s.e += b.e || 0; } }); tr2.appendChild(el("td", "n mono", s.n ? n0(s.i) + "·" + n0(s.c) + "·" + n0(s.e) : "")); });
    tr2.appendChild(el("td", "n mono", n0(tot.i) + "·" + n0(tot.c) + "·" + n0(tot.e))); bd.appendChild(tr2);
    add(tbl, th, bd); var w = clear($("cal")); w.appendChild(tbl); if (!rows.length) w.appendChild(el("div", "empty", "Nothing matches these slicers.")); fit(w);
    var latestM = items.map(function (i) { return i.metrics_at || ""; }).sort().pop();
    $("calMeta").textContent = "Click any cell for the post · cells: impressions·clicks·engagements · dot: green published, gold scheduled, red missed/unconfirmed · n/a = the platform doesn't report it (hover) · " + (latestM ? "metrics as of " + fmtD(latestM, true) : "no metrics yet");
    calDetail(items, t);
  };
  function calDetail(items, t) {
    var it = H.item && items.filter(function (i) { return i.id === H.item; })[0];
    if (!H.item) { hideDetail(); return; }
    var close = merge(H, {}); delete close.item;
    if (!it) { showDetail({ title: "Post not found", sub: "it may be outside the last 90 days", close: close, fields: [["Id", H.item]] }); return; }
    var g = items.filter(function (i) { return ckey(i) === ckey(it) && pcol(i.platform) === pcol(it.platform) && i.id !== it.id; });
    var na = function (v) { return v === null || v === undefined ? (it.status === "published" ? (it.note || it.metrics_at ? "n/a" : "not pulled yet") : "—") : n0(v); };
    var statsLk = HL.safeUrl(it.stats_link) ? { label: "Stats", url: it.stats_link } : HL.platformLink(it.platform, LINKS);
    showDetail({
      title: it.title || "(untitled)", sub: it.platform + " · " + fmtD(it.date) + (it.time && !it.time_tbc ? " " + it.time : " · time TBC"), close: close,
      links: [link(it.link, "Open post ↗"), ext(statsLk, statsLk && statsLk.label === "Stats" ? "Stats" : null), hl("All " + pcol(it.platform) + " posts", HL.route("calendar", { plat: pcol(it.platform), from: CS.from, to: CS.to })), docTag(it.platform)],
      fields: [["Status", pill(cstat(it, t).replace("?", ""))], ["Impressions", na(it.impressions)], ["Clicks", na(it.clicks)], ["Engagements", na(it.engagements)], ["Leads", na(it.leads)],
        ["CTR", it.impressions ? pct(it.clicks || 0, it.impressions) : ""], ["Metrics as of", it.metrics_at ? fmtD(it.metrics_at, true) : ""], ["Agent", it.agent], ["Source", it.source], ["Note", it.note]],
      table: g.length ? { rows: g, search: false, short: true, sort: { k: "date", dir: "asc" }, cols: [{ k: "date", l: "Other posts in this cell", cls: "nw", cell: function (i) { return hl(fmtD(i.date) + (i.time && !i.time_tbc ? " " + i.time : ""), "#" + HL.qs(merge(H, { item: i.id }))); } }, { k: "title", l: "Title", cls: "w" }, { k: "impressions", l: "Impr", num: true }, { k: "clicks", l: "Clicks", num: true }, { k: "engagements", l: "Eng", num: true }] } : null,
      ref: it.id
    });
  }

  var RANGES = { today: 1, "7d": 7, "14d": 14, "30d": 30 };
  R.ads = function (d) {
    var P = adsModel(d.ads || []), t = today(), keys = Object.keys(P).sort(function (a, b) { return (P[b].paid - P[a].paid) || a.localeCompare(b); });
    var A = function (p) { return HL.route("ads", p); }, ps = function (k) { return HL.slug(k); };
    var rows = keys.map(function (k) { var p = P[k], s = p.s7 || p.s30 || { i: null, c: null, s: null, v: null }; return { k: k, p: p, type: p.paid ? "Paid" : "Organic", ti: p.today.n ? p.today.i : null, tc: p.today.n ? p.today.c : null, ts: p.today.n ? p.today.s : null, i: s.i, c: s.c, ctr: s.i ? s.c / s.i : null, sp: s.s, cpc: s.c && s.s ? s.s / s.c : null, v: s.v, di: p.s7 && p.p7 && p.p7.i ? (p.s7.i - p.p7.i) / p.p7.i : null, latest: p.latest }; });
    function cellL(r, range, text) { return hl(text, A({ platform: ps(r.k), range: range })); }
    table($("plat"), {
      rows: rows, sort: { k: "sp", dir: "desc" }, selects: [{ l: "Type", k: "type", value: H.type === "Paid" || H.type === "Organic" ? H.type : "" }], search: false,
      cols: [
        { k: "k", l: "Platform", cls: "nw", cell: function (r) { var w = el("div"); add(w, hl(r.k, A({ platform: ps(r.k), range: "7d" }), "b")); if (r.p.note) w.appendChild(el("div", "muted", r.p.note)); return w; } },
        { k: "type", l: "Type" },
        { k: "ti", l: "Today impr", num: true, cell: function (r) { return cellL(r, "today", n0(r.ti)); } }, { k: "tc", l: "Today clicks", num: true, cell: function (r) { return cellL(r, "today", n0(r.tc)); } }, { k: "ts", l: "Today $", num: true, cell: function (r) { return cellL(r, "today", r.ts === null ? "—" : money(r.ts)); } },
        { k: "i", l: "7d impr", num: true, cell: function (r) { return cellL(r, "7d", n0(r.i)); } }, { k: "di", l: "vs prior", num: true, cell: function (r) { return r.di === null ? "—" : add(el("span"), el("span", r.di >= 0 ? "up" : "dn", (r.di >= 0 ? "▲" : "▼") + Math.abs(r.di * 100).toFixed(0) + "%")); } },
        { k: "c", l: "7d clicks", num: true, cell: function (r) { return cellL(r, "7d", n0(r.c)); } }, { k: "ctr", l: "CTR", num: true, cell: function (r) { return r.ctr === null ? "—" : (r.ctr * 100).toFixed(1) + "%"; } },
        { k: "sp", l: "7d spend", num: true, cell: function (r) { return cellL(r, "7d", r.type === "Paid" ? money(r.sp) : "—"); } }, { k: "cpc", l: "CPC", num: true, cell: function (r) { return r.cpc === null ? "—" : money(r.cpc); } },
        { k: "v", l: "Conv.", num: true },
        { k: "latest", l: "Data to", cls: "nw", cell: function (r) { var w = el("span"); add(w, fmtD(r.latest)); if (!r.latest || r.latest < addDays(t, -1)) w.appendChild(el("span", "stale-tag", "stale")); return w; } },
        { k: "rev", l: "Review", cls: "nw", get: function () { return ""; }, cell: function (r) { return reviewCell(A({ platform: ps(r.k), range: "7d" }), HL.platformLink(r.k, LINKS), r.k); } }
      ], ref: function (r) { return "platform:" + r.k.replace(/[^A-Za-z0-9]+/g, "-"); }
    });
    var days = lastDays(14), sp = [], im = [];
    keys.forEach(function (k, i) {
      var vs = {}, vi = {}; P[k].daily.forEach(function (r) { vs[r.date] = (vs[r.date] || 0) + (r.spend || 0); vi[r.date] = (vi[r.date] || 0) + (r.impressions || 0); });
      var c = COLORS[k] || PALETTE[i % PALETTE.length]; if (P[k].paid) sp.push({ name: k, color: c, vals: vs }); im.push({ name: k, color: c, vals: vi });
    });
    var dayHref = function (dd, name) { return A({ platform: ps(name), date: dd }); };
    columns($("chSpend"), days, sp, { fmt: function (v) { return "$" + Math.round(v); }, empty: "No daily spend in the last 14 days.", href: dayHref });
    columns($("chImpr"), days, im, { empty: "No daily impressions in the last 14 days.", href: dayHref });
    table($("daily"), {
      rows: (d.ads || []).filter(function (r) { return r.date >= addDays(t, -30); }), sort: { k: "date", dir: "desc" }, selects: [{ l: "Platform", k: "platform" }, { l: "Window", get: function (r) { return r.window_days + "d"; } }],
      cols: [{ k: "date", l: "Day / window end", cls: "nw", cell: function (r) { return hl(fmtD(r.date) + (r.window_days > 1 ? " (" + r.window_days + "-day total)" : ""), A({ platform: ps(r.platform), date: r.date })); } },
        { k: "platform", l: "Platform", cls: "nw", cell: function (r) { return hl(r.platform, A({ platform: ps(r.platform), range: "30d" })); } },
        { k: "campaign", l: "Campaign", cls: "nw", cell: function (r) { return hl(r.campaign, A({ platform: ps(r.platform), campaign: r.campaign, range: "30d" })); } },
        { k: "impressions", l: "Impr", num: true }, { k: "clicks", l: "Clicks", num: true }, { k: "spend", l: "Spend", num: true, cell: function (r) { return r.spend === null ? "—" : money(r.spend); } }, { k: "conversions", l: "Conv.", num: true }, { k: "source", l: "Source", cls: "nw" },
        { k: "open", l: "Open", cls: "nw", get: function () { return ""; }, cell: function (r) { return ext(HL.campaignLink(r.platform, r.campaign, LINKS), "Open") || ""; } }]
    });
    adsDetail(d, P, keys, t);
  };
  // Ads drill-down: #platform=google-ads&range=7d | #date=YYYY-MM-DD | #type=Paid&range=today | &campaign=…
  function adsDetail(d, P, keys, t) {
    if (!H.platform && !H.range && !H.date && !H.campaign) { hideDetail(); return; }
    var plat = H.platform ? HL.matchSlug(H.platform, keys) : null;
    var from, to, label, rk = RANGES[H.range] ? H.range : "7d";
    if (YMD.test(H.date || "")) { from = to = H.date; label = fmtD(H.date); } else { to = t; from = addDays(t, -(RANGES[rk] - 1)); label = rk === "today" ? "today" : "last " + RANGES[rk] + " days"; }
    var names = keys.filter(function (k) { return (!plat || k === plat) && (!H.type || (H.type === "Paid") === P[k].paid); });
    var raw = (d.ads || []).filter(function (r) { return names.indexOf(r.platform) >= 0 && (!H.campaign || r.campaign === H.campaign) && r.date >= from && r.date <= to; });
    // per platform + campaign: daily rows are summed; platforms that only report window totals use the newest window
    var G = {}; raw.forEach(function (r) { var k = r.platform + "\u0001" + r.campaign; (G[k] = G[k] || { platform: r.platform, campaign: r.campaign, daily: [], win: [] })[r.window_days === 1 ? "daily" : "win"].push(r); });
    if (!H.date) (d.ads || []).forEach(function (r) { // window totals that end just after the range still describe it
      if (r.window_days > 1 && names.indexOf(r.platform) >= 0 && (!H.campaign || r.campaign === H.campaign) && r.date > to && r.date <= addDays(to, 2)) { var k = r.platform + "\u0001" + r.campaign; (G[k] = G[k] || { platform: r.platform, campaign: r.campaign, daily: [], win: [] }).win.push(r); }
    });
    var sum = Object.keys(G).map(function (k) {
      var g = G[k], use = g.daily.length ? g.daily : g.win.sort(function (a, b) { return b.date.localeCompare(a.date); }).slice(0, 1);
      var o = use.reduce(function (s, r) { s.i += r.impressions || 0; s.c += r.clicks || 0; s.s += r.spend || 0; s.v += r.conversions || 0; return s; }, { i: 0, c: 0, s: 0, v: 0 });
      o.platform = g.platform; o.campaign = g.campaign; o.paid = P[g.platform] && P[g.platform].paid;
      o.basis = g.daily.length ? g.daily.length + " daily row" + (g.daily.length > 1 ? "s" : "") : use.length ? use[0].window_days + "-day platform total to " + fmtD(use[0].date) : ""; return o;
    });
    var T = sum.reduce(function (s, r) { s.i += r.i; s.c += r.c; s.s += r.s; s.v += r.v; return s; }, { i: 0, c: 0, s: 0, v: 0 });
    var base = merge(H, {}); delete base.date; delete base.range;
    var chips = el("span", "rng"); ["today", "7d", "14d", "30d"].forEach(function (x) { var a = hl(x === "today" ? "Today" : x, "#" + HL.qs(merge(base, { range: x })), "chip" + (!H.date && rk === x ? " on" : "")); chips.appendChild(a); });
    var lk = plat ? HL.campaignLink(plat, H.campaign, LINKS) : null;
    showDetail({
      title: (plat || (H.type ? H.type + " platforms" : "All platforms")) + (H.campaign ? " · " + H.campaign : "") + " · " + label, sub: from === to ? "" : fmtD(from) + " – " + fmtD(to), close: {},
      links: [chips, lk ? ext(lk, "Open " + lk.label) : null, plat ? docTag(plat) : null],
      fields: [["Impressions", n0(T.i)], ["Clicks", n0(T.c)], ["CTR", pct(T.c, T.i)], ["Spend", money(T.s)], ["CPC", T.c && T.s ? money(T.s / T.c) : "—"], ["Conversions", n0(T.v)]],
      table: { rows: sum, search: false, short: true, sort: { k: "s", dir: "desc" }, empty: "No rows for " + label + " yet" + (plat ? " on " + plat : "") + ". Data may not be pulled for this day.",
        cols: [{ k: "platform", l: "Platform", cls: "nw", cell: function (r) { return hl(r.platform, A2({ platform: HL.slug(r.platform) })); } }, { k: "campaign", l: "Campaign", cls: "nw", cell: function (r) { return hl(r.campaign, A2({ platform: HL.slug(r.platform), campaign: r.campaign })); } },
          { k: "i", l: "Impr", num: true }, { k: "c", l: "Clicks", num: true }, { k: "ctr", l: "CTR", num: true, get: function (r) { return r.i ? r.c / r.i : null; }, cell: function (r) { return pct(r.c, r.i); } },
          { k: "s", l: "Spend", num: true, cell: function (r) { return r.paid ? money(r.s) : "—"; } }, { k: "cpc", l: "CPC", num: true, get: function (r) { return r.c && r.s ? r.s / r.c : null; }, cell: function (r) { return r.c && r.s ? money(r.s / r.c) : "—"; } }, { k: "v", l: "Conv.", num: true },
          { k: "basis", l: "Basis", cls: "nw" }, { k: "open", l: "Open", cls: "nw", get: function () { return ""; }, cell: function (r) { return reviewCell(A2({ platform: HL.slug(r.platform) }), HL.campaignLink(r.platform, r.campaign, LINKS), r.platform); } }] },
      ref: plat ? "platform:" + plat.replace(/[^A-Za-z0-9]+/g, "-") : null
    });
    function A2(p) { return "#" + HL.qs(merge(H.date ? { date: H.date } : { range: rk }, p)); }
  }

  R.finance = function (d) {
    var f = d.finance || [], strip = clear($("kpis")), F = function (p) { return HL.route("finance", p); };
    var c = function (s) { return f.filter(function (x) { return x.status === s; }).length; };
    kpi(strip, "Waiting for you", String(c("open")), "bank-feed items", { bad: c("open") > 0, href: F({ status: "open" }) });
    kpi(strip, "Answered here", String(c("new") + c("seen")), "Finance posts them next run", { href: F({ status: "new" }) });
    kpi(strip, "Done", String(c("done")), "posted in QuickBooks", { href: F({ status: "done" }) });
    var qb = HL.platformLink("QuickBooks", LINKS); kpi(strip, "QuickBooks", "Banking ↗", "bank feed and categories", { ext: qb });
    var one = H.q ? f.filter(function (x) { return x.id === H.q; }) : null, host = $("fin");
    var sv = ["open", "new", "seen", "done"].indexOf(H.status) >= 0 ? H.status : one ? "" : "open";
    table(host, {
      rows: one || f, sort: { k: "o", dir: "asc" }, selects: [{ l: "Status", k: "status", value: sv }, { l: "Account", get: function (x) { var m = /, ([^,(]+?••\d{4})/.exec(x.question || ""); return m ? m[1] : ""; } }],
      cols: [
        { k: "o", l: "#", num: true, get: function (x) { return f.indexOf(x); }, cell: function (x) { return hl(String(f.indexOf(x) + 1), F({ q: x.id })); } },
        { k: "question", l: "Bank item", cls: "w", cell: function (x) { return clip(x.question); } },
        { k: "suggested_answer", l: "Suggested", cls: "ww" },
        { k: "status", l: "Your answer", cls: "ww", cell: function (x) { return answerCell("finance", x); } },
        { k: "qbo", l: "Open", cls: "nw", get: function () { return ""; }, cell: function () { return ext(qb, "QuickBooks") || ""; } }
      ], ref: function (x) { return x.id; }, empty: one ? "That finance item isn't in the list any more." : "No finance questions here.",
      reply: { head: "Ask / comment", label: "Ask / comment", kind: "question", marker: function (x) { return x.status === "open"; } }
    });
    if (one) host.insertBefore(filterChip("Showing finance item " + H.q, F({})), host.firstChild);
    var g = $("finAsk"); if (g) { clear(g).appendChild(commentBox("finance:general", "question", "Ask Finance anything (not tied to a row)")); }
  };

  R.leads = function (d) {
    var L = d.leads || [], t = today(), strip = clear($("kpis")), LR = function (p) { return HL.route("leads", p); };
    var wait = function (x) { return x.status === "new" || x.status === "drafted"; };
    kpi(strip, "Leads 7d", String(L.filter(function (x) { return ymdET(x.received_at) >= addDays(t, -6); }).length), "website forms", { href: LR({ range: "7d" }) });
    kpi(strip, "Leads 30d", String(L.filter(function (x) { return ymdET(x.received_at) >= addDays(t, -29); }).length), "", { href: LR({ range: "30d" }) });
    kpi(strip, "Waiting for a reply", String(L.filter(wait).length), "draft or not started", { bad: L.some(wait), href: LR({ status: "waiting" }) });
    kpi(strip, "Replied", String(L.filter(function (x) { return x.status === "sent" || x.status === "won"; }).length), "", { href: LR({ status: "sent" }) });
    kpi(strip, "Gmail", "Inbox ↗", "lead emails arrive here", { ext: HL.platformLink("Gmail", LINKS) });
    var rows = L, why = "";
    if (YMD.test(H.date || "")) { rows = rows.filter(function (x) { return ymdET(x.received_at) === H.date; }); why = "received " + fmtD(H.date); }
    else if (RANGES[H.range]) { var f0 = addDays(t, -(RANGES[H.range] - 1)); rows = rows.filter(function (x) { return ymdET(x.received_at) >= f0; }); why = "last " + RANGES[H.range] + " days"; }
    if (H.status === "waiting") { rows = rows.filter(wait); why = (why ? why + " · " : "") + "waiting for a reply"; }
    var host = $("leads");
    table(host, {
      rows: rows, sort: { k: "received_at", dir: "desc" }, selects: [{ l: "Status", k: "status", value: H.status && H.status !== "waiting" ? H.status : "" }, { l: "Source", k: "source" }],
      cols: [
        { k: "received_at", l: "Received (ET)", cls: "nw", cell: function (x) { return hl(fmtD(x.received_at, true), LR(merge(H, { lead: x.id }))); } },
        { k: "first_name", l: "Name", cls: "nw", cell: function (x) { return hl(x.first_name || "(no name)", LR(merge(H, { lead: x.id })), "b"); } }, { k: "email_domain", l: "Email domain", cls: "nw" },
        { k: "topic", l: "Topic", cls: "w", cell: function (x) { return clip(x.topic || ""); } }, { k: "source", l: "Source", cls: "nw" },
        { k: "status", l: "Reply", cell: function (x) { return pill(x.status); } },
        { k: "reminder_at", l: "Reminder", cls: "nw", cell: function (x) { return fmtD(x.reminder_at, true); } },
        { k: "note", l: "Note", cls: "ww", cell: function (x) { return clip(x.note || ""); } },
        { k: "gm", l: "Open", cls: "nw", get: function () { return ""; }, cell: function (x) { return link(HL.gmailSearch(x.first_name), "Gmail ↗") || ""; } }
      ], ref: function (x) { return "lead:" + x.id; }, empty: why ? "No leads for " + why + "." : "No leads logged yet."
    });
    if (why) host.insertBefore(filterChip("Leads: " + why, LR({})), host.firstChild);
    var x = H.lead && L.filter(function (l) { return l.id === H.lead; })[0], close = merge(H, {}); delete close.lead;
    if (!H.lead) { hideDetail(); return; }
    if (!x) { showDetail({ title: "Lead not found", close: close }); return; }
    showDetail({ title: (x.first_name || "Lead") + " · " + (x.email_domain || ""), sub: fmtD(x.received_at, true), close: close,
      links: [link(HL.gmailSearch(x.first_name), "Find in Gmail ↗"), docTag("Lead Engine")],
      fields: [["Topic", x.topic], ["Source", x.source], ["Reply", pill(x.status)], ["Reminder", fmtD(x.reminder_at, true)], ["Note", x.note], ["Updated", fmtD(x.updated_at, true)]],
      ref: "lead:" + x.id });
  };

  function tasksForm(host) {
    if (!host) return; clear(host);
    var area = el("select", "fld"); ["general", "site", "blog", "social", "ads", "store", "finance", "leads", "freelance"].forEach(function (a) { area.appendChild(new Option(a, a)); }); area.setAttribute("aria-label", "Area");
    var ta = el("textarea", "fld"); ta.maxLength = 4000; ta.rows = 2; ta.placeholder = "Ask the agents for anything: a change, a post, a report…"; ta.setAttribute("aria-label", "New request");
    var msg = el("span", ""), send = btn("btn-s gold", "Send request", function () {
      var b = ta.value.trim(); if (!b) { msg.className = "err-msg"; msg.textContent = "Write the request first."; return; }
      send.disabled = true; post("/api/hub/request", { area: area.value, body: b }).then(function (j) { msg.className = "ok-msg"; msg.textContent = "Sent ✓ request #" + j.request.id; ta.value = ""; })
        .catch(function (e) { msg.className = "err-msg"; msg.textContent = "Not sent (" + e.message + ")"; }).then(function () { send.disabled = false; });
    });
    add(host, add(el("div", "cbox"), ta, add(el("div", "row-acts"), area, send, msg)));
  }
  R.tasks = function (d) {
    tasksForm($("reqForm"));
    table($("reqs"), {
      rows: d.requests || [], sort: { k: "id", dir: "desc" }, selects: [{ l: "Status", k: "status" }, { l: "Area", k: "area" }],
      cols: [{ k: "id", l: "#", num: true }, { k: "created_at", l: "Asked (ET)", cls: "nw", cell: function (r) { return fmtD(r.created_at, true); } }, { k: "area", l: "Area", cell: function (r) { var ar = { ads: "ads", finance: "finance", leads: "leads", social: "calendar", blog: "calendar" }[r.area]; return ar ? hl(r.area, HL.route(ar)) : r.area; } },
        { k: "body", l: "Request", cls: "w", cell: function (r) { return clip(r.body); } }, { k: "status", l: "Status", cell: function (r) { return pill(r.status); } },
        { k: "agent_note", l: "Agent reply", cls: "w", cell: function (r) { return r.agent_note ? el("div", "note", r.agent_note) : el("span", "muted", "—"); } }],
      ref: function (r) { return "request:" + r.id; }, empty: "No requests yet. Use the box above."
    });
    var inputs = (d.allComments || []).map(function (c) { return { t: c.created_at, type: c.kind || "comment", where: c.page + " · " + c.item_ref, href: HL.refHref(c.page, c.item_ref), body: c.body, status: c.status, note: c.agent_note }; });
    (d.needs || []).filter(function (n) { return n.answer; }).forEach(function (n) { inputs.push({ t: n.answered_at, type: "answer", where: "needs · " + n.id, href: n.ref ? HL.refHref("home", n.ref) : HL.route("home"), body: n.answer, status: n.status, note: n.agent_note }); });
    table($("inputs"), {
      rows: inputs, sort: { k: "t", dir: "desc" }, selects: [{ l: "Type", k: "type" }, { l: "Status", k: "status" }],
      cols: [{ k: "t", l: "When (ET)", cls: "nw", cell: function (r) { return fmtD(r.t, true); } }, { k: "type", l: "Type" }, { k: "where", l: "On", cls: "ww", cell: function (r) { return hl(r.where, r.href); } }, { k: "body", l: "What you said", cls: "w", cell: function (r) { return clip(r.body); } },
        { k: "status", l: "Status", cell: function (r) { return pill(r.status); } }, { k: "note", l: "Agent reply", cls: "w", cell: function (r) { return r.note ? el("div", "note", r.note) : el("span", "muted", "—"); } }],
      empty: "Nothing sent from the hub yet."
    });
  };

  R.log = function () { pollLog($("log"), $("logAgent")); };

  // ---------- boot ----------
  function load() {
    status("Loading…");
    if (PAGE === "log") { R.log(); status(""); return; }
    getJSON("/api/hub/data?page=" + encodeURIComponent(PAGE)).then(function (d) {
      DATA = d; LINKS = HL.index(d.links); indexComments(d.comments); R[PAGE](d);
      status("Updated " + new Date().toLocaleTimeString("en-US", { timeZone: TZ, hour: "numeric", minute: "2-digit" }) + " ET");
    }).catch(function (e) { status("Couldn't load (" + e.message + "). Refresh; if it keeps failing, sign in again.", true); });
  }
  var rf = $("refresh"); if (rf) rf.addEventListener("click", function () { location.reload(); });
  // hash routes: re-draw the page from the loaded data (no refetch); back/forward work
  window.addEventListener("hashchange", function () {
    var n = HL.parseHash(location.hash); if (JSON.stringify(n) === JSON.stringify(H)) return; H = n;
    if (PAGE === "log") R.log(); else if (DATA && R[PAGE]) R[PAGE](DATA);
  });
  if (R[PAGE]) load();
})();
