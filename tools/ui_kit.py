"""Shared UI kit for MFA pages built by build_blog.py and build_landing.py.

FAQ accordions (same look as the homepage: hairline rows, gold plus that turns into a minus),
scroll reveal, staggered hero entrance, hover lift, sticky-header shadow and a reading-progress
bar on articles. Everything degrades gracefully:
  - without JavaScript every FAQ answer is visible and nothing is hidden;
  - with prefers-reduced-motion the page is static.
Standard library only. The JS contains no % signs, so it is safe inside %-formatted templates.
"""
import html as _html
import re

UI_CSS = r"""
/* ---------- MFA UI kit (tools/ui_kit.py) ---------- */
:root{--ui-ease:cubic-bezier(.16,1,.3,1)}
/* FAQ accordion */
.faqs{margin:56px 0 8px}
.faq-l{border-top:1px solid var(--hair);margin:8px 0 0}
.faq-i{border-bottom:1px solid var(--hair)}
.faq-h{margin:0!important;font:inherit!important}
.faq-q{width:100%;display:flex;align-items:center;justify-content:space-between;gap:22px;background:none;border:0;
  text-align:left;cursor:pointer;padding:22px 4px;font-family:'Cormorant Garamond',Georgia,serif;font-size:1.32rem;
  font-weight:500;line-height:1.3;color:var(--ink);transition:padding-left .45s var(--ui-ease),color .35s}
.faq-q:hover,.faq-i.open .faq-q{color:var(--gold)}
.faq-q:hover{padding-left:12px}
.faq-q:focus-visible{outline:2px solid var(--gold);outline-offset:3px;border-radius:4px}
.faq-pm{position:relative;width:14px;height:14px;flex-shrink:0}
.faq-pm::before,.faq-pm::after{content:"";position:absolute;background:var(--gold);transition:transform .45s var(--ui-ease)}
.faq-pm::before{top:6.25px;left:0;width:14px;height:1.5px}
.faq-pm::after{left:6.25px;top:0;width:1.5px;height:14px}
.faq-i.open .faq-pm::after{transform:rotate(90deg) scaleX(0)}
.faq-a-in{padding:0 40px 24px 4px}
.faq-a-in p{margin:0!important;color:var(--muted);line-height:1.8}
.js .faq-a{max-height:0;overflow:hidden;transition:max-height .55s var(--ui-ease)}
.js .faq-a-in{opacity:0;transform:translateY(-6px);transition:opacity .45s var(--ui-ease),transform .45s var(--ui-ease)}
.js .faq-i.open .faq-a-in{opacity:1;transform:none}
/* Scroll reveal (only when JS is running) */
.js .rv{opacity:0;transform:translateY(26px);transition:opacity .9s var(--ui-ease),transform .9s var(--ui-ease)}
.js .rv.in{opacity:1;transform:none}
/* Hero entrance */
@keyframes uiUp{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}
.ahead .wrap>*,.bhero .wrap>*,.hero-g>div:first-child>*,.hero-g>.hero-card{animation:uiUp .95s var(--ui-ease) both}
.ahead .wrap>:nth-child(2),.bhero .wrap>:nth-child(2),.hero-g>div:first-child>:nth-child(2){animation-delay:.08s}
.ahead .wrap>:nth-child(3),.bhero .wrap>:nth-child(3),.hero-g>div:first-child>:nth-child(3){animation-delay:.16s}
.ahead .wrap>:nth-child(4),.bhero .wrap>:nth-child(4),.hero-g>div:first-child>:nth-child(4){animation-delay:.24s}
.ahead .wrap>:nth-child(n+5),.bhero .wrap>:nth-child(n+5),.hero-g>div:first-child>:nth-child(n+5){animation-delay:.32s}
.hero-g>.hero-card{animation-delay:.22s}
/* Hover lift */
.btn{transition:background .3s,color .3s,border-color .3s,transform .35s var(--ui-ease),box-shadow .35s var(--ui-ease)}
.btn:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(16,35,63,.16)}
.btn:active{transform:translateY(0);box-shadow:none}
.card,.rev,.step,.why>div{transition:transform .5s var(--ui-ease),box-shadow .5s var(--ui-ease),border-color .3s}
.card:hover,.rev:hover,.step:hover,.why>div:hover{transform:translateY(-4px);box-shadow:0 18px 40px rgba(16,35,63,.10)}
.figure img{transition:transform 1.1s var(--ui-ease)}
.figure:hover img{transform:scale(1.015)}
.tbl tr{transition:background .25s}
.tbl tbody tr:hover{background:rgba(216,183,105,.10)}
/* Sticky header shadow */
.bnav,.top{transition:box-shadow .4s var(--ui-ease),background .4s}
.bnav.scrolled,.top.scrolled{box-shadow:0 8px 28px rgba(16,35,63,.08)}
/* Reading progress (articles) */
.rprog{position:fixed;top:0;left:0;height:3px;width:100%;background:linear-gradient(90deg,var(--gold),var(--gold-b));
  transform-origin:0 50%;transform:scaleX(0);z-index:100;pointer-events:none}
/* Related links strip above the footer (tool pages; tools/seo.py related_html) */
.relnav{border-top:1px solid var(--hair);background:var(--paper-2,#F5F4EF);padding:18px 0}
.relnav .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px}
.relnav span{font-size:10px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);margin-right:6px}
.relnav a{font-size:.86rem;line-height:1.3;padding:7px 13px;border:1px solid var(--hair);border-radius:999px;background:var(--paper);color:var(--ink);text-decoration:none;transition:border-color .3s}
.relnav a:hover{border-color:var(--gold)}
/* Footnotes and disclaimers before the footer (ui_kit.fineprint). They never sit on the footer line:
   the last section of <main> keeps 64px+ above the footer, and a stand-alone footnote gets 48px above it. */
main>.llc-sec:last-child{padding-bottom:72px}
main>.tinfo:last-child{padding-bottom:40px}
.fineprint{padding-top:48px!important;padding-bottom:72px}
.cta-block+.fineprint{padding-top:0!important}
.fineprint .disclaimer{margin:0!important;max-width:860px;line-height:1.7}
/* Add-to-calendar menu */
.kd-add{position:relative;display:inline-block}
.kd-add>summary{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:7px;white-space:nowrap}
.kd-add>summary::-webkit-details-marker{display:none}
.kd-add:not(.kd-sub)>summary{font-size:.78rem;font-weight:600;color:var(--navy);padding:7px 12px;border:1px solid rgba(176,141,63,.45);border-radius:999px;transition:background .3s,border-color .3s,color .3s}
.kd-add:not(.kd-sub)>summary:hover,.kd-add[open]:not(.kd-sub)>summary{background:var(--navy);border-color:var(--navy);color:#fff}
.kd-add summary svg{width:14px;height:14px;flex:none}
.kd-menu{position:absolute;right:0;top:calc(100% + 8px);z-index:40;min-width:230px;background:#fff;border:1px solid var(--hair);border-radius:12px;
  box-shadow:0 18px 44px rgba(16,35,63,.16);padding:6px;display:flex;flex-direction:column;animation:uiMenu .28s var(--ui-ease) both}
.kd-sub .kd-menu{left:0;right:auto}
.kd-menu a{display:block;padding:10px 14px;border-radius:8px;font-size:.88rem;font-weight:500;color:var(--ink)!important;border:0!important;text-decoration:none;white-space:nowrap}
.kd-menu a:hover{background:var(--paper-2,#F5F4EF);color:var(--navy)!important}
@keyframes uiMenu{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
@media (max-width:560px){.kd-menu{left:0;right:auto}.kd-sub{width:100%}.kd-sub>summary{width:100%;justify-content:center}}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
  .js .rv{opacity:1;transform:none}
  .js .faq-a-in{opacity:1;transform:none}
}
"""

UI_JS = r"""<script>
(function(){
  var d=document, root=d.documentElement; root.classList.add('js');
  var still=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  /* FAQ accordion */
  d.querySelectorAll('.faq-i').forEach(function(it){
    var q=it.querySelector('.faq-q'), a=it.querySelector('.faq-a'); if(!q||!a||q._ui)return; q._ui=1;
    q.addEventListener('click',function(){
      var open=!it.classList.contains('open');
      it.classList.toggle('open',open); q.setAttribute('aria-expanded',open?'true':'false');
      if(open){a.style.maxHeight=a.scrollHeight+'px';
        a.addEventListener('transitionend',function f(e){if(e.propertyName==='max-height'&&it.classList.contains('open'))a.style.maxHeight='none';a.removeEventListener('transitionend',f);});
        if(window.gtag)try{gtag('event','faq_open',{question:q.textContent.trim().slice(0,90)});}catch(e){}
      }else{a.style.maxHeight=a.scrollHeight+'px';a.offsetHeight;a.style.maxHeight='0px';}
    });
  });
  /* Open the FAQ a link points at (e.g. #faq-2) */
  if(location.hash){var t=d.querySelector(location.hash);var it=t&&t.closest&&t.closest('.faq-i');if(it&&!it.classList.contains('open'))it.querySelector('.faq-q').click();}
  /* Scroll reveal */
  var sel=['.article>h2','.article>figure','.article>.tldr','.article>table','.article>section','.article>div:not(.share)',
    '.pcard','.cta-card','.sec-hd','.card','.step','.why>div','.rev','.book-frame','.faq-l','.final .wrap','.nl-wrap','.alist li'];
  var els=[].slice.call(d.querySelectorAll(sel.join(',')));
  if(!still&&'IntersectionObserver' in window){
    els.forEach(function(el){
      el.classList.add('rv');
      var p=el.parentElement, sib=p?[].slice.call(p.children).filter(function(c){return c.classList.contains('rv');}):[];
      var i=sib.indexOf(el); if(sib.length>1&&i>0)el.style.transitionDelay=Math.min(i%4,3)*90+'ms';
    });
    var io=new IntersectionObserver(function(en){en.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{rootMargin:'0px 0px -8% 0px',threshold:.06});
    els.forEach(function(el){io.observe(el);});
    setTimeout(function(){els.forEach(function(el){el.classList.add('in');});},4000);   /* safety net */
  }
  /* Calendar menus: close on outside click / Esc, one open at a time, copy-link item */
  var menus=[].slice.call(d.querySelectorAll('details.kd-add'));
  menus.forEach(function(m){m.addEventListener('toggle',function(){if(m.open)menus.forEach(function(o){if(o!==m)o.open=false;});});});
  d.addEventListener('click',function(e){menus.forEach(function(m){if(m.open&&!m.contains(e.target))m.open=false;});
    var c=e.target.closest&&e.target.closest('a[data-copy]');
    if(c&&navigator.clipboard){e.preventDefault();navigator.clipboard.writeText(c.href).then(function(){var t=c.textContent;c.textContent='Link copied';setTimeout(function(){c.textContent=t;},2000);});}
  });
  d.addEventListener('keydown',function(e){if(e.key==='Escape')menus.forEach(function(m){m.open=false;});});
  /* Header shadow + reading progress */
  var hd=d.querySelector('.bnav,.top'), art=d.querySelector('.article'), bar=null;
  if(art&&d.querySelector('.ahead')){bar=d.createElement('div');bar.className='rprog';bar.setAttribute('aria-hidden','true');d.body.appendChild(bar);}
  var tick=false;
  function upd(){tick=false; var y=window.scrollY||root.scrollTop;
    if(hd)hd.classList.toggle('scrolled',y>8);
    if(bar){var r=art.getBoundingClientRect(), h=art.offsetHeight-window.innerHeight; var p=h>0?Math.min(1,Math.max(0,-r.top/h)):0; bar.style.transform='scaleX('+p+')';}
  }
  window.addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(upd);}},{passive:true});
  upd();
})();
</script>"""


# ---------------------------------------------------------------- header menus (Zain, 2026-10-24)
# "Add a dropdown menu for the buttons, like Resources has a dropdown page, so does Services, so people can
# jump to where they need to go." One source for every header on the site: build_blog.nav() (blog, resources,
# tools, services, shop, book, LLC pages, legal pages) and the hand-built home page (synced between
# <!--nav:...--> markers by build_blog.sync_home_nav()). Every link must exist: check_ui.py checks them.
# Item: (key, label, href, [(column heading, [(label, href), ...]), ...], (footer label, href) or None)
NAV = [
    ("s", "Services", "/services/", [
        ("What we do", [("Tax preparation & 1099 filing", "/services/#tax-preparation"),
                        ("Tax planning & strategy", "/services/#tax-planning"),
                        ("Bookkeeping & accounting", "/services/#bookkeeping"),
                        ("Financial reporting", "/services/#financial-reporting"),
                        ("Fractional CFO", "/services/#fractional-cfo"),
                        ("Audit support & controls", "/services/#audit-support"),
                        ("Technical accounting", "/services/#technical-accounting"),
                        ("Systems & business advisory", "/services/#business-advisory")]),
        ("Get started", [("LLC formation, all 50 states", "/llc-formation/"),
                         ("Monthly bookkeeping", "/llc-formation/#monthly"),
                         ("Bookkeeping cleanup & catch-up", "/bookkeeping-cleanup/"),
                         ("LLC costs by state", "/llc-formation/#states")]),
        ("By location", [("Princeton, NJ", "/princeton-nj/"), ("Union City, NJ", "/union-city-nj/"),
                         ("New York City", "/new-york-ny/")]),
    ], ("All services", "/services/")),
    ("res", "Resources", "/resources/", [
        ("Browse by type", [("Checkers", "/resources/#checkers"), ("Calculators", "/resources/#calculators"),
                            ("Tax calculators", "/resources/#taxcalcs"), ("Calendars", "/resources/#calendars"),
                            ("Templates & checklists", "/resources/#templates"), ("Guides", "/resources/#guides"),
                            ("State directory", "/resources/#states")]),
        ("Popular tools", [("Quarterly estimated tax calculator", "/tools/quarterly-estimated-tax-calculator/"),
                           ("1099 tax calculator", "/tools/1099-tax-calculator/"),
                           ("Paycheck tax calculator", "/tools/paycheck-tax-calculator/"),
                           ("Is It Deductible?", "/tools/is-it-deductible/"),
                           ("Do I need to send a 1099?", "/tools/do-i-need-to-send-a-1099/"),
                           ("2027 business tax deadlines", "/tools/tax-deadlines-2027/")]),
    ], ("All resources", "/resources/")),
    ("shop", "Shop", "/shop/", [
        ("Shop by type", [("Tax calculator spreadsheets", "/shop/#calc"), ("Checklists & kits", "/shop/#kit"),
                          ("AI prompt packs", "/shop/#ai"), ("Done-for-you services", "/shop/#services")]),
    ], ("Visit the shop", "/shop/")),
    ("blog", "Insights", "/blog/", [
        ("Read", [("All articles", "/blog/"), ("2027 tax calendar", "/blog/2027-tax-calendar/"),
                  ("Which tax form for your LLC?", "/blog/which-tax-form-llc-corporation/"),
                  ("Form 1099 guide for 2026", "/blog/form-1099-preparation-guide-2026/")]),
        ("Stay current", [("Newsletter", "/newsletter/"), ("Key-dates calendar", "/newsletter/#calendar"),
                          ("About Zain Merchant", "/authors/zain-merchant/")]),
    ], ("All articles", "/blog/")),
    ("b", "Book", "/book/", [], None),
]
HOME_EXTRA = {"s": ("Approach", "#approach"), "res": ("Reviews", "#reviews")}   # home-page anchors placed before these
_CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
_BURGER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>'
_e = lambda s: _html.escape(s, quote=True)


def _conv(href):
    return ' data-conv="book"' if href == "/book/" else ""


def nav_links(active="", home=False):
    """Desktop header links: a plain link per item, plus a chevron button and a dropdown panel where the item has groups."""
    out = []
    for key, label, href, cols, foot in NAV:
        if home and key in HOME_EXTRA:
            out.append(f'<a href="{HOME_EXTRA[key][1]}">{HOME_EXTRA[key][0]}</a>')
        on = ' class="on"' if key == active else ""
        if not cols:
            out.append(f'<a href="{href}"{on}{_conv(href)}>{label}</a>')
            continue
        pid = "dd-" + label.lower()
        body = "".join(f'<div class="dd-col"><span class="dd-h">{_e(h)}</span><ul>'
                       + "".join(f'<li><a href="{u}">{_e(t)}<i aria-hidden="true">→</i></a></li>' for t, u in links)
                       + '</ul></div>' for h, links in cols)
        ft = (f'<div class="dd-ft"><a class="dd-all" href="{foot[1]}">{_e(foot[0])} <i aria-hidden="true">→</i></a>'
              f'<a class="dd-book" href="/book/" data-conv="book">Book a consultation</a></div>') if foot else ""
        out.append(f'<div class="dd" data-dd><a href="{href}" class="dd-a{" on" if key == active else ""}">{label}</a>'
                   f'<button class="dd-t" type="button" aria-expanded="false" aria-controls="{pid}" aria-label="Show {label} links">{_CHEV}</button>'
                   f'<div class="dd-p" id="{pid}"><div class="dd-box"><div class="dd-cols">{body}</div>{ft}</div></div></div>')
    return "".join(out)


def nav_mobile(active="", home=False):
    """The same groups for phones: each item with sub-pages is an expandable row (gold plus that turns into a minus)."""
    rows = []
    for key, label, href, cols, foot in NAV:
        if home and key in HOME_EXTRA:
            rows.append(f'<li><a class="mg-a" href="{HOME_EXTRA[key][1]}">{HOME_EXTRA[key][0]}</a></li>')
        on = " on" if key == active else ""
        if key == "b" and home:
            continue   # the home sheet ends with its own "Book a Consultation" link
        if not cols:
            rows.append(f'<li><a class="mg-a{on}" href="{href}"{_conv(href)}>{label}</a></li>')
            continue
        pid = "mg-" + label.lower()
        inner = "".join(f'<div class="mg-col"><span class="mg-h">{_e(h)}</span>'
                        + "".join(f'<a href="{u}">{_e(t)}</a>' for t, u in links) + '</div>' for h, links in cols)
        if foot:
            inner += f'<div class="mg-col"><a class="mg-all" href="{foot[1]}">{_e(foot[0])} →</a></div>'
        rows.append(f'<li class="mg"><div class="mg-row"><a class="mg-a{on}" href="{href}">{label}</a>'
                    f'<button class="mg-t" type="button" aria-expanded="false" aria-controls="{pid}" aria-label="Show {label} links">'
                    f'<span class="mg-pm" aria-hidden="true"></span></button></div>'
                    f'<div class="mg-p" id="{pid}"><div class="mg-in">{inner}</div></div></li>')
    if home:
        rows.append('<li><a class="mg-a" href="#contact">Contact</a></li><li><a class="mg-a" href="/book/" data-conv="book">Book a Consultation</a></li>')
    return f'<ul class="mnav{" mnav-dark" if home else ""}">{"".join(rows)}</ul>'


BURGER_BTN = (f'<button class="bnav-burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="bsheet">'
              f'{_BURGER}</button>')


def mobile_sheet(active=""):
    """Phone menu for the inner-page header (.bnav). Sits after </header> (the header's backdrop-filter would trap a fixed child)."""
    return (f'<div class="bsheet" id="bsheet"><nav aria-label="Menu">{nav_mobile(active)}'
            f'<div class="bsheet-acts"><a class="btn btn-gold" href="/book/" data-conv="book">Book a 30-minute consultation</a>'
            f'<a class="btn btn-line-ink" href="/#contact">Contact us</a>'
            f'<a class="bsheet-tel" href="tel:+13472054468" data-conv="call">(347) 205-4468</a></div></nav></div>')


NAV_CSS = r"""
/* ---------- Header dropdown menus + phone menu (ui_kit.nav_links / nav_mobile) ---------- */
.dd{position:relative;display:flex;align-items:center;gap:3px}
.dd-t{display:inline-grid;place-items:center;width:20px;height:24px;margin-right:-6px;padding:0;border:0;background:none;color:inherit;cursor:pointer;border-radius:5px}
.dd-t svg{width:11px;height:11px;transition:transform .4s cubic-bezier(.16,1,.3,1)}
.dd.open .dd-t svg{transform:rotate(180deg)}
.dd-t:focus-visible{outline:2px solid #B08D3F;outline-offset:2px}
.dd-p{position:absolute;top:100%;left:50%;transform:translateX(calc(-50% + var(--dx,0px)));padding-top:18px;z-index:60;visibility:hidden;pointer-events:none;transition:visibility 0s .3s}
.dd.open .dd-p{visibility:visible;pointer-events:auto;transition:none}
html:not(.nav-js) .dd:hover .dd-p,html:not(.nav-js) .dd:focus-within .dd-p{visibility:visible;pointer-events:auto}
.dd-box{background:#FDFDFC;border:1px solid rgba(21,21,21,.09);border-top:2px solid #B08D3F;border-radius:14px;padding:20px 20px 14px;text-align:left;
  box-shadow:0 30px 60px -18px rgba(16,35,63,.32),0 6px 16px rgba(16,35,63,.06);opacity:0;transform:translateY(10px);
  transition:opacity .3s cubic-bezier(.16,1,.3,1),transform .5s cubic-bezier(.16,1,.3,1)}
.dd.open .dd-box,html:not(.nav-js) .dd:hover .dd-box,html:not(.nav-js) .dd:focus-within .dd-box{opacity:1;transform:none}
.dd-cols{display:flex;gap:26px}
.dd-col{min-width:200px}
.dd-col ul{list-style:none;margin:0;padding:0}
.dd-h{display:block;font-size:9.5px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:#B08D3F;margin:0 0 8px;padding-left:10px;line-height:1.4}
.dd-col li{opacity:0;transform:translateY(6px);transition:opacity .35s cubic-bezier(.16,1,.3,1),transform .5s cubic-bezier(.16,1,.3,1)}
.dd.open .dd-col li,html:not(.nav-js) .dd-col li{opacity:1;transform:none}
.dd.open .dd-col li:nth-child(2){transition-delay:.03s}.dd.open .dd-col li:nth-child(3){transition-delay:.06s}
.dd.open .dd-col li:nth-child(4){transition-delay:.09s}.dd.open .dd-col li:nth-child(5){transition-delay:.12s}
.dd.open .dd-col li:nth-child(6){transition-delay:.15s}.dd.open .dd-col li:nth-child(n+7){transition-delay:.18s}
.bnav-links .dd-p a,.nav-links .dd-p a{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:8px 10px;border-radius:8px;
  font-family:Inter,system-ui,sans-serif;font-size:13.5px;font-weight:500;letter-spacing:0;text-transform:none;line-height:1.35;white-space:nowrap;
  color:#10233F!important;opacity:1!important;transition:background .25s,padding .4s cubic-bezier(.16,1,.3,1)}
.bnav-links .dd-p a::after,.nav-links .dd-p a::after{display:none!important}
.bnav-links .dd-p li a:hover,.nav-links .dd-p li a:hover,.dd-p li a:focus-visible{background:#F5F4EF;padding-left:14px}
.dd-p a i{font-style:normal;color:#B08D3F;opacity:0;transform:translateX(-6px);transition:opacity .25s,transform .35s cubic-bezier(.16,1,.3,1)}
.dd-p a:hover i,.dd-p a:focus-visible i{opacity:1;transform:none}
.dd-p a:focus-visible{outline:2px solid #B08D3F;outline-offset:0}
.dd-ft{display:flex;align-items:center;justify-content:space-between;gap:18px;margin:12px 0 0;padding:12px 0 0;border-top:1px solid rgba(21,21,21,.08)}
.bnav-links .dd-ft a,.nav-links .dd-ft a{font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;padding:6px 10px}
.bnav-links .dd-ft a.dd-book,.nav-links .dd-ft a.dd-book{color:#B08D3F!important}
.dd-ft a.dd-all i{opacity:1;transform:none}
.bnav-links .dd-ft a:hover,.nav-links .dd-ft a:hover{background:#F5F4EF}
.bnav-burger{display:none;place-items:center;width:42px;height:42px;padding:0;border:1px solid rgba(21,21,21,.16);border-radius:999px;background:none;color:#151515;cursor:pointer;transition:background .3s,color .3s}
.bnav-burger svg{width:18px;height:18px;display:block}
.bnav-burger[aria-expanded="true"]{background:#10233F;border-color:#10233F;color:#fff}
.bnav-burger:focus-visible{outline:2px solid #B08D3F;outline-offset:3px}
.bsheet{position:fixed;left:0;right:0;bottom:0;top:var(--sheet-top,78px);z-index:49;overflow-y:auto;overscroll-behavior:contain;background:#FDFDFC;
  padding:6px 28px 48px;opacity:0;visibility:hidden;transform:translateY(-8px);
  transition:opacity .35s cubic-bezier(.16,1,.3,1),transform .5s cubic-bezier(.16,1,.3,1),visibility 0s .5s}
.bsheet.open{opacity:1;visibility:visible;transform:none;transition:opacity .35s cubic-bezier(.16,1,.3,1),transform .5s cubic-bezier(.16,1,.3,1)}
.bsheet>nav{max-width:560px;margin:0 auto}
.bsheet-acts{display:flex;flex-direction:column;gap:10px;margin-top:26px}
.bsheet-acts .btn{justify-content:center}
.bsheet-tel{align-self:center;margin-top:6px;font-weight:600;color:#10233F;border-bottom:1px solid rgba(176,141,63,.5)}
@media (max-width:1080px){.bnav-links{gap:24px!important}}
@media (max-width:1000px){.bnav-links{gap:17px!important}}
@media (max-width:940px){.bnav-links{gap:11px!important}}
.bnav .brand{flex-shrink:0}.bnav .brand-txt i{white-space:nowrap}
@media (max-width:860px){.bnav-links .dd{display:none!important}.bnav-burger{display:inline-grid}.bnav-links{gap:8px!important}}
@media (min-width:861px){.bsheet{display:none}}
@media (max-width:480px){.bnav-links a.cta{width:42px;height:42px;padding:0!important;justify-content:center}
  .bnav-links a.cta span{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
.mnav{list-style:none;margin:0;padding:0}
.mnav>li{border-bottom:1px solid rgba(21,21,21,.09)}
.mg-row{display:flex;align-items:center;justify-content:space-between;gap:12px}
.mnav .mg-a{flex:1;display:block;padding:15px 2px;font-family:'Cormorant Garamond',Georgia,serif;font-size:1.6rem;font-weight:500;line-height:1.2;color:#10233F;opacity:1;transform:none}
.mnav .mg-a.on{color:#B08D3F}
.mg-t{flex-shrink:0;display:grid;place-items:center;width:44px;height:44px;padding:0;border:0;border-radius:8px;background:none;cursor:pointer}
.mg-t:focus-visible{outline:2px solid #B08D3F;outline-offset:2px}
.mg-pm{position:relative;width:14px;height:14px}
.mg-pm::before,.mg-pm::after{content:"";position:absolute;background:#B08D3F;transition:transform .45s cubic-bezier(.16,1,.3,1)}
.mg-pm::before{top:6.25px;left:0;width:14px;height:1.5px}
.mg-pm::after{left:6.25px;top:0;width:1.5px;height:14px}
.mg.open .mg-pm::after{transform:rotate(90deg) scaleX(0)}
.mg-p{display:grid;grid-template-rows:0fr;visibility:hidden;transition:grid-template-rows .45s cubic-bezier(.16,1,.3,1),visibility 0s .45s}
.mg.open .mg-p{grid-template-rows:1fr;visibility:visible;transition:grid-template-rows .45s cubic-bezier(.16,1,.3,1)}
.mg-in{overflow:hidden;min-height:0}
.mg-col{padding:0 0 14px}
.mg-h{display:block;margin:2px 0 4px;font-family:Inter,system-ui,sans-serif;font-size:9.5px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:#B08D3F}
.mnav .mg-in a{display:block;padding:10px 0 10px 14px;border-left:1px solid rgba(176,141,63,.35);font-family:Inter,system-ui,sans-serif;font-size:15px;line-height:1.35;color:#151515;transition:color .25s,border-color .25s,padding .35s cubic-bezier(.16,1,.3,1)}
.mnav .mg-in a:hover{color:#B08D3F;border-left-color:#B08D3F;padding-left:18px}
.mnav .mg-in a.mg-all{font-weight:600;color:#10233F;border-left-color:transparent}
.bsheet.open .mnav>li,.msheet.open .mnav>li{animation:mgIn .55s cubic-bezier(.16,1,.3,1) both}
.bsheet.open .mnav>li:nth-child(2),.msheet.open .mnav>li:nth-child(2){animation-delay:.04s}
.bsheet.open .mnav>li:nth-child(3),.msheet.open .mnav>li:nth-child(3){animation-delay:.08s}
.bsheet.open .mnav>li:nth-child(4),.msheet.open .mnav>li:nth-child(4){animation-delay:.12s}
.bsheet.open .mnav>li:nth-child(5),.msheet.open .mnav>li:nth-child(5){animation-delay:.16s}
.bsheet.open .mnav>li:nth-child(n+6),.msheet.open .mnav>li:nth-child(n+6){animation-delay:.2s}
@keyframes mgIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.mnav-dark>li{border-bottom-color:rgba(255,255,255,.12)}
.mnav-dark .mg-a{color:#fff}
.mnav-dark .mg-h{color:#D8B769}
.mnav-dark .mg-pm::before,.mnav-dark .mg-pm::after{background:#D8B769}
.mnav.mnav-dark .mg-in a{color:rgba(255,255,255,.8);border-left-color:rgba(216,183,105,.35)}
.mnav.mnav-dark .mg-in a:hover{color:#D8B769;border-left-color:#D8B769}
.mnav.mnav-dark .mg-in a.mg-all{color:#fff}
body.nav-lock{overflow:hidden}
@media (prefers-reduced-motion:reduce){.dd-box,.dd-col li,.bsheet,.mg-p,.dd-t svg{transition:none!important}.mnav>li{animation:none!important}}
"""

NAV_JS = r"""<script>
(function(){
  var d=document, dds=[].slice.call(d.querySelectorAll('[data-dd]')); d.documentElement.classList.add('nav-js');
  var fine=window.matchMedia&&matchMedia('(hover: hover) and (pointer: fine)').matches;
  function btn(dd){return dd.querySelector('.dd-t');}
  function clamp(dd){var p=dd.querySelector('.dd-p');dd.style.setProperty('--dx','0px');
    var r=p.getBoundingClientRect(),vw=d.documentElement.clientWidth,m=16,dx=0;
    if(r.left<m)dx=m-r.left;else if(r.right>vw-m)dx=vw-m-r.right;
    if(dx)dd.style.setProperty('--dx',Math.round(dx)+'px');}
  function set(dd,v){
    if(v)dds.forEach(function(o){if(o!==dd)set(o,false);});
    if(v&&!dd.classList.contains('open'))clamp(dd);
    dd.classList.toggle('open',v);btn(dd).setAttribute('aria-expanded',v?'true':'false');
  }
  dds.forEach(function(dd){
    var t=btn(dd), a=dd.querySelector('.dd-a'), timer;
    dd.addEventListener('mouseenter',function(){if(!fine)return;clearTimeout(timer);timer=setTimeout(function(){set(dd,true);},60);});
    dd.addEventListener('mouseleave',function(){if(!fine)return;clearTimeout(timer);timer=setTimeout(function(){set(dd,false);},180);});
    t.addEventListener('click',function(e){e.preventDefault();set(dd,!dd.classList.contains('open'));});
    /* touch screens: the first tap on the label opens the menu, which has its own "All ..." link */
    a.addEventListener('click',function(e){if(!fine&&!dd.classList.contains('open')){e.preventDefault();set(dd,true);}});
    t.addEventListener('keydown',function(e){if(e.key==='ArrowDown'){e.preventDefault();set(dd,true);var f=dd.querySelector('.dd-p a');if(f)f.focus();}});
    dd.addEventListener('keydown',function(e){
      if(e.key==='Escape'&&dd.classList.contains('open')){e.stopPropagation();set(dd,false);t.focus();}
      if((e.key==='ArrowDown'||e.key==='ArrowUp')&&e.target.closest('.dd-p')){e.preventDefault();
        var l=[].slice.call(dd.querySelectorAll('.dd-p a')),i=l.indexOf(e.target);
        var n=l[(i+(e.key==='ArrowDown'?1:-1)+l.length)%l.length];if(n)n.focus();}
    });
    dd.addEventListener('focusout',function(e){if(!e.relatedTarget||!dd.contains(e.relatedTarget))set(dd,false);});
  });
  d.addEventListener('click',function(e){dds.forEach(function(dd){if(dd.classList.contains('open')&&!dd.contains(e.target))set(dd,false);});});
  d.addEventListener('keydown',function(e){if(e.key==='Escape')dds.forEach(function(dd){if(dd.classList.contains('open'))set(dd,false);});});
  /* phone menu: expandable groups */
  [].slice.call(d.querySelectorAll('.mg-t')).forEach(function(t){
    t.addEventListener('click',function(){var li=t.closest('.mg'),v=!li.classList.contains('open');
      li.classList.toggle('open',v);t.setAttribute('aria-expanded',v?'true':'false');});
  });
  /* inner-page burger */
  var b=d.querySelector('.bnav-burger'), s=d.getElementById('bsheet'), hd=d.querySelector('.bnav');
  if(b&&s){
    var ico=b.innerHTML, x='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>';
    var open=function(v){
      if(v&&hd)s.style.setProperty('--sheet-top',Math.max(0,Math.round(hd.getBoundingClientRect().bottom))+'px');
      s.classList.toggle('open',v);d.body.classList.toggle('nav-lock',v);
      b.setAttribute('aria-expanded',v?'true':'false');b.setAttribute('aria-label',v?'Close menu':'Open menu');b.innerHTML=v?x:ico;
    };
    b.addEventListener('click',function(){open(!s.classList.contains('open'));});
    s.addEventListener('click',function(e){if(e.target.closest('a'))open(false);});
    d.addEventListener('keydown',function(e){if(e.key==='Escape'&&s.classList.contains('open')){open(false);b.focus();}});
    window.addEventListener('resize',function(){if(window.innerWidth>860&&s.classList.contains('open'))open(false);});
  }
})();
</script>"""

UI_CSS += NAV_CSS
UI_JS += NAV_JS


def _plain(s):
    return _html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def fineprint(text_html):
    """Stand-alone footnote/disclaimer as the last block of <main>: muted italic .disclaimer text with proper
    space above it and above the footer. Use this instead of a bare <section><p class="disclaimer">."""
    return f'<section class="wrap llc-sec fineprint" aria-label="Fine print"><p class="disclaimer">{text_html}</p></section>'


def faq_accordion(pairs, prefix="faq", heading_tag="h3"):
    """pairs: list of (question_html, answer_html). Returns accordion markup.
    Questions stay inside <h3> so search engines still read them as headings."""
    items = []
    for i, (q, a) in enumerate(pairs, 1):
        a_html = a if a.lstrip().startswith("<p") else f"<p>{a}</p>"
        items.append(
            f'<div class="faq-i" id="{prefix}-{i}"><{heading_tag} class="faq-h">'
            f'<button class="faq-q" type="button" aria-expanded="false" aria-controls="{prefix}-a{i}" id="{prefix}-q{i}">'
            f'<span>{q}</span><span class="faq-pm" aria-hidden="true"></span></button></{heading_tag}>'
            f'<div class="faq-a" id="{prefix}-a{i}" role="region" aria-labelledby="{prefix}-q{i}"><div class="faq-a-in">{a_html}</div></div></div>')
    return '<div class="faq-l">' + "".join(items) + "</div>"


FAQ_HEAD_RE = r"<h2>(?:Quick answers|FAQs|Frequently asked questions)</h2>"


def faq_pairs(body):
    """(question, answer) pairs from the article's FAQ section (h3 + p pairs right after the FAQ h2)."""
    m = re.search(FAQ_HEAD_RE + r"\s*((?:<h3>.*?</h3>\s*<p>.*?</p>\s*)+)", body, re.S)
    if not m:
        return []
    return re.findall(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", m.group(1), re.S)


def accordionize_faqs(body):
    """Swap the article's FAQ section (h2 + h3/p pairs) for an accordion. Other content is untouched."""
    m = re.search(FAQ_HEAD_RE + r"\s*((?:<h3>.*?</h3>\s*<p>.*?</p>\s*)+)", body, re.S)
    if not m:
        return body
    pairs = re.findall(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", m.group(1), re.S)
    block = f'<section class="faqs" id="faqs"><h2>FAQs</h2>{faq_accordion(pairs)}</section>\n\n'
    return body[:m.start()] + block + body[m.end():]
