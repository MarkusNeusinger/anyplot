import { describe, expect, it } from 'vitest';

import type { RoleSpec } from 'src/lib/agent';
import {
  columnLines,
  expectedColumns,
  previewsByLibrary,
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
