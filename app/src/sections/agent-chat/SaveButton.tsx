/**
 * `.save()` in the chat header: downloads the session as one JSON file, the
 * feedback case the agents service assembles (the conversation, every version's
 * code, plan, result and images, the data profile, the bindings and the config
 * stamp), to keep or to hand on when something went wrong. `# include data.csv`
 * adds each version's data file; it is on by default, because in phase 1 only
 * admins save their own data (docs/concepts/agent-network.md, "Feedback
 * capture").
 *
 * The button holds its own saving flag and failure line: a save only reads the
 * session, so the session state does not track it. The page disables the
 * button until a session exists and while anything else is in flight; the data
 * box is locked with it, because the page renders the header anew once the
 * session is open, and a choice made before then would silently reset. A save
 * in progress marks the button `aria-disabled` instead of `disabled`, so the
 * browser does not move the keyboard focus away from it. The failure line
 * clears once anything else runs, because it is about an earlier attempt.
 */

import { useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { AgentApiError } from 'src/lib/agent';
import { ERROR_TEXT } from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { ghostButtonSx, labelSx, smallText } from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

/** Failures only a save meets; any other code reads as the page's turn errors do. */
const SAVE_FAILURE: Record<string, string> = {
  too_large: 'the session is over 32 MB, too large for one file',
  // On Cloud Run, a bundle over 32 MB fails on the agents service's side, before the BFF reads it.
  upstream: 'the session did not arrive; it may be over 32 MB',
  not_found: 'this session is no longer on the server',
  session_expired: 'the session expired',
};

function describeSaveFailure(code: string, ref: string | null): string {
  const text = SAVE_FAILURE[code] ?? ERROR_TEXT[code] ?? `request failed (${code})`;
  return ref ? `${text} · ref ${ref}` : text;
}

export interface SaveButtonProps {
  /** No session yet, or something else is in flight. */
  disabled: boolean;
  /** Fetch and download the bundle; rejects with an `AgentApiError` on failure. */
  onSave: (includeData: boolean) => Promise<void>;
}

export function SaveButton({ disabled, onSave }: SaveButtonProps) {
  const [includeData, setIncludeData] = useState(true);
  const [saving, setSaving] = useState(false);
  const [failure, setFailure] = useState<{ code: string; ref: string | null } | null>(null);
  // Something else started (a turn, a parse, a render): the failure line is stale.
  const [wasDisabled, setWasDisabled] = useState(disabled);
  if (disabled !== wasDisabled) {
    setWasDisabled(disabled);
    if (disabled) setFailure(null);
  }
  const locked = disabled || saving;
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const handleSave = async () => {
    if (disabled || saving) return;
    setSaving(true);
    setFailure(null);
    try {
      await onSave(includeData);
    } catch (err) {
      if (mounted.current) {
        setFailure(
          err instanceof AgentApiError
            ? { code: err.code, ref: err.ref }
            : { code: 'network', ref: null }
        );
      }
    } finally {
      if (mounted.current) setSaving(false);
    }
  };

  return (
    <Box
      data-testid="session-save"
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', ml: 'auto' }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', columnGap: 1.5 }}>
        <Box
          component="label"
          sx={{
            ...labelSx,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 0.75,
            minHeight: 32,
            cursor: locked ? 'default' : 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          <Box
            component="input"
            type="checkbox"
            checked={includeData}
            disabled={locked}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              setIncludeData(event.target.checked)
            }
            sx={{ m: 0, width: 14, height: 14, accentColor: colors.primary, cursor: 'inherit' }}
          />
          # include data.csv
        </Box>
        <Box
          component="button"
          type="button"
          onClick={() => void handleSave()}
          disabled={disabled}
          aria-disabled={saving || undefined}
          aria-label="Save"
          title="save the session as a json file"
          sx={{
            ...ghostButtonSx,
            '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
            '&[aria-disabled="true"]:hover': { color: 'var(--ink)', borderColor: 'var(--rule)' },
          }}
        >
          {/* As wide as the longest label, so the header does not jump while saving. */}
          <Box
            component="span"
            sx={{ display: 'inline-block', minWidth: '9ch', textAlign: 'center' }}
          >
            {saving ? '.save() …' : '.save()'}
          </Box>
        </Box>
      </Box>
      {failure && (
        <Box
          role="alert"
          sx={{
            fontFamily: typography.mono,
            fontSize: smallText,
            color: colors.error,
            maxWidth: 360,
            textAlign: 'right',
            overflowWrap: 'anywhere',
            mt: 0.5,
          }}
        >
          {describeSaveFailure(failure.code, failure.ref)}
          <ReloadHint code={failure.code} />
        </Box>
      )}
    </Box>
  );
}
