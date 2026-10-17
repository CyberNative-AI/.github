// Runs live-region-check.js against the study's control page (three arms) in headless Chromium.
// usage: node test_snippet.mjs <playwright-core dir> <base URL of controls/> <snippet path>
import fs from 'node:fs';
import { createRequire } from 'node:module';
const [pwDir, base, snippetPath] = process.argv.slice(2);
const { chromium } = createRequire(import.meta.url)(pwDir);
const SNIPPET = fs.readFileSync(snippetPath, 'utf8');
const expect = {
  silent: (r) => r.liveRegions.length === 0 && r.replyInsideLiveRegion === null && r.changesInsideLiveRegionsSincePaste === 0,
  once: (r) => r.replyInsideLiveRegion === 'div[role=log]' && r.changesInsideLiveRegionsSincePaste <= 3,
  chatter: (r) => r.replyInsideLiveRegion === 'div[aria-live=polite]' && r.changesInsideLiveRegionsSincePaste >= 50,
};
const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {});
let fail = 0;
for (const arm of Object.keys(expect)) {
  const page = await browser.newPage();
  await page.goto(`${base}/index.html?arm=${arm}`);
  await page.waitForFunction(() => document.readyState === 'complete');
  await page.waitForTimeout(300);
  await page.evaluate(SNIPPET);
  await page.fill('#q', 'Tell me about Lyon');
  await page.click('button[type=submit]');
  await page.waitForFunction(() => document.body.innerText.includes('ZETAEND'), null, { timeout: 15000 });
  await page.waitForTimeout(500);
  const r = await page.evaluate(() => window.liveCheck('ZETAEND'));
  const ok = expect[arm](r);
  if (!ok) fail += 1;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${arm} ${JSON.stringify(r)}`);
  await page.close();
}
await browser.close();
process.exit(fail ? 1 : 0);
