import { Outlet, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';

import { useAnalytics } from '../hooks';
import { setAnalyticsAmbientProps } from '../hooks/useAnalytics';
import { useTheme } from '../hooks/useLayoutContext';
import { MastheadRule } from './MastheadRule';
import { NavBar } from './NavBar';
import { Footer } from './Footer';

const containerSx = {
  px: { xs: 2, sm: 4, md: 8, lg: 12 },
  maxWidth: 'var(--max-catalog)',
  mx: 'auto',
} as const;

/**
 * Global layout shell — sticky masthead + navbar above, footer below, page
 * content via <Outlet />. On most routes the masthead sticks so the breadcrumb
 * stays visible while scrolling. On /plots the masthead flows with the page
 * so the FilterBar becomes the single sticky element at the top (browsing
 * screens need all the vertical room the viewport can give).
 */
export function RootLayout() {
  const { trackEvent } = useAnalytics();
  const { pathname } = useLocation();
  const { isDark } = useTheme();
  const mastheadSticks = pathname !== '/plots';

  // Set synchronously during render so the first pageview from a child page's
  // useEffect (which runs before the parent's useEffect) carries the theme prop.
  // setAnalyticsAmbientProps merges into module state, so re-renders are safe.
  setAnalyticsAmbientProps({ theme: isDark ? 'dark' : 'light' });

  return (
    <Box sx={{
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100svh',
      bgcolor: 'var(--bg-page)',
    }}>
      {/* Masthead — sticky everywhere except /plots, where it scrolls away with the page. */}
      <Box
        sx={{
          ...(mastheadSticks ? { position: 'sticky', top: 0, zIndex: 100 } : {}),
          bgcolor: 'var(--bg-page)',
          boxShadow: '0 1px 0 rgba(0,0,0,0.02)',
        }}
      >
        <Container maxWidth={false} sx={containerSx}>
          <MastheadRule />
        </Container>
      </Box>

      {/* NavBar flows with the page — scrolls out of view with the hero. */}
      <Container component="header" maxWidth={false} sx={containerSx}>
        <NavBar />
      </Container>

      <Box component="main" sx={{ flex: 1 }}>
        <Container maxWidth={false} sx={containerSx}>
          <Outlet />
        </Container>
      </Box>

      <Container maxWidth={false} sx={{ ...containerSx, pb: { xs: 4, md: 6 } }}>
        <Footer onTrackEvent={trackEvent} />
      </Container>
    </Box>
  );
}
