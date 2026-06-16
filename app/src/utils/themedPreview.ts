/**
 * Theme-aware preview-URL selection.
 *
 * Phase C of the big plot migration introduces per-theme preview files:
 *   plot-light.png / plot-dark.png  (and plot-light.html / plot-dark.html
 *   for interactive libraries). The backend exposes them as
 *   preview_url_light / preview_url_dark (or url_light / url_dark in the
 *   grid response shape).
 *
 * Legacy implementations that haven't been regenerated yet only have
 * preview_url / url (the backend synonym resolves those to the light
 * variant). These helpers pick the correct URL based on the current
 * theme and fall back to the legacy field during the transition.
 */

import { useTheme } from 'src/hooks/useLayoutContext';

/** Shape accepted by {@link selectPreviewUrl} — covers Implementation + PlotImage + POTD */
export interface ThemedPreviewSource {
  preview_url_light?: string | null;
  preview_url_dark?: string | null;
  preview_url?: string | null;
  // Grid/PlotImage shape uses `url_*` instead of `preview_url_*`
  url_light?: string | null;
  url_dark?: string | null;
  url?: string | null;
}

/** Shape for HTML preview selection */
export interface ThemedPreviewHtmlSource {
  preview_html_light?: string | null;
  preview_html_dark?: string | null;
  preview_html?: string | null;
  html_light?: string | null;
  html_dark?: string | null;
  html?: string | null;
}

/**
 * Pick the best preview-image URL for the current theme.
 *
 * Priority:
 *   1. theme-specific URL (preview_url_{theme} or url_{theme})
 *   2. the other theme's URL (better something than nothing for transition plots)
 *   3. legacy single-theme URL (preview_url or url)
 *   4. null if nothing is available
 */
export function selectPreviewUrl(
  src: ThemedPreviewSource | null | undefined,
  isDark: boolean
): string | null {
  if (!src) return null;
  const preferred = isDark
    ? (src.preview_url_dark ?? src.url_dark)
    : (src.preview_url_light ?? src.url_light);
  if (preferred) return preferred;
  const fallbackTheme = isDark
    ? (src.preview_url_light ?? src.url_light)
    : (src.preview_url_dark ?? src.url_dark);
  if (fallbackTheme) return fallbackTheme;
  return src.preview_url ?? src.url ?? null;
}

/** Pick the best preview-HTML URL for the current theme (same priority as {@link selectPreviewUrl}). */
export function selectPreviewHtml(
  src: ThemedPreviewHtmlSource | null | undefined,
  isDark: boolean
): string | null {
  if (!src) return null;
  const preferred = isDark
    ? (src.preview_html_dark ?? src.html_dark)
    : (src.preview_html_light ?? src.html_light);
  if (preferred) return preferred;
  const fallbackTheme = isDark
    ? (src.preview_html_light ?? src.html_light)
    : (src.preview_html_dark ?? src.html_dark);
  if (fallbackTheme) return fallbackTheme;
  return src.preview_html ?? src.html ?? null;
}

/** Hook: reads current theme and returns the matching preview-image URL. */
export function useThemedPreviewUrl(src: ThemedPreviewSource | null | undefined): string | null {
  const { isDark } = useTheme();
  return selectPreviewUrl(src, isDark);
}

/** Hook: reads current theme and returns the matching preview-HTML URL. */
export function useThemedPreviewHtml(
  src: ThemedPreviewHtmlSource | null | undefined
): string | null {
  const { isDark } = useTheme();
  return selectPreviewHtml(src, isDark);
}
