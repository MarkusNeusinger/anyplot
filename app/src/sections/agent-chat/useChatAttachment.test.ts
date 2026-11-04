import { describe, expect, it } from 'vitest';

import {
  insertedText,
  MAX_ATTACHMENT_LINES,
  overCap,
} from 'src/sections/agent-chat/useChatAttachment';

describe('insertedText', () => {
  it('finds what an input inserted at the start, in the middle and at the end', () => {
    expect(insertedText('', 'a,b\n1,2')).toBe('a,b\n1,2');
    expect(insertedText('note: ', 'note: a,b\n1,2')).toBe('a,b\n1,2');
    expect(insertedText('before after', 'before X,Y after')).toBe('X,Y ');
    expect(insertedText('same', 'same')).toBe('');
  });
});

describe('overCap', () => {
  it('holds a table over the row cap or the byte cap back, and lets JSON span many lines', () => {
    expect(overCap(`x\n${'1\n'.repeat(MAX_ATTACHMENT_LINES - 1)}`)).toBe(false);
    expect(overCap(`x\n${'1\n'.repeat(MAX_ATTACHMENT_LINES)}`)).toBe(true);
    expect(overCap('a'.repeat(1024 * 1024 + 1))).toBe(true);
    expect(overCap(`[\n${'  {"x": 1},\n'.repeat(MAX_ATTACHMENT_LINES)}  {"x": 2}\n]`)).toBe(false);
  });
});
