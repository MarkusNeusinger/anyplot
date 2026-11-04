/**
 * Quick feedback on one result version, at the foot of its result card, or
 * with `version` 0 on the chat itself, below the composer, for a session that
 * made no plot (docs/concepts/agent-network.md, "Feedback capture"): one of the site's four
 * reactions, an optional text of at most 500 characters, and
 * `# include data.csv`, ticked by default for an admin, who sends their own
 * test data, and unticked on the public lane, where a consent line under the
 * form says what sending stores (`lane.ts`). `.send()` has the BFF store the
 * version's case in the private case bucket.
 *
 * - Compact since 2026-11-02 (owner: less text): at first only the label and
 *   the reactions show; a click on one unfolds the message box, the data box,
 *   the consent line and `.send()`, so the consent is in view before anything
 *   can be sent. `.cancel()` folds a fresh form back to the reactions, with
 *   none picked, and the focus goes to the first of them.
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
 * - The form and the sent line swap, which removes the focused button. The
 *   focus moves on to `.edit()` after a send or `.cancel()`, and to the picked
 *   reaction after `.edit()`, unless the user has moved it elsewhere in the
 *   meantime. A status region outside the swap stays mounted, so a stored case
 *   is announced to screen readers.
 */

import { useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';

import type { FeedbackInput, FeedbackRecord } from 'src/hooks/useAgentSession';
import { AgentApiError, type FeedbackReaction, MAX_FEEDBACK_CHARS } from 'src/lib/agent';
import { paths } from 'src/routes/paths';
import { FEEDBACK_CONSENT, useAgentLane } from 'src/sections/agent-chat/lane';
import { ERROR_TEXT } from 'src/sections/agent-chat/messages';
import { REACTION_TEXT, REACTIONS } from 'src/sections/agent-chat/reactions';
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

/** Failures only a feedback send meets; any other code reads as the page's turn errors do. */
const FEEDBACK_FAILURE: Record<string, string> = {
  storage: 'the case could not be stored; try again',
  too_large: 'the session is over 32 MB, too large to store as a case',
  upstream: 'the agents service did not answer; try again',
  not_found: 'this version is no longer on the server',
  // The chat's case with `# include data.csv` ticked, before any data was pasted or computed.
  no_data: 'there is no data yet; untick # include data.csv',
  session_expired: 'the session expired',
  too_long: `the text is longer than ${MAX_FEEDBACK_CHARS} characters`,
  invalid: 'the server refused this feedback',
  // The files are in the bucket; the page recorded the case, so `.send()` again replaces it.
  row_missing: 'the case is stored but not yet listed for triage; edit or resend names it',
  // Any body-less 503: an API without a database, or the admin gate not configured.
  unavailable: 'the server is not ready; the case was not stored',
  // The public lane's cap on feedback cases per network and hour (`AGENT_PUBLIC_FEEDBACK_PER_HOUR`).
  rate_limited: 'too much feedback from your network in the last hour; try again later',
  // The public lane's Turnstile check: `.send()` again runs a fresh one, and the form keeps what was typed.
  bot_check_failed: 'the browser check did not go through; send again',
  bot_check_unavailable: 'the browser check is not available right now; send again in a minute',
};

function describeFailure(code: string, ref: string | null): string {
  const text = FEEDBACK_FAILURE[code] ?? ERROR_TEXT[code] ?? `request failed (${code})`;
  return ref ? `${text} · ref ${ref}` : text;
}

export interface ResultFeedbackProps {
  /** The version's number, as the server stored it; 0 is the chat itself. */
  version: number;
  /** The case stored for this version, if any. */
  sent: FeedbackRecord | null;
  /** Store the case; rejects with an `AgentApiError` on failure. */
  onSend: (version: number, input: FeedbackInput) => Promise<void>;
  /**
   * Whether the session holds data to include; false only for the chat's control before any
   * data was pasted or computed, which then sends without data.csv and says why.
   */
  dataAvailable?: boolean;
}

export function ResultFeedback({
  version,
  sent,
  onSend,
  dataAvailable = true,
}: ResultFeedbackProps) {
  // What the control is about, in its labels: a version, or the chat as a whole.
  const subject = version === 0 ? 'this chat' : `version ${version}`;
  const short = version === 0 ? 'this chat' : `v${version}`;
  const [editing, setEditing] = useState(!sent);
  const [reaction, setReaction] = useState<FeedbackReaction | null>(sent?.reaction ?? null);
  const [message, setMessage] = useState(sent?.message ?? '');
  // Ticked by default for an admin, who sends their own test data; unticked on the public lane,
  // where adding the file is the user's explicit choice (`FEEDBACK_CONSENT` says what is stored).
  const lane = useAgentLane();
  const [includeData, setIncludeData] = useState(sent?.includeData ?? lane === 'admin');
  const [sending, setSending] = useState(false);
  const [failure, setFailure] = useState<{ code: string; ref: string | null } | null>(null);
  // What the status region announces; set when a case is stored, cleared by `.edit()`.
  const [announcement, setAnnouncement] = useState('');

  const rootRef = useRef<HTMLDivElement>(null);
  const editRef = useRef<HTMLButtonElement>(null);
  const messageRef = useRef<HTMLTextAreaElement>(null);
  // Where the focus goes once the form and the sent line have swapped.
  const pendingFocus = useRef<'edit' | 'reaction' | null>(null);
  const showingSent = !!sent && !editing;
  // Data that does not exist yet cannot be included, whatever the box said before.
  const withData = includeData && dataAvailable;

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    const target = pendingFocus.current;
    if (!target) return;
    // The swap dropped the focus to the body; a focus the user moved elsewhere stays there.
    const active = document.activeElement;
    if (active && active !== document.body && !rootRef.current?.contains(active)) {
      pendingFocus.current = null;
      return;
    }
    if (target === 'edit' && showingSent) {
      pendingFocus.current = null;
      editRef.current?.focus();
    } else if (target === 'reaction' && !showingSent) {
      pendingFocus.current = null;
      const pressed = rootRef.current?.querySelector<HTMLElement>('button[aria-pressed="true"]');
      (pressed ?? messageRef.current)?.focus();
    }
  }, [showingSent]);

  const handleEdit = () => {
    if (sent) {
      setReaction(sent.reaction);
      setMessage(sent.message ?? '');
      setIncludeData(sent.includeData);
    }
    setFailure(null);
    setAnnouncement('');
    pendingFocus.current = 'reaction';
    setEditing(true);
  };

  const handleCancel = () => {
    setFailure(null);
    if (!sent) {
      // A fresh form folds back to the reactions, which stay mounted: the focus moves to the
      // first of them before `.cancel()` goes.
      rootRef.current?.querySelector<HTMLElement>('[role="group"] button')?.focus();
      setReaction(null);
      return;
    }
    pendingFocus.current = 'edit';
    setEditing(false);
  };

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!reaction || sending) return;
    setSending(true);
    setFailure(null);
    try {
      await onSend(version, { reaction, message, includeData: withData });
      // Stored: the control shows what was sent, which the page recorded on the version.
      if (mounted.current) {
        const label = REACTIONS.find(item => item.value === reaction)?.label ?? reaction;
        setAnnouncement(
          `Feedback sent on ${subject}: ${label}, ${withData ? 'with' : 'without'} data.csv.`
        );
        pendingFocus.current = 'edit';
        setEditing(false);
      }
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

  const sentOption = sent ? REACTIONS.find(item => item.value === sent.reaction) : undefined;
  const sentLine = sent && (
    <Box
      component="section"
      aria-label={`Feedback on ${subject}`}
      sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', columnGap: 1, rowGap: 0.5 }}
    >
      <Box component="span" sx={labelSx}>
        # feedback
      </Box>
      {/* A flex item laid out as plain text, so at phone width it wraps like a sentence. */}
      <Box
        component="span"
        data-testid="result-feedback-sent"
        sx={{ ...labelSx, color: 'var(--ink-soft)', minWidth: 0 }}
      >
        {sentOption && (
          <Box
            component="span"
            aria-hidden
            sx={{
              display: 'inline-flex',
              verticalAlign: 'middle',
              mr: 0.5,
              color: sentOption.color,
            }}
          >
            <sentOption.Filled fontSize="small" />
          </Box>
        )}
        sent · {short}{' '}
        <Box component="span" sx={{ color: 'var(--ink-muted)' }}>
          · {REACTION_TEXT[sent.reaction]}
          {sent.includeData ? ' · with data.csv' : ''}
        </Box>
      </Box>
      <Box
        component="button"
        type="button"
        ref={editRef}
        onClick={handleEdit}
        aria-label={`Edit the feedback on ${subject}`}
        sx={{ ...actionButtonSx, ml: 'auto' }}
      >
        .edit()
      </Box>
    </Box>
  );

  const form = (
    <Box
      component="form"
      aria-label={`Feedback on ${subject}`}
      onSubmit={(event: React.FormEvent) => void handleSend(event)}
      sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}
    >
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.5 }}>
        <Box component="span" sx={{ ...labelSx, mr: 0.5 }}>
          # feedback on {short}
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
      {/* Folded until a reaction is picked: the rest of the form, the consent line with it. */}
      {reaction && (
        <>
          <Box
            component="textarea"
            ref={messageRef}
            aria-label="Feedback message"
            placeholder="optional: what worked, what did not"
            value={message}
            maxLength={MAX_FEEDBACK_CHARS}
            rows={2}
            disabled={sending}
            onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
              setMessage(event.target.value)
            }
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
                aria-label={`Include data.csv in the feedback on ${subject}`}
                checked={withData}
                disabled={sending || !dataAvailable}
                onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                  setIncludeData(event.target.checked)
                }
                sx={{ m: 0, width: 14, height: 14, accentColor: colors.primary, cursor: 'inherit' }}
              />
              {dataAvailable ? '# include data.csv' : '# no data yet'}
            </Box>
            {/* Right-aligned, also on a line of its own at phone width. */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
              <Box component="span" aria-hidden sx={labelSx}>
                {message.length}/{MAX_FEEDBACK_CHARS}
              </Box>
              <Box
                component="button"
                type="button"
                onClick={handleCancel}
                disabled={sending}
                aria-label={
                  sent
                    ? `Cancel the edit of the feedback on ${subject}`
                    : `Cancel the feedback on ${subject}`
                }
                sx={actionButtonSx}
              >
                .cancel()
              </Box>
              <Box
                component="button"
                type="submit"
                disabled={!reaction}
                aria-disabled={sending || undefined}
                aria-label="Send feedback"
                title={
                  reaction
                    ? `store ${version === 0 ? 'this chat' : 'this version'} as a feedback case`
                    : 'pick a reaction first'
                }
                sx={{
                  ...ghostButtonSx,
                  '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
                  '&[aria-disabled="true"]:hover': {
                    color: 'var(--ink)',
                    borderColor: 'var(--rule)',
                  },
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
          {lane === 'public' && (
            <Box sx={{ ...labelSx, fontSize: smallText, lineHeight: 1.5 }}>
              # {FEEDBACK_CONSENT} {/* A new tab: leaving the page would end the session. */}
              <Box
                component="a"
                href={`${paths.legal}#assistant`}
                target="_blank"
                rel="noopener"
                sx={{ color: 'inherit' }}
              >
                legal
              </Box>
            </Box>
          )}
        </>
      )}
      {failureLine}
    </Box>
  );

  return (
    <Box ref={rootRef} data-testid="result-feedback" sx={{ minWidth: 0 }}>
      {/* Outside the swap, so it is mounted before the text that announces a stored case. */}
      <Box role="status" sx={visuallyHiddenSx}>
        {announcement}
      </Box>
      {showingSent ? sentLine : form}
    </Box>
  );
}
