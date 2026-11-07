import { describe, expect, it } from 'vitest';

import type { RoleSpec } from 'src/lib/agent';
import {
  columnLines,
  expectedColumns,
  kindWords,
  previewsByLibrary,
  roleChip,
  roleLine,
} from 'src/sections/agent-chat/specReference';

const role = (name: string, overrides: Partial<RoleSpec> = {}): RoleSpec => ({
  name,
  kinds: ['numeric'],
  required: true,
  variadic: false,
  description: `${name} values`,
  ...overrides,
});

describe('roleLine', () => {
  it('names the kinds and the description of a plain required role', () => {
    expect(roleLine(role('x', { kinds: ['numeric', 'datetime'] }))).toBe(
      '`x` (numeric / datetime) · x values'
    );
  });

  it('says when a role takes one column per series, is optional or is computed', () => {
    expect(roleLine(role('y', { variadic: true }))).toBe(
      '`y` (numeric, one column each) · y values'
    );
    expect(roleLine(role('series', { kinds: ['categorical'], required: false }))).toBe(
      '`series` (categorical, optional) · series values'
    );
    // The server reports a computed role as not required: it says how, never "optional" as well.
    expect(roleLine(role('sma', { required: false, computed: true }))).toBe(
      '`sma` (numeric, computed by the plot if left open) · sma values'
    );
  });

  it('takes any column without kinds and leaves an empty description out', () => {
    expect(roleLine(role('label', { kinds: [], description: '  ' }))).toBe('`label` (any column)');
  });
});

describe('kindWords', () => {
  it("says every kind the server knows in a table user's words", () => {
    expect(
      ['numeric', 'categorical', 'datetime', 'text', 'boolean'].map(k => kindWords([k]))
    ).toEqual(['numbers', 'categories', 'dates', 'text', 'yes/no']);
  });

  it("joins several kinds in the server's order, once each, and keeps an unknown one", () => {
    expect(kindWords(['numeric', 'datetime'])).toBe('numbers or dates');
    expect(kindWords(['datetime', 'numeric', 'datetime'])).toBe('dates or numbers');
    expect(kindWords(['geometry'])).toBe('geometry');
    expect(kindWords([])).toBe('any column');
  });
});

describe('roleChip', () => {
  it('names the role and what it takes', () => {
    expect(roleChip(role('x'))).toBe('x · numbers');
    expect(roleChip(role('when', { kinds: ['datetime', 'numeric'] }))).toBe(
      'when · dates or numbers'
    );
  });

  it('says a family takes one or more, and an optional or computed role that it is optional', () => {
    expect(roleChip(role('y', { variadic: true }))).toBe('y · numbers, one or more');
    expect(roleChip(role('series', { kinds: ['categorical'], required: false }))).toBe(
      'series · categories, optional'
    );
    expect(roleChip(role('sma', { required: false, computed: true }))).toBe(
      'sma · numbers, optional'
    );
    expect(roleChip(role('label', { kinds: [], required: false, variadic: true }))).toBe(
      'label · any column, one or more, optional'
    );
  });
});

describe('columnLines', () => {
  const bullets = ['`x` (numeric) - from the spec', 'Size: 50 points'];

  it("prefers the server's roles", () => {
    expect(columnLines([role('x'), role('y')], bullets)).toEqual([
      '`x` (numeric) · x values',
      '`y` (numeric) · y values',
    ]);
  });

  it("falls back to the spec's bullets without roles", () => {
    expect(columnLines(null, bullets)).toEqual(['`x` (numeric) - from the spec']);
    expect(columnLines([], bullets)).toEqual(['`x` (numeric) - from the spec']);
    expect(columnLines(null, undefined)).toEqual([]);
  });
});

describe('expectedColumns', () => {
  it('keeps the column bullets and drops the size and example lines', () => {
    expect(
      expectedColumns([
        '`value` (numeric) - The continuous variable to visualize as density curves',
        '`group` (categorical) - The grouping variable that creates separate ridges',
        'Size: 50-500 observations per group for smooth density estimation',
        'Example: Monthly temperature readings, survey scores by age group',
        'examples: lower case and plural too',
        '  ',
      ])
    ).toEqual([
      '`value` (numeric) - The continuous variable to visualize as density curves',
      '`group` (categorical) - The grouping variable that creates separate ridges',
    ]);
  });

  it('is empty without data bullets', () => {
    expect(expectedColumns(undefined)).toEqual([]);
    expect(expectedColumns(null)).toEqual([]);
  });

  it('keeps a column whose description mentions a size', () => {
    expect(expectedColumns(['`size` (numeric) - Size: the bubble area'])).toEqual([
      '`size` (numeric) - Size: the bubble area',
    ]);
  });
});

describe('previewsByLibrary', () => {
  it('keeps each library its previews and nothing else', () => {
    expect(
      previewsByLibrary([
        {
          library_id: 'matplotlib',
          preview_url: 'p.png',
          preview_url_light: 'l.png',
          preview_url_dark: 'd.png',
        },
      ])
    ).toEqual({
      matplotlib: { preview_url: 'p.png', preview_url_light: 'l.png', preview_url_dark: 'd.png' },
    });
  });
});
