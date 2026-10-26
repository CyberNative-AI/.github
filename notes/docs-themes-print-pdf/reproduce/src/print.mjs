// Print every arm to PDF with headless Chromium (CDP printToPDF = the route docs-to-PDF exporters use).
// Usage (inside mcr.microsoft.com/playwright:v1.62.1-noble, --network none):
//   NODE_PATH=/work/pw/node_modules node print.mjs /work/sites /work/out/<pass> [arm,arm,...]
// With no arm list it prints the ten themes in three modes and g0 (plain HTML, no CSS) as built.
// Modes: default (site as built), A and AB (FIXDIR/<arm>.<mode>.css injected after load; FIXDIR defaults to /work/fixes).
// Arms without a fix pair (g0, g0-prewrap, mdbook-print) print in default mode only.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const [, , SITES, OUT, ONLY] = process.argv;
export const ARMS = {
  g0: ['g0', '/index.html'],
  'g0-prewrap': ['g0-prewrap', '/index.html'],
  docusaurus: ['docusaurus/build', '/docs/fixture/'],
  starlight: ['starlight/dist', '/fixture/'],
  vitepress: ['vitepress/docs/.vitepress/dist', '/fixture.html'],
  'mkdocs-material': ['mkdocs-material/site', '/fixture/'],
  mkdocs: ['mkdocs/site', '/fixture/'],
  mdbook: ['mdbook/book', '/fixture.html'],
  'mdbook-print': ['mdbook/book', '/print.html'],
  'sphinx-alabaster': ['sphinx-alabaster/_build/html', '/fixture.html'],
  'sphinx-furo': ['sphinx-furo/_build/html', '/fixture.html'],
  'sphinx-rtd': ['sphinx-sphinx-rtd-theme/_build/html', '/fixture.html'],
  'sphinx-pydata': ['sphinx-pydata-sphinx-theme/_build/html', '/fixture.html'],
};
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.woff': 'font/woff', '.json': 'application/json', '.ico': 'image/x-icon' };

function serve(root) {
  return new Promise((res) => {
    const srv = http.createServer((req, rsp) => {
      let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      let f = path.join(root, p);
      if (!f.startsWith(root)) { rsp.writeHead(403); return rsp.end(); }
      if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
      if (!fs.existsSync(f) && fs.existsSync(f + '.html')) f = f + '.html';
      if (!fs.existsSync(f)) { rsp.writeHead(p.endsWith('favicon.ico') ? 204 : 404); return rsp.end(); }
      rsp.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
      fs.createReadStream(f).pipe(rsp);
    });
    srv.listen(0, '127.0.0.1', () => res(srv));
  });
}

const FIX = process.env.FIXDIR || '/work/fixes';
fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const meta = { chromium: browser.version(), arms: {} };
const THEMES = ['docusaurus', 'starlight', 'vitepress', 'mkdocs-material', 'mkdocs', 'mdbook',
  'sphinx-alabaster', 'sphinx-furo', 'sphinx-rtd', 'sphinx-pydata'];
const arms = ONLY ? ONLY.split(',') : [...THEMES, 'g0'];
for (const arm of arms) {
  const [dir, route] = ARMS[arm];
  const srv = await serve(path.resolve(SITES, dir));
  const url = `http://127.0.0.1:${srv.address().port}${route}`;
  for (const mode of THEMES.includes(arm) ? ['default', 'A', 'AB'] : ['default']) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await ctx.newPage();
    const failed = [];
    page.on('requestfailed', (r) => failed.push(r.url()));
    const rsp = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
    if (mode !== 'default') await page.addStyleTag({ content: fs.readFileSync(path.join(FIX, `${arm}.${mode}.css`), 'utf8') });
    // scale ruler: two text markers 200 CSS px apart; printed distance / 150 pt = print scale
    await page.evaluate(() => {
      for (const [id, x] of [['ZQRULA', 0], ['ZQRULB', 200]]) {
        const d = document.createElement('div');
        d.textContent = id;
        d.setAttribute('style', `position:absolute;left:${x}px;top:2px;z-index:2147483647;font:10px monospace;color:#000;white-space:nowrap;margin:0;padding:0`);
        document.documentElement.appendChild(d);
      }
    });
    const file = path.join(OUT, `${arm}.${mode}.pdf`);
    await page.pdf({ path: file, format: 'Letter', printBackground: false,
      margin: { top: '0.4in', bottom: '0.4in', left: '0.4in', right: '0.4in' } });
    meta.arms[`${arm}.${mode}`] = { url: route, status: rsp && rsp.status(), failed_requests: failed.length };
    await ctx.close();
  }
  srv.close();
  console.log(arm, 'ok');
}
await browser.close();
fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta, null, 1));
