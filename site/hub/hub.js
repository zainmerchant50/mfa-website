/* MFA Hub (private). All data comes from /api/hub/* and is written to the page with textContent only. */
(function () {
  "use strict";
  var PAGE = document.body.getAttribute("data-page");
  var $ = function (id) { return document.getElementById(id); };
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }
  function add(parent) { for (var i = 1; i < arguments.length; i++) { var k = arguments[i]; if (k) parent.appendChild(k); } return parent; }
  var TZ = "America/New_York";
  function fmt(iso, withTime) {
    if (!iso) return "";
    var d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso + "T12:00:00" : iso);
    if (isNaN(d)) return String(iso);
    var o = { timeZone: TZ, month: "short", day: "numeric" };
    if (withTime) { o.hour = "numeric"; o.minute = "2-digit"; }
    return d.toLocaleString("en-US", o);
  }
  function todayET() { return new Date().toLocaleDateString("en-CA", { timeZone: TZ }); }
  function addDays(ymd, n) { var d = new Date(ymd + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  function n0(v) { return v === null || v === undefined || v === "" ? "—" : Number(v).toLocaleString("en-US"); }
  function money(v) { return v === null || v === undefined ? "—" : "$" + Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function pill(s) { return el("span", "pill " + String(s || "").replace(/[^A-Za-z_]/g, ""), String(s || "").replace(/_/g, " ")); }
  function status(t, err) { var s = $("hubStatus"); if (s) { s.textContent = t || ""; s.className = "hub-status" + (err ? " err" : ""); } }
  function safeLink(url, label) {
    if (typeof url !== "string" || !/^https:\/\/[^\s]+$/.test(url)) return null;
    var a = el("a", "ext", label || url); a.href = url; a.target = "_blank"; a.rel = "noopener noreferrer"; return a;
  }

  // ---------- API ----------
  function getData(page) {
    return fetch("/api/hub/data?page=" + encodeURIComponent(page), { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
  }
  function post(path, body) {
    return fetch(path, { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-MFA-Hub": "1" }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || !j.ok) throw new Error(j.error || "HTTP " + r.status); return j; }); });
  }

  // ---------- comments ----------
  var COMMENTS = {};
  function indexComments(list) { COMMENTS = {}; (list || []).forEach(function (c) { (COMMENTS[c.item_ref] = COMMENTS[c.item_ref] || []).push(c); }); }
  function threadItem(c) {
    var li = el("li");
    add(li, pill(c.status), document.createTextNode(" " + fmt(c.created_at, true) + " · "), document.createTextNode(c.body));
    if (c.agent_note) add(li, el("span", "reply", "Agent: " + c.agent_note));
    return li;
  }
  function commentBox(ref) {
    var box = el("div", "cbox");
    var list = el("ul", "thread");
    (COMMENTS[ref] || []).slice().reverse().forEach(function (c) { list.appendChild(threadItem(c)); });
    var open = el("button", "hbtn line", (COMMENTS[ref] || []).length ? "Comment (" + COMMENTS[ref].length + ")" : "Comment");
    open.type = "button";
    var form = el("div", "cbox-f"); form.hidden = true;
    var ta = el("textarea"); ta.maxLength = 4000; ta.rows = 3; ta.setAttribute("aria-label", "Comment for the agents");
    ta.placeholder = "Your comment or instruction for the agents";
    var send = el("button", "hbtn", "Send"); send.type = "button";
    var msg = el("span", "sent");
    var acts = add(el("div", "acts"), send, msg);
    add(form, ta, acts);
    open.addEventListener("click", function () { form.hidden = !form.hidden; if (!form.hidden) ta.focus(); });
    send.addEventListener("click", function () {
      var body = ta.value.trim();
      if (!body) { msg.className = "sent err"; msg.textContent = "Write something first."; return; }
      send.disabled = true; msg.className = "sent"; msg.textContent = "Sending…";
      post("/api/hub/comment", { page: PAGE, item_ref: ref, body: body }).then(function (j) {
        msg.textContent = "Sent ✓"; ta.value = "";
        (COMMENTS[ref] = COMMENTS[ref] || []).unshift(j.comment);
        list.appendChild(threadItem(j.comment));
        open.textContent = "Comment (" + COMMENTS[ref].length + ")";
      }).catch(function (e) { msg.className = "sent err"; msg.textContent = "Not sent (" + e.message + "). Try again."; })
        .then(function () { send.disabled = false; });
    });
    add(box, list, add(el("div", "acts"), open), form);
    return box;
  }

  function kv(pairs) {
    var dl = el("dl", "kv");
    pairs.forEach(function (p) { if (p[1] === undefined || p[1] === null || p[1] === "") return; add(dl, el("dt", null, p[0]), el("dd", null, p[1])); });
    return dl;
  }

  // ---------- pages ----------
  var R = {};

  R.home = function (d) {
    var c = d.counts || {};
    var tiles = [
      ["board", "Agent Board", c.agents_blocked + " blocked · " + c.ideas_new + " new ideas", "What every agent is doing, what needs you, ideas to approve."],
      ["calendar", "Content Calendar", c.calendar_next7 + " in the next 7 days", "Every post, pin, video, blog and newsletter with its numbers."],
      ["ads", "Ads Monitor", c.ads_latest ? "Data through " + fmt(c.ads_latest) : "No data yet", "All platforms, today and the last 7 days."],
      ["finance", "Finance questions", c.finance_open + " waiting for you", "Bank-feed items to label as business or personal."]
    ];
    var g = $("tiles"); g.textContent = "";
    tiles.forEach(function (t) {
      var a = el("a", "tile"); a.href = "/hub/" + t[0] + "/";
      add(a, el("span", "eyebrow eb-dark", t[1]), el("span", "big", t[2]), el("p", null, t[3]));
      g.appendChild(a);
    });
    $("ccount").textContent = c.comments_new + " new comment(s) waiting for an agent · " + c.comments_done + " done";
    var r = $("replies"); r.textContent = "";
    if (!(d.replies || []).length) r.appendChild(el("p", "empty", "No agent replies yet. When an agent acts on a comment, its note shows here."));
    (d.replies || []).forEach(function (x) {
      var card = add(el("div", "hcard"), add(el("div", "row"), el("span", "muted", x.page + " · " + fmt(x.created_at, true)), pill(x.status)),
        el("p", "txt", x.body), el("p", "need", "Agent: " + x.agent_note));
      r.appendChild(card);
    });
  };

  var boardFilter = "new";
  R.board = function (d) {
    var items = d.items || [];
    var agents = items.filter(function (i) { return i.kind === "agent"; });
    var ideas = items.filter(function (i) { return i.kind === "idea"; });
    var acts = items.filter(function (i) { return i.kind === "activity"; }).sort(function (a, b) { return String(b.at).localeCompare(String(a.at)); });
    // needs you
    var nz = $("needs"); nz.textContent = "";
    agents.filter(function (a) { return a.data.needs_zain; }).forEach(function (a) {
      nz.appendChild(add(el("div", "need"), el("b", null, (a.agent || a.ref) + ": "), document.createTextNode(a.data.needs_zain)));
    });
    if (!nz.childNodes.length) nz.appendChild(el("p", "empty", "Nothing is waiting on you."));
    // agents
    var g = $("agents"); g.textContent = "";
    agents.sort(function (a, b) { return String(a.agent).localeCompare(String(b.agent)); }).forEach(function (a) {
      var c = el("article", "hcard"); c.setAttribute("data-s", a.status || "Idle");
      add(c, add(el("div", "row"), add(el("div"), el("h3", null, a.agent || a.ref), el("div", "muted", a.title || "")), pill(a.status || "Idle")));
      if (a.data.now) c.appendChild(el("p", "txt", a.data.now));
      c.appendChild(kv([["Last run", a.at ? fmt(a.at, true) : ""], ["Result", a.data.last_result], ["Next run", a.data.next_run ? fmt(a.data.next_run, true) : ""],
        ["Schedule", a.data.schedule], ["Next", a.data.next_steps]]));
      if (a.data.needs_zain) c.appendChild(add(el("div", "need"), el("b", null, "Needs you: "), document.createTextNode(a.data.needs_zain)));
      c.appendChild(commentBox(a.id));
      g.appendChild(c);
    });
    // ideas
    var chips = $("ideaChips"); chips.textContent = "";
    ["new", "approved", "done", "declined", "all"].forEach(function (s) {
      var n = s === "all" ? ideas.length : ideas.filter(function (i) { return i.status === s; }).length;
      var b = el("button", "chip", s + " (" + n + ")"); b.type = "button"; b.setAttribute("aria-pressed", String(boardFilter === s));
      b.addEventListener("click", function () { boardFilter = s; R.board(d); });
      chips.appendChild(b);
    });
    var il = $("ideas"); il.textContent = "";
    var shown = ideas.filter(function (i) { return boardFilter === "all" || i.status === boardFilter; }).sort(function (a, b) { return String(b.at).localeCompare(String(a.at)); });
    if (!shown.length) il.appendChild(el("p", "empty", "No ideas with this status."));
    shown.forEach(function (i) {
      var c = el("article", "hcard"); c.setAttribute("data-s", i.status || "new");
      add(c, add(el("div", "row"), el("span", "muted", (i.agent || "") + " · " + fmt(i.at)), pill(i.status)), el("h3", null, i.title || ""));
      if (i.data.why) c.appendChild(el("p", "txt", i.data.why));
      c.appendChild(kv([["Upside", i.data.upside], ["Cost", i.data.cost], ["Effort", i.data.effort], ["Owner", i.data.owner],
        ["Progress", i.data.progress ? String(i.data.progress).replace(/_/g, " ") + (i.data.progress_note ? ": " + i.data.progress_note : "") : ""]]));
      c.appendChild(commentBox(i.id));
      il.appendChild(c);
    });
    // activity
    var al = $("activity"); al.textContent = "";
    if (!acts.length) al.appendChild(el("p", "empty", "No activity in the last 30 days."));
    acts.slice(0, 60).forEach(function (e) {
      var c = add(el("article", "hcard"), add(el("div", "row"), el("b", null, e.agent || ""), el("span", "muted", fmt(e.at, true))), el("p", "txt", e.title || ""));
      c.appendChild(commentBox(e.id));
      al.appendChild(c);
    });
  };

  var cal = { view: "month", month: todayET().slice(0, 7), day: null };
  var sv = null;
  try { sv = localStorage.getItem("mfa-hub-cal-view"); } catch (e) {}
  if (sv === "list" || sv === "month") cal.view = sv;
  else if (window.matchMedia && window.matchMedia("(max-width:600px)").matches) cal.view = "list";
  function calCard(i) {
    var c = el("article", "hcard"); c.setAttribute("data-s", i.status || "");
    add(c, add(el("div", "row"), el("span", "muted", fmt(i.date) + " · " + (i.time_tbc || !i.time ? "time TBC" : i.time + " ET") + " · " + (i.platform || "")), pill(i.status)),
      el("h3", null, i.title || "(untitled)"));
    var m = el("div", "metrics");
    [["Impressions", i.impressions], ["Clicks", i.clicks], ["Engagements", i.engagements], ["Leads", i.leads]].forEach(function (p) {
      add(m, add(el("span"), document.createTextNode(p[0] + " "), el("b", null, n0(p[1]))));
    });
    c.appendChild(m);
    c.appendChild(kv([["Agent", i.agent], ["Note", i.note], ["Source", i.source]]));
    var l = safeLink(i.link, "Open the post"); if (l) c.appendChild(l);
    c.appendChild(commentBox(i.id));
    return c;
  }
  R.calendar = function (d) {
    var items = d.items || [];
    var byDay = {}; items.forEach(function (i) { (byDay[i.date] = byDay[i.date] || []).push(i); });
    $("vMonth").setAttribute("aria-pressed", String(cal.view === "month"));
    $("vList").setAttribute("aria-pressed", String(cal.view === "list"));
    $("monthBox").hidden = cal.view !== "month";
    var out = $("calItems"); out.textContent = "";
    if (cal.view === "month") {
      var y = +cal.month.slice(0, 4), mo = +cal.month.slice(5, 7) - 1;
      $("monthLabel").textContent = new Date(Date.UTC(y, mo, 15)).toLocaleDateString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
      var g = $("calGrid"); g.textContent = "";
      ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].forEach(function (w) { g.appendChild(el("div", "dow", w)); });
      var first = new Date(Date.UTC(y, mo, 1)), start = addDays(first.toISOString().slice(0, 10), -first.getUTCDay()), today = todayET();
      for (var k = 0; k < 42; k++) {
        var ymd = addDays(start, k), list = byDay[ymd] || [];
        var b = el("button", "day" + (ymd.slice(0, 7) !== cal.month ? " out" : "") + (ymd === today ? " today" : "")); b.type = "button";
        b.setAttribute("aria-pressed", String(cal.day === ymd)); b.setAttribute("aria-label", fmt(ymd) + ": " + list.length + " item(s)");
        var dots = el("span", "dots"); list.slice(0, 8).forEach(function (i) { dots.appendChild(el("span", "dot " + (i.status === "published" ? "published" : ""))); });
        add(b, el("span", "dn", String(+ymd.slice(8))), dots, list.length ? el("span", "cnt", list.length + " item" + (list.length > 1 ? "s" : "")) : null);
        (function (day) { b.addEventListener("click", function () { cal.day = cal.day === day ? null : day; R.calendar(d); }); })(ymd);
        g.appendChild(b);
        if (k === 34 && addDays(start, 35).slice(0, 7) !== cal.month) break;
      }
      var sel = cal.day ? (byDay[cal.day] || []) : items.filter(function (i) { return i.date.slice(0, 7) === cal.month; });
      $("calListHead").textContent = cal.day ? fmt(cal.day) + " (" + sel.length + ")" : "All of " + $("monthLabel").textContent + " (" + sel.length + ")";
      sel.forEach(function (i) { out.appendChild(calCard(i)); });
    } else {
      var from = addDays(todayET(), -7), up = items.filter(function (i) { return i.date >= from; });
      $("calListHead").textContent = "From " + fmt(from) + " on (" + up.length + ")";
      up.forEach(function (i) { out.appendChild(calCard(i)); });
    }
    if (!out.childNodes.length) out.appendChild(el("p", "empty", "Nothing on the calendar here."));
  };

  R.ads = function (d) {
    var rows = d.rows || [], today = todayET(), from7 = addDays(today, -6);
    var plats = {};
    rows.forEach(function (r) { var p = plats[r.platform] = plats[r.platform] || { name: r.platform, daily: [], windows: [], latest: null }; (r.window_days > 1 ? p.windows : p.daily).push(r); if (r.window_days === 1 && (!p.latest || r.date > p.latest)) p.latest = r.date; });
    function sum(list) { return list.reduce(function (s, r) { s.i += r.impressions || 0; s.c += r.clicks || 0; s.s += r.spend || 0; s.v += r.conversions || 0; s.hasV = s.hasV || r.conversions !== null; return s; }, { i: 0, c: 0, s: 0, v: 0, hasV: false }); }
    var tb = $("adsBody"); tb.textContent = "";
    var tot = { i: 0, c: 0, s: 0 };
    Object.keys(plats).sort().forEach(function (k) {
      var p = plats[k];
      var td = sum(p.daily.filter(function (r) { return r.date === today; }));
      var d7list = p.daily.filter(function (r) { return r.date >= from7 && r.date <= today; });
      var note = "";
      if (!d7list.length && p.windows.length) {
        var w = p.windows.slice().sort(function (a, b) { return b.date.localeCompare(a.date); })[0];
        d7list = [w]; note = "7-day total to " + fmt(w.date);
      }
      var s7 = sum(d7list); tot.i += s7.i; tot.c += s7.c; tot.s += s7.s;
      var tr = el("tr");
      var name = el("td"); add(name, el("b", null, p.name), el("div", "muted", note || (p.latest ? "Latest day " + fmt(p.latest) : "")));
      add(tr, name, el("td", "num", p.daily.some(function (r) { return r.date === today; }) ? n0(td.i) + " / " + n0(td.c) : "—"),
        el("td", "num", n0(s7.i)), el("td", "num", n0(s7.c)), el("td", "num", s7.i ? (100 * s7.c / s7.i).toFixed(1) + "%" : "—"),
        el("td", "num", money(s7.s)), el("td", "num", s7.c && s7.s ? money(s7.s / s7.c) : "—"), el("td", "num", s7.hasV ? n0(s7.v) : "—"));
      tb.appendChild(tr);
      var cr = el("tr"); var cc = el("td"); cc.colSpan = 8; cc.appendChild(commentBox("platform:" + p.name.replace(/[^A-Za-z0-9]+/g, "-"))); cr.appendChild(cc); tb.appendChild(cr);
    });
    $("kImp").textContent = n0(tot.i); $("kClk").textContent = n0(tot.c); $("kSp").textContent = money(tot.s);
    var db = $("dailyBody"); db.textContent = "";
    rows.filter(function (r) { return r.window_days === 1 && r.date >= addDays(today, -13); }).forEach(function (r) {
      add(db, add(el("tr"), el("td", null, fmt(r.date)), el("td", null, r.platform), el("td", null, r.campaign), el("td", "num", n0(r.impressions)), el("td", "num", n0(r.clicks)),
        el("td", "num", money(r.spend)), el("td", "num", n0(r.conversions))));
    });
    if (!rows.length) status("No ads data yet. The analytics task fills this 3 times a day.");
  };

  var finFilter = "open";
  R.finance = function (d) {
    var items = d.items || [];
    var groups = { open: ["open"], mine: ["new", "seen", "done"], all: null };
    var chips = $("finChips"); chips.textContent = "";
    [["open", "Waiting for you"], ["mine", "Answered here"], ["all", "All"]].forEach(function (g) {
      var n = items.filter(function (i) { return !groups[g[0]] || groups[g[0]].indexOf(i.status) >= 0; }).length;
      var b = el("button", "chip", g[1] + " (" + n + ")"); b.type = "button"; b.setAttribute("aria-pressed", String(finFilter === g[0]));
      b.addEventListener("click", function () { finFilter = g[0]; R.finance(d); }); chips.appendChild(b);
    });
    var box = $("fin"); box.textContent = "";
    var shown = items.filter(function (i) { return !groups[finFilter] || groups[finFilter].indexOf(i.status) >= 0; });
    if (!shown.length) box.appendChild(el("p", "empty", "No questions here."));
    shown.forEach(function (q) {
      var c = el("article", "hcard"); c.setAttribute("data-s", q.status);
      add(c, add(el("div", "row"), el("span", "muted", "Added " + fmt(q.created_at)), pill(q.status)), el("p", "txt", q.question));
      if (q.suggested_answer) c.appendChild(add(el("div", "need"), el("b", null, "Suggested: "), document.createTextNode(q.suggested_answer)));
      if (q.zain_answer) c.appendChild(kv([["Your answer", q.zain_answer], ["Answered", q.answered_at ? fmt(q.answered_at, true) : ""], ["Agent", q.agent_note]]));
      var ta = el("textarea"); ta.maxLength = 2000; ta.rows = 2; ta.setAttribute("aria-label", "Your answer"); ta.placeholder = "Your answer, e.g. Business · Meals (50% Deductible) · client lunch with …";
      var useS = el("button", "chip", "Use suggestion"); useS.type = "button";
      useS.addEventListener("click", function () { ta.value = String(q.suggested_answer || "").replace(/\s*\((High|Med|Low) confidence\)$/, ""); ta.focus(); });
      var pers = el("button", "chip", "Personal"); pers.type = "button";
      pers.addEventListener("click", function () { ta.value = "Personal · Owner's Draws"; ta.focus(); });
      var save = el("button", "hbtn gold", q.zain_answer ? "Update answer" : "Save answer"); save.type = "button";
      var msg = el("span", "sent");
      save.addEventListener("click", function () {
        var a = ta.value.trim(); if (!a) { msg.className = "sent err"; msg.textContent = "Write an answer first."; return; }
        save.disabled = true; msg.className = "sent"; msg.textContent = "Sending…";
        post("/api/hub/finance-answer", { id: q.id, answer: a }).then(function (j) {
          q.status = j.question.status; q.zain_answer = j.question.zain_answer; q.answered_at = j.question.answered_at; q.agent_note = null;
          msg.textContent = "Sent ✓ Finance picks it up on its next run."; save.textContent = "Update answer";
        }).catch(function (e) { msg.className = "sent err"; msg.textContent = "Not sent (" + e.message + "). Try again."; })
          .then(function () { save.disabled = false; });
      });
      add(c, add(el("div", "cbox"), add(el("div", "chips"), useS, pers), ta, add(el("div", "acts"), save, msg)), commentBox(q.id));
      box.appendChild(c);
    });
  };

  // ---------- boot ----------
  function load() {
    status("Loading…");
    getData(PAGE).then(function (d) {
      indexComments(d.comments);
      R[PAGE](d);
      status("Updated " + new Date().toLocaleTimeString("en-US", { timeZone: TZ, hour: "numeric", minute: "2-digit" }) + " ET");
      window.__hubData = d;
    }).catch(function (e) { status("Couldn't load (" + e.message + "). Refresh the page; if it keeps failing, sign in again.", true); });
  }
  if (PAGE === "calendar") {
    function setView(v) { cal.view = v; try { localStorage.setItem("mfa-hub-cal-view", v); } catch (e) {} if (window.__hubData) R.calendar(window.__hubData); }
    $("vMonth").addEventListener("click", function () { setView("month"); });
    $("vList").addEventListener("click", function () { setView("list"); });
    function shift(n) { var y = +cal.month.slice(0, 4), m = +cal.month.slice(5, 7) - 1 + n; var d = new Date(Date.UTC(y, m, 1)); cal.month = d.toISOString().slice(0, 7); cal.day = null; if (window.__hubData) R.calendar(window.__hubData); }
    $("prevM").addEventListener("click", function () { shift(-1); });
    $("nextM").addEventListener("click", function () { shift(1); });
  }
  var rf = $("refresh"); if (rf) rf.addEventListener("click", load);
  if (R[PAGE]) load();
})();
