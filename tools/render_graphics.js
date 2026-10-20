#!/usr/bin/env node
/* Render blog graphics (HTML/CSS in content/graphics) to PNG (or PDF when <out> ends in .pdf).
   Usage: node tools/render_graphics.js <graphic.html> <out.png|out.pdf> [width] [height] [scale]
   Needs Playwright + Chromium (preinstalled in Claude's cloud workspace). Fonts are vendored in tools/fonts. */
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright')); }
(async () => {
  const [src, out, w = '1200', h = '630', scale = '1'] = process.argv.slice(2);
  if (!src || !out) { console.error('usage: render_graphics.js <src.html> <out.png> [w] [h] [scale]'); process.exit(1); }
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: +scale });
  await p.goto('file://' + path.resolve(src));
  await p.evaluate(() => document.fonts.ready);
  const missing = await p.evaluate(() => [...document.fonts].filter(f => f.status === 'error').map(f => f.family + ' ' + f.weight));
  if (out.toLowerCase().endsWith('.pdf')) {   // one-page PDF guide at the same size as the graphic
    await p.emulateMedia({ media: 'screen' });
    await p.pdf({ path: out, width: w + 'px', height: h + 'px', printBackground: true, pageRanges: '1' });
  } else {
    await p.screenshot({ path: out, type: 'png' });
  }
  await b.close();
  console.log('rendered', out, missing.length ? 'UNLOADED FONTS: ' + missing.join(', ') : 'fonts ok');
})();
