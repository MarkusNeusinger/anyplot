import { describe, it, expect, beforeEach } from 'vitest';

import { buildClaudePrompt } from './claudePrompt';

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
});
