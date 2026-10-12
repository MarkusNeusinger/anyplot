import { describe, expect, it } from 'vitest';

import { acceptMatch, expectedFromReaction } from 'src/sections/debug/acceptMatch';

describe('acceptMatch', () => {
  it.each([
    ['thumbs_up', 'ok', true],
    ['thumbs_up', 'needs_attention', false],
    ['thumbs_up', null, null],
    ['thumbs_down', 'ok', false],
    ['thumbs_down', 'needs_attention', true],
    ['thumbs_down', null, null],
    ['bug', 'ok', null],
    ['bug', 'needs_attention', null],
    ['bug', null, null],
    ['idea', 'ok', null],
    ['idea', 'needs_attention', null],
    ['idea', null, null],
  ] as const)('%s with %s is %s', (reaction, status, expected) => {
    expect(acceptMatch(reaction, status)).toBe(expected);
  });

  it('counts any status but ok as rejected', () => {
    expect(acceptMatch('thumbs_down', 'failed')).toBe(true);
    expect(acceptMatch('thumbs_up', 'not_ready')).toBe(false);
  });

  it('gives the thumbs an outcome and a bug or an idea none', () => {
    expect(expectedFromReaction('thumbs_up')).toBe('accepted');
    expect(expectedFromReaction('thumbs_down')).toBe('rejected');
    expect(expectedFromReaction('bug')).toBeNull();
    expect(expectedFromReaction('idea')).toBeNull();
  });
});
