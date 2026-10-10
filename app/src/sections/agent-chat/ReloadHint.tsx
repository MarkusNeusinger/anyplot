/**
 * A reload link after an error a reload fixes: `unreachable` (in production
 * usually an expired Cloudflare Access session, which only a top-level page
 * load can renew) and `session_expired` (the server forgot the session).
 * Renders nothing for any other code.
 */

import Box from '@mui/material/Box';

import { colors } from 'src/theme';

const RELOAD_CODES = new Set(['unreachable', 'session_expired']);

export function ReloadHint({ code }: { code: string | null | undefined }) {
  if (!code || !RELOAD_CODES.has(code)) return null;
  return (
    <>
      {' · '}
      <Box
        component="button"
        type="button"
        onClick={() => window.location.reload()}
        sx={{
          all: 'unset',
          cursor: 'pointer',
          color: colors.primary,
          textDecoration: 'underline',
          textUnderlineOffset: '2px',
          '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
        }}
      >
        {code === 'unreachable' ? 'reload to sign in again' : 'reload'}
      </Box>
    </>
  );
}
