import { describe, expect, it } from 'vitest';

import type { ColumnProfile } from 'src/lib/agent';
import {
  columnWidth,
  compareNumericText,
  compareTextCells,
  MAX_COLUMN_PX,
  MIN_COLUMN_PX,
  numberOf,
  rowNumberWidth,
  viewTable,
} from 'src/sections/agent-chat/viewTable';

const column = (name: string, dtype: ColumnProfile['dtype']): ColumnProfile => ({
  name,
  dtype,
  missing: 0,
  unique: 1,
});

describe('viewTable', () => {
  it('takes the header and the cells from the file and each dtype from the profile by name', () => {
    const table = viewTable('id,city,when\n1,Bonn,2026-01-05\n2,,2026-01-06\n', [
      column('city', 'text'),
      column('id', 'integer'),
      column('when', 'datetime'),
    ]);
    expect(table.columns.map(({ name, dtype, numeric }) => [name, dtype, numeric])).toEqual([
      ['id', 'integer', true],
      ['city', 'text', false],
      ['when', 'datetime', false],
    ]);
    expect(table.rows).toEqual([
      ['1', 'Bonn', '2026-01-05'],
      ['2', '', '2026-01-06'],
    ]);
  });

  it('names no dtype for a column the profile does not know', () => {
    const table = viewTable('renamed\n1\n', [column('value', 'number')]);
    expect(table.columns[0]).toMatchObject({ name: 'renamed', dtype: null, numeric: false });
  });
});

describe('columnWidth', () => {
  it('fits the name, the dtype and the longest value within the bounds', () => {
    // `number` is the header's longer line: six characters beside the sort arrow and the menu.
    expect(columnWidth('x', 'number', [['1']], 0)).toBe(6 * 8 + 64);
    expect(columnWidth('x', null, [['1']], 0)).toBe(MIN_COLUMN_PX);
    expect(columnWidth('note', 'text', [['a'.repeat(30)]], 0)).toBe(30 * 8 + 24);
    expect(columnWidth('note', 'text', [['a'.repeat(200)]], 0)).toBe(MAX_COLUMN_PX);
  });

  it('measures the first thousand rows only', () => {
    const rows = [...Array.from({ length: 1000 }, () => ['a']), ['b'.repeat(100)]];
    expect(columnWidth('n', null, rows, 0)).toBe(MIN_COLUMN_PX);
  });
});

describe('rowNumberWidth', () => {
  it('grows with the digits of the row count', () => {
    expect(rowNumberWidth(9)).toBe(48);
    expect(rowNumberWidth(20_000)).toBe(5 * 8 + 24);
  });
});

describe('numberOf', () => {
  it.each([
    ['1.50', 1.5],
    ['-0.0', -0],
    ['1e-07', 1e-7],
    ['inf', Infinity],
    ['-Infinity', -Infinity],
    ['12', 12],
  ])('reads %s as a number', (cell, value) => {
    expect(numberOf(cell)).toBe(value);
  });

  it.each(['', '  ', 'n/a', 'NaN', '1,5'])('reads %j as no number', cell => {
    expect(numberOf(cell)).toBeNull();
  });
});

describe('compareNumericText', () => {
  it('orders by number, ties by text, and empty cells and text after every number', () => {
    const cells = ['10', '', '9', 'n/a', '-1', '1.0', '1', 'inf', '1e2'];
    expect([...cells].sort(compareNumericText)).toEqual([
      '-1',
      '1',
      '1.0',
      '9',
      '10',
      '1e2',
      'inf',
      '',
      'n/a',
    ]);
  });

  it('keeps empty cells and text after every number when it sorts down too', () => {
    const cells = ['10', '', '9', 'n/a', '-1', '1.0', '1'];
    expect([...cells].sort((a, b) => compareNumericText(a, b, 'desc'))).toEqual([
      '10',
      '9',
      '1.0',
      '1',
      '-1',
      '',
      'n/a',
    ]);
  });
});

describe('compareTextCells', () => {
  it.each([
    ['asc', ['Bonn', 'Köln', 'Ulm', '', '']],
    ['desc', ['Ulm', 'Köln', 'Bonn', '', '']],
  ] as const)('keeps the empty cells last when it sorts %s', (direction, sorted) => {
    const cells = ['Köln', '', 'Ulm', '', 'Bonn'];
    expect([...cells].sort((a, b) => compareTextCells(a, b, direction))).toEqual(sorted);
  });
});
