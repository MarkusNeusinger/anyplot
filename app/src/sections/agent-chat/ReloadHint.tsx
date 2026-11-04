/**
 * A reload link after an error a reload fixes: `unreachable` (in production
 * usually an expired Cloudflare Access session, which only a top-level page
 * load can renew) and `session_expired` (the server forgot the session).
 * With `opening`, the page could not open a session at all, so a reload loses
 * nothing: the public lane's bot check (`bot_check_failed`,
 * `bot_check_unavailable`) gets `try again`, which runs a fresh check. Renders
 * nothing for any other code. The user asked for this reload, so it passes the
 * page's leave warning.
 */

import Box from '@mui/material/Box';

import { reloadWithoutWarning } from 'src/hooks/useLeaveWarning';
import { colors } from 'src/theme';

const RELOAD_CODES = new Set(['unreachable', 'session_expired']);
const RETRY_CODES = new Set(['bot_check_failed', 'bot_check_unavailable']);

export function ReloadHint({
  code,
  opening = false,
}: {
  code: string | null | undefined;
  /** The session never opened: a reload also retries the bot check. */
  opening?: boolean;
}) {
  if (!code) return null;
  const retry = opening && RETRY_CODES.has(code);
  if (!retry && !RELOAD_CODES.has(code)) return null;
  const label = retry ? 'try again' : code === 'unreachable' ? 'reload to sign in again' : 'reload';
  return (
    <>
      {' · '}
      <Box
        component="button"
        type="button"
        onClick={() => reloadWithoutWarning()}
        sx={{
          all: 'unset',
          cursor: 'pointer',
          color: colors.primary,
          textDecoration: 'underline',
          textUnderlineOffset: '2px',
          '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
        }}
      >
        {label}
      </Box>
    </>
  );
}
