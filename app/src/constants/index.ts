// Constants for anyplot.ai frontend

import { CONFIG } from 'src/global-config';

export { CONFIG };
// Compat aliases — prefer CONFIG.api.* in new code.
export const API_URL = CONFIG.api.baseUrl;
export const DEBUG_API_URL = CONFIG.api.debugBaseUrl;
export const GITHUB_URL = 'https://github.com/MarkusNeusinger/anyplot';
export const LIBRARIES = [
  'altair',
  'bokeh',
  'chartjs',
  'd3',
  'echarts',
  'ggplot2',
  'highcharts',
  'letsplot',
  'makie',
  'matplotlib',
  'muix',
  'plotly',
  'plotnine',
  'pygal',
  'seaborn',
];
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
  makie: 'mk',
  chartjs: 'cjs',
  d3: 'd3',
  echarts: 'ec',
  muix: 'mui',
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
  chartjs: 'javascript',
  d3: 'javascript',
  echarts: 'javascript',
  ggplot2: 'r',
  highcharts: 'javascript',
  letsplot: 'python',
  makie: 'julia',
  matplotlib: 'python',
  muix: 'javascript',
  plotly: 'python',
  plotnine: 'python',
  pygal: 'python',
  seaborn: 'python',
};

// Static library → UI-framework map, mirroring core/constants.py
// LIBRARIES_METADATA `framework`. 'none' = framework-agnostic; 'react' = needs
// React (e.g. MUI X). Powers the generic "React-compatible" libraries filter so
// future Recharts / Vue / Svelte entries slot in by adding a row here — no
// schema or component change. The API also returns `framework` per library, but
// this static map keeps the filter deterministic and testable without a fetch.
export const LIB_TO_FRAMEWORK: Record<string, string> = {
  altair: 'none',
  bokeh: 'none',
  chartjs: 'none',
  d3: 'none',
  echarts: 'none',
  ggplot2: 'none',
  highcharts: 'none',
  letsplot: 'none',
  makie: 'none',
  matplotlib: 'none',
  muix: 'react',
  plotly: 'none',
  plotnine: 'none',
  pygal: 'none',
  seaborn: 'none',
};

// Display label for a language id (e.g. used in titles, breadcrumbs, chips).
export const LANG_DISPLAY: Record<string, string> = {
  python: 'Python',
  r: 'R',
  julia: 'Julia',
  javascript: 'JavaScript',
};

// File-extension token for a language id (e.g. used as the suffix in compact
// plot cards: "mpl.py", "ggplot2.r", "makie.jl"). The .R extension is uppercase
// on disk for R scripts, but the suffix here mirrors the language id for
// symmetry with "py" — display only, not a filesystem reference.
export const LANG_EXT: Record<string, string> = {
  python: 'py',
  r: 'r',
  julia: 'jl',
  javascript: 'js',
};

// Per-library file-extension override (display suffix), mirroring
// core/constants.py LIBRARY_FILE_EXTENSION_OVERRIDES. Most libraries inherit
// their language default (LANG_EXT); MUI X diverges — it is authored as React
// `.tsx`, not plain `.js`. Currently the only override.
export const LIB_EXT_OVERRIDE: Record<string, string> = {
  muix: 'tsx',
};

// Display/file-suffix extension for a (library, language) pair: the library's
// override when it declares one, else the language default. Used for the
// compact-card suffix ("mui.tsx" vs "mpl.py") and other display contexts.
export function libExt(library: string, language: string): string {
  return LIB_EXT_OVERRIDE[library] ?? LANG_EXT[language] ?? '';
}
