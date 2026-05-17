// Constants for anyplot.ai frontend

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// DebugPage uses this — set to "/api" in prod (same-origin via the
// Cloudflare Worker on anyplot.ai/api/*) so the CF Access cookie can be
// sent with fetch. Falls back to API_URL locally where there's no Worker.
export const DEBUG_API_URL = import.meta.env.VITE_DEBUG_API_URL || API_URL;
export const GITHUB_URL = 'https://github.com/MarkusNeusinger/anyplot';
export const LIBRARIES = ['altair', 'bokeh', 'ggplot2', 'highcharts', 'letsplot', 'matplotlib', 'plotly', 'plotnine', 'pygal', 'seaborn'];
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
  ggplot2: 'gg',
};

// Static library → language map, mirroring core/constants.py LIBRARIES_METADATA.
// Used to build correct /{spec}/{language}/{library} links from contexts that
// only know a library id — e.g. the debug-page spec matrix, where columns are
// keyed by library and the per-cell payload doesn't carry a language. The
// recent-activity list does NOT need this map; it gets `language_id` straight
// from /debug/status.
export const LIB_TO_LANG: Record<string, string> = {
  altair: 'python',
  bokeh: 'python',
  ggplot2: 'r',
  highcharts: 'python',
  letsplot: 'python',
  matplotlib: 'python',
  plotly: 'python',
  plotnine: 'python',
  pygal: 'python',
  seaborn: 'python',
};

// Display label for a language id (e.g. used in titles, breadcrumbs, chips).
export const LANG_DISPLAY: Record<string, string> = {
  python: 'Python',
  r: 'R',
};

// File-extension token for a language id (e.g. used as the suffix in compact
// plot cards: "mpl.py", "ggplot2.r"). The .R extension is uppercase on disk
// for R scripts, but the suffix here mirrors the language id for symmetry
// with "py" — display only, not a filesystem reference.
export const LANG_EXT: Record<string, string> = {
  python: 'py',
  r: 'r',
};
