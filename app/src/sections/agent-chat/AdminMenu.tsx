/**
 * The admin menu, the chat's one admin-only element (owner, 2026-11-06: the admin's chat looks
 * and behaves exactly like the visitors' and runs the same code, so the owner never misses what
 * a visitor meets; every admin extra sits behind this one element). It stands at the header
 * row's right end, where the "⋯" menu with `.save()` stood, only in a browser the page detected
 * as an admin's (`useAgentAdmin`), and holds:
 *
 * - the fan-out toggle, `all 15 libraries`: on, the library chip reads `all 15 libraries ▾` and
 *   the composer's create action is `.plot_all()`; a library picked in the chip turns it off;
 * - `.save()`, the session's debugging bundle (`SaveButton`), its data box unticked as the
 *   feedback form's is;
 * - "view as visitor", remembered per tab: the page runs on the public lane exactly as a
 *   visitor's (the public API, the bot check, the public limits), and this menu stays, so the
 *   admin can switch back;
 * - lines a visitor does not get, such as `AGENT_ENABLED` being off;
 * - after an expired admin session, the line that says so, with the link to `/debug`;
 * - in `children`, as further `AdminSection`s the page passes: the running turn's progress grid
 *   (`ProgressTimeline`, also in the visitor's view) and, on the admin lane only, the meters
 *   (`now 2 runs · today 62 %`), which the page reads again as the menu opens (`onOpen`).
 *
 * A popover like the language chip's. It stays mounted while closed, so the data box keeps the
 * user's choice from one save to the next. The button never waits: the switch back from "view as
 * visitor" and the sign-in link stay reachable while a run is in flight, and each control inside
 * waits on its own. A toggle closes the menu, which returns the focus to the button.
 */

import { useId, useState } from 'react';

import Box from '@mui/material/Box';
import Popover from '@mui/material/Popover';

import { paths } from 'src/routes/paths';
import { SaveButton } from 'src/sections/agent-chat/SaveButton';
import { actionButtonSx, headerChipSx, labelSx, smallText } from 'src/sections/agent-chat/styles';
import { proseLinkStyle, typography } from 'src/theme';

/**
 * What the admin's page runs as: the admin lane, the public lane by the admin's choice ("view as
 * visitor"), or the public lane because the admin check failed (an expired admin session).
 */
export type AdminMode = 'admin' | 'visitor' | 'expired';

export interface AdminFanOut {
  /** The libraries the fan-out plots in. */
  libraries: number;
  pressed: boolean;
  /** Something is in flight, or the fan-out's panel is open. */
  disabled: boolean;
  onChange: (pressed: boolean) => void;
}

export interface AdminSave {
  /** No session yet, or something else is in flight. */
  disabled: boolean;
  /** Fetch and download the bundle; rejects with an `AgentApiError` on failure. */
  onSave: (includeData: boolean) => Promise<void>;
}

export interface AdminMenuProps {
  mode: AdminMode;
  /** The code the failed admin check answered with, shown with the expired line. */
  failure?: string | null;
  /** "view as visitor" switched: on runs the page on the public lane. */
  onViewAsVisitor: (on: boolean) => void;
  /** The fan-out toggle, while the admin lane offers it (the server's lists, two libraries or more, a session). */
  fanOut?: AdminFanOut | null;
  /** `.save()`, on the admin lane while there is a session to save. */
  save?: AdminSave | null;
  /** Lines only an admin gets, such as why the session did not open. */
  diagnostics?: readonly string[];
  /** The menu opened: the page reads what its sections show again (the meters). */
  onOpen?: () => void;
  /** The page's admin extras, each an `AdminSection`: the progress grid, the meters. */
  children?: React.ReactNode;
}

/** A toggle in the menu: pressed with an ink border, like the library chip's options. */
const toggleSx = (pressed: boolean) => ({
  ...actionButtonSx,
  border: '1px solid',
  borderColor: pressed ? 'var(--ink-muted)' : 'var(--rule)',
  color: 'var(--ink)',
  bgcolor: pressed ? 'var(--bg-page)' : 'transparent',
  px: 1,
  '&:disabled': { cursor: 'default', opacity: 0.45 },
});

/** One part of the menu under its `# heading`. */
export function AdminSection({
  heading,
  children,
}: {
  heading: string;
  children: React.ReactNode;
}) {
  return (
    <Box component="section" aria-label={heading}>
      <Box aria-hidden sx={{ ...labelSx, mb: 0.75 }}>
        # {heading}
      </Box>
      {children}
    </Box>
  );
}

/**
 * The admin meters (kit 5 option C): the runs in flight now, from the lane's `/status`, and the
 * share of the day budget spent, from `/budget` (`budgetShare`, the debug page's share too):
 * `now 2 runs · today 62 %`, with the share as a small bar beside it. `null` reads `—`: not
 * read yet, or the read failed. Counts only; the admin lane only.
 */
export function AdminMeters({ runs, share }: { runs: number | null; share: number | null }) {
  const now = runs === null ? 'now —' : `now ${runs} run${runs === 1 ? '' : 's'}`;
  const today = share === null ? 'today —' : `today ${share} %`;
  return (
    <Box
      data-testid="admin-meters"
      sx={{
        fontFamily: typography.mono,
        fontSize: smallText,
        color: 'var(--ink)',
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 1,
      }}
    >
      <span>{`${now} · ${today}`}</span>
      {share !== null && (
        <Box
          component="span"
          aria-hidden
          sx={{ width: 96, height: 6, bgcolor: 'var(--rule)', display: 'inline-flex' }}
        >
          <Box
            component="span"
            sx={{ width: `${Math.min(share, 100)}%`, bgcolor: 'var(--ink-soft)' }}
          />
        </Box>
      )}
    </Box>
  );
}

const LABEL: Record<AdminMode, string> = {
  admin: 'admin',
  visitor: 'admin · as visitor',
  expired: 'admin · expired',
};

export function AdminMenu({
  mode,
  failure = null,
  onViewAsVisitor,
  fanOut = null,
  save = null,
  diagnostics = [],
  onOpen,
  children,
}: AdminMenuProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const popoverId = useId();
  const open = anchor !== null;
  const close = () => setAnchor(null);

  // Two elements and nothing around them, both marked `admin-menu…`: the button at the header
  // row's end and the popover in its portal. The parity test leaves out exactly these
  // (AgentChatPage.parity.test.tsx), so nothing else of the page may differ for an admin.
  return (
    <>
      <Box
        component="button"
        type="button"
        data-testid="admin-menu"
        onClick={(event: React.MouseEvent<HTMLElement>) => {
          setAnchor(event.currentTarget);
          onOpen?.();
        }}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? popoverId : undefined}
        title="admin only · the fan-out, .save(), the visitor's view, the progress grid and the meters"
        sx={{ ...headerChipSx, ml: 'auto' }}
      >
        {LABEL[mode]}
        <Box component="span" aria-hidden sx={{ color: 'var(--ink-soft)' }}>
          &nbsp;▾
        </Box>
      </Box>
      <Popover
        data-testid="admin-menu-panel"
        id={popoverId}
        open={open}
        anchorEl={anchor}
        onClose={close}
        keepMounted
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{
          paper: {
            role: 'dialog',
            'aria-label': 'Admin',
            sx: {
              width: { xs: 'calc(100vw - 32px)', sm: 360 },
              p: 1.5,
              mt: 0.5,
              display: 'flex',
              flexDirection: 'column',
              gap: 1.75,
            },
          },
        }}
      >
        {mode === 'expired' ? (
          <AdminSection heading="admin session expired">
            <Box
              data-testid="admin-expired"
              sx={{ fontFamily: typography.mono, fontSize: smallText, color: 'var(--ink)' }}
            >
              the chat runs as a visitor&apos;s. sign in again on{' '}
              {/* A new tab, which Cloudflare Access intercepts: leaving would end the session. */}
              <Box
                component="a"
                href={paths.debug}
                target="_blank"
                rel="noopener"
                sx={proseLinkStyle}
              >
                /debug
              </Box>
              , then reload this page.
            </Box>
            {failure && <Box sx={{ ...labelSx, mt: 0.5 }}># the check answered {failure}</Box>}
          </AdminSection>
        ) : (
          <>
            {fanOut && (
              <AdminSection heading="plot in every library at once">
                <Box
                  component="button"
                  type="button"
                  aria-pressed={fanOut.pressed}
                  disabled={fanOut.disabled}
                  onClick={() => {
                    close();
                    fanOut.onChange(!fanOut.pressed);
                  }}
                  sx={toggleSx(fanOut.pressed)}
                >
                  all {fanOut.libraries} libraries
                </Box>
              </AdminSection>
            )}
            {save && (
              <AdminSection heading="save the session as a json file">
                {/* Closed counts as disabled for the button: its failure line from an earlier attempt goes. */}
                <SaveButton
                  disabled={save.disabled || !open}
                  onSave={save.onSave}
                  onSaved={close}
                />
              </AdminSection>
            )}
            <AdminSection heading="the visitor's view: public API, bot check, public limits">
              <Box
                component="button"
                type="button"
                aria-pressed={mode === 'visitor'}
                onClick={() => {
                  close();
                  onViewAsVisitor(mode !== 'visitor');
                }}
                sx={toggleSx(mode === 'visitor')}
              >
                view as visitor
              </Box>
            </AdminSection>
            {diagnostics.length > 0 && (
              <AdminSection heading="diagnostics">
                {diagnostics.map(line => (
                  <Box
                    key={line}
                    sx={{ fontFamily: typography.mono, fontSize: smallText, color: 'var(--ink)' }}
                  >
                    {line}
                  </Box>
                ))}
              </AdminSection>
            )}
          </>
        )}
        {children}
      </Popover>
    </>
  );
}
