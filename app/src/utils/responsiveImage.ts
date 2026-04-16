/**
 * Responsive image utilities for multi-size PNG + WebP delivery (issue #5191).
 *
 * All variant URLs are derived by convention from the base plot.png URL:
 *   plot.png -> plot.webp, plot_1200.png, plot_1200.webp, plot_800.png, etc.
 *
 * Breakpoints match MUI defaults: sm=600, md=900, lg=1200, xl=1536.
 * Principle: always prefer slightly too large over too small (never pixelated).
 */

import type { ImageSize } from '../constants';

const RESPONSIVE_SIZES = [400, 800, 1200] as const;

/**
 * Derive the base path (without extension) from a plot URL.
 * e.g. ".../plots/scatter-basic/matplotlib/plot.png" -> ".../plots/scatter-basic/matplotlib/plot"
 */
function getBasePath(url: string): string {
  return url.replace(/\.png$/, '');
}

/**
 * Build a srcSet string for <source> or <img> elements.
 * Generates entries like: ".../plot_400.webp 400w, .../plot_800.webp 800w, .../plot_1200.webp 1200w"
 */
export function buildSrcSet(url: string, format: 'webp' | 'png'): string {
  const base = getBasePath(url);
  return RESPONSIVE_SIZES
    .map((w) => `${base}_${w}.${format} ${w}w`)
    .join(', ');
}

/**
 * Build a srcSet for the detail view that includes the full-resolution original.
 * Adds plot.webp/plot.png (~5000px) as the largest option so the detail view
 * is never pixelated, even on high-DPR displays.
 */
export function buildDetailSrcSet(url: string, format: 'webp' | 'png'): string {
  const base = getBasePath(url);
  const entries = RESPONSIVE_SIZES.map((w) => `${base}_${w}.${format} ${w}w`);
  entries.push(`${base}.${format} 3840w`);
  return entries.join(', ');
}

/**
 * Get the sizes attribute for the homepage image grid.
 * Matches MUI Grid columns: normal = 1→1→2→2→3, compact = 2→2→4→4→6.
 *
 * MUI breakpoints: xs=0, sm=600, md=900, lg=1200, xl=1536.
 */
export function getResponsiveSizes(imageSize: ImageSize): string {
  if (imageSize === 'compact') {
    // xs/sm: 2 cols (50vw), md/lg: 4 cols (25vw), xl: 6 cols (17vw)
    return '(max-width: 899px) 50vw, (max-width: 1535px) 25vw, 17vw';
  }
  // xs/sm: 1 col (100vw), md/lg: 2 cols (50vw), xl: 3 cols (33vw)
  return '(max-width: 899px) 100vw, (max-width: 1535px) 50vw, 33vw';
}

/**
 * Sizes for the detail view (single large image).
 * Container maxWidth: xs=100%, md=1200, lg=1400, xl=1600.
 */
export const DETAIL_SIZES = '(max-width: 1199px) 100vw, (max-width: 1535px) 1400px, 1600px';

/**
 * Sizes for the spec overview grid (always 3 columns).
 * Container maxWidth: xs=100%, md=1200, lg=1400, xl=1600.
 * Each card = container / 3.
 */
export const OVERVIEW_SIZES = '(max-width: 1199px) 33vw, (max-width: 1535px) 467px, 534px';

/**
 * Sizes for the specs page image thumbnails.
 * Mobile (xs): full width. Desktop (sm+): fixed 280px.
 */
export const SPECS_SIZES = '(max-width: 599px) 100vw, 280px';

/**
 * Get the fallback image URL (plot_800.png - good middle ground).
 */
export function getFallbackSrc(url: string): string {
  return `${getBasePath(url)}_800.png`;
}
