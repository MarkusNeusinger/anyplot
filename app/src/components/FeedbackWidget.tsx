import { useEffect, useMemo, useRef, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import Fab from '@mui/material/Fab';
import IconButton from '@mui/material/IconButton';
import Popover from '@mui/material/Popover';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import ForumIcon from '@mui/icons-material/ForumOutlined';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutlineOutlined';
import ThumbUpIcon from '@mui/icons-material/ThumbUpOutlined';
import ThumbDownIcon from '@mui/icons-material/ThumbDownOutlined';
import CloseIcon from '@mui/icons-material/Close';
import { API_URL } from '../constants';
import { useAnalytics } from '../hooks';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { RESERVED_TOP_LEVEL } from '../utils/paths';

const MAX_MESSAGE_LENGTH = 500;
const SESSION_KEY = 'anyplot_feedback_session';
const THANKS_TIMEOUT_MS = 1200;

// Floating quick-action buttons sit on the page background so they read as
// chips rather than coloured CTAs — the main FAB stays the only primary mark.
const miniFabSx = {
  width: 40,
  height: 40,
  bgcolor: 'background.default',
  color: 'text.primary',
  opacity: 0.85,
  '&:hover, &:focus-visible': { opacity: 1, bgcolor: 'action.hover' },
} as const;

const REACTIONS = [
  { value: 'thumbs_up', label: 'thumbs up', glyph: '👍' },
  { value: 'thumbs_down', label: 'thumbs down', glyph: '👎' },
  { value: 'idea', label: 'idea', glyph: '💡' },
  { value: 'bug', label: 'bug', glyph: '🪲' },
] as const;

type Reaction = (typeof REACTIONS)[number]['value'];
type Mode = 'closed' | 'quick' | 'full';

function specIdFromPath(pathname: string): string | undefined {
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) return undefined;
  if (RESERVED_TOP_LEVEL.has(segments[0])) return undefined;
  return segments[0];
}

function newSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return `s-${Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')}`;
  }
  // Browser without Web Crypto support (e.g. very old, or insecure context). The
  // session id is an opaque correlation handle, not a credential — a coarse
  // timestamp-derived id is acceptable here, but we never use Math.random().
  return `s-${Date.now().toString(36)}`;
}

/**
 * Floating quick-feedback widget (issue #5662). The FAB opens a small
 * vertical stack of 👍 / 👎 / 💬: the thumbs submit a reaction-only entry
 * (URL liked/disliked) and close immediately; the chat bubble expands the
 * full popover form with free-text, all reactions, and an optional contact.
 */
export function FeedbackWidget() {
  const { trackEvent } = useAnalytics();
  const anchorRef = useRef<HTMLButtonElement | null>(null);
  const [mode, setMode] = useState<Mode>('closed');
  const [thanksVisible, setThanksVisible] = useState(false);
  const [message, setMessage] = useState('');
  const [reaction, setReaction] = useState<Reaction | null>(null);
  const [contact, setContact] = useState('');
  // Honeypot — kept in state but rendered off-screen so real users never see it.
  const [website, setWebsite] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Number of pixels the footer currently overlaps the viewport — used to lift
  // the FAB stack so it cannot drift over the footer's last-line links once the
  // page is fully scrolled. When the footer is offscreen, lift stays at 0 and
  // the FAB sits at its normal corner position.
  const [lift, setLift] = useState(0);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const footer = document.querySelector('footer');
    if (!footer) return;
    let rafId = 0;
    const update = () => {
      // Only narrow mobile viewports actually collide — at MUI's sm breakpoint
      // and above the footer's last link sits well left of the FAB column.
      if (window.innerWidth >= 600) {
        setLift(0);
        return;
      }
      const r = footer.getBoundingClientRect();
      setLift(Math.max(0, window.innerHeight - r.top));
    };
    const onScroll = () => {
      if (rafId) return;
      rafId = window.requestAnimationFrame(() => {
        rafId = 0;
        update();
      });
    };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
    };
  }, []);
  // Default FAB center on xs is 32px from viewport bottom (bottom 12 + half of
  // 40). Once the footer enters far enough to cross that line, lift the stack
  // so the footer's top edge runs exactly through the FAB centre.
  const FAB_CENTER_FROM_BOTTOM_XS = 32;
  const liftTransform =
    lift > FAB_CENTER_FROM_BOTTOM_XS ? `translateY(-${lift - FAB_CENTER_FROM_BOTTOM_XS}px)` : 'none';

  const [sessionId, setSessionId] = useLocalStorage<string>(SESSION_KEY, '');

  const ensureSessionId = (): string => {
    if (sessionId) return sessionId;
    const fresh = newSessionId();
    setSessionId(fresh);
    return fresh;
  };

  const currentPath = useMemo(
    () => (typeof window !== 'undefined' ? window.location.pathname + window.location.search : ''),
    [mode]
  );

  // Auto-reset the full-form thank-you state and clear inputs.
  useEffect(() => {
    if (!submitted) return;
    const id = window.setTimeout(() => {
      setMode('closed');
      setSubmitted(false);
      setMessage('');
      setReaction(null);
      setContact('');
      setWebsite('');
    }, 1500);
    return () => window.clearTimeout(id);
  }, [submitted]);

  // Auto-dismiss the quick-submit "Thanks" toast.
  useEffect(() => {
    if (!thanksVisible) return;
    const id = window.setTimeout(() => setThanksVisible(false), THANKS_TIMEOUT_MS);
    return () => window.clearTimeout(id);
  }, [thanksVisible]);

  const handleFabClick = () => {
    if (mode === 'closed') {
      setMode('quick');
      setError(null);
      trackEvent('feedback_opened', { path: currentPath || undefined });
    } else {
      setMode('closed');
    }
  };

  const handleExpand = () => {
    setMode('full');
  };

  const handleClose = () => {
    if (submitting) return;
    setMode('closed');
    setError(null);
  };

  const handleQuickAway = () => {
    if (mode === 'quick') setMode('closed');
  };

  const buildPayload = (overrides: { message: string | null; reaction: Reaction | null; contact: string | null }) => ({
    message: overrides.message,
    reaction: overrides.reaction,
    contact: overrides.contact,
    path: currentPath,
    spec_id: specIdFromPath(window.location.pathname),
    viewport: `${window.innerWidth}x${window.innerHeight}`,
    session_id: ensureSessionId(),
    website,
  });

  const submitQuickReaction = async (r: Reaction) => {
    // Optimistic close + toast: the FAB returns to its quiet state immediately,
    // so the interaction feels instant even if the network is slow.
    setMode('closed');
    setThanksVisible(true);
    try {
      await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildPayload({ message: null, reaction: r, contact: null })),
      });
      trackEvent('feedback_submitted', {
        path: currentPath || undefined,
        reaction: r,
        has_contact: 'false',
        spec_id: specIdFromPath(window.location.pathname),
        mode: 'quick',
      });
    } catch {
      // The user already saw the toast; we don't undo it. A retried network
      // failure here is acceptable lossage for a one-tap reaction.
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed && !reaction) {
      setError('Please add a message or pick a reaction.');
      return;
    }
    if (trimmed.length > MAX_MESSAGE_LENGTH) {
      setError(`Please keep it under ${MAX_MESSAGE_LENGTH} characters.`);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          buildPayload({ message: trimmed || null, reaction, contact: contact.trim() || null })
        ),
      });

      if (!response.ok) {
        throw new Error(`status ${response.status}`);
      }

      trackEvent('feedback_submitted', {
        path: currentPath || undefined,
        reaction: reaction ?? undefined,
        has_contact: contact.trim() ? 'true' : 'false',
        spec_id: specIdFromPath(window.location.pathname),
        mode: 'full',
      });
      setSubmitted(true);
    } catch {
      setError("Couldn't send — try again in a moment.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Fab
        ref={anchorRef}
        size="medium"
        color="default"
        onClick={handleFabClick}
        aria-label="Open feedback"
        aria-expanded={mode !== 'closed'}
        sx={{
          position: 'fixed',
          bottom: { xs: 12, sm: 16 },
          right: { xs: 12, sm: 16 },
          zIndex: 1300,
          width: { xs: 40, sm: 48 },
          height: { xs: 40, sm: 48 },
          minHeight: { xs: 40, sm: 48 },
          bgcolor: 'background.default',
          color: 'primary.main',
          opacity: { xs: 0.75, sm: 0.85 },
          transform: liftTransform,
          transition: 'transform 120ms ease-out',
          '&:hover, &:focus-visible': { opacity: 1, bgcolor: 'action.hover' },
        }}
      >
        <ForumIcon />
      </Fab>

      {mode === 'quick' && (
        <ClickAwayListener onClickAway={handleQuickAway}>
          <Box
            role="menu"
            aria-label="Quick feedback"
            sx={{
              position: 'fixed',
              right: { xs: 12, sm: 20 },
              bottom: { xs: 60, sm: 72 },
              zIndex: 1301,
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
              alignItems: 'center',
              transform: liftTransform,
            }}
          >
            <Tooltip title="Leave detailed feedback" placement="left">
              <Fab
                size="small"
                color="default"
                onClick={handleExpand}
                aria-label="Open detailed feedback"
                sx={miniFabSx}
              >
                <ChatBubbleOutlineIcon fontSize="small" />
              </Fab>
            </Tooltip>
            <Tooltip title="I don't like this page" placement="left">
              <Fab
                size="small"
                color="default"
                onClick={() => submitQuickReaction('thumbs_down')}
                aria-label="Quick thumbs down"
                sx={miniFabSx}
              >
                <ThumbDownIcon fontSize="small" />
              </Fab>
            </Tooltip>
            <Tooltip title="I like this page" placement="left">
              <Fab
                size="small"
                color="default"
                onClick={() => submitQuickReaction('thumbs_up')}
                aria-label="Quick thumbs up"
                sx={miniFabSx}
              >
                <ThumbUpIcon fontSize="small" />
              </Fab>
            </Tooltip>
          </Box>
        </ClickAwayListener>
      )}

      {thanksVisible && (
        <Box
          role="status"
          aria-live="polite"
          sx={{
            position: 'fixed',
            right: { xs: 60, sm: 76 },
            bottom: { xs: 16, sm: 22 },
            bgcolor: 'background.paper',
            transform: liftTransform,
            color: 'text.primary',
            px: 1.5,
            py: 0.5,
            borderRadius: 1,
            boxShadow: 3,
            fontSize: 13,
            fontWeight: 500,
            zIndex: 1301,
            pointerEvents: 'none',
          }}
        >
          Thanks!
        </Box>
      )}

      <Popover
        open={mode === 'full'}
        anchorEl={anchorRef.current}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        transformOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        slotProps={{ paper: { sx: { width: { xs: 'calc(100vw - 12px)', sm: 360 }, maxWidth: 400, p: 1.5 } } }}
      >
        {submitted ? (
          <Box sx={{ py: 3, textAlign: 'center' }} role="status" aria-live="polite">
            <Box sx={{ fontSize: 28, mb: 1 }}>🙏</Box>
            <Box sx={{ fontWeight: 600 }}>Thanks!</Box>
            <Box sx={{ fontSize: 13, color: 'text.secondary', mt: 0.5 }}>
              We read every note.
            </Box>
          </Box>
        ) : (
          <Box component="form" onSubmit={handleSubmit} noValidate>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Box sx={{ fontWeight: 600 }}>Quick feedback</Box>
              <IconButton size="small" onClick={handleClose} aria-label="Close feedback" disabled={submitting}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>

            <TextField
              autoFocus
              multiline
              minRows={3}
              maxRows={6}
              fullWidth
              placeholder="Typo, weird chart, feature idea…"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              slotProps={{ htmlInput: { maxLength: MAX_MESSAGE_LENGTH, 'aria-label': 'Feedback message' } }}
              disabled={submitting}
              sx={{ mb: 1.5 }}
            />

            <ToggleButtonGroup
              value={reaction}
              exclusive
              onChange={(_, value: Reaction | null) => setReaction(value)}
              size="small"
              aria-label="Reaction"
              sx={{ display: 'flex', flexWrap: 'wrap', mb: 1.5 }}
            >
              {REACTIONS.map((r) => (
                <ToggleButton key={r.value} value={r.value} aria-label={r.label} sx={{ fontSize: 18, px: 1.5 }}>
                  {r.glyph}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>

            <TextField
              fullWidth
              size="small"
              placeholder="Name or email (optional)"
              value={contact}
              onChange={(e) => setContact(e.target.value)}
              slotProps={{ htmlInput: { maxLength: 255, 'aria-label': 'Contact (optional)' } }}
              disabled={submitting}
              sx={{ mb: 1 }}
            />

            <Box
              sx={{
                fontSize: 11,
                color: 'text.secondary',
                mb: 1.5,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
              title={currentPath || undefined}
            >
              Page: {currentPath || '/'}
            </Box>

            {/* Honeypot — real users never see this, bots will fill it and trip the server-side guard. */}
            <Box aria-hidden="true" sx={{ position: 'absolute', left: '-9999px', width: 1, height: 1, overflow: 'hidden' }}>
              <input
                type="text"
                name="website"
                tabIndex={-1}
                autoComplete="off"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
              />
            </Box>

            {error && (
              <Box sx={{ color: 'error.main', fontSize: 13, mb: 1 }} role="alert">
                {error}
              </Box>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ fontSize: 12, color: 'text.secondary' }}>
                {message.length}/{MAX_MESSAGE_LENGTH}
              </Box>
              <Button
                type="submit"
                variant="contained"
                size="small"
                disabled={submitting || (!message.trim() && !reaction)}
              >
                {submitting ? 'Sending…' : 'Send'}
              </Button>
            </Box>
          </Box>
        )}
      </Popover>
    </>
  );
}
