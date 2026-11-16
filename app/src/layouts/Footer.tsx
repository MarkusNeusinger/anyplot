import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';

import { GITHUB_URL } from 'src/constants';
import { paths } from 'src/routes/paths';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

const linkSx = {
  color: semanticColors.mutedText,
  textDecoration: 'none',
  position: 'relative' as const,
  '&::after': {
    content: '""',
    position: 'absolute' as const,
    bottom: -1,
    left: 0,
    right: 0,
    height: '1px',
    background: colors.primary,
    transform: 'scaleX(0)',
    transformOrigin: 'left',
    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  },
  '&:hover': {
    color: 'var(--ink)',
    '&::after': { transform: 'scaleX(1)' },
  },
} as const;

const ISSUE_CHOOSER_URL = `${GITHUB_URL}/issues/new/choose`;

// The five links need 356px in one row with MonoLisa at 14px. Below 400px the row would break
// before its last link and end on a "·", so the site's own pages take a row of their own there.
const NARROW = '@media (max-width: 399.95px)';
const siteRowSx = {
  display: 'flex',
  flexBasis: '100%',
  justifyContent: 'center',
  gap: 1,
} as const;

export function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        mt: 4,
        pt: 4,
        borderTop: '1px solid var(--rule)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 1,
        fontSize: fontSize.md,
        fontFamily: typography.mono,
        color: semanticColors.mutedText,
        letterSpacing: '0.08em',
      }}
    >
      <Link href={GITHUB_URL} target="_blank" rel="noopener noreferrer" sx={linkSx}>
        github
      </Link>
      <span>·</span>
      <Link href={ISSUE_CHOOSER_URL} target="_blank" rel="noopener noreferrer" sx={linkSx}>
        report
      </Link>
      <Box component="span" sx={{ [NARROW]: { display: 'none' } }}>
        ·
      </Box>
      {/* The site's own pages: in the row above 400px, a row of their own below. */}
      <Box component="span" sx={{ display: 'contents', [NARROW]: siteRowSx }}>
        <Link component={RouterLink} to={paths.mcp} sx={linkSx}>
          mcp
        </Link>
        <span>·</span>
        <Link component={RouterLink} to={paths.about} sx={linkSx}>
          about
        </Link>
        <span>·</span>
        <Link component={RouterLink} to={paths.legal} sx={linkSx}>
          legal
        </Link>
      </Box>
      {/* Below md the name takes a line of its own: the links alone stay clear of the floating
          buttons in the corner, which useFooterLift lifts only below sm. */}
      <Box component="span" sx={{ display: { xs: 'none', md: 'inline' } }}>
        ·
      </Box>
      <Box component="span" sx={{ flexBasis: { xs: '100%', md: 'auto' }, textAlign: 'center' }}>
        <Link
          href="https://www.linkedin.com/in/markus-neusinger/"
          target="_blank"
          rel="noopener noreferrer"
          sx={linkSx}
        >
          markus neusinger
        </Link>
      </Box>
    </Box>
  );
}
