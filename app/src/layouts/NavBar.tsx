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
  { label: 'mcp', to: '/mcp' },
  { label: 'about', to: '/about' },
];

const linkSx = {
  color: 'var(--ink-soft)',
  textDecoration: 'none',
  position: 'relative' as const,
  display: 'inline-block',
  // Below md (the two-row masthead of phones and tablets) the padding grows the
  // tap target to >= 44px; the negative margin compensates so the masthead
  // layout doesn't shift.
  padding: { xs: '14px 8px', md: '4px 0' },
  margin: { xs: '-14px -8px', md: 0 },
  transition: 'color 0.2s',
  '&::after': {
    content: '""',
    position: 'absolute' as const,
    // Keep the hover underline hugging the text despite the tap padding
    bottom: { xs: '10px', md: 0 },
    left: { xs: '8px', md: 0 },
    right: { xs: '8px', md: 0 },
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
    // Pull the ring back toward the text below md, where the box carries the
    // invisible tap padding
    outlineOffset: { xs: '-10px', md: '2px' },
  },
} as const;

const activeLinkSx = {
  ...linkSx,
  color: 'var(--ink)',
  '&::before': {
    // On phones the gap before a label can be as narrow as 9px, narrower than the box of the
    // "•" glyph, so the marker is a drawn 4px dot there: its box is its ink, and it ends 2px
    // before its own label. From sm the marker is the glyph.
    content: { xs: '""', sm: '"•"' },
    width: { xs: '4px', sm: 'auto' },
    height: { xs: '4px', sm: 'auto' },
    borderRadius: { xs: '50%', sm: 0 },
    backgroundColor: { xs: colors.primary, sm: 'transparent' },
    color: colors.primary,
    position: 'absolute' as const,
    // Offsets track the tap padding so the marker stays next to the text
    left: { xs: '2px', sm: '-4px', md: '-12px' },
    fontSize: '18px',
    lineHeight: 1,
    top: { xs: 'calc(50% - 2px)', sm: '13px', md: '3px' },
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
        // Below md: two rows (logo+search top, nav-links spanning wide below).
        // From md: single row: logo | nav-links | search. Eight links beside the
        // logo and the search need about 750 px, so a tablet width keeps two rows.
        gridTemplateColumns: { xs: '1fr auto', md: 'auto 1fr auto' },
        gridTemplateAreas: {
          xs: `"logo search" "nav nav"`,
          md: `"logo nav search"`,
        },
        alignItems: 'center',
        rowGap: { xs: 1.25, md: 0 },
        columnGap: { xs: 1.5, md: 4 },
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

      {/* Nav links — full row below md (shorthand labels on phones), inline from md */}
      <Box
        component="ul"
        sx={{
          gridArea: 'nav',
          display: 'flex',
          // The gap is the least space between two labels; below md the row spreads them wider.
          // From md to lg the row runs at 12px with 18px gaps: at 900px the full labels, the logo
          // and the search then fill all but ~13px, and the active "•" keeps clear of its neighbour.
          gap: { xs: 1, md: 2.25, lg: 3.5 },
          listStyle: 'none',
          m: 0,
          p: 0,
          fontFamily: typography.mono,
          // 12px from a 364px screen up; narrower phones shrink it so eight labels keep 8px apart.
          fontSize: { xs: 'clamp(10.5px, 3.3vw, 12px)', sm: '12px', lg: '13px' },
          justifyContent: { xs: 'space-between', md: 'flex-start' },
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
              {/* Full label from sm, short label on phones where it saves room */}
              <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
                {link.label}
              </Box>
              <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>
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
          fontSize: { xs: '11px', sm: '12px', lg: '13px' },
          color: 'var(--ink-soft)',
          cursor: 'pointer',
          transition: 'color 0.2s',
          textAlign: 'right',
          position: 'relative',
          // Below md the padding grows the tap target to >= 44px; the negative
          // margin compensates so the masthead layout doesn't shift.
          padding: { xs: '14px 8px', md: 0 },
          margin: { xs: '-14px -8px', md: 0 },
          '& .subj': { opacity: 0.55, transition: 'opacity 0.2s' },
          '&:hover': { color: colors.primary },
          '&:hover .subj': { opacity: 0.8 },
          // `all: unset` strips the UA focus ring — restore a visible one
          '&:focus-visible': {
            outline: `2px solid ${colors.primary}`,
            outlineOffset: { xs: '-10px', md: '2px' },
          },
        }}
      >
        <span className="subj">plots</span>.search()
      </Box>
    </Box>
  );
}
