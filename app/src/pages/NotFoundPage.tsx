import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { colors, semanticColors, typography } from '../theme';

export function NotFoundPage() {
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
          to="/"
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
