/**
 * Quick feedback on one result version, at the foot of its result card
 * (docs/concepts/agent-network.md, "Feedback capture"): one of the site's four
 * reactions, an optional text of at most 500 characters, and
 * `# include data.csv`, ticked by default because in phase 1 only admins send
 * their own data. `.send()` has the BFF store the version's case in the
 * private case bucket.
 *
 * - One case per version: once stored, the control shows `sent · v<n>` with
 *   the reaction, and `.edit()` opens the form again with what was sent; the
 *   next `.send()` stores a new case that replaces it. The record lives on the
 *   version in the session state, so it survives the card collapsing.
 * - Sending never blocks the flow: the control is never disabled by a turn or
 *   a render in flight, and nothing else waits for it. While a send runs its
 *   own inputs are locked and `.send()` is `aria-disabled` (not `disabled`, so
 *   the keyboard focus stays on it).
 * - A failure shows a line with its code's meaning and the request id; the
 *   next attempt clears it.
 */

import { type ComponentType, useEffect, useRef, useState } from 'react';

import BugReportIcon from '@mui/icons-material/BugReport';
import BugReportOutlinedIcon from '@mui/icons-material/BugReportOutlined';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbDownOutlinedIcon from '@mui/icons-material/ThumbDownOutlined';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbUpOutlinedIcon from '@mui/icons-material/ThumbUpOutlined';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';

import type { FeedbackInput, FeedbackRecord } from 'src/hooks/useAgentSession';
import { AgentApiError, type FeedbackReaction, MAX_FEEDBACK_CHARS } from 'src/lib/agent';
import { ERROR_TEXT } from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import {
  actionButtonSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

interface ReactionOption {
  value: FeedbackReaction;
  /** The accessible name, in words. */
  label: string;
  /** The tooltip, a method call like the plot page's `.like()`. */
  verb: string;
  color: string;
  Outlined: ComponentType<{ fontSize?: 'small' }>;
  Filled: ComponentType<{ fontSize?: 'small' }>;
}

/** The site feedback's reaction set, in the order of the plot page and the feedback widget. */
const REACTIONS: readonly ReactionOption[] = [
  {
    value: 'thumbs_up',
    label: 'Thumbs up',
    verb: '.like()',
    color: colors.primary,
    Outlined: ThumbUpOutlinedIcon,
    Filled: ThumbUpIcon,
  },
  {
    value: 'thumbs_down',
    label: 'Thumbs down',
    verb: '.dislike()',
    color: colors.error,
    Outlined: ThumbDownOutlinedIcon,
    Filled: ThumbDownIcon,
  },
  {
    value: 'idea',
    label: 'Idea',
    verb: '.idea()',
    color: colors.accent,
    Outlined: LightbulbOutlinedIcon,
    Filled: LightbulbIcon,
  },
  {
    value: 'bug',
    label: 'Bug',
    verb: '.bug()',
    color: colors.error,
    Outlined: BugReportOutlinedIcon,
    Filled: BugReportIcon,
  },
];

const REACTION_TEXT: Record<FeedbackReaction, string> = {
  thumbs_up: 'thumbs up',
  thumbs_down: 'thumbs down',
  idea: 'idea',
  bug: 'bug',
};

/** Failures only a feedback send meets; any other code reads as the page's turn errors do. */
const FEEDBACK_FAILURE: Record<string, string> = {
  storage: 'the case could not be stored; try again',
  too_large: 'the session is over 32 MB, too large to store as a case',
  upstream: 'the agents service did not answer; try again',
  not_found: 'this version is no longer on the server',
  session_expired: 'the session expired',
  too_long: `the text is longer than ${MAX_FEEDBACK_CHARS} characters`,
  invalid: 'the server refused this feedback',
};

function describeFailure(code: string, ref: string | null): string {
  const text = FEEDBACK_FAILURE[code] ?? ERROR_TEXT[code] ?? `request failed (${code})`;
  return ref ? `${text} · ref ${ref}` : text;
}

export interface ResultFeedbackProps {
  /** The version's number, as the server stored it. */
  version: number;
  /** The case stored for this version, if any. */
  sent: FeedbackRecord | null;
  /** Store the case; rejects with an `AgentApiError` on failure. */
  onSend: (version: number, input: FeedbackInput) => Promise<void>;
}

export function ResultFeedback({ version, sent, onSend }: ResultFeedbackProps) {
  const [editing, setEditing] = useState(!sent);
  const [reaction, setReaction] = useState<FeedbackReaction | null>(sent?.reaction ?? null);
  const [message, setMessage] = useState(sent?.message ?? '');
  const [includeData, setIncludeData] = useState(sent?.includeData ?? true);
  const [sending, setSending] = useState(false);
  const [failure, setFailure] = useState<{ code: string; ref: string | null } | null>(null);

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const handleEdit = () => {
    if (sent) {
      setReaction(sent.reaction);
      setMessage(sent.message ?? '');
      setIncludeData(sent.includeData);
    }
    setFailure(null);
    setEditing(true);
  };

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!reaction || sending) return;
    setSending(true);
    setFailure(null);
    try {
      await onSend(version, { reaction, message, includeData });
      // Stored: the control shows what was sent, which the page recorded on the version.
      if (mounted.current) setEditing(false);
    } catch (err) {
      if (mounted.current) {
        setFailure(
          err instanceof AgentApiError
            ? { code: err.code, ref: err.ref }
            : { code: 'network', ref: null }
        );
      }
    } finally {
      if (mounted.current) setSending(false);
    }
  };

  const failureLine = failure && (
    <Box
      role="alert"
      sx={{
        fontFamily: typography.mono,
        fontSize: smallText,
        color: colors.error,
        overflowWrap: 'anywhere',
      }}
    >
      {describeFailure(failure.code, failure.ref)}
      <ReloadHint code={failure.code} />
    </Box>
  );

  if (sent && !editing) {
    const option = REACTIONS.find(item => item.value === sent.reaction);
    return (
      <Box
        component="section"
        aria-label={`Feedback on version ${version}`}
        data-testid="result-feedback"
        sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', columnGap: 1, rowGap: 0.5 }}
      >
        <Box component="span" sx={labelSx}>
          # feedback
        </Box>
        <Box
          component="span"
          role="status"
          sx={{
            ...labelSx,
            color: 'var(--ink-soft)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 0.5,
          }}
        >
          {option && (
            <Box component="span" aria-hidden sx={{ display: 'inline-flex', color: option.color }}>
              <option.Filled fontSize="small" />
            </Box>
          )}
          sent · v{version}{' '}
          <Box component="span" sx={{ color: 'var(--ink-muted)' }}>
            · {REACTION_TEXT[sent.reaction]}
            {sent.includeData ? ' · with data.csv' : ''}
          </Box>
        </Box>
        <Box
          component="button"
          type="button"
          onClick={handleEdit}
          aria-label={`Edit the feedback on version ${version}`}
          sx={{ ...actionButtonSx, ml: 'auto' }}
        >
          .edit()
        </Box>
      </Box>
    );
  }

  return (
    <Box
      component="form"
      aria-label={`Feedback on version ${version}`}
      data-testid="result-feedback"
      onSubmit={(event: React.FormEvent) => void handleSend(event)}
      sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}
    >
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.5 }}>
        <Box component="span" sx={{ ...labelSx, mr: 0.5 }}>
          # feedback on v{version}
        </Box>
        <Box role="group" aria-label="Reaction" sx={{ display: 'flex', gap: 0.25 }}>
          {REACTIONS.map(option => {
            const active = reaction === option.value;
            const Icon = active ? option.Filled : option.Outlined;
            return (
              <Tooltip key={option.value} title={option.verb} disableFocusListener>
                <span style={{ display: 'inline-flex' }}>
                  <IconButton
                    aria-label={option.label}
                    aria-pressed={active}
                    disabled={sending}
                    onClick={() => setReaction(option.value)}
                    size="small"
                    sx={{
                      color: active ? option.color : 'var(--ink-soft)',
                      border: '1px solid',
                      borderColor: active ? option.color : 'transparent',
                      '&:hover': { color: option.color, bgcolor: 'var(--bg-elevated)' },
                      '&:focus-visible': {
                        outline: `2px solid ${colors.primary}`,
                        outlineOffset: 1,
                      },
                    }}
                  >
                    <Icon fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
            );
          })}
        </Box>
      </Box>
      <Box
        component="textarea"
        aria-label="Feedback message"
        placeholder="optional: what worked, what did not"
        value={message}
        maxLength={MAX_FEEDBACK_CHARS}
        rows={2}
        disabled={sending}
        onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => setMessage(event.target.value)}
        sx={{ ...nativeControlSx, width: '100%', boxSizing: 'border-box', resize: 'vertical' }}
      />
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          columnGap: 1.5,
          rowGap: 0.5,
        }}
      >
        <Box
          component="label"
          sx={{
            ...labelSx,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 0.75,
            minHeight: 32,
            cursor: sending ? 'default' : 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          <Box
            component="input"
            type="checkbox"
            checked={includeData}
            disabled={sending}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              setIncludeData(event.target.checked)
            }
            sx={{ m: 0, width: 14, height: 14, accentColor: colors.primary, cursor: 'inherit' }}
          />
          # include data.csv
        </Box>
        {/* Right-aligned, also on a line of its own at phone width. */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          <Box component="span" aria-hidden sx={labelSx}>
            {message.length}/{MAX_FEEDBACK_CHARS}
          </Box>
          {sent && (
            <Box
              component="button"
              type="button"
              onClick={() => {
                setFailure(null);
                setEditing(false);
              }}
              disabled={sending}
              sx={actionButtonSx}
            >
              .cancel()
            </Box>
          )}
          <Box
            component="button"
            type="submit"
            disabled={!reaction}
            aria-disabled={sending || undefined}
            aria-label="Send feedback"
            title={reaction ? 'store this version as a feedback case' : 'pick a reaction first'}
            sx={{
              ...ghostButtonSx,
              '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
              '&[aria-disabled="true"]:hover': { color: 'var(--ink)', borderColor: 'var(--rule)' },
            }}
          >
            {/* As wide as the longest label, so the row does not jump while sending. */}
            <Box
              component="span"
              sx={{ display: 'inline-block', minWidth: '9ch', textAlign: 'center' }}
            >
              {sending ? '.send() …' : '.send()'}
            </Box>
          </Box>
        </Box>
      </Box>
      {failureLine}
    </Box>
  );
}
