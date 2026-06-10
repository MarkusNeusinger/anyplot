import Box from '@mui/material/Box';

import { colors, typography } from 'src/theme';

// Cached global tag counts — loaded once, shared across all SpecTabs instances
let cachedTagCounts: Record<string, Record<string, number>> | null = null;

export function getCachedTagCounts(): Record<string, Record<string, number>> | null {
  return cachedTagCounts;
}

export function setCachedTagCounts(counts: Record<string, Record<string, number>>) {
  cachedTagCounts = counts;
}

// Map tag category names to URL parameter names
export const SPEC_TAG_PARAM_MAP: Record<string, string> = {
  plot_type: 'plot',
  data_type: 'data',
  domain: 'dom',
  features: 'feat',
};

export const IMPL_TAG_PARAM_MAP: Record<string, string> = {
  dependencies: 'dep',
  techniques: 'tech',
  patterns: 'pat',
  dataprep: 'prep',
  styling: 'style',
};

export type TrackEventFn = (name: string, props?: Record<string, string | undefined>) => void;

// Parse text with backticks into React nodes with inline code styling
export function parseInlineCode(text: string): React.ReactNode[] {
  const parts = text.split(/(`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <Box
          key={i}
          component="code"
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: '0.8rem',
            bgcolor: 'var(--bg-surface)',
            color: colors.primary,
            px: 0.5,
            py: 0.25,
            borderRadius: 0.5,
          }}
        >
          {part.slice(1, -1)}
        </Box>
      );
    }
    return part;
  });
}

// Format date
export function formatDate(dateStr?: string) {
  if (!dateStr) return null;
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}
