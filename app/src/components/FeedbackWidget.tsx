import { useEffect, useMemo, useRef, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Fab from '@mui/material/Fab';
import IconButton from '@mui/material/IconButton';
import Popover from '@mui/material/Popover';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import FeedbackIcon from '@mui/icons-material/Feedback';
import CloseIcon from '@mui/icons-material/Close';
import { API_URL } from '../constants';
import { useAnalytics } from '../hooks';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { RESERVED_TOP_LEVEL } from '../utils/paths';

const MAX_MESSAGE_LENGTH = 500;
const SESSION_KEY = 'anyplot_feedback_session';

const REACTIONS = [
  { value: 'thumbs_up', label: 'thumbs up', glyph: '👍' },
  { value: 'thumbs_down', label: 'thumbs down', glyph: '👎' },
  { value: 'bug', label: 'bug', glyph: '🐛' },
  { value: 'idea', label: 'idea', glyph: '💡' },
  { value: 'heart', label: 'love it', glyph: '❤️' },
] as const;

type Reaction = (typeof REACTIONS)[number]['value'];

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
 * Floating quick-feedback widget (issue #5662). Always-visible FAB in the
 * bottom-right corner opens a small popover with a free-text field, an optional
 * reaction, and an optional email. Submissions POST to `/feedback`. No GitHub
 * account or page navigation needed — the bar is "type one sentence and send."
 */
export function FeedbackWidget() {
  const { trackEvent } = useAnalytics();
  const anchorRef = useRef<HTMLButtonElement | null>(null);
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [reaction, setReaction] = useState<Reaction | null>(null);
  const [email, setEmail] = useState('');
  // Honeypot — kept in state but rendered off-screen so real users never see it.
  const [website, setWebsite] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [sessionId, setSessionId] = useLocalStorage<string>(SESSION_KEY, '');

  const ensureSessionId = (): string => {
    if (sessionId) return sessionId;
    const fresh = newSessionId();
    setSessionId(fresh);
    return fresh;
  };

  const currentPath = useMemo(
    () => (typeof window !== 'undefined' ? window.location.pathname + window.location.search : ''),
    [open]
  );

  // Auto-close after a successful submission so the FAB returns to its quiet state.
  useEffect(() => {
    if (!submitted) return;
    const id = window.setTimeout(() => {
      setOpen(false);
      setSubmitted(false);
      setMessage('');
      setReaction(null);
      setEmail('');
      setWebsite('');
    }, 1500);
    return () => window.clearTimeout(id);
  }, [submitted]);

  const handleOpen = () => {
    setOpen(true);
    setError(null);
    trackEvent('feedback_opened', { path: currentPath || undefined });
  };

  const handleClose = () => {
    if (submitting) return;
    setOpen(false);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      setError('Please add a short message.');
      return;
    }
    if (trimmed.length > MAX_MESSAGE_LENGTH) {
      setError(`Please keep it under ${MAX_MESSAGE_LENGTH} characters.`);
      return;
    }

    setSubmitting(true);
    setError(null);

    const spec_id = specIdFromPath(window.location.pathname);
    const viewport = `${window.innerWidth}x${window.innerHeight}`;

    try {
      const response = await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          reaction,
          email: email.trim() || null,
          path: currentPath,
          spec_id,
          viewport,
          session_id: ensureSessionId(),
          website,
        }),
      });

      if (!response.ok) {
        throw new Error(`status ${response.status}`);
      }

      trackEvent('feedback_submitted', {
        path: currentPath || undefined,
        reaction: reaction ?? undefined,
        has_email: email.trim() ? 'true' : 'false',
        spec_id,
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
        color="primary"
        onClick={handleOpen}
        aria-label="Open feedback"
        sx={{
          position: 'fixed',
          bottom: { xs: 12, sm: 16 },
          right: { xs: 12, sm: 16 },
          zIndex: 1300,
        }}
      >
        <FeedbackIcon />
      </Fab>

      <Popover
        open={open}
        anchorEl={anchorRef.current}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        transformOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        slotProps={{ paper: { sx: { width: { xs: 'calc(100vw - 24px)', sm: 360 }, maxWidth: 400, p: 2 } } }}
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
              type="email"
              fullWidth
              size="small"
              placeholder="Email (optional, for follow-up)"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              slotProps={{ htmlInput: { maxLength: 255, 'aria-label': 'Email (optional)' } }}
              disabled={submitting}
              sx={{ mb: 1.5 }}
            />

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
              <Button type="submit" variant="contained" size="small" disabled={submitting || !message.trim()}>
                {submitting ? 'Sending…' : 'Send'}
              </Button>
            </Box>
          </Box>
        )}
      </Popover>
    </>
  );
}
