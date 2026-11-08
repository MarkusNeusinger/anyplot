// The Plausible bootstrap in the SPA shell (index.html) carries options whose loss
// shows up nowhere but in the dashboard. The served script defaults every auto-capture
// to on and merges the init options over its defaults, so dropping an option here
// silently turns that capture back on: `autoCapturePageviews` would double every
// pageview the app records itself, and `formSubmissions` would count each agent-chat
// message as a "Form: Submission" goal that the chat's own events already count.
//
// The shell is read through Vite's `?raw` import, as in src/routes/seoCoverage.test.ts.

import { describe, expect, it } from 'vitest';

import shell from '../../index.html?raw';

function initOptions(): string {
  const match = shell.match(/plausible\.init\(\{([^}]*)\}\)/);
  if (!match) throw new Error('index.html has no plausible.init({ … }) call');
  return match[1];
}

describe('Plausible init in index.html', () => {
  it('keeps the form-submission auto-goal off', () => {
    expect(initOptions()).toMatch(/\bformSubmissions:\s*false\b/);
  });

  it('keeps pageviews manual', () => {
    expect(initOptions()).toMatch(/\bautoCapturePageviews:\s*false\b/);
  });

  it('posts events through the shielded /api/event proxy', () => {
    expect(initOptions()).toMatch(/\bendpoint:\s*'\/api\/event'/);
  });
});
