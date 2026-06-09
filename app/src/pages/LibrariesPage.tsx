import { useEffect, useState } from 'react';

import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';

import { LibraryCard } from 'src/components/LibraryCard';
import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_TO_FRAMEWORK, LIBRARIES } from 'src/constants';
import { useAnalytics, useAppData } from 'src/hooks';
import { colors, textStyle, typography } from 'src/theme';

// Framework filter (per library-expansion.md §6: "all JavaScript libs" vs
// "React-compatible"). Built generically off LIB_TO_FRAMEWORK so adding a
// Recharts / Vue / Svelte entry later is a one-line registry change — the
// matching filter chip appears here automatically, no UI edit. 'all' shows
// everything; any other value is a framework id that matches that framework.
type FrameworkFilter = string;

// Human label per framework; unknown frameworks fall back to "<id>-compatible".
const FRAMEWORK_FILTER_LABEL: Record<string, string> = {
  react: 'React-compatible',
  vue: 'Vue-compatible',
  svelte: 'Svelte-compatible',
  angular: 'Angular-compatible',
};

// Distinct non-"none" frameworks actually present in the registry, in stable
// order — the data-driven source for the filter chips below.
const PRESENT_FRAMEWORKS = Array.from(
  new Set(LIBRARIES.map(name => LIB_TO_FRAMEWORK[name]).filter(fw => fw && fw !== 'none'))
).sort();

const FILTERS: { id: FrameworkFilter; label: string }[] = [
  { id: 'all', label: 'all libraries' },
  ...PRESENT_FRAMEWORKS.map(fw => ({
    id: fw,
    label: FRAMEWORK_FILTER_LABEL[fw] ?? `${fw}-compatible`,
  })),
];

export function LibrariesPage() {
  const navigate = useNavigate();
  const { librariesData } = useAppData();
  const { trackPageview, trackEvent } = useAnalytics();
  const [frameworkFilter, setFrameworkFilter] = useState<FrameworkFilter>('all');

  useEffect(() => {
    trackPageview('/libraries');
  }, [trackPageview]);

  const byId = new Map(librariesData.map(lib => [lib.id, lib]));

  const visibleLibraries =
    frameworkFilter === 'all'
      ? LIBRARIES
      : LIBRARIES.filter(name => LIB_TO_FRAMEWORK[name] === frameworkFilter);

  const handleLibraryClick = (name: string) => {
    trackEvent('library_click', { source: 'libraries_page', library: name });
    navigate(`/plots?lib=${name}`);
  };

  const handleFilterClick = (id: FrameworkFilter) => {
    setFrameworkFilter(id);
    trackEvent('library_filter', { source: 'libraries_page', framework: id });
  };

  return (
    <>
      <Helmet>
        <title>libraries | anyplot.ai</title>
        <meta
          name="description"
          content="Fifteen plotting libraries across Python, R, Julia, and JavaScript — matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, lets-plot, ggplot2, Makie.jl, Chart.js, D3.js, ECharts, Highcharts, MUI X Charts. Same specs, every library."
        />
        <meta property="og:title" content="libraries | anyplot.ai" />
        <meta
          property="og:description"
          content="Fifteen plotting libraries across Python, R, Julia, and JavaScript — same specs, every library."
        />
        <link rel="canonical" href="https://anyplot.ai/libraries" />
      </Helmet>

      <Box sx={{ maxWidth: 'var(--max-catalog, 2200px)', mx: 'auto', pt: { xs: 2, md: 3 }, pb: 6 }}>
        <SectionHeader prompt="❯" title={<em>libraries</em>} />

        <Box sx={{ ...textStyle, maxWidth: 720, mb: 3 }}>
          each spec is implemented in every supported library so you can compare side-by-side. click
          a library to browse its plots, or open the upstream documentation in a new tab.
        </Box>

        {/* Framework filter — "all libraries" vs "React-compatible" (§6). */}
        <Box
          role="group"
          aria-label="Filter libraries by framework"
          sx={{ display: 'flex', gap: 1, mb: 5, flexWrap: 'wrap' }}
        >
          {FILTERS.map(({ id, label }) => {
            const active = frameworkFilter === id;
            return (
              <Box
                key={id}
                component="button"
                type="button"
                onClick={() => handleFilterClick(id)}
                aria-pressed={active}
                sx={{
                  all: 'unset',
                  cursor: 'pointer',
                  fontFamily: typography.mono,
                  fontSize: '12px',
                  letterSpacing: '0.04em',
                  px: 1.5,
                  py: 0.75,
                  borderRadius: '6px',
                  border: `1px solid ${active ? colors.primary : 'var(--rule)'}`,
                  color: active ? colors.primary : 'var(--ink-muted)',
                  bgcolor: active ? 'rgba(0, 158, 115, 0.08)' : 'transparent',
                  transition: 'all 0.2s',
                  '&:hover': { borderColor: colors.primary, color: colors.primary },
                  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
                }}
              >
                {label}
              </Box>
            );
          })}
        </Box>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(auto-fill, minmax(280px, 1fr))',
            },
            gap: 2.5,
          }}
        >
          {visibleLibraries.map(name => {
            const meta = byId.get(name);
            return (
              <Box key={name} sx={{ position: 'relative' }}>
                <LibraryCard
                  name={name}
                  language={meta?.language}
                  onClick={() => handleLibraryClick(name)}
                />
                {meta?.documentation_url && (
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      px: 0.5,
                      pt: 1,
                      fontFamily: typography.mono,
                      fontSize: '11px',
                      color: 'var(--ink-muted)',
                    }}
                  >
                    <span>{meta.version ? `v${meta.version}` : ''}</span>
                    <Link
                      href={meta.documentation_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={e => {
                        e.stopPropagation();
                        trackEvent('external_link', { destination: 'library_docs', library: name });
                      }}
                      sx={{
                        color: 'var(--ink-muted)',
                        textDecoration: 'none',
                        '&:hover': { color: colors.primary },
                      }}
                    >
                      docs ↗
                    </Link>
                  </Box>
                )}
              </Box>
            );
          })}
        </Box>
      </Box>
    </>
  );
}
