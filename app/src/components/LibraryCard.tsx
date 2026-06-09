import Box from '@mui/material/Box';
import { colors, typography } from '../theme';
import { LANG_DISPLAY, LIB_TO_FRAMEWORK } from '../constants';

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
  makie: 'High-performance Julia visualization. CairoMakie ships publication-quality static charts.',
  chartjs: 'Simple, flexible HTML5-canvas charts. The popular JS default.',
  d3: 'Data-driven SVG. Low-level, maximum control on the web.',
  echarts: 'Powerful interactive charts for the browser. Vast chart catalog.',
  muix: 'Charts for the MUI / Material UI React ecosystem. Community @mui/x-charts.',
};

// Human label for a non-"none" framework constraint (drives the React badge).
const FRAMEWORK_LABEL: Record<string, string> = {
  react: 'React',
  vue: 'Vue',
  svelte: 'Svelte',
  angular: 'Angular',
};

// Short license note surfaced on the card. Only set where it's worth calling
// out (e.g. MUI X ships community-MIT while Pro/Premium stay out of scope).
const LICENSE_NOTE: Record<string, string> = {
  muix: 'MIT · community',
};

interface LibraryCardProps {
  name: string;
  language?: string;
  count?: number;
  onClick: () => void;
}

export function LibraryCard({ name, language, count, onClick }: LibraryCardProps) {
  const langLabel = language ? (LANG_DISPLAY[language] || language).toUpperCase() : null;
  const framework = LIB_TO_FRAMEWORK[name];
  const frameworkLabel = framework && framework !== 'none' ? (FRAMEWORK_LABEL[framework] || framework) : null;
  const licenseNote = LICENSE_NOTE[name];
  const hasBadge = !!(langLabel || frameworkLabel);
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
      {/* Top-right corner chips — language, and (for framework-locked libs like
          MUI X) a framework badge stacked beneath it. They sit above the card's
          flow content so they don't push the library name around; the top offset
          clears the 2px hover-accent that animates in via ::before. */}
      {hasBadge && (
        <Box
          sx={{
            position: 'absolute',
            top: 10,
            right: 10,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: 0.5,
            pointerEvents: 'none',
          }}
        >
          {langLabel && (
            <Box
              aria-label={`Language: ${langLabel}`}
              sx={{
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
              }}
            >
              {langLabel}
            </Box>
          )}
          {frameworkLabel && (
            <Box
              aria-label={`Framework: ${frameworkLabel}`}
              sx={{
                fontFamily: typography.mono,
                fontSize: '9px',
                fontWeight: 600,
                color: colors.primary,
                bgcolor: 'var(--bg-elevated)',
                border: `1px solid ${colors.primary}`,
                borderRadius: '4px',
                px: 0.75,
                py: 0.25,
                letterSpacing: '0.08em',
                lineHeight: 1.4,
              }}
            >
              {frameworkLabel}
            </Box>
          )}
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
          pr: hasBadge ? 5 : 0,
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
        {licenseNote && (
          <Box component="span" aria-label={`License: ${licenseNote}`} sx={{
            fontSize: '10px',
            letterSpacing: '0.06em',
            color: 'var(--ink-muted)',
          }}>
            {licenseNote}
          </Box>
        )}
      </Box>
    </Box>
  );
}
