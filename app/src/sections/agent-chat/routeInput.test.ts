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

  it('routes text over the chat limit as data, whatever it holds', () => {
    expect(routeInput('a'.repeat(2001))).toBe('data');
    expect(routeInput(`${'word '.repeat(399)}word`)).toBe('message');
  });
});

describe('the code veto agrees with the server line by line', () => {
  it.each(shared.lines.map(item => [item.line, item] as const))('%s', (_line, item) => {
    expect(isStrongCodeLine(item.line)).toBe(item.strong);
    expect(isCodeShapedLine(item.line)).toBe(item.shaped);
  });
});
