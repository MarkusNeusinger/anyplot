import { describe, expect, it } from 'vitest';

import { previewSegments } from 'src/sections/agent-chat/previewCell';

describe('previewSegments', () => {
  it('leaves a cell without breaks or space runs as one segment', () => {
    expect(previewSegments('Zürich Nord')).toEqual([{ text: 'Zürich Nord' }]);
    expect(previewSegments('')).toEqual([]);
  });

  it('marks every line break, whatever its form', () => {
    expect(previewSegments('one\ntwo\r\nthree\rfour')).toEqual([
      { text: 'one' },
      { text: '↵', mark: 'break' },
      { text: 'two' },
      { text: '↵', mark: 'break' },
      { text: 'three' },
      { text: '↵', mark: 'break' },
      { text: 'four' },
    ]);
  });

  it('shows each space of a run, so `a  b` never reads as `a b`', () => {
    expect(previewSegments('a  b   c d')).toEqual([
      { text: 'a' },
      { text: '··', mark: 'spaces' },
      { text: 'b' },
      { text: '···', mark: 'spaces' },
      { text: 'c d' },
    ]);
  });

  it('marks a tab, which a cell that never wraps would show as a space', () => {
    expect(previewSegments('a\tb')).toEqual([
      { text: 'a' },
      { text: '→', mark: 'tab' },
      { text: 'b' },
    ]);
  });

  it('marks breaks and runs at the edges and next to each other', () => {
    expect(previewSegments('\n  x')).toEqual([
      { text: '↵', mark: 'break' },
      { text: '··', mark: 'spaces' },
      { text: 'x' },
    ]);
  });
});
