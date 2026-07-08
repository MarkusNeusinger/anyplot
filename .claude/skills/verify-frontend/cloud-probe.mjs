// Cloud fallback browser harness for /verify-frontend when no browser
// MCP is available (Claude Code on the web). Drives the pre-installed
// Chromium directly via playwright-core and reports the routine "did my
// change break layout" channels — overflow, the h1 type voice, console
// errors, and a screenshot per viewport — as machine-readable lines
// (exact pixels, not vibes). Extend the evaluate() block for per-task
// measurements (size ratios, specific rects).
//
// Run (playwright-core lives in the scratchpad, not the repo):
//   SCRATCH=/tmp/claude-.../scratchpad
//   cd "$SCRATCH" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright-core
//   NODE_PATH="$SCRATCH/node_modules" node .claude/skills/verify-frontend/cloud-probe.mjs \
//     http://localhost:3000/ http://localhost:3000/plots
//
// NODE_PATH does NOT reach ESM bare imports, so playwright-core is loaded
// via createRequire (which honours it). SHOTS overrides the output dir.
// Ported from the kurrentschrift verify-frontend probe.

import { createRequire } from 'node:module';
import { existsSync, readdirSync, mkdirSync } from 'node:fs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright-core');

// Resolve the pre-installed Chromium (version-pinned dir under PLAYWRIGHT_BROWSERS_PATH).
const root = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
if (!existsSync(root)) throw new Error(`browsers dir not found: ${root} — set PLAYWRIGHT_BROWSERS_PATH (cloud container only)`);
const dir = readdirSync(root)
  .filter((d) => /^chromium-\d+$/.test(d))
  .sort((a, b) => Number(b.slice(9)) - Number(a.slice(9)))[0]; // newest revision, deterministically
if (!dir) throw new Error(`no chromium-<rev> dir under ${root}`);
const executablePath = `${root}/${dir}/chrome-linux/chrome`;
if (!existsSync(executablePath)) throw new Error(`chromium binary missing: ${executablePath}`);

const urls = process.argv.slice(2);
if (urls.length === 0) urls.push('http://localhost:3000/');
const shots = process.env.SHOTS || '/tmp/anyplot-ui';
mkdirSync(shots, { recursive: true });

// Desktop + the mobile width the skill mandates; extras catch column overflow.
const widths = (process.env.WIDTHS || '1440,390,360,320').split(',').map(Number);

const browser = await chromium.launch({ executablePath });
for (const url of urls) {
  const slug = url.replace(/^https?:\/\//, '').replace(/[^a-z0-9]+/gi, '-').replace(/-+$/, '');
  for (const width of widths) {
    const ctx = await browser.newContext({ viewport: { width, height: 844 }, deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    const errors = [];   // JS errors (console text carries no URL for failed resources)
    const bad = [];      // 4xx/5xx responses, with URL — favicon + GitHub rate-limit noise filtered
    page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
    page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push(m.text()); });
    page.on('response', (r) => {
      const s = r.status();
      if (s >= 400 && !/favicon\.ico/.test(r.url()) && !/api\.github\.com/.test(r.url())) bad.push(`${s} ${r.url().replace(/^https?:\/\/[^/]+/, '')}`);
    });
    page.on('requestfailed', (r) => { if (!/favicon\.ico/.test(r.url())) errors.push(`requestfailed ${r.url().replace(/^https?:\/\/[^/]+/, '')}`); });

    // domcontentloaded first, then a *bounded* networkidle: a bare
    // networkidle can hang because Vite's HMR websocket never lets the network
    // settle, so cap it — the lazy route chunk + render normally finishes well
    // inside the timeout, and measurement proceeds even if it doesn't idle.
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});

    const data = await page.evaluate(() => {
      const docW = document.documentElement.scrollWidth;
      const winW = window.innerWidth;
      let culprit = null;
      if (docW > winW) {
        for (const el of document.querySelectorAll('*')) {
          const r = el.getBoundingClientRect();
          if (r.right > winW + 1 && (!culprit || r.width > culprit.width)) {
            culprit = {
              tag: el.tagName.toLowerCase(),
              cls: (el.className && el.className.toString().slice(0, 40)) || '',
              width: Math.round(r.width),
            };
          }
        }
      }
      const h1 = document.querySelector('h1');
      return {
        docW, winW, culprit,
        h1: h1 ? { fontSize: getComputedStyle(h1).fontSize, family: getComputedStyle(h1).fontFamily.split(',')[0] } : null,
      };
    });

    await page.screenshot({ path: `${shots}/${slug}-${width}.png` });
    const ov = data.culprit ? `OVERFLOW doc=${data.docW}>${data.winW} ${JSON.stringify(data.culprit)}` : 'ok';
    const issues = [...new Set([...errors, ...bad])];
    console.log(`${slug}\tw=${width}\t${ov}\th1=${data.h1?.fontSize} ${data.h1?.family}\tissues=${issues.length}${issues.length ? ' :: ' + issues.slice(0, 2).join(' | ') : ''}`);
    await ctx.close();
  }
}
await browser.close();
console.log('screenshots ->', shots);
