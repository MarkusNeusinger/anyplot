import { describe, expect, it } from 'vitest';

import type { ColumnProfile, RoleSpec } from 'src/lib/agent';
import { emptyChoice, signHint } from 'src/sections/agent-chat/bindings';

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

describe('emptyChoice', () => {
  const row = (role: RoleSpec, next = false) => ({ name: role.name, role, first: !next, next });

  it('says that the plot computes a role left open', () => {
    const sma = { ...radius, name: 'sma', non_negative: false, required: false, computed: true };
    expect(emptyChoice(row(sma))).toBe('— computed by the plot —');
  });

  it('offers no column for any other role, and another column for a family', () => {
    expect(emptyChoice(row(radius))).toBe('— none —');
    expect(emptyChoice(row({ ...radius, computed: undefined }))).toBe('— none —');
    expect(emptyChoice(row({ ...radius, variadic: true }, true))).toBe('— add a column —');
  });
});
