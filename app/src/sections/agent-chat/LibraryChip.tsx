/**
 * The library menu in the chat's header row, before the language chip (since
 * 2026-11-02, in place of a pill per library, up to 16 with `all`): the chip
 * names the library the plot is made in in plain words, `seaborn ▾`, or
 * `all 15 libraries ▾` while the admin's `all` is pressed (`lib: seaborn ·
 * python` until the v4 frame of 2026-11-06); its accessible name starts with
 * the same words and keeps the language, `Library: seaborn, Python. Change`,
 * so a voice command that says what the chip shows finds it. A click opens a
 * popover with the libraries grouped by language (Python, R, Julia,
 * JavaScript), each group in the header's order, and, for the admin, `all
 * libraries` after them. A popover like the language chip's, not a menu: the
 * groups hold buttons that say whether they are pressed, and a library is a
 * link where there is no session to switch.
 *
 * The rules of the pills it replaces stay. The library in use cannot be picked
 * again; while `all` is pressed it can, which only turns `all` off. Another
 * library switches (`onPick`), and a pick also turns `all` off (the page does
 * that). Without a session (`reopen`: ineligible or failed), another library
 * is a link that opens the page anew with its own session, and the library in
 * use stays a disabled button. `all` toggles, in the URL as `&all=1` (the page
 * keeps that). A choice closes the popover, which returns the focus to the chip.
 *
 * Like the language chip, it holds its own pending flag and failure line, and is
 * marked `aria-disabled` rather than `disabled` during its own switch, so the
 * keyboard focus stays on it. The page disables it while anything else is in
 * flight, during a run (the server refuses a switch then) and while the
 * fan-out's panel is open; that also closes an open popover and clears a stale
 * failure line. The target is a library today: the later plot-type switch adds
 * the spec beside it, as the session's (spec, library) pair already has it.
 */

import { useEffect, useId, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Popover from '@mui/material/Popover';

import { LANG_DISPLAY } from 'src/constants';
import { AgentApiError } from 'src/lib/agent';
import { groupByLanguage, languageOf } from 'src/sections/agent-chat/libraryGroups';
import { describeLibraryFailure } from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import {
  actionButtonSx,
  headerChipSx,
  labelSx,
  smallText,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

export interface LibraryChipProps {
  /** The library the session plots in. */
  library: string;
  /** The libraries the page offers, in the header's order. */
  libraries: readonly string[];
  /** The admin's `all` is offered (the lists are the server's, more than one library, a session). */
  offerAll: boolean;
  /** `all` is pressed: the composer's create action plots in every library at once. */
  allPressed: boolean;
  /** No session to switch: another library is a link to this address, which opens the page anew. */
  hrefFor?: (library: string) => string;
  /** Something else is in flight, a run, or the fan-out's panel is open. */
  disabled: boolean;
  /**
   * A library picked: the switch, or, for the library in use while `all` is
   * pressed, `all` off. Rejects with an `AgentApiError` when the switch failed.
   */
  onPick: (library: string) => Promise<void>;
  /** `all` pressed or released. */
  onAllChange: (pressed: boolean) => void;
  /** The chip's button, where the page returns the focus after the fan-out's panel. */
  buttonRef?: React.Ref<HTMLButtonElement>;
}

/** A library or `all` in the popover: pressed with an ink border, like the language chip's options. */
const optionSx = (pressed: boolean) => ({
  ...actionButtonSx,
  border: '1px solid',
  borderColor: pressed ? 'var(--ink-muted)' : 'var(--rule)',
  color: 'var(--ink)',
  bgcolor: pressed ? 'var(--bg-page)' : 'transparent',
  px: 1,
  textDecoration: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  // The library in use cannot be picked again: it reads as the pressed one, not as a dimmed one.
  '&:disabled': { cursor: 'default', opacity: pressed ? 1 : 0.45 },
});

export function LibraryChip({
  library,
  libraries,
  offerAll,
  allPressed,
  hrefFor,
  disabled,
  onPick,
  onAllChange,
  buttonRef,
}: LibraryChipProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<{ code: string; ref: string | null } | null>(null);
  // Something else started (a turn, a parse, the fan-out): close the popover, and the
  // failure line, which is about an earlier attempt, goes.
  const [wasDisabled, setWasDisabled] = useState(disabled);
  if (disabled !== wasDisabled) {
    setWasDisabled(disabled);
    if (disabled) {
      setFailure(null);
      setAnchor(null);
    }
  }
  // One announcement per change of the library or of `all`, whatever changed it; none on mount.
  const current = allPressed ? 'all' : library;
  const [shown, setShown] = useState(current);
  const [announcement, setAnnouncement] = useState('');
  if (shown !== current) {
    setShown(current);
    setAnnouncement(allPressed ? 'library: all libraries' : `library: ${library}`);
  }
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const popoverId = useId();
  const open = anchor !== null;
  const groups = groupByLanguage(libraries);
  const language = languageOf(library);

  const close = () => setAnchor(null);

  const pick = async (next: string) => {
    close();
    if (pending) return;
    setPending(true);
    setFailure(null);
    try {
      await onPick(next);
    } catch (err) {
      if (mounted.current) {
        setFailure(
          err instanceof AgentApiError
            ? { code: err.code, ref: err.shownRef }
            : { code: 'network', ref: null }
        );
      }
    } finally {
      if (mounted.current) setPending(false);
    }
  };

  const toggleAll = () => {
    close();
    onAllChange(!allPressed);
  };

  const locked = disabled && !pending;
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', minWidth: 0 }}>
      <Box
        component="button"
        type="button"
        ref={buttonRef}
        data-testid="library-chip"
        onClick={(event: React.MouseEvent<HTMLElement>) => {
          if (!pending) setAnchor(event.currentTarget);
        }}
        disabled={locked}
        aria-disabled={pending || undefined}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? popoverId : undefined}
        aria-label={
          allPressed
            ? `Library: all ${libraries.length} libraries. Change`
            : `Library: ${library}, ${LANG_DISPLAY[language] ?? language}. Change`
        }
        title="the library the plot is made in · a switch keeps your data and your decisions"
        sx={{ ...headerChipSx, maxWidth: '32ch' }}
      >
        <Box
          component="span"
          sx={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
        >
          {allPressed ? `all ${libraries.length} libraries` : library}
        </Box>
        {pending && (
          <Box component="span" sx={{ flexShrink: 0 }}>
            &nbsp;…
          </Box>
        )}
        <Box component="span" aria-hidden sx={{ color: 'var(--ink-soft)', flexShrink: 0 }}>
          &nbsp;▾
        </Box>
      </Box>
      <Box role="status" sx={visuallyHiddenSx}>
        {announcement}
      </Box>
      {failure && (
        <Box
          role="alert"
          sx={{
            fontFamily: typography.mono,
            fontSize: smallText,
            color: colors.error,
            maxWidth: 360,
            overflowWrap: 'anywhere',
            mt: 0.5,
          }}
        >
          {describeLibraryFailure(failure.code, failure.ref)}
          <ReloadHint code={failure.code} />
        </Box>
      )}
      <Popover
        id={popoverId}
        open={open}
        anchorEl={anchor}
        onClose={close}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        slotProps={{
          paper: {
            role: 'dialog',
            'aria-label': 'Library of the plot',
            sx: { width: { xs: 'calc(100vw - 32px)', sm: 380 }, p: 1.5, mt: 0.5 },
          },
        }}
      >
        <Box sx={{ ...labelSx, mb: 1, lineHeight: 1.6 }}>
          # library of the plot · a switch keeps your data and your decisions
        </Box>
        {groups.map(group => {
          const name = LANG_DISPLAY[group.language] ?? group.language;
          return (
            <Box key={group.language} sx={{ mb: 1 }}>
              <Box aria-hidden sx={{ ...labelSx, mb: 0.5 }}>
                # {group.language}
              </Box>
              <Box
                role="group"
                aria-label={name}
                sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}
              >
                {group.libraries.map(lib => {
                  const inUse = lib === library;
                  // While `all` is pressed the library in use is not the pressed one: picking it turns `all` off.
                  const pressed = inUse && !allPressed;
                  if (!inUse && hrefFor) {
                    return (
                      <Box key={lib} component="a" href={hrefFor(lib)} sx={optionSx(false)}>
                        {lib}
                      </Box>
                    );
                  }
                  return (
                    <Box
                      key={lib}
                      component="button"
                      type="button"
                      aria-pressed={pressed}
                      disabled={pressed || (inUse && !!hrefFor)}
                      onClick={() => void pick(lib)}
                      sx={optionSx(pressed)}
                    >
                      {lib}
                    </Box>
                  );
                })}
              </Box>
            </Box>
          );
        })}
        {offerAll && (
          <Box sx={{ mt: 1.5 }}>
            <Box aria-hidden sx={{ ...labelSx, mb: 0.5 }}>
              # admin · plot in every library at once
            </Box>
            <Box role="group" aria-label="Admin" sx={{ display: 'flex', gap: 0.5 }}>
              <Box
                component="button"
                type="button"
                aria-pressed={allPressed}
                aria-label="All libraries"
                onClick={toggleAll}
                sx={optionSx(allPressed)}
              >
                all libraries
              </Box>
            </Box>
          </Box>
        )}
      </Popover>
    </Box>
  );
}
