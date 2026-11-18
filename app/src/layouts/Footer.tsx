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
// bounds the row keeps at least the clearance it has at the default.
const ONE_ROW = '@media (min-width: 720px) and (min-width: 45em)';

// Below ONE_ROW the four links share a line and the name takes the line below it. That line is
// 270px wide at the 16px default: 222px of text, which grows with the default font size, and
// 48px of gaps, which do not. With the page's 16px on each side of a phone it fits from 302px at
// the default, 358px at 20px and 413px at 24px. 19em is 304px at the default and grows faster
// than the line, so it is the bound; 304px is the floor for a smaller default, where 19em alone
// would come before the line fits. Below the bound the links break as their pairs, "github · mcp"
// over "about · legal", and the separator between the pairs goes, so no line starts or ends on a
// "·". On a phone the footer lift parks the buttons 13px above the footer's first line. From
// 600px up, with a default from 16 to 24px, the links' line comes closest to the scroll-to-top
// button at 600px: 11.1px with a 23px default, and 9.3px with a 22px default when a classic
// 15px scrollbar narrows the layout. A default font size up to 24px, Chrome's largest preset, is
// the supported range. With a hand-set default of 36px or more, between 600 and about 650px wide,
// the builder's name touches the scroll-to-top button on /specs and /plots; that is accepted.
const LINKS_ROW = '@media (min-width: 304px) and (min-width: 19em)';

const pairSx = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 1,
  flexBasis: '100%',
  [LINKS_ROW]: { flexBasis: 'auto' },
} as const;
const separatorBetweenPairsSx = { display: 'none', [LINKS_ROW]: { display: 'inline' } } as const;
const oneRowOnlySx = { display: 'none', [ONE_ROW]: { display: 'inline' } } as const;
const nameOnOwnLineSx = {
  flexBasis: '100%',
  textAlign: 'center',
  [ONE_ROW]: { display: 'none' },
} as const;

function NameLink() {
  return (
    <Link
      href="https://www.linkedin.com/in/markus-neusinger/"
      target="_blank"
      rel="noopener noreferrer"
      sx={linkSx}
    >
      markus neusinger
    </Link>
  );
}

// The name stands in the middle of the single row and on a line of its own below the links
// everywhere else. Keyboard and screen-reader order follow the DOM, and a CSS `order` would move
// the name only for the eye, so the name is in the DOM twice, once at each place, and the copy
// that does not belong to the layout is display: none, which takes it out of the tab order and
// the accessibility tree. Each layout then reads in the order it shows.
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
      <Box component="span" sx={pairSx}>
        <Link href={GITHUB_URL} target="_blank" rel="noopener noreferrer" sx={linkSx}>
          github
        </Link>
        <span>·</span>
        <Link component={RouterLink} to={paths.mcp} sx={linkSx}>
          mcp
        </Link>
      </Box>
      <Box component="span" sx={separatorBetweenPairsSx}>
        ·
      </Box>
      <Box component="span" sx={oneRowOnlySx}>
        <NameLink />
      </Box>
      <Box component="span" sx={oneRowOnlySx}>
        ·
      </Box>
      <Box component="span" sx={pairSx}>
        <Link component={RouterLink} to={paths.about} sx={linkSx}>
          about
        </Link>
        <span>·</span>
        <Link component={RouterLink} to={paths.legal} sx={linkSx}>
          legal
        </Link>
      </Box>
      {/* A full-width line; the link inside keeps its own width, so its hover underline stays as
          long as the name. */}
      <Box component="span" sx={nameOnOwnLineSx}>
        <NameLink />
      </Box>
    </Box>
  );
}
