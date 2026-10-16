/**
 * The rows of the data panel's binding controls.
 *
 * Every role of the spec gets a column choice: a single role one dropdown
 * under its name, a variadic family such as `y` one dropdown per bound member
 * (`y1`, `y2`, ...) plus an empty one for the next member, so another series
 * is one pick away. The members stay contiguous (`compactFamilies` in
 * `src/hooks/useAgentSession.ts`), so the next member is always the first free number.
 */

import { type BindingMap, familyMembers, nthMember } from 'src/hooks/useAgentSession';
import type { ColumnProfile, LongSuggestion, RoleSpec } from 'src/lib/agent';

/** The BFF's limit on one binding set. */
const MAX_BINDINGS = 50;

export interface BindingRow {
  /** The binding name the dropdown sets: a single role, or a family member such as `y2`. */
  name: string;
  role: RoleSpec;
  /** The role's first row, which carries its required mark and kinds. */
  first: boolean;
  /** The empty dropdown for a family's next member. */
  next: boolean;
}

/** One row per single role, one per bound family member, and one for each family's next member. */
export function bindingRows(
  roles: readonly RoleSpec[],
  bindings: BindingMap,
  columnCount: number
): BindingRow[] {
  const rows: BindingRow[] = [];
  const room = Object.keys(bindings).length < MAX_BINDINGS;
  for (const role of roles) {
    if (!role.variadic) {
      rows.push({ name: role.name, role, first: true, next: false });
      continue;
    }
    const members = familyMembers(bindings, role, roles);
    members.forEach(([name], index) => rows.push({ name, role, first: index === 0, next: false }));
    if (members.length === 0 || (room && members.length < columnCount)) {
      const first = members.length === 0;
      const name = nthMember(role, members.length + 1, roles);
      rows.push({ name, role, first, next: !first });
    }
  }
  return rows;
}

/**
 * The label of a dropdown's empty choice: a role the plot computes when no column
 * is bound (the server marks it `computed`, `agents/anyplot/data/computed.py`)
 * says so, a family's next member offers another column, any other role has none.
 */
export function emptyChoice(row: BindingRow): string {
  if (row.role.computed) return '— computed by the plot —';
  return row.next ? '— add a column —' : '— none —';
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
