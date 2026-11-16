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

// The single row is 457px wide with MonoLisa at 14px and sits centred. From 600px up nothing
// lifts the floating buttons (useFooterLift), so the row has to end left of the scroll-to-top
// button on /specs and /plots, 112px from the right edge: it clears it from 682px, by 8px from
// 698px, and a classic 15px scrollbar (it narrows the layout, not the media query) adds its width
// to both. At 720px, where the masthead also takes one row, it clears it by 19px, 12px with that
// scrollbar. The row's text is in rem and follows the browser's default font size; its gaps and
// the corner buttons are in px and do not. So the row also waits for 45em, which is 720px at the
// 16px default and moves with that setting: 900px at 20px, where the row is 555px wide and a
// 720px bound alone would let it run under the button up to about 780px. 720px stays the floor,
// because with 45em alone a 13px default puts the row 3.5px under the button at 600px. With both
// bounds the row keeps at least the clearance it has at the default. Below them the name takes a
// line of its own between "github · mcp" and "about · legal", rows short enough to stay clear of
// the corner at any width.
const ONE_ROW = '@media (min-width: 720px) and (min-width: 45em)';
const separatorBesideNameSx = { display: 'none', [ONE_ROW]: { display: 'inline' } } as const;

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
      <Link component={RouterLink} to={paths.mcp} sx={linkSx}>
        mcp
      </Link>
      <Box component="span" sx={separatorBesideNameSx}>
        ·
      </Box>
      {/* A full-width line below the single row's width; the link inside keeps its own width,
          so its hover underline stays as long as the name. */}
      <Box
        component="span"
        sx={{ flexBasis: '100%', textAlign: 'center', [ONE_ROW]: { flexBasis: 'auto' } }}
      >
        <Link
          href="https://www.linkedin.com/in/markus-neusinger/"
          target="_blank"
          rel="noopener noreferrer"
          sx={linkSx}
        >
          markus neusinger
        </Link>
      </Box>
      <Box component="span" sx={separatorBesideNameSx}>
        ·
      </Box>
      <Link component={RouterLink} to={paths.about} sx={linkSx}>
        about
      </Link>
      <span>·</span>
      <Link component={RouterLink} to={paths.legal} sx={linkSx}>
        legal
      </Link>
    </Box>
  );
}
