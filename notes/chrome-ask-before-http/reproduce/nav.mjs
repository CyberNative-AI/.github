// Does a fresh-profile Chrome show the HTTP warning ("Ask before HTTP") on http:// origins?
// usage: node nav.mjs <chrome-binary> <arm> <origins.txt> <out.jsonl> [workers]
// One fresh profile (tmpfs) per origin, so site engagement never carries over. Raw CDP, no Playwright.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
const [bin, arm, listFile, outFile, workersArg] = process.argv.slice(2);
const WORKERS = Number(workersArg || 6);
const NAV_TIMEOUT_MS = 30000, SETTLE_MS = 2500;
const TRANSITION = process.env.TRANSITION || 'link';
const SHOTS = process.env.SHOTS || '';
const origins = fs.readFileSync(listFile, 'utf8').split('\n').map(s => s.trim()).filter(Boolean);
const done = new Set();
if (fs.existsSync(outFile)) for (const l of fs.readFileSync(outFile, 'utf8').split('\n')) if (l) done.add(JSON.parse(l).origin);
const out = fs.openSync(outFile, 'a');
const sleep = ms => new Promise(r => setTimeout(r, ms));
let portSeq = 0;

async function probe(origin, wid) {
  const port = 9400 + wid * 10 + (portSeq++ % 10);
  const ud = fs.mkdtempSync(`/tmp/ud-${arm}-`);
  const ch = spawn(bin, [...(process.env.HEADFUL ? [] : ['--headless=new']), '--no-sandbox', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    `--remote-debugging-port=${port}`, `--user-data-dir=${ud}`, '--window-size=1366,768', ...(process.env.EXTRA_FLAGS ? process.env.EXTRA_FLAGS.split(' ') : []), 'about:blank'], { stdio: 'ignore' });
  const rec = { arm, origin, t0: new Date().toISOString() };
  let ws;
  try {
    let ver; for (let i = 0; i < 60 && !ver; i++) { try { ver = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); } catch { await sleep(250); } }
    if (!ver) throw new Error('no_cdp');
    rec.browser = ver.Browser;
    const tgt = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page');
    ws = new WebSocket(tgt.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
    let id = 0; const pend = new Map(); const ev = [];
    ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id) { pend.get(d.id)?.(d); pend.delete(d.id); } else ev.push(d); };
    const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
    await send('Page.enable');
    const tNav = Date.now();
    const nav = await Promise.race([send('Page.navigate', { url: origin + '/', transitionType: TRANSITION }), sleep(NAV_TIMEOUT_MS).then(() => ({ timeout: true }))]);
    rec.navErrorText = nav.result?.errorText ?? null; rec.navTimeout = !!nav.timeout;
    for (let waited = 0; waited < NAV_TIMEOUT_MS && !ev.some(e => e.method === 'Page.loadEventFired'); waited += 250) await sleep(250);
    rec.loadEvent = ev.some(e => e.method === 'Page.loadEventFired');
    await sleep(SETTLE_MS);
    rec.ms = Date.now() - tNav;
    const hist = await send('Page.getNavigationHistory');
    const cur = hist.result?.entries?.[hist.result.currentIndex];
    rec.entryUrl = cur?.url ?? null; rec.entryTitle = cur?.title ?? null; rec.entryType = cur?.transitionType ?? null;
    const evalr = await Promise.race([send('Runtime.evaluate', { returnByValue: true, expression:
      `JSON.stringify({href: location.href, title: document.title,
        ltdType: (typeof loadTimeDataRaw !== 'undefined' && loadTimeDataRaw) ? (loadTimeDataRaw.type || null) : null,
        ltdHeading: (typeof loadTimeDataRaw !== 'undefined' && loadTimeDataRaw) ? (loadTimeDataRaw.heading || null) : null,
        mainMessage: (document.getElementById('main-message')||{}).innerText?.slice(0,300) || null,
        errorCode: (document.querySelector('.error-code')||{}).innerText || null,
        body: (document.body && document.body.innerText || '').slice(0, 300)})` }), sleep(8000).then(() => null)]);
    Object.assign(rec, evalr?.result?.result?.value ? JSON.parse(evalr.result.result.value) : { evalFailed: true });
    if (SHOTS) { const sh = await send('Page.captureScreenshot', { format: 'png' }); if (sh.result?.data) fs.writeFileSync(`${SHOTS}/${arm}-${origin.replace(/[^a-z0-9.]/gi, '_')}.png`, Buffer.from(sh.result.data, 'base64')); }
    rec.transition = TRANSITION;
    rec.mainFrameUrls = ev.filter(e => e.method === 'Page.frameNavigated' && !e.params.frame.parentId).map(e => e.params.frame.url);
  } catch (e) { rec.error = String(e.message || e); }
  try { ws?.close(); } catch {}
  ch.kill('SIGKILL'); await sleep(300);
  try { fs.rmSync(ud, { recursive: true, force: true }); } catch {}
  return rec;
}

const queue = origins.filter(o => !done.has(o));
let next = 0;
await Promise.all(Array.from({ length: WORKERS }, async (_, wid) => {
  while (next < queue.length) { const o = queue[next++]; const r = await probe(o, wid); fs.writeSync(out, JSON.stringify(r) + '\n'); }
}));
fs.closeSync(out);
