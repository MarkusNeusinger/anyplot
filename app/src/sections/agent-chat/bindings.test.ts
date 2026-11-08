import { describe, expect, it } from 'vitest';

import type { ColumnProfile, RoleSpec } from 'src/lib/agent';
import {
  axisWord,
  bindingRows,
  boundRoles,
  checkOnlyWarnings,
  columnLabel,
  dtypeWord,
  emptyChoice,
  fits,
  kindsHint,
  siblingHint,
  signHint,
} from 'src/sections/agent-chat/bindings';

const radius: RoleSpec = {
  name: 'radius',
  kinds: ['numeric'],
  required: true,
  variadic: false,
  description: 'distance',
  non_negative: true,
};

function column(min: number | string | null | undefined, dtype: ColumnProfile['dtype'] = 'number') {
  return { name: 'y', dtype, missing: 0, unique: 3, min } as ColumnProfile;
}

describe('checkOnlyWarnings', () => {
  it("keeps the check's lines that no bound column's own warning shows", () => {
    // The service's sentences (`signs.py`, `bindings.py`, `computed.py`, `bounds.py`, `fidelity.py`).
    const sign =
      "radius: column 'y' has negative values (down to -2); this role needs values of 0 or more";
    const sibling =
      "y: bound to 'Mo', one of 7 number columns ('Mo', 'Tu', 'We', 'Th', ...) that hold one measure side by side; y wants labels, so each number would become a category of its own: turn the columns into rows first (.to_long())";
    const unbound =
      "size: not bound, because every column that fits it ('a') has negative values; this role needs values of 0 or more";
    const window =
      "sma: column 'SMA 200' holds a 200-period value; the spec's convention is 20, so the plot shows the column's window";
    const repeated =
      "x: column 'Length' holds 9 values in 27 rows; the plot draws one value per x, so rows with the same x need an aggregate first";
    expect(checkOnlyWarnings([sign, sibling, unbound, window, repeated, 'a new kind'])).toEqual([
      unbound,
      window,
      repeated,
      'a new kind',
    ]);
    expect(checkOnlyWarnings(null)).toEqual([]);
  });
});

describe('signHint', () => {
  it('warns when a role that needs values of 0 or more gets a negative column', () => {
    expect(signHint(radius, column(-0.9996))).toBe(
      'has negative values (down to -0.9996); radius needs values of 0 or more'
    );
  });

  it('stays quiet for a column without negatives, a role without the mark, or no column', () => {
    expect(signHint(radius, column(0))).toBeNull();
    expect(signHint({ ...radius, non_negative: false }, column(-1))).toBeNull();
    expect(signHint({ ...radius, non_negative: undefined }, column(-1))).toBeNull();
    expect(signHint(radius, undefined)).toBeNull();
    expect(signHint(radius, column('2024-01-01', 'datetime'))).toBeNull();
  });
});

describe('siblingHint', () => {
  // Live test round 7: a heatmap of `Stunde;Mo;...;So`, its `y` bound to the numbers of `Mo`.
  const y: RoleSpec = { ...radius, name: 'y', kinds: ['text', 'numeric'], non_negative: false };
  const offer = {
    kind: 'to_long' as const,
    columns: ['Mo', 'Di', 'Mi'],
    names_to: 'y',
    values_to: 'value',
    keys: ['Stunde'],
    rows: 42,
    siblings: ['Mo', 'Di', 'Mi'],
  };

  it('warns when a role that takes labels is bound to a number column of a wide table', () => {
    expect(siblingHint(y, 'Mo', offer)).toBe(
      'one of 3 number columns that hold one measure side by side; y wants labels: .to_long() first'
    );
  });

  it('stays quiet for a measure role, a key column, no offer or no column', () => {
    expect(siblingHint({ ...y, name: 'value', kinds: ['numeric'] }, 'Mo', offer)).toBeNull();
    expect(siblingHint(y, 'Stunde', offer)).toBeNull();
    expect(siblingHint(y, 'Mo', null)).toBeNull();
    expect(siblingHint(y, undefined, offer)).toBeNull();
    expect(siblingHint(y, 'Mo', { ...offer, siblings: [] })).toBeNull();
  });
});

describe('emptyChoice', () => {
  it('says that the plot computes a role left open', () => {
    const sma = { ...radius, name: 'sma', non_negative: false, required: false, computed: true };
    expect(emptyChoice(sma)).toBe('— computed by the plot —');
  });

  it('offers no column for any other role', () => {
    expect(emptyChoice(radius)).toBe('— none —');
    expect(emptyChoice({ ...radius, computed: undefined })).toBe('— none —');
  });
});

describe('fits and columnLabel', () => {
  const values: RoleSpec = { ...radius, name: 'values', non_negative: false };
  const industry = { ...column(null, 'text'), name: 'Industry' };
  const price = { ...column(1, 'integer'), name: 'Price' };

  it('marks a column the role cannot take with the reason, in the chips’ words', () => {
    expect(fits(values, 'text')).toBe(false);
    expect(columnLabel(values, industry)).toBe('Industry (text) · values takes numbers');
    expect(columnLabel({ ...values, kinds: ['numeric', 'datetime'] }, industry)).toBe(
      'Industry (text) · values takes numbers or dates'
    );
  });

  it('lists a fitting column with its type as the preview names it', () => {
    expect(fits(values, 'integer')).toBe(true);
    // Whole numbers are numbers on the card; the server's dtype stays the one `fits` checks.
    expect(columnLabel(values, price)).toBe('Price (number)');
    // A category takes whole numbers and dates as labels, as the server does.
    const category = { ...values, name: 'category', kinds: ['categorical'] };
    expect(fits(category, 'integer')).toBe(true);
    expect(fits(category, 'datetime')).toBe(true);
    expect(columnLabel(category, { ...price, dtype: 'datetime' })).toBe('Price (date)');
    expect(columnLabel(category, { ...price, dtype: 'number' })).toBe(
      'Price (number) · category takes categories'
    );
  });

  it('leaves a role without kinds, or with a kind it does not know, to the server', () => {
    expect(fits({ ...values, kinds: [] }, 'text')).toBe(true);
    expect(fits({ ...values, kinds: ['geometry'] }, 'text')).toBe(true);
  });
});

describe('the words of the card', () => {
  it('says a whole number is a number and a datetime a date, and keeps the rest', () => {
    expect((['integer', 'number', 'datetime', 'text', 'boolean'] as const).map(dtypeWord)).toEqual([
      'number',
      'number',
      'date',
      'text',
      'boolean',
    ]);
  });

  it('names the way only for x and y', () => {
    expect(['x', 'y', 'color', 'y1', 'size'].map(axisWord)).toEqual([
      ' (across)',
      ' (up)',
      '',
      '',
      '',
    ]);
  });

  it("says what a role takes in the chips' words", () => {
    expect(kindsHint({ ...radius, kinds: ['numeric', 'datetime'] })).toBe('numbers or dates');
    expect(kindsHint({ ...radius, variadic: true })).toBe('numbers · one column each');
    expect(kindsHint({ ...radius, kinds: [] })).toBe('any column');
  });
});

describe('boundRoles', () => {
  const role = (name: string, overrides: Partial<RoleSpec> = {}): RoleSpec => ({
    name,
    kinds: ['numeric'],
    required: true,
    variadic: false,
    description: '',
    ...overrides,
  });
  const roles = [
    role('x'),
    role('y', { variadic: true }),
    role('series', { kinds: ['categorical'], required: false }),
    role('sma', { required: false, computed: true }),
  ];

  it("lists the bound roles in the spec's order, a family's columns together", () => {
    const bindings = { x: 'month', y1: 'shoes', y2: 'hats', series: 'region' };
    expect(boundRoles(bindingRows(roles, bindings, 5), bindings)).toEqual([
      { name: 'x', columns: ['month'], missing: false },
      { name: 'y', columns: ['shoes', 'hats'], missing: false },
      { name: 'series', columns: ['region'], missing: false },
    ]);
  });

  it('marks a required role without a column and leaves an open optional one out', () => {
    const bindings = { y1: 'shoes' };
    expect(boundRoles(bindingRows(roles, bindings, 5), bindings)).toEqual([
      { name: 'x', columns: [], missing: true },
      { name: 'y', columns: ['shoes'], missing: false },
    ]);
  });
});
