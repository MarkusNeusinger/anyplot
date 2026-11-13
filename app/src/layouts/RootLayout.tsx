import { useEffect, useLayoutEffect } from 'react';

import { Outlet, useLocation, useNavigationType } from 'react-router-dom';

import Box from '@mui/material/Box';
import Container from '@mui/material/Container';

import { FeedbackWidget } from 'src/components/FeedbackWidget';
import { useAnalytics } from 'src/hooks';
import { setAnalyticsAmbientProps } from 'src/hooks/useAnalytics';
import { useTheme } from 'src/hooks/useLayoutContext';
import { Footer } from 'src/layouts/Footer';
import { MastheadRule } from 'src/layouts/MastheadRule';
import { NavBar } from 'src/layouts/NavBar';
import { isPlotsPath, paths } from 'src/routes/paths';

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
  const { trackPageview } = useAnalytics();
  const { pathname, search, hash } = useLocation();
  const navigationType = useNavigationType();
  const { effective } = useTheme();
  const mastheadSticks = pathname !== paths.plots;
  // The agent chat has a feedback row of its own on every result, and the chat's for a session
  // without one; on a phone the site's button covered the composer's buttons and the replies.
  const siteFeedback = pathname !== paths.agent;

  // Set synchronously during render so the pageview below and a child page's
  // first event carry the theme prop.
  // setAnalyticsAmbientProps merges into module state, so re-renders are safe.
  // The ambient prop tracks the *effective* theme so existing Plausible
  // dark/light breakdowns keep working regardless of mode (system/light/dark).
  setAnalyticsAmbientProps({ theme: effective });

  // Reset scroll on forward navigation (PUSH/REPLACE). In SPA route changes,
  // the next page can otherwise keep the previous page's scroll position,
  // which is especially noticeable on short pages like /legal. Skip on POP
  // so browser back/forward keeps native scroll restoration; skip when a
  // hash anchor is present so in-page anchors still work. Pages with their
  // own saved-scroll restore in a later effect can still override this.
  // The gallery is such a page, and it turns the browser's restoration off
  // (`PlotsPage`): there the reset also runs on POP, or the offset of the page
  // being left would stand until the gallery restores its own, and count as
  // the visitor's scrolling of the gallery (`usePlotsScrolled`).
  // A layout effect, and declared before the pageview's: the script takes the
  // scroll position at the pageview as the new page's first depth.
  useLayoutEffect(() => {
    if (hash) return;
    if (navigationType === 'POP' && !isPlotsPath(pathname)) return;
    window.scrollTo(0, 0);
  }, [pathname, hash, navigationType]);

  // The pageview of every page, sent at the navigation itself. Plausible's
  // script closes the page being left with this call: it reports that page's
  // scroll depth as the deepest offset reached over the document height it
  // last observed, and its ResizeObserver hands it the next page's height at
  // the first layout. A layout effect runs before that layout, so the depth
  // is still measured against the page it belongs to. It also runs after the
  // children's layout effects, so the address is the one the page settled on
  // (`useUrlSync`) and the chat's admin mute is already on (`AgentChatPage`).
  //
  // Back and forward keep the browser's own scroll restoration, which some
  // browsers apply before this effect and Chrome after it, so the offset here
  // may still be the one of the page being left. The pageview is therefore
  // sent from the top, and the offset put back in the same breath: nothing is
  // painted in between, the visitor sees no difference, and the script learns
  // the page's real offset from the scroll event that follows.
  useLayoutEffect(() => {
    const offset = navigationType === 'POP' ? window.scrollY : 0;
    if (offset > 0) window.scrollTo(0, 0);
    trackPageview();
    if (offset > 0) window.scrollTo(0, offset);
  }, [pathname, search, navigationType, trackPageview]);

  // Always reset horizontal scroll on route change. If a previous page leaked
  // page-level horizontal scroll (e.g. a wide table on mobile), the offset
  // otherwise persists into the next page and clips its left edge.
  useEffect(() => {
    window.scrollTo({ left: 0, top: window.scrollY });
  }, [pathname]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100svh',
        bgcolor: 'var(--bg-page)',
      }}
    >
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
        <Footer />
      </Container>

      {siteFeedback && <FeedbackWidget />}
    </Box>
  );
}
