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


def _plain(s):
    return _html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


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
