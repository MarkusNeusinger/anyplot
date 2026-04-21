import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';

import { LibraryCard } from '../components/LibraryCard';
import { SectionHeader } from '../components/SectionHeader';
import { useAnalytics, useAppData } from '../hooks';
import { LIBRARIES } from '../constants';
import { colors, typography, textStyle } from '../theme';

export function LibrariesPage() {
  const navigate = useNavigate();
  const { librariesData } = useAppData();
  const { trackPageview, trackEvent } = useAnalytics();

  useEffect(() => {
    trackPageview('/libraries');
  }, [trackPageview]);

  const byId = new Map(librariesData.map(lib => [lib.id, lib]));

  const handleLibraryClick = (name: string) => {
    trackEvent('library_click', { source: 'libraries_page', library: name });
    navigate(`/plots?lib=${name}`);
  };

  return (
    <>
      <Helmet>
        <title>libraries | anyplot.ai</title>
        <meta
          name="description"
          content="Nine Python plotting libraries — matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, lets-plot. Same specs, every library."
        />
        <meta property="og:title" content="libraries | anyplot.ai" />
        <meta
          property="og:description"
          content="Nine Python plotting libraries — same specs, every library."
        />
        <link rel="canonical" href="https://anyplot.ai/libraries" />
      </Helmet>

      <Box sx={{ maxWidth: 'var(--max-catalog, 2200px)', mx: 'auto', pb: 6 }}>
        <SectionHeader prompt="§" title={<em>libraries</em>} />

        <Box sx={{ ...textStyle, maxWidth: 720, mb: 6 }}>
          Each spec is implemented in every supported library so you can compare side-by-side.
          Click a library to browse its plots, or open the upstream documentation in a new tab.
        </Box>

        <Box sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(auto-fill, minmax(320px, 1fr))' },
          gap: 2.5,
        }}>
          {LIBRARIES.map(name => {
            const meta = byId.get(name);
            return (
              <Box key={name} sx={{ position: 'relative' }}>
                <LibraryCard name={name} onClick={() => handleLibraryClick(name)} />
                {meta?.documentation_url && (
                  <Box sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    px: 0.5,
                    pt: 1,
                    fontFamily: typography.mono,
                    fontSize: '11px',
                    color: 'var(--ink-muted)',
                  }}>
                    <span>{meta.version ? `v${meta.version}` : ''}</span>
                    <Link
                      href={meta.documentation_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => {
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
