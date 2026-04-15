import { memo, useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ShuffleIcon from '@mui/icons-material/Shuffle';
import { colors, typography, semanticColors } from '../theme';

interface HeaderProps {
  stats?: { specs: number; plots: number; libraries: number } | null;
  onRandom?: (method: 'click' | 'space' | 'doubletap') => void;
}

export const Header = memo(function Header({ stats, onRandom }: HeaderProps) {
  const theme = useTheme();
  const navigate = useNavigate();
  const isXs = useMediaQuery(theme.breakpoints.down('sm'));
  const [tooltipOpen, setTooltipOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const clickCountRef = useRef(0);
  const clickTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
    };
  }, []);

  const handleLogoClick = useCallback(
    (e: React.MouseEvent | React.KeyboardEvent) => {
      e.preventDefault();
      clickCountRef.current += 1;
      if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
      clickTimerRef.current = setTimeout(() => {
        if (clickCountRef.current < 3) {
          navigate('/');
        }
        clickCountRef.current = 0;
      }, 400);
      if (clickCountRef.current >= 3) {
        clickCountRef.current = 0;
        if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
        navigate('/debug');
      }
    },
    [navigate]
  );

  const handleLogoKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        handleLogoClick(e);
      }
    },
    [handleLogoClick]
  );

  const tooltipText = stats
    ? `${stats.plots} plots across ${stats.libraries} libraries`
    : '';

  // Global double-tap handler for mobile (only on whitespace)
  useEffect(() => {
    if (!onRandom) return;
    let lastTap = 0;
    const handleTouchEnd = (e: TouchEvent) => {
      const target = e.target as HTMLElement;
      const interactive = target.closest('a, button, input, textarea, select, [role="button"], [tabindex], .MuiModal-root, .MuiDialog-root, .MuiChip-root, .MuiCard-root');
      if (interactive) return;

      const now = Date.now();
      if (now - lastTap < 300) {
        onRandom('doubletap');
      }
      lastTap = now;
    };
    document.addEventListener('touchend', handleTouchEnd);
    return () => document.removeEventListener('touchend', handleTouchEnd);
  }, [onRandom]);

  return (
    <Box component="header" sx={{
      textAlign: 'center',
      mb: 4,
      minHeight: { xs: '3.5rem', sm: '4.5rem', md: '6rem' },
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
    }}>
      {/* Logo: any.plot() */}
      <Typography
        variant="h2"
        component="h1"
        sx={{
          fontWeight: 700,
          fontFamily: typography.mono,
          mb: { xs: 2, md: 3 },
          letterSpacing: '-0.02em',
          fontSize: { xs: '2rem', sm: '2.75rem', md: '3.75rem' },
        }}
      >
        <Box
          component="span"
          role="link"
          tabIndex={0}
          onClick={handleLogoClick}
          onKeyDown={handleLogoKeyDown}
          sx={{ cursor: 'pointer', userSelect: 'none', '&:focus': { outline: 'none' } }}
        >
          <Box component="span" sx={{ color: colors.gray[800] }}>any</Box>
          <Box component="span" sx={{
            color: colors.primary,
            display: 'inline-block',
            transform: 'scale(1.45)',
            mx: '2px',
          }}>.</Box>
          <Box component="span" sx={{ color: colors.gray[800] }}>plot</Box>
          <Box component="span" sx={{ color: colors.gray[800], fontWeight: 400, opacity: 0.45 }}>()</Box>
        </Box>
        {onRandom && (
          <ShuffleIcon
            tabIndex={0}
            role="button"
            aria-hidden={false}
            aria-label="Random filter"
            onClick={(e) => {
              const el = e.currentTarget as unknown as HTMLElement;
              el.style.animation = 'none';
              void el.getBoundingClientRect();
              el.style.animation = 'shuffle-wiggle 0.8s ease';
              onRandom('click');
            }}
            onKeyDown={(e) => {
              if (e.key === ' ') {
                e.preventDefault();
                const el = e.currentTarget as unknown as HTMLElement;
                el.style.animation = 'none';
                void el.getBoundingClientRect();
                el.style.animation = 'shuffle-wiggle 0.8s ease';
                onRandom('space');
              }
            }}
            sx={{
              color: colors.gray[500],
              cursor: 'pointer',
              fontSize: '0.5em',
              ml: 0.5,
              verticalAlign: 'super',
              '&:hover': { color: colors.primary },
              '&:focus': { outline: 'none', color: colors.primary },
              '@keyframes shuffle-wiggle': {
                '0%': { transform: 'rotate(0deg)' },
                '20%': { transform: 'rotate(-25deg)' },
                '40%': { transform: 'rotate(25deg)' },
                '60%': { transform: 'rotate(-15deg)' },
                '80%': { transform: 'rotate(15deg)' },
                '100%': { transform: 'rotate(0deg)' },
              },
            }}
          />
        )}
      </Typography>

      {/* Tagline */}
      <Typography
        variant="body1"
        sx={{
          maxWidth: 560,
          mx: 'auto',
          lineHeight: 1.8,
          fontFamily: typography.serif,
          fontWeight: 300,
          color: semanticColors.subtleText,
          fontSize: { xs: '0.9375rem', md: '1.125rem' },
        }}
      >
        {isXs ? 'any library. one plot.' : 'a catalogue of scientific plotting.'}
      </Typography>

      {/* Stats line */}
      <Typography
        variant="body1"
        sx={{
          maxWidth: 560,
          mx: 'auto',
          mt: { xs: 1, md: 1.5 },
          lineHeight: 1.8,
          fontFamily: typography.mono,
          color: colors.gray[500],
          fontSize: { xs: '0.75rem', md: '0.8125rem' },
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
        }}
      >
        {stats ? (
          <ClickAwayListener onClickAway={() => { setTooltipOpen(false); setPinned(false); }}>
            <span>
              <Tooltip
                title={tooltipText}
                arrow
                placement="top"
                open={tooltipOpen}
                disableFocusListener
                disableTouchListener
              >
                <Box
                  component="span"
                  onClick={() => {
                    if (pinned) {
                      setPinned(false);
                      setTooltipOpen(false);
                    } else {
                      setPinned(true);
                      setTooltipOpen(true);
                    }
                  }}
                  onMouseEnter={() => setTooltipOpen(true)}
                  onMouseLeave={() => { if (!pinned) setTooltipOpen(false); }}
                  sx={{ cursor: 'pointer', '&:hover': { color: colors.primary } }}
                >
                  {stats.plots} plots · {stats.libraries} libraries
                </Box>
              </Tooltip>
            </span>
          </ClickAwayListener>
        ) : null}
      </Typography>
    </Box>
  );
});
