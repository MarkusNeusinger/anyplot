/**
 * The rows of the data panel's binding controls, and the words the card says them in.
 *
 * Every role of the spec gets one row: a single role a dropdown under its name, a
 * variadic family such as `y` its bound members (`y1`, `y2`, ...) as chips, each with
 * `×`, and `+ y` for another column. A plot may take two series or eight: a dropdown per
 * member grew one row per series, chips wrap in one. The members stay contiguous
 * (`compactFamilies` in `src/hooks/useAgentSession.ts`), so the next member is always the
 * first free number.
 *
 * The card names a column's type and a role's kinds in the start item's words
 * (`specReference.ts`): `number`, `date`; `numbers or dates`.
 */

import { type BindingMap, familyMembers, nthMember } from 'src/hooks/useAgentSession';
import type { ColumnDtype, ColumnProfile, LongSuggestion, RoleSpec } from 'src/lib/agent';
import { kindWords } from 'src/sections/agent-chat/specReference';

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
 * A column's type as the card shows it: whole numbers and decimals are both `number`, a datetime
 * is a `date`; text and yes/no (`boolean`) keep their names. The server's dtype stays the one the
 * page checks against (`fits`).
 */
export function dtypeWord(dtype: ColumnDtype): string {
  if (dtype === 'integer') return 'number';
  if (dtype === 'datetime') return 'date';
  return dtype;
}

/**
 * A dropdown option's label: the column and its type, and for a column the role cannot take,
 * why the option is greyed out (`Industry (text) · x takes numbers`). Picking it would only
 * bring the server's refusal, so the page never sends it.
 */
export function columnLabel(role: RoleSpec, column: ColumnProfile): string {
  const label = `${column.name} (${dtypeWord(column.dtype)})`;
  return fits(role, column.dtype)
    ? label
    : `${label} · ${role.name} takes ${kindWords(role.kinds)}`;
}

/** Which way a role runs on the plot, after its name in the bindings line; only `x` and `y`. */
export function axisWord(role: string): string {
  if (role === 'x') return ' (across)';
  if (role === 'y') return ' (up)';
  return '';
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

/** What a role accepts, under its name: `numbers or dates`, `any column`. */
export function kindsHint(role: RoleSpec): string {
  const kinds = kindWords(role.kinds);
  return role.variadic ? `${kinds} · one column each` : kinds;
}

/**
 * The warning on a bound column, the sibling one first (a wide table's number column in a role
 * that wants labels makes the plot meaningless), else the sign one; `null` without either.
 */
export function bindingHint(
  role: RoleSpec,
  column: string | undefined,
  columns: readonly ColumnProfile[],
  suggestion: LongSuggestion | null
): string | null {
  return (
    siblingHint(role, column, suggestion) ??
    signHint(
      role,
      columns.find(profile => profile.name === column)
    )
  );
}

/**
 * The server's sign and wide-table lines (`signs.sign_line`, `bindings.sibling_line`, as the
 * service's `warning_codes` reads them): the card shows those at the bound column already
 * (`bindingHint`), in its own words.
 */
const HINTED_LINES = [
  /^.*: column '.*' has negative values \(down to .*\); this role needs values of 0 or more$/s,
  /^.*: bound to '.*', one of [0-9]+ number columns .* turn the columns into rows first \(\.to_long\(\)\)$/s,
];

/**
 * The binding check's warnings (`bindingWarnings`) that no bound column's own warning shows: a
 * role left open because every fitting column is negative, a computed role on a column of another
 * window, a lower bound above its upper one, a key whose rows repeat, and any line the page does
 * not know. None while the check's word is unknown (`null`).
 */
export function checkOnlyWarnings(lines: readonly string[] | null): string[] {
  return (lines ?? []).filter(line => !HINTED_LINES.some(pattern => pattern.test(line)));
}

/** One role of the bindings line: its name, and its columns (several for a family) or none yet. */
export interface BoundRole {
  name: string;
  columns: string[];
  /** A required role without a column: the line marks it, and the step waits for it. */
  missing: boolean;
}

/**
 * The bindings line's roles, in the spec's order: every role with a column, and a required one
 * without (`missing`); an optional role left open, or one the plot computes, says nothing.
 */
export function boundRoles(rows: readonly BindingRow[], bindings: BindingMap): BoundRole[] {
  return rows.flatMap(row => {
    const columns = row.role.variadic
      ? row.members.map(([, column]) => column)
      : bindings[row.name]
        ? [bindings[row.name]]
        : [];
    if (columns.length === 0 && !row.role.required) return [];
    return [{ name: row.name, columns, missing: columns.length === 0 }];
  });
}
