import { describe, expect, it } from 'vitest';

import { formatSize } from 'src/sections/agent-chat/attachmentText';

describe('formatSize', () => {
  it('says bytes under 1 KB, one decimal below 10 KB and whole KB above', () => {
    expect(formatSize(46)).toBe('46 B');
    expect(formatSize(1023)).toBe('1023 B');
    expect(formatSize(1024)).toBe('1.0 KB');
    expect(formatSize(10 * 1024 - 1)).toBe('10.0 KB');
    expect(formatSize(48 * 1024)).toBe('48 KB');
  });
});
