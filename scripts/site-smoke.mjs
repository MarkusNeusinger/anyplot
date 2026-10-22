// Smoke test: does the site render? Run it after every merge to main, once the
// deploys the merge triggered have finished (CLAUDE.md, open-pr skill section
// 4); the app-image job of ci-image.yml runs it against the built container
// before the merge. A green PR did not prove the bundle boots: on 2026-10-22 a
// Vite minor bump (#12225) passed every check and blanked every page with
// `TypeError: t is not a function` until #12235.
//
// Per page it fails on a status other than 200, an uncaught page error, or a
// page whose #root holds next to no text; the <h1> is printed for the reader
// only, since some pages (`/plots`) have none. It also checks the API's
// /health. Console
// errors are printed as warnings only, since third-party noise (an analytics
// blocker, a GitHub rate limit) is not an outage. Exit code 0 means every
// check passed, 1 means at least one failed, 2 means the browser could not
// start.
//
// Run (playwright-core lives in the scratchpad, not the repo):
//   SCRATCH=<the session scratchpad>
//   cd "$SCRATCH" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i --silent playwright-core@1.64.1
//   NODE_PATH="$SCRATCH/node_modules" node scripts/site-smoke.mjs
//
// Optional arguments replace the default pages. SITE and API override the
// origins (SITE=http://localhost:3000 against a dev server, API=none to skip
// the health check), CHROME_PATH names a browser binary (CI's Google Chrome),
// and MIN_TEXT the characters a rendered #root must hold. NODE_PATH does not
// reach ESM bare imports, so playwright-core is loaded through createRequire,
// which honours it.

import { createRequire } from 'node:module';
import { existsSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright-core');

const SITE = (process.env.SITE || 'https://anyplot.ai').replace(/\/$/, '');
const API = (process.env.API || 'https://api.anyplot.ai').replace(/\/$/, '');
const pages = process.argv.slice(2);
if (pages.length === 0) pages.push('/', '/plots', '/scatter-basic');
// A rendered page carries far more; the blank page of #12225 carried none.
const MIN_TEXT = Number(process.env.MIN_TEXT || 200);

// A browser that is already on the machine: CHROME_PATH, the cloud container's
// Chromium, or the one the Playwright MCP plugin installed locally. Never
// download one.
function findChromium() {
  if (process.env.CHROME_PATH) return existsSync(process.env.CHROME_PATH) ? process.env.CHROME_PATH : null;
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH, '/opt/pw-browsers', `${homedir()}/.cache/ms-playwright`];
  for (const root of roots.filter(Boolean)) {
    if (!existsSync(root)) continue;
    const revisions = readdirSync(root)
      .filter((d) => /^chromium-\d+$/.test(d))
      .sort((a, b) => Number(b.slice(9)) - Number(a.slice(9)));
    for (const rev of revisions) {
      for (const sub of ['chrome-linux/chrome', 'chrome-linux64/chrome']) {
        const path = `${root}/${rev}/${sub}`;
        if (existsSync(path)) return path;
      }
    }
  }
  return null;
}

let failed = 0;

if (API !== 'none') {
  const health = await fetch(`${API}/health`).then(
    (r) => r.status,
    (e) => `error ${e.message}`,
  );
  console.log(`${health === 200 ? 'OK  ' : 'FAIL'}\t${API}/health\tstatus=${health}`);
  if (health !== 200) failed += 1;
}

const executablePath = findChromium();
if (!executablePath) {
  console.log('FAIL\tno browser found (CHROME_PATH, PLAYWRIGHT_BROWSERS_PATH, /opt/pw-browsers, ~/.cache/ms-playwright)');
  process.exit(2);
}
const browser = await chromium.launch({ executablePath });
for (const path of pages) {
  const url = `${SITE}${path.startsWith('/') ? path : `/${path}`}`;
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', (e) => pageErrors.push(e.message));
  page.on('console', (m) => {
    if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) consoleErrors.push(m.text());
  });
  let status = 'no response';
  try {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    status = response ? response.status() : status;
    // The app renders client-side: wait for #root to fill, bounded, then read it.
    await page
      .waitForFunction((min) => (document.getElementById('root')?.innerText.length ?? 0) >= min, MIN_TEXT, {
        timeout: 15000,
      })
      .catch(() => {});
  } catch (e) {
    pageErrors.push(`navigation: ${e.message.split('\n')[0]}`);
  }
  const seen = await page
    .evaluate(() => ({
      text: document.getElementById('root')?.innerText.length ?? 0,
      h1: document.querySelector('h1')?.innerText.trim().slice(0, 60) ?? null,
    }))
    .catch(() => ({ text: 0, h1: null }));
  const ok = status === 200 && pageErrors.length === 0 && seen.text >= MIN_TEXT;
  if (!ok) failed += 1;
  const detail = pageErrors.length ? `\tpageerror: ${pageErrors.slice(0, 2).join(' | ')}` : '';
  const warn = consoleErrors.length ? `\tconsole errors (warning): ${consoleErrors.length}` : '';
  console.log(`${ok ? 'OK  ' : 'FAIL'}\t${url}\tstatus=${status}\ttext=${seen.text}\th1=${JSON.stringify(seen.h1)}${detail}${warn}`);
  await page.close();
}
await browser.close();
console.log(failed ? `${failed} check(s) failed: treat it as an incident` : 'all checks passed');
process.exit(failed ? 1 : 0);
