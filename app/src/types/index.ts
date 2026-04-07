// Types for pyplots.ai frontend

export interface PlotImage {
  library: string;
  url: string;
  html?: string;
  code?: string;
  spec_id?: string;
  title?: string;
}

// Filter system types
// Spec-level categories describe WHAT is visualized
// Impl-level categories describe HOW the code implements it (issue #2434)
export type FilterCategory =
  | 'lib'
  | 'spec'
  | 'plot'
  | 'data'
  | 'dom'
  | 'feat'
  | 'dep'
  | 'tech'
  | 'pat'
  | 'prep'
  | 'style';

// Display labels for filter categories
export const FILTER_LABELS: Record<FilterCategory, string> = {
  // Spec-level
  lib: 'library',
  spec: 'spec',
  plot: 'type',
  data: 'data',
  dom: 'field',
  feat: 'extras',
  // Impl-level (issue #2434)
  dep: 'uses',
  tech: 'technique',
  pat: 'pattern',
  prep: 'dataprep',
  style: 'style',
};

// Tooltip descriptions for filter categories
export const FILTER_TOOLTIPS: Record<FilterCategory, string> = {
  // Spec-level: WHAT is visualized
  lib: 'python plotting library',
  spec: 'plot specification by identifier',
  plot: 'type of visualization or chart',
  data: 'structure of the input data',
  dom: 'application domain or field',
  feat: 'special plot features and capabilities',
  // Impl-level: HOW the code implements it
  dep: 'external packages beyond the plotting library',
  tech: 'advanced visualization techniques in the code',
  pat: 'code structure and organization patterns',
  prep: 'statistical or mathematical data transformations',
  style: 'visual styling choices that differ from defaults',
};

// All filter categories in display order
export const FILTER_CATEGORIES: FilterCategory[] = [
  // Spec-level
  'lib',
  'spec',
  'plot',
  'data',
  'dom',
  'feat',
  // Impl-level (issue #2434)
  'dep',
  'tech',
  'pat',
  'prep',
  'style',
];

// A single filter group (one chip) - values within are OR-linked
export interface FilterGroup {
  category: FilterCategory;
  values: string[];
}

// Active filters: array of filter groups - groups are AND-linked
export type ActiveFilters = FilterGroup[];

// Counts per filter value
export type FilterCounts = Record<FilterCategory, Record<string, number>>;

// API response for filtered plots
export interface FilteredPlotsResponse {
  total: number;
  images: PlotImage[];
  counts: FilterCounts;  // Contextual counts (for AND additions)
  globalCounts: FilterCounts;  // Global counts (for reference)
  orCounts: Record<string, number>[];  // Per-group counts for OR additions
  specTitles: Record<string, string>;  // Mapping spec_id -> title for search/tooltips
}

export interface LibraryInfo {
  id: string;
  name: string;
  version?: string;
  documentation_url?: string;
  description?: string;
}

export interface SpecInfo {
  id: string;
  title: string;
  description?: string;
}

// Implementation of a spec for a specific library
export interface Implementation {
  library_id: string;
  library_name: string;
  preview_url: string;
  preview_html?: string;
  quality_score: number | null;
  code: string | null;
  generated_at?: string;
  updated?: string;
  library_version?: string;
  review_strengths?: string[];
  review_weaknesses?: string[];
  review_image_description?: string;
  review_criteria_checklist?: Record<string, unknown>;
  review_verdict?: string;
  impl_tags?: Record<string, string[]>;
}

// Plausible analytics (only in production)
declare global {
  interface Window {
    plausible?: (event: string, options?: { url?: string; props?: Record<string, string> }) => void;
  }
}
