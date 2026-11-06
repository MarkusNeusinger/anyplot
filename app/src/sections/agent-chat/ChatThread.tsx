/**
 * The chat thread: the user's turns and the page's own (`.example_data()`, `.create_plot()`,
 * `.carry_plot()`), the attachments the user sent and the data card after each (a later
 * paste leaves the card it replaced as a stub of its shape), the assistant's replies, the fixed
 * refusal under a plain label (its code behind the label's ⓘ), errors with their code and
 * request id, and a result card per plot version. Earlier versions stay in the thread,
 * collapsed, each with its own image and code. A lost confirmation adds nothing here: the status
 * line at the chat frame's foot names it. While a turn without pipeline steps waits for its reply, an
 * in-progress line with the site's loader holds the assistant's slot
 * (`pendingReply` in `steps.ts`); the log's own polite live region announces
 * it once, and the reply takes its place. So does a plot run once its card is
 * in, below the card, while the reply to it is written (`writing the reply`).
 *
 * The page's own turns show as the button the user pressed (`.start_over()`, "plot in plotly with
 * your 3 decisions"), never as the action the page sends. The summary of the data after a paste
 * has no button and shows no line of its own: the card says what was sent, and the summary
 * follows it. Its item stays in the state, which the in-progress line reads. The first reply
 * after a card comes into view as it arrives, when the user's focus is in the composer
 * (`followReply`): a tall card would leave it below the fold.
 */

import { type ReactNode, useEffect, useRef } from 'react';

import Box from '@mui/material/Box';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import {
  type AgentSessionState,
  type ChatItem,
  type FeedbackInput,
  sessionBusy,
} from 'src/hooks/useAgentSession';
import { type ArtifactName, isPlotAction, type Theme } from 'src/lib/agent';
import { countOf } from 'src/sections/agent-chat/countOf';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import {
  ERROR_TEXT,
  localClock,
  PLOT_FAILED_TEXT,
  RECONNECTING_TEXT,
  refusalLabel,
} from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { type CardOutcome, ResultCard } from 'src/sections/agent-chat/ResultCard';
import { awaitsReply, type PendingReply, pendingReply } from 'src/sections/agent-chat/steps';
import {
  bodyTextSx,
  CHAT_SECTION_GAP,
  CHAT_TEXT_MAX,
  inlineCodeSx,
  labelSx,
  readableSx as textSx,
  THREAD_GAP,
} from 'src/sections/agent-chat/styles';
import { colors, fontSize, typography } from 'src/theme';

/** A passage of a reply in backticks, on one line: code, a column or a button the reply names. */
const INLINE_CODE = /`([^`\n]+)`/g;

/** A reply's text with its passages in backticks set off as code, never with the backticks. */
function ReplyText({ text }: { text: string }) {
  const parts: ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(INLINE_CODE)) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    parts.push(
      <Box component="code" key={match.index} sx={inlineCodeSx}>
        {match[1]}
      </Box>
    );
    last = match.index + match[0].length;
  }
  parts.push(text.slice(last));
  return <>{parts}</>;
}

/**
 * What the user's bubble of a page turn says: the button as it read when pressed (the page passes
 * it), else the button that sends the action; a carry the chat started has no button of its own.
 */
function actionText(item: Extract<ChatItem, { kind: 'action' }>): string {
  if (item.label) return item.label;
  return item.action === 'carry_plot'
    ? `plot in ${item.library} with your decisions`
    : `.${item.action}()`;
}

/** The in-progress line's words, beside the site's loader. */
const PENDING_TEXT: Record<PendingReply, string> = {
  summarize_data: 'summarizing your data',
  example_data: 'making example data',
  message: 'working on your message',
  stopping: 'stopping',
  reconnecting: RECONNECTING_TEXT,
  writing: 'writing the reply',
};

interface ChatThreadProps {
  state: AgentSessionState;
  specId: string;
  language: string;
  onRequestTheme: (version: number, theme: Theme) => void;
  onFetchArtifact: (version: number, name: ArtifactName, theme?: Theme) => Promise<Blob>;
  onTrack: (event: string, props?: Record<string, string | undefined>) => void;
  /** The result cards' usage beacon (`ResultCard`'s `onOutcome`). */
  onOutcome?: (action: CardOutcome, version: number) => void;
  /** The result cards' quick feedback; without it they show no control. */
  onSendFeedback?: (version: number, input: FeedbackInput) => Promise<void>;
  /** The card at a `data` item, or at the `transcription` item that waits (`DataPanel`). */
  renderData?: (part: 'data' | 'transcription') => React.ReactNode;
  /** Whether the first reply after a card may come into view: the user's focus is in the composer. */
  followReply?: () => boolean;
}

/** The kinds of item that answer a turn: the first of them after a card is its reply. */
const REPLY_KINDS: ReadonlySet<ChatItem['kind']> = new Set(['assistant', 'refusal', 'error']);

/**
 * The user's turns, on the right; like every text item of the thread (`textSx`), no wider than
 * a readable line since the column grows up to 1360 px (2026-11-02). The result cards take the
 * full width.
 */
const promptSx = {
  ...bodyTextSx,
  alignSelf: 'flex-end',
  maxWidth: { xs: '100%', sm: `min(85%, ${CHAT_TEXT_MAX})` },
  bgcolor: 'var(--bg-elevated)',
  border: '1px solid var(--rule)',
  borderRadius: 2,
  px: 1.5,
  py: 1,
} as const;

function Item({
  item,
  props,
  latestVersion,
  waiting,
}: {
  item: ChatItem;
  props: ChatThreadProps;
  latestVersion: number;
  /** This `transcription` item is the table read from text that waits for its decision. */
  waiting: boolean;
}) {
  switch (item.kind) {
    case 'paste':
      // The attachment as its chip named it: the user's turn, which the card answers.
      return (
        <Box data-testid="paste-item" sx={{ ...promptSx, fontFamily: typography.mono }}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          {item.text}
        </Box>
      );
    case 'data':
      return <>{props.renderData?.('data')}</>;
    case 'data_stub':
      return (
        <Box data-testid="data-stub" sx={{ ...labelSx, ...textSx }}>
          # earlier data · {countOf(item.rows, 'row')} · {countOf(item.columns, 'column')} ·
          replaced below
        </Box>
      );
    case 'transcription':
      // Only the table that waits shows its card; one a new paste or a switch dropped says so.
      return waiting ? (
        <>{props.renderData?.('transcription')}</>
      ) : (
        <Box sx={{ ...labelSx, ...textSx }}># table read from text · not used</Box>
      );
    case 'user':
      return (
        <Box sx={promptSx}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          {item.text}
        </Box>
      );
    case 'action':
      // The page's own turns as their buttons: `.example_data()` without data, `.create_plot()`
      // or `.start_over()`, the carry after a library switch. A plot names the library it is made
      // in, which the carry's text names already.
      return (
        <Box data-testid="action-item" sx={{ ...promptSx, fontFamily: typography.mono }}>
          <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', mr: 1 }}>
            ❯
          </Box>
          {actionText(item)}
          {isPlotAction(item.action) && item.action !== 'carry_plot' && (
            <Box component="span" sx={{ color: 'var(--ink-muted)', ml: 1 }}>
              # {item.library}
            </Box>
          )}
        </Box>
      );
    case 'assistant':
      return (
        <Box sx={{ ...bodyTextSx, ...textSx, borderLeft: '2px solid var(--rule)', pl: 1.5 }}>
          <ReplyText text={item.text} />
        </Box>
      );
    case 'refusal':
      return (
        <Box
          sx={{ ...textSx, borderLeft: `2px solid ${colors.warning}`, pl: 1.5 }}
          data-testid="refusal"
        >
          {/* A plain label: the code is the service's word for the log, behind the ⓘ. The
              line height of the other ⓘ lines, so a label that wraps keeps its spacing. */}
          <Box sx={{ ...labelSx, lineHeight: 1.6 }}>
            {refusalLabel(item.code)}
            {/* The service's own text says 00:00 UTC: the page adds the user's own time. */}
            {item.until && localClock(item.until) ? ` · until ${localClock(item.until)}` : ''}
            <InfoPopover
              label="About this answer"
              heading="# a fixed answer of the service, not the assistant's"
              lines={[`reason: ${item.code}`]}
              testId="refusal-details"
            />
          </Box>
          <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>{item.text}</Box>
        </Box>
      );
    case 'error':
      return (
        <Box role="alert" sx={{ ...textSx, borderLeft: `2px solid ${colors.error}`, pl: 1.5 }}>
          <Box sx={{ ...labelSx, color: colors.error }}>
            error · {item.code}
            {item.ref ? ` · ref ${item.ref}` : ''}
          </Box>
          <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
            {ERROR_TEXT[item.code] ?? 'the request failed'}
            <ReloadHint code={item.code} />
          </Box>
        </Box>
      );
    case 'notice':
      // A quiet line; its details, where it has any, behind the ⓘ at its end. A lost
      // confirmation has none: the status line at the chat frame's foot names it.
      return (
        <Box sx={{ ...labelSx, ...textSx, lineHeight: 1.6 }}>
          # {item.text}
          {item.info && (
            <InfoPopover
              label={item.info.label}
              heading={item.info.heading}
              lines={item.info.lines}
            />
          )}
        </Box>
      );
    case 'plot_failed':
      return (
        <Box sx={{ ...textSx, borderLeft: `2px solid ${colors.error}`, pl: 1.5 }}>
          <Box sx={{ ...labelSx, color: colors.error }}>
            plot · {item.result.status === 'not_ready' ? 'not ready' : 'failed'}
            {item.result.reason ? ` · ${item.result.reason}` : ''}
          </Box>
          <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
            {PLOT_FAILED_TEXT[item.result.reason ?? ''] ?? 'no plot this time'}
          </Box>
        </Box>
      );
    case 'plot': {
      const version = props.state.versions[item.version];
      if (!version) return null;
      return (
        <ResultCard
          version={version}
          specId={props.specId}
          language={props.language}
          latest={version.number === latestVersion}
          busy={sessionBusy(props.state)}
          onRequestTheme={props.onRequestTheme}
          onFetchArtifact={props.onFetchArtifact}
          onTrack={props.onTrack}
          onOutcome={props.onOutcome}
          onSendFeedback={props.onSendFeedback}
        />
      );
    }
    default:
      return null;
  }
}

/** The id of the first reply after the latest card, or null while it has none yet. */
function firstReplyId(items: ChatItem[]): number | null {
  let card = -1;
  for (let index = items.length - 1; index >= 0; index -= 1) {
    if (items[index].kind === 'data') {
      card = index;
      break;
    }
  }
  if (card < 0) return null;
  return items.slice(card + 1).find(item => REPLY_KINDS.has(item.kind))?.id ?? null;
}

export function ChatThread(props: ChatThreadProps) {
  const { items, versions } = props.state;
  const numbers = Object.keys(versions).map(Number);
  const latestVersion = numbers.length ? Math.max(...numbers) : 0;
  const pending = pendingReply(props.state);
  // Below a run's card no timeline follows: the line stands where the reply will, which takes
  // its place without a jump.
  const afterCard = awaitsReply(props.state);
  const waitingId = props.state.transcription
    ? [...items].reverse().find(item => item.kind === 'transcription')?.id
    : undefined;
  // The first reply after a card comes into view once, as it arrives (C-08): below a tall card
  // it would land under the fold, while the user's eyes are on the composer.
  const replyId = firstReplyId(items);
  const replyRef = useRef<HTMLDivElement>(null);
  // A reply that was there when the thread mounted has arrived already: only a new one moves it.
  const followed = useRef<number | null>(replyId);
  const { followReply } = props;
  useEffect(() => {
    if (replyId === null || followed.current === replyId) return;
    followed.current = replyId;
    if (followReply?.())
      replyRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
  }, [replyId, followReply]);
  return (
    <Box
      role="log"
      aria-label="Conversation"
      sx={{ display: 'flex', flexDirection: 'column', gap: THREAD_GAP, minWidth: 0 }}
    >
      {items.map(item => {
        // The page's summary turn has no button: its card says what was sent, and the summary
        // follows.
        if (item.kind === 'action' && item.action === 'summarize_data') return null;
        const node = (
          <Item
            key={item.id}
            item={item}
            props={props}
            latestVersion={latestVersion}
            waiting={item.id === waitingId}
          />
        );
        return item.id === replyId ? (
          <Box key={item.id} ref={replyRef} data-testid="first-reply" sx={{ minWidth: 0 }}>
            {node}
          </Box>
        ) : (
          node
        );
      })}
      {/* The assistant's slot, in its style, in softer ink: provisional until the reply. The
          site's loader says it works; the log's live region reads the words alone. */}
      {/* Laid out as the progress timeline is (`ProgressTimeline.tsx`): a turn that reaches a
          pipeline step hands the line over to the timeline below the thread, and the loader must
          stay where it is, only the text beside it changing. So the loader stands first, in a
          box one line of the run's font tall, on a phone above the text; and the line keeps a
          margin of the difference between the thread's gap and the gap above the timeline, so
          the timeline's top lands where this line's top was. Below a run's card, while its reply
          is written, no timeline follows: the line is the reply's first line instead, in the
          thread's gap alone, one row at every width and of the reply's line height, so the reply
          starts where it started and a one-line reply moves nothing below it. */}
      {pending && (
        <Box
          data-testid="pending-reply"
          sx={{
            display: 'flex',
            flexDirection: afterCard ? 'row' : { xs: 'column', sm: 'row' },
            alignItems: 'flex-start',
            gap: afterCard ? 1.5 : { xs: 1, sm: 1.5 },
            fontFamily: typography.mono,
            fontSize: fontSize.md,
            lineHeight: afterCard ? bodyTextSx.lineHeight : undefined,
            color: 'var(--ink-soft)',
            mt: afterCard ? 0 : CHAT_SECTION_GAP - THREAD_GAP,
          }}
        >
          <Box
            component="span"
            sx={{ display: 'flex', alignItems: 'center', '&::before': { content: '"\\200b"' } }}
          >
            <LoaderSpinner size="inline" />
          </Box>
          <Box sx={{ minWidth: 0 }}>{PENDING_TEXT[pending]}</Box>
        </Box>
      )}
    </Box>
  );
}
