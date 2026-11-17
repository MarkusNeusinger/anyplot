import { beforeEach, describe, expect, it } from 'vitest';

import { buildClaudePrompt } from 'src/utils/claudePrompt';

describe('buildClaudePrompt', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, origin: 'https://anyplot.ai', href: 'https://anyplot.ai/debug' },
    });
  });

  it.each([
    ['bug', 'bug report'],
    ['idea', 'feature request'],
    ['thumbs_down', 'negative feedback'],
    ['thumbs_up', 'positive feedback'],
    [null, 'feedback'],
    ['unknown_reaction', 'feedback'],
  ])('labels reaction %s as %s', (reaction, label) => {
    const out = buildClaudePrompt('hi', '/plots/x', reaction);
    expect(out).toContain(`following ${label} on`);
  });

  it('prefixes the path with the current origin', () => {
    const out = buildClaudePrompt('msg', '/plots/scatter-basic', 'bug');
    expect(out).toContain('on https://anyplot.ai/plots/scatter-basic:');
  });

  it('falls back to the origin when path is null', () => {
    const out = buildClaudePrompt('msg', null, 'bug');
    expect(out).toContain('on https://anyplot.ai:');
    expect(out).not.toContain('null');
  });

  it('uses "(unknown URL)" when origin and path are both empty', () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, origin: '' },
    });
    const out = buildClaudePrompt('msg', null, null);
    expect(out).toContain('on (unknown URL):');
  });

  it('quotes every line of multi-line messages', () => {
    const out = buildClaudePrompt('line one\nline two\nline three', '/p', 'idea');
    expect(out).toContain('> line one\n> line two\n> line three');
  });

  it('includes the three-step instruction block', () => {
    const out = buildClaudePrompt('hi', '/p', 'bug');
    expect(out).toMatch(/Analyze the report/);
    expect(out).toMatch(/Implement a fix/);
    expect(out).toMatch(/Open a pull request/);
  });

  // The legal page's site feedback row (src/pages/LegalPage.tsx) names the message, the page and
  // the reaction as what can go to the coding assistant: a fourth parameter changes that row too.
  it('carries the message, the page and the reaction of an entry and none of its other fields', () => {
    const entry = {
      id: 'entry-id-5c1e',
      message: 'The legend hides the last bar',
      path: '/plots/bar-basic',
      reaction: 'bug',
      contact: 'reader@example.com',
      session_id: 'random-id-9a47',
      user_agent: 'Mozilla/5.0 (TestAgent)',
      viewport: '390x844',
    };
    expect(buildClaudePrompt).toHaveLength(3);

    const out = buildClaudePrompt(entry.message, entry.path, entry.reaction);
    expect(out).toContain('> The legend hides the last bar');
    expect(out).toContain('on https://anyplot.ai/plots/bar-basic:');
    expect(out).toContain('following bug report on');
    for (const field of [
      entry.contact,
      entry.id,
      entry.session_id,
      entry.user_agent,
      entry.viewport,
    ]) {
      expect(out).not.toContain(field);
    }
  });

  // The repository is public: the visitor's words stay out of what a session publishes there.
  it('asks to keep the quoted message out of commits, pull requests and issues', () => {
    const out = buildClaudePrompt('hi', '/p', 'bug');
    expect(out).toContain(
      'Do not quote the message in a commit, a pull request or an issue; describe the problem in your own words.'
    );
  });
});
