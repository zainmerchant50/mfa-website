import React from 'react';
import {
  AbsoluteFill,
  Img,
  Sequence,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from 'remotion';

// ---- Brand (docs/design-system.md + tools/ui_kit.py + social/render.py) ----
const NAVY = '#10233F';
const NAVY_DEEP = '#0A1628';
const GOLD = '#D8B769';
const GOLD_DARK = '#B08D3F';
const CREAM = '#F5F4EF';
const SERIF = "'Cormorant Garamond', Georgia, serif";
const SANS = "'Inter', system-ui, sans-serif";
const EASE = Easing.bezier(0.16, 1, 0.3, 1);

// ---- Fonts: bundled woff2 copied into public/_gen/fonts by render.mjs (no network) ----
const FONTS = [
  ['Cormorant Garamond', 'cormorant-garamond-latin-500-normal.woff2', '500', 'normal'],
  ['Cormorant Garamond', 'cormorant-garamond-latin-500-italic.woff2', '500', 'italic'],
  ['Inter', 'inter-latin-400-normal.woff2', '400', 'normal'],
  ['Inter', 'inter-latin-500-normal.woff2', '500', 'normal'],
  ['Inter', 'inter-latin-600-normal.woff2', '600', 'normal'],
];
if (typeof document !== 'undefined' && !window.__mfaFonts) {
  window.__mfaFonts = true;
  const h = delayRender('fonts');
  Promise.all(
    FONTS.map(([fam, file, weight, style]) => {
      const f = new FontFace(fam, `url(${staticFile('_gen/fonts/' + file)}) format('woff2')`, {weight, style});
      return f.load().then((ff) => document.fonts.add(ff));
    }),
  )
    .then(() => continueRender(h))
    .catch((e) => {
      console.error(e);
      continueRender(h);
    });
}

export const defaultProps = {
  seconds: 15,
  label: 'SELF-EMPLOYED TAX PLANNER',
  title: ['1099 Self-Employed', '*Tax Calculator*'],
  sub: 'Excel + Google Sheets · instant download',
  bullets: ['Bullet one', 'Bullet two', 'Bullet three'],
  images: [],
  montage: false,
  cta: ['Built by an', '*accounting firm*'],
  ctaSub: 'ACCA · over 10 years of accounting, audit and tax experience',
  ctaPill: 'Shop MFASZ on Etsy',
  footer: 'MERCHANT FINANCIAL ADVISORY · MFA-ADVISORY.COM',
  logo: '_gen/logo-white.png',
};

// "*word*" -> gold italic
const Rich = ({text}) => {
  const parts = String(text).split(/(\*[^*]+\*)/g).filter(Boolean);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith('*') && p.endsWith('*') ? (
          <em key={i} style={{color: GOLD, fontStyle: 'italic'}}>
            {p.slice(1, -1)}
          </em>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  );
};

// fade + rise entrance, optional fade-out at the end of a scene
const useEnter = (delay = 0, dur = 18) => {
  const f = useCurrentFrame();
  const t = interpolate(f, [delay, delay + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE});
  return t;
};
const Rise = ({delay = 0, dist = 40, children, style}) => {
  const t = useEnter(delay);
  return <div style={{opacity: t, transform: `translateY(${(1 - t) * dist}px)`, ...style}}>{children}</div>;
};

const SceneFade = ({len, children}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 10, len - 10, len], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: o}}>{children}</AbsoluteFill>;
};

// ---- persistent chrome ----
const Background = () => {
  const f = useCurrentFrame();
  const {width, height, durationInFrames} = useVideoConfig();
  const drift = interpolate(f, [0, durationInFrames], [0, 1]);
  const gx = 70 - drift * 20;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at ${gx}% 30%, rgba(46,74,122,.55) 0%, rgba(16,35,63,0) 55%),
                     radial-gradient(ellipse at 15% 100%, rgba(176,141,63,.16) 0%, rgba(16,35,63,0) 45%),
                     linear-gradient(160deg, ${NAVY} 0%, ${NAVY_DEEP} 100%)`,
      }}
    >
      {/* gold hairline frame, as on the shop cover images */}
      <div
        style={{
          position: 'absolute',
          inset: Math.round(Math.min(width, height) * 0.025),
          border: '1.5px solid rgba(216,183,105,.28)',
          borderRadius: 28,
        }}
      />
    </AbsoluteFill>
  );
};

const Header = ({logo, v, pad, top, len}) => {
  const f = useCurrentFrame();
  const t = Math.min(useEnter(0, 20), interpolate(f, [len - 10, len], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const lh = v ? 96 : 84;
  return (
    <div
      style={{
        position: 'absolute',
        left: pad,
        top,
        display: 'flex',
        alignItems: 'center',
        gap: v ? 26 : 22,
        opacity: t,
      }}
    >
      <Img src={staticFile(logo)} style={{height: lh, width: 'auto'}} />
      <div style={{display: 'flex', flexDirection: 'column', lineHeight: 1}}>
        <span style={{fontFamily: SERIF, fontWeight: 500, fontSize: v ? 54 : 46, color: CREAM}}>Merchant</span>
        <span style={{fontFamily: SANS, fontWeight: 500, fontSize: v ? 21 : 18, letterSpacing: '0.32em', color: 'rgba(245,244,239,.75)', marginTop: 8}}>
          FINANCIAL ADVISORY
        </span>
      </div>
    </div>
  );
};

const Footer = ({text, v, pad, bottom}) => {
  const f = useCurrentFrame();
  const {durationInFrames, width} = useVideoConfig();
  const p = interpolate(f, [0, durationInFrames - 1], [0, 1], {extrapolateRight: 'clamp'});
  if (v) {
    // 9:16: just the progress bar, on the top edge of the safe area (text there would sit under the app UI)
    return (
      <div style={{position: 'absolute', left: pad, right: pad, top: 250, height: 5, background: 'rgba(216,183,105,.18)', borderRadius: 3, overflow: 'hidden'}}>
        <div style={{width: `${p * 100}%`, height: '100%', background: GOLD}} />
      </div>
    );
  }
  return (
    <div style={{position: 'absolute', left: pad, right: pad, bottom}}>
      <div style={{height: 4, background: 'rgba(216,183,105,.18)', borderRadius: 2, overflow: 'hidden'}}>
        <div style={{width: `${p * 100}%`, height: '100%', background: GOLD}} />
      </div>
      <div
        style={{
          marginTop: v ? 22 : 18,
          fontFamily: SANS,
          fontWeight: 600,
          fontSize: v ? 24 : 22,
          letterSpacing: '0.18em',
          color: 'rgba(245,244,239,.7)',
          textAlign: v ? 'center' : 'left',
        }}
      >
        {text}
      </div>
    </div>
  );
};

const Pill = ({children, v, filled = true, size}) => (
  <span
    style={{
      display: 'inline-block',
      fontFamily: SANS,
      fontWeight: 600,
      fontSize: size || (v ? 30 : 26),
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      color: filled ? NAVY : GOLD,
      background: filled ? GOLD : 'transparent',
      border: `2px solid ${GOLD}`,
      borderRadius: 999,
      padding: v ? '14px 34px' : '12px 30px',
      whiteSpace: 'nowrap',
    }}
  >
    {children}
  </span>
);

// product picture in a soft card with a slow push-in
const Shot = ({src, w, h, delay = 0, zoom = 0.06, len = 240, rotate = 0, style}) => {
  const f = useCurrentFrame();
  const t = useEnter(delay, 22);
  const s = interpolate(f, [delay, delay + len], [1, 1 + zoom], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        width: w,
        height: h,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        opacity: t,
        transform: `translateY(${(1 - t) * 50}px) rotate(${rotate}deg) scale(${s})`,
        ...style,
      }}
    >
      <Img
        src={staticFile(src)}
        style={{
          maxWidth: '100%',
          maxHeight: '100%',
          borderRadius: 18,
          boxShadow: '0 30px 80px rgba(0,0,0,.45), 0 0 0 1.5px rgba(216,183,105,.35)',
        }}
      />
    </div>
  );
};

// cycle through images with a crossfade
const Cycler = ({images, w, h, len}) => {
  const f = useCurrentFrame();
  const n = Math.max(1, images.length);
  const per = len / n;
  return (
    <div style={{position: 'relative', width: w, height: h}}>
      {images.map((src, i) => {
        const start = i * per;
        const fadeIn = i === 0 ? 1 : interpolate(f, [start - 5, start + 5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const fadeOut = i === n - 1 ? 1 : interpolate(f, [start + per - 5, start + per + 5], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const op = Math.min(fadeIn, fadeOut);
        const s = interpolate(f, [start, start + per + 16], [1.0, 1.05], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        return (
          <div key={i} style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: op, transform: `scale(${s})`}}>
            <Img
              src={staticFile(src)}
              style={{maxWidth: '100%', maxHeight: '100%', borderRadius: 18, boxShadow: '0 30px 80px rgba(0,0,0,.45), 0 0 0 1.5px rgba(216,183,105,.35)'}}
            />
          </div>
        );
      })}
    </div>
  );
};

// grid of product covers (shop overview)
const Montage = ({images, w, h, cols}) => {
  const rows = Math.ceil(images.length / cols);
  const gap = 22;
  const cell = Math.min((w - gap * (cols - 1)) / cols, (h - gap * (rows - 1)) / rows);
  return (
    <div style={{width: w, height: h, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{display: 'grid', gridTemplateColumns: `repeat(${cols}, ${cell}px)`, gap}}>
        {images.map((src, i) => (
          <Shot key={i} src={src} w={cell} h={cell} delay={6 + i * 5} zoom={0.03} />
        ))}
      </div>
    </div>
  );
};

const Check = ({size}) => (
  <svg width={size} height={size} viewBox="0 0 40 40" style={{flex: 'none', marginTop: size * 0.08}}>
    <circle cx="20" cy="20" r="18.5" fill="rgba(216,183,105,.14)" stroke={GOLD} strokeWidth="2" />
    <path d="M12 20.5l5.5 5.5L28.5 14.5" fill="none" stroke={GOLD} strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Bullets = ({items, v, start = 8, step}) => {
  const fs = v ? 44 : 42;
  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: v ? 24 : 26}}>
      {items.map((b, i) => (
        <Rise key={i} delay={start + i * step} dist={30}>
          <div style={{display: 'flex', gap: v ? 24 : 22, alignItems: 'flex-start'}}>
            <Check size={fs * 1.05} />
            <span style={{fontFamily: SANS, fontWeight: 500, fontSize: fs, lineHeight: 1.22, color: CREAM}}>{b}</span>
          </div>
        </Rise>
      ))}
    </div>
  );
};

// Cormorant Garamond averages ~0.46 em per character: shrink the size so the longest line fits maxW on one line
const fit = (lines, size, maxW) => {
  const n = Math.max(...lines.map((l) => String(l).replace(/\*/g, '').length));
  return maxW ? Math.min(size, Math.floor(maxW / (n * 0.47))) : size;
};
const Title = ({lines, size, delay = 4, maxW, align}) => {
  const fs = fit(lines, size, maxW);
  return (
    <div style={{fontFamily: SERIF, fontWeight: 500, fontSize: fs, lineHeight: 1.04, color: CREAM, letterSpacing: '-0.005em', textAlign: align}}>
      {lines.map((l, i) => (
        <Rise key={i} delay={delay + i * 5} dist={36}>
          <div style={{whiteSpace: 'nowrap'}}>
            <Rich text={l} />
          </div>
        </Rise>
      ))}
    </div>
  );
};

// ---- scenes ----
const Hero = ({p, v, L, len}) => {
  const imgs = p.images;
  return (
    <SceneFade len={len}>
      {v ? (
        <div style={{position: 'absolute', left: L.pad, right: L.pad, top: L.contentTop, height: L.contentH, display: 'flex', flexDirection: 'column', alignItems: 'flex-start'}}>
          <Rise delay={2}>
            <Pill v={v}>{p.label}</Pill>
          </Rise>
          <div style={{height: 32}} />
          <Title lines={p.title} size={118} maxW={L.inner} />
          <div style={{height: 22}} />
          <Rise delay={14}>
            <div style={{fontFamily: SANS, fontWeight: 500, fontSize: 40, color: 'rgba(245,244,239,.82)'}}>{p.sub}</div>
          </Rise>
          <div style={{height: 44}} />
          <div style={{flex: 1, minHeight: 0, width: '100%'}}>
            {p.montage ? <Fan images={imgs.slice(0, 3)} w={L.inner} h={L.contentH * 0.42} /> : <Shot src={imgs[0]} w="100%" h="100%" delay={10} len={len} />}
          </div>
        </div>
      ) : (
        <>
          <div style={{position: 'absolute', left: L.pad, top: 0, bottom: 0, width: 860, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
            <Rise delay={2}>
              <Pill v={v}>{p.label}</Pill>
            </Rise>
            <div style={{height: 36}} />
            <Title lines={p.title} size={p.titleSize || 124} maxW={860} />
            <div style={{height: 30}} />
            <Rise delay={14}>
              <div style={{fontFamily: SANS, fontWeight: 500, fontSize: 36, color: 'rgba(245,244,239,.82)'}}>{p.sub}</div>
            </Rise>
          </div>
          <div style={{position: 'absolute', right: L.pad, top: 150, bottom: 150, width: 780, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            {p.montage ? <Fan images={imgs.slice(0, 3)} w={780} h={700} /> : <Shot src={imgs[0]} w={780} h={720} delay={10} len={len} />}
          </div>
        </>
      )}
    </SceneFade>
  );
};

const Fan = ({images, w, h}) => {
  const c = Math.min(h * 0.92, w * 0.5);
  const rot = [-8, 0, 8];
  const dx = [-0.3, 0, 0.3];
  return (
    <div style={{position: 'relative', width: w, height: h}}>
      {images.map((src, i) => (
        <div key={i} style={{position: 'absolute', left: w / 2 - c / 2 + dx[i] * w * 0.9, top: (h - c) / 2 + (i === 1 ? -10 : 18), zIndex: i === 1 ? 2 : 1}}>
          <Shot src={src} w={c} h={c} delay={8 + (i === 1 ? 8 : 0)} rotate={rot[i]} zoom={0.03} />
        </div>
      ))}
    </div>
  );
};

const Details = ({p, v, L, len}) => {
  const n = p.bullets.length;
  const step = Math.max(8, Math.min(26, Math.floor((len * 0.55) / n)));
  const imgs = p.images.length > 1 && !p.montage ? p.images.slice(1).concat(p.images[0]) : p.images;
  return (
    <SceneFade len={len}>
      {v ? (
        <div style={{position: 'absolute', left: L.pad, right: L.pad, top: L.contentTop, height: L.contentH, display: 'flex', flexDirection: 'column'}}>
          <Title lines={[(p.shortTitle || p.title).join(' ')]} size={72} maxW={L.inner} delay={0} />
          <div style={{height: 30}} />
          <div style={{flex: 1, minHeight: 0, width: '100%'}}>
            <Rise delay={4} dist={30} style={{width: '100%', height: '100%'}}>
              {p.montage ? <Montage images={imgs} w={L.inner} h={L.montageH} cols={3} /> : <Cycler images={imgs} w="100%" h="100%" len={len} />}
            </Rise>
          </div>
          <div style={{height: 40}} />
          <Bullets items={p.bullets} v={v} start={12} step={step} />
        </div>
      ) : (
        <>
          <div style={{position: 'absolute', left: L.pad, top: 0, bottom: 0, width: 820, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
            <Title lines={p.shortTitle || p.title} size={78} maxW={820} delay={0} />
            <div style={{height: 44}} />
            <Bullets items={p.bullets} v={v} start={10} step={step} />
          </div>
          <div style={{position: 'absolute', right: L.pad, top: 150, bottom: 150, width: 800, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            {p.montage ? <Montage images={imgs} w={800} h={700} cols={3} /> : <Cycler images={imgs} w={800} h={720} len={len} />}
          </div>
        </>
      )}
    </SceneFade>
  );
};

const Cta = ({p, v, L, len}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame: f - 2, fps, config: {damping: 14, stiffness: 120}});
  return (
    <SceneFade len={len + 10}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: L.pad}}>
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', marginTop: v ? -80 : -30}}>
          <div style={{transform: `scale(${0.85 + 0.15 * pop})`, opacity: pop}}>
            <Img src={staticFile(p.logo)} style={{height: v ? 200 : 170, width: 'auto'}} />
          </div>
          <div style={{height: v ? 56 : 44}} />
          <Title lines={p.cta} size={v ? 112 : 112} delay={6} />
          <div style={{height: v ? 44 : 34}} />
          <Rise delay={14}>
            <div style={{fontFamily: SANS, fontWeight: 500, fontSize: v ? 40 : 36, lineHeight: 1.35, color: 'rgba(245,244,239,.85)', maxWidth: v ? 860 : 1300}}>{p.ctaSub}</div>
          </Rise>
          {p.ctaNote ? (
            <Rise delay={17}>
              <div style={{marginTop: v ? 18 : 14, fontFamily: SANS, fontWeight: 400, fontSize: v ? 32 : 28, lineHeight: 1.35, color: 'rgba(245,244,239,.66)', maxWidth: v ? 860 : 1300}}>{p.ctaNote}</div>
            </Rise>
          ) : null}
          <div style={{height: v ? 60 : 48}} />
          <Rise delay={20}>
            <Pill v={v} size={v ? 34 : 30}>
              {p.ctaPill}
            </Pill>
          </Rise>
          {v ? (
            <Rise delay={24}>
              <div style={{marginTop: 48, fontFamily: SANS, fontWeight: 600, fontSize: 28, letterSpacing: '0.18em', color: 'rgba(245,244,239,.7)'}}>MFA-ADVISORY.COM</div>
            </Rise>
          ) : null}
        </div>
      </AbsoluteFill>
    </SceneFade>
  );
};

export const Listing = (props) => {
  const p = {...defaultProps, ...props};
  const {width, height, durationInFrames} = useVideoConfig();
  const v = height > width;
  const pad = v ? 96 : 110;
  // 9:16 keeps the top 250 px and bottom 350 px clear for the Reels / Shorts / TikTok UI
  const L = v
    ? {pad, inner: width - pad * 2, headerTop: 290, contentTop: 420, contentH: 1570 - 420, montageH: 560, footerBottom: 350}
    : {pad, inner: width - pad * 2, headerTop: 70, contentTop: 0, footerBottom: 62};
  const a = Math.round(durationInFrames * 0.24);
  const c = Math.round(durationInFrames * 0.24);
  const b = durationInFrames - a - c;
  return (
    <AbsoluteFill style={{backgroundColor: NAVY}}>
      <Background />
      <Sequence from={0} durationInFrames={a + b} layout="none">
        <Header logo={p.logo} v={v} pad={pad} top={L.headerTop} len={a + b} />
      </Sequence>
      <Sequence from={0} durationInFrames={a}>
        <Hero p={p} v={v} L={L} len={a} />
      </Sequence>
      <Sequence from={a} durationInFrames={b}>
        <Details p={p} v={v} L={L} len={b} />
      </Sequence>
      <Sequence from={a + b} durationInFrames={c}>
        <Cta p={p} v={v} L={L} len={c} />
      </Sequence>
      <Footer text={p.footer} v={v} pad={pad} bottom={L.footerBottom} />
    </AbsoluteFill>
  );
};
