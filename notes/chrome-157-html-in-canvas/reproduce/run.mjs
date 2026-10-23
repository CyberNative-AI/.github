// Runner: load each test page in a fresh-profile headless Chrome, record exceptions/console/probe,
// screenshot the first <canvas> at 4 s and 7 s. Raw CDP, no Playwright.
// usage: node run.mjs <chrome-binary> <arm> <pagesDir> <assetsDir> <outDir> <reps> PAGE...
// EXTRA_FLAGS (space-separated) adds browser flags for the arm.
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const [bin, arm, pagesDir, assetsDir, outDir, repsArg, ...pages] = process.argv.slice(2);
const REPS = Number(repsArg || 2);
const SHOT_MS = [4000, 7000];
const sleep = ms => new Promise(r => setTimeout(r, ms));
fs.mkdirSync(outDir, { recursive: true });
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm' };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (u === '/favicon.ico') { res.writeHead(204); return res.end(); }
  const f = u.startsWith('/assets/') ? path.join(assetsDir, u.slice(8)) : path.join(pagesDir, u.slice(1));
  if (!f.startsWith(assetsDir) && !f.startsWith(pagesDir)) { res.writeHead(403); return res.end(); }
  fs.readFile(f, (e, b) => {
    if (e) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); res.end(b);
  });
});
await new Promise(r => server.listen(8765, '127.0.0.1', r));
const flags = ['--headless=new', '--no-sandbox', '--no-first-run', '--no-default-browser-check', '--disable-field-trial-config',
  '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-unsafe-webgpu', '--enable-features=Vulkan', '--use-vulkan=swiftshader', '--window-size=800,600', '--force-device-scale-factor=1',
  ...(process.env.EXTRA_FLAGS ? process.env.EXTRA_FLAGS.split(' ').filter(Boolean) : [])];
const out = fs.openSync(path.join(outDir, `${arm}.jsonl`), 'a');
let port = 9500;
for (const page of pages) for (let rep = 1; rep <= REPS; rep++) {
  const ud = fs.mkdtempSync(`/tmp/ud-${arm}-`);
  const p = port++;
  const ch = spawn(bin, [...flags, `--remote-debugging-port=${p}`, `--user-data-dir=${ud}`, 'about:blank'], { stdio: 'ignore' });
  const rec = { arm, page, rep, flags, t0: new Date().toISOString(), exceptions: [], console: [], log: [], shots: [] };
  let ws;
  try {
    let ver; for (let i = 0; i < 80 && !ver; i++) { try { ver = await (await fetch(`http://127.0.0.1:${p}/json/version`)).json(); } catch { await sleep(250); } }
    if (!ver) throw new Error('no_cdp');
    rec.browser = ver.Browser;
    const tgt = (await (await fetch(`http://127.0.0.1:${p}/json/list`)).json()).find(t => t.type === 'page');
    ws = new WebSocket(tgt.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
    let id = 0; const pend = new Map(); const ev = [];
    ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id) { pend.get(d.id)?.(d); pend.delete(d.id); } else ev.push(d); };
    const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
    await send('Page.enable'); await send('Runtime.enable'); await send('Log.enable');
    await send('Emulation.setDeviceMetricsOverride', { width: 800, height: 600, deviceScaleFactor: 1, mobile: false });
    const tNav = Date.now();
    await send('Page.navigate', { url: `http://127.0.0.1:8765/${page}.html` });
    for (let w = 0; w < 15000 && !ev.some(e => e.method === 'Page.loadEventFired'); w += 100) await sleep(100);
    rec.loadEvent = ev.some(e => e.method === 'Page.loadEventFired');
    for (const at of SHOT_MS) {
      const wait = at - (Date.now() - tNav); if (wait > 0) await sleep(wait);
      const rr = await send('Runtime.evaluate', { expression: `JSON.stringify((() => { const r = document.querySelector('canvas').getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; })())`, returnByValue: true });
      const rect = JSON.parse(rr.result.result.value);
      const s = await send('Page.captureScreenshot', { format: 'png', clip: { x: rect.x, y: rect.y, width: rect.w, height: rect.h, scale: 1 } });
      const fn = `${arm}-${page}-r${rep}-${at}.png`;
      fs.writeFileSync(path.join(outDir, fn), Buffer.from(s.result.data, 'base64'));
      rec.shots.push({ at, file: fn, rect });
    }
    const pr = await send('Runtime.evaluate', { expression: 'JSON.stringify(window.__probe || null)', returnByValue: true });
    rec.probe = JSON.parse(pr.result?.result?.value ?? 'null');
    for (const e of ev) {
      if (e.method === 'Runtime.exceptionThrown') { const d = e.params.exceptionDetails; rec.exceptions.push((d.exception?.description || d.text || '').split('\n')[0].slice(0, 300)); }
      else if (e.method === 'Runtime.consoleAPICalled' && ['error', 'warning', 'assert'].includes(e.params.type))
        rec.console.push({ type: e.params.type, text: e.params.args.map(a => a.value ?? a.description ?? '').join(' ').slice(0, 300) });
      else if (e.method === 'Log.entryAdded' && ['error', 'warning'].includes(e.params.entry.level))
        rec.log.push({ level: e.params.entry.level, source: e.params.entry.source, text: e.params.entry.text.slice(0, 300) });
    }
  } catch (e) { rec.error = String(e).slice(0, 300); }
  try { ws?.close(); } catch {}
  ch.kill('SIGKILL'); await sleep(300);
  fs.rmSync(ud, { recursive: true, force: true });
  fs.writeSync(out, JSON.stringify(rec) + '\n');
  console.log(arm, page, rep, rec.error || '', 'exc', rec.exceptions.length, 'con', rec.console.length);
}
server.close();
