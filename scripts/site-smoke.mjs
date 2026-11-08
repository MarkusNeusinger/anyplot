// Smoke test: does the site render? Run it after every merge to main, once the
// deploys the merge triggered have finished (CLAUDE.md, open-pr skill section
// 4); the app-image job of ci-image.yml runs it against the built container
// before the merge. A green PR did not prove the bundle boots: on 2026-10-22 a
// Vite minor bump (#12225) passed every check and blanked every page with
// `TypeError: t is not a function` until #12235.
//
// Per page it fails on a status other than 200, an uncaught page error, a
// page whose #root holds next to no text, or the app's error boundary ("Something
// went wrong", "A new version is available"), which keeps the masthead and
// footer around a failed route; the <h1> is printed for the reader only, since
// some pages (`/plots`) have none, and so is the entry bundle (`index-*.js`),
// which tells which deploy answered. It also checks the API's /health. Console
// errors are printed as warnings only, since third-party noise (an analytics
// blocker, a GitHub rate limit) is not an outage. Exit code 0 means every
// check passed, 1 means at least one failed, 2 means none failed but something
// went unchecked: no browser could be found or started, or Cloudflare answered
// a page with a challenge (SMOKE_TOKEN below).
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
//
// SMOKE_TOKEN: Cloudflare classes headless Chromium as "definitely automated",
// so once Super Bot Fight Mode challenges that group every page here would see
// a challenge page instead of the site. A WAF skip rule lets a request through
// that phase when it carries `X-Smoke-Token` with the right value
// (infra/cloudflare/README.md, "Security rules"). The value lives only in the
// dev box's .env and in that rule, never in the repository; the open-pr skill's
// recipe passes it in. The header goes only to requests for SITE's own origin,
// so neither the API host nor a third party ever sees it, and the script never
// prints it. Unset, nothing is sent. CI's "Browser boot" step runs against
// localhost, where no Cloudflare stands in between, and never needs it. A page
// Cloudflare challenged anyway says nothing about the site behind it, so its
// line reads SKIP, not FAIL, and names the challenge.

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
const SMOKE_TOKEN = process.env.SMOKE_TOKEN || '';
const SITE_ORIGIN = new URL(SITE).origin;

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
let browser;
try {
  browser = await chromium.launch({ executablePath });
} catch (e) {
  // A browser that will not start (missing libraries, a sandbox) checked nothing: not an incident.
  console.log(`FAIL\tthe browser at ${executablePath} did not start: ${e.message.split('\n')[0]}`);
  process.exit(2);
}

// A context of its own per page, as browser.newPage() gives, so no page inherits another's cookies.
// The token is added by a route rather than extraHTTPHeaders: those go out with every request of
// the context, the page's calls to the API host and to third parties included.
async function openPage() {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  if (SMOKE_TOKEN) {
    await context.route(
      (u) => u.origin === SITE_ORIGIN,
      (route) => route.continue({ headers: { ...route.request().headers(), 'x-smoke-token': SMOKE_TOKEN } }),
    );
  }
  return context.newPage();
}

let challenged = 0;
for (const path of pages) {
  const url = `${SITE}${path.startsWith('/') ? path : `/${path}`}`;
  const page = await openPage();
  let challenge = false;
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
    // Cloudflare marks its challenge pages; such a page says nothing about the site behind it.
    challenge = response?.headers()['cf-mitigated'] === 'challenge';
    // A challenge page never grows the app's #root, so waiting for it would only burn the timeouts.
    if (!challenge) {
      // The app renders client-side: wait for #root to fill, bounded, then read it.
      await page
        .waitForFunction((min) => (document.getElementById('root')?.innerText.length ?? 0) >= min, MIN_TEXT, {
          timeout: 15000,
        })
        .catch(() => {});
      // The layout chrome alone can pass the text threshold while the route's lazy chunk still
      // loads, so let the network settle (bounded) before the route is judged.
      await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
    }
  } catch (e) {
    pageErrors.push(`navigation: ${e.message.split('\n')[0]}`);
  }
  const seen = await page
    .evaluate(() => {
      const text = document.getElementById('root')?.innerText ?? '';
      const entry = document.querySelector('script[type="module"][src*="/assets/index-"]')?.getAttribute('src');
      return {
        text: text.length,
        boundary: text.match(/Something went wrong|A new version is available/)?.[0] ?? null,
        h1: document.querySelector('h1')?.innerText.trim().slice(0, 60) ?? null,
        bundle: entry ? entry.split('/').pop() : null,
      };
    })
    .catch(() => ({ text: 0, boundary: null, h1: null, bundle: null }));
  const ok = status === 200 && pageErrors.length === 0 && seen.text >= MIN_TEXT && !seen.boundary;
  const skipped = !ok && challenge;
  if (skipped) challenged += 1;
  else if (!ok) failed += 1;
  const detail =
    (skipped ? `\tchallenged by Cloudflare, not checked (SMOKE_TOKEN ${SMOKE_TOKEN ? 'sent' : 'unset'})` : '') +
    (pageErrors.length ? `\tpageerror: ${pageErrors.slice(0, 2).join(' | ')}` : '') +
    (seen.boundary ? `\terror boundary: "${seen.boundary}"` : '');
  const warn = consoleErrors.length ? `\tconsole errors (warning): ${consoleErrors.length}` : '';
  console.log(
    `${ok ? 'OK  ' : skipped ? 'SKIP' : 'FAIL'}\t${url}\tstatus=${status}\ttext=${seen.text}` +
      `\th1=${JSON.stringify(seen.h1)}\tbundle=${seen.bundle}${detail}${warn}`,
  );
  await page.context().close();
}
await browser.close();
if (failed) {
  console.log(`${failed} check(s) failed${challenged ? `, ${challenged} not checked` : ''}: treat it as an incident`);
} else if (challenged) {
  console.log(`${challenged} page(s) challenged by Cloudflare, so not checked: check SMOKE_TOKEN and the smoke bypass`);
} else {
  console.log('all checks passed');
}
process.exit(failed ? 1 : challenged ? 2 : 0);
