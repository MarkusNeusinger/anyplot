import Box from '@mui/material/Box';
import { colors, typography } from '../theme';
import { LANG_DISPLAY } from '../constants';

const DESCRIPTIONS: Record<string, string> = {
  matplotlib: 'The foundation. Publication-ready figures with total control.',
  seaborn: 'Statistical visualization, built on matplotlib. Elegant by default.',
  plotly: 'Interactive charts for the web. Hover, zoom, embed.',
  bokeh: 'Interactive plotting for modern browsers. Dashboard-ready.',
  altair: 'Declarative statistical visualization based on Vega-Lite.',
  plotnine: 'Grammar of Graphics in Python — if you miss ggplot2.',
  pygal: 'Minimalistic SVG charts with a clean API.',
  highcharts: 'Interactive web charts, stock charts, and maps.',
  letsplot: 'Grammar of graphics by JetBrains. Interactive.',
  ggplot2: 'The reference grammar of graphics. R’s expressive plotting standard.',
};

interface LibraryCardProps {
  name: string;
  language?: string;
  count?: number;
  onClick: () => void;
}

export function LibraryCard({ name, language, count, onClick }: LibraryCardProps) {
  const langLabel = language ? (LANG_DISPLAY[language] || language).toUpperCase() : null;
  return (
    <Box
      component="button"
      onClick={onClick}
      aria-label={`Browse ${name} examples`}
      sx={{
        all: 'unset',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        background: 'var(--bg-surface)',
        border: '1px solid var(--rule)',
        borderRadius: '12px',
        p: 3,
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: colors.primary,
          transform: 'scaleX(0)',
          transformOrigin: 'left',
          transition: 'transform 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        '&:hover': {
          transform: 'translateY(-3px)',
          boxShadow: '0 16px 32px -12px rgba(0,0,0,0.08)',
          borderColor: 'rgba(0, 158, 115, 0.2)',
          '&::before': { transform: 'scaleX(1)' },
          '& .lib-card-cta': { color: colors.primary },
        },
        '&:focus-visible': {
          outline: `2px solid ${colors.primary}`,
          outlineOffset: 2,
        },
      }}
    >
      {/* Top-right corner chip — sits above the card's flow content so it
          doesn't push the library name around. Top offset clears the 2px
          hover-accent that animates in via ::before. */}
      {langLabel && (
        <Box
          aria-label={`Language: ${langLabel}`}
          sx={{
            position: 'absolute',
            top: 10,
            right: 10,
            fontFamily: typography.mono,
            fontSize: '9px',
            fontWeight: 600,
            color: 'var(--ink-muted)',
            bgcolor: 'var(--bg-elevated)',
            border: '1px solid var(--rule)',
            borderRadius: '4px',
            px: 0.75,
            py: 0.25,
            letterSpacing: '0.08em',
            lineHeight: 1.4,
            pointerEvents: 'none',
          }}
        >
          {langLabel}
        </Box>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 1 }}>
        <Box sx={{
          fontFamily: typography.mono,
          fontSize: '15px',
          fontWeight: 700,
          color: 'var(--ink)',
          // Reserve space under the absolute-positioned chip so a long
          // library name doesn't slide under it.
          pr: langLabel ? 5 : 0,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          minWidth: 0,
        }}>
          {name}
        </Box>
        {count != null && (
          <Box sx={{
            fontFamily: typography.mono,
            fontSize: '10px',
            color: 'var(--ink-muted)',
            letterSpacing: '0.08em',
            flexShrink: 0,
          }}>
            {count} examples
          </Box>
        )}
      </Box>

      <Box sx={{
        fontFamily: typography.serif,
        fontSize: '14px',
        lineHeight: 1.5,
        color: 'var(--ink-soft)',
        fontWeight: 300,
      }}>
        {DESCRIPTIONS[name] || ''}
      </Box>

      <Box className="lib-card-cta" sx={{
        fontFamily: typography.mono,
        fontSize: '11px',
        color: 'var(--ink-muted)',
        mt: 'auto',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        transition: 'color 0.2s',
      }}>
        <span aria-hidden="true">.explore()</span>
      </Box>
    </Box>
  );
}
