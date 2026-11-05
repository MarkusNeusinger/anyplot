/**
 * The rows of the data panel's binding controls.
 *
 * Every role of the spec gets one row: a single role a dropdown under its name, a
 * variadic family such as `y` its bound members (`y1`, `y2`, ...) as chips, each with
 * `×`, and `+ y` for another column. A plot may take two series or eight: a dropdown per
 * member grew one row per series, chips wrap in one. The members stay contiguous
 * (`compactFamilies` in `src/hooks/useAgentSession.ts`), so the next member is always the
 * first free number.
 */

import { type BindingMap, familyMembers, nthMember } from 'src/hooks/useAgentSession';
import type { ColumnDtype, ColumnProfile, LongSuggestion, RoleSpec } from 'src/lib/agent';

/** The BFF's limit on one binding set. */
const MAX_BINDINGS = 50;

/**
 * The column types each role kind takes, as the server's binding check accepts them
 * (`ACCEPTS` in `agents/anyplot/data/bindings.py`; `test_bindings.py` keeps the two equal).
 */
export const ACCEPTS: Record<string, readonly ColumnDtype[]> = {
  numeric: ['number', 'integer'],
  categorical: ['text', 'boolean', 'datetime', 'integer'],
  text: ['text', 'datetime', 'boolean', 'integer'],
  boolean: ['boolean', 'integer'],
  datetime: ['datetime'],
};

/**
 * Whether the server takes a column of `dtype` for `role`: a role without kinds takes any
 * column, and an unknown kind (a newer server) is left to the server to judge.
 */
export function fits(role: RoleSpec, dtype: ColumnDtype): boolean {
  if (!role.kinds.length || role.kinds.some(kind => !(kind in ACCEPTS))) return true;
  return role.kinds.some(kind => ACCEPTS[kind].includes(dtype));
}

/**
 * A dropdown option's label: the column and its type, and for a column the role cannot take,
 * why the option is greyed out (`Industry (text) · not numeric`). Picking it would only bring
 * the server's refusal, so the page never sends it.
 */
export function columnLabel(role: RoleSpec, column: ColumnProfile): string {
  const label = `${column.name} (${column.dtype})`;
  return fits(role, column.dtype) ? label : `${label} · not ${role.kinds.join(' or ')}`;
}

export interface BindingRow {
  /** A single role's binding name, which its dropdown sets; a family's own name (`y`). */
  name: string;
  role: RoleSpec;
  /** A family's bound members in their order, as `[binding name, column]`; empty for a single role. */
  members: [string, string][];
  /**
   * The binding name a family's `+` binds (`y3`, the first free number), or `null`: a single
   * role, every column taken, or the binding set full.
   */
  next: string | null;
}

/** One row per role: a single role's dropdown, or a family's chips and its next member. */
export function bindingRows(
  roles: readonly RoleSpec[],
  bindings: BindingMap,
  columnCount: number
): BindingRow[] {
  const room = Object.keys(bindings).length < MAX_BINDINGS;
  return roles.map(role => {
    if (!role.variadic) return { name: role.name, role, members: [], next: null };
    const members = familyMembers(bindings, role, roles);
    const next =
      room && members.length < columnCount ? nthMember(role, members.length + 1, roles) : null;
    return { name: role.name, role, members, next };
  });
}

/**
 * The label of a dropdown's empty choice: a role the plot computes when no column
 * is bound (the server marks it `computed`, `agents/anyplot/data/computed.py`)
 * says so, any other role has none.
 */
export function emptyChoice(role: RoleSpec): string {
  return role.computed ? '— computed by the plot —' : '— none —';
}

/**
 * The warning under a dropdown when a role that needs values of 0 or more (the
 * server marks it `non_negative`, `agents/anyplot/data/signs.py`) is bound to a
 * column whose smallest value is negative; `null` otherwise. Never a refusal: the
 * user may keep the column, for example to drop the negative rows afterwards.
 */
export function signHint(role: RoleSpec, column: ColumnProfile | undefined): string | null {
  if (!role.non_negative || !column || typeof column.min !== 'number' || column.min >= 0) {
    return null;
  }
  return `has negative values (down to ${column.min}); ${role.name} needs values of 0 or more`;
}

/**
 * The warning under a dropdown when a role that takes labels (its kinds include
 * `categorical` or `text`, as a heatmap's `x` and `y` do) is bound to one of the
 * number columns of a wide table (the suggestion's `siblings`, the server's
 * `bindings.label_siblings`); `null` otherwise. Never a refusal: `.to_long()` is
 * the fix the page offers.
 */
export function siblingHint(
  role: RoleSpec,
  column: string | undefined,
  suggestion: LongSuggestion | null
): string | null {
  if (!column || !suggestion || !suggestion.siblings.includes(column)) return null;
  if (!role.kinds.some(kind => kind === 'categorical' || kind === 'text')) return null;
  const count = suggestion.siblings.length;
  return `one of ${count} number columns that hold one measure side by side; ${role.name} wants labels: .to_long() first`;
}

/** What a role accepts, under its name: `numeric / datetime`, `any column`. */
export function kindsHint(role: RoleSpec): string {
  const kinds = role.kinds.length ? role.kinds.join(' / ') : 'any column';
  return role.variadic ? `${kinds} · one column each` : kinds;
}
