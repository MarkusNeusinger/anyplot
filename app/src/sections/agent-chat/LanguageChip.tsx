/**
 * The session language chip in the chat header, next to the library pills:
 * `lang: en` until something sets it, `lang: de · detected` after the
 * session's first typed message, `lang: de · chosen` after a choice here or a
 * request in the chat ("labels in English"). The session language is the
 * language of the assistant's replies and of every text in the plot; code,
 * comments and column names stay as they are.
 *
 * A click opens a popover with the ten common languages and a free-text field
 * for any other, in Latin letters (`LANGUAGE_PATTERN`, the server's pattern;
 * the field trims first, because the server matches the value as sent). A
 * choice closes the popover, which returns the focus to the chip, and calls
 * `onSet`; the chip then shows the server's answer, never the typed text
 * (`English` comes back as `en`). A popover rather than a menu: a menu's
 * typeahead takes the letters typed into the field.
 *
 * Like `.save()`, the chip holds its own pending flag and failure line, and is
 * marked `aria-disabled` rather than `disabled` during its own call, so the
 * keyboard focus stays on it. The page disables it until the session is open
 * (the header renders anew then) and while anything else is in flight, which
 * the server would refuse with `409 run_active`; that also closes an open
 * popover and clears a stale failure line.
 */

import { useEffect, useId, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Popover from '@mui/material/Popover';

import { AgentApiError, LANGUAGE_PATTERN, type PlotLanguage } from 'src/lib/agent';
import { COMMON_LANGUAGES } from 'src/sections/agent-chat/languages';
import { describeLanguageFailure } from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import {
  actionButtonSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  smallText,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

/** The server's longest language value; the field stops there. */
const MAX_LANGUAGE_CHARS = 40;

export interface LanguageChipProps {
  /** The session language as the server last named it. */
  value: PlotLanguage;
  /** No session yet, or something else is in flight. */
  disabled: boolean;
  /** Set the session language; rejects with an `AgentApiError` on failure. */
  onSet: (language: string) => Promise<void>;
}

const sameCode = (value: string, code: string) => value.toLowerCase() === code;

export function LanguageChip({ value, disabled, onSet }: LanguageChipProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [draft, setDraft] = useState('');
  const [hint, setHint] = useState(false);
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<{ code: string; ref: string | null } | null>(null);
  // Something else started (a turn, a parse, a render): close the popover, and
  // the failure line, which is about an earlier attempt, goes.
  const [wasDisabled, setWasDisabled] = useState(disabled);
  if (disabled !== wasDisabled) {
    setWasDisabled(disabled);
    if (disabled) {
      setFailure(null);
      setAnchor(null);
    }
  }
  // One announcement per change of the value, whatever set it; none on mount.
  const [shown, setShown] = useState(value);
  const [announcement, setAnnouncement] = useState('');
  if (shown.language !== value.language || shown.source !== value.source) {
    setShown(value);
    setAnnouncement(`plot language: ${value.language}`);
  }
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const hintId = useId();
  const popoverId = useId();
  const open = anchor !== null;

  const close = () => {
    setAnchor(null);
    setHint(false);
  };

  const choose = async (language: string) => {
    close();
    setDraft('');
    if (pending) return;
    setPending(true);
    setFailure(null);
    try {
      await onSet(language);
    } catch (err) {
      if (mounted.current) {
        setFailure(
          err instanceof AgentApiError
            ? { code: err.code, ref: err.ref }
            : { code: 'network', ref: null }
        );
      }
    } finally {
      if (mounted.current) setPending(false);
    }
  };

  const pick = (code: string) => {
    // The same language, already final: nothing to ask the server.
    if (value.source === 'chosen' && sameCode(value.language, code)) {
      close();
      return;
    }
    void choose(code);
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const language = draft.trim();
    if (!LANGUAGE_PATTERN.test(language)) {
      setHint(true);
      return;
    }
    void choose(language);
  };

  const locked = disabled && !pending;
  const chosen = value.source === 'chosen';
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', minWidth: 0 }}>
      <Box
        component="button"
        type="button"
        data-testid="language-chip"
        onClick={(event: React.MouseEvent<HTMLElement>) => {
          if (!pending) setAnchor(event.currentTarget);
        }}
        disabled={locked}
        aria-disabled={pending || undefined}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? popoverId : undefined}
        aria-label={`Plot language: ${value.language}, ${value.source}. Change`}
        title={`language of the plot's text and the replies: ${value.language}`}
        sx={{
          ...actionButtonSx,
          display: 'inline-flex',
          alignItems: 'baseline',
          maxWidth: '26ch',
          border: '1px solid',
          borderColor: chosen ? 'var(--ink-muted)' : 'var(--rule)',
          color: value.source === 'default' ? 'var(--ink-soft)' : 'var(--ink)',
          bgcolor: chosen ? 'var(--bg-elevated)' : 'transparent',
          '&:disabled': { opacity: 0.45, cursor: 'default' },
          '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
        }}
      >
        <Box component="span" sx={{ flexShrink: 0 }}>
          lang:&nbsp;
        </Box>
        <Box
          component="span"
          sx={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
        >
          {value.language}
        </Box>
        {value.source !== 'default' && (
          <Box component="span" sx={{ color: 'var(--ink-muted)', flexShrink: 0 }}>
            &nbsp;· {value.source}
          </Box>
        )}
        {pending && (
          <Box component="span" sx={{ flexShrink: 0 }}>
            &nbsp;…
          </Box>
        )}
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
          {describeLanguageFailure(failure.code, failure.ref)}
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
            'aria-label': 'Plot language',
            sx: { width: { xs: 'calc(100vw - 32px)', sm: 380 }, p: 1.5, mt: 0.5 },
          },
        }}
      >
        <Box sx={{ ...labelSx, mb: 1 }}># language of the plot&apos;s text and the replies</Box>
        <Box
          role="group"
          aria-label="Common languages"
          sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}
        >
          {COMMON_LANGUAGES.map(option => {
            const current = sameCode(value.language, option.code);
            return (
              <Box
                key={option.code}
                component="button"
                type="button"
                aria-pressed={current}
                aria-label={`${option.code} ${option.endonym} (${option.name})`}
                onClick={() => pick(option.code)}
                sx={{
                  ...actionButtonSx,
                  border: '1px solid',
                  borderColor: current ? 'var(--ink-muted)' : 'var(--rule)',
                  color: 'var(--ink)',
                  bgcolor: current ? 'var(--bg-page)' : 'transparent',
                  px: 1,
                }}
              >
                {option.code}
                <Box component="span" sx={{ color: 'var(--ink-muted)', ml: 0.75 }}>
                  {option.endonym}
                </Box>
              </Box>
            );
          })}
        </Box>
        <Box sx={{ ...labelSx, mt: 1.5, mb: 0.75 }}># any other language, in latin letters</Box>
        <Box
          component="form"
          noValidate
          onSubmit={submit}
          sx={{ display: 'flex', gap: 1, alignItems: 'center' }}
        >
          <Box
            component="input"
            type="text"
            value={draft}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              setDraft(event.target.value);
              setHint(false);
            }}
            maxLength={MAX_LANGUAGE_CHARS}
            placeholder="klingon"
            autoComplete="off"
            spellCheck={false}
            aria-label="Other language"
            aria-invalid={hint || undefined}
            aria-describedby={hint ? hintId : undefined}
            sx={{ ...nativeControlSx, bgcolor: 'var(--bg-page)', flex: 1 }}
          />
          <Box
            component="button"
            type="submit"
            disabled={!draft.trim()}
            aria-label="Set language"
            sx={ghostButtonSx}
          >
            .set()
          </Box>
        </Box>
        {hint && (
          <Box id={hintId} role="alert" sx={{ ...labelSx, color: colors.error, mt: 0.75 }}>
            # letters a–z, spaces and hyphens, up to 40
          </Box>
        )}
        <Box sx={{ ...labelSx, mt: 1.5 }}>
          # the next plot version uses it; earlier versions keep their text
        </Box>
      </Popover>
    </Box>
  );
}
