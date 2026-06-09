/**
 * Tooltip ID utilities for consistent ID generation.
 */

export type TooltipType = 'spec' | 'lib';

/**
 * Create a unique tooltip ID for a spec/library combination.
 *
 * @param type - 'spec' or 'lib'
 * @param specId - Specification ID
 * @param library - Library ID
 * @returns Unique tooltip ID string
 *
 * @example
 * const id = createTooltipId('spec', 'scatter-basic', 'matplotlib');
 * // Returns: 'spec-scatter-basic-matplotlib'
 */
export function createTooltipId(type: TooltipType, specId: string, library: string): string {
  return `${type}-${specId}-${library}`;
}

/**
 * Parse a tooltip ID back into its components.
 *
 * @param id - Tooltip ID to parse
 * @returns Parsed components or null if invalid
 *
 * @example
 * parseTooltipId('spec-scatter-basic-matplotlib')
 * // Returns: { type: 'spec', specId: 'scatter-basic', library: 'matplotlib' }
 */
export function parseTooltipId(
  id: string
): { type: TooltipType; specId: string; library: string } | null {
  const parts = id.split('-');
  if (parts.length < 3) return null;

  const typeRaw = parts[0];
  if (typeRaw !== 'spec' && typeRaw !== 'lib') return null;

  // Library is always the last part, specId is everything in between
  const library = parts[parts.length - 1];
  const specId = parts.slice(1, -1).join('-');

  if (!specId || !library) return null;

  return {
    type: typeRaw,
    specId,
    library,
  };
}

/**
 * Check if a tooltip is currently open for a specific spec/library.
 *
 * @param openTooltip - Currently open tooltip ID
 * @param type - Tooltip type to check
 * @param specId - Spec ID to check
 * @param library - Library to check
 * @returns Whether this tooltip is open
 */
export function isTooltipOpen(
  openTooltip: string | null,
  type: TooltipType,
  specId: string,
  library: string
): boolean {
  if (!openTooltip) return false;
  return openTooltip === createTooltipId(type, specId, library);
}
