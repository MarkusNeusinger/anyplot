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
import type { RoleSpec } from 'src/lib/agent';

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

/** What a role accepts, under its name: `numeric / datetime`, `any column`. */
export function kindsHint(role: RoleSpec): string {
  const kinds = role.kinds.length ? role.kinds.join(' / ') : 'any column';
  return role.variadic ? `${kinds} · one column each` : kinds;
}
