import { Link } from 'react-router-dom';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { paths } from 'src/routes/paths';
import { colors, semanticColors, typography } from 'src/theme';

/**
 * The page for an address that names nothing. It sends no event of its own: the layout records
 * the address as a pageview like any other, so a missing page shows under the dashboard's pages
 * with the path the visitor asked for.
 */
export function NotFoundPage() {
  return (
    <>
      <>
        <title>page not found | anyplot.ai</title>
        <meta name="robots" content="noindex, follow" />
      </>
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
