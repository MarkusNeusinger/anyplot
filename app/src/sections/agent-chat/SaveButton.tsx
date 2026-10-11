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
 * button until a session exists and while anything else is in flight.
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
            cursor: saving ? 'default' : 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          <Box
            component="input"
            type="checkbox"
            checked={includeData}
            disabled={saving}
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
          disabled={disabled || saving}
          aria-label="Save"
          title="save the session as a json file"
          sx={ghostButtonSx}
        >
          {saving ? '.save() …' : '.save()'}
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
