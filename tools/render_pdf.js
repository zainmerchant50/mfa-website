#!/usr/bin/env node
/* Render an MFA product HTML (US Letter pages) to PDF.  Usage: node tools/render_pdf.js <in.html> <out.pdf> */
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright')); }
(async () => {
  const [src, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + path.resolve(src));
  await p.evaluate(() => document.fonts.ready);
  const bad = await p.evaluate(() => [...document.querySelectorAll('.page')].map((e, i) => { const ft = e.querySelector('.ft'); const lim = ft ? ft.offsetTop : e.clientHeight; const kids = [...e.children].filter(c => c !== ft && !c.classList.contains('frame') && getComputedStyle(c).position !== 'absolute'); const bottom = Math.max(0, ...kids.map(c => c.offsetTop + c.offsetHeight)); return bottom > lim - 4 ? i + 1 : 0; }).filter(Boolean));
  await p.emulateMedia({ media: 'print' });
  await p.pdf({ path: out, format: 'Letter', printBackground: true, preferCSSPageSize: true });
  await b.close();
  console.log('rendered', out, bad.length ? 'OVERFLOW on pages: ' + bad.join(',') : 'no overflow');
})();
