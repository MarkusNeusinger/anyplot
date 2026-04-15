import Box from '@mui/material/Box';
import { colors, typography } from '../theme';

const ACCENT_COLORS: Record<string, string> = {
  matplotlib: colors.okabe.green,
  seaborn: colors.okabe.vermillion,
  plotly: colors.okabe.blue,
  bokeh: colors.okabe.purple,
  altair: colors.okabe.orange,
  plotnine: colors.okabe.sky,
  pygal: colors.okabe.green,
  highcharts: colors.okabe.vermillion,
  letsplot: colors.okabe.blue,
};

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
};

interface LibraryCardProps {
  name: string;
  count?: number;
  onClick: () => void;
}

export function LibraryCard({ name, count, onClick }: LibraryCardProps) {
  const accent = ACCENT_COLORS[name] || colors.primary;

  return (
    <Box
      component="button"
      onClick={onClick}
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
          background: accent,
          transform: 'scaleX(0)',
          transformOrigin: 'left',
          transition: 'transform 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        '&:hover': {
          transform: 'translateY(-3px)',
          boxShadow: '0 16px 32px -12px rgba(0,0,0,0.08)',
          borderColor: 'rgba(0, 158, 115, 0.2)',
          '&::before': { transform: 'scaleX(1)' },
        },
        '&:focus-visible': {
          outline: `2px solid ${colors.primary}`,
          outlineOffset: 2,
        },
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <Box sx={{
          fontFamily: typography.mono,
          fontSize: '15px',
          fontWeight: 700,
          color: 'var(--ink)',
        }}>
          {name}
        </Box>
        {count != null && (
          <Box sx={{
            fontFamily: typography.mono,
            fontSize: '10px',
            color: 'var(--ink-muted)',
            letterSpacing: '0.08em',
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

      <Box sx={{
        fontFamily: typography.mono,
        fontSize: '11px',
        color: 'var(--ink-muted)',
        mt: 'auto',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span>browse →</span>
      </Box>
    </Box>
  );
}
