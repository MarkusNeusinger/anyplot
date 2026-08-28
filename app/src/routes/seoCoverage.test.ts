// Drift guard for the machine-facing surface: the route registry in paths.ts,
// public/llms.txt, public/robots.txt and the SPA shell (index.html) must
// describe the SAME site and point at each other. Each of these has drifted
// silently before — a route missing from llms.txt, a guide findable only by
// guessing the convention, a shell that told a JS-less agent nothing — because
// nothing coupled them. This test is that coupling; the API side of the same
// contract (the API host's robots.txt, /llms.txt redirect, the bot-page nav)
// lives in tests/unit/api/test_routers.py.
//
// The files are read through Vite's `?raw` imports rather than node:fs so the
// test needs no Node typings — vitest resolves them exactly as the build does.

import { describe, expect, it } from 'vitest';

import shell from '../../index.html?raw';
import llmsTxt from '../../public/llms.txt?raw';
import robotsTxt from '../../public/robots.txt?raw';
import { paths } from './paths';

const ORIGIN = 'https://anyplot.ai';
const API = 'https://api.anyplot.ai';

// The public content routes are the top-level string values of paths, minus
// the ones that are deliberately absent from the machine guide: '/' is the
// document's own subject, /debug is an app internal (robots.txt disallows it),
// and the search deep link is a view of /plots, not a page.
const publicPaths = Object.values(paths)
  .flatMap(v => (typeof v === 'string' ? [v] : []))
  .filter(p => p !== paths.home && p !== paths.debug && !p.includes('?'));

// One complete, callable example per surface. Assistants' fetch tools often
// allow only URLs that already appeared verbatim in fetched content, so the
// same example pair must stand in the guide AND in the shell — a template with
// placeholders satisfies neither (kurrentschrift finding 2026-08-28).
const EXAMPLE_CODE_URL = `${API}/specs/bar-error/seaborn/code`;
const EXAMPLE_RENDER_URL =
  'https://storage.googleapis.com/anyplot-images/plots/bar-error/python/seaborn/plot-light.png';

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

describe('seo coverage', () => {
  it('llms.txt links every public content route', () => {
    // Word-boundary match, not substring: a link to /plots must not be
    // satisfied by /plots?focus=search, nor /specs by /specs/…. The literal
    // parts are regex-escaped — the dots in the origin would otherwise match
    // any character and quietly weaken the guard.
    for (const p of publicPaths) {
      expect(llmsTxt, `llms.txt lacks ${p}`).toMatch(
        new RegExp(`${escapeRe(ORIGIN + p)}(?![\\w./?-])`)
      );
    }
  });

  it('llms.txt carries the complete example pair and the machine surfaces', () => {
    expect(llmsTxt).toContain(EXAMPLE_CODE_URL);
    expect(llmsTxt).toContain(EXAMPLE_RENDER_URL);
    expect(llmsTxt).toContain(`${ORIGIN}/llms-full.txt`);
    expect(llmsTxt).toContain(`${API}/openapi.json`);
    expect(llmsTxt).toContain(`${API}/mcp/`);
  });

  it('robots.txt announces the sitemap and the machine guide, head and foot', () => {
    // Two terse lines at the very top for readers that only take the file
    // head seriously, the fuller block beside `Sitemap:` for everyone else.
    const lines = robotsTxt.split('\n');
    expect(lines[0]).toBe(`# llms.txt (machine guide): ${ORIGIN}/llms.txt`);
    expect(lines[1]).toBe(`# OpenAPI: ${API}/openapi.json`);
    expect(robotsTxt).toContain(`Sitemap: ${ORIGIN}/sitemap.xml`);
    expect(robotsTxt).toContain(`${ORIGIN}/llms-full.txt`);
  });

  it('robots.txt uses only the three contentsignals.org tokens, in every group', () => {
    // `use=reference` used to ride along; it is not a signal, and a strict
    // parser may discard the whole line over an unknown token — taking the
    // three real ones with it.
    const signals = robotsTxt.split('\n').filter(l => l.startsWith('Content-Signal:'));
    const groups = robotsTxt.split('\n').filter(l => l.startsWith('User-agent:'));
    expect(signals).toHaveLength(groups.length);
    for (const s of signals) expect(s).toBe('Content-Signal: search=yes,ai-input=yes,ai-train=yes');
  });

  it('the SPA shell itself carries the machine fallback', () => {
    // Agents NOT in the nginx $is_bot map get the shell on every route, and
    // most read raw HTML without executing JS. The shell must therefore name
    // the machine guide and one complete, callable example per surface — in
    // the head link and the <noscript> block — as ABSOLUTE URLs.
    expect(shell).toContain('rel="alternate" type="text/plain" href="/llms.txt"');
    // The block itself lives in the body — a head comment mentions the tag
    // name too, so anchor the search after <body> rather than on the first
    // occurrence of the string.
    const bodyStart = shell.indexOf('<body>');
    const open = shell.indexOf('<noscript>', bodyStart);
    const close = shell.indexOf('</noscript>', open);
    expect(open, 'no <noscript> block in the body').toBeGreaterThan(bodyStart);
    const noscript = shell.slice(open, close);
    expect(noscript).toContain(`href="${ORIGIN}/llms.txt"`);
    expect(noscript).toContain(`href="${ORIGIN}/llms-full.txt"`);
    expect(noscript).toContain(`href="${EXAMPLE_CODE_URL}"`);
    expect(noscript).toContain(`href="${EXAMPLE_RENDER_URL}"`);
    expect(noscript).toContain(`href="${API}/openapi.json"`);
    expect(noscript).toContain(`href="${API}/mcp/"`);
    // No relative machine links may creep back into the fallback — a relative
    // href never appeared "verbatim in fetched content" as a full URL.
    expect(noscript).not.toMatch(/href="\//);
  });
});
