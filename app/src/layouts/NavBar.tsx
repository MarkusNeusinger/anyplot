import { useCallback, useEffect, useRef } from 'react';

import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';

import { paths } from 'src/routes/paths';
import { colors, typography } from 'src/theme';

const DEBUG_CLICK_COUNT = 5;
const DEBUG_CLICK_WINDOW_MS = 800;

const NAV_LINKS: { label: string; to: string; short?: string }[] = [
  { label: 'specs', to: '/specs' },
  { label: 'plots', to: '/plots' },
  { label: 'map', to: '/map' },
  { label: 'libraries', to: '/libraries', short: 'libs' },
  { label: 'stats', to: '/stats' },
  { label: 'palette', to: '/palette', short: 'pal' },
  { label: 'about', to: '/about' },
];

// Logo, seven short labels and the search share one row from 716px up with MonoLisa; below that the
// grid squeezed the logo onto two lines and pushed the search past the edge. So the two-row
// masthead of phones runs up to 719px.
const ONE_ROW = '@media (min-width: 720px)';

// Below 353px the row's gaps are narrower than the box of the "•" glyph plus 3px, so the marker
// there is a drawn 4px dot that ends 2px before its label: its box is its ink.
const NARROW_PHONE = '@media (max-width: 359.95px)';

const linkSx = {
  color: 'var(--ink-soft)',
  textDecoration: 'none',
  position: 'relative' as const,
  display: 'inline-block',
  // On xs the padding grows the tap target to >= 44px; the negative margin
  // compensates so the masthead layout doesn't shift.
  padding: { xs: '14px 8px', sm: '4px 0' },
  margin: { xs: '-14px -8px', sm: 0 },
  transition: 'color 0.2s',
  '&::after': {
    content: '""',
    position: 'absolute' as const,
    // Keep the hover underline hugging the text despite the xs tap padding
    bottom: { xs: '10px', sm: 0 },
    left: { xs: '8px', sm: 0 },
    right: { xs: '8px', sm: 0 },
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
  '&:focus-visible': {
    outline: `2px solid ${colors.primary}`,
    // Pull the ring back toward the text on xs, where the box carries the
    // invisible tap padding
    outlineOffset: { xs: '-10px', sm: '2px' },
  },
} as const;

const activeLinkSx = {
  ...linkSx,
  color: 'var(--ink)',
  '&::before': {
    content: '"•"',
    color: colors.primary,
    position: 'absolute' as const,
    // Offsets track the xs tap padding so the bullet stays next to the text
    left: { xs: '-4px', sm: '-12px' },
    fontSize: '18px',
    lineHeight: 1,
    top: { xs: '13px', sm: '3px' },
    [NARROW_PHONE]: {
      content: '""',
      width: '4px',
      height: '4px',
      borderRadius: '50%',
      backgroundColor: colors.primary,
      left: '2px',
      top: 'calc(50% - 2px)',
    },
  },
} as const;

export function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const clickCountRef = useRef(0);
  const clickTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
    };
  }, []);

  const handleSearch = () => {
    navigate(paths.plotsSearch);
  };

  // 5 rapid clicks on the logo opens /debug.
  // Non-triggering clicks fall through to RouterLink's normal `/` navigation.
  const handleLogoClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
      clickCountRef.current += 1;
      if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
      clickTimerRef.current = setTimeout(() => {
        clickCountRef.current = 0;
      }, DEBUG_CLICK_WINDOW_MS);
      if (clickCountRef.current >= DEBUG_CLICK_COUNT) {
        e.preventDefault();
        navigate(paths.debug);
      }
    },
    [navigate]
  );

  return (
    <Box
      component="nav"
      sx={{
        display: 'grid',
        // Below 720px: two rows (logo+search top, nav-links spanning wide below).
        // From 720px: single row: logo | nav-links | search.
        gridTemplateColumns: '1fr auto',
        gridTemplateAreas: `"logo search" "nav nav"`,
        alignItems: 'center',
        rowGap: 1.25,
        columnGap: 1.5,
        [ONE_ROW]: {
          gridTemplateColumns: 'auto 1fr auto',
          gridTemplateAreas: `"logo nav search"`,
          rowGap: 0,
          columnGap: 4,
        },
        py: { xs: 1.25, sm: 2 },
        borderBottom: '1px solid var(--rule)',
      }}
    >
      {/* Logo */}
      <Box
        component={RouterLink}
        to={paths.home}
        onClick={handleLogoClick}
        sx={{
          gridArea: 'logo',
          fontFamily: typography.mono,
          fontWeight: 700,
          fontSize: { xs: '18px', sm: '22px' },
          letterSpacing: '-0.02em',
          textDecoration: 'none',
          color: 'var(--ink)',
          userSelect: 'none',
        }}
      >
        any
        <Box
          component="span"
          sx={{
            color: colors.primary,
            display: 'inline-block',
            transform: 'scale(1.45)',
            mx: '2px',
          }}
        >
          .
        </Box>
        plot
        <Box component="span" sx={{ fontWeight: 400, opacity: 0.45 }}>
          ()
        </Box>
      </Box>

      {/* Nav links — full row below 720px (shorthand labels below md), inline from 720px */}
      <Box
        component="ul"
        sx={{
          gridArea: 'nav',
          display: 'flex',
          // The gap is the least space between two labels; in the full-width row space-between
          // spreads them wider. 8px lets seven labels fit a 320px phone. From 900 to 1199px the
          // full labels at 13px leave the logo room for one line only with 20px gaps.
          gap: { xs: 1, sm: 2.25, md: 2.5, lg: 3.5 },
          listStyle: 'none',
          m: 0,
          p: 0,
          fontFamily: typography.mono,
          fontSize: { xs: '12px', sm: '12px', md: '13px' },
          justifyContent: 'space-between',
          [ONE_ROW]: { justifyContent: 'flex-start' },
          flexWrap: 'nowrap',
        }}
      >
        {NAV_LINKS.map(link => (
          <li key={link.to}>
            <Box
              component={RouterLink}
              to={link.to}
              sx={location.pathname === link.to ? activeLinkSx : linkSx}
            >
              {/* Full label on ≥md, short label on smaller screens where it saves room */}
              <Box component="span" sx={{ display: { xs: 'none', md: 'inline' } }}>
                {link.label}
              </Box>
              <Box component="span" sx={{ display: { xs: 'inline', md: 'none' } }}>
                {link.short || link.label}
              </Box>
            </Box>
          </li>
        ))}
      </Box>

      {/* Search — method-call link, opens the filter-bar search on /plots */}
      <Box
        component="button"
        onClick={handleSearch}
        aria-label="Search plots"
        sx={{
          gridArea: 'search',
          all: 'unset',
          fontFamily: typography.mono,
          fontSize: { xs: '11px', sm: '12px', md: '13px' },
          color: 'var(--ink-soft)',
          cursor: 'pointer',
          transition: 'color 0.2s',
          textAlign: 'right',
          position: 'relative',
          // On xs the padding grows the tap target to >= 44px; the negative
          // margin compensates so the masthead layout doesn't shift.
          padding: { xs: '14px 8px', sm: 0 },
          margin: { xs: '-14px -8px', sm: 0 },
          '& .subj': { opacity: 0.55, transition: 'opacity 0.2s' },
          '&:hover': { color: colors.primary },
          '&:hover .subj': { opacity: 0.8 },
          // `all: unset` strips the UA focus ring — restore a visible one
          '&:focus-visible': {
            outline: `2px solid ${colors.primary}`,
            outlineOffset: { xs: '-10px', sm: '2px' },
          },
        }}
      >
        <span className="subj">plots</span>.search()
      </Box>
    </Box>
  );
}
