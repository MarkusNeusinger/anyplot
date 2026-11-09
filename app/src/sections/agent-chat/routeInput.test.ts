import { describe, expect, it } from 'vitest';

import { isCodeShapedLine, isStrongCodeLine, routeInput } from 'src/sections/agent-chat/routeInput';
import shared from 'src/sections/agent-chat/routeInput.cases.json';

interface RouteCase {
  id: number;
  text: string;
  repeat?: number;
  route: 'data' | 'message' | null;
  rule: string;
}

const cases = shared.cases as RouteCase[];

describe('routeInput', () => {
  it.each(cases.map(item => [item.id, item.rule, item] as const))(
    'routes case %i by rule %s',
    (_id, _rule, item) => {
      expect(routeInput(item.text.repeat(item.repeat ?? 1))).toBe(item.route);
    }
  );

  it('reads a newline inside a quoted cell as part of the cell, and an escaped quote as a quote', () => {
    // Without logical rows the quoted line break would make four rows of two fields and one of one.
    expect(routeInput('name,quote\n"Anna","she said ""hi""\nand left"\nBen,ok\nCem,fine')).toBe(
      'data'
    );
  });

  it('keeps a table with a stray call in one cell a table, and code with a table in it code', () => {
    expect(routeInput('item,note\nA,print(x)\nB,ok\nC,fine')).toBe('data');
    expect(routeInput('import pandas as pd\ndf = pd.DataFrame({"x": [1, 2]})\nprint(df)')).toBe(
      'message'
    );
  });

  it('routes text over the chat limit as data only by a format, never by its values alone', () => {
    expect(routeInput('a'.repeat(2001))).toBe('message');
    expect(routeInput(`${'word '.repeat(399)}word`)).toBe('message');
    // Mostly values is data while the chat takes it (rule 14), not above it.
    const values = '7 '.repeat(1100);
    expect(routeInput(values.slice(0, 1998))).toBe('data');
    expect(values.length).toBeGreaterThan(2000);
    expect(routeInput(values)).toBe('message');
    // A table in a format is data at any length.
    expect(routeInput(`month,sales\n${'Jan,5\n'.repeat(400)}`)).toBe('data');
    expect(routeInput(`Alpha\n\n120\n\n${'Beta\n\n118\n\n'.repeat(300)}`)).toBe('data');
    expect(routeInput('Jan: 5\n'.repeat(400))).toBe('data');
  });

  it('reads one cell per line only with one block pattern, and leaves an ambiguous one a message', () => {
    // A trailing block of the column labels is no row.
    expect(routeInput('Alpha\n1\nBeta\n2\nGamma\n3\nname\nvalue')).toBe('data');
    // A number below the rows is a broken row, not a label block: over the chat limit, where no
    // transcriber reads it (rule 14), that leaves it in the box.
    expect(routeInput(`${'Alpha\n1\n'.repeat(300)}4`)).toBe('message');
    // Names alone, and numbers alone, are no blocks.
    expect(routeInput('Alpha\nBeta\nGamma\nDelta')).toBe('message');
  });

  it('reads pairs of one form with a number each, and keeps a ratio, a time and a single pair a message', () => {
    expect(routeInput('x=1, y=2, z=3')).toBe('data');
    expect(routeInput('2024: 7\n2025: 9')).toBe('data');
    // Two forms in one list are no list.
    expect(routeInput('a:7, b=12')).toBe('message');
    expect(routeInput('use 16:9, or 4:3')).toBe('message');
    expect(routeInput('meet at 10:30, then 11:45')).toBe('message');
  });
});

describe('the code veto agrees with the server line by line', () => {
  it.each(shared.lines.map(item => [item.line, item] as const))('%s', (_line, item) => {
    expect(isStrongCodeLine(item.line)).toBe(item.strong);
    expect(isCodeShapedLine(item.line)).toBe(item.shaped);
  });
});
