// Screenshot helper for the site-auditor of /audit: loads public pages in a
// headless Chromium of its own and saves one PNG plus one line of facts per
// page, so the auditor judges what a visitor sees and not what the code implies.
// Its own browser on purpose: the Playwright MCP browser has one "current tab"
// for every session on the machine, and parallel auditors would steer each
// other's pages.
//
// Run from the repository root (playwright-core lives in the scratchpad, not the
// repo, as for scripts/site-smoke.mjs; the install runs in a subshell so the
// shell stays in the repository):
//   SCRATCH=<the session scratchpad>
//   [ -d "$SCRATCH/node_modules/playwright-core" ] || \
//     (cd "$SCRATCH" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i --silent playwright-core@1.64.1)
//   MAIN=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
//   SMOKE_TOKEN="$(grep -E '^SMOKE_TOKEN=' "$MAIN/.env" | cut -d= -f2-)" \
//     NODE_PATH="$SCRATCH/node_modules" node agentic/commands/audit/site-shots.mjs \
//     --out "$SCRATCH/shots" [--viewport desktop|tablet|mobile] [--theme light|dark] \
//     [--full] [--scroll <px>] [--wait <ms>] <path-or-url>...
//
// A path ("/plots") is resolved against SITE (default https://anyplot.ai); a
// full URL is used as it is. Per page it prints: the status, the final URL, the
// load time, <title>, <h1>, the text length, the page height, whether the page
// scrolls horizontally, and the counts of console errors, page errors and
// failed requests (the first few of each). NODE_PATH does not reach ESM bare
// imports, so playwright-core is loaded through createRequire, which honours it.
//
// SMOKE_TOKEN follows scripts/site-smoke.mjs: sent as X-Smoke-Token only to
// https requests for the site's own hosts and never to /api paths, so neither
// the API host nor a third party sees it; never printed; unset, nothing is sent.
//
// The page is left for about:blank before its context closes. A page that holds
// a server-side session (the agent chat) frees it on pagehide; a context closed
// without one keeps the session until the idle sweep, and those sessions count
// against the per-network cap the owner's own browser shares.

import { createRequire } from 'node:module';
import { existsSync, mkdirSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright-core');

const SITE = (process.env.SITE || 'https://anyplot.ai').replace(/\/$/, '');
const SMOKE_TOKEN = process.env.SMOKE_TOKEN || '';
const VIEWPORTS = {
  desktop: { width: 1440, height: 900 },
  tablet: { width: 820, height: 1180 },
  mobile: { width: 390, height: 844 },
};
const USAGE =
  'usage: node site-shots.mjs --out DIR [--viewport desktop|tablet|mobile] [--theme light|dark] ' +
  '[--full] [--scroll PX] [--wait MS] PATH_OR_URL...';

const opt = { out: '', viewport: 'desktop', theme: 'light', full: false, wait: 1200, scroll: 0 };
const targets = [];
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i += 1) {
  const arg = argv[i];
  if (arg === '--out') opt.out = argv[(i += 1)] ?? '';
  else if (arg === '--viewport') opt.viewport = argv[(i += 1)] ?? '';
  else if (arg === '--theme') opt.theme = argv[(i += 1)] ?? '';
  else if (arg === '--wait') opt.wait = Number(argv[(i += 1)]);
  else if (arg === '--scroll') opt.scroll = Number(argv[(i += 1)]);
  else if (arg === '--full') opt.full = true;
  else targets.push(arg);
}
const valid =
  opt.out &&
  targets.length > 0 &&
  VIEWPORTS[opt.viewport] &&
  ['light', 'dark'].includes(opt.theme) &&
  Number.isFinite(opt.wait) &&
  Number.isFinite(opt.scroll);
if (!valid) {
  console.log(USAGE);
  process.exit(2);
}
// Resolved before a browser starts: a target that is no URL ends the run here, not in the middle of it.
const urls = targets.map((target) => {
  const text = /^https?:\/\//.test(target) ? target : `${SITE}${target.startsWith('/') ? target : `/${target}`}`;
  return URL.canParse(text) ? new URL(text) : null;
});
if (urls.includes(null)) {
  console.log(`not a path or URL: ${targets[urls.indexOf(null)]}`);
  process.exit(2);
}
mkdirSync(opt.out, { recursive: true });

// The hosts the Cloudflare smoke bypass matches; anywhere else the token means nothing.
const TOKEN_HOSTS = new Set(['anyplot.ai', 'www.anyplot.ai', 'python.anyplot.ai']);
const carriesToken = (u) =>
  u.protocol === 'https:' && TOKEN_HOSTS.has(u.hostname) && !/^\/api(\/|$)/.test(u.pathname);

// A browser that is already on the machine; never download one.
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

// One file per page, viewport, theme and scroll position, so a second run overwrites only its own shots.
function shotPath({ hostname, pathname }) {
  const host = hostname === new URL(SITE).hostname ? '' : `${hostname}_`;
  const page = pathname.replace(/^\/|\/$/g, '').replace(/[^A-Za-z0-9._-]+/g, '_') || 'home';
  const suffix = `${opt.scroll ? `-y${opt.scroll}` : ''}${opt.full ? '-full' : ''}`;
  return `${opt.out}/${host}${page}__${opt.viewport}-${opt.theme}${suffix}.png`;
}

const executablePath = findChromium();
if (!executablePath) {
  console.log('no browser found (CHROME_PATH, PLAYWRIGHT_BROWSERS_PATH, /opt/pw-browsers, ~/.cache/ms-playwright)');
  process.exit(2);
}
const browser = await chromium.launch({ executablePath });
const mobile = opt.viewport === 'mobile';
const few = (items, n) => (items.length ? ` [${items.slice(0, n).join(' | ')}]` : '');

async function shoot(url) {
  // A context of its own per page, so no page inherits another's cookies or storage.
  const context = await browser.newContext({
    viewport: VIEWPORTS[opt.viewport],
    colorScheme: opt.theme,
    isMobile: mobile,
    hasTouch: mobile,
  });
  try {
    await shootIn(context, url);
  } finally {
    await context.close().catch(() => {});
  }
}

async function shootIn(context, url) {
  if (SMOKE_TOKEN) {
    // A request the page aborts in flight rejects its `continue`; that is the page's business, not an error here.
    await context.route(carriesToken, (route) =>
      route.continue({ headers: { ...route.request().headers(), 'x-smoke-token': SMOKE_TOKEN } }).catch(() => {}),
    );
  }
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const failedRequests = [];
  page.on('pageerror', (e) => pageErrors.push(e.message.split('\n')[0]));
  page.on('console', (m) => {
    if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200));
  });
  page.on('response', (r) => {
    if (r.status() >= 400) failedRequests.push(`${r.status()} ${r.url().slice(0, 120)}`);
  });

  let status = 'no response';
  let challenge = false;
  const started = Date.now();
  try {
    const response = await page.goto(url.href, { waitUntil: 'domcontentloaded', timeout: 30000 });
    status = response ? response.status() : status;
    // Cloudflare marks its challenge pages; such a page says nothing about the site behind it.
    challenge = response?.headers()['cf-mitigated'] === 'challenge';
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(opt.wait);
    if (opt.scroll) {
      await page.evaluate((y) => window.scrollTo(0, y), opt.scroll);
      await page.waitForTimeout(600);
    }
  } catch (e) {
    pageErrors.push(`navigation: ${e.message.split('\n')[0]}`);
  }
  const loadMs = Date.now() - started;

  const seen = await page
    .evaluate(() => ({
      title: document.title,
      h1: document.querySelector('h1')?.innerText.trim().slice(0, 80) ?? null,
      text: (document.body?.innerText ?? '').length,
      height: document.documentElement.scrollHeight,
      overflowX: document.documentElement.scrollWidth > window.innerWidth,
    }))
    .catch(() => ({ title: null, h1: null, text: 0, height: 0, overflowX: false }));
  const file = shotPath(url);
  await page
    .screenshot({ path: file, fullPage: opt.full })
    .catch((e) => pageErrors.push(`screenshot: ${e.message.split('\n')[0]}`));

  console.log(
    [
      `status=${status}${challenge ? ' (Cloudflare challenge, not the site)' : ''}`,
      `url=${page.url()}`,
      `ms=${loadMs}`,
      `title=${JSON.stringify(seen.title)}`,
      `h1=${JSON.stringify(seen.h1)}`,
      `text=${seen.text}`,
      `pageHeight=${seen.height}`,
      `horizontalOverflow=${seen.overflowX}`,
      `consoleErrors=${consoleErrors.length}${few(consoleErrors, 2)}`,
      `pageErrors=${pageErrors.length}${few(pageErrors, 2)}`,
      `failedRequests=${failedRequests.length}${few(failedRequests, 3)}`,
      `png=${file}`,
    ].join('\t'),
  );

  await page.goto('about:blank').catch(() => {});
  await page.waitForTimeout(400).catch(() => {});
}

// The browser is closed whatever a page does: a run that dies half-way must not leave a Chromium behind.
try {
  for (const url of urls) await shoot(url);
} finally {
  await browser.close().catch(() => {});
}
