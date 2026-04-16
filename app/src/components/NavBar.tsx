import { useCallback } from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import { colors, typography } from '../theme';

interface NavBarProps {
  /** Ref to FilterBar search input -- when on /plots, focuses it; otherwise navigates to /plots */
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
}

const NAV_LINKS = [
  { label: 'plots', to: '/plots' },
  { label: 'specs', to: '/specs' },
  { label: 'palette', to: '/palette' },
  { label: 'mcp', to: '/mcp' },
];

const linkSx = {
  color: 'var(--ink-soft)',
  textDecoration: 'none',
  position: 'relative' as const,
  padding: '4px 0',
  transition: 'color 0.2s',
  '&::after': {
    content: '""',
    position: 'absolute' as const,
    bottom: 0,
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

const activeLinkSx = {
  ...linkSx,
  color: 'var(--ink)',
  '&::before': {
    content: '"•"',
    color: colors.primary,
    position: 'absolute' as const,
    left: -12,
    fontSize: '18px',
    lineHeight: 1,
    top: '3px',
  },
} as const;

export function NavBar({ searchInputRef }: NavBarProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleSearch = useCallback(() => {
    if (location.pathname === '/plots' && searchInputRef?.current) {
      searchInputRef.current.focus();
    } else {
      navigate('/plots');
    }
  }, [location.pathname, searchInputRef, navigate]);

  return (
    <Box component="nav" sx={{
      display: 'grid',
      gridTemplateColumns: 'auto 1fr auto',
      alignItems: 'center',
      py: 2,
      gap: 4,
      borderBottom: '1px solid var(--rule)',
    }}>
      {/* Logo */}
      <Box
        component={RouterLink}
        to="/"
        sx={{
          fontFamily: typography.mono,
          fontWeight: 700,
          fontSize: '22px',
          letterSpacing: '-0.02em',
          textDecoration: 'none',
          color: 'var(--ink)',
        }}
      >
        any<Box component="span" sx={{ color: colors.primary, display: 'inline-block', transform: 'scale(1.45)', mx: '2px' }}>.</Box>plot<Box component="span" sx={{ fontWeight: 400, opacity: 0.45 }}>()</Box>
      </Box>

      {/* Nav links */}
      <Box component="ul" sx={{
        display: { xs: 'none', sm: 'flex' },
        gap: 3.5,
        listStyle: 'none',
        m: 0,
        p: 0,
        fontFamily: typography.mono,
        fontSize: '13px',
      }}>
        {NAV_LINKS.map(link => (
          <li key={link.to}>
            <Box
              component={RouterLink}
              to={link.to}
              sx={location.pathname === link.to ? activeLinkSx : linkSx}
            >
              {link.label}
            </Box>
          </li>
        ))}
      </Box>

      {/* Search pill */}
      <Box
        component="button"
        onClick={handleSearch}
        sx={{
          all: 'unset',
          boxSizing: 'border-box',
          fontFamily: typography.mono,
          fontSize: '12px',
          padding: '8px 14px',
          bgcolor: 'var(--bg-surface)',
          border: '1px solid var(--rule)',
          borderRadius: '99px',
          color: 'var(--ink-muted)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          transition: 'all 0.2s',
          '&:hover': {
            borderColor: 'var(--ink-soft)',
            color: 'var(--ink)',
          },
        }}
      >
        <span>⌕ search plots</span>
        <Box component="span" sx={{
          fontFamily: typography.mono,
          fontSize: '10px',
          padding: '1px 5px',
          bgcolor: 'var(--bg-page)',
          border: '1px solid var(--rule)',
          borderRadius: '3px',
          letterSpacing: 0,
          display: { xs: 'none', md: 'inline' },
        }}>
          ⌘ K
        </Box>
      </Box>
    </Box>
  );
}
