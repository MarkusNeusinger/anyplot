import { useEffect, useRef, useState } from 'react';

import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutlineOutlined';
import CloseIcon from '@mui/icons-material/Close';
import ForumIcon from '@mui/icons-material/ForumOutlined';
import ThumbDownIcon from '@mui/icons-material/ThumbDownOutlined';
import ThumbUpIcon from '@mui/icons-material/ThumbUpOutlined';
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

import { useAnalytics } from 'src/hooks';
import { useFooterLift } from 'src/hooks/useFooterLift';
import { useLocalStorage } from 'src/hooks/useLocalStorage';
import { apiPost, endpoints } from 'src/lib/api';
import { specIdFromPath } from 'src/routes/paths';
import { FAB_GAP, FAB_INSET, FAB_SIZE, FAB_SLOT_ABOVE, MINI_FAB_SIZE } from 'src/theme';
import { FEEDBACK_SESSION_KEY, newFeedbackSessionId } from 'src/utils/feedback';

const MAX_MESSAGE_LENGTH = 500;
const THANKS_TIMEOUT_MS = 1200;

// Floating quick-action buttons sit on the page background so they read as
// chips rather than coloured CTAs — the main FAB stays the only primary mark.
const miniFabSx = {
  width: MINI_FAB_SIZE,
  height: MINI_FAB_SIZE,
  bgcolor: 'var(--bg-surface)',
  color: 'var(--ink)',
  opacity: 0.85,
  '&:hover, &:focus-visible': { opacity: 1, bgcolor: 'var(--bg-elevated)' },
} as const;

const REACTIONS = [
  { value: 'thumbs_up', label: 'thumbs up', glyph: '👍' },
  { value: 'thumbs_down', label: 'thumbs down', glyph: '👎' },
  { value: 'idea', label: 'idea', glyph: '💡' },
  { value: 'bug', label: 'bug', glyph: '🪲' },
] as const;

type Reaction = (typeof REACTIONS)[number]['value'];
type Mode = 'closed' | 'quick' | 'full';

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

  // Lifts the FAB stack clear of the footer's links on narrow viewports; the
  // scroll-to-top button beside it applies the same transform.
  const liftTransform = useFooterLift();

  const [sessionId, setSessionId] = useLocalStorage<string>(FEEDBACK_SESSION_KEY, '');

  const ensureSessionId = (): string => {
    if (sessionId) return sessionId;
    const fresh = newFeedbackSessionId();
    setSessionId(fresh);
    return fresh;
  };

  // Read freshly at each call site so client-side navigations (which don't
  // remount the widget) don't poison the next `feedback_opened` track or the
  // submitted `path` field — useMemo with [mode] would only refresh on open,
  // not on the route changes that happened while the widget was closed.
  const getCurrentPath = (): string =>
    typeof window !== 'undefined' ? window.location.pathname + window.location.search : '';

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
      // The toast shares the slot above the FAB with the quick stack.
      setThanksVisible(false);
      trackEvent('feedback_opened', { path: getCurrentPath() || undefined });
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

  const buildPayload = (overrides: {
    message: string | null;
    reaction: Reaction | null;
    contact: string | null;
  }) => ({
    message: overrides.message,
    reaction: overrides.reaction,
    contact: overrides.contact,
    path: getCurrentPath(),
    spec_id: specIdFromPath(window.location.pathname),
    viewport: `${window.innerWidth}x${window.innerHeight}`,
    session_id: ensureSessionId(),
    website,
  });

  const submitQuickReaction = async (r: Reaction) => {
    // Close the FAB immediately so the interaction feels instant, then show the
    // Thanks toast only after the server confirms — otherwise a 429/500 (or a
    // silently dropped spam-filter response) would still flash "Thanks" while
    // the row was never written.
    setMode('closed');
    try {
      await apiPost<unknown>(
        endpoints.feedback,
        buildPayload({ message: null, reaction: r, contact: null })
      );
      setThanksVisible(true);
      trackEvent('feedback_submitted', {
        path: getCurrentPath() || undefined,
        reaction: r,
        has_contact: 'false',
        spec_id: specIdFromPath(window.location.pathname),
        mode: 'quick',
      });
    } catch {
      // Non-2xx or network failure — drop silently. The quick interaction has
      // no error UI surface (we closed the FAB optimistically); the user can retry.
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
      await apiPost<unknown>(
        endpoints.feedback,
        buildPayload({ message: trimmed || null, reaction, contact: contact.trim() || null })
      );

      trackEvent('feedback_submitted', {
        path: getCurrentPath() || undefined,
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
          bottom: FAB_INSET,
          right: FAB_INSET,
          zIndex: 1300,
          width: FAB_SIZE,
          height: FAB_SIZE,
          minHeight: FAB_SIZE,
          bgcolor: 'var(--bg-surface)',
          color: 'primary.main',
          opacity: { xs: 0.75, sm: 0.85 },
          transform: liftTransform,
          transition: 'transform 120ms ease-out',
          '&:hover, &:focus-visible': { opacity: 1, bgcolor: 'var(--bg-elevated)' },
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
              right: FAB_SLOT_ABOVE.right,
              bottom: FAB_SLOT_ABOVE.bottom,
              zIndex: 1301,
              display: 'flex',
              flexDirection: 'column',
              gap: `${FAB_GAP}px`,
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

      {/* Above the FAB, where the tapped 👍/👎 was — the slot left of the FAB
          belongs to the scroll-to-top button. The mode guard covers a POST
          that resolves after the quick stack was reopened into that slot. */}
      {thanksVisible && mode === 'closed' && (
        <Box
          role="status"
          aria-live="polite"
          sx={{
            position: 'fixed',
            right: FAB_INSET,
            bottom: FAB_SLOT_ABOVE.bottom,
            bgcolor: 'var(--bg-elevated)',
            transform: liftTransform,
            color: 'var(--ink)',
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
        slotProps={{
          paper: {
            sx: {
              width: { xs: 'calc(100vw - 12px)', sm: 360 },
              maxWidth: 400,
              p: 1.5,
              bgcolor: 'var(--bg-elevated)',
              color: 'var(--ink)',
              '& .MuiOutlinedInput-root': {
                color: 'var(--ink)',
                '& fieldset': { borderColor: 'var(--rule)' },
                '&:hover fieldset': { borderColor: 'var(--ink-muted)' },
                '&.Mui-focused fieldset': { borderColor: 'primary.main' },
              },
              '& .MuiOutlinedInput-input::placeholder': {
                color: 'var(--ink-muted)',
                opacity: 1,
              },
              '& .MuiToggleButton-root': {
                color: 'var(--ink)',
                borderColor: 'var(--rule)',
                '&.Mui-selected': {
                  bgcolor: 'var(--bg-surface)',
                  '&:hover': { bgcolor: 'var(--bg-surface)' },
                },
              },
            },
          },
        }}
      >
        {submitted ? (
          <Box sx={{ py: 3, textAlign: 'center' }} role="status" aria-live="polite">
            <Box sx={{ fontSize: 28, mb: 1 }}>🙏</Box>
            <Box sx={{ fontWeight: 600 }}>Thanks!</Box>
            <Box sx={{ fontSize: 13, color: 'var(--ink-muted)', mt: 0.5 }}>We read every note.</Box>
          </Box>
        ) : (
          <Box component="form" onSubmit={handleSubmit} noValidate>
            <Box
              sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}
            >
              <Box sx={{ fontWeight: 600 }}>Quick feedback</Box>
              <IconButton
                size="small"
                onClick={handleClose}
                aria-label="Close feedback"
                disabled={submitting}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>

            <TextField
              autoFocus
              multiline
              minRows={3}
              maxRows={6}
              fullWidth
              placeholder="Bug, idea, typo, anything…"
              value={message}
              onChange={e => setMessage(e.target.value)}
              slotProps={{
                htmlInput: { maxLength: MAX_MESSAGE_LENGTH, 'aria-label': 'Feedback message' },
              }}
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
              {REACTIONS.map(r => (
                <ToggleButton
                  key={r.value}
                  value={r.value}
                  aria-label={r.label}
                  sx={{ fontSize: 18, px: 1.5 }}
                >
                  {r.glyph}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>

            <TextField
              fullWidth
              size="small"
              placeholder="Name or email (optional)"
              value={contact}
              onChange={e => setContact(e.target.value)}
              slotProps={{ htmlInput: { maxLength: 255, 'aria-label': 'Contact (optional)' } }}
              disabled={submitting}
              sx={{ mb: 1 }}
            />

            <Box
              sx={{
                fontSize: 11,
                color: 'var(--ink-muted)',
                mb: 1.5,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
              title={getCurrentPath() || undefined}
            >
              Page: {getCurrentPath() || '/'}
            </Box>

            {/* Honeypot — real users never see this, bots will fill it and trip the server-side guard. */}
            <Box
              aria-hidden="true"
              sx={{
                position: 'absolute',
                left: '-9999px',
                width: 1,
                height: 1,
                overflow: 'hidden',
              }}
            >
              <input
                type="text"
                name="website"
                tabIndex={-1}
                autoComplete="off"
                value={website}
                onChange={e => setWebsite(e.target.value)}
              />
            </Box>

            {error && (
              <Box sx={{ color: 'error.main', fontSize: 13, mb: 1 }} role="alert">
                {error}
              </Box>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ fontSize: 12, color: 'var(--ink-muted)' }}>
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
