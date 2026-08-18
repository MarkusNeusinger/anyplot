import { useEffect } from 'react';

import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { useAnalytics } from 'src/hooks/useAnalytics';
import { paths } from 'src/routes/paths';
import { colors, semanticColors, typography } from 'src/theme';

/** Where the miss came from — a URL that matches no route is a different
 *  problem from one that routes fine but names content we no longer have.
 *
 *  `impl_missing` is the odd one out: it is reported from SpecPage, which
 *  redirects the visitor to the hub rather than rendering this page, so the
 *  event fires without a 404 ever being shown. It is still the same signal —
 *  a URL naming content that no longer exists — and it is the case a library
 *  migration actually produces, so it belongs in the same event. */
export type NotFoundSource =
  'catch_all' | 'spec_missing' | 'impl_missing' | 'language_params' | 'route_error';

interface NotFoundPageProps {
  source?: NotFoundSource;
}

export function NotFoundPage({ source = 'catch_all' }: NotFoundPageProps = {}) {
  const { trackEvent } = useAnalytics();

  useEffect(() => {
    // window.location rather than useLocation: this component is also the
    // fallback inside RouteErrorBoundary, where router context is exactly the
    // thing that may have failed, and an analytics call must never be the
    // reason the 404 page itself cannot render.
    trackEvent('page_not_found', { path: window.location.pathname, source });
  }, [source, trackEvent]);

  return (
    <>
      <Helmet>
        <title>page not found | anyplot.ai</title>
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      <Box sx={{ textAlign: 'center', py: 12 }}>
        <Typography
          variant="h4"
          component="h1"
          aria-label="Page not found"
          sx={{
            fontFamily: typography.mono,
            fontWeight: 600,
            mb: 2,
            color: 'var(--ink)',
            '& .subj': { color: 'var(--ink-muted)' },
          }}
        >
          <span className="subj">page</span>.miss()
        </Typography>
        <Typography
          sx={{ fontFamily: typography.fontFamily, color: semanticColors.mutedText, mb: 4 }}
        >
          404 — no route matched
        </Typography>
        <Box
          component={Link}
          to={paths.home}
          aria-label="Go home"
          sx={{
            color: colors.primary,
            fontFamily: typography.mono,
            textDecoration: 'none',
            '&:hover': { textDecoration: 'underline' },
          }}
        >
          <span aria-hidden="true">
            <Box component="span" sx={{ color: 'var(--ink-muted)' }}>
              page
            </Box>
            .home()
          </span>
        </Box>
      </Box>
    </>
  );
}
