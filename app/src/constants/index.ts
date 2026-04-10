// Constants for pyplots.ai frontend

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const GITHUB_URL = 'https://github.com/MarkusNeusinger/pyplots';
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
