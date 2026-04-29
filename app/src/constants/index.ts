// Constants for anyplot.ai frontend

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// DebugPage uses this — set to "/api" in prod (same-origin via the
// Cloudflare Worker on anyplot.ai/api/*) so the CF Access cookie can be
// sent with fetch. Falls back to API_URL locally where there's no Worker.
export const DEBUG_API_URL = import.meta.env.VITE_DEBUG_API_URL || API_URL;
export const GITHUB_URL = 'https://github.com/MarkusNeusinger/anyplot';
export const LIBRARIES = ['altair', 'bokeh', 'highcharts', 'letsplot', 'matplotlib', 'plotly', 'plotnine', 'pygal', 'seaborn'];
export const BATCH_SIZE = 36;

// Image size: 'normal' or 'compact' (half size)
export type ImageSize = 'normal' | 'compact';

// Library abbreviations for compact display
export const LIB_ABBREV: Record<string, string> = {
  matplotlib: 'mpl',
  seaborn: 'sns',
  plotly: 'ply',
  bokeh: 'bok',
  altair: 'alt',
  plotnine: 'p9',
  pygal: 'pyg',
  highcharts: 'hc',
  letsplot: 'lp',
};
