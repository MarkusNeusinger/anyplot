/**
 * What the chat's header shows of the catalogue plot it adapts: the preview per library, read
 * from the spec the page already fetches (`GET /specs/{id}`), and the columns the plot expects,
 * from the spec's roles as the session's open answers them (the names the data card's dropdowns
 * use), else from the spec's own `data` bullets.
 */

import type { RoleSpec } from 'src/lib/agent';
import type { ThemedPreviewSource } from 'src/utils/themedPreview';

/** A spec's `## Data` meta lines: the sample size and the example, no column the plot reads. */
const META_LINE = /^\s*(size|examples?)\s*:/i;

/**
 * The spec's `data` bullets that name a column (`` `x` (numeric) - ... ``), without the meta
 * lines (`Size: ...`, `Example: ...`), for the ⓘ beside the title. Blank bullets are dropped.
 */
export function expectedColumns(data: readonly string[] | null | undefined): string[] {
  return (data ?? []).filter(line => line.trim() !== '' && !META_LINE.test(line));
}

/**
 * One role as a line of the ⓘ, in the spec bullets' shape: `` `y` (numeric, one column each) ·
 * the spec's words ``. The kinds as the data card names them, then whether the role takes one
 * column per series, is optional, or is computed by the plot when left open (the server reports
 * such a role as not required, so it says that instead of "optional").
 */
export function roleLine(role: RoleSpec): string {
  const notes = [
    role.kinds.length ? role.kinds.join(' / ') : 'any column',
    ...(role.variadic ? ['one column each'] : []),
    ...(role.computed ? ['computed by the plot if left open'] : role.required ? [] : ['optional']),
  ];
  const description = role.description.trim();
  return `\`${role.name}\` (${notes.join(', ')})${description ? ` · ${description}` : ''}`;
}

/** The ⓘ's lines: the server's roles when the session's open named any, else the spec's bullets. */
export function columnLines(
  roles: readonly RoleSpec[] | null,
  data: readonly string[] | null | undefined
): string[] {
  return roles && roles.length > 0 ? roles.map(roleLine) : expectedColumns(data);
}

/** The catalogue previews of a spec by library, as `selectPreviewUrl` reads them. */
export function previewsByLibrary(
  implementations: readonly (ThemedPreviewSource & { library_id: string })[]
): Record<string, ThemedPreviewSource> {
  return Object.fromEntries(
    implementations.map(({ library_id, preview_url, preview_url_light, preview_url_dark }) => [
      library_id,
      { preview_url, preview_url_light, preview_url_dark },
    ])
  );
}
