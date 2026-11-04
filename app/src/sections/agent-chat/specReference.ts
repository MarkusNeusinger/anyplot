/**
 * What the chat's header shows of the catalogue plot it adapts, read from the spec the page
 * already fetches (`GET /specs/{id}`): the preview per library and the columns the plot expects.
 */

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
