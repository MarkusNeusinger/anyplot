import { useEffect, useState } from 'react';

import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import Fab from '@mui/material/Fab';

// Direct path, not the 'src/hooks' barrel: page tests mock the barrel with a
// bare factory, which would drop this hook.
import { useFooterLift } from 'src/hooks/useFooterLift';
import { colors, FAB_SLOT_LEFT, semanticColors } from 'src/theme';

const SCROLL_TOP_THRESHOLD = 300;

/**
 * Floating scroll-to-top button for long pages (/plots, /specs). It fades in
 * after the first 300px of scroll and parks in the slot left of the global
 * FeedbackWidget FAB, riding the same footer lift so the two stay one row.
 */
export function ScrollToTopFab() {
  const [visible, setVisible] = useState(false);
  const liftTransform = useFooterLift();

  useEffect(() => {
    const handleScroll = () => {
      setVisible(window.scrollY > SCROLL_TOP_THRESHOLD);
    };
    // Run once on mount so a restored scroll position shows the button at once.
    handleScroll();
    // passive: true — handler doesn't preventDefault.
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <Fab
      size="small"
      aria-label="Scroll to top"
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      sx={{
        position: 'fixed',
        bottom: FAB_SLOT_LEFT.bottom,
        right: FAB_SLOT_LEFT.right,
        bgcolor: 'var(--bg-surface)',
        color: semanticColors.mutedText,
        opacity: visible ? 1 : 0,
        visibility: visible ? 'visible' : 'hidden',
        transform: liftTransform,
        transition: 'opacity 0.3s, visibility 0.3s, transform 120ms ease-out',
        '&:hover': { bgcolor: 'var(--bg-elevated)', color: colors.primary },
      }}
    >
      <KeyboardArrowUpIcon />
    </Fab>
  );
}
