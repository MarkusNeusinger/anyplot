/**
 * Responsive image utilities for multi-size PNG + WebP delivery (issue #5191).
 *
 * All variant URLs are derived by convention from the base plot.png URL:
 *   plot.png -> plot.webp, plot_1200.png, plot_1200.webp, plot_800.png, etc.
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
 * Get the sizes attribute based on the view mode.
 *
 * Normal mode: fewer, larger cards.
 * Compact mode: more, smaller cards (roughly half the width).
 */
export function getResponsiveSizes(imageSize: ImageSize): string {
  if (imageSize === 'compact') {
    return '(max-width: 600px) 50vw, (max-width: 1200px) 25vw, 17vw';
  }
  return '(max-width: 600px) 100vw, (max-width: 1200px) 50vw, 33vw';
}

/**
 * Get the fallback image URL (plot_800.png - good middle ground).
 */
export function getFallbackSrc(url: string): string {
  return `${getBasePath(url)}_800.png`;
}
