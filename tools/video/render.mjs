#!/usr/bin/env node
// MFA listing-video renderer (Remotion).
// License: Remotion's "Free License" (node_modules/remotion/LICENSE.md) covers individuals and for-profit
// organizations with up to 3 employees, commercial use included; above that a Company License is needed (remotion.pro).
// Chromium: uses the preinstalled Playwright chrome-headless-shell (or $REMOTION_CHROME); no browser download.
//
//   cd tools/video && npm ci            # once (node_modules is git-ignored)
//   node render.mjs props/1099-se-calculator.json          # both sizes -> site/assets/videos/
//   node render.mjs props/*.json --only 9x16               # one size
//   node render.mjs props/x.json --stills /tmp/frames      # also save check frames (PNG) at 6 points
//   node render.mjs props/x.json --frames-only DIR      # fast layout check: PNG stills only, no video
//   node render.mjs props/x.json --finalize-only        # re-run only the ffmpeg yuv420p/faststart pass
//   node render.mjs props/x.json --prep-only               # just build the cropped images in public/_gen
//
// Each props file: {name, seconds?, label, title[], shortTitle[]?, sub, bullets[3-5], images[2-4 or a montage],
//   montage?, cta[], ctaSub, ctaPill, footer?}. images[] entries are repo-relative paths or
//   {src, crop:[l,t,r,b] fractions, width?}. The text is checked against MFA's public-copy rules before rendering.
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {execFileSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const GEN = path.join(HERE, 'public', '_gen');
const OUT = path.join(ROOT, 'site', 'assets', 'videos');
const CHROME = [
  process.env.REMOTION_CHROME,
  '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell',
].find((p) => p && fs.existsSync(p));

const args = process.argv.slice(2);
const flag = (k) => {
  const i = args.indexOf(k);
  return i >= 0 ? args[i + 1] : null;
};
const only = flag('--only');
const stills = flag('--stills');
const framesOnly = flag('--frames-only');
const prepOnly = args.includes('--prep-only');
const files = args.filter((a, i) => a.endsWith('.json') && !['--only', '--stills', '--frames-only'].includes(args[i - 1]));
if (!files.length) {
  console.error('usage: node render.mjs props/<name>.json [...] [--only 16x9|9x16] [--stills DIR] [--prep-only]');
  process.exit(2);
}

// ---- MFA public-copy rules (CLAUDE project rules + docs/design-system.md) ----
const RULES = [
  [/\bfree\b/i, 'the word "free"'],
  [/\bCPA\b/, '"CPA" (never a claim about MFA or Zain)'],
  [/certified public accountant/i, 'a CPA claim'],
  [/[$€£]\s?\d|\d\s?(usd|dollars)\b/i, 'a price or dollar amount'],
  [/\b\d{1,5}\s+\w+(\s\w+)?\s+(st|street|ave|avenue|rd|road|blvd|lane|ln|drive|dr|suite|ste)\b\.?/i, 'a street address'],
  [/\bguarantee/i, 'a guarantee'],
];
function checkCopy(p, file) {
  const texts = [p.label, ...(p.title || []), ...(p.shortTitle || []), p.sub, ...(p.bullets || []), ...(p.cta || []), p.ctaSub, p.ctaNote, p.ctaPill, p.footer]
    .filter(Boolean)
    .map(String);
  const bad = [];
  for (const t of texts) for (const [re, why] of RULES) if (re.test(t)) bad.push(`${why}: "${t}"`);
  if (!p.bullets || p.bullets.length < 3 || p.bullets.length > 5) bad.push('bullets: need 3-5');
  if (!p.montage && (!p.images || p.images.length < 2 || p.images.length > 4)) bad.push('images: need 2-4 (or montage: true)');
  if (bad.length) {
    console.error(`${file}: copy check failed\n  - ${bad.join('\n  - ')}`);
    process.exit(1);
  }
}

// ---- assets: fonts + logo + cropped preview images into public/_gen (git-ignored) ----
function prepShared() {
  fs.mkdirSync(path.join(GEN, 'fonts'), {recursive: true});
  for (const f of fs.readdirSync(path.join(ROOT, 'tools', 'fonts'))) fs.copyFileSync(path.join(ROOT, 'tools', 'fonts', f), path.join(GEN, 'fonts', f));
  fs.copyFileSync(path.join(ROOT, 'social', 'assets', 'mfa-logo-white.png'), path.join(GEN, 'logo-white.png'));
}
function prepImages(p) {
  fs.mkdirSync(path.join(GEN, 'img'), {recursive: true});
  return p.images.map((im, i) => {
    const spec = typeof im === 'string' ? {src: im} : im;
    const out = `_gen/img/${p.name}-${i + 1}.jpg`;
    const vf = [];
    if (spec.crop) {
      const [l, t, r, b] = spec.crop;
      vf.push(`crop=iw*${r - l}:ih*${b - t}:iw*${l}:ih*${t}`);
    }
    vf.push(`scale='max(iw,${spec.width || 900})':-2:flags=lanczos`);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', path.join(ROOT, spec.src), '-vf', vf.join(','), '-q:v', '2', path.join(HERE, 'public', out)]);
    return out;
  });
}

// Remotion's frames give full-range yuvj420p; re-encode to standard limited-range yuv420p H.264 (veryfast)
// with faststart, which Etsy, Instagram, YouTube and TikTok all accept.
function finalize(file) {
  const tmp = file.replace(/\.mp4$/, '.tmp.mp4');
  fs.renameSync(file, tmp);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', tmp, '-an', '-vf', 'scale=in_range=full:out_range=tv,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-profile:v', 'high', '-color_range', 'tv', '-movflags', '+faststart', file]);
  fs.unlinkSync(tmp);
}
if (args.includes('--finalize-only')) {
  for (const f of files) {
    const name = JSON.parse(fs.readFileSync(path.resolve(f), 'utf8')).name;
    for (const tag of ['16x9', '9x16']) {
      const file = path.join(OUT, `${name}-${tag}.mp4`);
      if (fs.existsSync(file)) { finalize(file); console.log('finalized', path.relative(ROOT, file), (fs.statSync(file).size / 1048576).toFixed(2), 'MB'); }
    }
  }
  process.exit(0);
}

prepShared();
const jobs = files.map((f) => {
  const p = JSON.parse(fs.readFileSync(path.resolve(f), 'utf8'));
  checkCopy(p, f);
  return {file: f, props: {...p, images: prepImages(p)}};
});
if (prepOnly) {
  console.log('prepared', GEN);
  process.exit(0);
}

if (!CHROME) console.warn('No local Chromium found; Remotion will try to download chrome-headless-shell.');
const serveUrl = await bundle({entryPoint: path.join(HERE, 'src', 'index.jsx'), publicDir: path.join(HERE, 'public')});
fs.mkdirSync(OUT, {recursive: true});

for (const {props} of jobs) {
  for (const [id, tag] of [
    ['Listing16x9', '16x9'],
    ['Listing9x16', '9x16'],
  ]) {
    if (only && only !== tag) continue;
    const comp = await selectComposition({serveUrl, id, inputProps: props, browserExecutable: CHROME});
    if (framesOnly) {
      fs.mkdirSync(framesOnly, {recursive: true});
      const d = comp.durationInFrames;
      for (const fr of [12, Math.round(d * 0.18), Math.round(d * 0.3), Math.round(d * 0.5), Math.round(d * 0.7), Math.round(d * 0.9)]) {
        await renderStill({serveUrl, composition: comp, inputProps: props, frame: fr, output: path.join(framesOnly, `${props.name}-${tag}-${(fr / comp.fps).toFixed(1)}s.png`), browserExecutable: CHROME, chromiumOptions: {gl: 'swangle'}});
      }
      console.log('stills', props.name, tag);
      continue;
    }
    const outFile = path.join(OUT, `${props.name}-${tag}.mp4`);
    const t0 = Date.now();
    await renderMedia({
      serveUrl,
      composition: comp,
      inputProps: props,
      codec: 'h264',
      x264Preset: 'veryfast',
      crf: tag === '16x9' ? 24 : 24,
      pixelFormat: 'yuv420p',
      muted: true,
      enforceAudioTrack: false,
      outputLocation: outFile,
      concurrency: 2,
      browserExecutable: CHROME,
      chromiumOptions: {gl: 'swangle'},
    });
    finalize(outFile);
    const mb = fs.statSync(outFile).size / 1048576;
    console.log(`${path.relative(ROOT, outFile)}  ${(comp.durationInFrames / comp.fps).toFixed(1)} s  ${mb.toFixed(2)} MB  (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
    if (mb > 10) console.warn(`  WARNING: over 10 MB; raise crf for ${props.name}`);
    if (stills) {
      fs.mkdirSync(stills, {recursive: true});
      const dur = comp.durationInFrames / comp.fps;
      for (const s of [0.4, dur * 0.18, dur * 0.3, dur * 0.5, dur * 0.7, dur * 0.9]) {
        execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', s.toFixed(2), '-i', outFile, '-frames:v', '1', path.join(stills, `${props.name}-${tag}-${s.toFixed(1)}s.png`)]);
      }
    }
  }
}
